"""Integration tests that run just commands in generated projects."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from tests.helpers import generate_project, git_init, run_just

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def integration_project(tmp_path_factory):
    """Generate a project with git init and install deps for integration testing."""
    dest = tmp_path_factory.mktemp("integration")
    project = generate_project(dest)
    git_init(project)
    # Install dependencies upfront so individual tests don't depend on order
    result = run_just(project, "install")
    if result.returncode != 0:
        pytest.fail(
            f"just install failed during fixture setup:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return project


def test_just_install(integration_project):
    """Verify that just install succeeds (already run in fixture, re-run is idempotent)."""
    result = run_just(integration_project, "install")
    assert result.returncode == 0, (
        f"just install failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.skipif(
    sys.version_info >= (3, 13),
    reason="linkml's ShEx generator crashes on Python 3.13 (pyjsg incompatibility)",
)
def test_just_test(integration_project):
    result = run_just(integration_project, "test")
    assert result.returncode == 0, (
        f"just test failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_just_lint(integration_project):
    # just lint exits 1 on warnings, 2 on errors — only errors are failures
    result = run_just(integration_project, "lint")
    assert result.returncode < 2, (
        f"just lint found errors:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    # Verify exact warning/error counts via JSON output
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    lint_json = subprocess.run(
        ["uv", "run", "linkml-lint", "--format", "json", "src/test_schema/schema"],
        cwd=integration_project,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    problems = json.loads(lint_json.stdout)
    errors = [p for p in problems if p["level"] == "error"]
    warnings = [p for p in problems if p["level"] == "warning"]
    assert len(errors) == 0, f"Expected 0 lint errors, got {len(errors)}: {errors}"
    assert len(warnings) == 4, (
        f"Expected 4 lint warnings, got {len(warnings)}: {warnings}"
    )


def test_just_gen_doc(integration_project):
    result = run_just(integration_project, "gen-doc")
    assert result.returncode == 0, (
        f"just gen-doc failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_just_gen_project_owl_follows_config(integration_project):
    """The OWL file holds what config.yaml's owl section asks for."""
    result = run_just(integration_project, "gen-project")
    assert result.returncode == 0, (
        f"just gen-project failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    owl = (integration_project / "project" / "owl" / "test_schema.owl.ttl").read_text(
        encoding="utf-8"
    )
    # add_root_classes: true makes each class a subclass of linkml:ClassDefinition.
    assert "linkml:ClassDefinition" in owl
    # gen-project names the ontology by the schema's id, without a file suffix.
    assert ".owl.ttl>" not in owl
