from __future__ import annotations

import csv
from pathlib import Path

import click

from ..metrics import LanguageAnalyzer, function_list_to_dicts, metrics_to_language_summary
from .common import ensure_repo_path, scan_date_iso, to_json


@click.command(name="report")
@click.option("--repo", required=True, type=click.Path(path_type=Path), help="Repository path")
@click.option("--output", required=True, type=click.Path(path_type=Path), help="Output file path")
@click.option(
    "--format",
    "report_format",
    required=False,
    default="json",
    show_default=True,
    type=click.Choice(["json", "csv"], case_sensitive=False),
    help="Report output format",
)
def report_command(repo: Path, output: Path, report_format: str) -> None:
    """Generate summary report in JSON or CSV."""
    repo_path = ensure_repo_path(str(repo))
    analyzer = LanguageAnalyzer()
    language_totals, functions = analyzer.scan_repository(str(repo_path))
    summary = metrics_to_language_summary(language_totals)

    output.parent.mkdir(parents=True, exist_ok=True)

    if report_format.lower() == "csv":
        with output.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["language", "files", "loc", "comment_lines", "blank_lines", "cc_avg"])
            for language, values in summary.items():
                writer.writerow(
                    [
                        language,
                        values["files"],
                        values["loc"],
                        values["comment_lines"],
                        values["blank_lines"],
                        values["cc_avg"],
                    ]
                )
        click.echo(str(output))
        return

    payload = {
        "repository": str(repo_path.resolve()),
        "scan_date": scan_date_iso(),
        "languages": summary,
        "functions": function_list_to_dicts(functions),
        "history": [],
    }
    output.write_text(to_json(payload), encoding="utf-8")
    click.echo(str(output))
