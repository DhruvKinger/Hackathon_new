from metrics_cli.metrics import LanguageAnalyzer, metrics_to_language_summary


def test_python_metrics_counting(tmp_path):
    source = tmp_path / "demo.py"
    source.write_text(
        """# header\n\n
def fn(a):\n    if a:\n        return 1\n    return 0\n""",
        encoding="utf-8",
    )

    analyzer = LanguageAnalyzer()
    result = analyzer.analyze_content(source.read_text(encoding="utf-8"), "demo.py", "Python")

    assert result.files == 1
    assert result.loc == 7
    assert result.comment_lines == 1
    assert result.blank_lines == 2
    assert any(f.function == "fn" for f in result.functions)


def test_language_summary_cc_avg():
    analyzer = LanguageAnalyzer()
    language_totals, _ = analyzer.scan_repository("data/sample_repo")

    summary = metrics_to_language_summary(language_totals)
    assert "Python" in summary
    assert summary["Python"]["files"] >= 1
    assert summary["Python"]["cc_avg"] >= 1
