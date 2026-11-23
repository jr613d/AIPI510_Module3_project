"""Exercise the actual W&B SDK with synthetic files, without cloud syncing.

Run from the repository: python tests/check_tracking_offline.py
This is a smoke check, not a real model experiment or a network integration test.
"""

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    # Keep SDK caches and all run output outside the repository and user config.
    with tempfile.TemporaryDirectory(prefix="churn-wandb-smoke-") as folder:
        root = Path(folder)
        for variable, name in (
            ("WANDB_CACHE_DIR", "cache"), ("WANDB_CONFIG_DIR", "config"),
            ("WANDB_DATA_DIR", "data"), ("WANDB_ARTIFACT_DIR", "artifacts"),
        ):
            os.environ[variable] = str(root / name)
        os.environ["WANDB_MODE"] = "offline"
        import wandb
        from src.tracking import log_training_run
        from test_tracking import sample_report

        model_bytes = b"synthetic SDK smoke fixture; not a trained model"
        model = root / "synthetic.joblib"
        model.write_bytes(model_bytes)
        try:
            result = log_training_run(
                sample_report(), model, project="aipi510-tracking-smoke",
                mode="offline", run_name="synthetic-offline-check", run_root=root,
            )
            assert result["mode"] == "offline" and result["url"] is None
            files = list((root / "wandb").glob("offline-run-*/run-*.wandb"))
            assert len(files) == 1 and files[0].stat().st_size > 0
            record = files[0].read_bytes()
            # SDK binary run records preserve metric and artifact field names.
            for identifier in (b"validation/roc_auc", b"validation/true_positives",
                               b"model.joblib", b"validation_report.json"):
                assert identifier in record, identifier
            # wandb 0.31 stages offline artifact files under WANDB_DATA_DIR until sync.
            cached = [path.read_bytes() for folder in (root / "cache", root / "data")
                      for path in folder.rglob("*") if path.is_file()]
            assert model_bytes in cached, "Model snapshot was not cached for the offline artifact."
            reports = []
            for content in cached:
                try:
                    value = json.loads(content)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if isinstance(value, dict) and "processed_sha256" in value:
                    reports.append(value)
            assert len(reports) == 1
            assert reports[0]["model_sha256"] == hashlib.sha256(model_bytes).hexdigest()
            assert reports[0]["metrics"]["roc_auc"] == 0.8
            print(json.dumps({"sdk": wandb.__version__, "mode": result["mode"],
                              "run_id": result["run_id"], "artifact_files": 2,
                              "status": "synthetic offline smoke check passed"}))
        finally:
            wandb.teardown()


if __name__ == "__main__":
    main()
