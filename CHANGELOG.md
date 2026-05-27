# Changelog

This changelog provides a high-level overview of changes.
From v0.2.0 onwards, the versioning follows the principles of [Semantic Versioning](https://semver.org/).
The format is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

<!-- possible sections:
    Added       for new features.
    Fixed       for any bug fixes.
    Changed     for changes in existing functionality.
    Breaking    for changes that are backward incompatible
    Deprecated  for soon-to-be removed features.
    Removed     for now removed features.
    Security    in case of vulnerabilities.
-->
## Unreleased

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.5.0...main)

## Release [0.5.0] - 2026-05-27

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.4.2...v0.5.0)

[0.5.0]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.5.0

### Added

- Pytest-based integration test suite for the copier template, including
  helpers module and CONTRIBUTING.md for the template. #140
- Submission of releases to the LinkML community on Zenodo. #141
- List of recommended mkdocs/material extensions in the project mkdocs
  configuration. #148
- Support for Python 3.14 in the template's CI matrix. #160
- README in the `project/` directory so the folder is tracked even before
  generation. #161 (fixes #124)
- Auto-detect WSL2 in `just setup` and advise the user accordingly. #149
- Copier prompt for an existing custom LICENSE file; when set, the user's
  file is preserved and `pyproject.toml`'s `license-files` references it
  (using the PEP 639 SPDX expression `LicenseRef-Custom`). #162 (closes #151)
- Add Noel McLoughlin as a co-creator in the Zenodo metadata. #165
- `tool.ruff` section in `pyproject.toml` excluding auto-generated `_version.py`
  and setting the minimum Python version. #170
- Module docstrings in template `__init__.py` files to avoid ruff D104. #170

### Changed

- Default `license` is now `Apache-2.0` (was `MIT`). #151

### Added

- New `existing_license_file` prompt: when set to the path of a license file
  already present in the project (e.g. `LICENSE.md`, `LICENSE.txt`), the
  template skips generating a new `LICENSE` and points `license-files` in
  `pyproject.toml` at the provided file. The `license` prompt then defaults to
  `Custom` (recorded as the PEP 639 SPDX identifier `LicenseRef-Custom`),
  signalling "see the license file"; the user can override with a specific
  SPDX identifier if they know it. #151

### Fixed

- `just gen-project` tolerates a missing `project/` directory. #161
- Generated YAML files (GitHub Actions, mkdocs) and `test_data.py` now pass
  default yamllint/ruff checks. #170
- Reject invalid `project_name` input (e.g. trailing dot, single character) at
  the prompt with a friendly message instead of crashing later.
- `just _update-linkml` uses `uv lock` instead of `uv add` to avoid side-effect
  of adding linkml as main dependency. #159
- Force-push to `gh-pages` during docs deployment to avoid history conflicts. #154
- Align `uv sync` invocation in template workflows. #150
- Skip ShEx integration test on Python 3.13 and install dependencies in the
  integration test fixture. #140
- Lint test tolerates warnings; example reduced to 4 warnings. #140

### Changed

- Default license for new projects is now Apache-2.0 (was MIT), matching
  linkml core. #162
- Drop Python 3.9 from the supported version matrix; bump minimum Python
  requirement to >=3.10. #155
- Update pre-commit configuration and recommend installing pre-commit via
  `pre-commit-uv`. #145
- Group Dependabot updates into a single monthly PR. #139
- Update URLs throughout the project to the new linkml monorepo / template
  location (README, migration notes, CHANGELOG). #132
- Cleaner linter defaults: yamllint ignores non-compliant generated files and
  uses line-length 88; pre-commit skips `.copier-answers.yml` and pins newer
  tool versions. #170
- Enable `set windows-shell` by default in the template `justfile`
  (no-op on Linux/macOS). #170
- README notes that migrating existing projects should review/merge template
  linter configs rather than overwrite. #170

## Release [0.4.2] - 2026-02-25

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.4.1...v0.4.2)

[0.4.2]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.4.2

### Added

- Generate TypeScript output and allow regeneration of OWL artifacts. #113
- `just` improvements: allow overriding generator commands and generating
  additional formats. #114
- mkdocs customizations and pymdown extensions in the generated project. #101
- Document the `UV_DEFAULT_INDEX` environment variable for custom package
  indexes. #97
- Document handling of the WSL2 `just setup` error in the README. #99

### Fixed

- Fix `uv tool` install command so that `jinja2-time` is included with
  copier. #90
- Disable Jinja interpolation of `{{ }}` in generated outputs to avoid
  double-brace breakage. #105
- `just setup` no longer fails when the working tree is not git-clean. #102
- Skip the docs-preview action on PRs originating from forks. #111

