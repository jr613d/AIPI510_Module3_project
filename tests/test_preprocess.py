"""Check population eligibility, reproducibility, and separation of customers."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import yaml
from google.auth.exceptions import DefaultCredentialsError

from src.ingest import ROOT, sha256
from src.preprocess import filter_modeling_population, prepare_splits, stratified_splits


def sample_customers():
    return pd.DataFrame({
        "customerID": [f"customer-{i}" for i in range(202)],
        "tenure": [0, 0] + [1] * 200,
        "TotalCharges": [float("nan"), float("nan")] + [50.0] * 200,
        "Churn": ["No", "No"] + ["Yes"] * 40 + ["No"] * 160,
    })


class PopulationTests(unittest.TestCase):
    def test_excludes_zero_tenure_even_when_total_charges_are_present(self):
        data = sample_customers()
        data.loc[0, "TotalCharges"] = 25.0
        original = data.copy(deep=True)
        eligible, summary = filter_modeling_population(data)
        self.assertEqual(summary["excluded_rows"], 2)
        self.assertEqual(summary["input_rows"], 202)
        self.assertEqual(summary["eligible_rows"], 200)
        pd.testing.assert_frame_equal(eligible, original.iloc[2:])
        eligible.loc[2, "TotalCharges"] = 999
        pd.testing.assert_frame_equal(data, original)

    def test_missing_charge_for_eligible_customer_is_not_silently_dropped_or_imputed(self):
        data = sample_customers()
        data.loc[2, "TotalCharges"] = float("nan")
        with self.assertRaisesRegex(ValueError, "Eligible customers"):
            filter_modeling_population(data)

    def test_invalid_tenure_is_not_silently_excluded(self):
        for value in (float("nan"), -1, 1.5, float("inf")):
            with self.subTest(value=value):
                data = sample_customers().astype({"tenure": float})
                data.loc[0, "tenure"] = value
                with self.assertRaisesRegex(ValueError, "Tenure must"):
                    filter_modeling_population(data)

    def test_invalid_minimum_and_empty_population_fail(self):
        for minimum in (0, -1, 1.5, True):
            with self.subTest(minimum=minimum), self.assertRaises(ValueError):
                filter_modeling_population(sample_customers(), minimum)
        with self.assertRaisesRegex(ValueError, "No customers"):
            filter_modeling_population(sample_customers(), 2)


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.data, _ = filter_modeling_population(sample_customers())
        self.fractions = {"train": 0.7, "validation": 0.15, "test": 0.15}

    def test_splits_are_disjoint_complete_stratified_and_leave_input_unchanged(self):
        original = self.data.copy(deep=True)
        splits = stratified_splits(self.data, self.fractions, 42)
        seen = set()
        for name, part in splits.items():
            ids = set(part["customerID"])
            self.assertFalse(seen & ids)
            seen.update(ids)
            self.assertEqual(len(part), round(len(self.data) * self.fractions[name]))
            self.assertAlmostEqual(part["Churn"].eq("Yes").mean(), 0.2)
        self.assertEqual(seen, set(self.data["customerID"]))
        pd.testing.assert_frame_equal(self.data, original)

    def test_fixed_seed_reproduces_assignment_and_new_seed_changes_it(self):
        first = stratified_splits(self.data, self.fractions, 42)
        repeated = stratified_splits(self.data, self.fractions, 42)
        different = stratified_splits(self.data, self.fractions, 43)
        for name in first:
            pd.testing.assert_frame_equal(first[name], repeated[name])
        self.assertNotEqual(set(first["train"].customerID), set(different["train"].customerID))

    def test_invalid_fractions_fail(self):
        for train in (0.5, -0.1, float("nan"), True):
            with self.subTest(train=train), self.assertRaisesRegex(ValueError, "fractions"):
                stratified_splits(self.data, {**self.fractions, "train": train}, 42)

    def test_duplicate_ids_and_invalid_labels_fail(self):
        for column, value in (("customerID", "customer-3"), ("Churn", "Maybe")):
            with self.subTest(column=column):
                data = self.data.copy()
                data.loc[2, column] = value
                with self.assertRaises(ValueError):
                    stratified_splits(data, self.fractions, 42)


class CloudInputTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.cloud = self.root / "cloud.csv"
        self.local = self.root / "local.csv"
        sample_customers().to_csv(self.cloud, index=False)
        self.content = self.cloud.read_bytes()
        self.config = deepcopy(yaml.safe_load((ROOT / "config.yaml").read_text()))
        self.config["paths"] = {name: str(self.root / name) for name in self.config["paths"]}
        self.config["paths"]["processed"] = str(self.local)
        self.config["storage"]["expected_sha256"] = sha256(self.content)
        self.config["storage"]["download_path"] = str(self.cloud)
        self.config_path = self.root / "config.yaml"
        self.config_path.write_text(yaml.safe_dump(self.config))

    def test_cloud_data_alone_is_sufficient_and_records_actual_bytes(self):
        self.assertFalse(self.local.exists())
        with patch("src.preprocess.storage.download", return_value=self.cloud) as download:
            splits, report = prepare_splits(self.config_path)
        download.assert_called_once_with(self.config_path)
        self.assertEqual(report["source"]["sha256"], sha256(self.content))
        self.assertEqual(report["source"]["path"], str(self.cloud))
        self.assertEqual(report["eligible_rows"], 200)
        self.assertEqual(sum(len(part) for part in splits.values()), 200)
        self.assertEqual(self.cloud.read_bytes(), self.content)

    def test_edited_local_csv_is_ignored(self):
        self.local.write_text("not,the,cloud,dataset\n")
        with patch("src.preprocess.storage.download", return_value=self.cloud):
            _, report = prepare_splits(self.config_path)
        self.assertEqual(report["source"]["sha256"], sha256(self.content))
        self.assertEqual(self.local.read_text(), "not,the,cloud,dataset\n")

    def test_altered_download_is_rejected_before_parsing_or_splitting(self):
        self.cloud.write_bytes(self.content + b"\n")
        with patch("src.preprocess.storage.download", return_value=self.cloud), \
                patch("src.preprocess.stratified_splits") as split:
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                prepare_splits(self.config_path)
        split.assert_not_called()

    def test_failed_download_does_not_fall_back_to_valid_local_data(self):
        self.local.write_bytes(self.content)
        with patch("src.preprocess.storage.download", side_effect=DefaultCredentialsError("offline")), \
                patch("src.preprocess.stratified_splits") as split:
            with self.assertRaises(DefaultCredentialsError):
                prepare_splits(self.config_path)
        split.assert_not_called()


if __name__ == "__main__":
    unittest.main()
