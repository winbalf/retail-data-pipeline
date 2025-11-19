# Quick Start Guide

## 🚀 5-Minute Setup

### 1. Generate Environment File

```bash
make setup
# OR
python3 scripts/generate_env.py
```

### 2. Edit `.env` File

Update these critical values:
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET_RAW` and `S3_BUCKET_PROCESSED`
- Retailer API URLs and keys (RETAILER_1, 2, 3)

### 3. Start Services

```bash
make up
```

Wait ~30 seconds for services to initialize, then access:
- **Airflow UI**: http://localhost:8080
  - Username: `admin`
  - Password: `admin` (from `.env`)

### 4. Enable DAG

1. Open Airflow UI
2. Find `retail_data_pipeline` DAG
3. Toggle it ON (left side)
4. Click "Trigger DAG" to run immediately, or wait for scheduled run (2 AM daily)

## 📋 Common Commands

```bash
# View logs
make logs

# Stop services
make down

# Connect to PostgreSQL
make psql

# Test ingestion manually (defaults to yesterday's date)
make test-ingestion

# Test ingestion for a specific date
make test-ingestion DATE=2024-01-15

# Test transformation manually
make test-transformation

# Test S3 bucket connectivity
make test-s3
```
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
run_terminal_cmd

## 🔍 Verify Setup

### Check PostgreSQL

```bash
make psql
# Then run:
SELECT COUNT(*) FROM fact_sales;
SELECT * FROM dim_retailer;
```

### Check Airflow

1. Go to http://localhost:8080
2. Login with admin/admin
3. Check DAG status

### Check S3 (if configured)

**Option 1: Using the test script (Recommended)**
```bash
make test-s3
```

This will:
- Test S3 connection
- Verify bucket exists
- List all uploaded files
- Download and verify a sample file

**Option 2: Using AWS CLI**
```bash
# List all files in raw bucket
aws s3 ls s3://your-raw-bucket/raw/ --recursive

# Download a specific file
aws s3 cp s3://your-raw-bucket/raw/retailer_1/year=2024/month=01/day=01/sales_data.json - | jq .

# Count files
aws s3 ls s3://your-raw-bucket/raw/ --recursive | wc -l
```

**Option 3: From inside Docker container**
```bash
# Run the test script
docker-compose run --rm ingestion python scripts/test_s3.py

# Or test specific retailer/date
docker-compose run --rm ingestion python scripts/test_s3.py retailer_1 2024-01-15
```

## ⚠️ Troubleshooting

### Services won't start
- Check if ports 5432, 8080 are available
- Verify Docker is running: `docker ps`
- Check logs: `make logs`

### Network configuration errors
If you see errors like "Network needs to be recreated" or "com.docker.network.enable_ipv6 has changed":
```bash
make recreate-network
# OR manually:
docker-compose down
docker-compose up -d
```

### Airflow DAG not appearing
- Wait 30-60 seconds for DAG to load
- Check scheduler logs: `make logs-airflow`
- Verify DAG file syntax: `python -m py_compile airflow/dags/retail_pipeline_dag.py`

### Database connection errors
- Ensure PostgreSQL is healthy: `docker-compose ps`
- Check credentials in `.env`
- Verify network: `docker network ls`

### S3 connection errors
- Verify AWS credentials in `.env`:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_DEFAULT_REGION`
- Check bucket exists: `aws s3 ls s3://your-bucket-name`
- Test connection: `make test-s3`
- For local testing, consider using LocalStack or MinIO (S3-compatible)

## 🧪 Complete Testing Workflow

To test the entire pipeline end-to-end:

1. **Run ingestion** (uploads data to S3):
   ```bash
   # Use a date that has data (retailer APIs have sample data for 2024-01-15)
   make test-ingestion DATE=2024-01-15
   
   # Or use yesterday's date (may return 0 records if no data exists)
   make test-ingestion
   ```

2. **Verify S3 uploads**:
   ```bash
   make test-s3
   ```

3. **Run transformation** (loads S3 data to PostgreSQL):
   ```bash
   make test-transformation
   ```

4. **Check PostgreSQL**:
   ```bash
   make psql
   # Then run:
   SELECT COUNT(*) FROM fact_sales;
   SELECT * FROM dim_retailer;
   ```

## 📚 Next Steps

1. **Customize Retailer APIs**: Edit `ingestion/services/retailer*.py`
2. **Adjust Schedule**: Edit `airflow/dags/retail_pipeline_dag.py`
3. **Review Data Quality Results**: Check data quality check results in Airflow task logs
4. **Connect BI Tools**: Use PostgreSQL connection details from `.env`
5. **Add Monitoring**: Set up alerts and dashboards (see `docs/PENDING_TASKS.md`)

