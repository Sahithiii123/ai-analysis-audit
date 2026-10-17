"""Freeze the Olist prompt: schema plus fixed-seed 20-row samples from the real CSVs.

Writes cases/03_olist_delivery_reviews/ai_output/PROMPT_TO_PASTE.md and a
PASTE_HERE.md skeleton that already embeds that exact prompt. Refuses to
overwrite an existing prompt unless --force is given, so a frozen prompt
cannot change silently after a model response has been collected.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CASE = "03_olist_delivery_reviews"
SEED = 20261016
QUESTION = (
    "Does late delivery associate with review scores, "
    "and how do seller-level late-delivery rates vary?"
)

SCHEMA: dict[str, dict[str, str]] = {
    "olist_customers_dataset.csv": {
        "customer_id": "Customer key used to join to orders.",
        "customer_unique_id": "Unique identifier of a customer.",
        "customer_zip_code_prefix": "First five digits of the customer zip code.",
        "customer_city": "Customer city name.",
        "customer_state": "Customer state.",
    },
    "olist_orders_dataset.csv": {
        "order_id": "Unique order identifier.",
        "customer_id": "Key to the customers file.",
        "order_status": "Order status (for example delivered, shipped, canceled).",
        "order_purchase_timestamp": "Purchase timestamp.",
        "order_approved_at": "Payment approval timestamp.",
        "order_delivered_carrier_date": "Timestamp the order was handed to the carrier.",
        "order_delivered_customer_date": "Actual delivery date to the customer.",
        "order_estimated_delivery_date": "Estimated delivery date shown at purchase.",
    },
    "olist_order_items_dataset.csv": {
        "order_id": "Order identifier.",
        "order_item_id": "Sequential item number within an order.",
        "product_id": "Product identifier.",
        "seller_id": "Seller identifier.",
        "shipping_limit_date": "Seller shipping limit date for the item.",
        "price": "Item price.",
        "freight_value": "Item freight cost.",
    },
    "olist_order_reviews_dataset.csv": {
        "review_id": "Review identifier.",
        "order_id": "Order identifier.",
        "review_score": "Satisfaction score from 1 to 5.",
        "review_comment_title": "Optional review title.",
        "review_comment_message": "Optional review comment.",
        "review_creation_date": "Date the satisfaction survey was sent.",
        "review_answer_timestamp": "Satisfaction survey answer timestamp.",
    },
    "olist_sellers_dataset.csv": {
        "seller_id": "Seller identifier.",
        "seller_zip_code_prefix": "First five digits of the seller zip code.",
        "seller_city": "Seller city name.",
        "seller_state": "Seller state.",
    },
}

RESPONSE_SECTION = """## Requested response

Please return exactly these three sections:

### Analysis plan

### Runnable Python code

Provide one Python code block that reads the complete dataset from the paths above \
and can run from the project root.

### Written conclusion
"""


def build_prompt(raw_dir: Path) -> str:
    rel = f"data/raw/{CASE}"
    parts = [f"# User request\n\n{QUESTION}\n"]
    files = "\n".join(f"- `{rel}/{name}`" for name in SCHEMA)
    parts.append(
        "## Data files\n\n"
        f"The complete dataset is five CSV files, relative to the project root:\n\n{files}\n\n"
        "Please read the full files in your Python code; the samples below are only previews.\n"
    )

    schema_blocks = ["## Data schema\n"]
    sample_blocks = [
        "## 20-row random samples\n\n"
        f"Each sample was drawn from the real file with pandas "
        f"`sample(n=20, random_state={SEED})`.\n"
    ]
    for name, columns in SCHEMA.items():
        frame = pd.read_csv(raw_dir / name)
        if list(frame.columns) != list(columns):
            raise SystemExit(
                f"{name}: columns {list(frame.columns)} differ from the expected schema "
                f"{list(columns)}; refusing to build the prompt."
            )
        rows = "\n".join(f"| `{col}` | {desc} |" for col, desc in columns.items())
        schema_blocks.append(f"### `{name}`\n\n| Column | Description |\n|---|---|\n{rows}\n")
        sample = frame.sample(n=20, random_state=SEED).to_csv(index=False, lineterminator="\n")
        sample_blocks.append(f"### `{name}`\n\n```csv\n{sample.strip()}\n```\n")
    parts.extend(["\n".join(schema_blocks), "\n".join(sample_blocks), RESPONSE_SECTION])
    return "\n".join(parts).strip() + "\n"


def paste_skeleton(prompt: str) -> str:
    return (
        "# Model Output Record\n\n"
        "## Model metadata\n\n"
        "- Model name: [fill in]\n"
        "- Model version: [fill in]\n"
        "- Interface: [fill in]\n"
        "- Date/time: [fill in]\n"
        "- Settings: [fill in, or write: not exposed]\n\n"
        "## Exact prompt sent\n\n"
        f"{prompt.strip()}\n\n"
        "## Verbatim model response\n\n"
        "[paste the complete, unedited response here]\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw" / CASE)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "cases" / CASE / "ai_output")
    parser.add_argument("--force", action="store_true", help="overwrite a frozen prompt")
    arguments = parser.parse_args()

    prompt_path = arguments.out_dir / "PROMPT_TO_PASTE.md"
    paste_path = arguments.out_dir / "PASTE_HERE.md"
    if prompt_path.exists() and not arguments.force:
        print(f"{prompt_path} already exists; the prompt is frozen. Use --force to replace it.",
              file=sys.stderr)
        return 2
    prompt = build_prompt(arguments.raw_dir)
    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    existing = paste_path.read_text(encoding="utf-8") if paste_path.exists() else ""
    if "## Verbatim model response" in existing and "[paste the complete" not in existing:
        print("PASTE_HERE.md already holds a response; left untouched.", file=sys.stderr)
    else:
        paste_path.write_text(paste_skeleton(prompt), encoding="utf-8", newline="\n")
    print(f"Wrote {prompt_path}")
    print(f"Wrote {paste_path} (prompt embedded; metadata and response still to fill)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
