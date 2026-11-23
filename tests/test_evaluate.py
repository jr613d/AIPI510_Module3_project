"""Final-evaluation tests; cloud download, model loading, and W&B are mocked."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

import yaml

from src.evaluate import evaluate
from src.ingest import ROOT
from src.tracking import log_test_run
from src.train import build_pipeline, validate_inputs
from tests.test_train import sample_customers


class EvaluateTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        out = Path(self.folder.name)
        self.config = yaml.safe_load((ROOT / "config.yaml").read_text())
        self.config["final_evaluation"] = {"summary_json": str(out / "test.json"),
                                           "summary_markdown": str(out / "test.md")}
        self.model_path = out / "model.joblib"
        self.model_path.write_bytes(b"model bytes")
        self.config["training"]["model_path"] = str(self.model_path)
        self.config_path = out / "config.yaml"
        self.config_path.write_text(yaml.safe_dump(self.config))
        settings = self.config["training"]
        data = sample_customers()
        pipeline = build_pipeline(settings)
        pipeline.fit(validate_inputs(data, settings), data["Churn"].eq("Yes").astype(int))
        self.splits = {"train": None, "validation": None, "test": data}
        patches = [
            patch("src.evaluate.prepare_splits",
                  return_value=(self.splits, {"source": {"sha256": "a" * 64}})),
            patch("src.evaluate.load_matching_model", return_value=pipeline),
            patch("joblib.load", return_value={"settings": dict(settings)}),
        ]
        self.mocks = [p.start() for p in patches]
        self.addCleanup(patch.stopall)

    def test_scores_test_rows_once_and_refuses_a_second_run(self):
        report, markdown, result = evaluate(self.config_path, "disabled")
        self.assertIsNone(result)
        self.assertEqual(report["evaluation_partition"], "test")
        self.assertEqual(report["test_customers"], len(self.splits["test"]))
        saved = json.loads(Path(self.config["final_evaluation"]["summary_json"]).read_text())
        self.assertTrue(saved["test_evaluated"])
        self.assertIn("Final test evaluation", markdown.read_text())
        download = self.mocks[0]
        download.reset_mock()
        with self.assertRaisesRegex(ValueError, "already evaluated"):
            evaluate(self.config_path, "disabled")
        download.assert_not_called()  # The guard stops before touching the data.

    def test_model_trained_with_a_different_threshold_is_rejected(self):
        self.mocks[2].return_value = {"settings": {**self.config["training"], "threshold": 0.5}}
        self.config["training"]["threshold"] = 0.35
        self.config_path.write_text(yaml.safe_dump(self.config))
        with self.assertRaisesRegex(ValueError, "threshold differs"):
            evaluate(self.config_path, "disabled")
        self.assertFalse(Path(self.config["final_evaluation"]["summary_json"]).exists())


class TestRunTrackingTests(unittest.TestCase):
    def setUp(self):
        self.sdk = Mock()
        self.sdk.run = None
        self.run = Mock(id="f", dir="d", url="https://wandb.example/f")
        self.run.summary = {}
        context = MagicMock()
        context.__enter__.return_value = self.run
        self.sdk.init.return_value = context
        self.report = {
            "evaluation_partition": "test", "test_evaluated": True, "settings": {"threshold": 0.35},
            "data_sha256": "a" * 64, "model_sha256": "b" * 64,
            "metrics": {"roc_auc": 0.84, "precision": 0.6, "recall": 0.7, "threshold": 0.35,
                        "confusion_matrix": {"true_negatives": 1, "false_positives": 2,
                                             "false_negatives": 3, "true_positives": 4}},
        }

    def test_logs_metrics_under_test_prefix(self):
        with patch("src.tracking.code_version", return_value={}):
            log_test_run(self.report, project="p", mode="online", sdk=self.sdk)
        logged = self.run.log.call_args.args[0]
        self.assertEqual(logged["test/roc_auc"], 0.84)
        self.assertEqual(logged["test/true_positives"], 4)
        self.assertEqual(self.sdk.init.call_args.kwargs["job_type"], "final-test")
        self.assertTrue(self.run.summary["test_evaluated"])

    def test_validation_reports_are_refused(self):
        self.report["evaluation_partition"] = "validation"
        with self.assertRaisesRegex(ValueError, "final test"):
            log_test_run(self.report, project="p", sdk=self.sdk)
        self.sdk.init.assert_not_called()


if __name__ == "__main__":
    unittest.main()
