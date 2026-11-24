# Data: Source, Cleaning, and Modeling Population

How the dataset was sourced and verified, how it is cleaned, and which customers the model is trained on. Moved from the README during the final review; the README has a short summary.

## The dataset

We use [scikit-learn/churn-prediction on Hugging Face](https://huggingface.co/datasets/scikit-learn/churn-prediction),
a mirror of **IBM's fictional telecom customer sample**. The HF dataset card
lists **CC BY 4.0**. Credit IBM Sample Datasets and this HF mirror when sharing
the project or derived data.

- 7,043 customers and 21 columns.
- Target: `Churn`, with values `Yes` and `No`.
- The card describes customers who left in the last month. It does not
  establish a prospective prediction time, so we will not claim a validated
  forecast of future cancellations.
- Customer IDs are for auditing rows, not model inputs. The model uses eight service, account, and billing inputs (see the [model guide](MODEL.md)) and excludes demographics; this does not establish that its predictions are free of demographic bias.

## Where it came from and how it was created

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

## What each row contains

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

## Ingesting the data locally

To recreate the publisher's data locally for inspection or a future upload (not required for cloud-fed training):

```bash
python src/ingest.py
python -m unittest discover -s tests -v
```

Read the generated [data summary](../reports/data_summary.md). The JSON version
in the same folder is machine-readable evidence for later pipeline steps.

## Agreed cleaning policy

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

## Modeling population

Jim chose to require at least one month of tenure (`training.min_tenure_months: 1`) before splitting. In the current dataset this excludes 11 zero-tenure records, all with missing `TotalCharges` and `Churn = No`, leaving 7,032 records (1,869 `Yes`, 5,163 `No`) with no missing `TotalCharges`. This is an eligibility rule for this project; the data does not establish that zero-tenure records are prospects or cannot churn. The raw and cleaned CSVs retain all 7,043 rows. Median imputation was proposed but not adopted. The filter is implemented in `src/preprocess.py` and runs in memory, separately from ingestion and cleaning. Missing totals among eligible customers cause an error for review rather than silent imputation or exclusion.

## Preprocessing checkpoint: eligibility and splitting

After installing the requirements, inspect the preprocessing summary with:

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

[← Back to the README](../README.md)
