"""Shared helpers for template tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from copier import run_copy

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

ALL_LICENSES = ["MIT", "BSD-3-Clause", "Apache-2.0", "MPL-2.0", "LGPL-3.0-only", "GPL-3.0-only"]

DEFAULT_DATA = {
    "project_name": "test-schema",
    "project_slug": "test_schema",
    "email": "test@example.org",
    "full_name": "Test User",
    "github_org": "test-org",
    "project_description": "A test project.",
    "existing_license_file": "",
    "license": "MIT",
    "copyright_year": "2025",
    "add_example": True,
    "gh_action_pypi": True,
    "gh_action_docs_preview": True,
    "use_sssom": False,
}


def generate_project(
    dest: Path,
    data_overrides: dict | None = None,
) -> Path:
    """Generate a project from the copier template.

    Args:
        dest: Directory where the project will be generated.
        data_overrides: Values to override in DEFAULT_DATA.

    Returns:
        Path to the generated project directory.
    """
    data = {**DEFAULT_DATA, **(data_overrides or {})}
    run_copy(
        str(TEMPLATE_ROOT),
        dest,
        data=data,
        defaults=True,
        unsafe=True,
        vcs_ref="HEAD",
    )
    return dest


def git_init(project_dir: Path) -> None:
    """Initialize a git repo with an initial commit (needed for dynamic versioning)."""
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )


def run_just(project_dir: Path, *args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run a just command in the given project directory."""
    # Remove VIRTUAL_ENV so the generated project's uv uses its own .venv
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    return subprocess.run(
        ["just", *args],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
