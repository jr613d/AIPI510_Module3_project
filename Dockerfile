# One image for the whole pipeline: serve (default), train, and test.
#   docker build -t churn-predictor .
#   docker run --rm -p 8001:8080 churn-predictor            # serve the API
# See the README's "Docker" section for training with credentials.
#
# The trained model is copied in at build time, so train before building.
# No credentials are ever copied into the image; training receives them at run time.

FROM python:3.13.18-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first so code changes do not force a slow reinstall.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Code, configuration, committed reports (they keep the one-time test guard),
# and the trained model. .dockerignore keeps data, environments, and secrets out.
COPY config.yaml docker-entrypoint.sh ./
COPY src/ src/
COPY tests/ tests/
COPY reports/ reports/
COPY artifacts/churn_pipeline.joblib artifacts/churn_pipeline.joblib

# Fail the build, with the API's own message, if the model is unusable.
# Record the model's fingerprint so a running image can be matched to its training run.
RUN python -c "from src.api import load_model; load_model()" \
    && sha256sum artifacts/churn_pipeline.joblib | cut -d' ' -f1 > MODEL_SHA256 \
    && echo "Model SHA-256: $(cat MODEL_SHA256)"

# Run as an ordinary user, not root. Training writes downloads, models, reports, and W&B files.
RUN useradd --create-home --uid 10001 app \
    && mkdir -p data/cloud wandb \
    && chown -R app:app /app \
    && chmod +x docker-entrypoint.sh
USER app

# Cloud Run supplies PORT; 8080 is the default otherwise.
ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["serve"]
