"""Transfer the reviewed cleaned CSV to/from a Google Cloud bucket.

Run from the repository: python -m src.storage download
Authentication uses Application Default Credentials, never a key in config.yaml.
Downloads fall back to anonymous access when no Google login exists, which
works only if the file is publicly readable. Uploads always require a login.
"""

import argparse
import hashlib
import os
from pathlib import Path
import re
import tempfile

from google.api_core.exceptions import Forbidden, GoogleAPIError, PreconditionFailed, Unauthorized
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
from google.cloud import storage
from google.cloud.storage.exceptions import DataCorruption
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_settings(config_path):
    with Path(config_path).open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict) or not isinstance(config.get("paths"), dict):
        raise ValueError("Configuration must contain paths and storage mappings.")
    settings = config.get("storage") or {}
    if not isinstance(settings, dict):
        raise ValueError("storage must be a mapping in config.yaml.")
    settings = dict(settings)
    for field in ("project", "bucket", "object", "download_path", "expected_sha256"):
        value = settings.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Set storage.{field} in config.yaml before transferring data.")
    if "/" in settings["bucket"] or settings["object"].startswith(("gs://", "/")):
        raise ValueError("Use a bucket name and a relative object name, not a full URL.")
    if not re.fullmatch(r"[0-9a-f]{64}", settings["expected_sha256"]):
        raise ValueError("storage.expected_sha256 must be a lowercase SHA-256 fingerprint.")

    settings["upload_path"] = ROOT / config["paths"]["processed"]
    destination = (ROOT / settings["download_path"]).resolve()
    # Restrict downloaded data to its own ignored folder, even with a custom config.
    cloud_folder = (ROOT / "data/cloud").resolve()
    if cloud_folder not in destination.parents:
        raise ValueError("storage.download_path must be a file inside data/cloud/.")
    protected = {(ROOT / value).resolve() for value in config["paths"].values()}
    if destination in protected:
        raise ValueError("Cloud downloads must not overwrite ingestion outputs.")
    settings["download_path"] = destination
    return settings


def verify_content(content, expected):
    actual = hashlib.sha256(content).hexdigest()
    if actual != expected:
        raise ValueError(
            f"Cleaned CSV checksum mismatch: expected {expected}, got {actual}. "
            "Check that you uploaded data/processed/telco_churn.csv unchanged. "
            "Do not change the expected fingerprint just to accept a different file."
        )


def get_blob(settings, client=None, allow_anonymous=False):
    """Return the object handle and whether it is accessed anonymously."""
    anonymous = False
    if client is None:
        try:
            client = storage.Client(project=settings["project"])
        except DefaultCredentialsError:
            if not allow_anonymous:
                raise
            # No Google login on this machine: try the file as a public object.
            client = storage.Client.create_anonymous_client()
            anonymous = True
            print("No Google login found; trying anonymous download (works only for a public file).")
    return client.bucket(settings["bucket"]).blob(settings["object"]), anonymous


def upload(config_path=ROOT / "config.yaml", client=None):
    """Upload verified bytes only if the named object does not already exist."""
    settings = load_settings(config_path)
    content = settings["upload_path"].read_bytes()
    verify_content(content, settings["expected_sha256"])
    blob, _ = get_blob(settings, client)
    # Create-only: a repeat upload must not silently replace an existing dataset.
    blob.upload_from_string(
        content, content_type="text/csv", if_generation_match=0, timeout=60,
    )
    print(f"Uploaded verified CSV to gs://{settings['bucket']}/{settings['object']}")


def download(config_path=ROOT / "config.yaml", client=None):
    """Always fetch cloud bytes; save atomically only after SHA-256 matches."""
    settings = load_settings(config_path)
    blob, anonymous = get_blob(settings, client, allow_anonymous=True)
    # The sample is <1 MB. Holding it in memory lets us verify before writing.
    try:
        content = blob.download_as_bytes(raw_download=True, checksum="auto", timeout=60)
    except (Forbidden, Unauthorized, GoogleAuthError) as error:
        # A private file answers anonymous callers with 401, which surfaces as a refresh error.
        if not anonymous:
            raise
        raise PermissionError(
            f"gs://{settings['bucket']}/{settings['object']} is not publicly readable and no Google "
            "login was found. Run 'gcloud auth application-default login' with an account that can "
            "read the bucket, or use your own bucket (README: Reproducing without author credentials)."
        ) from error
    verify_content(content, settings["expected_sha256"])
    destination = settings["download_path"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Downloaded gs://{settings['bucket']}/{settings['object']}")
    print(f"Verified SHA-256: {settings['expected_sha256']}")
    print(f"Saved cleaned CSV: {destination}")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("upload", "download"))
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    args = parser.parse_args()
    try:
        {"upload": upload, "download": download}[args.action](args.config)
    except PreconditionFailed:
        parser.exit(1, "Upload refused: the object already exists. Use download to verify it, "
                    "or choose a new object name for a new dataset version.\n")
    except GoogleAuthError:
        parser.exit(1, "Google authentication failed. Run 'gcloud auth application-default "
                    "login' locally and sign in with an account allowed to access the bucket.\n")
    except (GoogleAPIError, DataCorruption, OSError, ValueError, KeyError, yaml.YAMLError) as error:
        parser.exit(1, f"Storage transfer failed: {error}\n")


if __name__ == "__main__":
    main()
