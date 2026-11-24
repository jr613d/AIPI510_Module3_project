# Customer Churn Predictor

**AIPI 510 Module 3: From Data to Decisions.** A reproducible machine learning pipeline that predicts whether a telecom customer will churn, served as a public API and an interactive web app.

![System architecture: users and the Streamlit app call the Cloud Run API, whose Docker image contains the model; separately, data flows from Hugging Face to Cloud Storage, training logs to Weights & Biases, and the image is pushed to Artifact Registry and deployed to Cloud Run.](docs/architecture.svg)

*Blue: what happens on every prediction. Black: how the data, model, and API are rebuilt and redeployed.*

| | Link |
| --- | --- |
| **Live app** | [https://aipi510module3project-churn.streamlit.app/](https://aipi510module3project-churn.streamlit.app/) |
| **Live API** | [https://churn-api-161834179213.us-east1.run.app](https://churn-api-161834179213.us-east1.run.app) (`POST /predict`, `GET /health`; interactive docs at [`/docs`](https://churn-api-161834179213.us-east1.run.app/docs)) |
| **Experiment tracking** | [W&B project `aipi510-churn`](https://forge.coreweave.com/wandb/jr613-d/aipi510-churn) (public, view-only) |
| **Dataset** | [IBM Telco Customer Churn on Hugging Face](https://huggingface.co/datasets/scikit-learn/churn-prediction) |

This is Jim Redden's solo project, built with AI coding assistants. Jim made the project decisions and reviewed and merged every pull request; the assistants helped with implementation, testing, and explanations. The [AI Collaboration Summary](AI%20Collaboration%20Summary.md) is the short version of how we worked together; the [collaboration log](collaboration.md) has the full record.

## Project overview and goals

**Question:** which customer profiles are associated with leaving a telecommunications company? The model is a supervised binary classifier that predicts `Churn` (`Yes` or `No`) from eight account and service details.

**Goal:** build the full production path, not the best possible model: cloud-hosted data, a configurable and reproducible training pipeline, tracked experiments, a containerized API deployed to the cloud, and a front-end that calls it.

## Dataset

[IBM's Telco Customer Churn sample](https://huggingface.co/datasets/scikit-learn/churn-prediction) (CC BY 4.0, credit IBM Sample Datasets and the Hugging Face mirror): **7,043 fictional customers** of a fictional company, with 21 columns covering demographics, services, account details, and the `Churn` target. About **26.5%** of customers churned.

- The data is **fictional teaching data**, not real customer records.
- The pinned download is verified by SHA-256 checksum. Cleaning keeps all rows and columns and preserves the 11 blank `TotalCharges` values as missing.
- For modeling, the 11 customers with zero months of tenure are excluded, leaving **7,032**. Customer IDs are never used as model inputs.

Details: [data guide](docs/DATA.md) (source verification, cleaning policy, modeling population, and splits).

## Model and evaluation

**Model:** L2-regularized **logistic regression** (`C = 1.0`) on eight inputs:

| Treatment | Inputs |
| --- | --- |
| Scaled numbers | `tenure`, `MonthlyCharges` |
| One-hot categories | `Contract`, `InternetService`, `TechSupport`, `OnlineSecurity`, `PaymentMethod`, `PaperlessBilling` |

Gender and other demographics are deliberately excluded. Data is split 70/15/15 into training, validation, and test sets (stratified by `Churn`, seed 42). Scaling and encoding are fitted on training data only.

**Metrics:** **ROC AUC** is the primary metric (how well the model ranks churners above non-churners), with **precision** and **recall** at the chosen threshold. Accuracy alone would mislead: predicting "no churn" for everyone is 73.5% accurate but catches no one.

**Model selection (validation set):**

- **Experiments:** 8 versions (8 vs. all 19 inputs × `C` = 0.01, 0.1, 1, 10) scored validation ROC AUC between 0.8487 and 0.8532, differences within chance. The simpler 8-input model with `C = 1.0` was kept. ([results](reports/experiments.md))
- **Threshold:** cutoffs from 0.20 to 0.70 were compared. **0.35** had the best F1 score, catching more churners at the cost of more false alarms. ([results](reports/threshold_selection.md))

**Final evaluation (test set, scored once):**

| Metric | Validation | **Test** |
| --- | ---: | ---: |
| ROC AUC | 0.849 | **0.819** |
| Precision at 0.35 | 57.3% | **52.7%** |
| Recall at 0.35 | 76.9% | **68.9%** |
| Churners caught | 216 of 281 | **193 of 280** |

Test scores are slightly lower than validation scores, as expected after making choices on validation data. The model was not changed after seeing the test results, and the evaluation script refuses to run a second time. ([test report](reports/test_evaluation.md))

Details: [model guide](docs/MODEL.md) (encoding, training settings, experiments, threshold, and evaluation).

## Cloud services used

| Service | Role |
| --- | --- |
| **Google Cloud Storage** | Hosts the cleaned dataset; training downloads it and verifies its checksum ([walkthrough](docs/CLOUD_STORAGE.md)) |
| **Weights & Biases** | Tracks every training run: settings, metrics, data and code versions, and the model file ([guide](docs/EXPERIMENT_TRACKING.md)) |
| **Google Artifact Registry** | Stores the Docker image that Cloud Run deploys |
| **Google Cloud Run** | Serves the `/predict` API from the Docker image, with the model built in ([deployment guide](docs/DEPLOYMENT.md)) |
| **Streamlit Community Cloud** | Hosts the public front-end app, which calls the Cloud Run API |
| **Hugging Face** | Original source of the dataset, pinned to an exact revision |

## Setup and usage

### Setup

Requires **Python 3.13**. From the repository root:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Train the model

All settings (inputs, split, seed, model parameters, threshold, cloud locations) live in [`config.yaml`](config.yaml).

```bash
python -m src.train                            # downloads the data, trains, records a W&B run
python -m src.train --tracking-mode disabled   # same, without W&B
```

Training works without any of Jim's credentials: the dataset file is publicly readable, and W&B is optional. To record runs in W&B, run `wandb login` with your own account first. The model is saved to `artifacts/churn_pipeline.joblib`.

The model-selection steps can be rerun with `python -m src.experiments` and `python -m src.thresholds`. The one-time test evaluation (`python -m src.evaluate`) refuses to run again because its report already exists.

### Run the tests

```bash
python -m unittest discover -s tests -v                               # 86 pipeline and API tests
frontend/.venv/bin/python -m unittest discover -s frontend/tests -v   # 20 front-end tests
```

All tests run offline, with no cloud or W&B access. (The front-end has its own environment; see below.)

### Build and test the API locally

```bash
python -m src.api --port 8001     # then open http://127.0.0.1:8001/docs
```

```bash
curl -X POST http://127.0.0.1:8001/predict -H "Content-Type: application/json" \
  -d '{"tenure": 12, "MonthlyCharges": 70.5, "Contract": "Month-to-month",
       "InternetService": "Fiber optic", "TechSupport": "No", "OnlineSecurity": "No",
       "PaymentMethod": "Electronic check", "PaperlessBilling": "Yes"}'
# {"churn_probability": 0.6705, "churn_prediction": "Yes", "threshold": 0.35}
```

The API rejects values outside the training data's ranges and returns plain-language errors. Details: [API guide](docs/API.md) (inputs, allowed values, errors).

### Run with Docker

One image trains, serves, and tests. The trained model is built into the image.

```bash
docker build -t churn-predictor .
docker run --rm -p 8001:8080 churn-predictor        # serve the API
docker run --rm churn-predictor test                # run the tests
```

Details: [Docker guide](docs/DOCKER.md) (training in the container, what goes into the image, and reproducing the project without the author's credentials).

### Run the front-end locally

```bash
cd frontend
python3.13 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
API_URL=http://127.0.0.1:8001 .venv/bin/streamlit run app.py
```

The app sends the eight inputs to the API and shows the churn probability and prediction. Its **Explore how the model sees this customer** section charts which choices would change the risk most, how risk varies with tenure and monthly charges, and where the customer falls on the logistic S-curve. Details: [front-end guide](frontend/README.md).

### Deploy to the cloud

**API (Google Cloud Run).** After the [one-time setup](docs/DEPLOYMENT.md#how-to-deploy-it-yourself), build the image for Cloud Run's x86 machines, push it to Artifact Registry, and deploy it as a public service:

```bash
IMAGE=us-east1-docker.pkg.dev/PROJECT/churn/churn-api:$(git rev-parse --short HEAD)
docker buildx build --platform linux/amd64 -t $IMAGE --load .
docker push $IMAGE          # prints the image digest (sha256:...)
gcloud run deploy churn-api \
  --image=us-east1-docker.pkg.dev/PROJECT/churn/churn-api@sha256:DIGEST \
  --region=us-east1 \
  --service-account=churn-api-runtime@PROJECT.iam.gserviceaccount.com \
  --allow-unauthenticated --port=8080 --cpu=1 --memory=1Gi \
  --min-instances=0 --max-instances=1 --timeout=30
```

The [deployment guide](docs/DEPLOYMENT.md) has the one-time setup, the exact settings used, and how to release a new model.

**Front-end (Streamlit Community Cloud).** At [share.streamlit.io](https://share.streamlit.io), sign in with GitHub and create an app from this repository with:

- **Branch:** `main`; **main file path:** `frontend/app.py` (Streamlit installs `frontend/requirements.txt`)
- **Advanced settings:** Python 3.13, and this secret, so the app knows where the API is:

  ```toml
  API_URL = "https://churn-api-161834179213.us-east1.run.app"
  ```

The app redeploys automatically when `main` changes. The first prediction after a quiet period can take a few seconds while Cloud Run starts the API.

## Ethics and limitations

This model is built on fictional data, so its results say nothing about real customers. The main considerations are summarized in [Ethics and Limitations](docs/ETHICS_AND_LIMITATIONS.md):

1. Ethics and fairness can't be fully evaluated without knowing the data's origin and how predictions are used.
2. Privacy: no re-identifiable data, and customer IDs are kept out of the model.
3. Excluding demographics does not rule out bias through proxy variables.
4. The small test set (about 280 churners) limits how precise the results are.

## Repository structure

```text
config.yaml          Pipeline configuration: data source, splits, model, threshold, tracking
requirements.txt     Pipeline and API dependencies (Python 3.13)
Dockerfile           One image for training, serving, and tests (docker-entrypoint.sh)
src/                 Ingestion, cloud storage, preprocessing, training, tracking,
                     experiments, threshold selection, evaluation, and the FastAPI app
tests/               Offline tests for the pipeline and API
frontend/            Streamlit app, local stand-in API, and front-end tests
reports/             Data summary, validation, experiment, threshold, and test reports
docs/                Guides: data, model, API, Docker, deployment, cloud storage, tracking,
                     ethics, and the architecture diagram
AI Collaboration Summary.md  Short summary of how the project was built with AI
collaboration.md     How the project was built with AI assistance, step by step
```

Data files, trained models, virtual environments, and W&B run files are not committed.

## How this project was built

Each step was built on its own branch and merged through a pull request after Jim's review.

| Step | Branch | Outcome |
| --- | --- | --- |
| 1 | `feat/setup-data-ingestion` | Dataset selection, problem definition, verified ingestion (PR #1) |
| 2 | `feat/cloud-storage` | Dataset hosted in Google Cloud Storage (PR #2) |
| 3 | `feat/training-pipeline` | Configurable preprocessing and logistic regression training (PR #3) |
| 4 | `feat/experiment-tracking` | Weights & Biases tracking (PR #4) |
| 4b | `feat/model-selection` | Experiments, threshold choice, one-time test evaluation (PR #5) |
| 5 | `feat/prediction-api` | FastAPI `/predict` endpoint (PR #6) |
| 6 | `feat/docker` | Docker image for training, serving, and tests (PR #8) |
| 6b | `feat/reproducibility` | Public data file and retraining without the author's credentials (PR #10) |
| 7 | `feat/api-deployment` | Public API on Google Cloud Run (PR #11) |
| 8 | `feat/frontend` | Streamlit front-end (PR #7), deployed on Streamlit Community Cloud |
| 9 | `docs/final-review`, `docs/readme-final` | Ethics and limitations (PR #9), final documentation, reflections |

The [AI Collaboration Summary](AI%20Collaboration%20Summary.md) gives the short version, including the rules the AI followed and Jim's reflection. The [collaboration log](collaboration.md) records the decisions, AI assistance, corrections, and verification for every step.
