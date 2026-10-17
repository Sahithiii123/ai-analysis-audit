"""Validate manual-paste response records and frozen prompt samples."""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path

import pandas as pd

if __package__:
    from .ai_output_utils import extract_prompt, extract_python_code, extract_response
    from .fetch_data import parse_arff
else:
    from ai_output_utils import extract_prompt, extract_python_code, extract_response
    from fetch_data import parse_arff

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    "01_bank_marketing",
    "02_telco_churn",
    "04_simpsons_paradox",
    "05_multiple_comparisons",
    "06_iris_control",
)
OLIST_CASE = "03_olist_delivery_reviews"
DATA_FILES = {
    "01_bank_marketing": "data/raw/01_bank_marketing/data.csv",
    "02_telco_churn": "data/raw/02_telco_churn/telco-customer-churn.arff",
    "04_simpsons_paradox": "data/raw/04_simpsons_paradox/UCBAdmissions.csv",
    "05_multiple_comparisons": "data/raw/05_multiple_comparisons/adult.arff",
    "06_iris_control": "data/raw/06_iris_control/data.csv",
}
METADATA_FIELDS = ("Model name", "Model version", "Interface", "Date/time", "Settings")
RESPONSE_HEADINGS = ("Analysis plan", "Runnable Python code", "Written conclusion")
SEED = 20261016


def has_response_heading(response: str, heading: str) -> bool:
    return (
        re.search(
            rf"^[ \t]*(?:###[ \t]+)?{re.escape(heading)}:?[ \t]*$",
            response,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        is not None
    )


def parse_csv_table(text: str) -> list[list[str]]:
    blocks = re.findall(
        r"^```csv[ \t]*\r?\n(.*?)^```[ \t]*$",
        text,
        flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if len(blocks) != 1:
        raise ValueError("Expected exactly one fenced CSV sample.")
    return list(csv.reader(io.StringIO(blocks[0])))


def check_prompt(case: str) -> list[str]:
    path = ROOT / "cases" / case / "ai_output" / "PROMPT_TO_PASTE.md"
    if not path.is_file():
        return [f"{case}: missing {path.relative_to(ROOT)}"]

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    for heading in ("## Data schema", "## 20-row random sample", "## Requested response"):
        if heading not in text:
            problems.append(f"{case}: missing prompt heading {heading!r}")
    if f"random_state={SEED}" not in text:
        problems.append(f"{case}: sample seed {SEED} is not documented")
    for heading in RESPONSE_HEADINGS:
        if f"### {heading}" not in text:
            problems.append(f"{case}: requested response heading {heading!r} is missing")

    try:
        rows = parse_csv_table(text)
    except ValueError as error:
        problems.append(f"{case}: {error}")
        return problems

    if len(rows) != 21:
        problems.append(f"{case}: sample has {max(len(rows) - 1, 0)} records; expected 20")
        return problems

    schema_fields = re.findall(r"^\| `([^`]+)` \|", text, flags=re.MULTILINE)
    if rows[0] != schema_fields:
        problems.append(f"{case}: sample header does not match the schema columns")

    data_path = ROOT / DATA_FILES[case]
    if data_path.is_file():
        if data_path.suffix == ".arff":
            payload = data_path.read_bytes()
            lines = payload.decode("utf-8-sig").splitlines()
            fields = parse_arff(payload)[2]
            data_start = next(
                index for index, line in enumerate(lines) if line.strip().lower() == "@data"
            )
            frame = pd.DataFrame(list(csv.reader(lines[data_start + 1 :])), columns=fields)
        else:
            frame = pd.read_csv(data_path, sep=None, engine="python")
        expected = frame.sample(n=20, random_state=SEED).to_csv(
            index=False,
            lineterminator="\n",
        ).strip()
        actual = parse_csv_table(text)
        actual_text = io.StringIO()
        csv.writer(actual_text, lineterminator="\n").writerows(actual)
        if actual_text.getvalue().strip() != expected:
            problems.append(f"{case}: sample differs from the fixed-seed sample of the real file")
    else:
        problems.append(f"{case}: source file unavailable; could not verify sample values")
    return problems


def check_record(case: str) -> list[str]:
    path = ROOT / "cases" / case / "ai_output" / "PASTE_HERE.md"
    if not path.is_file():
        return [f"{case}: missing {path.relative_to(ROOT)}"]
    record = path.read_text(encoding="utf-8")
    problems: list[str] = []

    for field in METADATA_FIELDS:
        match = re.search(rf"^- {re.escape(field)}:\s*(.*?)\s*$", record, flags=re.MULTILINE)
        if match is None or not match.group(1) or match.group(1).startswith("["):
            problems.append(f"{case}: metadata field {field!r} is missing or still a placeholder")

    try:
        supplied_prompt = extract_prompt(record)
        expected_prompt = (
            ROOT / "cases" / case / "ai_output" / "PROMPT_TO_PASTE.md"
        ).read_text(encoding="utf-8").strip()
        if supplied_prompt != expected_prompt:
            problems.append(f"{case}: exact prompt does not match PROMPT_TO_PASTE.md")
        response = extract_response(record)
        if not response or response.startswith("["):
            problems.append(f"{case}: verbatim model response is empty or still a placeholder")
        for heading in RESPONSE_HEADINGS:
            if not has_response_heading(response, heading):
                if heading == "Runnable Python code":
                    try:
                        extract_python_code(response)
                    except ValueError:
                        problems.append(f"{case}: response is missing heading {heading!r}")
                    continue
                problems.append(f"{case}: response is missing heading {heading!r}")
        extract_python_code(response)
    except ValueError as error:
        problems.append(f"{case}: {error}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "cases",
        nargs="*",
        choices=(*CASES, OLIST_CASE),
        help="case ids; defaults to the five registered cases",
    )
    parser.add_argument(
        "--check-prompts",
        action="store_true",
        help=(
            "check frozen prompts, schema/sample shape, and fixed-seed values "
            "without requiring model output"
        ),
    )
    arguments = parser.parse_args()
    selected_cases = arguments.cases or CASES
    if arguments.check_prompts:
        # Olist prompt is generated from real files by src/make_olist_prompt.py
        selected_cases = tuple(case for case in selected_cases if case != OLIST_CASE)
    problems: list[str] = []
    for case in selected_cases:
        problems.extend(check_prompt(case) if arguments.check_prompts else check_record(case))

    if problems:
        print("Validation failed:")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    action = "Prompt" if arguments.check_prompts else "Output"
    print(f"{action} validation passed for {len(selected_cases)} case(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())