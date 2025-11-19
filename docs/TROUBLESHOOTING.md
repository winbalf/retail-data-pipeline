# Troubleshooting Guide

This guide helps you diagnose and fix issues with the retail data pipeline.

## 🔍 Quick Health Check

Run these commands to quickly check if everything is working:

```bash
# 1. Check if all services are running
docker-compose ps

# 2. Check Airflow UI
# Open http://localhost:8080 and verify:
# - DAG is visible and enabled
# - No failed tasks in recent runs

# 3. Check database has data
make psql
# Then run: SELECT COUNT(*) FROM fact_sales;

# 4. Check S3 connectivity
make test-s3
```

## 📊 Step-by-Step Verification

### 1. Check Docker Services Status

```bash
# List all services and their status
docker-compose ps

# Expected output should show all services as "Up" or "Up (healthy)"
# Services to check:
# - postgres (should be Up)
# - airflow-webserver (should be Up)
# - airflow-scheduler (should be Up)
# - retailer1-api, retailer2-api, retailer3-api (should be Up)
```

**If services are down:**
```bash
# Check logs for errors
docker-compose logs [service_name]

# Restart a specific service
docker-compose restart [service_name]

# Rebuild and restart all
docker-compose down
docker-compose up -d --build
```

### 2. Check Airflow Status

**Via Web UI:**
1. Open http://localhost:8080
2. Login with credentials from `.env`
3. Check DAG status:
   - Is `retail_data_pipeline` visible?
   - Is it enabled (toggle on left side)?
   - Are there any recent runs?
   - Click on a DAG run to see task status

**Via Command Line:**
```bash
# Check Airflow logs
make logs-airflow

# Or specific service
docker-compose logs airflow-scheduler
docker-compose logs airflow-webserver

# Check if scheduler is running
docker-compose exec airflow-scheduler airflow jobs check --job-type SchedulerJob
```

**Common Airflow Issues:**
- **DAG not appearing**: Check `airflow/dags/` directory is mounted correctly
- **Tasks failing**: Click on failed task → View Log to see error details
- **Scheduler not running**: Check scheduler logs for errors

### 3. Check Database Connection

```bash
# Connect to PostgreSQL
make psql

# Or directly
docker-compose exec postgres psql -U retail_user -d retail_analytics
```

**Inside psql, run these checks:**
```sql
-- Check if tables exist
\dt

-- Check if data exists
SELECT COUNT(*) FROM fact_sales;
SELECT COUNT(*) FROM dim_product;
SELECT COUNT(*) FROM dim_retailer;

-- Check recent data
SELECT * FROM fact_sales ORDER BY created_at DESC LIMIT 10;

-- Check retailer dimension
SELECT * FROM dim_retailer;
```

**If database is empty:**
- Pipeline hasn't run yet, or
- Transformation step failed, or
- No data in S3 to process

### 4. Check S3 Connectivity

```bash
# Test S3 connection and list files
make test-s3

# Or manually
docker-compose run --rm ingestion python -c "
from shared.s3_client import get_s3_client
import os
client = get_s3_client()
bucket = os.getenv('S3_BUCKET_RAW')
print(f'Testing connection to bucket: {bucket}')
try:
    response = client.list_objects_v2(Bucket=bucket, MaxKeys=5)
    print('✅ S3 connection successful!')
    if 'Contents' in response:
        print(f'Found {len(response[\"Contents\"])} files')
    else:
        print('⚠️  Bucket is empty')
except Exception as e:
    print(f'❌ S3 connection failed: {e}')
"
```

**Common S3 Issues:**
- **Access Denied**: Check AWS credentials in `.env`
- **Bucket doesn't exist**: Create bucket or update `S3_BUCKET_RAW` in `.env`
- **Wrong region**: Verify `AWS_DEFAULT_REGION` matches bucket region

### 5. Check Retailer APIs

```bash
# Test each retailer API
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health

# Test data endpoints
curl -H "X-API-Key: retailer1_api_key_123" \
     http://localhost:5001/api/sales?date=2024-01-15
```

**If APIs are not responding:**
```bash
# Check retailer service logs
docker-compose logs retailer1-api
docker-compose logs retailer2-api
docker-compose logs retailer3-api

# Restart retailer services
docker-compose restart retailer1-api retailer2-api retailer3-api
```

### 6. Test Ingestion Manually

```bash
# Test ingestion for a specific date
make test-ingestion DATE=2024-01-15

# Or for yesterday (default)
make test-ingestion

# Check output for:
# - ✅ Success messages
# - ❌ Error messages
# - Number of records ingested
```

**Common Ingestion Issues:**
- **No data returned**: Check retailer APIs are running and have data
- **S3 upload failed**: Check AWS credentials and bucket permissions
- **Network errors**: Check Docker network: `docker network inspect retail-data-pipeline_retail_network`

### 7. Test Transformation Manually

```bash
# Test transformation for a specific date
make test-transformation DATE=2024-01-15

# Or for yesterday (default)
make test-transformation
```

**Common Transformation Issues:**
- **No files found in S3**: Run ingestion first
- **Database connection failed**: Check PostgreSQL is running and credentials are correct
- **Schema errors**: Check database schema exists: `\dt` in psql

## 🔧 Common Problems and Solutions

### Problem: Services won't start

**Symptoms:**
- `docker-compose up` fails
- Services show as "Exited" in `docker-compose ps`

**Solutions:**
```bash
# Check logs
docker-compose logs

# Recreate network (fixes network issues)
make recreate-network

# Clean start
docker-compose down -v
docker-compose up -d --build
```

### Problem: Airflow DAG not running

**Symptoms:**
- DAG is enabled but no runs appear
- Scheduler shows errors

