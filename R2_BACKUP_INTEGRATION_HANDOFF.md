# 🚀 Cloudflare R2 Database Backup — Template Integration Handoff

> **Purpose:** This document is a complete, one-shot implementation blueprint. You can hand this file directly to an AI agent (or follow it yourself) in your template project to replicate the exact Cloudflare R2 automated PostgreSQL backup & restore feature without any iterative debugging.

---

## 📋 Overview of Changes

To add this feature to any FastAPI + PostgreSQL template project, you will:
1. Add `boto3` to project dependencies.
2. Update `app/core/config.py` to add R2 & Backup configuration fields.
3. Update `.env.example` to document the environment variables.
4. Add the standalone CLI script `scripts/r2_backup.py`.
5. Add unit tests in `tests/test_r2_backup.py`.
6. Verify with `pytest` and `ruff`.

---

## Step 1: Install Dependency (`boto3`)

Run the following command in the template project root:

```bash
# If using uv:
uv add "boto3>=1.34.0"

# Or if using poetry / pip:
pip install "boto3>=1.34.0"
```

Or add `"boto3>=1.34.0"` to the `dependencies` array in `pyproject.toml`.

---

## Step 2: Update `app/core/config.py`

In `app/core/config.py`, add the following fields inside the `Settings` class:

```python
    # Cloudflare R2 & Automated Database Backup
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_DOCKER_CONTAINER: str = "digital-product-db"  # Change to your DB container name if different
```

---

## Step 3: Update `.env.example`

Append the following lines to your `.env.example`:

```ini
# Cloudflare R2 Automated Database Backup
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET_NAME=your_r2_bucket_name
BACKUP_RETENTION_DAYS=30
BACKUP_DOCKER_CONTAINER=digital-product-db
```

---

## Step 4: Create `scripts/r2_backup.py`

Create a new file at `scripts/r2_backup.py` with the following content:

