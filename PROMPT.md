# Code Metrics CLI Tool with Git History Tracking

## Description

Build a command-line tool that analyzes software repositories to measure code metrics across multiple programming languages. The tool MUST:

- Scan directories and count lines of code (LOC), comment lines, blank lines, and file counts per language
- Measure cyclomatic complexity (CC) for functions across supported languages
- Track metrics over Git history to show evolution across commits
- Generate trend reports (JSON and CSV formats)
- Generate trend charts (as PNG or SVG files)
- Run fully offline with bundled sample repositories for testing

The tool is designed for engineering managers and architects who need objective codebase metrics without relying on external services.

## Tech Stack

- Language: Python 3.10+
- Testing: pytest
- CLI Framework: click 8.x
- Chart Generation: matplotlib
- Git operations: GitPython
- Cyclomatic complexity: radon (for Python) + regex-based extraction for JS/TS
- Data formats: JSON, CSV
- No external APIs or network calls

## CLI Interface

- Invocation: python -m metrics_cli <command> [options]
- Commands: scan, history, report, chart
- Required options: --repo for all commands
- Depth option: --depth default 50, max 500
- Report format option: --format <json|csv>

## Expected Outputs

- JSON summary with repository, scan_date, languages, functions, and history arrays
- CSV summary with: language, files, loc, comment_lines, blank_lines, cc_avg
- PNG charts for LOC and CC trends across history

## Exit Codes

- 0 for success
- 1 for invalid repository path
- 2 for Git operation errors

## Offline Constraint

- Fully offline execution only
- Bundled sample repository required at data/sample_repo
