# Customer Churn Predictor

AIPI 510 Module 3: build a reproducible machine learning pipeline, one step at a time.

This is Jim's solo student project, developed with Codex as an AI coding and learning assistant. Jim makes project decisions, reviews the work, and merges pull requests; Codex helps with implementation, testing, and explanations.

## Project overview

Our question is: **which customer profiles are associated with leaving a telecommunications company in the sample dataset?** We will build a supervised binary classification model to predict `Churn` (`Yes` or `No`), then serve it through an API and a browser interface.

Our primary evaluation metric is **ROC AUC**, which measures how well the model ranks customers who churn above customers who stay across classification thresholds. A score of 0.5 represents chance-level ranking, and 1.0 represents perfect ranking. An AUC of 0.8 does not mean 80% classification accuracy.

We will also report **precision** (of customers flagged as churning, how many actually churned) and **recall** (of customers who actually churned, how many the model caught) at a classification threshold selected using validation data. Final evaluation will use held-out test data that is not used to fit the model or choose the threshold.

Accuracy alone would be misleading: approximately 73.5% of customers in this sample stayed, so predicting `No` for everyone would appear 73.5% accurate while missing every customer who churned. These metrics will help us evaluate model behavior; the assignment emphasizes a reproducible production pipeline rather than achieving a particular score.

## Current step: cloud storage

Branch: `feat/cloud-storage`.

Local ingestion is implemented. This step adds upload and verified download
of the cleaned CSV using Google Cloud Storage. Jim sets up the bucket and
uploads the file; the repository supplies configuration and transfer code.
See the [cloud storage walkthrough](docs/CLOUD_STORAGE.md) for the next steps.
The bucket address is configured. A real authenticated download on November
23, 2026 matched the reviewed cleaned CSV's SHA-256 and retained all 7,043
customers, 21 columns, and 11 missing charge values. Changes await Jim's review.

## Project map

This is our agreed sequence of branches. Step 1 is merged into `main`; step 2 is implemented and verified with Google Cloud Storage, ready for PR review. Later steps are planned. We will choose the model, tracking tool, and interface framework together when we reach those decisions.

| Step | Branch | Outcome |
| --- | --- | --- |
| 1 | `feat/setup-data-ingestion` | Project setup, dataset selection, problem definition, and reproducible local ingestion |
| 2 | `feat/cloud-storage` | GCS storage and verified programmatic download implemented; review pending |
| 3 | `feat/training-pipeline` | Split data, preprocess, train a simple model, and evaluate using configuration-controlled settings |
| 4 | `feat/experiment-tracking` | Record experiment parameters, metrics, and model artifacts |
| 5 | `feat/prediction-api` | Build and test the `/predict` endpoint locally |
| 6 | `feat/docker` | Package and run training and serving in Docker |
| 7 | `feat/api-deployment` | Deploy and verify the public API |
| 8 | `feat/frontend` | Build and deploy an interface that calls the API |
| 9 | `docs/final-review` | Finish usage and deployment instructions, limitations, and collaboration reflections |

Each step follows: **branch → implementation and explanation → review → commit and push → PR → Jim's merge**. After a PR is merged, update local `main` from GitHub and create the next branch from that updated `main` so it inherits the completed work and this map. We create branches as each step begins, rather than creating all branches in advance.

Update this map's status and [collaboration log](collaboration.md) as each step progresses. Jim decides when to begin the next step and approves any changes to the plan.

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
- Customer IDs are for auditing rows, not model inputs. Feature selection and
  handling of demographics will be reviewed in the modeling step.

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

Use **Python 3.10** for the initial project environment. From this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The virtual environment keeps project packages separate from other projects.
The dependencies are pandas for tables, requests for downloading,
PyYAML for reading configuration, and the Google Cloud Storage client for
cloud transfers. We will add ML packages when we reach
the training step.

Download, clean, and check the data:

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
src/ingest.py              Download, validate, and clean the original dataset
src/storage.py             Upload/download cleaned CSV with SHA-256 verification
tests/                     Offline ingestion and storage checks
data/raw/                  Original CSV, unchanged and Git-ignored
data/processed/            Cleaned CSV, Git-ignored
data/cloud/                Verified cloud download, Git-ignored
reports/                   Aggregate data-quality report, committed to Git
docs/CLOUD_STORAGE.md       Cloud setup, authentication, and transfer walkthrough
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
