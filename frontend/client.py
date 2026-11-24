"""Talk to the churn prediction API using the contract Jim approved.

POST /predict  {8 customer inputs}  ->  {churn_probability, churn_prediction, threshold}
GET  /health                        ->  {"status": "ok"}

No Streamlit code here, so the request/response logic can be tested on its own.
"""

import math

import requests

# Allowed values, taken from the training data (tenure-eligible customers).
CHOICES = {
    "Contract": ["Month-to-month", "One year", "Two year"],
    "InternetService": ["DSL", "Fiber optic", "No"],
    "TechSupport": ["No", "Yes", "No internet service"],
    "OnlineSecurity": ["No", "Yes", "No internet service"],
    "PaymentMethod": ["Electronic check", "Mailed check",
                      "Bank transfer (automatic)", "Credit card (automatic)"],
    "PaperlessBilling": ["Yes", "No"],
}
# Ranges of the model's TRAINING data (reports/training_validation.json, input_ranges).
# The API rejects values outside them, so the sliders stop at the same limits.
TENURE_RANGE = (1, 72)            # Months; the model was trained on tenure >= 1.
MONTHLY_CHARGES_RANGE = (18.40, 118.60)
FIELDS = ("tenure", "MonthlyCharges", "Contract", "InternetService", "TechSupport",
          "OnlineSecurity", "PaymentMethod", "PaperlessBilling")
TIMEOUT_SECONDS = 30  # Cloud services can take a few seconds to wake up.


class APIError(Exception):
    """A readable problem to show the user instead of a stack trace."""


def build_payload(tenure, monthly_charges, contract, internet_service, tech_support,
                  online_security, payment_method, paperless_billing):
    """Return the JSON body for /predict, enforcing the data's own consistency rules."""
    if internet_service == "No":
        # In the data, customers without internet always have these add-ons as
        # "No internet service", so the form cannot send another combination.
        tech_support = online_security = "No internet service"
    elif "No internet service" in (tech_support, online_security):
        raise ValueError("Tech support and online security need internet service.")
    payload = {
        "tenure": int(tenure), "MonthlyCharges": round(float(monthly_charges), 2),
        "Contract": contract, "InternetService": internet_service,
        "TechSupport": tech_support, "OnlineSecurity": online_security,
        "PaymentMethod": payment_method, "PaperlessBilling": paperless_billing,
    }
    for field, allowed in CHOICES.items():
        if payload[field] not in allowed:
            raise ValueError(f"{field} must be one of: {', '.join(allowed)}.")
    if not TENURE_RANGE[0] <= payload["tenure"] <= TENURE_RANGE[1]:
        raise ValueError(f"Tenure must be {TENURE_RANGE[0]}–{TENURE_RANGE[1]} months.")
    if not MONTHLY_CHARGES_RANGE[0] <= payload["MonthlyCharges"] <= MONTHLY_CHARGES_RANGE[1]:
        raise ValueError("Monthly charges are outside the range seen in training.")
    return payload


def parse_prediction(body):
    """Check the response matches the contract before showing it."""
    try:
        probability = float(body["churn_probability"])
        threshold = float(body["threshold"])
        label = body["churn_prediction"]
    except (KeyError, TypeError, ValueError):
        raise APIError("The API's response was not in the expected format.") from None
    if (not all(math.isfinite(x) and 0 <= x <= 1 for x in (probability, threshold))
            or label not in ("Yes", "No")):
        raise APIError("The API returned values outside the expected ranges.")
    return {"churn_probability": probability, "churn_prediction": label, "threshold": threshold}


def _error_detail(response):
    """Pull a readable message out of an error response, if there is one."""
    try:
        body = response.json()
        # The project API sends {"error": "...", "details": [...]}; FastAPI's default is "detail".
        detail = body.get("error") or body.get("detail")
    except (ValueError, AttributeError):
        return response.text[:200] or response.reason
    if isinstance(detail, list):  # FastAPI-style validation errors
        return "; ".join(str(item.get("msg", item)) if isinstance(item, dict) else str(item)
                         for item in detail)
    return str(detail) if detail else response.reason


