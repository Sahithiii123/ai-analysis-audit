"""Shared parsing helpers for manual-paste AI output records."""

from __future__ import annotations

import re

RESPONSE_HEADING = re.compile(
    r"^[ \t]*(?:###[ \t]+)?"
    r"(?P<heading>Analysis plan|Runnable Python code|Written conclusion):?[ \t]*$",
    flags=re.MULTILINE | re.IGNORECASE,
)


def extract_prompt(record: str) -> str:
    match = re.search(
        r"^## Exact prompt sent[ \t]*\r?\n(.*?)(?=^## Verbatim model response[ \t]*$)",
        record,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise ValueError("Missing 'Exact prompt sent' section.")
    return match.group(1).strip()


def extract_response(record: str) -> str:
    match = re.search(
        r"^## Verbatim model response[ \t]*\r?\n(.*)\Z",
        record,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise ValueError("Missing 'Verbatim model response' section.")
    return match.group(1).strip()


def extract_python_code(response: str) -> str:
    headings = list(RESPONSE_HEADING.finditer(response))
    code_heading = next(
        (
            heading
            for heading in headings
            if heading.group("heading").casefold() == "runnable python code"
        ),
        None,
    )
    if code_heading is not None:
        section_end = next(
            (heading.start() for heading in headings if heading.start() > code_heading.start()),
            len(response),
        )
        section = response[code_heading.end() : section_end]
    else:
        analysis_heading = next(
            (
                heading
                for heading in headings
                if heading.group("heading").casefold() == "analysis plan"
            ),
            None,
        )
        conclusion_heading = next(
            (
                heading
                for heading in headings
                if heading.group("heading").casefold() == "written conclusion"
                and (analysis_heading is None or heading.start() > analysis_heading.start())
            ),
            None,
        )
        if analysis_heading is None or conclusion_heading is None:
            raise ValueError("Missing 'Runnable Python code' response section.")
        section = response[analysis_heading.end() : conclusion_heading.start()]
        code_start = re.search(
            r"^(?:from[ \t]+[\w.]+[ \t]+import\b|import[ \t]+[\w.]+)",
            section,
            flags=re.MULTILINE,
        )
        if code_start is None:
            raise ValueError("Missing Python code in the response.")
        section = section[code_start.start() :]

    blocks = re.findall(
        r"^```python[ \t]*\r?\n(.*?)^```[ \t]*$",
        section,
        flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if len(blocks) == 1 and blocks[0].strip():
        return blocks[0]
    if re.search(r"^```", section, flags=re.MULTILINE):
        raise ValueError("Expected exactly one non-empty fenced Python code block.")
    code = section.strip()
    if not code:
        raise ValueError("Expected non-empty Python code.")
    return code