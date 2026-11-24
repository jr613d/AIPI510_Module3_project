# Customer Churn Predictor

AIPI 510 Module 3: build a reproducible machine learning pipeline, one step at a time.

This is Jim's solo student project, developed with an AI coding and learning assistant. Jim makes project decisions, reviews the work, and merges pull requests; the AI assistant helps with implementation, testing, and explanations.

## Project overview

Our question is: **which customer profiles are associated with leaving a telecommunications company in the sample dataset?** We will build a supervised binary classification model to predict `Churn` (`Yes` or `No`), then serve it through an API and a browser interface.

Our primary evaluation metric is **ROC AUC**, which measures how well the model ranks customers who churn above customers who stay across classification thresholds. A score of 0.5 represents chance-level ranking, and 1.0 represents perfect ranking. An AUC of 0.8 does not mean 80% classification accuracy.

We will also report **precision** (of customers flagged as churning, how many actually churned) and **recall** (of customers who actually churned, how many the model caught) at a classification threshold selected using validation data. Final evaluation will use held-out test data that is not used to fit the model or choose the threshold.

Accuracy alone would be misleading: approximately 73.5% of customers in this sample stayed, so predicting `No` for everyone would appear 73.5% accurate while missing every customer who churned. These metrics will help us evaluate model behavior; the assignment emphasizes a reproducible production pipeline rather than achieving a particular score.

## Model selection and final evaluation

Merged in PR #5 (branch `feat/model-selection`). In this step we used W&B to compare model versions on **validation data**, chose the final model, and then scored it **once** on the held-out test data.

**1. Experiments** (`python -m src.experiments`, results in [reports/experiments.md](reports/experiments.md)). We trained 8 versions: the 8-input model and an all-19-input model, each with regularization strength `C` = 0.01, 0.1, 1, and 10. Validation ROC AUC ranged only from 0.8487 to 0.8532. Changing `C` made no meaningful difference, and all 19 inputs scored about 0.004 higher than 8, which is within the random variation expected for about 1,000 validation customers. Jim kept the **8-input model with `C = 1.0`**. It is simpler to explain, needs a shorter input form, and leaves out gender and other demographic inputs.

**2. Threshold** (`python -m src.thresholds`, results in [reports/threshold_selection.md](reports/threshold_selection.md)). The model outputs a churn probability, and the threshold decides when that counts as a predicted churner. We compared cutoffs from 0.20 to 0.70 on validation data. Jim chose **0.35**, which had the best balance of precision and recall (highest F1). Compared with 0.50, it catches 216 instead of 155 of the 281 validation churners, at the cost of 161 instead of 76 false alarms. This assumes that missing a customer who leaves costs more than an unnecessary retention contact; the dataset contains no real costs to confirm that.

**3. Final test** (`python -m src.evaluate`, results in [reports/test_evaluation.md](reports/test_evaluation.md)). After the choices above were committed, the final model was retrained and scored once on 1,055 test customers that were never used for training or for any choice:

| Final test result | Value |
| --- | ---: |
| ROC AUC | **0.8192** |
| Threshold | 0.35 |
| Precision | 52.7% |
| Recall | 68.9% |
| Churners caught | 193 of 280 |
| False alarms | 173 |

Test results are a little lower than validation (ROC AUC 0.849, precision 57.3%, recall 76.9%). This is expected: the validation data was used to make choices, so its scores are slightly optimistic, and with about 280 churners per group, scores vary by a few points by chance. The model was not adjusted after seeing the test results. `src/evaluate.py` refuses to run again once the test report exists, so the test set stays a one-time check.

All runs are in the W&B project `aipi510-churn`: the 8 experiments and the threshold comparison (group `model-selection`), the final training run, and the `final-test` run.

## Docker

Branch: `feat/docker` (step 6), in progress. One image runs the whole project through three entry points: `serve` (the default), `train`, and `test`. It uses the official `python:3.13.18-slim` base, installs `requirements.txt`, and runs as an ordinary user rather than root. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and start it before running these commands.

### Workflow: train → build → run

