"""Download the pinned HF CSV, preserve raw bytes, and summarize basic cleaning.

Run from the repository: python src/ingest.py
No values are imputed and no model or learned preprocessing is fitted here.
"""

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COLUMNS = [
    "customerID", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure",
    "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
    "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV",
    "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod",
    "MonthlyCharges", "TotalCharges", "Churn",
]
NUMERIC_COLUMNS = ["SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges"]


def sha256(content):
    """A fingerprint of the actual file bytes, not just its filename."""
    return hashlib.sha256(content).hexdigest()


def load_config(config_path):
    with Path(config_path).open() as stream:
        config = yaml.safe_load(stream)
    paths = {key: ROOT / value for key, value in config["paths"].items()}
    if len({p.resolve() for p in paths.values()}) != len(paths):
        raise ValueError("Raw, processed, and report paths must be different.")
    return config, paths


def fetch_raw(dataset, path):
    """Reuse a verified local raw file, or download and verify it before saving."""
    path = Path(path)
    if path.exists():
        content = path.read_bytes()
        action = "Reused verified local source"
    else:
        response = requests.get(dataset["url"], timeout=60)
        response.raise_for_status()
        content = response.content
        action = "Downloaded source from Hugging Face"
    if sha256(content) != dataset["sha256"]:
        raise ValueError(
            "Source checksum does not match config.yaml. Inspect the source "
            "or local raw file before replacing anything."
        )
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    print(action)
    return content


def clean_data(raw):
    """Apply deterministic formatting and type conversion; preserve every row."""
    if list(raw.columns) != EXPECTED_COLUMNS:
        raise ValueError("Unexpected source columns or column order; review the schema.")
    cleaned = raw.copy(deep=True)
    text_columns = cleaned.select_dtypes(include=["object", "string"]).columns
    for column in text_columns:
        # Whitespace-only cells become actual missing values, not an empty category.
        cleaned[column] = cleaned[column].astype("string").str.strip().replace("", pd.NA)
    for column in NUMERIC_COLUMNS:
        # Malformed nonblank numbers fail visibly instead of silently disappearing.
        cleaned[column] = pd.to_numeric(cleaned[column], errors="raise")

    if cleaned["customerID"].isna().any():
        raise ValueError("Customer IDs must be present.")
    if cleaned["customerID"].duplicated().any():
        raise ValueError("Duplicate customer IDs; do not silently drop customers.")
    if not cleaned["Churn"].isin(["Yes", "No"]).all():
        raise ValueError("Churn must be Yes or No, with no missing labels.")
    if cleaned.drop(columns="TotalCharges").isna().any().any():
        raise ValueError("Unexpected missing values outside TotalCharges; review the data.")
    if not cleaned["SeniorCitizen"].isin([0, 1]).all():
        raise ValueError("SeniorCitizen must be 0 or 1.")
    if (cleaned["tenure"] < 0).any() or (cleaned["tenure"] % 1 != 0).any():
        raise ValueError("Tenure must be a nonnegative whole number of months.")
    for column in ["MonthlyCharges", "TotalCharges"]:
        values = cleaned[column].dropna()
        if (values < 0).any() or values.isin([float("inf"), float("-inf")]).any():
            raise ValueError(f"{column} must contain finite, nonnegative amounts.")
    return cleaned


