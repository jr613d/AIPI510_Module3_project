"""Threshold-selection tests on a small synthetic dataset; no cloud or W&B access."""

import unittest
from unittest.mock import MagicMock, Mock, patch

import yaml

from src.ingest import ROOT
from src.thresholds import load_matching_model, threshold_rows
from src.tracking import THRESHOLD_COLUMNS, log_threshold_table
from src.train import build_pipeline, validate_inputs
from tests.test_train import sample_customers


class ThresholdTests(unittest.TestCase):
    def setUp(self):
        self.settings = yaml.safe_load((ROOT / "config.yaml").read_text())["training"]
        data = sample_customers()
        self.pipeline = build_pipeline(self.settings)
        self.pipeline.fit(validate_inputs(data, self.settings), data["Churn"].eq("Yes").astype(int))
        self.data = data

    def test_lower_cutoffs_flag_at_least_as_many_customers(self):
        rows = threshold_rows(self.pipeline, self.data, self.settings, [0.2, 0.5, 0.8])
        flagged = [row["flagged"] for row in rows]
        self.assertEqual(flagged, sorted(flagged, reverse=True))
        churners = (self.data["Churn"] == "Yes").sum()
        for row in rows:
            self.assertEqual(set(row), set(THRESHOLD_COLUMNS))
            self.assertEqual(row["churners_caught"] + row["churners_missed"], churners)
            self.assertEqual(row["flagged"], row["churners_caught"] + row["false_alarms"])

    def test_invalid_candidates_are_rejected(self):
        with self.assertRaises(ValueError):
            threshold_rows(self.pipeline, self.data, self.settings, [])
        with self.assertRaises(ValueError):
            threshold_rows(self.pipeline, self.data, self.settings, [1.5])

    def test_saved_model_must_match_config_and_data(self):
        config = {"training": self.settings}
        bundle = {"pipeline": self.pipeline, "settings": dict(self.settings), "processed_sha256": "a" * 64}
        with patch("src.thresholds.joblib.load", return_value=bundle):
            self.assertIs(load_matching_model(config, {"sha256": "a" * 64}), self.pipeline)
            with self.assertRaisesRegex(ValueError, "different data"):
                load_matching_model(config, {"sha256": "b" * 64})
            bundle["settings"] = {**self.settings, "logistic_regression": {"C": 0.01, "max_iter": 1000}}
            with self.assertRaisesRegex(ValueError, "does not match"):
                load_matching_model(config, {"sha256": "a" * 64})


class ThresholdTrackingTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{name: 0.5 for name in THRESHOLD_COLUMNS}]
        self.sdk = Mock()
        self.sdk.run = None
        self.run = Mock(id="t", dir="d", url="https://wandb.example/t")
        self.run.summary = {}
        context = MagicMock()
        context.__enter__.return_value = self.run
        self.sdk.init.return_value = context

    def log(self, **kwargs):
        with patch("src.tracking.code_version", return_value={"git_commit": "abc", "git_dirty": False}):
            return log_threshold_table(self.rows, data_sha256="a" * 64, project="p",
                                       sdk=self.sdk, **kwargs)

    def test_logs_table_and_chart_as_validation_only(self):
        result = self.log(mode="online")
        logged = self.run.log.call_args.args[0]
        self.assertEqual(set(logged), {"validation/threshold_table",
                                       "validation/precision_recall_by_threshold"})
        self.assertEqual(self.sdk.init.call_args.kwargs["config"]["evaluation_partition"], "validation")
        self.assertFalse(self.run.summary["test_evaluated"])
        self.assertEqual(result["url"], "https://wandb.example/t")

    def test_malformed_rows_and_modes_are_rejected(self):
        self.rows[0].pop("recall")
        with self.assertRaisesRegex(ValueError, "threshold row"):
            self.log()
        self.sdk.init.assert_not_called()
        with self.assertRaisesRegex(ValueError, "mode"):
            log_threshold_table([], data_sha256="a", project="p", mode="disabled", sdk=self.sdk)


if __name__ == "__main__":
    unittest.main()
