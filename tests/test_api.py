"""Offline API checks with a small synthetic model; no cloud, W&B, or real data needed."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient
import joblib
import pandas as pd
import yaml

from src.api import ModelLoadError, create_app, round_half_up
from src.ingest import ROOT
from src.train import build_pipeline, validate_inputs

VALID = {
    "tenure": 12, "MonthlyCharges": 70.5, "Contract": "Month-to-month",
    "InternetService": "Fiber optic", "TechSupport": "No", "OnlineSecurity": "No",
    "PaymentMethod": "Electronic check", "PaperlessBilling": "Yes",
}


def synthetic_customers():
    """Internally consistent rows covering every category, with known numeric ranges."""
    rows = []
    for i in range(240):
        internet = ["DSL", "Fiber optic", "No"][i % 3]
        addon = "No internet service" if internet == "No" else ["Yes", "No"][i % 2]
        rows.append({
            "tenure": i % 72 + 1, "MonthlyCharges": 20.0 + (i % 99),
            "Contract": ["Month-to-month", "One year", "Two year"][i % 3],
            "InternetService": internet, "TechSupport": addon, "OnlineSecurity": addon,
            "PaymentMethod": ["Electronic check", "Mailed check", "Bank transfer (automatic)",
                              "Credit card (automatic)"][i % 4],
            "PaperlessBilling": ["Yes", "No"][i % 2],
            "Churn": "Yes" if (i % 5 == 0 or (internet == "Fiber optic" and i % 7 == 0)) else "No",
        })
    return pd.DataFrame(rows)


class ApiTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.config = yaml.safe_load((ROOT / "config.yaml").read_text())
        # Absolute temp paths so the tests never read or write project files.
        self.config["paths"] = {key: str(self.root / f"{key}.out") for key in self.config["paths"]}
        self.config["training"]["model_path"] = str(self.root / "model.joblib")
        self.settings = self.config["training"]
        data = synthetic_customers()
        inputs = validate_inputs(data, self.settings)
        self.pipeline = build_pipeline(self.settings)
        self.pipeline.fit(inputs, data.Churn.eq("Yes").astype(int))
        self.bundle = {
            "pipeline": self.pipeline, "settings": deepcopy(self.settings),
            "data_source": {"sha256": self.config["storage"]["expected_sha256"]},
            "input_ranges": {"tenure": {"min": 1.0, "max": 72.0},
                             "MonthlyCharges": {"min": 20.0, "max": 118.0}},
        }
        self.client = self.make_client()

    def make_client(self, bundle=None, config=None):
        config = config or self.config
        if bundle is not False:
            joblib.dump(bundle or self.bundle, config["training"]["model_path"])
        path = self.root / "config.yaml"
        path.write_text(yaml.safe_dump(config))
        return TestClient(create_app(path))

    def post(self, **changes):
        body = {**VALID, **changes}
        return self.client.post("/predict", json={k: v for k, v in body.items() if v is not None})

    def assert_rejected(self, response, *phrases):
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(set(body), {"error", "details"})
        for phrase in phrases:
            self.assertIn(phrase, body["error"])
        return body

    # --- Contract ---------------------------------------------------------------
    def test_health_reports_ok(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_predict_returns_contract_fields_matching_the_pipeline(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body), {"churn_probability", "churn_prediction", "threshold"})
        expected = self.pipeline.predict_proba(pd.DataFrame([VALID]))[0, 1]
        self.assertAlmostEqual(body["churn_probability"], expected)
        self.assertEqual(body["threshold"], self.settings["threshold"])
        self.assertEqual(body["churn_prediction"], "Yes" if expected >= body["threshold"] else "No")

    def test_threshold_comes_from_config_and_includes_equality(self):
        probability = self.post().json()["churn_probability"]
        for threshold, label in ((probability, "Yes"), (min(probability + 0.01, 0.99), "No")):
            with self.subTest(threshold=threshold):
                config = deepcopy(self.config)
                config["training"]["threshold"] = threshold
                self.client = self.make_client(config=config)
                body = self.post().json()
                self.assertEqual(body["threshold"], threshold)
                self.assertEqual(body["churn_prediction"], label)

    def test_cors_allows_any_website(self):
        response = self.client.options("/predict", headers={
            "Origin": "https://example.org", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "*")

    # --- Tenure rounding and ranges ---------------------------------------------
    def test_tenure_rounds_to_nearest_month_with_halves_up(self):
        self.assertEqual([round_half_up(v) for v in (0.4, 0.5, 2.5, 11.49, 71.5)], [0, 1, 3, 11, 72])
        whole = self.post(tenure=12).json()["churn_probability"]
        self.assertEqual(self.post(tenure=11.6).json()["churn_probability"], whole)
        self.assertEqual(self.post(tenure=12.4).json()["churn_probability"], whole)

    def test_tenure_outside_training_range_is_rejected_after_rounding(self):
        self.assertEqual(self.post(tenure=0.5).status_code, 200)
        self.assertEqual(self.post(tenure=72.49).status_code, 200)
        for value in (0, 0.49, 72.5, 100, -3):
            with self.subTest(value=value):
                self.assert_rejected(self.post(tenure=value), "tenure must be between 1 and 72 months",
                                     "training data")

    def test_monthly_charges_outside_training_range_are_rejected(self):
        self.assertEqual(self.post(MonthlyCharges=20.0).status_code, 200)
        self.assertEqual(self.post(MonthlyCharges=118.0).status_code, 200)
        for value in (19.99, 118.01, 0, -5):
            with self.subTest(value=value):
                self.assert_rejected(self.post(MonthlyCharges=value),
                                     "MonthlyCharges must be between 20.0 and 118.0", "training data")

    def test_numbers_must_be_real_numbers(self):
        for field in ("tenure", "MonthlyCharges"):
            for value in ("12", True, None):
                with self.subTest(field=field, value=value):
                    response = self.client.post("/predict", json={**VALID, field: value})
                    self.assert_rejected(response, field)
        nan = self.client.post("/predict", content='{"tenure": NaN}',
                               headers={"content-type": "application/json"})
        self.assertEqual(nan.status_code, 422)

    # --- Categories and consistency ---------------------------------------------
    def test_categories_must_match_training_values_exactly(self):
        body = self.assert_rejected(self.post(Contract="month-to-month"),
                                    "Contract must be one of", "'Month-to-month'", "capitalization")
        self.assertEqual(body["details"][0]["field"], "Contract")
        self.assert_rejected(self.post(PaymentMethod="Bitcoin"), "PaymentMethod must be one of")

    def test_internet_fields_must_be_consistent(self):
        self.assert_rejected(self.post(TechSupport="No internet service"),
                             "TechSupport cannot be 'No internet service'")
        self.assert_rejected(self.post(InternetService="No"),
                             "must be 'No internet service' when InternetService is 'No'")
        ok = self.post(InternetService="No", TechSupport="No internet service",
                       OnlineSecurity="No internet service")
        self.assertEqual(ok.status_code, 200)

    def test_missing_extra_and_malformed_bodies_get_readable_errors(self):
        missing = dict(VALID)
        del missing["Contract"]
        self.assert_rejected(self.client.post("/predict", json=missing), "Contract is required")
        self.assert_rejected(self.client.post("/predict", json={**VALID, "gender": "Male"}),
                             "gender is not a model input")
        self.assert_rejected(self.client.post("/predict", content="{not json",
                                              headers={"content-type": "application/json"}),
                             "not valid JSON")
        self.assert_rejected(self.client.post("/predict", json=[VALID]), "JSON object")

    def test_several_problems_are_all_reported(self):
        body = self.assert_rejected(self.post(tenure=500, Contract="Weekly"))
        self.assertEqual({item["field"] for item in body["details"]}, {"tenure", "Contract"})

    # --- Refusing to start ------------------------------------------------------
    def test_api_refuses_to_start_without_a_usable_model(self):
        cases = {
            "missing file": False,
            "no input ranges": {k: v for k, v in self.bundle.items() if k != "input_ranges"},
            "different data": {**self.bundle, "data_source": {"sha256": "0" * 64}},
            "different features": {**self.bundle, "settings": {
                **self.settings, "categorical_features": self.settings["categorical_features"][:-1]}},
        }
        for name, bundle in cases.items():
            with self.subTest(name), self.assertRaises(ModelLoadError):
                Path(self.settings["model_path"]).unlink(missing_ok=True)
                self.make_client(bundle=bundle)

    def test_invalid_threshold_stops_startup(self):
        for threshold in (0, 1, 1.5, True):
            with self.subTest(threshold=threshold), self.assertRaises(ModelLoadError):
                config = deepcopy(self.config)
                config["training"]["threshold"] = threshold
                self.make_client(config=config)


if __name__ == "__main__":
    unittest.main()
