# Retail Analytics Data Pipeline

An end-to-end retail analytics data pipeline that ingests raw sales data from 3 different retailers into AWS S3, transforms it into a star schema using Python + SQL, orchestrates daily runs with Airflow, and exposes analytics tables in PostgreSQL 14 for BI tools like Athena/Quicksight.

## 🏗️ Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Retailer 1 │     │  Retailer 2 │     │  Retailer 3 │
│ (Simulated) │     │ (Simulated) │     │ (Simulated) │
│  PostgreSQL │     │  PostgreSQL │     │  PostgreSQL │
│  + Flask API│     │  + Flask API│     │  + Flask API│
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Ingestion Service   │
              │   (Python)            │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   AWS S3 (Raw Data)   │
              │   s3://raw-bucket/    │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │Transformation Service │
              │   (Python + SQL)      │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  PostgreSQL 14        │
              │  (Star Schema)        │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  BI Tools             │
              │  (Athena/Quicksight)  │
              └───────────────────────┘
```

> **Note**: The 3 retailers are **simulated systems** running in Docker containers. Each retailer has its own PostgreSQL database with different schemas, column names, and data structures to simulate real-world heterogeneity. See [docs/RETAILERS.md](docs/RETAILERS.md) for details.

## 📁 Repository Structure

```
retail-data-pipeline/
├── airflow/                    # Airflow orchestration
│   ├── dags/                   # Airflow DAG definitions
│   │   └── retail_pipeline_dag.py
│   ├── config/                 # Airflow configuration
│   └── plugins/                # Custom Airflow plugins
├── database/                   # Database initialization
│   └── init/
│       └── 01_create_schema.sql  # Star schema creation
├── docker/                     # Docker configurations
│   ├── airflow/               # Airflow Dockerfile (uses official image)
│   ├── ingestion/
│   │   └── Dockerfile         # Ingestion service container
│   ├── transformation/
│   │   └── Dockerfile         # Transformation service container
│   └── data_quality/
│       └── Dockerfile         # Data quality service container
├── ingestion/                  # Data ingestion service
│   ├── models/                # Data models
│   │   └── retailer_data.py
│   ├── services/              # Retailer API services
│   │   ├── retailer1_service.py
│   │   ├── retailer2_service.py
│   │   └── retailer3_service.py
│   └── main.py                # Main ingestion entry point
├── transformation/             # Data transformation service
│   ├── processors/
│   │   └── star_schema_processor.py
│   └── main.py                # Main transformation entry point
├── data_quality/               # Data quality service
│   ├── quality_checks.py      # Quality check implementations
│   └── main.py                # Main data quality entry point
├── shared/                     # Shared utilities
│   ├── database.py            # PostgreSQL connection utilities
│   └── s3_client.py           # S3 client utilities
├── scripts/                    # Utility scripts
│   └── generate_env.py        # Auto-generate .env file
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Main Folders Overview

- **`airflow/`** - Apache Airflow orchestration configuration and DAGs. Contains workflow definitions, Airflow configuration files, and custom plugins for scheduling and monitoring the data pipeline.

- **`database/`** - Database initialization scripts. Contains SQL scripts that create the star schema (dimension and fact tables) in PostgreSQL when the database is first initialized.

- **`docker/`** - Docker container definitions. Contains Dockerfiles for building the ingestion and transformation service containers, as well as Airflow-specific Docker configurations.

- **`docs/`** - Project documentation. Contains detailed documentation including retailer schemas, troubleshooting guides, and other project documentation.

- **`ingestion/`** - Data ingestion service. Python service that fetches sales data from the three retailer APIs, normalizes the data to a common format, and uploads it to AWS S3. Contains retailer-specific service implementations and data models.

- **`logs/`** - Application log files. Directory where runtime logs from services are stored (if configured).

