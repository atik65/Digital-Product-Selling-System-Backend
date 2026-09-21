from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from scripts.r2_backup import (
    get_r2_client,
    cleanup_expired_backups,
    list_backups,
    upload_backup_to_r2,
)


def test_get_r2_client_missing_credentials(monkeypatch):
    monkeypatch.setattr("scripts.r2_backup.settings.R2_ACCOUNT_ID", "")
    monkeypatch.setattr("scripts.r2_backup.settings.R2_ACCESS_KEY_ID", "")
    monkeypatch.setattr("scripts.r2_backup.settings.R2_SECRET_ACCESS_KEY", "")

    with pytest.raises(ValueError, match="Cloudflare R2 credentials are missing"):
        get_r2_client()


def test_get_r2_client_success(monkeypatch):
    monkeypatch.setattr("scripts.r2_backup.settings.R2_ACCOUNT_ID", "mock_account_id")
    monkeypatch.setattr("scripts.r2_backup.settings.R2_ACCESS_KEY_ID", "mock_key")
    monkeypatch.setattr("scripts.r2_backup.settings.R2_SECRET_ACCESS_KEY", "mock_secret")

    with patch("scripts.r2_backup.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        client = get_r2_client()
        assert client == mock_client
        mock_boto.assert_called_once()
        _, kwargs = mock_boto.call_args
        assert "mock_account_id.r2.cloudflarestorage.com" in kwargs["endpoint_url"]


def test_upload_backup_to_r2(tmp_path, monkeypatch):
    test_file = tmp_path / "test_backup.sql.gz"
    test_file.write_bytes(b"dummy compressed sql data")

    mock_client = MagicMock()
    with patch("scripts.r2_backup.get_r2_client", return_value=mock_client):
        uploaded_key = upload_backup_to_r2(test_file, bucket_name="my-test-bucket")
        assert "backups/" in uploaded_key
        assert uploaded_key.endswith(".sql.gz")
        mock_client.put_object.assert_called_once()
        _, kwargs = mock_client.put_object.call_args
        assert kwargs["Bucket"] == "my-test-bucket"
        assert kwargs["Key"] == uploaded_key
        assert kwargs["ContentType"] == "application/gzip"


def test_cleanup_expired_backups():
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator

    now = datetime.now(timezone.utc)
    old_date = now - timedelta(days=40)
    fresh_date = now - timedelta(days=5)

    mock_paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": "backups/2026/08/old.sql.gz", "LastModified": old_date, "Size": 1024},
                {"Key": "backups/2026/09/fresh.sql.gz", "LastModified": fresh_date, "Size": 2048},
            ]
        }
    ]

    with patch("scripts.r2_backup.get_r2_client", return_value=mock_client):
        deleted = cleanup_expired_backups(retention_days=30, bucket_name="my-test-bucket")
        assert deleted == 1
        mock_client.delete_object.assert_called_once_with(
            Bucket="my-test-bucket",
            Key="backups/2026/08/old.sql.gz",
        )


def test_list_backups():
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator

    now = datetime.now(timezone.utc)
    mock_paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": "backups/2026/09/b1.sql.gz", "LastModified": now, "Size": 1024 * 1024 * 2},
            ]
        }
    ]

    with patch("scripts.r2_backup.get_r2_client", return_value=mock_client):
        backups = list_backups(bucket_name="my-test-bucket")
        assert len(backups) == 1
        assert backups[0]["key"] == "backups/2026/09/b1.sql.gz"
        assert backups[0]["size_mb"] == 2.0
