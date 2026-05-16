from __future__ import annotations

from pathlib import Path

import click

from ..git_tracker import GitHistoryTracker
from .common import emit_payload, ensure_repo_path, wrap_git_error


@click.command(name="history")
@click.option("--repo", required=True, type=click.Path(path_type=Path), help="Repository path")
@click.option("--output", required=False, type=click.Path(path_type=Path), help="Output JSON file path")
@click.option("--depth", required=False, default=50, show_default=True, type=int, help="Commits to scan")
def history_command(repo: Path, output: Path | None, depth: int) -> None:
    """Track metrics across git history."""
    repo_path = ensure_repo_path(str(repo))
    depth = min(max(depth, 1), 500)

    try:
        tracker = GitHistoryTracker(str(repo_path))
        history = tracker.collect_history(depth=depth)
    except Exception as exc:  # pragma: no cover - click error wrapping
        raise wrap_git_error(exc)

    payload = {
        "repository": str(repo_path.resolve()),
        "history": [
            {
                "commit": item.commit,
                "date": item.date,
                "author": item.author,
                "metrics": item.metrics,
            }
            for item in history
        ],
    }

    emit_payload(payload, str(output) if output else None)