- **`retailers/`** - Simulated retailer systems. Contains the three simulated retailer systems (PostgreSQL databases + Flask APIs) that represent different retailer data sources with varying schemas and authentication methods.

- **`scripts/`** - Utility and helper scripts. Contains various utility scripts for environment setup, health checks, testing, and other operational tasks.

- **`shared/`** - Shared utilities and common code. Contains reusable Python modules for database connections, S3 client operations, and other shared functionality used across ingestion and transformation services.

- **`tests/`** - Test files. Contains unit tests, integration tests, and other test suites for validating the pipeline components.

- **`transformation/`** - Data transformation service. Python service that reads raw data from S3, transforms it into a star schema format, and loads it into PostgreSQL. Contains processors for handling dimension and fact table transformations.

- **`data_quality/`** - Data quality service. Python service that performs quality checks on transformed data in PostgreSQL. Validates record counts, data completeness, business rules, referential integrity, and data freshness. Can be run standalone or as part of the Airflow DAG.

## 🐳 Docker Containers

The project uses Docker Compose to orchestrate the following containers:

### 1. **PostgreSQL 14** (`postgres`)
   - **Purpose**: Data warehouse storing the star schema
   - **Port**: 5432 (configurable via `.env`)
   - **Volumes**: 
     - Persistent data storage
     - Database initialization scripts
   - **Health Check**: Monitors database readiness

### 2. **Airflow Webserver** (`airflow-webserver`)
   - **Purpose**: Web UI for monitoring and managing DAGs
   - **Port**: 8080 (configurable via `.env`)
   - **Volumes**: DAGs, plugins, logs, and application code
   - **Dependencies**: PostgreSQL (for Airflow metadata)

### 3. **Airflow Scheduler** (`airflow-scheduler`)
   - **Purpose**: Executes scheduled DAGs
   - **Volumes**: Same as webserver
   - **Dependencies**: PostgreSQL

### 4. **Airflow Init** (`airflow-init`)
   - **Purpose**: One-time initialization of Airflow database and admin user
   - **Runs**: Only on first startup

### 5. **Retailer Systems** (3 simulated retailers)
   - **Retailer 1**: PostgreSQL + Flask API (port 5001, DB port 5433)
   - **Retailer 2**: PostgreSQL + Flask API (port 5002, DB port 5434)
   - **Retailer 3**: PostgreSQL + Flask API (port 5003, DB port 5435)
   - **Purpose**: Simulate real retailer systems with different schemas
   - **Features**:
     - Each has unique table names, column names, and data types
     - Pre-populated with sample sales data
     - REST APIs with different authentication methods
     - See [docs/RETAILERS.md](docs/RETAILERS.md) for details

### 6. **Ingestion Service** (`ingestion`)
   - **Purpose**: Fetches data from 3 retailer APIs and uploads to S3
   - **Profile**: `services` (optional, can be run standalone)
   - **Functionality**:
     - Connects to 3 different retailer APIs (simulated)
     - Normalizes data to common format
     - Uploads to S3 with date partitioning

### 7. **Transformation Service** (`transformation`)
   - **Purpose**: Reads from S3 and loads into PostgreSQL star schema
   - **Profile**: `services` (optional, can be run standalone)
   - **Functionality**:
     - Downloads data from S3
     - Transforms to star schema (dimensions + facts)
     - Loads into PostgreSQL

### 8. **Data Quality Service** (`data-quality`)
   - **Purpose**: Performs quality checks on transformed data in PostgreSQL
   - **Profile**: `services` (optional, can be run standalone)
   - **Functionality**:
     - Validates record counts
     - Checks data completeness (null values)
     - Validates business rules (e.g., total_amount = quantity * unit_price)
     - Checks referential integrity (foreign keys)
     - Validates data freshness

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose installed
- AWS account with S3 buckets created
- AWS credentials (Access Key ID and Secret Access Key)
- API credentials for the 3 retailers

### Step 1: Generate Environment File

