#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


def parse_status(stdout_text: str, stderr_text: str):
    tests = []

    combined = stdout_text + "\n" + stderr_text

    # Verbose pytest lines look like:
    # tests/test_mod.py::test_name PASSED [ 50%]
    case_line_pattern = re.compile(
        r"^(\S.*?::\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)(?:\s+\[.*\])?\s*$",
        re.MULTILINE,
    )
    for name, status in case_line_pattern.findall(combined):
        tests.append({"name": name.strip(), "status": status.strip()})

    # Summary lines for failures/errors.
    summary_pattern = re.compile(r"^(FAILED|ERROR)\s+([^\s]+)", re.MULTILINE)
    for status, name in summary_pattern.findall(combined):
        tests.append({"name": name.strip(), "status": status.strip()})

    # Fallback parser for terse output where test names are not printed for passes.
    if not tests:
        short_fail = re.findall(r"\b([FE])\b", stdout_text)
        for idx, marker in enumerate(short_fail, start=1):
            status = "FAILED" if marker == "F" else "ERROR"
            tests.append({"name": f"unknown_test_{idx}", "status": status})

    unique = {}
    for item in tests:
        unique[item["name"]] = item

    ordered = [unique[name] for name in sorted(unique)]
    return {"tests": ordered}


def main():
    if len(sys.argv) != 4:
        print("Usage: parsing.py <stdout.txt> <stderr.txt> <output.json>", file=sys.stderr)
        sys.exit(2)

    stdout_path = Path(sys.argv[1])
    stderr_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    stdout_text = stdout_path.read_text(encoding="utf-8", errors="ignore") if stdout_path.exists() else ""
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="ignore") if stderr_path.exists() else ""

    payload = parse_status(stdout_text, stderr_text)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
