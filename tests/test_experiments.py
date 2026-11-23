"""Experiment-runner tests; training and W&B are replaced with mocks."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from src.experiments import run_experiments, variants
from src.ingest import ROOT


def load_real_config():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def fake_train(config_path):
    """Return a minimal report built from the variant config that was written."""
    settings = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))["training"]
    features = settings["numeric_features"] + settings["categorical_features"]
    c_value = settings["logistic_regression"]["C"]
    return None, {
        "settings": settings, "input_features": features,
        "encoded_feature_count": len(features) * 2,
        "metrics": {"roc_auc": 0.8 + c_value / 1000, "precision": 0.6,
                    "recall": 0.5, "threshold": settings["threshold"]},
    }


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.config = load_real_config()
        out = Path(self.folder.name)
        self.config["experiments"]["summary_json"] = str(out / "experiments.json")
        self.config["experiments"]["summary_markdown"] = str(out / "experiments.md")
        self.config_path = out / "config.yaml"
        self.write_config()

    def write_config(self):
        self.config_path.write_text(yaml.safe_dump(self.config), encoding="utf-8")

    def test_every_combination_gets_its_own_outputs(self):
        planned = list(variants(self.config))
        section = self.config["experiments"]
        self.assertEqual(len(planned), len(section["C_values"]) * len(section["feature_sets"]))
        names = [name for name, _, _ in planned]
        self.assertEqual(len(names), len(set(names)))
        main_model = self.config["training"]["model_path"]
        for name, set_name, settings in planned:
            self.assertTrue(settings["model_path"].startswith(section["output_dir"]))
            self.assertNotEqual(settings["model_path"], main_model)
            self.assertIn(name, settings["model_path"])
            expected = section["feature_sets"][set_name]
            self.assertEqual(settings["numeric_features"], expected["numeric_features"])

    def test_variants_do_not_modify_the_loaded_config(self):
        original = deepcopy(self.config)
        list(variants(self.config))
        self.assertEqual(self.config, original)

    def test_disabled_mode_trains_all_variants_without_wandb(self):
        with patch("src.experiments.train", side_effect=fake_train) as train, \
                patch("src.experiments.log_training_run") as log, \
                patch("builtins.print"):
            rows, markdown = run_experiments(self.config_path, "disabled")
        self.assertEqual(train.call_count, len(rows))
        log.assert_not_called()
        summary = json.loads(Path(self.config["experiments"]["summary_json"]).read_text())
        self.assertEqual(summary["evaluation_partition"], "validation")
        self.assertFalse(summary["test_evaluated"])
        self.assertEqual(len(summary["runs"]), len(rows))
        self.assertIn("| eight_inputs-C1.0 | 8 | 1.0 |", markdown.read_text())

    def test_tracked_runs_are_named_and_grouped(self):
        result = {"url": "https://wandb.example/r", "run_id": "r", "mode": "online"}
        with patch("src.experiments.train", side_effect=fake_train), \
                patch("src.experiments.log_training_run", return_value=result) as log, \
                patch("builtins.print"):
            rows, _ = run_experiments(self.config_path, "online")
        names = [call.kwargs["run_name"] for call in log.call_args_list]
        self.assertEqual(names, [row["name"] for row in rows])
        self.assertTrue(all(call.kwargs["group"] == "model-selection"
                            for call in log.call_args_list))
        self.assertTrue(all(row["wandb_run"] == "https://wandb.example/r" for row in rows))

    def test_invalid_plan_is_rejected_before_any_training(self):
        self.config["experiments"]["C_values"] = []
        self.write_config()
        with patch("src.experiments.train") as train, self.assertRaisesRegex(ValueError, "C_values"):
            run_experiments(self.config_path, "disabled")
        train.assert_not_called()


if __name__ == "__main__":
    unittest.main()