The project includes an automatic `.env` file generator:

```bash
python3 scripts/generate_env.py
```

This will create a `.env` file with:
- Auto-generated Airflow encryption keys
- Default PostgreSQL credentials
- Placeholder values for AWS and retailer APIs

### Step 2: Configure Environment Variables

Edit the `.env` file and update the following with your actual values:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_actual_aws_key
AWS_SECRET_ACCESS_KEY=your_actual_aws_secret
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_RAW=your-raw-bucket-name
S3_BUCKET_PROCESSED=your-processed-bucket-name
```

> **Note**: The retailer APIs are already configured to use local simulated systems. No changes needed unless you want to use external APIs.

### Step 3: Create S3 Buckets

Create two S3 buckets in your AWS account:
- **Raw bucket**: For storing raw ingested data (e.g., `retail-raw-data`)
- **Processed bucket**: For storing processed/transformed data (optional, for future use)

> **Note**: If you don't have AWS access, you can use LocalStack or MinIO to simulate S3 locally. The pipeline will work with any S3-compatible storage.

### Step 4: Start the Pipeline

Start all services:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL 14
- Airflow (webserver + scheduler)
- Initialize Airflow database

To also start the ingestion and transformation services (optional):

```bash
docker-compose --profile services up -d
```

### Step 5: Access Airflow UI

1. Open your browser and go to: `http://localhost:8080`
2. Login with credentials from `.env`:
   - Username: `admin` (or your configured `AIRFLOW_USERNAME`)
   - Password: `admin` (or your configured `AIRFLOW_PASSWORD`)

### Step 6: Enable and Monitor DAGs

1. In the Airflow UI, find the `retail_data_pipeline` DAG
2. Toggle it ON to enable scheduling
3. The DAG runs daily at 2 AM (configurable in `airflow/dags/retail_pipeline_dag.py`)

## 📊 Database Schema (Star Schema)

The pipeline creates a star schema in PostgreSQL with the following structure:

### Dimension Tables

- **dim_date**: Date dimension with year, quarter, month, week, day attributes
- **dim_product**: Product dimension with SKU, name, category
- **dim_customer**: Customer dimension
- **dim_store**: Store dimension
- **dim_retailer**: Retailer dimension (3 retailers)

### Fact Table

- **fact_sales**: Sales fact table with:
  - Foreign keys to all dimensions
  - Transaction ID
  - Quantity, unit price, total amount
  - Timestamps

## 🔄 Pipeline Workflow

### Daily Execution Flow

1. **Ingestion** (2:00 AM daily):
   - Fetches sales data from Retailer 1, 2, and 3 APIs
   - Normalizes data to common format
   - Uploads to S3 with partitioning: `raw/{retailer_id}/year={year}/month={month}/day={day}/sales_data.json`

2. **Transformation** (after ingestion):
   - Downloads data from S3
   - Creates/updates dimension tables
   - Loads fact records into `fact_sales`
   - Handles duplicates (ON CONFLICT DO NOTHING)

3. **Data Quality** (after transformation):
   - Runs comprehensive quality checks on transformed data
   - Validates record counts, completeness, business rules, referential integrity, and freshness
   - Fails the pipeline if any critical checks fail

## 🛠️ Manual Execution

### Run Ingestion Manually

```bash
# Using Docker
docker-compose run --rm ingestion python -m ingestion.main 2024-01-15

# Or directly
cd ingestion && python main.py 2024-01-15
```

### Run Transformation Manually

```bash
# Using Docker
docker-compose run --rm transformation python -m transformation.main 2024-01-15

# Or directly
cd transformation && python main.py 2024-01-15
```

### Run Data Quality Checks Manually

```bash
# Using Docker
docker-compose run --rm data-quality python -m data_quality.main 2024-01-15

# Or directly
cd data_quality && python main.py 2024-01-15
```

## 📈 Connecting BI Tools

