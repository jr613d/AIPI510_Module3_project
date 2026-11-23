"""Train the agreed eight-input classifier and evaluate validation data only.

Run: python -m src.train [--tracking-mode online|offline|disabled]
After training succeeds, results are recorded in Weights & Biases.
The test partition is reserved for evaluation after the approach is finalized.
"""

import argparse
from importlib.metadata import version
import json
import math
from numbers import Integral, Real
from pathlib import Path
import platform
import warnings

import joblib
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from google.cloud.storage.exceptions import DataCorruption
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.ingest import EXPECTED_COLUMNS, ROOT, load_config
from src.preprocess import prepare_splits
from src.tracking import MODES, log_training_run, tracking_settings


def feature_names(settings):
    """Use explicit input lists; IDs and the target cannot become predictors."""
    numeric = settings["numeric_features"]
    categorical = settings["categorical_features"]
    if not isinstance(numeric, list) or not isinstance(categorical, list):
        raise ValueError("Numeric and categorical features must be lists.")
    features = numeric + categorical
    allowed = set(EXPECTED_COLUMNS) - {"customerID", "Churn"}
    if (not numeric or not categorical
            or any(not isinstance(name, str) or name not in allowed for name in features)
            or len(features) != len(set(features))):
        raise ValueError("Feature lists must be nonempty, unique, and exclude IDs and Churn.")
    return features


def build_pipeline(settings):
    """Fit numeric scales and category vocabulary in the same pipeline as the model."""
    feature_names(settings)
    if settings["model"] != "logistic_regression":
        raise ValueError("This training step supports logistic_regression only.")
    params = settings["logistic_regression"]
    if (isinstance(params["C"], bool) or not isinstance(params["C"], Real)
            or not math.isfinite(params["C"]) or params["C"] <= 0):
        raise ValueError("C must be a finite positive number.")
    if (isinstance(params["max_iter"], bool)
            or not isinstance(params["max_iter"], Integral) or params["max_iter"] < 1):
        raise ValueError("max_iter must be a positive integer.")
    preprocessor = ColumnTransformer([
        ("numeric", StandardScaler(), settings["numeric_features"]),
        ("categorical", OneHotEncoder(handle_unknown="ignore", drop=None, sparse_output=False),
         settings["categorical_features"]),
    ], remainder="drop")
    classifier = LogisticRegression(
        C=params["C"], max_iter=params["max_iter"], penalty="l2",
        solver="lbfgs", random_state=settings["random_state"],
    )
    return Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])


def validate_inputs(data, settings):
    """Fail visibly on unexpected missing inputs instead of adding imputation."""
    selected = data.loc[:, feature_names(settings)]
    if selected.isna().any().any():
        raise ValueError("Selected model inputs contain missing values; review the data.")
    for column in settings["numeric_features"]:
        if any(not isinstance(value, Real) or not math.isfinite(value)
               for value in selected[column]):
            raise ValueError(f"{column} must contain finite numeric values.")
    return selected


def validation_metrics(pipeline, data, settings):
    threshold = settings["threshold"]
    if (isinstance(threshold, bool) or not isinstance(threshold, Real)
            or not math.isfinite(threshold) or not 0 < threshold < 1):
        raise ValueError("Classification threshold must be between 0 and 1.")
    inputs = validate_inputs(data, settings)
    target = data["Churn"].eq("Yes").astype(int)
    probabilities = pipeline.predict_proba(inputs)[:, 1]
    predicted = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(target, predicted, labels=[0, 1]).ravel()
    return {
        "roc_auc": float(roc_auc_score(target, probabilities)),
        "precision": float(precision_score(target, predicted, zero_division=0)),
        "recall": float(recall_score(target, predicted, zero_division=0)),
        "threshold": threshold,
        "threshold_status": settings.get("threshold_status", "provisional; not tuned or finalized"),
        "confusion_matrix": {
            "true_negatives": int(tn), "false_positives": int(fp),
            "false_negatives": int(fn), "true_positives": int(tp),
        },
    }


def train(config_path=ROOT / "config.yaml"):
    config, paths = load_config(config_path)
    settings = config["training"]
    model_path = ROOT / settings["model_path"]
    report_path = ROOT / settings["validation_report"]
    # Training outputs must never overwrite source data, configuration, or ingestion reports.
    protected = {path.resolve() for path in paths.values()} | {Path(config_path).resolve()}
    protected.add((ROOT / config["storage"]["download_path"]).resolve())
    if (model_path.resolve() in protected or report_path.resolve() in protected
            or model_path.resolve() == report_path.resolve()):
        raise ValueError("Model and validation report need distinct, unprotected output paths.")
    pipeline = build_pipeline(settings)
    splits, population = prepare_splits(config_path)
    inputs = validate_inputs(splits["train"], settings)
    target = splits["train"]["Churn"].eq("Yes").astype(int)
    # A nonconverged fit must not be saved and presented as a successful run.
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        pipeline.fit(inputs, target)
    metrics = validation_metrics(pipeline, splits["validation"], settings)
    expanded = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    report = {
        "evaluation_partition": "validation",
        "test_evaluated": False,
        "target_mapping": {"No": 0, "Yes": 1},
        "processed_sha256": population["source"]["sha256"],
        "data_source": population["source"],
        "settings": settings,
        "population": population,
        "input_features": feature_names(settings),
        "encoded_feature_count": len(expanded),
        "encoded_feature_names": expanded,
        "metrics": metrics,
        "versions": {"python": platform.python_version(), **{
            name: version(name) for name in (
                "pandas", "numpy", "scipy", "scikit-learn", "joblib", "google-cloud-storage")
        }},
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "settings": settings,
                 "processed_sha256": report["processed_sha256"],
                 "data_source": report["data_source"]}, model_path)
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return pipeline, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--tracking-mode", choices=MODES,
                        help="Override tracking.mode in config.yaml for this run.")
    args = parser.parse_args(argv)
    try:
        # Check tracking settings first so a typo does not waste a training run.
        config, _ = load_config(args.config)
        tracking = tracking_settings(config, args.tracking_mode)
        _, report = train(args.config)
    except (ValueError, KeyError, OSError, ConvergenceWarning,
            GoogleAPIError, GoogleAuthError, DataCorruption) as error:
        parser.exit(1, f"Training failed: {error}\n")
    print(json.dumps({"encoded_features": report["encoded_feature_count"],
                      "validation": report["metrics"], "test_evaluated": False}, indent=2))
    if tracking["mode"] == "disabled":
        print("W&B tracking disabled; nothing recorded.")
        return
    try:
        result = log_training_run(
            report, ROOT / report["settings"]["model_path"],
            project=tracking["project"], entity=tracking["entity"], mode=tracking["mode"],
        )
    except Exception as error:  # Any SDK/network failure: never report the run as tracked.
        parser.exit(1, f"Training outputs were saved, but W&B tracking failed: {error}\n")
    print(f"W&B {result['mode']} run recorded: {result['url'] or result['run_dir']}")


if __name__ == "__main__":
    main()
