#!/usr/bin/env python3
"""Replay SSSOM mappings onto a LinkML schema.

The curated ``*.sssom.tsv`` files under the mappings directory are the source
of truth for how the elements of this schema relate to other vocabularies.
This tool reads them with sssom-py, resolves every subject to a class, slot,
enum or permissible value of the schema, and adds the object CURIE to the
LinkML mapping slot that the predicate names. The schema is rewritten with
ruamel.yaml so that comments and layout survive; a second run changes nothing.

With ``--check`` nothing is written and the exit status is 1 when the schema
lacks a mapping that the files carry, which makes it the CI gate.

The specification is linkml/linkml-project-copier#163.
"""

import argparse
import sys
from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from sssom.parsers import parse_sssom_table

# The predicate decides which LinkML mapping slot receives the object. The
# two OWL equivalences are read as exact matches.
PREDICATE_SLOTS = {
    "skos:exactMatch": "exact_mappings",
    "skos:closeMatch": "close_mappings",
    "skos:broadMatch": "broad_mappings",
    "skos:narrowMatch": "narrow_mappings",
    "skos:relatedMatch": "related_mappings",
    "skos:mappingRelation": "mappings",
    "owl:equivalentClass": "exact_mappings",
    "owl:equivalentProperty": "exact_mappings",
}

# These slots state what an element is. An exact match to the URI one of them
# holds is already expressed and is not repeated in exact_mappings.
IDENTITY_SLOTS = ("class_uri", "slot_uri", "enum_uri", "meaning")


def read_mappings(mappings_dir: Path, view: SchemaView) -> tuple[list[tuple], dict]:
    """Return the rows of every SSSOM file and the union of their curie maps.

    A row is (file, subject as written, subject IRI, mapping slot, object).
    sssom-py parses the table and its metadata block. The subject is expanded
    with the file's own curie map, or failing that with the schema's prefixes.
    Rows that state the absence of a mapping, through a ``Not`` predicate
    modifier or the object ``sssom:NoTermFound``, are skipped.
    """
    rows, prefixes = [], {}
    for path in sorted(mappings_dir.glob("*.sssom.tsv")):
        msdf = parse_sssom_table(path)
        prefixes.update(msdf.prefix_map)
        for row in msdf.df.itertuples(index=False):
            negated = getattr(row, "predicate_modifier", None) == "Not"
            if negated or row.object_id == "sssom:NoTermFound":
                continue
            slot = PREDICATE_SLOTS.get(row.predicate_id)
            if slot is None:
                sys.exit(f"{path.name}: no mapping slot for {row.predicate_id}")
            subject = row.subject_id
            if ":" in subject:
                subject = msdf.converter.expand(subject) or view.expand_curie(subject)
            rows.append((path.name, row.subject_id, subject, slot, row.object_id))
    return rows, prefixes


def schema_targets(view: SchemaView, doc: CommentedMap) -> dict[str, tuple]:
    """Map every name and URI that addresses an element of this file to where it sits.

    Classes, slots, enums and class attributes are reachable by name, by the
    URI they declare (``class_uri`` and the like) and by their native URI under
    the schema's default prefix. A permissible value is reachable as
    ``<enum>#<value>``, the form that linkml's ``gen-sssom`` writes for it.
    Each target is the YAML mapping that holds the element together with the
    element's key, so that an element written with an empty body keeps it
    unless a mapping is added to it.
    """
    targets = {}

    def keys_for(name):
        declared = view.get_uri(name, expand=True)
        return {name, declared, view.get_uri(name, expand=True, native=True)}

    for section in ("classes", "slots", "enums"):
        elements = doc.get(section) or {}
        for name, node in elements.items():
            targets.update(dict.fromkeys(keys_for(name), (elements, name)))
            attributes = (node or {}).get("attributes") or {}
            for attribute in attributes:
                targets.update(
                    dict.fromkeys(keys_for(attribute), (attributes, attribute))
                )
            values = (node or {}).get("permissible_values") or {}
            for value in values:
                keys = {f"{key}#{value}" for key in keys_for(name)}
                targets.update(dict.fromkeys(keys, (values, value)))
    return targets


def overlay(
    doc: CommentedMap, view: SchemaView, rows: list, prefixes: dict, check: bool
) -> tuple[list[str], list[str]]:
    """Add every mapping the schema lacks and the prefixes those mappings need.

    Returns one line per mapping and one per prefix that the schema lacks. A
    prefix that an object uses and the schema does not declare is copied from
    the SSSOM curie map into ``prefixes``. With ``check`` nothing is changed.
    """
    targets = schema_targets(view, doc)
    declared = doc.get("prefixes")
    known = set(declared or {}) | set(view.namespaces())
    mappings, new_prefixes, seen = [], [], set()
    for file, written, subject, slot, obj in rows:
        if subject not in targets:
            sys.exit(f"{file}: subject {written} is not an element of this schema")
        parent, key = targets[subject]
        node = parent[key] or {}
        identity = {node.get(name) for name in IDENTITY_SLOTS}
        if slot == "exact_mappings" and obj in identity:
            continue
        # Two rows can name the same element, by name and by URI or in two
        # files; the mapping is listed once, in check mode as when writing.
        if obj in (node.get(slot) or []) or (id(parent), key, slot, obj) in seen:
            continue
        seen.add((id(parent), key, slot, obj))
        mappings.append(f"{written}: {slot} gets {obj}")
        if not check:
            if parent[key] is None:
                parent[key] = CommentedMap()
            parent[key][slot] = [*(parent[key].get(slot) or []), obj]
        prefix = obj.split(":", 1)[0]
        if ":" in obj and prefix not in known:
            if prefix not in prefixes:
                sys.exit(f"{file}: prefix {prefix} missing from curie map and schema")
            new_prefixes.append(f"prefixes: {prefix} gets {prefixes[prefix]}")
            known.add(prefix)
            if not check:
                if declared is None:
                    declared = doc["prefixes"] = CommentedMap()
                declared[prefix] = prefixes[prefix]
    return mappings, new_prefixes


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("schema", type=Path, help="the LinkML schema YAML file")
    parser.add_argument(
        "mappings_dir", type=Path, help="directory of the curated *.sssom.tsv files"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; list the mappings the schema lacks and exit 1 if any",
    )
    args = parser.parse_args(argv)

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    text = args.schema.read_text(encoding="utf-8")
    yaml.explicit_start = text.startswith("---")
    doc = yaml.load(text)
    view = SchemaView(str(args.schema))

    rows, prefixes = read_mappings(args.mappings_dir, view)
    mappings, new_prefixes = overlay(doc, view, rows, prefixes, check=args.check)
    for line in mappings + new_prefixes:
        print(line)
    if not mappings:
        print(f"{args.schema} carries every mapping in {args.mappings_dir}")
    elif args.check:
        print(f"{args.schema} lacks {len(mappings)} of them", file=sys.stderr)
        return 1
    else:
        yaml.dump(doc, args.schema)
        noun = "mapping" if len(mappings) == 1 else "mappings"
        print(f"{args.schema}: {len(mappings)} {noun} added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
