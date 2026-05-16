import json
from pathlib import Path

from click.testing import CliRunner

from metrics_cli.cli import main


SAMPLE_REPO = str(Path(__file__).resolve().parents[1] / "data" / "sample_repo")


def test_scan_command_outputs_json():
    runner = CliRunner()
    result = runner.invoke(main, ["scan", "--repo", SAMPLE_REPO])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "languages" in payload
    assert "functions" in payload


def test_history_command_has_commits_in_order():
    runner = CliRunner()
    result = runner.invoke(main, ["history", "--repo", SAMPLE_REPO, "--depth", "5"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    history = payload["history"]
    assert len(history) == 5

    dates = [item["date"] for item in history]
    assert dates == sorted(dates)


def test_report_csv_headers(tmp_path):
    runner = CliRunner()
    output_file = tmp_path / "report.csv"

    result = runner.invoke(
        main,
        ["report", "--repo", SAMPLE_REPO, "--output", str(output_file), "--format", "csv"],
    )

    assert result.exit_code == 0
    assert output_file.exists()
    first_line = output_file.read_text(encoding="utf-8").splitlines()[0]
    assert first_line == "language,files,loc,comment_lines,blank_lines,cc_avg"


def test_chart_creates_png_files(tmp_path):
    runner = CliRunner()
    out_dir = tmp_path / "charts"

    result = runner.invoke(main, ["chart", "--repo", SAMPLE_REPO, "--output", str(out_dir), "--depth", "5"])

    assert result.exit_code == 0
    assert (out_dir / "loc_trend.png").exists()
    assert (out_dir / "cc_trend.png").exists()