def predict(api_url, payload, session=None):
    """Send one customer to the API and return the parsed prediction."""
    http = session or requests
    try:
        response = http.post(f"{api_url.rstrip('/')}/predict", json=payload, timeout=TIMEOUT_SECONDS)
    except requests.Timeout:
        raise APIError("The prediction service took too long to respond. Try again.") from None
    except requests.RequestException:
        raise APIError(f"Could not reach the prediction service at {api_url}.") from None
    if 400 <= response.status_code < 500:
        raise APIError(f"The API rejected the input: {_error_detail(response)}")
    if response.status_code != 200:
        raise APIError(f"The prediction service had a problem (HTTP {response.status_code}).")
    try:
        body = response.json()
    except ValueError:
        raise APIError("The API's response was not valid JSON.") from None
    return parse_prediction(body)


def health(api_url, session=None):
    """True if GET /health answers {"status": "ok"}."""
    http = session or requests
    try:
        response = http.get(f"{api_url.rstrip('/')}/health", timeout=TIMEOUT_SECONDS)
        return response.status_code == 200 and response.json().get("status") == "ok"
    except (requests.RequestException, ValueError, AttributeError):
        return False


# ---- "What if?" exploration: the same customer with one input changed ----

FIELD_LABELS = {
    "Contract": "Contract", "PaymentMethod": "Payment method",
    "PaperlessBilling": "Paperless billing", "InternetService": "Internet service",
    "TechSupport": "Tech support", "OnlineSecurity": "Online security",
}
TENURE_POINTS = [1, 3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72]
CHARGE_POINTS = [round(MONTHLY_CHARGES_RANGE[0] + step * (MONTHLY_CHARGES_RANGE[1] - MONTHLY_CHARGES_RANGE[0]) / 10, 2)
                 for step in range(11)]  # 11 evenly spaced points across the range


def with_change(payload, field, value):
    """Copy the customer with one input changed, keeping internet add-ons consistent."""
    changed = {**payload, field: value}
    if field == "InternetService":
        addon = "No internet service" if value == "No" else "No"
        if value == "No" or payload["InternetService"] == "No":
            changed["TechSupport"] = changed["OnlineSecurity"] = addon
    return changed


def what_if_requests(payload):
    """Return (kind, field, value, payload) for every variation to ask the API about."""
    requests_ = [("curve", "tenure", t, with_change(payload, "tenure", t))
                 for t in sorted(set(TENURE_POINTS) | {payload["tenure"]})]
    requests_ += [("curve", "MonthlyCharges", c, with_change(payload, "MonthlyCharges", c))
                  for c in sorted(set(CHARGE_POINTS) | {payload["MonthlyCharges"]})]
    for field, options in CHOICES.items():
        if field in ("TechSupport", "OnlineSecurity"):
            if payload["InternetService"] == "No":
                continue  # Add-ons are fixed without internet.
            options = ["No", "Yes"]
        for option in options:
            requests_.append(("lever", field, option, with_change(payload, field, option)))
    return requests_


def explore(api_url, payload, session=None, workers=4):
    """Ask the API about every variation (in parallel) and organize the answers."""
    from concurrent.futures import ThreadPoolExecutor

    planned = what_if_requests(payload)
    http = session or requests.Session()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda item: predict(api_url, item[3], session=http), planned))
    curves = {"tenure": [], "MonthlyCharges": []}
    levers = []
    for (kind, field, value, _), result in zip(planned, results):
        probability = result["churn_probability"]
        if kind == "curve":
            curves[field].append({"value": value, "probability": probability,
                                  "current": value == payload[field]})
        else:
            levers.append({"field": FIELD_LABELS[field], "option": value,
                           "probability": probability, "current": value == payload[field]})
    return {"curves": curves, "levers": levers}


def biggest_lever(levers):
    """The single change that lowers this customer's probability the most, if any."""
    current = {row["field"]: row["probability"] for row in levers if row["current"]}
    best = min((row for row in levers if not row["current"]),
               key=lambda row: row["probability"] - current[row["field"]], default=None)
    if best is None or best["probability"] >= current[best["field"]]:
        return None
    return {**best, "from": current[best["field"]]}