**Solutions:**
```bash
# Check scheduler logs
docker-compose logs airflow-scheduler

# Verify DAG file syntax
docker-compose exec airflow-webserver python -m py_compile /opt/airflow/dags/retail_pipeline_dag.py

# Restart scheduler
docker-compose restart airflow-scheduler
```

### Problem: Tasks failing in Airflow

**Symptoms:**
- Tasks show as "Failed" (red) in Airflow UI
- Error: `ModuleNotFoundError: No module named 'ingestion'`

**Solutions:**
1. Click on failed task → "View Log"
2. Look for error messages
3. Common causes:
   - **ModuleNotFoundError**: Python path not set correctly (see fix below)
   - Missing environment variables
   - S3 connection issues
   - Database connection issues
   - Missing dependencies

**If you see `ModuleNotFoundError: No module named 'ingestion'`:**
- This is fixed in the latest DAG code
- The DAG needs `/opt/airflow` in Python path, not `/opt/airflow/ingestion`
- Restart Airflow scheduler to reload DAG:
  ```bash
  docker-compose restart airflow-scheduler
  ```

**Debug steps:**
```bash
# Run task manually to see full error
make test-ingestion DATE=2024-01-15

# Check environment variables are set
docker-compose exec airflow-scheduler env | grep -E "AWS|S3|POSTGRES"

# Verify modules are accessible in Airflow container
docker-compose exec airflow-scheduler ls -la /opt/airflow/ingestion
docker-compose exec airflow-scheduler python -c "import sys; sys.path.insert(0, '/opt/airflow'); from ingestion.main import main; print('Import successful')"
```

### Problem: No data in database

**Symptoms:**
- `SELECT COUNT(*) FROM fact_sales;` returns 0
- Tables exist but are empty

**Solutions:**
1. **Check if ingestion ran:**
   ```bash
   # Check S3 for files
   make test-s3
   ```

2. **Check if transformation ran:**
   ```bash
   # Check Airflow task logs
   # Or run manually
   make test-transformation
   ```

3. **Check for errors:**
   ```bash
   # Check transformation logs
   docker-compose logs transformation
   ```

### Problem: S3 connection fails

**Symptoms:**
- "Access Denied" or "Bucket not found" errors

**Solutions:**
1. **Verify credentials in `.env`:**
   ```bash
   cat .env | grep AWS
   ```

2. **Test credentials:**
   ```bash
   aws s3 ls s3://your-bucket-name/
   ```

3. **Check bucket exists and region:**
   ```bash
   aws s3api head-bucket --bucket your-bucket-name
   ```

4. **Verify IAM permissions:**
   - Need: `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`

### Problem: Database connection fails

**Symptoms:**
- "Connection refused" or "Authentication failed"

**Solutions:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check credentials
cat .env | grep POSTGRES

# Test connection
docker-compose exec postgres psql -U retail_user -d retail_analytics -c "SELECT 1;"

# Check if database exists
docker-compose exec postgres psql -U retail_user -d postgres -c "\l"
```

### Problem: Retailer APIs not responding

**Symptoms:**
- `curl http://localhost:5001/health` fails
- Ingestion fails with connection errors

**Solutions:**
```bash
# Check if services are running
docker-compose ps | grep retailer

# Check logs
docker-compose logs retailer1-api

# Restart services
docker-compose restart retailer1-api retailer2-api retailer3-api

# Rebuild if needed
docker-compose up -d --build retailer1-api retailer2-api retailer3-api
```

## 📋 Diagnostic Checklist

Use this checklist to systematically diagnose issues:

- [ ] All Docker services are running (`docker-compose ps`)
- [ ] Airflow UI is accessible (http://localhost:8080)
- [ ] DAG is enabled in Airflow UI
- [ ] PostgreSQL is accessible (`make psql`)
- [ ] Database schema exists (`\dt` in psql)
- [ ] S3 connection works (`make test-s3`)
- [ ] Retailer APIs respond (`curl http://localhost:5001/health`)
- [ ] Environment variables are set (check `.env` file)
- [ ] Recent DAG runs exist in Airflow
- [ ] No failed tasks in recent runs
- [ ] Data exists in S3 (check with `make test-s3`)
- [ ] Data exists in database (`SELECT COUNT(*) FROM fact_sales;`)

## 🚨 Emergency Reset

If everything is broken and you need a fresh start:

```bash
# ⚠️ WARNING: This deletes all data!

# Stop everything
docker-compose down -v

# Remove all containers and volumes
docker system prune -a --volumes

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d

# Wait for services to initialize
sleep 30

# Verify services are up
docker-compose ps

# Re-enable DAG in Airflow UI
```

## 📞 Getting Help

When asking for help, provide:

1. **Error messages**: Full error output from logs
2. **Service status**: Output of `docker-compose ps`
3. **Recent logs**: Relevant log excerpts
4. **Configuration**: `.env` file (with sensitive data redacted)
5. **What you tried**: Steps you've already attempted

## 🔍 Advanced Debugging

### View Real-time Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f airflow-scheduler

# Last 100 lines
docker-compose logs --tail=100 airflow-scheduler
```

### Execute Commands in Containers

```bash
# Access Airflow container
docker-compose exec airflow-webserver bash

# Access PostgreSQL
docker-compose exec postgres bash

# Run Python in ingestion container
docker-compose run --rm ingestion python
```

### Check Network Connectivity

```bash
# List networks
docker network ls

# Inspect network
docker network inspect retail-data-pipeline_retail_network

# Test connectivity between containers
docker-compose exec ingestion ping postgres
docker-compose exec ingestion ping retailer1-api
```

### Monitor Resource Usage

```bash
# Container resource usage
docker stats

# Disk usage
docker system df

# Volume usage
docker volume ls
```