```python
"""Cloudflare R2 Automated Database Backup and Restore Utility.

This script allows you to:
1. Dump the PostgreSQL database (via running Docker container or local pg_dump).
2. Compress the SQL dump using gzip (.sql.gz).
3. Upload the compressed backup to Cloudflare R2 (S3-compatible object storage).
4. Enforce a retention policy by automatically deleting backups older than N days.
5. List all available backups stored in Cloudflare R2.
6. Restore a backup directly into PostgreSQL.

Usage:
    # Run a full backup and rotate old backups:
    python scripts/r2_backup.py backup

    # List all backups in R2:
    python scripts/r2_backup.py list

    # Restore a specific backup from R2:
    python scripts/r2_backup.py restore backups/2026/09/digital_product_selling_system_backup_20260921_120000.sql.gz --yes
"""

import argparse
import gzip
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    Config = None
    ClientError = Exception

# Add project root to sys.path so we can import app settings
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.config import settings  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("r2_backup")


def get_r2_client() -> Any:
    """Initialize and return a boto3 S3 client configured for Cloudflare R2."""
    if boto3 is None:
        raise RuntimeError(
            "boto3 is not installed. Please install it using `pip install boto3` or `uv add boto3`."
        )

    account_id = settings.R2_ACCOUNT_ID or os.getenv("R2_ACCOUNT_ID")
    access_key = settings.R2_ACCESS_KEY_ID or os.getenv("R2_ACCESS_KEY_ID")
    secret_key = settings.R2_SECRET_ACCESS_KEY or os.getenv("R2_SECRET_ACCESS_KEY")

    if not account_id or not access_key or not secret_key:
        raise ValueError(
            "Cloudflare R2 credentials are missing. "
            "Please ensure R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY "
            "are configured in your .env file or environment variables."
        )

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def is_docker_container_running(container_name: str) -> bool:
    """Check if the specified Docker container is currently running."""
    if not shutil.which("docker"):
        return False

    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        running_names = [name.strip() for name in result.stdout.splitlines() if name.strip()]
        return container_name in running_names
    except Exception:
        return False


def dump_postgres_database(output_gz_path: Path, container_name: Optional[str] = None) -> None:
    """Dump the PostgreSQL database and write directly into a gzip compressed file."""
    db_user = settings.DB_USER
    db_password = settings.DB_PASSWORD
    db_name = settings.DB_NAME
    db_host = settings.DB_HOST
    db_port = str(settings.DB_PORT)

    target_container = container_name or settings.BACKUP_DOCKER_CONTAINER

    # 1. Check if Docker container is available and running
    if target_container and is_docker_container_running(target_container):
        logger.info(f"Using running Docker container '{target_container}' for pg_dump.")
        cmd = [
            "docker",
            "exec",
            "-i",
            target_container,
            "pg_dump",
            "-U",
            db_user,
            "-d",
            db_name,
            "--no-owner",
            "--clean",
            "--if-exists",
        ]
        env = os.environ.copy()
    else:
        # 2. Fallback to host pg_dump
        if not shutil.which("pg_dump"):
            raise RuntimeError(
                f"Neither running docker container '{target_container}' nor local 'pg_dump' executable was found. "
                "Ensure PostgreSQL Docker container is running or pg_dump is installed on the host."
            )
        logger.info(f"Using host pg_dump to connect to {db_host}:{db_port}.")
        cmd = [
            "pg_dump",
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "-d",
            db_name,
            "--no-owner",
            "--clean",
            "--if-exists",
        ]
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password

    logger.info(f"Executing database dump into compressed file: {output_gz_path}")

    # Stream stdout from pg_dump directly into gzip file to save memory and disk
    with gzip.open(output_gz_path, "wb", compresslevel=9) as gz_out:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        if process.stdout:
            shutil.copyfileobj(process.stdout, gz_out)
        _, stderr_data = process.communicate()

        if process.returncode != 0:
            error_msg = stderr_data.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"pg_dump failed with exit code {process.returncode}: {error_msg}")

    dump_size_mb = output_gz_path.stat().st_size / (1024 * 1024)
    logger.info(f"Database dump successful! Compressed file size: {dump_size_mb:.2f} MB")


def upload_backup_to_r2(local_file_path: Path, bucket_name: Optional[str] = None) -> str:
    """Upload the compressed backup file to Cloudflare R2 bucket."""
    bucket = bucket_name or settings.R2_BUCKET_NAME or os.getenv("R2_BUCKET_NAME")
    if not bucket:
        raise ValueError(
            "R2_BUCKET_NAME is not configured. Please set it in your .env file or pass --bucket."
        )

    client = get_r2_client()

    now = datetime.now(timezone.utc)
    safe_project = settings.PROJECT_NAME.lower().replace(" ", "_")
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    object_key = f"backups/{now.strftime('%Y/%m')}/{safe_project}_backup_{timestamp_str}.sql.gz"

    file_size_bytes = local_file_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    logger.info(f"Uploading {local_file_path.name} ({file_size_mb:.2f} MB) to R2 bucket '{bucket}'...")
    logger.info(f"Destination Key: {object_key}")

    with open(local_file_path, "rb") as file_data:
        client.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=file_data,
            ContentType="application/gzip",
            Metadata={
                "project": safe_project,
                "version": settings.VERSION,
                "created_at": now.isoformat(),
            },
        )

    logger.info("Upload to Cloudflare R2 completed successfully!")
    return object_key


def cleanup_expired_backups(retention_days: Optional[int] = None, bucket_name: Optional[str] = None) -> int:
    """Delete backups from Cloudflare R2 that are older than the specified retention days."""
    days = retention_days if retention_days is not None else settings.BACKUP_RETENTION_DAYS
    bucket = bucket_name or settings.R2_BUCKET_NAME or os.getenv("R2_BUCKET_NAME")

    if not bucket:
        logger.warning("R2_BUCKET_NAME not configured; skipping retention cleanup.")
        return 0

    if days <= 0:
        logger.info("Retention days <= 0; retention cleanup disabled.")
        return 0

    client = get_r2_client()
    now = datetime.now(timezone.utc)
    deleted_count = 0

    logger.info(f"Scanning R2 bucket '{bucket}' for backups older than {days} days...")

    paginator = client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix="backups/")

    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            last_modified = obj["LastModified"]
            age_days = (now - last_modified).total_seconds() / (24 * 3600)

            if age_days > days:
                logger.info(f"Deleting expired backup: {key} (Age: {age_days:.1f} days)")
                client.delete_object(Bucket=bucket, Key=key)
                deleted_count += 1

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired backup(s) from R2.")
    else:
        logger.info("No expired backups found to delete.")

    return deleted_count


def list_backups(bucket_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all backups currently stored in the Cloudflare R2 bucket."""
    bucket = bucket_name or settings.R2_BUCKET_NAME or os.getenv("R2_BUCKET_NAME")
    if not bucket:
        raise ValueError("R2_BUCKET_NAME is not configured.")

    client = get_r2_client()
    now = datetime.now(timezone.utc)
    backups = []

    paginator = client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix="backups/")

    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            size_mb = obj["Size"] / (1024 * 1024)
            last_modified = obj["LastModified"]
            age_days = (now - last_modified).total_seconds() / (24 * 3600)

            backups.append(
                {
                    "key": key,
                    "size_mb": size_mb,
                    "last_modified": last_modified.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "age_days": round(age_days, 1),
                }
            )

    backups.sort(key=lambda x: x["last_modified"], reverse=True)

    print("\n" + "=" * 80)
    print(f"Cloudflare R2 Backups in Bucket: '{bucket}'")
    print("=" * 80)
    if not backups:
        print("No backups found.")
    else:
        print(f"{'No.':<4} {'Date (UTC)':<22} {'Size':<10} {'Age (Days)':<12} {'Key'}")
        print("-" * 80)
        for idx, item in enumerate(backups, 1):
            print(
                f"{idx:<4} {item['last_modified']:<22} {item['size_mb']:>6.2f} MB   {item['age_days']:<12} {item['key']}"
            )
    print("=" * 80 + "\n")

    return backups


def restore_backup(
    object_key: str,
    bucket_name: Optional[str] = None,
    container_name: Optional[str] = None,
    assume_yes: bool = False,
) -> None:
    """Download a backup from Cloudflare R2 and restore it into PostgreSQL."""
    bucket = bucket_name or settings.R2_BUCKET_NAME or os.getenv("R2_BUCKET_NAME")
    if not bucket:
        raise ValueError("R2_BUCKET_NAME is not configured.")

    if not assume_yes:
        print("\n" + "!" * 80)
        print("WARNING: Restoring a database backup will OVERWRITE existing data!")
        print(f"Target Database: {settings.DB_NAME}")
        print(f"Backup File: {object_key}")
        print("!" * 80)
        confirm = input("Are you absolutely sure you want to proceed? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("Database restore operation cancelled by user.")
            return

    client = get_r2_client()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        download_gz_path = temp_path / "restore_download.sql.gz"

        logger.info(f"Downloading '{object_key}' from R2 bucket '{bucket}'...")
        client.download_file(bucket, object_key, str(download_gz_path))
        logger.info("Download completed. Decompressing SQL dump...")

        decompressed_sql_path = temp_path / "restore.sql"
        with gzip.open(download_gz_path, "rb") as gz_in, open(decompressed_sql_path, "wb") as sql_out:
            shutil.copyfileobj(gz_in, sql_out)

        db_user = settings.DB_USER
        db_password = settings.DB_PASSWORD
        db_name = settings.DB_NAME
        db_host = settings.DB_HOST
        db_port = str(settings.DB_PORT)

        target_container = container_name or settings.BACKUP_DOCKER_CONTAINER

        if target_container and is_docker_container_running(target_container):
            logger.info(f"Restoring into running Docker container '{target_container}'...")
            cmd = ["docker", "exec", "-i", target_container, "psql", "-U", db_user, "-d", db_name]
            env = os.environ.copy()
        else:
            if not shutil.which("psql"):
                raise RuntimeError(
                    f"Neither running docker container '{target_container}' nor local 'psql' executable was found."
                )
            logger.info(f"Restoring via host psql into {db_host}:{db_port}/{db_name}...")
            cmd = ["psql", "-h", db_host, "-p", db_port, "-U", db_user, "-d", db_name]
            env = os.environ.copy()
            env["PGPASSWORD"] = db_password

        with open(decompressed_sql_path, "rb") as sql_file:
            process = subprocess.run(
                cmd,
                stdin=sql_file,
                capture_output=True,
                env=env,
            )

        if process.returncode != 0:
            err = process.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"psql restore failed with code {process.returncode}: {err}")

        logger.info("Database restored successfully from Cloudflare R2 backup!")


def perform_full_backup(
    container_name: Optional[str] = None,
    bucket_name: Optional[str] = None,
    retention_days: Optional[int] = None,
) -> str:
    """High-level function: dumps DB, compresses, uploads to R2, and cleans up expired backups."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        local_gz_path = temp_path / f"db_dump_{now_str}.sql.gz"

        dump_postgres_database(local_gz_path, container_name=container_name)
        uploaded_key = upload_backup_to_r2(local_gz_path, bucket_name=bucket_name)
        cleanup_expired_backups(retention_days=retention_days, bucket_name=bucket_name)

        return uploaded_key


def main():
    parser = argparse.ArgumentParser(
        description="Cloudflare R2 Database Backup, List, and Restore CLI Utility"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # backup
    backup_parser = subparsers.add_parser("backup", help="Perform full database backup to Cloudflare R2")
    backup_parser.add_argument("--container", help="Name of the running PostgreSQL Docker container")
    backup_parser.add_argument("--bucket", help="R2 Bucket Name override")
    backup_parser.add_argument(
        "--retention-days",
        type=int,
        help="Number of days to keep backups (default: from settings.BACKUP_RETENTION_DAYS)",
    )

    # list
    list_parser = subparsers.add_parser("list", help="List all backups available in Cloudflare R2")
    list_parser.add_argument("--bucket", help="R2 Bucket Name override")

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore a backup from Cloudflare R2 into PostgreSQL")
    restore_parser.add_argument("key", help="The R2 object key of the backup file")
    restore_parser.add_argument("--container", help="Name of the running PostgreSQL Docker container")
    restore_parser.add_argument("--bucket", help="R2 Bucket Name override")
    restore_parser.add_argument("-y", "--yes", action="store_true", help="Confirm overwrite without interactive prompt")

    args = parser.parse_args()

    try:
        if args.command == "backup":
            key = perform_full_backup(
                container_name=args.container,
                bucket_name=args.bucket,
                retention_days=args.retention_days,
            )
            print(f"\n[SUCCESS] Backup completed and saved as: {key}")
        elif args.command == "list":
            list_backups(bucket_name=args.bucket)
        elif args.command == "restore":
            restore_backup(
                object_key=args.key,
                bucket_name=args.bucket,
                container_name=args.container,
                assume_yes=args.yes,
            )
            print("\n[SUCCESS] Restore operation completed successfully.")
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Step 5: Add Unit Tests (`tests/test_r2_backup.py`)

Create `tests/test_r2_backup.py` with mock tests:

```python
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
```

---

## Step 6: Verification

Run the test suite to confirm everything works:

```bash
uv run pytest tests/test_r2_backup.py
uv run python scripts/r2_backup.py --help
```

---

## Step 7: (Optional) Add Shortcuts to `Makefile`

If your template project uses a `Makefile`, add these targets for convenient developer shortcuts:

```makefile
backup: ## Run database backup to Cloudflare R2
	uv run python scripts/r2_backup.py backup

backup-list: ## List available database backups in Cloudflare R2
	uv run python scripts/r2_backup.py list

backup-restore: ## Restore database backup from Cloudflare R2 (Usage: make backup-restore key="path/to/file.sql.gz")
	@if [ -z "$(key)" ]; then echo "Error: 'key' parameter is required. Usage: make backup-restore key=\"backups/YYYY/MM/...sql.gz\""; exit 1; fi
	uv run python scripts/r2_backup.py restore $(key)
```

And don't forget to append `backup backup-list backup-restore` to `.PHONY`.

