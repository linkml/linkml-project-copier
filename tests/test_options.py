"""Tests for boolean template options."""

from __future__ import annotations

import pytest


class TestWithoutExample:
    """With add_example=False, example-specific files should be absent."""

    ABSENT_FILES = [
        "src/test_schema/schema/test_schema.yaml",
        "tests/test_data.py",
        "tests/data/valid/Person-001.yaml",
        "tests/data/valid/PersonCollection-001.yaml",
        "tests/data/invalid/Person-002.yaml",
    ]

    PRESENT_FILES = [
        "pyproject.toml",
        "justfile",
        "config.public.mk",
        "src/test_schema/__init__.py",
        "src/test_schema/schema/README.md",
        "tests/__init__.py",
        "tests/data/README.md",
    ]

    @pytest.mark.parametrize("relpath", ABSENT_FILES)
    def test_file_absent(self, no_example_project, relpath):
        assert not (no_example_project / relpath).exists(), f"Should be absent: {relpath}"

    @pytest.mark.parametrize("relpath", PRESENT_FILES)
    def test_file_present(self, no_example_project, relpath):
        assert (no_example_project / relpath).exists(), f"Missing: {relpath}"


class TestWithoutPypiAction:
    """With gh_action_pypi=False, pypi-publish.yaml should be absent."""

    def test_pypi_publish_absent(self, no_pypi_project):
        assert not (no_pypi_project / ".github/workflows/pypi-publish.yaml").exists()

    def test_main_workflow_present(self, no_pypi_project):
        assert (no_pypi_project / ".github/workflows/main.yaml").exists()


class TestWithoutDocsPreview:
    """With gh_action_docs_preview=False, test_pages_build.yaml should be absent."""

    def test_pages_build_absent(self, no_docs_preview_project):
        assert not (
            no_docs_preview_project / ".github/workflows/test_pages_build.yaml"
        ).exists()

    def test_deploy_docs_present(self, no_docs_preview_project):
        assert (no_docs_preview_project / ".github/workflows/deploy-docs.yaml").exists()


class TestWithoutSssom:
    """With use_sssom=False (the default), all sssom/overlay assets should be absent."""

    ABSENT_FILES = [
        "sssom.justfile",
        "scripts/overlay_sssom.py",
        "src/test_schema/mappings/README.md",
        "src/test_schema/mappings/test_schema-schemaorg.sssom.tsv",
        "src/test_schema/mappings/test_schema-personstatus.sssom.tsv",
        "tests/test_overlay_sssom.py",
    ]

    @pytest.mark.parametrize("relpath", ABSENT_FILES)
    def test_file_absent(self, default_project, relpath):
        assert not (default_project / relpath).exists(), f"Should be absent: {relpath}"

    def test_sssom_dependency_absent(self, default_project):
        pyproject = (default_project / "pyproject.toml").read_text(encoding="utf-8")
        assert "sssom" not in pyproject
        assert "ruamel" not in pyproject
        dev_array = pyproject.split("dev = [", 1)[1].split("]", 1)[0]
        assert "\n\n" not in dev_array, "stray blank line in dev dependency array"

    def test_justfile_import_is_optional(self, default_project):
        # The main justfile always references sssom.justfile via an optional
        # import, so `just` works whether or not the file is present.
        assert 'import? "sssom.justfile"' in (default_project / "justfile").read_text(
            encoding="utf-8"
        )

    def test_ci_drift_gate_absent(self, default_project):
        workflow = (default_project / ".github/workflows/main.yaml").read_text(
            encoding="utf-8"
        )
        assert "overlay-sssom" not in workflow
        assert "${{ matrix.python-version }}" in workflow


class TestWithSssom:
    """With use_sssom=True (and default add_example=True), all sssom/overlay assets present."""

    PRESENT_FILES = [
        "sssom.justfile",
        "scripts/overlay_sssom.py",
        "src/test_schema/mappings/README.md",
        "src/test_schema/mappings/test_schema-schemaorg.sssom.tsv",
        "src/test_schema/mappings/test_schema-personstatus.sssom.tsv",
        "tests/test_overlay_sssom.py",
    ]

    @pytest.mark.parametrize("relpath", PRESENT_FILES)
    def test_file_present(self, sssom_project, relpath):
        assert (sssom_project / relpath).exists(), f"Missing: {relpath}"

    def test_overlay_script_is_executable(self, sssom_project):
        path = sssom_project / "scripts/overlay_sssom.py"
        assert path.stat().st_mode & 0o111, "overlay_sssom.py should be executable"

    def test_sssom_dependency_present(self, sssom_project):
        pyproject = (sssom_project / "pyproject.toml").read_text(encoding="utf-8")
        assert '"sssom' in pyproject
        assert "ruamel.yaml" in pyproject

    def test_justfile_recipes_present(self, sssom_project):
        justfile = (sssom_project / "sssom.justfile").read_text(encoding="utf-8")
        assert "gen-sssom:" in justfile
        assert "validate-sssom:" in justfile
        assert "overlay-sssom " in justfile
        assert "test-overlay-sssom:" in justfile
        # Just-syntax variables must survive rendering; Jinja tags must not leak.
        assert "{{dest}}" in justfile
        assert "{%" not in justfile

    def test_pyproject_dev_array_has_no_blank_lines(self, sssom_project):
        pyproject = (sssom_project / "pyproject.toml").read_text(encoding="utf-8")
        dev_array = pyproject.split("dev = [", 1)[1].split("]", 1)[0]
        assert "\n\n" not in dev_array, "stray blank line in dev dependency array"

    def test_readme_list_is_contiguous(self, sssom_project):
        readme = (sssom_project / "README.md").read_text(encoding="utf-8")
        assert "Python datamodel\n    * [mappings/]" in readme, (
            "mappings bullet must directly follow datamodel bullet "
            "(a blank line would split the Markdown list)"
        )

    def test_ci_drift_gate_present(self, sssom_project):
        workflow = (sssom_project / ".github/workflows/main.yaml").read_text(
            encoding="utf-8"
        )
        assert "just overlay-sssom --check" in workflow
        # GitHub Actions ${{ }} must survive; Jinja tags must not leak.
        assert "${{ matrix.python-version }}" in workflow
        assert "{% raw %}" not in workflow


class TestSssomWithoutExample:
    """With use_sssom=True and add_example=False, only example-specific assets are absent."""

    ABSENT_FILES = [
        "src/test_schema/mappings/test_schema-schemaorg.sssom.tsv",
        "src/test_schema/mappings/test_schema-personstatus.sssom.tsv",
        "tests/test_overlay_sssom.py",
    ]

    PRESENT_FILES = [
        "sssom.justfile",
        "scripts/overlay_sssom.py",
        "src/test_schema/mappings/README.md",
    ]

    @pytest.mark.parametrize("relpath", ABSENT_FILES)
    def test_file_absent(self, sssom_no_example_project, relpath):
        assert not (sssom_no_example_project / relpath).exists(), (
            f"Should be absent: {relpath}"
        )

    @pytest.mark.parametrize("relpath", PRESENT_FILES)
    def test_file_present(self, sssom_no_example_project, relpath):
        assert (sssom_no_example_project / relpath).exists(), f"Missing: {relpath}"

    def test_test_overlay_recipe_absent(self, sssom_no_example_project):
        # The test recipe would fail without the bundled test file (pytest
        # collects nothing) and its gen-python prerequisite needs a schema.
        justfile = (sssom_no_example_project / "sssom.justfile").read_text(
            encoding="utf-8"
        )
        assert "test-overlay-sssom" not in justfile
