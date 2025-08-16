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

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.4.1...main)

### Fixed

- Fix `uv tool` command that includes jinja2-time into copier. #90

## Release [0.4.1] - 2025-08-02

### Changed

- Update to also test on Python 3.13 and use Python 3.13 as default in actions. #89
- Update to use linkml >= 1.9.3 #89
- Update github actions to latest versions. #89
- Update github actions in project and change from hash version specifier to text. #86

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.4.0...0.4.1)

[0.4.1]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.4.1

## Release [0.4.0] - 2025-04-06

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.3.1...0.4.0)

[0.4.0]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.4.0

### Added

- New pre-commit command that updates the uv.lock file. #81
- Automatic publishing of releases to Zenodo ([doi:10.5281/zenodo.15163584](https://doi.org/10.5281/zenodo.15163584)). #

### Fixed

- Adjust docs-preview required permission to publish messages in PR thread.
- Create directory `docs/schema` within `_gen-yaml` recipe if not present.

### Changed

- Migrate to new packaging/build tools: uv, uv-dynamic-versioning and hatch. #81

## Release [0.3.1] - 2025-04-04

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.3.0...0.3.1)

[0.3.1]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.3.1

### Added

- The `just gen-doc` command will now also build a merged schema (yaml).
- The `just test` command will now also test all json test datafiles (in addition to yaml). #79

### Fixed

- Give docs-preview required permission to publish messages in PR thread. #74
- Correct lower Python boundary to 3.9 in template. #80

### Changed

- Applied April-2025 updates to dependencies of gh-actions. #80

## Release [0.3.0] - 2025-03-02

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.2.2...0.3.0)

[0.3.0]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.3.0

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

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.2.2...v0.2.1)

[0.2.2]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.2.2

### Changed

- Improved 0.2.x-migration message for `just update`.

### Fixed

- Moving files in the 0.2.0-migration was incomplete and gave git errors due to non-existing folders.
  The just shell recipe was replaced by a new Python recipe to work around the limitations of `git mv`.

## Release [0.2.1] - 2025-02-16

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.2.1...v0.2.0)

[0.2.1]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.2.1

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

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.2.0...v0.1.6) relative to v0.1.6 since this was the base of v0.2.0.

[0.2.0]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.2.0

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

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.1.7...v0.1.6)

[0.1.7]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.1.7

### Fixed

- Testing of valid & invalid data as part of `just test` recipe. #41

## Release [0.1.6] - 2025-02-12

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.1.6...v0.1.5)

[0.1.6]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.1.6

### Added

- Add .editorconfig to template & project. #29

### Fixed

- Fix clean recipe. #35

### Changed

- Give gh-pages bot a name/email for a better git log. #28

## Release [0.1.5] - 2025-02-08

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.1.5...v0.1.4)

[0.1.5]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.1.5

### Fixed

- deploy-docs action was failing because credentials were removed directly after checkout although they were still needed later.

## Release [0.1.4] - 2025-02-08

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.1.4...v0.1.3)

[0.1.4]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.1.4

### Fixed

- install cmd in docs-building actions. #26

## Release [0.1.3] - 2025-02-08

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.1.3...v0.1.2)

[0.1.3]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.1.3

### Fixed

- clean command should not remove README and init.py. #22

## Release [0.1.2] - 2025-02-06

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.1.2...v0.1.1)

[0.1.2]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.1.2

### Added

- copier validation for main_schema_class name. #21

## Release [0.1.1] - 2025-02-06

[Full changelog](https://github.com/dalito/linkml-project-copier/compare/v0.1.1...v0.1.0)

[0.1.1]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.1.1

### Added

* Add command groups to justfile by @dalito in #16
* Add dependabot for action-updates. #14

### Changed

* Improve updating by adding more files/dirs for copier to skip #11
* Update actions. #14

## Release [0.1.0] - 2025-01-19

[Full changelog](https://github.com/dalito/linkml-project-copier/commits/v0.1.0)

[0.1.0]: https://github.com/dalito/linkml-project-copier/releases/tag/v0.1.0

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
