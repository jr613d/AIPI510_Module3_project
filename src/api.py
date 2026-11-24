"""Serve the trained churn model over HTTP.

Run locally:   python -m src.api            (then open http://127.0.0.1:8000/docs)
Endpoints:     POST /predict, GET /health

The API only loads an existing model file; it never trains, reads the
dataset, or touches the test partition. The classification threshold comes
from config.yaml. Allowed category values and numeric ranges come from the
saved model, so the API accepts exactly the kinds of customers the model
was trained on.
"""

import argparse
import math
from pathlib import Path
from typing import Literal

import joblib
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator, model_validator

from src.ingest import ROOT, load_config

NO_INTERNET = "No internet service"
INTERNET_DEPENDENT = ("TechSupport", "OnlineSecurity")
FIELD_DESCRIPTIONS = {
    "tenure": "Months as a customer. Decimals are rounded to the nearest whole month "
              "(halves round up) before the range check.",
    "MonthlyCharges": "Current monthly bill in dollars.",
    "Contract": "Contract term.",
    "InternetService": "Type of internet service, or No.",
    "TechSupport": "Tech support add-on. Use 'No internet service' only when InternetService is No.",
    "OnlineSecurity": "Online security add-on. Use 'No internet service' only when InternetService is No.",
    "PaymentMethod": "How the customer pays.",
    "PaperlessBilling": "Whether the customer receives paperless bills.",
}


class ModelLoadError(RuntimeError):
    """The model file is missing or does not match config.yaml; the API must not start."""


class PredictionResponse(BaseModel):
    churn_probability: float = Field(description="Model probability that the customer churns (0 to 1).")
    churn_prediction: Literal["Yes", "No"] = Field(
        description="Yes when churn_probability is at or above the threshold.")
    threshold: float = Field(description="Classification cutoff from config.yaml.")


class HealthResponse(BaseModel):
    status: Literal["ok"]


def load_model(config_path=ROOT / "config.yaml"):
    """Load the trusted local model file and check it against config.yaml."""
    config, _ = load_config(config_path)
    settings = config["training"]
    threshold = settings["threshold"]
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 < threshold < 1:
        raise ModelLoadError("training.threshold in config.yaml must be between 0 and 1.")
    model_path = ROOT / settings["model_path"]
    if not model_path.is_file():
        raise ModelLoadError(f"No model file at {model_path}. Train first: python -m src.train")
    bundle = joblib.load(model_path)  # Trusted output of src.train; never load untrusted files.
    if not isinstance(bundle, dict) or "pipeline" not in bundle:
        raise ModelLoadError(f"{model_path} is not a model saved by src.train.")
    if "input_ranges" not in bundle:
        raise ModelLoadError("The model file predates input-range recording. Retrain: python -m src.train")
    saved = bundle["settings"]
    for key in ("numeric_features", "categorical_features"):
        if saved[key] != settings[key]:
            raise ModelLoadError(f"The model's {key} do not match config.yaml. Retrain the model.")
    trained_on = bundle.get("data_source", {}).get("sha256")
    if trained_on != config["storage"]["expected_sha256"]:
        raise ModelLoadError("The model was trained on different data than config.yaml specifies.")
    encoder = bundle["pipeline"].named_steps["preprocessor"].named_transformers_["categorical"]
    categories = {name: [str(value) for value in values]
                  for name, values in zip(settings["categorical_features"], encoder.categories_)}
    return {
        "pipeline": bundle["pipeline"],
        "threshold": float(threshold),
        "numeric_features": list(settings["numeric_features"]),
        "categorical_features": list(settings["categorical_features"]),
        "categories": categories,
        "ranges": bundle["input_ranges"],
    }


def round_half_up(value):
    return math.floor(value + 0.5)


