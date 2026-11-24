# Deploying the API (Google Cloud Run)

The API runs on **Google Cloud Run** at **https://churn-api-161834179213.us-east1.run.app** in region `us-east1`, from the same Docker image tested locally. Everything was set up with the `gcloud` command line, with no web console steps. Jim ran each command with his own Google login.

## Live endpoints

```bash
curl https://churn-api-161834179213.us-east1.run.app/health
curl -X POST https://churn-api-161834179213.us-east1.run.app/predict -H "Content-Type: application/json" \
  -d '{"tenure": 12, "MonthlyCharges": 70.5, "Contract": "Month-to-month",
       "InternetService": "Fiber optic", "TechSupport": "No", "OnlineSecurity": "No",
       "PaymentMethod": "Electronic check", "PaperlessBilling": "Yes"}'
```

This returns `{"churn_probability": 0.6705…, "churn_prediction": "Yes", "threshold": 0.35}`, the same result as the local API. Interactive documentation is at [https://churn-api-161834179213.us-east1.run.app/docs](https://churn-api-161834179213.us-east1.run.app/docs). The first request after an idle period can take a few seconds while Cloud Run starts a container.

## Service settings

| Setting | Value | Why |
| --- | --- | --- |
| Image | `us-east1-docker.pkg.dev/project-902e069e-c3ed-49c2-a13/churn/churn-api`, deployed by digest | Exactly the image that was built and tested; the model's SHA-256 (`5c1ddc44…`) matches W&B run `udfqgkyz` |
| Access | Public (`--allow-unauthenticated`) | The assignment requires a public endpoint |
| Identity | `churn-api-runtime` service account with **no permissions** | The model is in the image, so the API needs no access to anything |
| CPU and memory | 1 CPU, 1 GiB | Enough for pandas and scikit-learn |
| Instances | min 0, max 1 | Scales to zero when idle (no cost), and one instance caps how fast costs can grow |
| Request timeout | 30 seconds | A prediction takes milliseconds |

The bucket and Artifact Registry are in the same region. A $5 cost guard (a budget that automatically makes the API and data private) is designed and set aside for later; the one-instance limit is the current safeguard.

## How to deploy it yourself

These commands assume Docker Desktop, the [gcloud CLI](https://cloud.google.com/sdk/docs/install), a Google Cloud project with billing enabled, and a trained model in `artifacts/` (see [DOCKER.md](DOCKER.md)). Replace `PROJECT` with your project ID.

```bash
# One-time setup
gcloud auth login
gcloud config set project PROJECT
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
gcloud artifacts repositories create churn --repository-format=docker --location=us-east1
gcloud auth configure-docker us-east1-docker.pkg.dev
gcloud iam service-accounts create churn-api-runtime --display-name="Churn API runtime (no permissions)"

# Build for Cloud Run's x86 machines (Apple-silicon Macs build ARM by default) and push
TAG=$(git rev-parse --short HEAD)
IMAGE=us-east1-docker.pkg.dev/PROJECT/churn/churn-api:$TAG
docker buildx build --platform linux/amd64 -t $IMAGE --load .
docker push $IMAGE          # prints the image digest (sha256:...)

# Deploy (use the digest printed by docker push)
gcloud run deploy churn-api \
  --image=us-east1-docker.pkg.dev/PROJECT/churn/churn-api@sha256:DIGEST \
  --region=us-east1 \
  --service-account=churn-api-runtime@PROJECT.iam.gserviceaccount.com \
  --allow-unauthenticated --port=8080 --cpu=1 --memory=1Gi \
  --min-instances=0 --max-instances=1 --timeout=30
```

`gcloud run deploy` prints the service URL. To release a new model, retrain, rebuild, push, and deploy again. Cloud Run creates a new revision and moves traffic to it, and the previous revision stays available for rollback.

Two separate Google logins are involved. `gcloud auth login` authorizes the `gcloud` command itself (deploying, creating resources). `gcloud auth application-default login` authorizes Python programs such as training. Deploying needs only the first.

## Where the API fits

![System architecture: users and the Streamlit app call the Cloud Run API, whose Docker image contains the model; separately, data flows from Hugging Face to Cloud Storage, training logs to Weights & Biases, and the image is pushed to Artifact Registry and deployed to Cloud Run.](architecture.svg)

The system has two paths:

- **Every prediction (blue).** A user fills in a customer's details in the Streamlit app. The app sends them to the API's `POST /predict` endpoint on Google Cloud Run, which returns a churn probability and a Yes/No prediction at the 0.35 threshold. The trained model is built into the API's Docker image, so a prediction never touches the data bucket, Weights & Biases, or anyone's login.
- **Retraining and redeploying (black).** `src/ingest.py` recreates the cleaned dataset from its pinned Hugging Face source. The cleaned file lives in a public [Cloud Storage bucket](https://storage.googleapis.com/kangaroo_baseball_field/telco_churn.csv). Training downloads it, refuses to run unless its SHA-256 matches `config.yaml`, and records each run in [Weights & Biases](https://forge.coreweave.com/wandb/jr613-d/aipi510-churn). `docker build` puts the new model in the image, `docker push` sends it to Artifact Registry, and `gcloud run deploy` puts it live.

