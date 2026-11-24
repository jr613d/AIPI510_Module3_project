"""Headless tests of the Streamlit page against the local mock API.

Run with the front-end environment (it has Streamlit installed):
    frontend/.venv/bin/python -m unittest discover -s frontend/tests -v
"""

from http.server import ThreadingHTTPServer
import os
from pathlib import Path
import sys
import threading
import unittest

FRONTEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FRONTEND))

try:
    from streamlit.testing.v1 import AppTest
except ImportError:  # The back-end environment does not install Streamlit.
    AppTest = None

from mock_api import Handler, MockServer  # noqa: E402


class AppCase(unittest.TestCase):
    """Mock API on a free port, with API_URL pointing at it."""

    @classmethod
    def setUpClass(cls):
        Handler.log_message = lambda *args: None
        cls.server = MockServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.previous_url = os.environ.get("API_URL")
        os.environ["API_URL"] = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        if cls.previous_url is None:
            os.environ.pop("API_URL", None)
        else:
            os.environ["API_URL"] = cls.previous_url

    def run_app(self):
        app = AppTest.from_file(str(FRONTEND / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception, [e.value for e in app.exception])
        return app


@unittest.skipIf(AppTest is None, "Streamlit is not installed in this environment.")
class AppPageTests(AppCase):
    def test_sliders_are_limited_to_the_training_ranges(self):
        app = self.run_app()
        self.assertEqual((app.slider(key="tenure").min, app.slider(key="tenure").max), (1, 72))
        monthly = app.slider(key="monthly")
        self.assertEqual((monthly.min, monthly.max, monthly.step), (18.40, 118.60, 0.05))
        self.assertIn("has not been tested outside these ranges", app.caption[0].value)

    def test_prediction_is_displayed(self):
        app = self.run_app()
        app.button(key="predict").click().run()
        labels = {metric.label: metric.value for metric in app.metric}
        self.assertIn(labels["Prediction"], ("Likely to churn", "Likely to stay"))
        self.assertTrue(labels["Churn probability"].endswith("%"))
        self.assertFalse(app.error)

    def test_no_internet_locks_the_addon_services(self):
        app = self.run_app()
        app.segmented_control(key="internet").set_value("No").run()
        for key in ("tech_False", "security_False"):
            control = app.segmented_control(key=key)
            self.assertEqual(control.value, "No internet service")
            self.assertTrue(control.disabled)
        app.button(key="predict").click().run()
        self.assertFalse(app.error)

    def test_unreachable_api_shows_a_message_not_a_crash(self):
        os.environ["API_URL"] = "http://127.0.0.1:9"
        try:
            app = self.run_app()
            app.button(key="predict").click().run()
            self.assertIn("Could not reach", app.error[0].value)
        finally:
            os.environ["API_URL"] = f"http://127.0.0.1:{self.server.server_address[1]}"


if __name__ == "__main__":
    unittest.main()


@unittest.skipIf(AppTest is None, "Streamlit is not installed in this environment.")
class ExploreSectionTests(AppCase):
    def test_explore_section_renders_three_charts_and_a_lever(self):
        app = self.run_app()
        app.button(key="predict").click().run()
        self.assertEqual(len(app.tabs), 3)
        self.assertTrue(any("Biggest single lever" in (info.proto.title or "") or
                            "lower this customer's" in info.value for info in app.info))
        self.assertTrue(any("cannot show that a change would cause" in caption.value
                            for caption in app.caption))
        self.assertFalse(app.error)

    def test_changing_an_input_asks_for_a_new_prediction(self):
        app = self.run_app()
        app.button(key="predict").click().run()
        app.slider(key="tenure").set_value(40).run()
        self.assertIn("inputs changed", app.info[0].value)
        self.assertFalse(app.metric)
