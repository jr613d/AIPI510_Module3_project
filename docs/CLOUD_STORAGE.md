# Cloud storage walkthrough

## What this step adds

GitHub stores the code and configuration. Google Cloud Storage holds the
cleaned CSV. Your local Google credentials authorize Python to access that
private file. A bucket name is an address, not a password or access grant.

```text
HF source → src/ingest.py → data/processed/telco_churn.csv
                                         ↓ upload in console or with Python
                          gs://BUCKET/processed/telco_churn.csv
                                         ↓ python -m src.storage download
                            data/cloud/telco_churn.csv
```

The training pipeline now calls this download function and uses the verified
cloud bytes for preprocessing and training. Transfers preserve all 7,043 rows;
the tenure eligibility rule is applied separately in model preprocessing.

## 1. Jim creates the bucket and uploads the cleaned file

In your Google Cloud project, create a private Cloud Storage bucket. Keep
public access prevention enabled and use uniform bucket-level access.
You do not need to make this dataset publicly readable for the assignment.

Upload **`data/processed/telco_churn.csv`**, not the original in `data/raw/`.
Upload the file unchanged rather than opening and resaving it in a spreadsheet.
You can put it inside a `processed` folder or upload it at the bucket root;
the configuration must match the actual object name.

The existing file from the ingestion checkout on Jim's Mac is:

```text
/Users/jim/dukeaipi/510_Sourcing_Data/Module_3_project/AIPI510_Module3_project/data/processed/telco_churn.csv
```

Record the **project ID** (not just the display name) and the object's
**gs:// URI**, available in its details. For example:

```text
Project ID: aipi510-example
Object URI: gs://aipi510-example-data/processed/telco_churn.csv
```

Those identifiers are safe to put in configuration. Login tokens and keys
are not needed in the repository or chat.

## 2. Point config.yaml to that object

Jim reported the following console setup. A real authenticated download has
verified object access and contents; the region, storage class, and project
number below remain Jim-reported console metadata:

| Setting | Value |
| --- | --- |
| Project name | My First Project |
| Project ID | `project-902e069e-c3ed-49c2-a13` |
| Project number | `161834179213` |
| Bucket | `kangaroo_baseball_field` |
| Bucket location | `us-east1` (South Carolina) |
| Storage class | Standard |
| Object URI | `gs://kangaroo_baseball_field/telco_churn.csv` |
| Reported object size / type | Approximately 971.9 KB / `text/csv` |

The region and storage class describe the existing bucket; the transfer code
only needs its project ID, bucket name, and object name. The reported size is
consistent with the local cleaned CSV, but only a checksum comparison can
confirm that the bytes match.

Jim's project and uploaded object are now configured in `config.yaml`:

```yaml
storage:
  project: project-902e069e-c3ed-49c2-a13
  bucket: kangaroo_baseball_field
  object: telco_churn.csv
  download_path: data/cloud/telco_churn.csv
  expected_sha256: 3281639149f21b9ae68c21245c383b35afdd2705ad005f1bc5c20da416430c35
```

For another bucket, replace those identifiers. If the URI is
`gs://my-bucket/telco_churn.csv`, use bucket `my-bucket` and object
`telco_churn.csv`. Do not put the entire URI in either field.

The expected SHA-256 comes from `processed_sha256` in the reviewed
`reports/data_summary.json`. It identifies the cleaned CSV, not the raw
source. Keep it unchanged for this dataset version. A future intentional
dataset change should use a new object name and a reviewed fingerprint.

## 3. Authorize Python on your Mac

Install the [Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install-sdk),
then run this yourself in a local terminal:

```bash
gcloud auth application-default login
```

