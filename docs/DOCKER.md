# Docker and Reproducing the Project

One image runs the whole project through three entry points: `serve` (the default), `train`, and `test`. It uses the official `python:3.13.18-slim` base, installs `requirements.txt`, and runs as an ordinary user rather than root. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and start it before running these commands.

## Workflow: train → build → run

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

   Then open http://127.0.0.1:8001/docs or call `/health` and `/predict` as in the [API guide](API.md). Stop it with Ctrl+C.

4. Run the test suite inside the container (offline; no credentials needed):

   ```bash
   docker run --rm churn-predictor test
   ```

## Training in the container

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
- The first line uses the Google login created by `gcloud auth application-default login` (see the [cloud storage walkthrough](CLOUD_STORAGE.md)); the `.netrc` line uses the W&B login created by `wandb login`.
- Add `--tracking-mode disabled` after `train` to skip W&B (then the `.netrc` line is not needed).
- Then rebuild the image (step 2) so it serves the new model.

## What goes into the image

`.dockerignore` uses an allow-list. Only `requirements.txt`, `config.yaml`, `src/`, `tests/`, `reports/`, the entry-point script, and the one model file are sent to Docker. Data CSVs, virtual environments, `.git`, W&B output, and credential files are never included. The committed reports are included so the one-time test evaluation still refuses to run again inside the container.

Docker Desktop on an Apple-silicon Mac builds ARM images by default. Cloud Run runs on x86 (amd64), so deployment (step 7) builds the image for that platform.

## Reproducing without author credentials

The repository and Docker image contain **addresses but no keys**. `config.yaml` names the Google Cloud project, bucket, file, and expected checksum, and the W&B project, but no login of Jim's is stored anywhere. What someone else can do:

| Goal | What they need |
| --- | --- |
| Use the deployed API or the front end | Nothing |
| Serve the model locally | Docker only: `docker build -t churn-predictor .` then `docker run --rm -p 8001:8080 churn-predictor` |
| Run the tests | Docker only: `docker run --rm churn-predictor test` |
| See Jim's tracked runs | A browser: [W&B project `jr613-d/aipi510-churn`](https://forge.coreweave.com/wandb/jr613-d/aipi510-churn) (public, view-only) |
| Download the cleaned data | A browser: [telco_churn.csv](https://storage.googleapis.com/kangaroo_baseball_field/telco_churn.csv) (public, read-only) |
| Retrain the model | Nothing: no Google login; their own W&B login is optional (below) |

### Getting the data

The cleaned CSV in Jim's bucket is **publicly readable** at
**https://storage.googleapis.com/kangaroo_baseball_field/telco_churn.csv**.
It is IBM's fictional sample, already public on Hugging Face under CC BY 4.0, so this exposes nothing private.

When no Google login is found, the download falls back to anonymous access and prints a note saying so. The **SHA-256 check still applies**, so training stops if the public file ever differs from the reviewed bytes. Uploads always require a login. Retraining with no credentials at all:

```bash
docker run --rm -v "$PWD/artifacts:/app/artifacts" -v "$PWD/reports:/app/reports" \
  churn-predictor train --tracking-mode disabled
# or, without Docker:  python -m src.train --tracking-mode disabled
```

This was verified in a container with no credentials. It downloaded the public file anonymously, the checksum matched, and the validation results were identical to Jim's.

**Full independence (own bucket).** If the public file is ever unavailable, recreate it with no access to Jim's resources:

1. Run `python src/ingest.py`. It downloads the pinned Hugging Face file and produces the identical cleaned CSV, verified by checksum.
2. Upload `data/processed/telco_churn.csv` unchanged to a bucket you own.
3. Change `storage.project` and `storage.bucket` (and `storage.object` if needed) in `config.yaml`. Leave `expected_sha256` unchanged.
4. Log in with `gcloud auth application-default login`, or make your file public, and train.

Because `expected_sha256` is unchanged, training verifies that your data is byte-for-byte the data Jim used. The same split seed then reproduces the same partitions and validation results. See the [cloud storage walkthrough](CLOUD_STORAGE.md) for details.

### Recording runs in W&B

No one can write to Jim's W&B workspace without an invitation. Retraining offers two choices:

- **Skip tracking:** add `--tracking-mode disabled`. Training, the model file, and the validation report work the same; nothing is recorded.
- **Use your own W&B account:** run `wandb login` with your own account and train normally. Because `tracking.entity` is blank in `config.yaml`, runs go to an `aipi510-churn` project in *your* default workspace, with no config changes. In Docker, connect your login with `-v "$HOME/.netrc:/home/app/.netrc:ro"` (see "Training in the container" above).

[← Back to the README](../README.md)
