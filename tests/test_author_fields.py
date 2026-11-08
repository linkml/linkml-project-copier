"""Author details with special characters must still render valid files."""

from __future__ import annotations

import sys

import pytest

from tests.helpers import generate_project

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib


@pytest.mark.parametrize(
    ("full_name", "email"),
    [
        ("Ann O'Brien", "ann@example.org"),
        ('Ann "Annie" Brien', "ann@example.org"),
        ("Ann \\x Brien", "ann\\x@example.org"),
        ("Ünï 🚀", "ann@example.org"),
    ],
)
def test_pyproject_authors_parse(tmp_path, full_name, email):
    project = generate_project(tmp_path / "project", {"full_name": full_name, "email": email})

    pyproject = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["authors"] == [{"name": full_name, "email": email}]


def test_config_escapes_author(tmp_path):
    project = generate_project(tmp_path / "project", {"full_name": 'Ann "$HOME" Brien'})

    config = (project / "config.public.mk").read_text(encoding="utf-8")
    assert 'LINKML_SCHEMA_AUTHOR="Ann \\"\\$HOME\\" Brien <test@example.org>"' in config
