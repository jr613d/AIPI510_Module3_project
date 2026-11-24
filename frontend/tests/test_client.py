"""Front-end client tests against the local mock API (no cloud, no model).

Run from the repository:  python -m unittest discover -s frontend/tests -v
"""

from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests  # noqa: E402

from client import APIError, build_payload, health, parse_prediction, predict  # noqa: E402
from mock_api import Handler, MockServer  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402

CUSTOMER = dict(tenure=12, monthly_charges=70.5, contract="Month-to-month",
                internet_service="Fiber optic", tech_support="No", online_security="No",
                payment_method="Electronic check", paperless_billing="Yes")


class PayloadTests(unittest.TestCase):
    def test_payload_uses_the_contract_field_names(self):
        self.assertEqual(build_payload(**CUSTOMER), {
            "tenure": 12, "MonthlyCharges": 70.5, "Contract": "Month-to-month",
            "InternetService": "Fiber optic", "TechSupport": "No", "OnlineSecurity": "No",
            "PaymentMethod": "Electronic check", "PaperlessBilling": "Yes"})

    def test_no_internet_forces_matching_addon_values(self):
        payload = build_payload(**{**CUSTOMER, "internet_service": "No", "tech_support": "Yes"})
        self.assertEqual(payload["TechSupport"], "No internet service")
        self.assertEqual(payload["OnlineSecurity"], "No internet service")
        with self.assertRaises(ValueError):
            build_payload(**{**CUSTOMER, "tech_support": "No internet service"})

    def test_out_of_range_or_unknown_values_are_rejected(self):
        for change in ({"tenure": 0}, {"tenure": 73}, {"monthly_charges": 500},
                       {"contract": "Weekly"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                build_payload(**{**CUSTOMER, **change})

    def test_responses_outside_the_contract_are_rejected(self):
        good = {"churn_probability": 0.62, "churn_prediction": "Yes", "threshold": 0.35}
        self.assertEqual(parse_prediction(good), good)
        for bad in ({}, {**good, "churn_probability": 1.5}, {**good, "churn_prediction": "maybe"},
                    {**good, "threshold": "high"}, None):
            with self.subTest(bad=bad), self.assertRaises(APIError):
                parse_prediction(bad)


class MockServerCase(unittest.TestCase):
    """Start the mock API on a free port for the tests in a subclass."""

    @classmethod
    def setUpClass(cls):
        cls.server = MockServer(("127.0.0.1", 0), Handler)
        Handler.log_message = lambda *args: None  # Keep test output quiet.
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()


class MockAPITests(MockServerCase):
    def test_round_trip_prediction_and_health(self):
        self.assertTrue(health(self.url))
        result = predict(self.url, build_payload(**CUSTOMER))
        self.assertEqual(result["threshold"], 0.35)
        expected = "Yes" if result["churn_probability"] >= 0.35 else "No"
        self.assertEqual(result["churn_prediction"], expected)

    def test_api_validation_error_is_shown_readably(self):
        bad = {**build_payload(**CUSTOMER), "Contract": "Weekly"}
        with self.assertRaisesRegex(APIError, "rejected the input: Contract must be one of"):
            predict(self.url, bad)

    def test_unreachable_service_gives_a_friendly_error(self):
        self.assertFalse(health("http://127.0.0.1:9"))
        with self.assertRaisesRegex(APIError, "Could not reach"):
            predict("http://127.0.0.1:9", build_payload(**CUSTOMER))

    def test_fastapi_style_errors_and_server_errors(self):
        session = Mock()
        session.post.return_value = Mock(status_code=422, json=lambda: {
            "detail": [{"msg": "Input should be a valid integer"}]})
        with self.assertRaisesRegex(APIError, "valid integer"):
            predict(self.url, {}, session=session)
        session.post.return_value = Mock(status_code=422, json=lambda: {
            "error": "tenure must be between 1 and 72.", "details": []})
        with self.assertRaisesRegex(APIError, "tenure must be between 1 and 72"):
            predict(self.url, {}, session=session)
        session.post.return_value = Mock(status_code=503)
        with self.assertRaisesRegex(APIError, "HTTP 503"):
            predict(self.url, {}, session=session)
        session.post.side_effect = requests.Timeout()
        with self.assertRaisesRegex(APIError, "too long"):
            predict(self.url, {}, session=session)


if __name__ == "__main__":
    unittest.main()


class WhatIfTests(unittest.TestCase):
    def setUp(self):
        from client import what_if_requests, with_change
        self.what_if_requests, self.with_change = what_if_requests, with_change
        self.payload = build_payload(**CUSTOMER)

    def test_internet_changes_keep_addons_consistent(self):
        no_internet = self.with_change(self.payload, "InternetService", "No")
        self.assertEqual((no_internet["TechSupport"], no_internet["OnlineSecurity"]),
                         ("No internet service", "No internet service"))
        start = self.with_change(self.payload, "InternetService", "No")
        back = self.with_change(start, "InternetService", "DSL")
        self.assertEqual((back["TechSupport"], back["OnlineSecurity"]), ("No", "No"))
        dsl = self.with_change({**self.payload, "TechSupport": "Yes"}, "InternetService", "DSL")
        self.assertEqual(dsl["TechSupport"], "Yes")  # Switching between internet types keeps add-ons.

    def test_every_variation_is_a_valid_request_changing_one_choice(self):
        for kind, field, value, varied in self.what_if_requests(self.payload):
            self.assertEqual(varied[field], value)
            rebuilt = build_payload(varied["tenure"], varied["MonthlyCharges"], varied["Contract"],
                                    varied["InternetService"], varied["TechSupport"],
                                    varied["OnlineSecurity"], varied["PaymentMethod"],
                                    varied["PaperlessBilling"])
            self.assertEqual(rebuilt, varied)

    def test_no_internet_customer_gets_no_addon_rows(self):
        payload = build_payload(**{**CUSTOMER, "internet_service": "No"})
        fields = {field for kind, field, _, _ in self.what_if_requests(payload) if kind == "lever"}
        self.assertNotIn("TechSupport", fields)
        self.assertIn("InternetService", fields)


class ExploreTests(MockServerCase):
    def test_explore_returns_curves_and_levers_with_one_current_value_each(self):
        from client import biggest_lever, explore
        result = explore(self.url, build_payload(**CUSTOMER))
        for points in result["curves"].values():
            self.assertEqual(sum(point["current"] for point in points), 1)
        current = [row for row in result["levers"] if row["current"]]
        self.assertEqual(len(current), len({row["field"] for row in result["levers"]}))
        lever = biggest_lever(result["levers"])
        self.assertIsNotNone(lever)
        self.assertLess(lever["probability"], lever["from"])

    def test_biggest_lever_is_none_when_nothing_lowers_risk(self):
        from client import biggest_lever
        rows = [{"field": "Contract", "option": "A", "probability": 0.2, "current": True},
                {"field": "Contract", "option": "B", "probability": 0.4, "current": False}]
        self.assertIsNone(biggest_lever(rows))