Complete the browser login using the Google account that can access the
bucket. This sets up **Application Default Credentials (ADC)**, which the
Python client finds automatically. Being signed into the console, or running
only `gcloud auth login`, does not set up these Python application credentials.
No downloaded service account key is required for this local workflow.
Credentials are stored outside the repository. See Google's
[local authentication guide](https://docs.cloud.google.com/docs/authentication/set-up-adc-local-dev-environment).

Your account needs permission to read the object. If access is managed by
someone else, ask for **Storage Object Viewer** on this bucket for downloads.
The optional upload command also needs permission to create objects (for
example **Storage Object Creator**). Existing owner/admin access may already
cover both. See [Google's role definitions](https://docs.cloud.google.com/storage/docs/access-control/iam-roles).

## 4. Install dependencies and verify a real download

Run commands from a repository checkout containing the merged storage code. On Jim's Mac, the current training checkout is:

```bash
cd /Users/jim/dukeaipi/510_Sourcing_Data/Module_3_project/AIPI510_Module3_project
```

The project now targets Python 3.13. For a fresh clone or worktree with
Python 3.13 installed, first create its own environment:

```bash
python3.13 -m venv .venv
```

Activate it, install dependencies, and download:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.storage download
```

Success prints the cloud URI, verified SHA-256, and saved path. The file
appears at `data/cloud/telco_churn.csv`; it stays out of Git. There is no need
to rerun ingestion to download the cloud file: the expected hash is in Git.

The download always contacts GCS, even if a previous local copy exists.
It checks the bytes before saving, then replaces the previous cloud download
atomically. A failed request or checksum mismatch does not silently use a
local dataset or replace an existing local copy. Raw and processed ingestion
files remain separate. Matching bytes also preserves all customers and the
11 missing `TotalCharges` values without adding any new cleaning.

## Optional: upload programmatically

Since Jim is uploading through the console, this command is optional. It
supports reproducing the upload from another checkout after running ingestion:

```bash
python src/ingest.py
python -m src.storage upload
```

It verifies the local cleaned CSV against the same fingerprint and creates
the configured object only if it does not exist. A repeat upload refuses to
overwrite an existing cloud object; use `download` to verify the console
upload instead. No bucket is created and no permissions are changed by the code.

Both commands accept `--config /path/to/config.yaml`. Relative data paths
resolve from the repository root, not from the config file's folder.

## Troubleshooting

| Message | What to check |
| --- | --- |
| Set storage.project or storage.bucket | Fill missing settings in `config.yaml` with your actual identifiers |
| Google authentication failed | Run `gcloud auth application-default login` with the correct Google account |
| 403 / Forbidden | Check the account's bucket permissions and any API, organization, or quota-project restriction named in the error |
| 404 / Not Found | Check bucket and exact object name, including capitalization and folders |
| Checksum mismatch | Make sure you uploaded the cleaned CSV unchanged; don't replace the expected hash to bypass the check |
| Upload refused: object already exists | Use `download` to verify it; choose a new object name for an intentional dataset version |

## Validation and completion

```bash
python -m unittest discover -s tests -v
```

The automated checks are offline and use mocked cloud responses. They cover
byte preservation, wrong-file rejection, authentication/access failures,
atomic saving, and upload replacement protection. Passing them does not
prove that Google credentials, permissions, or the bucket are configured.

The original cloud-branch checks ran under Python 3.10 and emitted Google's
Python support warning. During the training branch, Jim approved Python 3.13
as the project target. Use the Python 3.13 environment described in the README;
do not reuse the old Python 3.10 virtual environment for new setup.

On November 23, 2026, Codex ran `python -m src.storage download` against Jim's
configured bucket using his local ADC login. The real download succeeded:

- 971,878 bytes, matching SHA-256
  `3281639149f21b9ae68c21245c383b35afdd2705ad005f1bc5c20da416430c35`.
- 7,043 customers, 21 columns, and 11 missing `TotalCharges` values retained.
- Target counts unchanged: 5,174 `No` and 1,869 `Yes`; customer IDs unique.
- Downloaded CSV stays in Git-ignored `data/cloud/`.

The SDK also warned that the user ADC has no quota project configured; the
download still succeeded. If Google later reports a quota-project issue,
follow [Google's troubleshooting guidance](https://cloud.google.com/docs/authentication/adc-troubleshooting/user-creds)
rather than changing bucket visibility.

Functional cloud verification is complete. The optional Python upload command
has offline coverage; Jim performed the actual upload in the console, so no
live Python upload was needed or attempted. Review the changes with Jim, then
commit and open the PR when he is ready.
