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


# ---------------------------------------------------------------------------
# use_sssom=True project
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sssom_integration_project(tmp_path_factory):
    """Generate a use_sssom=True project with git init and installed deps."""
    dest = tmp_path_factory.mktemp("sssom_integration")
    project = generate_project(dest, {"use_sssom": True})
    git_init(project)
    result = run_just(project, "install")
    if result.returncode != 0:
        pytest.fail(
            f"just install failed during fixture setup:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return project


def _restore_schema(project):
    """Discard overlay edits so each test sees the pristine generated schema."""
    subprocess.run(
        ["git", "checkout", "--", "src/test_schema/schema"],
        cwd=project,
        check=True,
        capture_output=True,
    )


def test_just_gen_and_validate_sssom(sssom_integration_project):
    result = run_just(sssom_integration_project, "validate-sssom")
    assert result.returncode == 0, (
        f"just validate-sssom failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    tsv = sssom_integration_project / "project/sssom/test_schema.sssom.tsv"
    assert tsv.is_file(), "gen-sssom did not produce the expected TSV"


def test_just_test_overlay_sssom(sssom_integration_project):
    result = run_just(sssom_integration_project, "test-overlay-sssom")
    assert result.returncode == 0, (
        f"just test-overlay-sssom failed:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_sssom_drift_lifecycle(sssom_integration_project):
    """The CI drift gate: check fails on a fresh project, passes after apply."""
    project = sssom_integration_project
    try:
        check_fresh = run_just(project, "overlay-sssom", "--check")
        assert check_fresh.returncode == 1, (
            f"expected drift on fresh project:\n"
            f"stdout: {check_fresh.stdout}\nstderr: {check_fresh.stderr}"
        )
        assert "Verification FAILED" in check_fresh.stdout + check_fresh.stderr

        apply = run_just(project, "overlay-sssom")
        assert apply.returncode == 0, (
            f"just overlay-sssom failed:\nstdout: {apply.stdout}\nstderr: {apply.stderr}"
        )

        check_synced = run_just(project, "overlay-sssom", "--check")
        assert check_synced.returncode == 0, (
            f"expected in-sync after apply:\n"
            f"stdout: {check_synced.stdout}\nstderr: {check_synced.stderr}"
        )
    finally:
        _restore_schema(project)


def test_just_setup_applies_sssom_overlay(sssom_integration_project):
    """_setup_part2 applies the overlay, so setup leaves the project in sync."""
    project = sssom_integration_project
    try:
        result = run_just(project, "_setup_part2")
        assert result.returncode == 0, (
            f"just _setup_part2 failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        check = run_just(project, "overlay-sssom", "--check")
        assert check.returncode == 0, (
            f"project not in sync after setup:\n"
            f"stdout: {check.stdout}\nstderr: {check.stderr}"
        )
    finally:
        _restore_schema(project)
