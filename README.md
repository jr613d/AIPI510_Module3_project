# Customer Churn Predictor

AIPI 510 Module 3: build a reproducible machine learning pipeline, one step at a time.

This is Jim's solo student project, developed with Codex as an AI coding and learning assistant. Jim makes project decisions, reviews the work, and merges pull requests; Codex helps with implementation, testing, and explanations.

Our question is: **which customer profiles are associated with leaving a
telecommunications company in the sample dataset?** Later, we will train a
small classifier and serve it through an API and a browser interface.

## Current step: project setup and data ingestion

Branch: `feat/setup-data-ingestion`.

This step sets up Python, downloads the selected dataset, prepares a cleaned
copy, and produces a data-quality summary. It does not split data, encode
categories, train a model, create an API, or deploy cloud resources.

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
The initial dependencies are pandas for tables, requests for downloading,
and PyYAML for reading configuration. We will add ML packages when we reach
the training step.

Download, clean, and check the data:

```bash
python src/ingest.py
python -m unittest discover -s tests -v
```

Read the generated [data summary](reports/data_summary.md). The JSON version
in the same folder is machine-readable evidence for later pipeline steps.

## Data and outputs

Downloaded and cleaned CSVs stay local and are excluded from Git. We commit
the download script, configuration, source attribution, and aggregate data
summary so anyone can recreate and inspect the data.

```text
config.yaml                Source revision, checksum, and output paths
requirements.txt           Initial Python dependencies
src/                       Ingestion code
tests/                     Checks for ingestion behavior
data/raw/                  Original CSV, unchanged and Git-ignored
data/processed/            Cleaned CSV, Git-ignored
reports/                   Aggregate data-quality report, committed to Git
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
