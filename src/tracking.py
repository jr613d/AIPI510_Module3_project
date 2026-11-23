"""Record completed validation runs without owning training or reading datasets.

`python -m src.train` calls log_training_run() after a successful fit, using
the `tracking` section of config.yaml (or --tracking-mode) to pick the mode.
"""

from copy import deepcopy
import hashlib
import json
import math
from numbers import Integral, Real
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TRAINING_FIELDS = (
    "model", "min_tenure_months", "random_state", "split", "numeric_features",
    "categorical_features", "logistic_regression", "threshold",
)
COUNTS = ("true_negatives", "false_positives", "false_negatives", "true_positives")
MODES = ("online", "offline", "disabled")


def tracking_settings(config, mode=None):
    """Read config.yaml's tracking section; a command-line mode overrides it."""
    section = config.get("tracking")
    if not isinstance(section, dict):
        raise ValueError("config.yaml needs a tracking section (project, entity, mode).")
    chosen = mode if mode is not None else section.get("mode")
    if chosen not in MODES:
        raise ValueError(f"Tracking mode must be one of {', '.join(MODES)}.")
    project, entity = section.get("project"), section.get("entity")
    if chosen != "disabled" and (not isinstance(project, str) or not project.strip()):
        raise ValueError("Set tracking.project in config.yaml before recording a run.")
    return {"project": project, "entity": entity, "mode": chosen}


