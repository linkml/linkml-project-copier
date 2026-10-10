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
    """With use_sssom=False (the default), nothing of the SSSOM option is present."""

    ABSENT_FILES = [
        "sssom.justfile",
        "scripts/overlay_sssom.py",
        "src/test_schema/mappings/README.md",
        "src/test_schema/mappings/test_schema.sssom.tsv",
    ]

    @pytest.mark.parametrize("relpath", ABSENT_FILES)
    def test_file_absent(self, default_project, relpath):
        assert not (default_project / relpath).exists(), f"Should be absent: {relpath}"

    def test_sssom_dependencies_absent(self, default_project):
        pyproject = (default_project / "pyproject.toml").read_text(encoding="utf-8")
        assert "sssom" not in pyproject
        assert "ruamel" not in pyproject

    def test_ci_gate_absent(self, default_project):
        workflow = (default_project / ".github/workflows/main.yaml").read_text(encoding="utf-8")
        assert "overlay-sssom" not in workflow
        # The GitHub Actions expressions must survive the Jinja rendering.
        assert "${{ matrix.python-version }}" in workflow


class TestWithSssom:
    """With use_sssom=True, the recipes, script, README and example file are present."""

    PRESENT_FILES = [
        "sssom.justfile",
        "scripts/overlay_sssom.py",
        "src/test_schema/mappings/README.md",
        "src/test_schema/mappings/test_schema.sssom.tsv",
    ]

    @pytest.mark.parametrize("relpath", PRESENT_FILES)
    def test_file_present(self, sssom_project, relpath):
        assert (sssom_project / relpath).exists(), f"Missing: {relpath}"

    def test_sssom_dependencies_present(self, sssom_project):
        pyproject = (sssom_project / "pyproject.toml").read_text(encoding="utf-8")
        assert '"sssom>=' in pyproject
        assert '"ruamel.yaml>=' in pyproject

    def test_recipes_present(self, sssom_project):
        recipes = (sssom_project / "sssom.justfile").read_text(encoding="utf-8")
        for recipe in ("validate-sssom:", "overlay-sssom *FLAGS:", "gen-sssom:"):
            assert recipe in recipes, f"Missing recipe: {recipe}"
        justfile = (sssom_project / "justfile").read_text(encoding="utf-8")
        assert 'import? "sssom.justfile"' in justfile

    def test_example_file_names_the_schema(self, sssom_project):
        tsv = (sssom_project / "src/test_schema/mappings/test_schema.sssom.tsv").read_text(
            encoding="utf-8"
        )
        assert "#  test_schema: https://w3id.org/test-org/test-schema/" in tsv
        assert "test_schema:PersonStatus#UNKNOWN\tskos:exactMatch\tNCIT:C17998" in tsv
        assert "{{" not in tsv

    def test_ci_gate_present(self, sssom_project):
        workflow = (sssom_project / ".github/workflows/main.yaml").read_text(encoding="utf-8")
        assert "just overlay-sssom --check" in workflow
        assert "${{ matrix.python-version }}" in workflow
        assert "{% raw %}" not in workflow


class TestSssomWithoutExample:
    """With use_sssom=True and add_example=False, only the example file is absent."""

    PRESENT_FILES = [
        "sssom.justfile",
        "scripts/overlay_sssom.py",
        "src/test_schema/mappings/README.md",
    ]

    def test_example_file_absent(self, sssom_no_example_project):
        tsv = sssom_no_example_project / "src/test_schema/mappings/test_schema.sssom.tsv"
        assert not tsv.exists()

    @pytest.mark.parametrize("relpath", PRESENT_FILES)
    def test_file_present(self, sssom_no_example_project, relpath):
        assert (sssom_no_example_project / relpath).exists(), f"Missing: {relpath}"
