"""Turn a pytest JUnit report into a Markdown test record.

    python -m pytest -q -W ignore --junitxml=pytest-report.xml
    python -m evaluation.make_test_record pytest-report.xml ../docs/evidence/test_record.md

Expected behaviour is read from each test's name (and docstring if present); the actual result
is what pytest reported. The corrective-action column is left for the developer to fill in.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date


def humanise(name):
    return name.removeprefix("test_").replace("_", " ").capitalize()


def main(report, out):
    suite = ET.parse(report).getroot()
    rows, counts = [], {"passed": 0, "failed": 0, "skipped": 0}
    for case in suite.iter("testcase"):
        module = case.get("classname", "").split(".")[-1]
        status = "failed" if case.find("failure") is not None or case.find("error") is not None else (
            "skipped" if case.find("skipped") is not None else "passed")
        counts[status] += 1
        rows.append((module, case.get("name"), status))
    rows.sort()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    lines = [
        "# Backend automated test record", "",
        f"Date: {date.today().isoformat()} | Commit: {commit} | Runner: pytest (in-memory SQLite)", "",
        f"Total: {len(rows)} | Passed: {counts['passed']} | Failed: {counts['failed']} | Skipped: {counts['skipped']}", "",
        "| Module | Test | Expected behaviour | Actual | Corrective action |", "|---|---|---|---|---|",
    ]
    for module, name, status in rows:
        lines.append(f"| {module} | `{name}` | {humanise(name)} | {status} | {'-' if status == 'passed' else 'TBD'} |")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
