#!/usr/bin/env python3
"""Overlay SSSOM mappings onto LinkML schema YAML files.

For every ``*.sssom.tsv`` under ``--mappings-dir``, merges each row's
object CURIE into the matching LinkML mapping slot (``exact_mappings``,
``close_mappings``, ``broad_mappings``, ``narrow_mappings``,
``related_mappings``) on every element (class / slot / enum / type /
attribute / permissible value) whose local name matches the row
subject. The file is rewritten with ruamel.yaml round-trip mode so
comments and styling are preserved; the operation is idempotent.

Layout assumptions (good-path only):
  * TSV ``#``-metadata is valid YAML with a ``curie_map:`` block.
  * Subjects are written as ``<prefix>:<Name>`` or
    ``<prefix>:<Enum>/<PV>`` (slash-separated permissible values).
  * Subject prefixes come from each schema's own ``default_prefix``
    and ``name``; extend with repeated ``--subject-prefix`` if needed.
  * When invoked with no path flags, discovers
    ``<repo>/src/<slug>/{schema,mappings}`` relative to this script.

Typical usage (justfile ``overlay-sssom`` target)::

    python scripts/overlay_sssom.py            # apply
    python scripts/overlay_sssom.py --dry-run  # preview
    python scripts/overlay_sssom.py --check    # CI verification gate
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from sssom.parsers import parse_sssom_table


SSSOM_PREDICATE_TO_LINKML_SLOT: dict[str, str] = {
    "skos:exactMatch":        "exact_mappings",
    "skos:closeMatch":        "close_mappings",
    "skos:broadMatch":        "broad_mappings",
    "skos:narrowMatch":       "narrow_mappings",
    "skos:relatedMatch":      "related_mappings",
    "owl:equivalentClass":    "exact_mappings",
    "owl:equivalentProperty": "exact_mappings",
}

_IGNORED_PREDICATES = frozenset({"skos:broader", "skos:narrower", "rdf:type"})

_BUILTIN_PREFIXES = frozenset({
    "sssom", "owl", "rdf", "rdfs", "skos", "semapv",
    "linkml", "xsd", "dcterms",
})

_MAPPING_SLOT_ORDER = (
    "exact_mappings", "close_mappings", "broad_mappings",
    "narrow_mappings", "related_mappings",
)

# Keys that conventionally follow the mapping slots; a freshly-inserted
# mapping slot (or PV ``meaning``) is placed just before the first of
# these that exists in the element body.
_POST_MAPPING_ANCHORS = (
    "aliases", "in_subset", "permissible_values", "attributes", "slots",
    "slot_usage", "rules", "comments", "annotations", "pattern",
)

_ELEMENT_SECTIONS = ("classes", "slots", "enums", "types")

_SECTION_KIND = {"classes": "class", "slots": "slot",
                 "enums": "enum", "types": "type"}

# YAML files under the schema dir that carry none of these are treated
# as non-LinkML (mkdocs.yml, GitHub Actions, etc.) and silently skipped.
_LINKML_SCHEMA_KEYS = frozenset({
    "id", "name", "prefixes", "default_prefix", "default_range",
    "imports", "classes", "slots", "enums", "types", "subsets",
})


def _make_yaml() -> YAML:
    y = YAML(typ="rt")
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def _looks_like_linkml_schema(data: object) -> bool:
    return (isinstance(data, CommentedMap)
            and bool(_LINKML_SCHEMA_KEYS & set(data.keys())))


# ---------------------------------------------------------------------------
# Mapping index
# ---------------------------------------------------------------------------

class MappingIndex:
    """Raw SSSOM rows plus a prefix-filtered ``by_name`` view."""

    def __init__(self) -> None:
        # subject_local_name -> mapping_slot -> ordered [object CURIE, ...]
        self.by_name: dict[str, dict[str, list[str]]] = {}
        # CURIE prefix -> URI, from each TSV's ``#curie_map:`` block.
        self.prefix_uris: dict[str, str] = {}
        # (subject_curie, slot, object_curie) triples from all TSVs.
        self.rows: list[tuple[str, str, str]] = []

    def build_for_prefixes(self, prefixes: set[str]) -> None:
        self.by_name.clear()
        with_colon = tuple(f"{p}:" for p in prefixes)
        for subject, slot, obj in self.rows:
            local: str | None = None
            for px in with_colon:
                if subject.startswith(px):
                    local = subject[len(px):]
                    break
            if local is None:
                continue
            entries = self.by_name.setdefault(local, {}).setdefault(slot, [])
            if obj not in entries:
                entries.append(obj)

    def used_prefixes_for(self, name: str) -> set[str]:
        return {c.split(":", 1)[0]
                for curies in self.by_name.get(name, {}).values()
                for c in curies if ":" in c}


def load_mappings(mappings_dir: Path) -> MappingIndex:
    """Load every ``*.sssom.tsv`` under ``mappings_dir`` (recursive).

    Parsing (TSV rows, ``#``-metadata, and ``curie_map``) is delegated to
    sssom-py, which also drops malformed rows with a logged warning instead
    of failing the whole file.
    """
    idx = MappingIndex()
    for tsv in sorted(mappings_dir.rglob("*.sssom.tsv")):
        msdf = parse_sssom_table(tsv)

        for px, uri in msdf.prefix_map.items():
            if px in _BUILTIN_PREFIXES:
                continue
            idx.prefix_uris.setdefault(str(px), str(uri))

        columns = set(msdf.df.columns)
        if not {"subject_id", "predicate_id", "object_id"} <= columns:
            continue
        for row in msdf.df.itertuples(index=False):
            subject = str(row.subject_id).strip()
            predicate = str(row.predicate_id).strip()
            obj = str(row.object_id).strip()
            if not subject or not obj or predicate in _IGNORED_PREDICATES:
                continue
            slot = SSSOM_PREDICATE_TO_LINKML_SLOT.get(predicate)
            if slot is None:
                continue
            idx.rows.append((subject, slot, obj))
    return idx


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def discover_subject_prefixes(data: CommentedMap) -> set[str]:
    """Return the CURIE prefixes that identify the schema itself."""
    out: set[str] = set()
    for key in ("default_prefix", "name"):
        v = data.get(key)
        if isinstance(v, str) and v:
            out.add(v)
    return out


def _insert_before_anchors(body: CommentedMap, key: str, value) -> None:
    """Insert ``key`` before the first post-mapping anchor; else append."""
    if key in body:
        body[key] = value
        return
    keys = list(body.keys())
    for anchor in _POST_MAPPING_ANCHORS:
        if anchor in keys:
            body.insert(keys.index(anchor), key, value)
            return
    body[key] = value


def _merge_mappings(
    body: CommentedMap,
    slot_map: dict[str, list[str]],
    *,
    is_permissible_value: bool = False,
) -> tuple[bool, int]:
    """Merge ``slot_map`` into ``body``; return ``(touched, links_added)``.

    For permissible values, the first ``exact_mappings`` CURIE is
    promoted to ``meaning`` when meaning is unset; the remaining exact
    CURIEs still land in ``exact_mappings``.
    """
    touched = False
    links_added = 0
    for slot in _MAPPING_SLOT_ORDER:
        curies = slot_map.get(slot)
        if not curies:
            continue

        if is_permissible_value and slot == "exact_mappings":
            remaining = list(curies)
            meaning = body.get("meaning")
            if not meaning:
                _insert_before_anchors(body, "meaning", remaining.pop(0))
                links_added += 1
                touched = True
            else:
                remaining = [c for c in remaining if c != meaning]
            if not remaining:
                continue
            curies = remaining

        existing = body.get(slot)
        if existing is None:
            _insert_before_anchors(body, slot, CommentedSeq(curies))
            links_added += len(curies)
            touched = True
            continue
        new_list = list(existing)
        added = [c for c in curies if c not in new_list]
        if added:
            body[slot] = CommentedSeq(new_list + added)
            links_added += len(added)
            touched = True
    return touched, links_added


def _ensure_prefixes(
    data: CommentedMap,
    needed: set[str],
    prefix_uris: dict[str, str],
    own_prefixes: set[str],
) -> bool:
    prefixes = data.get("prefixes")
    if not isinstance(prefixes, dict):
        prefixes = CommentedMap()
        data["prefixes"] = prefixes
    changed = False
    for px in sorted(needed):
        if (px in _BUILTIN_PREFIXES or px in own_prefixes
                or px in prefixes):
            continue
        uri = prefix_uris.get(px)
        if uri is None:
            continue
        prefixes[px] = uri
        changed = True
    return changed


def _iter_targets(
    data: CommentedMap,
    by_name: dict[str, dict[str, list[str]]],
):
    """Yield ``(kind, display_name, body, slot_map, is_pv, subject)`` for
    each element in ``data`` that has a matching mapping in ``by_name``.
    ``subject`` is the SSSOM local name used to look up ``slot_map``.
    """
    for section in _ELEMENT_SECTIONS:
        collection = data.get(section)
        if not isinstance(collection, dict):
            continue
        kind = _SECTION_KIND[section]
        for name, body in collection.items():
            if not isinstance(body, CommentedMap):
                continue
            slot_map = by_name.get(name)
            if slot_map:
                yield kind, name, body, slot_map, False, name
            if section == "classes":
                attrs = body.get("attributes")
                if not isinstance(attrs, dict):
                    continue
                for aname, abody in attrs.items():
                    if not isinstance(abody, CommentedMap):
                        continue
                    asm = by_name.get(aname)
                    if asm:
                        yield ("attribute", f"{name}.{aname}",
                               abody, asm, False, aname)

    enums = data.get("enums")
    if not isinstance(enums, dict):
        return
    for subject, slot_map in by_name.items():
        if "/" not in subject:
            continue
        enum_name, _, pv_name = subject.partition("/")
        enum_body = enums.get(enum_name)
        if not isinstance(enum_body, CommentedMap):
            continue
        pvs = enum_body.get("permissible_values")
        if not isinstance(pvs, dict):
            continue
        pv_body = pvs.get(pv_name)
        if isinstance(pv_body, CommentedMap):
            yield ("permissible_value", pv_name, pv_body, slot_map,
                   True, subject)


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------

def overlay_file(
    schema_path: Path,
    mappings: MappingIndex,
    extra_subject_prefixes: set[str],
    *,
    dry_run: bool = False,
    display_path: str | None = None,  # accepted for CLI symmetry; unused here
) -> tuple[int, int]:
    """Overlay ``mappings`` onto one schema YAML in place.

    Returns ``(elements_updated, links_added)``. The file is rewritten
    only when at least one element was modified or a new prefix was
    declared (and ``dry_run`` is False).
    """
    del display_path  # not needed once diagnostics are suppressed
    y = _make_yaml()
    with open(schema_path, encoding="utf-8") as fh:
        data = y.load(fh)
    if not _looks_like_linkml_schema(data):
        return 0, 0

    subject_prefixes = discover_subject_prefixes(data) | extra_subject_prefixes
    if not subject_prefixes:
        return 0, 0
    mappings.build_for_prefixes(subject_prefixes)
    if not mappings.by_name:
        return 0, 0

    elements_updated = 0
    links_added = 0
    used_prefixes: set[str] = set()
    for _kind, _disp, body, slot_map, is_pv, subject in _iter_targets(
        data, mappings.by_name,
    ):
        touched, n_added = _merge_mappings(
            body, slot_map, is_permissible_value=is_pv,
        )
        if touched:
            elements_updated += 1
            links_added += n_added
            used_prefixes |= mappings.used_prefixes_for(subject)

    prefixes_changed = _ensure_prefixes(
        data, used_prefixes, mappings.prefix_uris, subject_prefixes,
    )

    if (elements_updated or prefixes_changed) and not dry_run:
        with open(schema_path, "w", encoding="utf-8") as fh:
            y.dump(data, fh)
    return elements_updated, links_added


# ---------------------------------------------------------------------------
# Verification (read-only)
# ---------------------------------------------------------------------------

def _row_is_present(
    body: CommentedMap, slot: str, curie: str,
    *, is_pv: bool, pv_promoted: set[str],
) -> bool:
    """True iff ``(slot, curie)`` is already reflected in ``body``.

    For PV ``exact_mappings`` rows, a CURIE counts as present if it
    matches ``meaning``. When several exact rows target a PV with no
    meaning yet, only the first is treated as the (future) promotion;
    the caller passes ``pv_promoted`` to keep that state across rows.
    """
    existing = list(body.get(slot) or [])
    if curie in existing:
        return True
    if is_pv and slot == "exact_mappings":
        meaning = body.get("meaning")
        if meaning and curie == meaning:
            return True
        if not meaning and not pv_promoted:
            pv_promoted.add(curie)
    return False


def _relative_display(path: Path, root: Path | None) -> str:
    if root is None:
        return path.name
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _diagnose(
    data: CommentedMap,
    display: str,
    by_name: dict[str, dict[str, list[str]]],
    subject_prefixes: set[str],
    known_subjects: set[str],
) -> list[str]:
    diagnostics: list[str] = []
    matched: set[str] = set()
    for kind, name, body, slot_map, is_pv, subject in _iter_targets(
        data, by_name,
    ):
        matched.add(subject)
        promoted: set[str] = set()
        for slot in _MAPPING_SLOT_ORDER:
            for curie in slot_map.get(slot) or ():
                if not _row_is_present(body, slot, curie,
                                       is_pv=is_pv, pv_promoted=promoted):
                    diagnostics.append(
                        f"{display}: {kind} {name!r} missing "
                        f"{slot}: {curie}"
                    )

    for name in sorted(set(by_name) - matched - known_subjects):
        diagnostics.append(
            f"{display}: SSSOM subject {name!r} does not resolve to any "
            "schema element (class / slot / enum / type / attribute / "
            "permissible value)"
        )

    declared = set((data.get("prefixes") or {}).keys())
    referenced = {curie.split(":", 1)[0]
                  for slot_map in by_name.values()
                  for curies in slot_map.values()
                  for curie in curies if ":" in curie}
    for px in sorted(referenced - declared - _BUILTIN_PREFIXES
                     - subject_prefixes):
        diagnostics.append(
            f"{display}: prefix {px!r} is referenced by a mapping but not "
            "declared in the schema's prefixes: block"
        )
    return diagnostics


def check_files(
    schema_paths: list[Path],
    mappings: MappingIndex,
    extra_subject_prefixes: set[str],
    *,
    schema_root: Path | None = None,
) -> list[str]:
    """Multi-file verification driver.

    Snapshots each file's ``by_name`` view so a later
    ``build_for_prefixes`` call doesn't clobber it, then emits per-file
    diagnostics using a global match-set so an unresolved-subject
    diagnostic only fires for subjects that resolve in no file.
    """
    y = _make_yaml()
    per_file: list[tuple[str, CommentedMap | None, set[str] | None,
                         dict | None]] = []
    globally_matched: set[str] = set()

    for path in schema_paths:
        display = _relative_display(path, schema_root)
        with open(path, encoding="utf-8") as fh:
            data = y.load(fh)
        if not _looks_like_linkml_schema(data):
            continue
        subject_prefixes = (
            discover_subject_prefixes(data) | extra_subject_prefixes
        )
        if not subject_prefixes:
            per_file.append((display, None, None, None))
            continue
        mappings.build_for_prefixes(subject_prefixes)
        snapshot = {k: {s: list(v) for s, v in slots.items()}
                    for k, slots in mappings.by_name.items()}
        for _k, _n, _b, _sm, _ipv, subject in _iter_targets(data, snapshot):
            globally_matched.add(subject)
        per_file.append((display, data, subject_prefixes, snapshot))

    diagnostics: list[str] = []
    for display, data, subject_prefixes, by_name in per_file:
        if data is None:
            diagnostics.append(
                f"{display}: no default_prefix/name in schema and no "
                "--subject-prefix supplied; cannot verify"
            )
            continue
        if not by_name:
            continue
        assert subject_prefixes is not None
        diagnostics.extend(_diagnose(
            data, display, by_name, subject_prefixes, globally_matched,
        ))
    return diagnostics


def check_file(
    schema_path: Path,
    mappings: MappingIndex,
    extra_subject_prefixes: set[str],
    *,
    display_path: str | None = None,  # accepted for backwards compat
    known_subjects: set[str] | None = None,  # ditto
) -> list[str]:
    """Single-file wrapper around :func:`check_files`."""
    del display_path, known_subjects
    return check_files([schema_path], mappings, extra_subject_prefixes)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _autodiscover(script_path: Path) -> tuple[Path, str] | None:
    """Locate ``<repo>/src/<slug>/`` from the shipped script location."""
    root = script_path.resolve().parent.parent
    src = root / "src"
    if not src.is_dir():
        return None
    candidates = [d for d in sorted(src.iterdir())
                  if d.is_dir() and (d / "schema").is_dir()]
    if len(candidates) == 1:
        return root, candidates[0].name
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = p.add_mutually_exclusive_group()
    src.add_argument("--schema-dir", type=Path,
                     help="dir of LinkML schema YAMLs (recursive); "
                          "defaults to src/<slug>/schema")
    src.add_argument("--schema", type=Path,
                     help="single LinkML schema YAML file")
    p.add_argument("--mappings-dir", type=Path,
                   help="dir of *.sssom.tsv files; defaults to "
                        "src/<slug>/mappings")
    p.add_argument("--subject-prefix", action="append", default=[],
                   metavar="PREFIX",
                   help="extra subject-side CURIE prefix (repeatable)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="report changes without writing any files")
    mode.add_argument("--check", action="store_true",
                      help="read-only verification gate (exit 1 on drift)")
    args = p.parse_args(argv)

    need_discovery = (args.schema is None and args.schema_dir is None
                      or args.mappings_dir is None)
    if need_discovery:
        discovered = _autodiscover(Path(__file__))
        if discovered is None:
            print("ERROR: could not auto-discover src/<slug>/; pass "
                  "--schema-dir/--schema and --mappings-dir",
                  file=sys.stderr)
            return 1
        root, slug = discovered
        if args.schema is None and args.schema_dir is None:
            args.schema_dir = root / "src" / slug / "schema"
        if args.mappings_dir is None:
            args.mappings_dir = root / "src" / slug / "mappings"

    if args.schema:
        schemas = [args.schema]
        schema_root: Path | None = args.schema.parent
    else:
        schemas = sorted(args.schema_dir.rglob("*.yaml"))
        if not schemas:
            print(f"No YAML schemas in {args.schema_dir}", file=sys.stderr)
            return 1
        schema_root = args.schema_dir

    mappings = load_mappings(args.mappings_dir)
    if not mappings.rows:
        print(f"No mapping rows loaded from {args.mappings_dir}",
              file=sys.stderr)
        return 0

    extra = {px.rstrip(":") for px in args.subject_prefix if px}

    if args.check:
        diagnostics = check_files(schemas, mappings, extra,
                                  schema_root=schema_root)
        for line in diagnostics:
            print(line)
        if diagnostics:
            print(f"\nVerification FAILED: {len(diagnostics)} issue(s) "
                  f"across {len(schemas)} schema file(s). Run without "
                  "--check to apply.", file=sys.stderr)
            return 1
        print(f"\nVerification OK: {len(schemas)} schema file(s) are in "
              "sync with the SSSOM TSVs.")
        return 0

    files_changed = total_elements = total_links = 0
    for path in schemas:
        display = _relative_display(path, schema_root)
        elements, links = overlay_file(
            path, mappings, extra, dry_run=args.dry_run,
        )
        if elements:
            files_changed += 1
            total_elements += elements
            total_links += links
            prefix = "[dry-run] " if args.dry_run else ""
            print(f"  {prefix}{display}: +{links} links across "
                  f"{elements} elements")

    if total_links:
        verb = "would apply" if args.dry_run else "applied"
        print(f"\nOverlay complete: {total_links} new mappings {verb} to "
              f"{total_elements} elements across {files_changed} files")
    else:
        print("\nOverlay complete: schemas already in sync with SSSOM "
              "files - no changes needed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