### Amazon Athena

1. Create an external table pointing to S3:
```sql
CREATE EXTERNAL TABLE retail_sales (
    retailer_id string,
    transaction_id string,
    product_id string,
    ...
)
STORED AS JSON
LOCATION 's3://your-bucket/raw/';
```

### Amazon QuickSight

1. Connect to PostgreSQL data source
2. Use connection details from `.env`:
   - Host: `localhost` (or your PostgreSQL host)
   - Port: `5432`
   - Database: `retail_analytics`
   - Username/Password: From `.env`

### Direct PostgreSQL Connection

Connect using any PostgreSQL client:
- Host: `localhost`
- Port: `5432` (or your configured port)
- Database: `retail_analytics`
- Username/Password: From `.env`

## 🔧 Configuration

### Change DAG Schedule

Edit `airflow/dags/retail_pipeline_dag.py`:

```python
schedule_interval='0 2 * * *',  # Change to your preferred schedule
```

### Modify Retailer API Integration

The project includes **3 simulated retailer systems** with different schemas. To modify them:

1. **Retailer Database Schemas**: Edit SQL files in:
   - `retailers/retailer1/database/init_schema.sql`
   - `retailers/retailer2/database/init_schema.sql`
   - `retailers/retailer3/database/init_schema.sql`

2. **Retailer APIs**: Edit Flask apps in:
   - `retailers/retailer1/api/app.py`
   - `retailers/retailer2/api/app.py`
   - `retailers/retailer3/api/app.py`

3. **Ingestion Services**: Edit normalization logic in `ingestion/services/`:
   - `retailer1_service.py`
   - `retailer2_service.py`
   - `retailer3_service.py`

Each service implements:
- `fetch_sales_data()`: Fetches data from API
- `normalize_sales_record()`: Normalizes to common format

See [docs/RETAILERS.md](docs/RETAILERS.md) for detailed information about each retailer's schema and API.

## 🧪 Testing

### Quick Health Check

Run a comprehensive health check of all pipeline components:

```bash
make health-check
```

This will check:
- Docker services status
- PostgreSQL connectivity and data
- Airflow webserver and scheduler
- Retailer APIs
- S3 connection
- Environment variables
- Recent pipeline activity

### Test Database Connection

```bash
docker-compose exec postgres psql -U retail_user -d retail_analytics -c "SELECT COUNT(*) FROM fact_sales;"
```

### Test S3 Connection

```bash
make test-s3
```

Or manually:
```bash
docker-compose run --rm ingestion python -c "from shared.s3_client import get_s3_client; print(get_s3_client())"
```

## 📝 Logs

- **Airflow logs**: `airflow/logs/`
- **Application logs**: `logs/` (if configured)
- **Docker logs**: `docker-compose logs -f [service_name]`

## 🔧 Troubleshooting

If you encounter issues, see the comprehensive troubleshooting guide:

```bash
# View troubleshooting guide
cat docs/TROUBLESHOOTING.md

# Or run health check
make health-check
```

The troubleshooting guide covers:
- Step-by-step verification procedures
- Common problems and solutions
- Diagnostic checklist
- How to check each component
- Emergency reset procedures

## 🛑 Stopping the Pipeline

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

## 🔐 Security Notes

- **Never commit `.env` file** (already in `.gitignore`)
- Rotate AWS credentials regularly
- Use IAM roles instead of access keys when possible
- Secure PostgreSQL with strong passwords in production
- Use Airflow's RBAC for user management in production

## 📚 Next Steps

- Enhance data quality checks (add Great Expectations, audit tables, alerting)
- Implement incremental loading strategies
- Add monitoring and alerting
- Create materialized views for common queries
- Set up data retention policies
- Add unit and integration tests

For a complete list of pending tasks and enhancements, see [docs/PENDING_TASKS.md](docs/PENDING_TASKS.md).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is provided as-is for educational and commercial use.
