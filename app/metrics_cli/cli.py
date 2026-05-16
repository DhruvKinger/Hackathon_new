from __future__ import annotations

import click

from .commands.chart import chart_command
from .commands.history import history_command
from .commands.report import report_command
from .commands.scan import scan_command


@click.group(name="metrics_cli")
def main() -> None:
    """Code metrics CLI with git history tracking."""


main.add_command(scan_command)
main.add_command(history_command)
main.add_command(report_command)
main.add_command(chart_command)
