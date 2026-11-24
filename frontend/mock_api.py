"""A stand-in for the real prediction API, for developing the front-end locally.

Run:  python frontend/mock_api.py [port]   (default: http://localhost:8000)
It follows the approved contract but does NOT use the trained model: the
probability is a made-up formula. Use it only to check the app's behavior.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math

from client import CHOICES, FIELDS

THRESHOLD = 0.35


def fake_probability(customer):
    """Illustrative only (NOT the trained model): every input nudges a made-up score."""
    score = -1.0 - 0.04 * customer["tenure"] + 0.02 * (customer["MonthlyCharges"] - 65)
    score += {"Month-to-month": 1.5, "One year": 0.0, "Two year": -1.0}[customer["Contract"]]
    score += {"Fiber optic": 0.6, "DSL": 0.0, "No": -0.6}[customer["InternetService"]]
    score += {"Yes": -0.5}.get(customer["TechSupport"], 0.0)
    score += {"Yes": -0.5}.get(customer["OnlineSecurity"], 0.0)
    score += 0.5 if customer["PaymentMethod"] == "Electronic check" else 0.0
    score += 0.3 if customer["PaperlessBilling"] == "Yes" else 0.0
    return round(1 / (1 + math.exp(-score)), 4)


def validate(body):
    if not isinstance(body, dict) or set(body) != set(FIELDS):
        return f"Send exactly these fields: {', '.join(FIELDS)}."
    if not isinstance(body["tenure"], int) or not isinstance(body["MonthlyCharges"], (int, float)):
        return "tenure must be an integer and MonthlyCharges a number."
    for field, allowed in CHOICES.items():
        if body[field] not in allowed:
            return f"{field} must be one of: {', '.join(allowed)}."
    return None


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok"})
        else:
            self.send_json(404, {"detail": "Not found"})

    def do_POST(self):
        if self.path != "/predict":
            return self.send_json(404, {"detail": "Not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except (ValueError, json.JSONDecodeError):
            return self.send_json(400, {"detail": "Request body must be JSON."})
        problem = validate(body)
        if problem:
            return self.send_json(422, {"detail": problem})
        probability = fake_probability(body)
        self.send_json(200, {"churn_probability": probability, "threshold": THRESHOLD,
                             "churn_prediction": "Yes" if probability >= THRESHOLD else "No"})


class MockServer(ThreadingHTTPServer):
    request_queue_size = 64  # The app sends several "what if?" requests at once.


def serve(port=8000):
    server = MockServer(("127.0.0.1", port), Handler)
    print(f"Mock churn API (fake predictions) on http://127.0.0.1:{port}")
    return server


if __name__ == "__main__":
    import sys
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8000).serve_forever()
