# Churn predictor front-end (Streamlit)

A browser app that collects a customer's details, sends them to the prediction
API, and shows the churn prediction. It never loads the model itself: every
prediction is an HTTP request to the API.

## What the page does

- **Inputs.** Tenure and monthly charges are sliders limited to the ranges in the
  training data (1–72 months; $18.25–$118.75 in 5-cent steps). The model has not
  been tested outside these ranges. The six choices (contract, payment method,
  paperless billing, internet service, tech support, online security) show every
  option at once. Without internet service, tech support and online security are
  locked to "No internet service", matching the data.
- **Prediction.** The churn probability, "Likely to churn" or "Likely to stay",
  and how the probability compares with the model's 35% threshold. Probabilities
  below 1% or above 99% are shown as "<1%" and ">99%" rather than 0% or 100%.
- **Explore how the model sees this customer.** The app asks the API "what if?"
  by sending the same customer with one detail changed (about 40 requests,
  four at a time, cached for 10 minutes):
  - *What would change the risk?* A dot plot: for each choice, the probability
    under every option, with this customer's option in orange and the
    single biggest risk-lowering change called out.
  - *Tenure and charges:* the probability across the full tenure and
    monthly-charge ranges, with everything else unchanged.
  - *The S-curve:* how logistic regression turns a weighted score into a
    probability, and where this customer lands relative to the threshold.
    The score is the log-odds implied by the API's probability.

The result stays on screen while you explore. If an input changes, the page asks
for a new prediction instead of showing an out-of-date one.

## Files

```text
app.py              Streamlit page (layout, inputs, results, explore section)
client.py           API calls, input rules, and "what if?" variations (no Streamlit)
charts.py           Altair charts for the explore section
mock_api.py         Local stand-in API with FAKE predictions, for development only
requirements.txt    Front-end dependencies (Streamlit, requests)
tests/              Client, mock-API, and headless page tests
```

## API contract

The front-end follows the contract Jim approved for the prediction API:

```text
POST /predict
  request:  {"tenure": 12, "MonthlyCharges": 70.5, "Contract": "Month-to-month",
             "InternetService": "Fiber optic", "TechSupport": "No", "OnlineSecurity": "No",
             "PaymentMethod": "Electronic check", "PaperlessBilling": "Yes"}
  response: {"churn_probability": 0.62, "churn_prediction": "Yes", "threshold": 0.35}
GET /health  →  {"status": "ok"}
```

Error responses (4xx) are shown to the user as readable messages, as are timeouts
and an unreachable service.

## Run locally

Use a separate virtual environment for the front-end (Python 3.13):

```bash
cd frontend
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Until the real API is deployed, start the stand-in API in one terminal. Its
predictions come from a made-up formula, not the trained model:

```bash
.venv/bin/python mock_api.py          # http://localhost:8000 (or: mock_api.py 8011)
```

Then start the app in a second terminal:

```bash
.venv/bin/streamlit run app.py
```

The app calls `http://localhost:8000` unless `API_URL` is set, either as an
environment variable (`API_URL=https://… .venv/bin/streamlit run app.py`) or as a
Streamlit secret in `frontend/.streamlit/secrets.toml` (Git-ignored):

```toml
API_URL = "https://your-api-address"
```

If you edit `client.py` or `charts.py` while the app is running, restart
Streamlit (`Ctrl+C`, then run it again). It reloads `app.py` automatically but
can keep an old copy of the helper files in memory.

## Tests

From the repository root:

```bash
frontend/.venv/bin/python -m unittest discover -s frontend/tests -v
```

The 19 tests run against the stand-in API on a temporary port, with no cloud
access. They cover the request format and input rules, response checking and
error messages, the "what if?" variations, and the page itself (slider limits,
prediction display, locked add-ons, the explore section, and stale results).
The six page tests use Streamlit's headless `AppTest` and are skipped in an
environment without Streamlit.

## Deployment

Planned: Streamlit Community Cloud, with `frontend/app.py` as the entry point and
the deployed API's address in the app's `API_URL` secret. Deployment
instructions and the public link will be added when the API is live.
