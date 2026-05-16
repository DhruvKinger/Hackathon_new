from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..git_tracker import GitHistoryTracker
from .common import ensure_repo_path, wrap_git_error


@click.command(name="chart")
@click.option("--repo", required=True, type=click.Path(path_type=Path), help="Repository path")
@click.option("--output", required=True, type=click.Path(path_type=Path), help="Output directory path")
@click.option("--depth", required=False, default=50, show_default=True, type=int, help="Commits to scan")
def chart_command(repo: Path, output: Path, depth: int) -> None:
    """Generate LOC and CC trend charts as PNG files."""
    repo_path = ensure_repo_path(str(repo))
    depth = min(max(depth, 1), 500)

    try:
        tracker = GitHistoryTracker(str(repo_path))
        history = tracker.collect_history(depth=depth)
    except Exception as exc:  # pragma: no cover
        raise wrap_git_error(exc)

    output.mkdir(parents=True, exist_ok=True)
    loc_chart = output / "loc_trend.png"
    cc_chart = output / "cc_trend.png"

    x_labels = []
    loc_series: dict[str, list[float]] = {}
    overall_cc: list[float] = []

    for index, item in enumerate(history):
        date_label = _date_label(item.date, index)
        x_labels.append(date_label)

        commit_cc_values = []
        for language, values in item.metrics.items():
            loc_series.setdefault(language, [0.0] * len(overall_cc))
            if len(loc_series[language]) < len(x_labels) - 1:
                loc_series[language].extend([0.0] * ((len(x_labels) - 1) - len(loc_series[language])))
            loc_series[language].append(float(values.get("loc", 0.0)))
            commit_cc_values.append(float(values.get("cc_avg", 0.0)))

        for language in loc_series:
            if len(loc_series[language]) < len(x_labels):
                loc_series[language].append(0.0)

        overall_cc.append(sum(commit_cc_values) / len(commit_cc_values) if commit_cc_values else 0.0)

    _plot_loc(loc_chart, x_labels, loc_series)
    _plot_cc(cc_chart, x_labels, overall_cc)

    click.echo(f"{loc_chart}\n{cc_chart}")


def _date_label(iso_date: str, index: int) -> str:
    try:
        return datetime.fromisoformat(iso_date).strftime("%Y-%m-%d")
    except ValueError:
        return str(index)


def _plot_loc(chart_path: Path, x_labels: list[str], loc_series: dict[str, list[float]]) -> None:
    plt.figure(figsize=(12, 6))
    for language, series in sorted(loc_series.items()):
        plt.plot(x_labels, series, marker="o", label=language)
    plt.title("LOC Trend by Language")
    plt.xlabel("Commit Date")
    plt.ylabel("LOC")
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(chart_path, format="png", dpi=120)
    plt.close()


def _plot_cc(chart_path: Path, x_labels: list[str], cc_series: list[float]) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(x_labels, cc_series, marker="o", color="#D1495B", label="Overall CC")
    plt.title("Cyclomatic Complexity Trend")
    plt.xlabel("Commit Date")
    plt.ylabel("Average CC")
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(chart_path, format="png", dpi=120)
    plt.close()