### Changed

- Adjust README and project metadata for the new home under the `linkml`
  GitHub organization (replace `dalito` references, spelling fixes, remove
  cookiecutter-era text). #94, #104
- Update OWL settings in `config.yaml`. #96
- Improve the docs-preview action and activate it by default. #115
- Update all GitHub actions in the template to current versions. #108
- Rename the example schema container slot `entries` to `people`. #110
- Allow a configurable Python version in the template workflows' matrix. #100

## Release [0.4.1] - 2025-08-02

### Changed

- Update to also test on Python 3.13 and use Python 3.13 as default in actions. #89
- Update to use linkml >= 1.9.3 #89
- Update github actions to latest versions. #89
- Update github actions in project and change from hash version specifier to text. #86

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.4.0...v0.4.1)

[0.4.1]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.4.1

## Release [0.4.0] - 2025-04-06

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.3.1...v0.4.0)

[0.4.0]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.4.0

### Added

- New pre-commit command that updates the uv.lock file. #81
- Automatic publishing of releases to Zenodo ([doi:10.5281/zenodo.15163584](https://doi.org/10.5281/zenodo.15163584)).

### Fixed

- Adjust docs-preview required permission to publish messages in PR thread.
- Create directory `docs/schema` within `_gen-yaml` recipe if not present.

### Changed

- Migrate to new packaging/build tools: uv, uv-dynamic-versioning and hatch. #81

## Release [0.3.1] - 2025-04-04

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.3.0...v0.3.1)

[0.3.1]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.3.1

### Added

- The `just gen-doc` command will now also build a merged schema (yaml).
- The `just test` command will now also test all json test datafiles (in addition to yaml). #79

### Fixed

- Give docs-preview required permission to publish messages in PR thread. #74
- Correct lower Python boundary to 3.9 in template. #80

### Changed

- Applied April-2025 updates to dependencies of gh-actions. #80

## Release [0.3.0] - 2025-03-02

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.2.2...v0.3.0)

[0.3.0]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.3.0

### Added

- Typos integration with pre-commit (was only an gh-action before). #58

### Fixed