def validation_record(report):
    """Select aggregate fields explicitly; never forward a full config or CSV."""
    if report.get("evaluation_partition") != "validation" or report.get("test_evaluated") is not False:
        raise ValueError("This helper records validation-only runs with test_evaluated=False.")
    fingerprint = report.get("processed_sha256", "")
    if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise ValueError("A valid processed_sha256 is required to identify the training data.")
    settings = report["settings"]
    training = {key: deepcopy(settings[key]) for key in TRAINING_FIELDS}
    metrics = {}
    for name in ("roc_auc", "precision", "recall", "threshold"):
        value = report["metrics"][name]
        if (isinstance(value, bool) or not isinstance(value, Real)
                or not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError(f"Validation metric {name} must be finite and between 0 and 1.")
        metrics[name] = float(value)
    if metrics["threshold"] != training["threshold"]:
        raise ValueError("The reported threshold must match the training settings.")
    matrix = report["metrics"]["confusion_matrix"]
    confusion = {}
    for name in COUNTS:
        value = matrix[name]
        if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
            raise ValueError("Confusion-matrix entries must be nonnegative integers.")
        confusion[name] = int(value)
    metrics["confusion_matrix"] = confusion
    record = {
        "evaluation_partition": "validation", "test_evaluated": False,
        "processed_sha256": fingerprint, "settings": training, "metrics": metrics,
        "threshold_status": report["metrics"].get("threshold_status", "unspecified"),
        "versions": deepcopy(report.get("versions", {})),
    }
    source = report.get("data_source")
    if source is not None:
        if source.get("sha256") != fingerprint or not source.get("uri", "").startswith("gs://"):
            raise ValueError("Cloud source provenance must match processed_sha256 and use a gs:// URI.")
        record["data_source"] = {"uri": source["uri"], "sha256": source["sha256"]}
    # Reject non-JSON / nonfinite values before creating a W&B run.
    json.dumps(record, allow_nan=False)
    return record


def code_version(root=ROOT):
    """Record the commit and dirty flag; do not upload file contents or diffs."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
            text=True, check=True, timeout=5,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, capture_output=True,
            text=True, check=True, timeout=5,
        ).stdout
        return {"git_commit": commit, "git_dirty": bool(status.strip())}
    except (OSError, subprocess.SubprocessError):
        return {"git_commit": None, "git_dirty": None}


def log_training_run(report, model_path, *, project, entity=None, mode="offline",
                     run_name=None, group=None, run_root=ROOT, sdk=None):
    """Log aggregate metrics and a snapshot of an existing model, never fit one.

    sdk is injectable for offline unit tests. No login or online sync is
    attempted by this function unless the caller explicitly selects online.
    """
    if mode not in ("offline", "online"):
        raise ValueError("Tracking mode must be offline or online.")
    if not isinstance(project, str) or not project.strip():
        raise ValueError("Choose a W&B project name before recording a run.")
    if entity is not None and (not isinstance(entity, str) or not entity.strip()):
        raise ValueError("W&B entity must be a workspace name or None.")
    record = validation_record(report)
    model_path = Path(model_path)
    if model_path.suffix != ".joblib":
        raise ValueError("Provide the saved .joblib model artifact, not a dataset.")
    model_bytes = model_path.read_bytes()
    if not model_bytes:
        raise ValueError("Model artifact is empty.")
    record.update(code_version())
    record["model_sha256"] = hashlib.sha256(model_bytes).hexdigest()
    if sdk is None:
        import wandb as sdk
    if sdk.run is not None:
        raise RuntimeError("Finish the active W&B run before recording another training result.")
    run_root = Path(run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    run_config = {
        "training": record["settings"], "data_sha256": record["processed_sha256"],
        "model_sha256": record["model_sha256"], "versions": record["versions"],
        "git_commit": record["git_commit"], "git_dirty": record["git_dirty"],
        "evaluation_partition": "validation", "threshold_status": record["threshold_status"],
        "data_source": record.get("data_source"),
    }
    # Keep both snapshots until run.finish() completes the artifact logging.
    with tempfile.TemporaryDirectory(prefix="churn-tracking-") as folder:
        snapshot = Path(folder)
        model_copy = snapshot / "model.joblib"
        model_copy.write_bytes(model_bytes)
        report_copy = snapshot / "validation_report.json"
        report_copy.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        with sdk.init(
            project=project, entity=entity, mode=mode, name=run_name, group=group,
            job_type="training-result", config=run_config, dir=str(run_root),
            save_code=False,
            settings=sdk.Settings(disable_git=True, disable_code=True, console="off"),
        ) as run:
            metrics = {f"validation/{key}": value for key, value in record["metrics"].items()
                       if key != "confusion_matrix"}
            metrics.update({f"validation/{key}": value
                            for key, value in record["metrics"]["confusion_matrix"].items()})
            run.log(metrics)
            run.summary["test_evaluated"] = False
            artifact = sdk.Artifact(
                "churn-model", type="model",
                metadata={"data_sha256": record["processed_sha256"],
                          "model_sha256": record["model_sha256"],
                          "git_commit": record["git_commit"], "git_dirty": record["git_dirty"]},
            )
            artifact.add_file(str(model_copy), name="model.joblib")
            artifact.add_file(str(report_copy), name="validation_report.json")
            run.log_artifact(artifact)
            result = {"run_id": run.id, "mode": mode, "run_dir": run.dir,
                      "url": run.url if mode == "online" else None}
    return result


THRESHOLD_COLUMNS = ("threshold", "flagged", "churners_caught", "false_alarms",
                     "churners_missed", "precision", "recall")


def _settings(sdk):
    return sdk.Settings(disable_git=True, disable_code=True, console="off")


def log_threshold_table(rows, *, data_sha256, project, entity=None, mode="offline",
                        run_root=ROOT, sdk=None):
    """Log a validation-only cutoff comparison as a W&B table and line chart."""
    if mode not in ("offline", "online"):
        raise ValueError("Tracking mode must be offline or online.")
    if not rows or any(set(row) != set(THRESHOLD_COLUMNS) for row in rows):
        raise ValueError(f"Each threshold row needs exactly: {', '.join(THRESHOLD_COLUMNS)}.")
    if sdk is None:
        import wandb as sdk
    if sdk.run is not None:
        raise RuntimeError("Finish the active W&B run before recording another result.")
    Path(run_root).mkdir(parents=True, exist_ok=True)
    config = {"evaluation_partition": "validation", "data_sha256": data_sha256, **code_version()}
    with sdk.init(project=project, entity=entity, mode=mode, name="threshold-selection",
                  group="model-selection", job_type="threshold-selection", config=config,
                  dir=str(run_root), save_code=False, settings=_settings(sdk)) as run:
        table = sdk.Table(columns=list(THRESHOLD_COLUMNS),
                          data=[[row[name] for name in THRESHOLD_COLUMNS] for row in rows])
        thresholds = [row["threshold"] for row in rows]
        run.log({
            "validation/threshold_table": table,
            "validation/precision_recall_by_threshold": sdk.plot.line_series(
                xs=thresholds, ys=[[row["precision"] for row in rows], [row["recall"] for row in rows]],
                keys=["precision", "recall"], title="Precision and recall by threshold (validation)",
                xname="threshold"),
        })
        run.summary["test_evaluated"] = False
        return {"run_id": run.id, "mode": mode, "run_dir": run.dir,
                "url": run.url if mode == "online" else None}


def log_test_run(report, *, project, entity=None, mode="offline", run_root=ROOT, sdk=None):
    """Log the one-time final test result as its own clearly labelled run."""
    if mode not in ("offline", "online"):
        raise ValueError("Tracking mode must be offline or online.")
    if report.get("evaluation_partition") != "test" or report.get("test_evaluated") is not True:
        raise ValueError("log_test_run records only the final test evaluation.")
    if sdk is None:
        import wandb as sdk
    if sdk.run is not None:
        raise RuntimeError("Finish the active W&B run before recording another result.")
    Path(run_root).mkdir(parents=True, exist_ok=True)
    metrics, counts = report["metrics"], report["metrics"]["confusion_matrix"]
    config = {"evaluation_partition": "test", "training": deepcopy(report["settings"]),
              "data_sha256": report["data_sha256"], "model_sha256": report["model_sha256"],
              **code_version()}
    with sdk.init(project=project, entity=entity, mode=mode, name="final-test",
                  job_type="final-test", config=config, dir=str(run_root),
                  save_code=False, settings=_settings(sdk)) as run:
        logged = {f"test/{key}": metrics[key] for key in ("roc_auc", "precision", "recall", "threshold")}
        logged.update({f"test/{key}": value for key, value in counts.items()})
        run.log(logged)
        run.summary["test_evaluated"] = True
        return {"run_id": run.id, "mode": mode, "run_dir": run.dir,
                "url": run.url if mode == "online" else None}
