"""Structural tests for default project generation."""

from __future__ import annotations

import ast
import sys

import yaml
import pytest

from tests.helpers import generate_project

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib


# Files expected in a default project (add_example=True, all actions enabled)
EXPECTED_FILES = [
    # Root config files
    ".editorconfig",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".yamllint.yaml",
    "config.public.mk",
    "config.yaml",
    "justfile",
    "project.justfile",
    "pyproject.toml",
    "LICENSE",
    "README.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "mkdocs.yml",
    ".copier-answers.yml",
    # GitHub
    ".github/dependabot.yml",
    ".github/workflows/deploy-docs.yaml",
    ".github/workflows/main.yaml",
    ".github/workflows/pypi-publish.yaml",
    ".github/workflows/test_pages_build.yaml",
    # Docs
    "docs/about.md",
    "docs/index.md",
    "docs/elements/.gitkeep",
    "docs/js/extra-loader.js",
    "docs/templates-linkml/README.md",
    # Source
    "src/test_schema/__init__.py",
    "src/test_schema/_version.py",
    "src/test_schema/datamodel/__init__.py",
    "src/test_schema/schema/README.md",
    "src/test_schema/schema/test_schema.yaml",
    # Tests (in generated project)
    "tests/__init__.py",
    "tests/test_data.py",
    "tests/data/README.md",
    "tests/data/valid/.gitkeep",
    "tests/data/valid/Person-001.yaml",
    "tests/data/valid/PersonCollection-001.yaml",
    "tests/data/invalid/.gitkeep",
    "tests/data/invalid/Person-002.yaml",
    "tests/data/problem/valid/.gitkeep",
    "tests/data/problem/invalid/.gitkeep",
    # Examples
    "examples/README.md",
]


class TestDefaultProjectStructure:
    """Verify that expected files exist in the default generated project."""

    @pytest.mark.parametrize("relpath", EXPECTED_FILES)
    def test_file_exists(self, default_project, relpath):
        assert (default_project / relpath).exists(), f"Missing: {relpath}"


class TestNoJinjaArtifacts:
    """Verify that no Jinja artifacts remain in the generated project."""

    def test_no_jinja_extension_files(self, default_project):
        jinja_files = list(default_project.rglob("*.jinja"))
        assert jinja_files == [], f"Jinja files remain: {jinja_files}"

    def test_no_unexpanded_markers(self, default_project):
        """No {{ }} or {% %} markers should remain in generated text files.

        GitHub Actions workflow files are excluded because they use ${{ }}
        syntax which is GitHub Actions expression syntax, not Jinja.
        """
        text_extensions = {".py", ".toml", ".yaml", ".yml", ".md", ".mk", ".cfg", ".txt"}
        # GitHub Actions workflows legitimately use ${{ }} syntax
        excluded_dirs = {".github"}
        failures = []
        for path in default_project.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in text_extensions:
                continue
            rel = path.relative_to(default_project)
            if rel.parts[0] in excluded_dirs:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for marker in ("{{", "}}", "{%", "%}"):
                if marker in content:
                    failures.append(f"{rel} contains '{marker}'")
                    break
        assert failures == [], "Unexpanded Jinja markers found:\n" + "\n".join(failures)


class TestPyprojectToml:
    """Validate generated pyproject.toml content."""

    @pytest.fixture(scope="class")
    def pyproject(self, default_project):
        return tomllib.loads((default_project / "pyproject.toml").read_text(encoding="utf-8"))

    def test_project_name(self, pyproject):
        assert pyproject["project"]["name"] == "test_schema"

    def test_description(self, pyproject):
        assert pyproject["project"]["description"] == "A test project."

    def test_license(self, pyproject):
        assert pyproject["project"]["license"] == "MIT"

    def test_authors(self, pyproject):
        authors = pyproject["project"]["authors"]
        assert len(authors) == 1
        assert authors[0]["name"] == "Test User"
        assert authors[0]["email"] == "test@example.org"

    def test_linkml_runtime_dependency(self, pyproject):
        deps = pyproject["project"]["dependencies"]
        assert any("linkml-runtime" in d for d in deps)

    def test_dynamic_version(self, pyproject):
        assert "version" in pyproject["project"]["dynamic"]


class TestSchemaYaml:
    """Validate the generated example schema."""

    @pytest.fixture(scope="class")
    def schema(self, default_project):
        return yaml.safe_load(
            (default_project / "src/test_schema/schema/test_schema.yaml").read_text(
                encoding="utf-8"
            )
        )

    def test_schema_name(self, schema):
        assert schema["name"] == "test-schema"

    def test_schema_license(self, schema):
        assert schema["license"] == "MIT"

    def test_classes_present(self, schema):
        classes = schema["classes"]
        assert "Person" in classes
        assert "NamedThing" in classes
        assert "PersonCollection" in classes


class TestConfigPublicMk:
    """Validate config.public.mk values."""

    @pytest.fixture(scope="class")
    def config_lines(self, default_project):
        return (default_project / "config.public.mk").read_text(encoding="utf-8")

    def test_schema_name(self, config_lines):
        assert 'LINKML_SCHEMA_NAME="test_schema"' in config_lines

    def test_schema_source_dir(self, config_lines):
        assert 'LINKML_SCHEMA_SOURCE_DIR="src/test_schema/schema"' in config_lines


class TestCopierAnswers:
    """Validate .copier-answers.yml content."""

    @pytest.fixture(scope="class")
    def answers(self, default_project):
        return yaml.safe_load(
            (default_project / ".copier-answers.yml").read_text(encoding="utf-8")
        )

    def test_project_slug(self, answers):
        assert answers["project_slug"] == "test_schema"

    def test_project_name(self, answers):
        assert answers["project_name"] == "test-schema"

    def test_add_example(self, answers):
        assert answers["add_example"] is True

    def test_github_org(self, answers):
        assert answers["github_org"] == "test-org"


class TestAwkwardDescription:
    """A description with special characters must still render valid files."""

    @pytest.mark.parametrize(
        ("description", "summary"),
        [
            ("first\nsecond", "first second"),
            ("first\r\nsecond", "first second"),
            ('A "quoted" word', 'A "quoted" word'),
            ("path C:\\new\\users", "path C:\\new\\users"),
            ("  Ünï  🚀  ", "Ünï 🚀"),
            ("  first\nsecond", "first second"),
            ('a """ b', 'a """ b'),
            ("costs $HOME", "costs $HOME"),
        ],
    )
    def test_files_parse(self, tmp_path, description, summary):
        project = generate_project(tmp_path / "project", {"project_description": description})

        pyproject = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
        assert pyproject["project"]["description"] == summary

        init = (project / "src/test_schema/__init__.py").read_text(encoding="utf-8")
        docstring = ast.get_docstring(ast.parse(init))
        assert docstring.split() == ["test-schema.", *description.split()]

        config = (project / "config.public.mk").read_text(encoding="utf-8")
        assert "$HOME" not in config.replace("\\$HOME", "")

        schema_path = project / "src/test_schema/schema/test_schema.yaml"
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        assert schema["description"].split() == description.split()