def customer_model(model):
    """Build the request schema from the model, so /docs shows the real allowed values."""
    fields = {}
    for name in model["numeric_features"]:
        bounds = model["ranges"][name]
        if name == "tenure":
            fields[name] = (int, Field(ge=int(bounds["min"]), le=int(bounds["max"]),
                                       description=FIELD_DESCRIPTIONS.get(name)))
        else:
            fields[name] = (float, Field(ge=bounds["min"], le=bounds["max"], allow_inf_nan=False,
                                         description=FIELD_DESCRIPTIONS.get(name)))
    for name, values in model["categories"].items():
        fields[name] = (Literal[tuple(values)], Field(description=FIELD_DESCRIPTIONS.get(name)))

    def no_text_or_booleans(cls, value):
        # JSON true/false or "12" are almost certainly client mistakes; require real numbers.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("must be a number")
        return value

    def round_tenure(cls, value):
        if isinstance(value, float) and math.isfinite(value):
            return round_half_up(value)
        return value

    def consistent_internet(self):
        has_internet = self.InternetService != "No"
        for name in INTERNET_DEPENDENT:
            value = getattr(self, name)
            if not has_internet and value != NO_INTERNET:
                raise ValueError(f"{name} must be '{NO_INTERNET}' when InternetService is 'No'.")
            if has_internet and value == NO_INTERNET:
                raise ValueError(f"{name} cannot be '{NO_INTERNET}' when InternetService is "
                                 f"'{self.InternetService}'.")
        return self

    validators = {
        "check_numbers": field_validator(*model["numeric_features"], mode="before")(no_text_or_booleans),
    }
    if "tenure" in model["numeric_features"]:
        validators["round_tenure"] = field_validator("tenure", mode="before")(round_tenure)
    if "InternetService" in model["categories"] and all(n in model["categories"] for n in INTERNET_DEPENDENT):
        validators["consistent_internet"] = model_validator(mode="after")(consistent_internet)
    example = {"tenure": 12, "MonthlyCharges": 70.5, "Contract": "Month-to-month",
               "InternetService": "Fiber optic", "TechSupport": "No", "OnlineSecurity": "No",
               "PaymentMethod": "Electronic check", "PaperlessBilling": "Yes"}
    return create_model(
        "Customer",
        __config__=ConfigDict(extra="forbid", json_schema_extra={"examples": [example]}),
        __validators__=validators,
        **fields,
    )


def readable_errors(errors, model):
    """Turn Pydantic's error list into one plain sentence per problem."""
    messages = []
    for error in errors:
        location = [str(part) for part in error.get("loc", ()) if part != "body"]
        field = location[0] if location else None
        kind = error.get("type", "")
        received = error.get("input")
        if kind == "json_invalid":
            messages.append({"field": None, "message": "The request body is not valid JSON."})
            continue
        if field is None:
            if kind in ("model_type", "dict_type", "model_attributes_type"):
                text = "The request body must be a JSON object with the customer's fields."
            else:
                text = str(error.get("msg", "Invalid request.")).removeprefix("Value error, ")
            messages.append({"field": None, "message": text})
            continue
        if kind == "missing":
            text = f"{field} is required."
        elif kind == "extra_forbidden":
            text = (f"{field} is not a model input. Expected fields: "
                    f"{', '.join(model['numeric_features'] + model['categorical_features'])}.")
        elif kind == "literal_error":
            allowed = ", ".join(f"'{value}'" for value in model["categories"][field])
            text = f"{field} must be one of {allowed} (exact spelling and capitalization); got {received!r}."
        elif kind in ("greater_than_equal", "less_than_equal"):
            bounds = model["ranges"][field]
            low, high = (int(bounds["min"]), int(bounds["max"])) if field == "tenure" else (
                bounds["min"], bounds["max"])
            unit = " months" if field == "tenure" else ""
            shown = f"{received} (after rounding)" if field == "tenure" else f"{received}"
            text = (f"{field} must be between {low} and {high}{unit}, the range in the training data; "
                    f"got {shown}. The model does not make predictions outside that range.")
        elif kind == "finite_number":
            text = f"{field} must be a finite number."
        else:
            text = f"{field} {str(error.get('msg', 'is invalid')).removeprefix('Value error, ')}."
        messages.append({"field": field, "message": text})
    return messages


def create_app(config_path=ROOT / "config.yaml"):
    """Load the model once and return the FastAPI app (fails to start if the model is unusable)."""
    model = load_model(config_path)
    Customer = customer_model(model)
    inputs = model["numeric_features"] + model["categorical_features"]

    app = FastAPI(
        title="Customer Churn Predictor API",
        description=("Predicts whether a customer of IBM's fictional telecom sample will churn. "
                     f"Threshold {model['threshold']}. This is a class project trained on a "
                     "teaching dataset, not a validated business tool."),
        version="1.0.0",
    )
    # Public, read-only predictions with no logins or cookies; any site may call it.
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"],
                       allow_headers=["Content-Type"])

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        details = readable_errors(error.errors(), model)
        summary = " ".join(item["message"] for item in details)
        return JSONResponse(status_code=422, content={"error": summary, "details": details})

    @app.get("/health", response_model=HealthResponse)
    def health():
        """The app only starts after the model loads, so a reply means it is ready."""
        return {"status": "ok"}

    @app.post("/predict", response_model=PredictionResponse)
    def predict(customer: Customer):
        row = pd.DataFrame([customer.model_dump()], columns=inputs)
        probability = float(model["pipeline"].predict_proba(row)[0, 1])
        return {
            "churn_probability": probability,
            "churn_prediction": "Yes" if probability >= model["threshold"] else "No",
            "threshold": model["threshold"],
        }

    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Use 0.0.0.0 inside Docker; 127.0.0.1 keeps it on this computer.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    try:
        app = create_app(args.config)
    except (ModelLoadError, OSError, KeyError, ValueError) as error:
        parser.exit(1, f"API not started: {error}\n")
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
