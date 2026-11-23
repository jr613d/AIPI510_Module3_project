"""Offline contract tests; no W&B login, training, or network access needed."""

from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from src.tracking import log_training_run, tracking_settings, validation_record


def sample_report():
    return {
        "evaluation_partition": "validation", "test_evaluated": False,
        "processed_sha256": "a" * 64,
        "data_source": {"uri": "gs://example-bucket/churn.csv", "sha256": "a" * 64,
                        "path": "/local/path/not-needed-in-wandb"},
        "settings": {
            "model": "logistic_regression", "min_tenure_months": 1, "random_state": 42,
            "split": {"train": 0.7, "validation": 0.15, "test": 0.15},
            "numeric_features": ["tenure", "MonthlyCharges"],
            "categorical_features": ["Contract"],
            "logistic_regression": {"C": 1.0, "max_iter": 1000}, "threshold": 0.5,
        },
        "metrics": {
            "roc_auc": 0.8, "precision": 0.75, "recall": 0.6, "threshold": 0.5,
            "threshold_status": "provisional; not tuned or finalized",
            "confusion_matrix": {"true_negatives": 35, "false_positives": 5,
                                 "false_negatives": 10, "true_positives": 15},
        },
        "versions": {"python": "3.10.0", "scikit-learn": "1.7.2"},
    }


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.model = self.root / "pipeline.joblib"
        self.model.write_bytes(b"synthetic model fixture; not a trained model")
        self.report = sample_report()
        self.sdk = Mock()
        self.sdk.run = None
        self.run = Mock()
        self.run.id = "test-run"
        self.run.dir = str(self.root / "wandb/test-run/files")
        self.run.url = "https://wandb.example/test-run"
        self.run.summary = {}
        # Mock the SDK context manager, including its finish-on-exit behavior.
        self.context = MagicMock()
        self.context.__enter__.return_value = self.run
        self.sdk.init.return_value = self.context

    def record(self, **kwargs):
        with patch("src.tracking.code_version", return_value={"git_commit": "abc123", "git_dirty": True}):
            return log_training_run(self.report, self.model, project="tracking-tests",
                                    run_root=self.root, sdk=self.sdk, **kwargs)

    def test_records_validation_metrics_with_correct_namespace_and_offline_default(self):
        original = deepcopy(self.report)
        result = self.record()
        self.assertEqual(result["mode"], "offline")
        self.assertIsNone(result["url"])
        self.assertEqual(self.sdk.init.call_args.kwargs["mode"], "offline")
        metrics = self.run.log.call_args.args[0]
        self.assertEqual(metrics["validation/roc_auc"], 0.8)
        self.assertEqual(metrics["validation/true_positives"], 15)
        self.assertTrue(all(name.startswith("validation/") for name in metrics))
        self.assertFalse(self.run.summary["test_evaluated"])
        self.assertEqual(self.report, original)

    def test_artifact_contains_matching_model_and_sanitized_report_snapshots(self):
        captured = {}
        def capture(path, name):
            captured[name] = Path(path).read_bytes()
        self.sdk.Artifact.return_value.add_file.side_effect = capture
        self.report["rows"] = [{"customerID": "never-log-this"}]
        self.report["settings"]["api_key"] = "never-log-this"
        self.record()
        self.assertEqual(set(captured), {"model.joblib", "validation_report.json"})
        self.assertEqual(captured["model.joblib"], self.model.read_bytes())
        recorded = json.loads(captured["validation_report.json"])
        self.assertEqual(recorded["model_sha256"], hashlib.sha256(captured["model.joblib"]).hexdigest())
        self.assertNotIn("never-log-this", captured["validation_report.json"].decode())
        self.assertNotIn("path", recorded["data_source"])
        self.assertEqual(recorded["git_commit"], "abc123")
        self.assertTrue(recorded["git_dirty"])
        self.run.log_artifact.assert_called_once_with(self.sdk.Artifact.return_value)

    def test_test_partition_results_are_not_mislabeled_as_validation(self):
        for key, value in (("evaluation_partition", "test"), ("test_evaluated", True)):
            with self.subTest(key=key):
                self.report = sample_report()
                self.report[key] = value
                with self.assertRaisesRegex(ValueError, "validation-only"):
                    self.record()
        self.sdk.init.assert_not_called()

    def test_bad_metrics_or_mismatched_provenance_fail_before_creating_run(self):
        for value in (float("nan"), float("inf"), -0.1, True):
            with self.subTest(value=value):
                self.report = sample_report()
                self.report["metrics"]["roc_auc"] = value
                with self.assertRaisesRegex(ValueError, "finite"):
                    self.record()
        self.report = sample_report()
        self.report["data_source"]["sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "provenance"):
            self.record()
        self.sdk.init.assert_not_called()

    def test_online_mode_requires_explicit_choice(self):
        result = self.record(mode="online")
        self.assertEqual(result["url"], self.run.url)
        self.assertEqual(self.sdk.init.call_args.kwargs["mode"], "online")

    def test_unsupported_mode_missing_model_and_dataset_path_do_not_create_run(self):
        with self.assertRaises(ValueError):
            self.record(mode="disabled")
        self.model.unlink()
        with self.assertRaises(FileNotFoundError):
            self.record()
        with self.assertRaisesRegex(ValueError, "model artifact"):
            log_training_run(self.report, self.root / "data.csv", project="test", sdk=self.sdk)
        self.sdk.init.assert_not_called()

    def test_existing_run_is_not_reused_and_upload_errors_propagate(self):
        self.sdk.run = Mock()
        with self.assertRaisesRegex(RuntimeError, "active W&B run"):
            self.record()
        self.sdk.init.assert_not_called()
        self.sdk.run = None
        self.run.log_artifact.side_effect = RuntimeError("artifact logging failed")
        with self.assertRaisesRegex(RuntimeError, "artifact logging failed"):
            self.record()
        self.assertIs(self.context.__exit__.call_args.args[0], RuntimeError)


class TrackingSettingsTests(unittest.TestCase):
    config = {"tracking": {"project": "aipi510-churn", "entity": None, "mode": "online"}}

    def test_config_mode_is_used_unless_overridden(self):
        self.assertEqual(tracking_settings(self.config)["mode"], "online")
        self.assertEqual(tracking_settings(self.config, "offline")["mode"], "offline")

    def test_invalid_or_missing_settings_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "tracking section"):
            tracking_settings({})
        with self.assertRaisesRegex(ValueError, "mode must be"):
            tracking_settings(self.config, "sometimes")
        with self.assertRaisesRegex(ValueError, "tracking.project"):
            tracking_settings({"tracking": {"project": " ", "mode": "online"}})

    def test_disabled_mode_does_not_need_a_project(self):
        self.assertEqual(tracking_settings({"tracking": {"mode": "disabled"}})["mode"], "disabled")


