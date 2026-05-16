from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import click

from ..git_tracker import GitTrackerError


class InvalidRepoError(click.ClickException):
    exit_code = 1


class GitOperationError(click.ClickException):
    exit_code = 2


def ensure_repo_path(repo: str) -> Path:
    path = Path(repo)
    if not path.exists() or not path.is_dir():
        raise InvalidRepoError(f"Invalid repository path: {repo}")
    return path


def to_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def emit_payload(payload: Dict[str, Any], output: str | None) -> None:
    rendered = to_json(payload)
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        click.echo(rendered)


def scan_date_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def wrap_git_error(exc: Exception) -> GitOperationError:
    if isinstance(exc, GitTrackerError):
        return GitOperationError(str(exc))
    return GitOperationError(f"Git operation failed: {exc}")
