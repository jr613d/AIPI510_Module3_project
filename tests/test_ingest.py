"""Offline checks for the agreed cleaning policy and reproducible ingestion."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import pandas as pd
import yaml

from src.ingest import EXPECTED_COLUMNS, clean_data, fetch_raw, ingest, load_config


def sample_data():
    row = {
        "customerID": "sample-1", "gender": "Female", "SeniorCitizen": 0,
        "Partner": "No", "Dependents": "No", "tenure": 0,
        "PhoneService": "No", "MultipleLines": "No phone service",
        "InternetService": "DSL", "OnlineSecurity": "No", "OnlineBackup": "Yes",
        "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "No",
        "StreamingMovies": "No", "Contract": "Month-to-month",
        "PaperlessBilling": "Yes", "PaymentMethod": "Electronic check",
        "MonthlyCharges": 29.85, "TotalCharges": " ", "Churn": "No",
    }
    second = {**row, "customerID": "sample-2", "tenure": 3,
              "TotalCharges": " 89.55 ", "Churn": "Yes"}
    return pd.DataFrame([row, second], columns=EXPECTED_COLUMNS)


class CleaningTests(unittest.TestCase):
    def test_preserves_rows_ids_target_and_original_frame(self):
        raw = sample_data()
        original = raw.copy(deep=True)
        cleaned = clean_data(raw)
        pd.testing.assert_frame_equal(raw, original)
        self.assertEqual(len(cleaned), len(raw))
        self.assertEqual(list(cleaned.columns), EXPECTED_COLUMNS)
        self.assertEqual(cleaned.customerID.tolist(), raw.customerID.tolist())
        self.assertEqual(cleaned.Churn.tolist(), raw.Churn.tolist())

    def test_blank_charge_is_missing_and_valid_charge_is_numeric(self):
        cleaned = clean_data(sample_data())
        self.assertTrue(pd.isna(cleaned.loc[0, "TotalCharges"]))
        self.assertAlmostEqual(cleaned.loc[1, "TotalCharges"], 89.55)
        self.assertTrue(pd.api.types.is_numeric_dtype(cleaned.TotalCharges))

    def test_legitimate_no_service_category_is_not_missing(self):
        cleaned = clean_data(sample_data())
        self.assertEqual(cleaned.loc[0, "MultipleLines"], "No phone service")

    def test_invalid_nonblank_charge_is_rejected(self):
        raw = sample_data()
        raw.loc[1, "TotalCharges"] = "not-a-number"
        with self.assertRaises(ValueError):
            clean_data(raw)

    def test_duplicate_customer_is_rejected(self):
        raw = sample_data()
        raw.loc[1, "customerID"] = raw.loc[0, "customerID"]
        with self.assertRaisesRegex(ValueError, "Duplicate customer"):
            clean_data(raw)

    def test_unknown_or_missing_churn_is_rejected(self):
        for label in ["Maybe", " "]:
            with self.subTest(label=label):
                raw = sample_data()
                raw.loc[1, "Churn"] = label
                with self.assertRaisesRegex(ValueError, "Churn must"):
                    clean_data(raw)

    def test_unexpected_schema_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unexpected source columns"):
            clean_data(sample_data().drop(columns="Contract"))


class IngestionTests(unittest.TestCase):
    def test_bad_checksum_does_not_save_download(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "raw.csv"
            response = Mock(content=b"unexpected bytes")
            with patch("src.ingest.requests.get", return_value=response):
                with self.assertRaisesRegex(ValueError, "checksum"):
                    fetch_raw({"url": "https://example.invalid/data.csv", "sha256": "wrong"}, path)
            self.assertFalse(path.exists())

    def test_corrupted_cached_file_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "raw.csv"
            path.write_bytes(b"local contents")
            with patch("src.ingest.requests.get") as download:
                with self.assertRaisesRegex(ValueError, "checksum"):
                    fetch_raw({"sha256": "wrong"}, path)
                download.assert_not_called()
            self.assertEqual(path.read_bytes(), b"local contents")

    def test_repeated_run_is_identical_and_uses_cache(self):
        content = sample_data().to_csv(index=False).encode()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = {
                "dataset": {"name": "Test sample", "url": "https://example.invalid/data.csv",
                            "sha256": hashlib.sha256(content).hexdigest()},
                "paths": {"raw": str(root / "raw.csv"), "processed": str(root / "processed.csv"),
                          "summary_json": str(root / "summary.json"),
                          "summary_markdown": str(root / "summary.md")},
            }
            config_path = root / "config.yaml"
            config_path.write_text(yaml.safe_dump(config))
            response = Mock(content=content)
            with patch("src.ingest.requests.get", return_value=response) as download:
                first = ingest(config_path)
                outputs = {p: Path(p).read_bytes() for p in config["paths"].values()}
                second = ingest(config_path)
                self.assertEqual(download.call_count, 1)
            self.assertEqual(first, second)
            for path, original in outputs.items():
                self.assertEqual(Path(path).read_bytes(), original)
            self.assertEqual((root / "raw.csv").read_bytes(), content)
            cleaned = pd.read_csv(root / "processed.csv")
            self.assertEqual(len(cleaned), 2)
            self.assertEqual(int(cleaned.TotalCharges.isna().sum()), 1)
            self.assertEqual(json.loads((root / "summary.json").read_text())["processed_rows"], 2)

    def test_config_cannot_overwrite_raw_with_processed(self):
        with tempfile.TemporaryDirectory() as folder:
            config = {"paths": {"raw": "same.csv", "processed": "same.csv",
                                 "summary_json": "summary.json", "summary_markdown": "summary.md"}}
            path = Path(folder) / "config.yaml"
            path.write_text(yaml.safe_dump(config))
            with self.assertRaisesRegex(ValueError, "paths must be different"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