The trained model is **built into the image**, so the image serves without downloading anything or needing any login. The build copies `artifacts/churn_pipeline.joblib`, and checks it with the same startup checks the API uses. The build **fails** if the model file is missing (Docker reports `artifacts/churn_pipeline.joblib: not found`) or if it fails those checks, for example a model that does not match `config.yaml` (the build log shows the API's message). The build log and `/app/MODEL_SHA256` in the image record the model's SHA-256, which matches the `model_sha256` W&B records for the training run that produced it (when that run had tracking turned on).

1. Make sure a current model exists: run `python -m src.train` locally, or use the container's `train` command below.
2. Build the image (repeat after retraining or changing code):

   ```bash
   docker build -t churn-predictor .
   ```

3. Serve the API. Inside the container it listens on port 8080 (or `$PORT`, which Cloud Run sets). `-p 8001:8080` makes it available at port 8001 on your Mac, which avoids the front end's mock on port 8000:

   ```bash
   docker run --rm -p 8001:8080 churn-predictor
   ```

   Then open http://127.0.0.1:8001/docs or call `/health` and `/predict` as in the API section. Stop it with Ctrl+C.

4. Run the test suite inside the container (offline; no credentials needed):

   ```bash
   docker run --rm churn-predictor test
   ```

### Training in the container

Training needs two logins: Google, to download the dataset from the bucket, and W&B, to record the run. **Neither is stored in the image.** You connect your own login files to the container, read-only, only when you run `train`. The new model and validation report are written back to your Mac's `artifacts/` and `reports/` folders:

```bash
docker run --rm \
  -v "$HOME/.config/gcloud/application_default_credentials.json:/secrets/gcloud.json:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcloud.json \
  -v "$HOME/.netrc:/home/app/.netrc:ro" \
  -v "$PWD/artifacts:/app/artifacts" \
  -v "$PWD/reports:/app/reports" \
  churn-predictor train
```

- `-v source:destination:ro` connects a file or folder from your Mac into the container; `:ro` makes it read-only.
- The first line uses the Google login created by `gcloud auth application-default login` (see the [cloud storage walkthrough](docs/CLOUD_STORAGE.md)); the `.netrc` line uses the W&B login created by `wandb login`.
- Add `--tracking-mode disabled` after `train` to skip W&B (then the `.netrc` line is not needed).
- Then rebuild the image (step 2) so it serves the new model.

### What goes into the image

`.dockerignore` uses an allow-list. Only `requirements.txt`, `config.yaml`, `src/`, `tests/`, `reports/`, the entry-point script, and the one model file are sent to Docker. Data CSVs, virtual environments, `.git`, W&B output, and credential files are never included. The committed reports are included so the one-time test evaluation still refuses to run again inside the container.

Docker Desktop on an Apple-silicon Mac builds ARM images by default. Cloud Run runs on x86 (amd64), so deployment (step 7) builds the image for that platform.

## Prediction API

Branch: `feat/prediction-api` (step 5), merged in PR #6. The API serves the final model with [FastAPI](https://fastapi.tiangolo.com/) and the uvicorn web server. It loads the saved model once at startup and answers each request in milliseconds; it never trains, reads the dataset, or touches the test set.

### Run it locally

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

### Inputs

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

- **Exact categories.** Values must match the training data exactly, including capitalization. The front end will use dropdowns so users cannot mistype them.
- **No predictions outside the training range.** The numeric ranges are the smallest and largest values in the training partition. Training now records them in the model file, and the API reads them from there. Values outside them are rejected rather than extrapolated.
- **Consistent internet fields.** `TechSupport` and `OnlineSecurity` must be `No internet service` exactly when `InternetService` is `No`, as in every row of the data.
- Numbers must be JSON numbers (not text such as `"12"`), and unexpected fields are rejected so typos are not silently ignored.

### Errors

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

### Tests

`tests/test_api.py` checks the contract with a small synthetic model (no cloud, W&B, or real data): response fields, the threshold cutoff, rounding, ranges, categories, the internet-field rule, readable errors, CORS, and each startup refusal.

## Experiment tracking

Merged in PR #4. Every training run is recorded in **Weights & Biases (W&B)** with the training settings, validation metrics, data fingerprint, Git commit, and a versioned copy of the fitted model. After a one-time `wandb login`, `python -m src.train` uploads a run to the `aipi510-churn` W&B project automatically. `--tracking-mode offline` saves the run locally instead, and `--tracking-mode disabled` skips W&B. See the [experiment tracking guide](docs/EXPERIMENT_TRACKING.md) for setup, what is recorded, and verification.

## Training pipeline

Merged in PR #3. The training pipeline uses **logistic regression**, selected by Jim. It predicts the probability of `Churn = Yes`; ROC AUC remains our primary evaluation metric. The model choice is recorded in `config.yaml`.

The initial eight-input model has been trained and evaluated on validation data. The fitted preprocessing and classifier are saved together locally. The classification threshold (0.35) and the final test evaluation are described under the current step above. Training now calls `storage.download()` to fetch the configured cloud CSV and verify its fingerprint before filtering, splitting, encoding, and fitting. It does not read or fall back to the local processed CSV. Serving and deployment remain later steps.

**Modeling population:** Jim chose to require at least one month of tenure (`training.min_tenure_months: 1`) before splitting. In the current dataset this excludes 11 zero-tenure records, all with missing `TotalCharges` and `Churn = No`, leaving 7,032 records (1,869 `Yes`, 5,163 `No`) with no missing `TotalCharges`. This is an eligibility rule for this project; the data does not establish that zero-tenure records are prospects or cannot churn. The raw and cleaned CSVs retain all 7,043 rows. Median imputation was proposed but not adopted. The filter is implemented in `src/preprocess.py` and runs in memory, separately from ingestion and cleaning. Missing totals among eligible customers cause an error for review rather than silent imputation or exclusion.

### Preprocessing checkpoint: eligibility and splitting

After installing the requirements and configuring cloud access as described in the [storage walkthrough](docs/CLOUD_STORAGE.md), inspect the preprocessing summary with:

```bash
python -m src.preprocess
```

This downloads and verifies the cloud CSV into `data/cloud/`, then reads its bytes into memory and verifies the exact bytes passed to pandas. It applies the tenure rule and creates in-memory train/validation/test partitions. It prints aggregate counts, cloud URI, download path, and the actual and expected SHA-256 fingerprints. It preserves the raw and locally processed CSVs; only the verified cloud download is refreshed. Training reuses these same functions. Neither preprocessing nor training requires a local processed CSV, and failed cloud access or a checksum mismatch stops the run without falling back to local data.

Splitting uses stratified random sampling by `Churn` in both stages, with configurable 70%/15%/15% defaults and random seed 42. Stratification preserves approximate class proportions; it does not balance the classes to 50/50. Integer row counts require rounding.

| Partition | Customers | Churn = Yes | Churn rate |
| --- | ---: | ---: | ---: |
| Training | 4,922 | 1,308 | 26.57% |
| Validation | 1,055 | 281 | 26.64% |
| Test | 1,055 | 280 | 26.54% |

Checks confirmed that every eligible customer appears in exactly one partition, repeated runs reproduce the assignments, and both source CSVs remain unchanged. IDs remain in these partitions for auditing and are excluded from model inputs.

### Encoding and training checkpoint

Jim chose to start with eight understandable inputs. The rationale is to keep the first production pipeline manageable, make the model easier to explain, and reduce the number of fields required by the eventual API and interface. Tenure, contract, charges, services, and billing preferences have a plausible connection to churn. This is a deliberate scope and learning choice, not evidence that 19 predictors would be too many or that these eight are the strongest predictors. No automated feature selection or feature-set comparison informed this choice.

**Optional future exploration, if time permits:** Revisit the eight-input choice by comparing it with all 19 eligible predictors using the same customer partitions, preprocessing approach, logistic regression settings, and validation metrics. Assess whether any improvement justifies the extra inputs and complexity. This comparison is deferred so we can complete the production pipeline first. It must not guide selection using the held-out test set. If we revisit feature selection after final test evaluation, treat the existing test result as belonging to the original model and use a fresh untouched holdout or a suitably designed nested evaluation for a new independent performance claim.

| Treatment | Inputs |
| --- | --- |
| Numeric scaling | `tenure`, `MonthlyCharges` |
| One-hot encoding | `Contract`, `InternetService`, `TechSupport`, `OnlineSecurity`, `PaymentMethod`, `PaperlessBilling` |

One-hot encoding creates a 0/1 indicator for each category, avoiding an invented numeric order. For example, `Contract` produces indicators for `Month-to-month`, `One year`, and `Two year`. We retain all category indicators (`drop=None`) and use L2-regularized logistic regression. The current training categories produce 18 indicator columns, plus two scaled numeric columns: **20 model columns from eight original inputs**. Meaningful categories such as `No internet service` are retained. Unseen categories are encoded as all zeros for the corresponding field (`handle_unknown="ignore"`); this permits prediction but does not teach the model the meaning of that new category.

Numeric scaling subtracts each training column's mean and divides by its standard deviation. The scaler and category vocabulary are fitted only on training data, then reused without refitting for validation. The target maps `No` to 0 and `Yes` to 1. No imputation or class balancing is used. The classifier uses solver `lbfgs`, L2 regularization with `C: 1.0`, and a maximum of 1,000 iterations; the run stops if fitting does not converge.

Run training and validation from the repository:

```bash
python -m src.train
python -m unittest discover -s tests -v
```

Optional `--config <path>` arguments are supported by preprocessing and training. Inputs, split proportions, seed, regularization strength, iteration limit, provisional threshold, and output paths are controlled by `config.yaml`.

Outputs are a local Git-ignored fitted pipeline at `artifacts/churn_pipeline.joblib` and an aggregate [validation report](reports/training_validation.json). Both record the cloud source URI, download path, and checksum of the exact in-memory CSV bytes used for splitting and training. The report also records configuration, environment versions, partition counts, encoded column names, and validation metrics. The saved artifact contains the scaler, encoder, classifier, and settings. It can be recreated from the cloud data and configuration; the report is suitable for committing, while fitted artifacts remain local. Each successful run is also recorded in Weights & Biases (see Experiment tracking above).

| Initial validation result (before threshold selection) | Value |
| --- | ---: |
| ROC AUC | 0.8488 |
| Precision at provisional cutoff 0.5 | 67.10% |
| Recall at provisional cutoff 0.5 | 55.16% |
| Actual churners flagged | 155 |
| Customers who stayed but were flagged | 76 |
| Actual churners missed | 126 |
| Customers who stayed and were not flagged | 698 |

These were the first validation results, at the provisional 0.5 cutoff used before threshold selection. The final model uses threshold 0.35; see the current step above for the experiments, threshold choice, and final test result. The dataset remains a fictional teaching sample and the model applies to the project's tenure-eligible population.

The full suite of 69 offline tests passes under Python 3.13 (11 ingestion, 11 cloud-storage, 12 preprocessing, 6 training, 15 experiment tracking, 5 experiments, 5 threshold selection, 4 final evaluation), along with `pip check`. The tests include train-only scales and category vocabulary, unseen categories, ID/target exclusion, missing-input rejection, saved-model reloading, convergence failure, and no test-partition access by the training routine. Cloud tests use mocked transfers. Separately, a live run of `python -m src.train` under Python 3.13 downloaded and verified the cloud CSV and reproduced the validation results below exactly.

## Project map

This is our agreed project map. Steps 1–4 are merged into `main` through PRs #1–#4. Jim added step 4b (model selection and the one-time test evaluation) after experiment tracking; it is in progress. The training model is logistic regression; remaining technology choices will be made together at the relevant step. All later steps are planned.

| Step | Branch | Outcome |
| --- | --- | --- |
| 1 | `feat/setup-data-ingestion` | Project setup, dataset selection, problem definition, and reproducible local ingestion |
| 2 | `feat/cloud-storage` | GCS storage and verified programmatic download implemented; merged in PR #2 |
| 3 | `feat/training-pipeline` | Split data, preprocess, train a simple model, and evaluate using configuration-controlled settings; merged in PR #3 |
| 4 | `feat/experiment-tracking` | Record experiment parameters, metrics, and model artifacts in Weights & Biases; merged in PR #4 |
| 4b | `feat/model-selection` | Compare model versions in W&B, choose the threshold on validation data, and score the test set once; merged in PR #5 |
| 5 | `feat/prediction-api` | Build and test the `/predict` endpoint locally; merged in PR #6 |
| 6 | `feat/docker` | Package and run training and serving in Docker |
| 7 | `feat/api-deployment` | Deploy and verify the public API |
| 8 | `feat/frontend` | Build and deploy an interface that calls the API; Streamlit app in progress |
| 9 | `docs/final-review` | Finish usage and deployment instructions, limitations, and collaboration reflections |

Each step follows: **branch → implementation and explanation → review → commit and push → PR → Jim's merge**. After a PR is merged, update local `main` from GitHub and create the next branch from that updated `main` so it inherits the completed work and this map. We create branches as each step begins, rather than creating all branches in advance.

Update this map's status and [collaboration log](collaboration.md) as each step progresses. Jim decides when to begin the next step and approves any changes to the plan.

Cloud storage is implemented and was verified against the configured bucket in PR #2. See the [cloud storage walkthrough](docs/CLOUD_STORAGE.md) for setup, authentication, and `python -m src.storage download`. Cloud transfers preserve all 7,043 source rows; the tenure exclusion remains a separate modeling step.

## Front-end app

Branch: `feat/frontend` (step 8, in progress). A Streamlit app in [`frontend/`](frontend/README.md) collects a customer's eight inputs, sends them to the prediction API, and shows the churn probability, the prediction, and how it compares with the 35% threshold. Tenure and monthly charges are limited to the ranges seen in the training data, because the model has not been tested outside them.

Below the prediction, an **Explore how the model sees this customer** section asks the API "what if?" questions (the same customer with one detail changed) and charts the answers: which choices would change the risk most, how risk changes across tenure and monthly charges, and where the customer lands on logistic regression's S-curve.

The front-end never loads the model; it only calls the API. Until the API is deployed, it is developed against a local stand-in API with fake predictions. See the [front-end README](frontend/README.md) to run it locally and for its tests. The public link will be added after deployment.

## Dataset

We use [scikit-learn/churn-prediction on Hugging Face](https://huggingface.co/datasets/scikit-learn/churn-prediction),
a mirror of **IBM's fictional telecom customer sample**. The HF dataset card
lists **CC BY 4.0**. Credit IBM Sample Datasets and this HF mirror when sharing
the project or derived data.

- 7,043 customers and 21 columns.
- Target: `Churn`, with values `Yes` and `No`.
- The card describes customers who left in the last month. It does not
  establish a prospective prediction time, so we will not claim a validated
  forecast of future cancellations.
- Customer IDs are for auditing rows, not model inputs. The initial model uses the eight service/account/billing inputs listed above and excludes demographics; this does not establish that its predictions are free of demographic bias.

### Where it came from and how it was created

IBM published Telco Customer Churn as sample material for analytics and
machine learning demonstrations. Our HF CSV is **byte-for-byte identical**
to the CSV in [IBM's public sample repository](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv):
both contain 970,457 bytes and have the source checksum in `config.yaml`.

Both the HF card and [IBM's sample documentation](https://community.ibm.com/community/user/blogs/steven-macko/2019/07/11/telco-customer-churn-1113)
describe a fictional company. The reviewed descriptions do not document a
real customer collection process or a reproducible data-generation algorithm.
We therefore describe this as **fictional sample data**, not a verified
extract of real customer records, a customer survey, or anonymized real data.

IBM also documents an expanded version with location, satisfaction scores,
churn reasons, and other fields. Our simpler 21-column CSV does not include
those extra fields or observation dates. We should not mix the two schemas
or infer a dated forecasting period from the expanded version's narrative.

### What each row contains

Each row represents one fictional customer, rather than a transaction or
a monthly history of that customer.

| Group | Columns | Examples |
| --- | ---: | --- |
| Identifier | 1 | `customerID` |
| Demographics | 4 | `gender`, `SeniorCitizen`, `Partner`, `Dependents` |
| Services | 9 | Phone and internet services, security, backup, device protection, support, streaming |
| Account and billing | 6 | `tenure`, contract, billing preference, payment method, monthly and total charges |
| Outcome | 1 | `Churn`: `Yes` or `No` |

`tenure` is months as a customer. `MonthlyCharges` is the monthly bill, and
`TotalCharges` is the cumulative charge amount in the sample. The target
labels are 1,869 `Yes` and 5,174 `No`: approximately **26.5% churn**.
These are properties of this teaching sample, not estimates for the telecom
industry. A model built here demonstrates the pipeline; it still needs real
business data and independent evaluation before practical use.

The source URL in `config.yaml` points to an exact HF revision. A SHA-256
checksum identifies the exact bytes we expect, rather than assuming that a
file with the same name still has the same contents.

## Setup

Use **Python 3.13**, recorded in `.python-version`, for this project and the later Docker/deployment work. Jim approved upgrading from Python 3.10 after the Google SDK's support warning. Python 3.10 has reached end of life; Python 3.13 is supported through October 2029. See the [Python support schedule](https://devguide.python.org/versions/) and [Google client support policy](https://docs.cloud.google.com/python/docs/supported-python-versions).

For a fresh environment, install Python 3.13 (for example with [uv's Python manager](https://docs.astral.sh/uv/guides/install-python/)) and run from this repository:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The virtual environment keeps project packages separate from other projects.
The dependencies are pandas for tables, requests for downloading, PyYAML for reading configuration, google-cloud-storage for verified cloud transfers, scikit-learn for splitting and logistic regression, joblib for saving the fitted pipeline, and wandb for experiment tracking. NumPy and SciPy are pinned to the versions used by the original training run so the Python upgrade does not also change those numerical libraries.

Jim's checkout uses a project-local Python runtime in the ignored `.python-runtime/` directory and a Python 3.13 `.venv`. System Python is unchanged. The old Python 3.10 environment is retained in ignored `.venv-py310-backup/` for rollback; activate `.venv` for current work. If your terminal was already activated before the upgrade, reactivate it and check `python --version`. Installing Python 3.13 alone does not upgrade an existing virtual environment; fresh clones should create `.venv` with the chosen interpreter as above.

To recreate the publisher's data locally for inspection or a future upload (not required for cloud-fed training):

```bash
python src/ingest.py
python -m unittest discover -s tests -v
```

Read the generated [data summary](reports/data_summary.md). The JSON version
in the same folder is machine-readable evidence for later pipeline steps.

## Data and outputs

Raw, cleaned, and cloud-downloaded CSVs are excluded from Git. The cleaned
CSV also lives in a private cloud bucket after Jim uploads it. We commit the
scripts, configuration, source attribution, and aggregate data summary so
others can recreate the local data; cloud access requires their own permission.

```text
config.yaml                Source revision, checksum, and output paths
requirements.txt           Initial Python dependencies
src/                       Ingestion, cloud transfers, preprocessing, training, W&B tracking,
                           experiments, threshold selection, and final evaluation
tests/                     Offline ingestion, storage, preprocessing, training, and tracking checks
data/raw/                  Original CSV, unchanged and Git-ignored
data/processed/            Cleaned CSV, Git-ignored
data/cloud/                Verified cloud download, Git-ignored
reports/                   Aggregate data-quality, validation, experiment, threshold, and test reports
docs/CLOUD_STORAGE.md       Cloud setup, authentication, and transfer walkthrough
docs/EXPERIMENT_TRACKING.md W&B setup, usage, and verification
frontend/                  Streamlit app, local stand-in API, and front-end tests
wandb/                     Local W&B run files, Git-ignored
artifacts/                 Recreated fitted pipeline, Git-ignored
```

We retain the full dataset during ingestion. We will select model inputs
later. Operations that learn from the data, such as imputation, scaling, and
category encoding, belong after the train/validation/test split.

### Agreed cleaning policy

- Save the original CSV exactly as downloaded and verify its checksum.
- Trim surrounding whitespace and convert the numeric columns to numbers.
- Preserve all 7,043 rows and all 21 columns, including the `Yes`/`No` target.
- Preserve 11 blank `TotalCharges` entries as missing numeric values. All
  11 belong to customers with zero tenure, but we do not assume a zero bill.
- Keep `No internet service` and `No phone service` as meaningful categories.
- Reject unexpected columns, duplicate IDs, invalid labels, or malformed
  numbers rather than silently changing or removing records.

The script reuses an existing raw file only when its checksum matches.
Repeated runs generate the same outputs. Ingestion uses no random sampling
and does not fill missing values or learn any model transformations.

## How we collaborate

1. Work on one agreed feature branch and scope at a time.
2. Explain each stage and pause for decisions or questions.
3. Review the diff and relevant checks together before committing.
4. Make focused commits, push the branch, and open a PR into `main`.
5. Jim reviews and merges the PR before the next step starts.

We use branches, focused commits, and pull requests to keep Jim's solo project organized and make each learning step reviewable. AI assistance will be documented honestly, and we will work through the implementation together so Jim understands what is submitted.
