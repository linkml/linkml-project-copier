"""Fixtures for linkml-project-copier template tests."""

from __future__ import annotations

import pytest

from tests.helpers import ALL_LICENSES, generate_project


# ---------------------------------------------------------------------------
# Session-scoped fixtures for structural tests (read-only, generated once)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def default_project(tmp_path_factory):
    """Project generated with all defaults and add_example=True."""
    dest = tmp_path_factory.mktemp("default")
    return generate_project(dest)


@pytest.fixture(scope="session")
def no_example_project(tmp_path_factory):
    """Project generated with add_example=False."""
    dest = tmp_path_factory.mktemp("no_example")
    return generate_project(dest, {"add_example": False})


@pytest.fixture(scope="session")
def no_pypi_project(tmp_path_factory):
    """Project generated with gh_action_pypi=False."""
    dest = tmp_path_factory.mktemp("no_pypi")
    return generate_project(dest, {"gh_action_pypi": False})


@pytest.fixture(scope="session")
def no_docs_preview_project(tmp_path_factory):
    """Project generated with gh_action_docs_preview=False."""
    dest = tmp_path_factory.mktemp("no_docs_preview")
    return generate_project(dest, {"gh_action_docs_preview": False})


@pytest.fixture(scope="session")
def sssom_project(tmp_path_factory):
    """Project generated with use_sssom=True."""
    dest = tmp_path_factory.mktemp("sssom")
    return generate_project(dest, {"use_sssom": True})


@pytest.fixture(scope="session")
def sssom_no_example_project(tmp_path_factory):
    """Project generated with use_sssom=True and add_example=False."""
    dest = tmp_path_factory.mktemp("sssom_no_example")
    return generate_project(dest, {"use_sssom": True, "add_example": False})


@pytest.fixture(scope="session", params=ALL_LICENSES)
def license_project(request, tmp_path_factory):
    """Project generated for each license type. Returns (license_name, project_path)."""
    license_name = request.param
    dest = tmp_path_factory.mktemp(f"license_{license_name}")
    project_path = generate_project(dest, {"license": license_name})
    return license_name, project_path
