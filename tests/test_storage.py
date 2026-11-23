"""Offline transfer checks. These do not prove access to a real GCS bucket."""

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from google.api_core.exceptions import Forbidden, PreconditionFailed
from google.auth.exceptions import DefaultCredentialsError
from google.cloud.storage.blob import Blob
import yaml

from src.storage import download, load_settings, upload


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name).resolve()
        self.root_patch = patch("src.storage.ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.content = b"customerID,TotalCharges,Churn\nsample-1,,No\nsample-2,89.55,Yes\n"
        self.source = self.root / "data/processed/telco_churn.csv"
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(self.content)
        self.destination = self.root / "data/cloud/telco_churn.csv"
        self.config = {
            "paths": {"raw": "data/raw/telco_churn.csv",
                      "processed": "data/processed/telco_churn.csv",
                      "summary_json": "reports/data_summary.json",
                      "summary_markdown": "reports/data_summary.md"},
            "storage": {"project": "test-project", "bucket": "test-bucket",
                        "object": "processed/telco_churn.csv",
                        "download_path": "data/cloud/telco_churn.csv",
                        "expected_sha256": hashlib.sha256(self.content).hexdigest()},
        }
        self.config_path = self.root / "config.yaml"
        self.save_config()
        self.blob = Mock(spec=Blob)
        self.blob.download_as_bytes.return_value = self.content
        self.client = Mock()
        self.client.bucket.return_value.blob.return_value = self.blob

    def save_config(self):
        self.config_path.write_text(yaml.safe_dump(self.config))

    def existing_download(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.write_bytes(b"keep previous file")

    def test_download_preserves_exact_bytes_and_ingestion_source(self):
        result = download(self.config_path, self.client)
        self.assertEqual(result, self.destination)
        self.assertEqual(result.read_bytes(), self.content)
        self.assertEqual(self.source.read_bytes(), self.content)
        self.client.bucket.assert_called_once_with("test-bucket")
        self.client.bucket.return_value.blob.assert_called_once_with("processed/telco_churn.csv")

    def test_bad_download_does_not_replace_existing_file(self):
        self.existing_download()
        self.blob.download_as_bytes.return_value = b"wrong file or changed data"
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            download(self.config_path, self.client)
        self.assertEqual(self.destination.read_bytes(), b"keep previous file")

    def test_bad_first_download_creates_no_csv(self):
        self.blob.download_as_bytes.return_value = b"wrong file"
        with self.assertRaises(ValueError):
            download(self.config_path, self.client)
        self.assertFalse(self.destination.exists())

    def test_failed_cloud_access_never_silently_uses_local_data(self):
        self.existing_download()
        self.blob.download_as_bytes.side_effect = Forbidden("Access denied")
        with self.assertRaises(Forbidden):
            download(self.config_path, self.client)
        self.assertEqual(self.destination.read_bytes(), b"keep previous file")

    def test_repeated_download_still_contacts_cloud(self):
        download(self.config_path, self.client)
        download(self.config_path, self.client)
        self.assertEqual(self.blob.download_as_bytes.call_count, 2)
        self.assertEqual(self.destination.read_bytes(), self.content)

    def test_failed_save_cleans_temporary_file_and_preserves_previous(self):
        self.existing_download()
        with patch("src.storage.os.replace", side_effect=OSError("Cannot replace")):
            with self.assertRaises(OSError):
                download(self.config_path, self.client)
        self.assertEqual(self.destination.read_bytes(), b"keep previous file")
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_upload_uses_verified_bytes_and_refuses_replacement(self):
        upload(self.config_path, self.client)
        self.assertEqual(self.blob.upload_from_string.call_args.args[0], self.content)
        self.assertEqual(self.blob.upload_from_string.call_args.kwargs["if_generation_match"], 0)
        self.blob.upload_from_string.side_effect = PreconditionFailed("Object exists")
        with self.assertRaises(PreconditionFailed):
            upload(self.config_path, self.client)

    def test_altered_source_is_rejected_before_auth_or_upload(self):
        self.source.write_bytes(b"unexpected CSV")
        with patch("src.storage.storage.Client") as create_client:
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                upload(self.config_path)
            create_client.assert_not_called()

    def test_missing_bucket_is_actionable_before_auth(self):
        self.config["storage"]["bucket"] = None
        self.save_config()
        with patch("src.storage.storage.Client") as create_client:
            with self.assertRaisesRegex(ValueError, "Set storage.bucket"):
                download(self.config_path)
            create_client.assert_not_called()

    def test_download_cannot_target_raw_processed_or_outside_cloud_folder(self):
        for path in ["data/raw/telco_churn.csv", "data/processed/telco_churn.csv",
                     "data/cloud/../../README.md", "README.md", "data/cloud"]:
            with self.subTest(path=path):
                self.config["storage"]["download_path"] = path
                self.save_config()
                with self.assertRaisesRegex(ValueError, "inside data/cloud"):
                    load_settings(self.config_path)

    def test_authentication_failure_propagates_without_saving(self):
        with patch("src.storage.storage.Client", side_effect=DefaultCredentialsError("No ADC")):
            with self.assertRaises(DefaultCredentialsError):
                download(self.config_path)
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
