"""Check encoding, train-only fitting, persistence, and isolation of test data."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import joblib
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
import yaml

from src.ingest import ROOT, sha256
from src.preprocess import prepare_splits
from src.train import build_pipeline, feature_names, train, validate_inputs, validation_metrics


def sample_customers():
    rows = []
    for i in range(200):
        rows.append({
            "customerID": f"customer-{i}", "tenure": i % 50 + 1,
            "MonthlyCharges": 20.0 + i % 80, "TotalCharges": 100.0 + i,
            "Contract": ["Month-to-month", "One year", "Two year"][i % 3],
            "InternetService": ["DSL", "Fiber optic", "No"][i % 3],
            "TechSupport": ["Yes", "No", "No internet service"][i % 3],
            "OnlineSecurity": ["No", "Yes", "No internet service"][i % 3],
            "PaymentMethod": ["Electronic check", "Mailed check"][i % 2],
            "PaperlessBilling": ["Yes", "No"][i % 2],
            "Churn": "Yes" if i % 5 == 0 else "No",
        })
    return pd.DataFrame(rows)


class TrainingTests(unittest.TestCase):
    def setUp(self):
        self.config = yaml.safe_load((ROOT / "config.yaml").read_text())
        self.settings = self.config["training"]
        self.data = sample_customers()

    def test_feature_lists_reject_identifier_target_unknown_and_duplicates(self):
        for forbidden in ("customerID", "Churn", "unknown", "Contract"):
            with self.subTest(forbidden=forbidden):
                settings = deepcopy(self.settings)
                settings["categorical_features"].append(forbidden)
                with self.assertRaises(ValueError):
                    build_pipeline(settings)

    def test_validation_does_not_fit_scales_or_learn_new_categories(self):
        training = self.data.iloc[:150].copy()
        validation = self.data.iloc[150:].copy()
        validation["MonthlyCharges"] = 99999.0
        validation["Contract"] = "Validation-only category"
        pipeline = build_pipeline(self.settings)
        pipeline.fit(validate_inputs(training, self.settings), training.Churn.eq("Yes").astype(int))
        prep = pipeline.named_steps["preprocessor"]
        scaler = prep.named_transformers_["numeric"]
        encoder = prep.named_transformers_["categorical"]
        means = scaler.mean_.copy()
        self.assertAlmostEqual(means[1], training.MonthlyCharges.mean())
        self.assertNotIn("Validation-only category", encoder.categories_[0])
        result = validation_metrics(pipeline, validation, self.settings)
        self.assertTrue((means == scaler.mean_).all())
        self.assertNotIn("Validation-only category", encoder.categories_[0])
        self.assertTrue(0 <= result["roc_auc"] <= 1)
        encoded = prep.transform(validate_inputs(validation, self.settings))
        # Contract is the first categorical field, after the two numeric fields.
        self.assertTrue((encoded[:, 2:2 + len(encoder.categories_[0])] == 0).all())
        self.assertTrue(all("customerID" not in name and "Churn" not in name
                            for name in prep.get_feature_names_out()))

    def test_missing_inputs_fail_instead_of_being_imputed(self):
        data = self.data.copy()
        data.loc[0, "Contract"] = None
        with self.assertRaisesRegex(ValueError, "missing"):
            validate_inputs(data, self.settings)

    def test_training_preserves_csv_saves_reloadable_pipeline_and_never_accesses_test(self):
        class GuardedSplits(dict):
            def __getitem__(self, key):
                if key == "test":
                    raise AssertionError("Training must not access the test partition")
                return super().__getitem__(key)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = deepcopy(self.config)
            data = self.data.copy()
            data.loc[0, ["tenure", "TotalCharges"]] = [0, float("nan")]
            data_path = root / "cloud.csv"
            data.to_csv(data_path, index=False)
            original = data_path.read_bytes()
            config["paths"] = {name: str(root / f"{name}.csv") for name in config["paths"]}
            config["storage"]["download_path"] = str(data_path)
            config["storage"]["expected_sha256"] = sha256(original)
            config["training"]["model_path"] = str(root / "model.joblib")
            config["training"]["validation_report"] = str(root / "validation.json")
            config_path = root / "config.yaml"
            config_path.write_text(yaml.safe_dump(config))
            with patch("src.preprocess.storage.download", return_value=data_path) as download:
                splits, population = prepare_splits(config_path)
                download.assert_called_once_with(config_path)
            with patch("src.train.prepare_splits", return_value=(GuardedSplits(splits), population)):
                pipeline, report = train(config_path)
            self.assertEqual(data_path.read_bytes(), original)
            self.assertFalse(Path(config["paths"]["processed"]).exists())
            self.assertEqual(report["population"]["excluded_rows"], 1)
            self.assertFalse(report["test_evaluated"])
            self.assertEqual(report["evaluation_partition"], "validation")
            self.assertEqual(json.loads((root / "validation.json").read_text()), report)
            saved = joblib.load(root / "model.joblib")
            inputs = splits["validation"][feature_names(config["training"])]
            self.assertTrue((pipeline.predict_proba(inputs) == saved["pipeline"].predict_proba(inputs)).all())
            self.assertEqual(saved["settings"], config["training"])
            self.assertEqual(report["processed_sha256"], sha256(original))
            self.assertEqual(saved["data_source"], report["data_source"])

    def test_nonconvergence_is_an_error(self):
        settings = deepcopy(self.settings)
        settings["logistic_regression"]["max_iter"] = 1
        pipeline = build_pipeline(settings)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            with self.assertRaises(ConvergenceWarning):
                pipeline.fit(self.data[feature_names(settings)], self.data.Churn.eq("Yes").astype(int))

    def test_training_outputs_cannot_overwrite_cloud_input(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            for field in ("model_path", "validation_report"):
                with self.subTest(field=field):
                    config = deepcopy(self.config)
                    config["training"][field] = config["storage"]["download_path"]
                    config_path.write_text(yaml.safe_dump(config))
                    with patch("src.preprocess.storage.download") as download:
                        with self.assertRaisesRegex(ValueError, "unprotected output paths"):
                            train(config_path)
                    download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
