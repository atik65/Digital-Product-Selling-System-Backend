# 🛡️ Production Database Backup & Uptime Monitoring Guide

This guide provides complete instructions for setting up **Automated Database Backups to Cloudflare R2** and **Real-Time Uptime Monitoring with UptimeRobot**.

---

## 📑 Table of Contents
1. [Cloudflare R2 Setup (Free 10 GB Object Storage)](#1-cloudflare-r2-setup-free-10-gb-object-storage)
2. [Environment Configuration](#2-environment-configuration)
3. [Backup Script Usage (CLI)](#3-backup-script-usage-cli)
4. [Automating Backups with Linux Cron](#4-automating-backups-with-linux-cron)
5. [Disaster Recovery & Restoring Backups](#5-disaster-recovery--restoring-backups)
6. [Uptime Monitoring with UptimeRobot](#6-uptime-monitoring-with-uptimerobot)

---

## 1. Cloudflare R2 Setup (Free 10 GB Object Storage)

Cloudflare R2 provides S3-compatible cloud storage with **10 GB completely free every month** and **zero egress (download) fees**.

### Step 1.1: Create a Cloudflare Account & Enable R2
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/) and log in (or sign up).
2. In the left navigation menu, click **R2** (or **Storage & Databases** > **R2**).
3. If prompted, enable R2 (you may need to add a payment card, but 10 GB / month is 100% free and won't charge).

### Step 1.2: Create an R2 Bucket
1. Click **Create bucket**.
2. Name your bucket (e.g. `digital-product-db-backups` or `project-prod-backups`).
3. Location: Choose **Automatic** (or closest region).
4. Storage Class: **Standard**.
5. Click **Create Bucket**.

### Step 1.3: Generate API Tokens (Credentials)
1. On the R2 Overview page, look at the right side under **Account Details** to find your **Account ID** (a 32-character hexadecimal string). Copy this.
2. In the right-hand panel, click **Manage R2 API Tokens** > **Create API Token**.
3. Configure the token:
   - **Token Name**: `db-backup-token`
   - **Permissions**: **Object Read & Write** (or Admin Read & Write).
   - **Apply to**: Specific bucket (`digital-product-db-backups`) or All buckets.
   - **TTL**: Forever (leave blank or select maximal duration).
4. Click **Create API Token**.
5. **CRITICAL**: Copy the generated credentials immediately (they are shown only once!):
   - **Access Key ID** (e.g., `8a7b9c...`)
   - **Secret Access Key** (e.g., `5f6e7d8c...`)
   - **Endpoint URL**: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`

---

## 2. Environment Configuration

Add the following variables to your `.env` file on the server:

```ini
# ==============================================================================
# Cloudflare R2 Automated Database Backup
# ==============================================================================
R2_ACCOUNT_ID="your_32_character_cloudflare_account_id"
R2_ACCESS_KEY_ID="your_r2_access_key_id"
R2_SECRET_ACCESS_KEY="your_r2_secret_access_key"
R2_BUCKET_NAME="digital-product-db-backups"
BACKUP_RETENTION_DAYS=30
BACKUP_DOCKER_CONTAINER="digital-product-db"
```

### Explanation of Settings:
- `BACKUP_RETENTION_DAYS`: Number of days to retain backups in R2 before automatic deletion (default: 30 days).
- `BACKUP_DOCKER_CONTAINER`: The Docker container name for PostgreSQL (`digital-product-db`). If Docker is not running or this is left blank, the script automatically falls back to local `pg_dump`.

---

## 3. Backup Script Usage (CLI)

The backup tool is located at `scripts/r2_backup.py`. It requires `boto3`.

### 3.1 Run a Full Database Backup
```bash
# Using uv:
uv run python scripts/r2_backup.py backup

# Or using standard python:
python3 scripts/r2_backup.py backup
```

**What this does:**
1. Streams `pg_dump` from Docker container or host PostgreSQL.
2. Compresses the dump with high-ratio `gzip` (`.sql.gz`).
3. Uploads directly to Cloudflare R2 under `backups/YYYY/MM/<project>_backup_<timestamp>.sql.gz`.
4. Automatically scans and deletes any backups older than `BACKUP_RETENTION_DAYS`.

### 3.2 List Backups in Cloudflare R2
```bash
uv run python scripts/r2_backup.py list
```
**Output Example:**
```text
================================================================================
Cloudflare R2 Backups in Bucket: 'digital-product-db-backups'
================================================================================
No.  Date (UTC)             Size       Age (Days)   Key
--------------------------------------------------------------------------------
1    2026-09-21 17:00:00    2.45 MB    0.1          backups/2026/09/digital_product_selling_system_backup_20260921_170000.sql.gz
2    2026-09-20 17:00:00    2.38 MB    1.1          backups/2026/09/digital_product_selling_system_backup_20260920_170000.sql.gz
================================================================================
```

---

## 4. Automating Backups with Linux Cron

To run daily backups automatically every night at 02:00 AM UTC:

1. Open crontab on the host server:
   ```bash
   crontab -e
   ```
2. Add the following entry (adjust `/path/to/project` to your actual repo directory):
   ```bash
   # Run automated PostgreSQL backup to Cloudflare R2 every day at 2:00 AM UTC
   0 2 * * * cd /home/atik/Codes/python/fast\ api/diigtal\ product\ selling\ system/digital\ product\ selling\ system\ Backened && /usr/local/bin/uv run python scripts/r2_backup.py backup >> /var/log/db_backup.log 2>&1
   ```
3. To view backup logs:
   ```bash
   tail -f /var/log/db_backup.log
   ```

---

## 5. Disaster Recovery & Restoring Backups

If your VPS crashes, gets corrupted, or data needs to be restored from a specific snapshot:

### Step 5.1: Find the Desired Backup Key
```bash
uv run python scripts/r2_backup.py list
```

### Step 5.2: Run the Restore Command
```bash
uv run python scripts/r2_backup.py restore backups/2026/09/digital_product_selling_system_backup_20260921_170000.sql.gz
```
- The script will display a warning and ask for user confirmation (`yes/no`).
- For non-interactive scripts/CI, add the `--yes` or `-y` flag:
  ```bash
  uv run python scripts/r2_backup.py restore backups/2026/09/...sql.gz --yes
  ```

**What restore does:**
1. Downloads the `.sql.gz` snapshot from Cloudflare R2 into a secure temp directory.
2. Decompresses the SQL file.
3. Restores into PostgreSQL using `psql` (cleanly dropping and recreating tables).
4. Cleans up the temporary files from the server.

---

## 6. Uptime Monitoring with UptimeRobot

[UptimeRobot](https://uptimerobot.com) pings your application every 5 minutes (for free) and sends immediate alerts to your Telegram, Discord, or Email if the server or database goes down.

### Step 6.1: Verify Your Health Endpoint
Our API provides a dedicated health check endpoint at `/health` and `/api/v1/health`.
When accessed:
- If healthy: Returns HTTP status **200 OK** with:
  ```json
  {
    "success": true,
    "status_code": 200,
    "message": "Service is healthy",
    "data": {
      "status": "healthy",
      "database": "connected",
      "version": "0.1.0",
      "timestamp": "2026-09-21T16:00:00.000Z"
    }
  }
  ```
- If PostgreSQL is down or disconnected: It immediately returns HTTP status **503 SERVICE UNAVAILABLE**!

### Step 6.2: Configure UptimeRobot
1. Create a free account at [uptimerobot.com](https://uptimerobot.com).
2. Click **Add New Monitor**.
3. Fill in the details:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `Digital Product API Health`
   - **URL (or IP)**: `https://api.yourdomain.com/health` (or `https://yourdomain.com/health`)
   - **Monitoring Interval**: `5 minutes`
4. **Alert Contacts**:
   - Check your Email address.
   - (Recommended) Add **Telegram Bot** alert:
     - Go to *My Settings* > *Alert Contacts* > *Add Alert Contact* > Select *Telegram*.
     - Follow the instructions to connect with the UptimeRobot Telegram bot.
     - You will receive instant notifications on your phone whenever the server is down or recovers!
5. Click **Create Monitor**.

### Step 6.3: Monitor Frontend & SSL Expiry
1. Add a second monitor for your Frontend Website:
   - **URL**: `https://yourdomain.com`
   - **Monitor Type**: `HTTP(s)`
2. UptimeRobot will automatically track SSL certificate validity and alert you 7 days before SSL expiration if auto-renewal fails.
