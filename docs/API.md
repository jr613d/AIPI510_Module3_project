# Prediction API

The API serves the final model with [FastAPI](https://fastapi.tiangolo.com/) and the uvicorn web server. It loads the saved model once at startup and answers each request in milliseconds; it never trains, reads the dataset, or touches the test set.

## Run it locally

Train first if `artifacts/churn_pipeline.joblib` does not exist or predates this step (`python -m src.train`), then:

```bash
python -m src.api                       # serves http://127.0.0.1:8000
```

**Port conflicts:** only one program can use a port at a time. During development the front end's mock API uses port 8000, so run the real API on another port with `python -m src.api --port 8001` and replace `8000` with `8001` in the addresses below. If startup fails with "address already in use", another server is already on that port. The server only answers while it is running; stop it with Ctrl+C.

Open **http://127.0.0.1:8000/docs** for interactive documentation where you can send test requests in the browser. From another terminal:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" \
  -d '{"tenure": 12, "MonthlyCharges": 70.5, "Contract": "Month-to-month",
       "InternetService": "Fiber optic", "TechSupport": "No", "OnlineSecurity": "No",
       "PaymentMethod": "Electronic check", "PaperlessBilling": "Yes"}'
```

```json
{"churn_probability": 0.6705, "churn_prediction": "Yes", "threshold": 0.35}
```

(The probability is returned unrounded.) `GET /health` returns `{"status": "ok"}`. `churn_prediction` is `Yes` when the probability is at or above the threshold in `config.yaml`.

## Inputs

| Field | Meaning and allowed values |
| --- | --- |
| `tenure` | Months as a customer, **1–72**. Decimals are rounded to the nearest whole month, with halves rounding up (0.5 → 1), before the range check. |
| `MonthlyCharges` | Monthly bill in dollars, **18.40–118.60**. |
| `Contract` | `Month-to-month`, `One year`, `Two year` |
| `InternetService` | `DSL`, `Fiber optic`, `No` |
| `TechSupport` | `Yes`, `No`, `No internet service` |
| `OnlineSecurity` | `Yes`, `No`, `No internet service` |
| `PaymentMethod` | `Electronic check`, `Mailed check`, `Bank transfer (automatic)`, `Credit card (automatic)` |
| `PaperlessBilling` | `Yes`, `No` |

Jim decided these rules:

- **Exact categories.** Values must match the training data exactly, including capitalization. The front end offers only these values, so users cannot mistype them.
- **No predictions outside the training range.** The numeric ranges are the smallest and largest values in the training partition. Training now records them in the model file, and the API reads them from there. Values outside them are rejected rather than extrapolated.
- **Consistent internet fields.** `TechSupport` and `OnlineSecurity` must be `No internet service` exactly when `InternetService` is `No`, as in every row of the data.
- Numbers must be JSON numbers (not text such as `"12"`), and unexpected fields are rejected so typos are not silently ignored.

## Errors

Invalid requests return HTTP **422** with one plain-language sentence per problem, and every problem is reported at once:

```json
{
  "error": "tenure must be between 1 and 72 months, the range in the training data; got 0 (after rounding). The model does not make predictions outside that range.",
  "details": [{"field": "tenure", "message": "tenure must be between 1 and 72 months, ..."}]
}
```

`details[].field` is `null` for problems involving several fields (such as the internet-field rule) or the whole request.

The API **refuses to start** with a clear message if the model file is missing, was saved before training recorded input ranges, was trained on inputs or data that differ from `config.yaml`, or if the threshold is not between 0 and 1. It never runs with a mismatched model.

Allowed values and ranges come from the saved model, and the threshold comes from `config.yaml`, so the `/docs` page always shows what the running model accepts. Cross-origin requests (CORS) are allowed from any website, for `GET` and `POST` only: the API is read-only, uses no logins or cookies, and stores nothing.

## Tests

`tests/test_api.py` checks the contract with a small synthetic model (no cloud, W&B, or real data): response fields, the threshold cutoff, rounding, ranges, categories, the internet-field rule, readable errors, CORS, and each startup refusal.

[← Back to the README](../README.md)
