from __future__ import annotations

from pathlib import Path

import click

from ..metrics import LanguageAnalyzer, function_list_to_dicts, metrics_to_language_summary
from .common import emit_payload, ensure_repo_path, scan_date_iso


@click.command(name="scan")
@click.option("--repo", required=True, type=click.Path(path_type=Path), help="Repository path")
@click.option("--output", required=False, type=click.Path(path_type=Path), help="Output JSON file path")
def scan_command(repo: Path, output: Path | None) -> None:
    """Scan a repository at the current commit and return metrics JSON."""
    repo_path = ensure_repo_path(str(repo))

    analyzer = LanguageAnalyzer()
    language_totals, functions = analyzer.scan_repository(str(repo_path))

    payload = {
        "repository": str(repo_path.resolve()),
        "scan_date": scan_date_iso(),
        "languages": metrics_to_language_summary(language_totals),
        "functions": function_list_to_dicts(functions),
        "history": [],
    }
    emit_payload(payload, str(output) if output else None)