class TrainCommandTrackingTests(unittest.TestCase):
    """src.train.main() wiring, with training and the W&B SDK replaced by mocks."""

    def setUp(self):
        self.report = sample_report()
        self.report.update(encoded_feature_count=20)
        self.report["settings"]["model_path"] = "artifacts/churn_pipeline.joblib"
        patches = {
            "train": patch("src.train.train", return_value=(None, self.report)),
            "log": patch("src.train.log_training_run",
                         return_value={"mode": "online", "url": "https://wandb.example/r", "run_dir": "x"}),
        }
        self.mocks = {name: p.start() for name, p in patches.items()}
        self.addCleanup(patch.stopall)

    def run_main(self, *argv):
        from src.train import main
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            main(list(argv))
        return out.getvalue()

    def test_successful_training_is_logged_with_config_settings(self):
        from src.ingest import ROOT
        output = self.run_main()
        args, kwargs = self.mocks["log"].call_args
        self.assertEqual(args, (self.report, ROOT / "artifacts/churn_pipeline.joblib"))
        self.assertEqual(kwargs, {"project": "aipi510-churn", "entity": None, "mode": "online"})
        self.assertIn("https://wandb.example/r", output)

    def test_command_line_mode_overrides_config(self):
        self.run_main("--tracking-mode", "offline")
        self.assertEqual(self.mocks["log"].call_args.kwargs["mode"], "offline")

    def test_disabled_mode_skips_wandb(self):
        output = self.run_main("--tracking-mode", "disabled")
        self.mocks["log"].assert_not_called()
        self.assertIn("tracking disabled", output)

    def test_tracking_failure_exits_with_error(self):
        self.mocks["log"].side_effect = RuntimeError("network down")
        with patch("sys.stderr", new_callable=io.StringIO) as err, self.assertRaises(SystemExit) as stop:
            self.run_main()
        self.assertEqual(stop.exception.code, 1)
        self.assertIn("W&B tracking failed: network down", err.getvalue())

    def test_invalid_tracking_mode_in_config_stops_before_training(self):
        with tempfile.TemporaryDirectory() as folder:
            config_path = Path(folder) / "config.yaml"
            from src.ingest import ROOT
            text = (ROOT / "config.yaml").read_text(encoding="utf-8")
            config_path.write_text(text.replace("mode: online", "mode: sometimes"), encoding="utf-8")
            with patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                self.run_main("--config", str(config_path))
        self.mocks["train"].assert_not_called()


if __name__ == "__main__":
    unittest.main()