def build_summary(raw, cleaned, dataset, raw_content, processed_content):
    counts = cleaned["Churn"].value_counts()
    columns = []
    for column in cleaned.columns:
        entry = {
            "name": column,
            "dtype": str(cleaned[column].dtype),
            "missing": int(cleaned[column].isna().sum()),
            "unique_nonmissing": int(cleaned[column].nunique()),
        }
        if column in NUMERIC_COLUMNS:
            entry.update(min=float(cleaned[column].min()), max=float(cleaned[column].max()))
        columns.append(entry)
    missing_total = cleaned["TotalCharges"].isna()
    return {
        "dataset_name": dataset["name"],
        "origin": "IBM fictional telecom sample; downloaded from a Hugging Face mirror",
        "collection_method": "Not documented in the reviewed publisher descriptions; do not claim real-customer collection.",
        "source_url": dataset["url"],
        "raw_sha256": sha256(raw_content),
        "processed_sha256": sha256(processed_content),
        "raw_rows": len(raw), "processed_rows": len(cleaned),
        "column_count": len(cleaned.columns),
        "duplicate_rows": int(cleaned.duplicated().sum()),
        "duplicate_customer_ids": int(cleaned["customerID"].duplicated().sum()),
        "churn_counts": {"No": int(counts.get("No", 0)), "Yes": int(counts.get("Yes", 0))},
        "churn_rate": float(cleaned["Churn"].eq("Yes").mean()),
        "missing_total_charges": int(missing_total.sum()),
        "missing_total_charges_with_zero_tenure": int((missing_total & cleaned["tenure"].eq(0)).sum()),
        "cleaning": [
            "Preserved the raw CSV byte for byte.",
            "Trimmed surrounding whitespace in text fields.",
            "Converted numeric columns to numeric types.",
            "Preserved blank TotalCharges values as missing; retained every customer.",
            "Preserved Yes/No target labels and all 21 columns.",
            "No imputation, encoding, scaling, splitting, or model training.",
        ],
        "columns": columns,
    }


def markdown_summary(summary):
    lines = [
        "# Dataset quality summary", "",
        "Generated by `python src/ingest.py`. Counts describe the downloaded file, not a live customer population.", "",
        f"- Source: [pinned Hugging Face CSV]({summary['source_url']})",
        "- Origin: IBM fictional telecom customer sample.",
        "- Collection/generation method: not documented in the reviewed publisher descriptions.",
        f"- Customers: **{summary['raw_rows']:,} raw → {summary['processed_rows']:,} cleaned**.",
        f"- Columns: **{summary['column_count']}**.",
        f"- Duplicate customer IDs: **{summary['duplicate_customer_ids']}**.",
        f"- Duplicate rows: **{summary['duplicate_rows']}**.",
        f"- Churn = Yes: **{summary['churn_counts']['Yes']:,} ({summary['churn_rate']:.2%})**.",
        f"- Churn = No: **{summary['churn_counts']['No']:,}**.",
        f"- Missing TotalCharges: **{summary['missing_total_charges']}**, all retained.",
        f"- Of those, zero-tenure customers: **{summary['missing_total_charges_with_zero_tenure']}**.",
        "", "## Cleaning performed", "",
        *[f"- {step}" for step in summary["cleaning"]],
        "", "`No internet service` and `No phone service` remain valid categories; they are not missing values.",
        "The 11 blank charge cells are empty in the cleaned CSV and load as missing values in pandas.",
        "Customer IDs are retained for auditing and must be excluded from future model inputs.",
        "", "## Column inventory", "",
        "| Column | Cleaned type | Missing | Distinct nonmissing values |",
        "| --- | --- | ---: | ---: |",
    ]
    lines.extend(f"| {c['name']} | {c['dtype']} | {c['missing']} | {c['unique_nonmissing']} |"
                 for c in summary["columns"])
    lines.extend(["", "## File fingerprints", "",
                  f"- Raw SHA-256: `{summary['raw_sha256']}`",
                  f"- Processed SHA-256: `{summary['processed_sha256']}`", ""])
    return "\n".join(lines)


def ingest(config_path=ROOT / "config.yaml"):
    config, paths = load_config(config_path)
    content = fetch_raw(config["dataset"], paths["raw"])
    raw = pd.read_csv(paths["raw"], dtype={"customerID": "string"})
    cleaned = clean_data(raw)
    # Fixed formatting makes identical input/config/package versions reproduce outputs.
    processed = cleaned.to_csv(index=False, lineterminator="\n").encode("utf-8")
    summary = build_summary(raw, cleaned, config["dataset"], content, processed)
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    paths["processed"].write_bytes(processed)
    paths["summary_json"].write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    paths["summary_markdown"].write_text(markdown_summary(summary), encoding="utf-8")
    print(f"Customers retained: {len(cleaned):,} / {len(raw):,}")
    print(f"Churn labels: {summary['churn_counts']}")
    print(f"Missing TotalCharges preserved: {summary['missing_total_charges']}")
    print(f"Cleaned CSV: {paths['processed']}")
    print(f"Summary: {paths['summary_markdown']}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    args = parser.parse_args()
    try:
        ingest(args.config)
    except (ValueError, OSError, requests.RequestException) as error:
        parser.exit(1, f"Ingestion failed: {error}\n")