- Fix yamllint config-location in pre-commit configuration of the project. #60
- Generate markdown schema documentation as part of docs build in gh-actions.
- Remove old files from `docs/elemnents" before re-creating markdown files. #66
- Fix clean command to remove only md-files from `docs/elements`.
- Generate java code from model. #70
- Clean `examples/output` folder before re-creating its content in recipe `just test`. #72

### Changed

- The generated part of the documentation is now git-ignored (`docs/elements/*.md`). #59
- Make gen-doc a visible just command (was already present as "_gendoc").
- Don't commit project artifacts on initialisation. #65
- Let `just lint` recipe lint all schema files in schema dir instead of only
  the main schema. #71

### Breaking

- The environment variable to the schema file `LINKML_SCHEMA_SOURCE_PATH` was
  replaced by a new environment variable `LINKML_SCHEMA_SOURCE_DIR` pointing to
  the directory with schema files.

## Release [0.2.2] - 2025-02-17

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.2.2...v0.2.1)

[0.2.2]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.2.2

### Changed

- Improved 0.2.x-migration message for `just update`.

### Fixed

- Moving files in the 0.2.0-migration was incomplete and gave git errors due to non-existing folders.
  The just shell recipe was replaced by a new Python recipe to work around the limitations of `git mv`.

## Release [0.2.1] - 2025-02-16

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.2.1...v0.2.0)

[0.2.1]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.2.1

### Added

- Notes on updating from 0.1.x to 0.2.x to [README.md](./README.md#notes-on-specific-updates).
- Developer tools: Repo and generated project now have a pre-commit configuration with sections for yamllint, typos, ruff (only in project) and some basic checks from pre-commit itself. #50
- Typos spell checker as gh-action for the repo (but not for the generated project). #50
- Added a README to the schema subfolder so that it is added to git even in absence of a schema file.

### Fixed

- Syntax of `just setup` recipe.
- Invalid just recipe name for migrating from 0.1.x to 0.2.x which prevented execution on copier update.
- Excessive whitespace generation in jinja-templates (e.g. in LICENSE files)
- Some LICENSES were not correctly copied to the generated project. #52
- Wrong jinja escaping for creating the example schema and test-page-build action. This led to the creation of the files even if the question was answered with "no" in copier.

### Changed

- All yes/no question are now treated as type bool in copier.
- Ignore also `docs/index.md` and `docs/about.md` when updating with copier.
- Make Python test for example schema/datamodel more general.
- Make `just gen-project` a visible command (it was already present but hidden).
- Improved yamllint configuration and reformatted all non-conforming yaml files in the project. #50
- Change license of linkml-project-copier from CC0 to MIT. #49

### Removed

- Removed schemasheet integration from copier-setup questions and related just recipes. Since it never worked this removal is not considered a breaking change. #46

## Release [0.2.0] - 2025-02-13

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.2.0...v0.1.6) relative to v0.1.6 since this was the base of v0.2.0.

[0.2.0]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.2.0

### Highlights ⚡

**This release implements many of the changes that motivated the project.**

- Cleaner directory structure matching the expectations on mkdocs/python-projects.
  - `docs` is now the permanent storage for docs.
  - `docs/elements` is the new directory for markdown files generated from the schema.
  - `docs/templates-linkml` contains the jinja-templates for customizing the generated schema documentation.
  - `tests/data`-folder is now the primary source of example data (was `src/data`)
- Easier customization of mkdocs documentation: Thanks to the above directory changes, the guidelines from mkdocs on [customizing the theme/js/css](https://www.mkdocs.org/user-guide/customizing-your-theme/) are now directly applicable for projects generated from the template.
- `project/*` all code in this folder is now generated from the schema and no longer included in the template.
- Improved example project (more examples, better tests that use [pytest](https://pytest.org))
- If the example project or if certain GitHub actions should be created or not, can be selected via copier setup questions.
- Several of the changes result in combination in a **low risk of conflicts when updating the underlying template** in existing projects (for future updates after 0.2.0).
- Support `just` as the only command runner. The support for `make` was removed to simplify maintenance.

Most changes were made in one PR (#31) followed by fixups in #42 and #44.

### Removed

- support for make as alternative command runner

### Breaking

- New directory layout for docs and example/test data compared to 0.1.x series (see above)

## Release [0.1.7] - 2025-02-13

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.1.7...v0.1.6)

[0.1.7]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.1.7

### Fixed

- Testing of valid & invalid data as part of `just test` recipe. #41

## Release [0.1.6] - 2025-02-12

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.1.6...v0.1.5)

[0.1.6]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.1.6

### Added

- Add .editorconfig to template & project. #29

### Fixed

- Fix clean recipe. #35

### Changed

- Give gh-pages bot a name/email for a better git log. #28

## Release [0.1.5] - 2025-02-08

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.1.5...v0.1.4)

[0.1.5]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.1.5

### Fixed

- deploy-docs action was failing because credentials were removed directly after checkout although they were still needed later.

## Release [0.1.4] - 2025-02-08

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.1.4...v0.1.3)

[0.1.4]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.1.4

### Fixed

- install cmd in docs-building actions. #26

## Release [0.1.3] - 2025-02-08

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.1.3...v0.1.2)

[0.1.3]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.1.3

### Fixed

- clean command should not remove README and init.py. #22

## Release [0.1.2] - 2025-02-06

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.1.2...v0.1.1)

[0.1.2]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.1.2

### Added

- copier validation for main_schema_class name. #21

## Release [0.1.1] - 2025-02-06

[Full changelog](https://github.com/linkml/linkml-project-copier/compare/v0.1.1...v0.1.0)

[0.1.1]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.1.1

### Added

* Add command groups to justfile by @dalito in #16
* Add dependabot for action-updates. #14

### Changed

* Improve updating by adding more files/dirs for copier to skip #11
* Update actions. #14

## Release [0.1.0] - 2025-01-19

[Full changelog](https://github.com/linkml/linkml-project-copier/commits/v0.1.0)

[0.1.0]: https://github.com/linkml/linkml-project-copier/releases/tag/v0.1.0

**First release of a new [copier](https://copier.readthedocs.io/en/stable/)-based [LinkML](https://linkml.io/linkml)-project template.**

- This and later 0.1.x releases are compatible with [linkml-project-cookiecutter](https://github.com/linkml/linkml-project-cookiecutter/) except that they use copier instead of cruft/cookiecutter as scaffolding tool.  
- This release generates the same project as linkml-project-cookiecutter (commit [1094cf2](https://github.com/linkml/linkml-project-cookiecutter/commit/1094cf2ce542028ab0017eaa059dd49cdde81fb5), date 2025-01-10).

### Changed

In comparison to linkml-project-cookiecutter:

- Switch from cruft/cookiecutter to copier. #3
- Replace hooks by copier features and improve updates. #5
- [just](https://github.com/casey/just) is the primary command runner instead of make.

### Breaking

In comparison to linkml-project-cookiecutter:

- dot-env-standard compliant formatting of the configuration file (`config.public.mk`). This breaks Makefile-compatibility. See the notes in the file to restore make-conformity.
