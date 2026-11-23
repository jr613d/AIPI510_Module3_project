"""Select the modeling population and split it without changing source CSVs.

Run from the repository: python -m src.preprocess
No encoding, scaling, imputation, or model fitting happens in this step.
"""

import argparse
from io import BytesIO
import json
import math
from numbers import Integral, Real
from pathlib import Path

import pandas as pd
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from google.cloud.storage.exceptions import DataCorruption
from sklearn.model_selection import train_test_split

from src import storage
from src.ingest import ROOT, load_config, sha256


def filter_modeling_population(data, min_tenure_months=1):
    """Exclude ineligible tenure before splitting; preserve the input frame."""
    if (isinstance(min_tenure_months, bool)
            or not isinstance(min_tenure_months, Integral)
            or min_tenure_months < 1):
        raise ValueError("Minimum tenure must be a positive whole number of months.")
    tenure = data["tenure"]
    if (not pd.api.types.is_numeric_dtype(tenure)
            or tenure.isna().any()
            or tenure.isin([float("inf"), float("-inf")]).any()
            or (tenure < 0).any() or (tenure % 1 != 0).any()):
        raise ValueError("Tenure must contain finite, nonnegative whole numbers.")
    eligible = data.loc[tenure.ge(min_tenure_months)].copy(deep=True)
    if eligible.empty:
        raise ValueError("No customers meet the minimum-tenure rule.")
    # Missing charges outside the excluded population need a new decision.
    if eligible["TotalCharges"].isna().any():
        raise ValueError("Eligible customers have missing TotalCharges; review the data.")
    return eligible, {
        "input_rows": len(data),
        "excluded_rows": len(data) - len(eligible),
        "eligible_rows": len(eligible),
        "min_tenure_months": int(min_tenure_months),
    }


def stratified_splits(data, fractions, random_state):
    """Keep each customer in one partition and stratify both stages by Churn."""
    names = ("train", "validation", "test")
    values = [fractions[name] for name in names]
    if (any(isinstance(value, bool) or not isinstance(value, Real)
            or not math.isfinite(value) or not 0 < value < 1 for value in values)
            or not math.isclose(sum(values), 1.0, rel_tol=0, abs_tol=1e-9)):
        raise ValueError("Train, validation, and test fractions must be positive and sum to 1.")
    if (isinstance(random_state, bool) or not isinstance(random_state, Integral)
            or not 0 <= random_state < 2**32):
        raise ValueError("Random state must be an integer from 0 through 2**32 - 1.")
    if data["customerID"].isna().any() or data["customerID"].duplicated().any():
        raise ValueError("Customer IDs must be present and unique before splitting.")
    if data["Churn"].isna().any() or set(data["Churn"]) != {"Yes", "No"}:
        raise ValueError("Splitting requires both Yes and No Churn labels, without missing values.")

    holdout_fraction = fractions["validation"] + fractions["test"]
    train, holdout = train_test_split(
        data, test_size=holdout_fraction, random_state=random_state,
        stratify=data["Churn"],
    )
    validation, test = train_test_split(
        holdout, test_size=fractions["test"] / holdout_fraction,
        random_state=random_state, stratify=holdout["Churn"],
    )
    splits = dict(zip(names, (train.copy(), validation.copy(), test.copy())))
    if any(set(part["Churn"]) != {"Yes", "No"} for part in splits.values()):
        raise ValueError("Each split must contain both classes; use more data or larger splits.")
    return splits


def prepare_splits(config_path=ROOT / "config.yaml"):
    """Download verified cloud bytes; return partitions and their exact provenance."""
    config, _ = load_config(config_path)
    settings = config["training"]
    source_path = storage.download(config_path)
    content = source_path.read_bytes()
    # Verify the exact in-memory bytes pandas reads, not a different file or later read.
    storage.verify_content(content, config["storage"]["expected_sha256"])
    data = pd.read_csv(BytesIO(content), dtype={"customerID": "string"})
    eligible, summary = filter_modeling_population(data, settings["min_tenure_months"])
    splits = stratified_splits(eligible, settings["split"], settings["random_state"])
    summary["source"] = {
        "uri": f"gs://{config['storage']['bucket']}/{config['storage']['object']}",
        "path": str(source_path.relative_to(ROOT) if source_path.is_relative_to(ROOT) else source_path),
        "sha256": sha256(content),
        "expected_sha256": config["storage"]["expected_sha256"],
    }
    summary["random_state"] = settings["random_state"]
    summary["splits"] = {
        name: {
            "rows": len(part),
            "churn_counts": {label: int(part["Churn"].eq(label).sum())
                             for label in ("No", "Yes")},
            "churn_rate": float(part["Churn"].eq("Yes").mean()),
        }
        for name, part in splits.items()
    }
    return splits, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    args = parser.parse_args()
    try:
        _, summary = prepare_splits(args.config)
    except (ValueError, KeyError, OSError, GoogleAPIError, GoogleAuthError, DataCorruption) as error:
        parser.exit(1, f"Preprocessing failed: {error}\n")
    print(json.dumps(summary, indent=2, allow_nan=False))
