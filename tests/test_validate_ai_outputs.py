"""Tests for manual-paste AI-output record validation."""

from __future__ import annotations

import pytest

from src.ai_output_utils import extract_python_code
from src.validate_ai_outputs import has_response_heading


@pytest.mark.parametrize(
    ("response", "heading"),
    [
        ("analysis plan:\n", "Analysis plan"),
        ("### ANALYSIS PLAN\n", "Analysis plan"),
        ("Runnable Python code:\n", "Runnable Python code"),
        ("  ### written conclusion:\n", "Written conclusion"),
    ],
)
def test_response_headings_accept_plain_text_and_markdown(
    response: str,
    heading: str,
) -> None:
    assert has_response_heading(response, heading)


def test_extract_python_code_from_plain_section_headings() -> None:
    response = (
        "analysis plan:\nReview the data.\n"
        "runnable python code:\nimport math\nprint(math.pi)\n"
        "written conclusion:\nThe code is reproducible.\n"
    )

    assert extract_python_code(response) == "import math\nprint(math.pi)"


def test_extract_python_code_when_plain_response_omits_code_heading() -> None:
    response = (
        "Analysis plan\nReview the data.\n\n"
        "import math\nprint(math.pi)\n\n"
        "Written conclusion\nThe code is reproducible.\n"
    )

    assert extract_python_code(response) == "import math\nprint(math.pi)"
