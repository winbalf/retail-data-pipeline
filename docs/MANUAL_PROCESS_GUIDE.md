# Manual Process Guide: From Setup to Viewing Data in Superset/Grafana

This guide provides a complete step-by-step manual process to set up the retail data pipeline and view the final data in either Apache Superset or Grafana.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Step 1: Environment Setup](#step-1-environment-setup)
3. [Step 2: Start Infrastructure Services](#step-2-start-infrastructure-services)
4. [Step 3: Run Data Pipeline Manually](#step-3-run-data-pipeline-manually)
5. [Step 4: Verify Data in PostgreSQL](#step-4-verify-data-in-postgresql)
6. [Step 5: View Data in Grafana](#step-5-view-data-in-grafana)
7. [Step 6: View Data in Superset](#step-6-view-data-in-superset)

---

## Prerequisites

Before starting, ensure you have:
- Docker and Docker Compose installed
- AWS account with S3 buckets (or use LocalStack/MinIO for local testing)
- AWS credentials (Access Key ID and Secret Access Key)
- Basic knowledge of command line

---

## Step 1: Environment Setup

### 1.1 Generate Environment File

Navigate to the project root directory and generate the `.env` file:

```bash
cd /home/ehbuenoa/Projects/retail-data-pipeline
python3 scripts/generate_env.py
```

This creates a `.env` file with default values and auto-generated keys.

### 1.2 Configure Environment Variables

Edit the `.env` file and update the following critical values:

```bash
# AWS Configuration (REQUIRED)
AWS_ACCESS_KEY_ID=your_actual_aws_key
AWS_SECRET_ACCESS_KEY=your_actual_aws_secret
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_RAW=your-raw-bucket-name
S3_BUCKET_PROCESSED=your-processed-bucket-name

# PostgreSQL Configuration (optional - defaults are fine for local)
POSTGRES_USER=retail_user
POSTGRES_PASSWORD=retail_password_123
POSTGRES_DB=retail_analytics
POSTGRES_PORT=5432

# Airflow Configuration (optional - defaults are fine)
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=admin

# Grafana Configuration (optional - defaults are fine)
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin

# Superset Configuration (optional - defaults are fine)
SUPERSET_PORT=8088
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASSWORD=admin
```

**Note**: The retailer APIs are simulated and don't require external configuration.

### 1.3 Create S3 Buckets (if using AWS)

If you're using real AWS S3, create two buckets:
- Raw bucket: `your-raw-bucket-name` (for storing raw ingested data)
- Processed bucket: `your-processed-bucket-name` (for storing processed data)

**Alternative**: For local testing without AWS, you can use LocalStack or MinIO to simulate S3.

---

## Step 2: Start Infrastructure Services

### 2.1 Start Core Services

Start PostgreSQL, Airflow, and retailer systems:

```bash
docker-compose up -d postgres airflow-init
```

Wait for initialization to complete (about 30-60 seconds).

### 2.2 Start Airflow Services

```bash
docker-compose up -d airflow-webserver airflow-scheduler
```

### 2.3 Start Retailer Systems

```bash
docker-compose up -d retailer1-postgres retailer1-api \
                    retailer2-postgres retailer2-api \
                    retailer3-postgres retailer3-api
```

### 2.4 Verify Services Are Running

Check that all services are healthy:

```bash
docker-compose ps
```

You should see all services with status "Up" or "Up (healthy)".

### 2.5 Wait for Services to Be Ready

Wait approximately 30-60 seconds for all services to fully initialize, then verify:

```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U retail_user

# Check Airflow (should return HTTP 200)
curl http://localhost:8080/health

# Check Retailer APIs
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

---

## Step 3: Run Data Pipeline Manually

The pipeline consists of 4 main steps:
1. **Ingestion**: Fetch data from retailers and upload to S3
2. **Transformation**: Transform S3 data and load into PostgreSQL star schema
3. **Data Quality**: Run quality checks on transformed data
4. **Materialized Views**: Refresh materialized views for BI tools

### 3.1 Step 1: Run Ingestion

Ingest data from all 3 retailers for a specific date (use a date that has sample data, e.g., 2024-01-15):

```bash
# Using Docker (recommended)
docker-compose run --rm ingestion python -m ingestion.main 2024-01-15
```

**What this does:**
- Connects to Retailer 1, 2, and 3 APIs
- Fetches sales data for the specified date
- Normalizes data to a common format
- Uploads to S3 at: `s3://your-raw-bucket/raw/retailer_X/year=2024/month=01/day=15/sales_data.json`

**Expected output:**
```
✅ Successfully ingested 150 records from retailer_1
✅ Successfully ingested 120 records from retailer_2
✅ Successfully ingested 180 records from retailer_3
Total records ingested: 450
```

### 3.2 Verify S3 Upload

Verify that data was uploaded to S3:

```bash
# Using AWS CLI (if configured)
aws s3 ls s3://your-raw-bucket/raw/ --recursive

# Or test from Docker container
docker-compose run --rm ingestion python -c "
from shared.s3_client import get_s3_client
import boto3
s3 = get_s3_client()
response = s3.list_objects_v2(Bucket='your-raw-bucket', Prefix='raw/')
for obj in response.get('Contents', []):
    print(obj['Key'])
"
```

### 3.3 Step 2: Run Transformation

Transform the S3 data and load it into PostgreSQL:

```bash
# Using Docker (recommended)
docker-compose run --rm transformation python -m transformation.main 2024-01-15
```

**What this does:**
- Downloads data from S3 for the specified date
- Transforms data into star schema format
- Creates/updates dimension tables (dim_date, dim_product, dim_customer, dim_store, dim_retailer)
- Loads fact records into `fact_sales` table
- Handles duplicates (ON CONFLICT DO NOTHING)

**Expected output:**
```
✅ Successfully transformed and loaded data for 2024-01-15
- Dimension records created/updated: 45
- Fact records loaded: 450
```

### 3.4 Step 3: Run Data Quality Checks

Run quality checks on the transformed data:

```bash
# Using Docker (recommended)
docker-compose run --rm data-quality python -m data_quality.main 2024-01-15
```

**What this does:**
- Validates record counts
- Checks data completeness (null values)
- Validates business rules (e.g., total_amount = quantity * unit_price)
- Checks referential integrity (foreign keys)
- Validates data freshness

**Expected output:**
```
✅ Data quality checks passed
- Record count check: PASSED
- Completeness check: PASSED
- Business rules check: PASSED
- Referential integrity check: PASSED
- Data freshness check: PASSED
```

### 3.5 Step 4: Refresh Materialized Views

Refresh materialized views for BI tools:

```bash
# Using Docker (recommended)
docker-compose exec airflow-scheduler python -m materialized_views.refresh_views
```

**What this does:**
- Refreshes all 6 materialized views:
  - `mv_daily_sales_summary`
  - `mv_monthly_sales_by_category`
  - `mv_top_products_by_revenue`
  - `mv_weekly_sales_trends`
  - `mv_quarterly_sales_summary`
  - `mv_daily_sales_by_product`

**Expected output:**
```
✅ Refreshed mv_daily_sales_summary
✅ Refreshed mv_monthly_sales_by_category
✅ Refreshed mv_top_products_by_revenue
✅ Refreshed mv_weekly_sales_trends
✅ Refreshed mv_quarterly_sales_summary
✅ Refreshed mv_daily_sales_by_product
✅ All materialized views refreshed successfully
```

---

## Step 4: Verify Data in PostgreSQL

Before connecting to BI tools, verify that data exists in PostgreSQL:

### 4.1 Connect to PostgreSQL

```bash
docker-compose exec postgres psql -U retail_user -d retail_analytics
```

### 4.2 Check Fact Table

```sql
-- Check total records in fact_sales
SELECT COUNT(*) as total_sales_records FROM fact_sales;

-- View sample records
SELECT * FROM fact_sales LIMIT 5;

-- Check by retailer
SELECT 
    r.retailer_name,
    COUNT(*) as record_count,
    SUM(fs.total_amount) as total_revenue
FROM fact_sales fs
JOIN dim_retailer r ON fs.retailer_id = r.retailer_id
GROUP BY r.retailer_name;
```

### 4.3 Check Materialized Views

```sql
-- Check materialized views exist and have data
SELECT 'mv_daily_sales_summary' as view_name, COUNT(*) as row_count 
FROM mv_daily_sales_summary
UNION ALL
SELECT 'mv_top_products_by_revenue', COUNT(*) 
FROM mv_top_products_by_revenue
UNION ALL
SELECT 'mv_monthly_sales_by_category', COUNT(*) 
FROM mv_monthly_sales_by_category;

-- View sample from daily sales summary
SELECT * FROM mv_daily_sales_summary ORDER BY date DESC LIMIT 10;

-- View top products
SELECT * FROM mv_top_products_by_revenue LIMIT 10;
```

### 4.4 Exit PostgreSQL

```sql
\q
```

---

## Step 5: View Data in Grafana

### 5.1 Start Grafana Service

```bash
docker-compose up -d grafana
```

Wait for Grafana to start (about 10-20 seconds).

### 5.2 Configure Grafana Datasource

#### Option A: Use Setup Script (Recommended)

```bash
# Update datasource configuration with environment variables
./grafana/setup_datasource.sh
docker-compose restart grafana
```

#### Option B: Manual Configuration

1. **Access Grafana UI:**
   - Open browser: `http://localhost:3000`
   - Login with:
     - Username: `admin`
     - Password: `admin` (change on first login)

2. **Configure PostgreSQL Datasource:**
   - Go to **Configuration** → **Data Sources** → **Add data source**
   - Select **PostgreSQL**
   - Configure:
     - **Name**: Retail Analytics PostgreSQL
     - **Host**: `postgres:5432` (or `localhost:5432` if connecting from host)
     - **Database**: `retail_analytics`
     - **User**: `grafana_user` (or `retail_user` from your `.env`)
     - **Password**: `grafana_password_123` (or your configured password)
     - **SSL Mode**: `disable`
   - Click **Save & Test** (should show "Data source is working")

### 5.3 Access Pre-configured Dashboards

1. **Navigate to Dashboards:**
   - Click **Dashboards** → **Browse** → **Retail Analytics**

2. **Available Dashboards:**
   - **Daily Sales Dashboard**: Daily revenue trends, transaction counts, retailer comparisons
   - **Product Performance Dashboard**: Top products by revenue, category performance
   - **Sales Trends & Analytics**: Weekly trends, quarterly summaries, heatmaps

3. **View a Dashboard:**
   - Click on any dashboard to view it
   - Dashboards should automatically display data from materialized views

### 5.4 Create Custom Dashboard (Optional)

1. **Create New Dashboard:**
   - Click **Dashboards** → **New Dashboard** → **Add visualization**

2. **Add Panel:**
   - Select **Retail Analytics PostgreSQL** datasource
   - Write SQL query, for example:
   ```sql
   SELECT 
       date,
       retailer_name,
       total_revenue
   FROM mv_daily_sales_summary
   WHERE date >= CURRENT_DATE - INTERVAL '7 days'
   ORDER BY date DESC;
   ```
   - Choose visualization type (Time series, Table, etc.)
   - Click **Apply** and **Save dashboard**

### 5.5 Example Queries for Grafana

```sql
-- Daily sales summary (last 30 days)
SELECT date, retailer_name, total_revenue 
FROM mv_daily_sales_summary 
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC;

-- Top 10 products by revenue
SELECT product_name, total_revenue 
FROM mv_top_products_by_revenue 
ORDER BY total_revenue DESC 
LIMIT 10;

-- Monthly category performance
SELECT category, SUM(total_revenue) as revenue 
FROM mv_monthly_sales_by_category 
WHERE year = EXTRACT(YEAR FROM NOW()) 
GROUP BY category
ORDER BY revenue DESC;
```

---

## Step 6: View Data in Superset

### 6.1 Start Superset Service

```bash
docker-compose up -d superset-init superset
```

Wait for Superset to initialize (about 60-90 seconds). Check logs:

```bash
docker-compose logs -f superset-init
```

Wait until you see: `✅ Superset initialization completed!`

### 6.2 Access Superset UI

1. **Open Browser:**
   - URL: `http://localhost:8088`
   - Login with:
     - Username: `admin`
     - Password: `admin` (change on first login)

### 6.3 Add PostgreSQL Datasource

1. **Navigate to Databases:**
   - Click **Data** → **Databases** → **+ Database**

2. **Configure Connection (Two Methods):**

   **Method 1: Using SQLAlchemy URI (Recommended)**
   - Select **PostgreSQL** as the database type
   - **Display Name**: Retail Analytics PostgreSQL
   - **SQLAlchemy URI**: 
     ```
     postgresql://superset_user:superset_password_123@postgres:5432/retail_analytics
     ```
     **Note**: If your credentials differ, use:
     ```
     postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@postgres:5432/<POSTGRES_DB>
     ```
   - Click **Test Connection** (should show "Connection looks good!")
   - Click **Connect**

   **Method 2: Using Step-by-Step Form (If using the connection wizard)**
   - **Host**: `postgres` ⚠️ **Important**: Use `postgres` (Docker service name), NOT `localhost` or `127.0.0.1`
   - **Port**: `5432`
   - **Database name**: `retail_analytics`
   - **Username**: `superset_user`
   - **Password**: `superset_password_123` (or your configured `SUPERSET_DB_PASSWORD`)
   - **Display Name**: `Retail Analytics`
   - **SSL**: Leave disabled (toggle off)
   - Click **Test Connection** (should show "Connection looks good!")
   - Click **Connect**

   **Why `postgres` instead of `localhost`?**
   - Superset runs inside a Docker container on the same network as PostgreSQL
   - Docker containers communicate using service names (e.g., `postgres`) from `docker-compose.yml`
   - Using `localhost` would try to connect to PostgreSQL on the Superset container itself, which doesn't have PostgreSQL running

### 6.4 Explore Tables and Views

1. **View Available Tables:**
   - Go to **Data** → **Datasets**
   - You should see tables like:
     - `fact_sales`
     - `dim_date`, `dim_product`, `dim_customer`, `dim_store`, `dim_retailer`
     - `mv_daily_sales_summary`, `mv_top_products_by_revenue`, etc.

2. **Add a Dataset:**
   - Click **+ Dataset**
   - Select **Retail Analytics PostgreSQL** database
   - Select a table (e.g., `mv_daily_sales_summary`)
   - Click **Add**

### 6.5 Create Your First Chart

1. **Create Chart:**
   - Go to **Charts** → **+ Chart**
   - Select your dataset (e.g., `mv_daily_sales_summary`)
   - Choose visualization type (e.g., **Time-series Line Chart**)

2. **Configure Query:**
   - **Time Column**: `date`
   - **Metrics**: `SUM(total_revenue)` or `AVG(total_revenue)`
   - **Group by**: `retailer_name` (optional, for multi-line chart)
   - Click **Run Query** to preview
   - Click **Create Chart**

### 6.6 Create a Dashboard

1. **Create Dashboard:**
   - Go to **Dashboards** → **+ Dashboard**
   - Enter dashboard name: "Retail Analytics Overview"
   - Click **Save**

2. **Add Charts to Dashboard:**
   - Click **Edit Dashboard**
   - Click **+ Add Chart**
   - Select charts you created
   - Arrange and resize charts
   - Click **Save**

### 6.7 Example Queries for Superset

#### Daily Sales by Retailer
```sql
SELECT 
    date,
    retailer_name,
    total_revenue,
    transaction_count
FROM mv_daily_sales_summary
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC, retailer_name;
```

#### Top Products by Revenue
```sql
SELECT 
    product_name,
    category,
    total_revenue,
    total_quantity
FROM mv_top_products_by_revenue
ORDER BY total_revenue DESC
LIMIT 20;
```

#### Monthly Sales Trend
```sql
SELECT 
    year,
    month,
    category,
    total_revenue
FROM mv_monthly_sales_by_category
WHERE year = EXTRACT(YEAR FROM NOW())
ORDER BY year, month, category;
```

#### Quarterly Summary
```sql
SELECT 
    year,
    quarter,
    retailer_name,
    total_revenue,
    transaction_count
FROM mv_quarterly_sales_summary
ORDER BY year DESC, quarter DESC, retailer_name;
```

### 6.8 Use SQL Lab (Advanced)

1. **Open SQL Lab:**
   - Go to **SQL Lab** → **SQL Editor**

2. **Write and Execute Queries:**
   - Select **Retail Analytics PostgreSQL** database
   - Write any SQL query
   - Click **Run** to execute
   - View results in table format
   - Optionally save as a chart or add to dashboard

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs [service_name]

# Check if ports are in use
netstat -tuln | grep -E ':(3000|5432|8080|8088)'

# Restart services
docker-compose restart [service_name]
```

### Can't Connect to PostgreSQL from BI Tools

1. **Verify PostgreSQL is running:**
   ```bash
   docker-compose ps postgres
   ```

2. **Test connection:**
   ```bash
   docker-compose exec postgres psql -U retail_user -d retail_analytics -c "SELECT 1;"
   ```

3. **Check credentials in `.env` file match what you're using in BI tools**

### No Data in Materialized Views

1. **Verify fact_sales has data:**
   ```sql
   SELECT COUNT(*) FROM fact_sales;
   ```

2. **Manually refresh views:**
   ```bash
   docker-compose exec airflow-scheduler python -m materialized_views.refresh_views
   ```

3. **Check view definitions:**
   ```sql
   SELECT definition FROM pg_matviews WHERE matviewname LIKE 'mv_%';
   ```

### Grafana/Superset Can't See Tables

1. **Verify database user has permissions:**
   ```sql
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_user;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO superset_user;
   ```

2. **Refresh datasource in Grafana/Superset UI**

---

## Quick Reference: Complete Manual Run

For a complete manual run of the entire pipeline:

```bash
# 1. Setup (one-time)
python3 scripts/generate_env.py
# Edit .env file with your AWS credentials

# 2. Start services
docker-compose up -d postgres airflow-init
sleep 30
docker-compose up -d airflow-webserver airflow-scheduler
docker-compose up -d retailer1-postgres retailer1-api \
                    retailer2-postgres retailer2-api \
                    retailer3-postgres retailer3-api

# 3. Run pipeline (use a date with sample data, e.g., 2024-01-15)
DATE=2024-01-15

# Ingestion
docker-compose run --rm ingestion python -m ingestion.main $DATE

# Transformation
docker-compose run --rm transformation python -m transformation.main $DATE

# Data Quality
docker-compose run --rm data-quality python -m data_quality.main $DATE

# Refresh Materialized Views
docker-compose exec airflow-scheduler python -m materialized_views.refresh_views

# 4. Start BI tools
docker-compose up -d grafana superset-init superset

# 5. Access tools
# Grafana: http://localhost:3000 (admin/admin)
# Superset: http://localhost:8088 (admin/admin)
```

---

## Next Steps

- **Schedule Pipeline**: Enable the Airflow DAG to run automatically
- **Add More Data**: Run ingestion for multiple dates
- **Customize Dashboards**: Create custom visualizations in Grafana/Superset
- **Set Up Alerts**: Configure alerts for data quality issues
- **Explore Materialized Views**: Use stored procedures for advanced queries

For more information, see:
- `docs/MATERIALIZED_VIEWS.md` - Materialized views documentation
- `docs/STORED_PROCEDURES.md` - Stored procedures guide
- `grafana/README.md` - Grafana setup details
- `superset/README.md` - Superset setup details

