# Architecture Documentation

## System Overview

This retail analytics data pipeline is designed as a modern ETL (Extract, Transform, Load) system following best practices for data engineering.

## Component Details

### 1. Data Ingestion Layer

**Purpose**: Extract data from multiple heterogeneous sources and land it in a centralized raw data store.

**Components**:
- **Retailer Services** (`ingestion/services/`):
  - Each retailer has a dedicated service class
  - Handles API authentication and data fetching
  - Normalizes data to a common schema (`SalesRecord`)
  
- **Main Ingestion** (`ingestion/main.py`):
  - Orchestrates ingestion from all retailers
  - Handles errors gracefully (one retailer failure doesn't stop others)
  - Uploads to S3 with date partitioning

**Data Flow**:
```
Retailer APIs → Normalization → S3 Raw Bucket
                (SalesRecord)
```

**S3 Structure**:
```
s3://raw-bucket/
  raw/
    retailer_1/
      year=2024/
        month=01/
          day=15/
            sales_data.json
    retailer_2/
      ...
    retailer_3/
      ...
```

### 2. Data Transformation Layer

**Purpose**: Transform raw data into an analytical star schema optimized for BI queries.

**Components**:
- **Star Schema Processor** (`transformation/processors/star_schema_processor.py`):
  - Reads from S3
  - Creates/updates dimension tables (SCD Type 1)
  - Loads fact records with deduplication

**Star Schema Design**:

```
                    fact_sales
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    dim_date      dim_product    dim_customer
        │              │              │
    dim_store      dim_retailer
```

**Dimension Tables**:
- **dim_date**: Pre-aggregated date attributes for time-based analysis
- **dim_product**: Product master data
- **dim_customer**: Customer dimension (optional)
- **dim_store**: Store dimension (optional)
- **dim_retailer**: Retailer dimension (3 retailers)

**Fact Table**:
- **fact_sales**: Transaction-level sales data
  - Granularity: One row per product per transaction
  - Measures: quantity, unit_price, total_amount
  - Foreign keys to all dimensions

### 3. Data Storage Layer

**PostgreSQL 14**:
- **Purpose**: Analytical data warehouse
- **Schema**: Star schema (denormalized for query performance)
- **Indexes**: Optimized for common query patterns
- **Partitioning**: Can be added for large-scale deployments

**Benefits**:
- Fast analytical queries
- Easy to understand for business users
- Compatible with all BI tools
- Supports complex joins and aggregations

### 4. Orchestration Layer

**Apache Airflow**:
- **Purpose**: Schedule and monitor data pipeline execution
- **DAG**: `retail_data_pipeline`
  - Runs daily at 2 AM
  - Sequential tasks: Ingest → Transform → Quality Check → Refresh Materialized Views
  - Retry logic: 2 retries with 5-minute delay

**Task Dependencies**:
```
ingest_retailers_to_s3
    ↓
transform_s3_to_postgres
    ↓
data_quality_check
    ↓
refresh_materialized_views
```

## Data Quality Considerations

### Current Implementation
- **Deduplication**: Uses `ON CONFLICT DO NOTHING` for fact table
- **Error Handling**: Graceful degradation (one retailer failure doesn't stop pipeline)
- **Logging**: Comprehensive logging at each step

### Future Enhancements
- Great Expectations integration
- Data profiling and statistics
- Alerting on data quality issues
- Schema validation

## Scalability Considerations

### Current Design
- **Batch Processing**: Daily batch loads
- **Partitioning**: Date-based S3 partitioning
- **Deduplication**: Handles re-runs safely

### Scaling Options
1. **Horizontal Scaling**: Add more Airflow workers
2. **Incremental Loading**: Process only new/changed records
3. **Parallel Processing**: Process retailers in parallel
4. **Database Partitioning**: Partition fact_sales by date
5. **Materialized Views**: ✅ Pre-aggregate common queries (6 views implemented)

## Security

### Current Implementation
- Environment variables for sensitive data
- `.env` file in `.gitignore`
- Docker network isolation

### Production Recommendations
1. Use AWS IAM roles instead of access keys
2. Encrypt S3 buckets
3. Use PostgreSQL SSL connections
4. Implement Airflow RBAC
5. Rotate credentials regularly
6. Use secrets management (AWS Secrets Manager, HashiCorp Vault)

## Monitoring & Observability

### Current Logging
- Application logs via print statements
- Airflow task logs
- Docker container logs

### Recommended Additions
1. **Metrics**: Track record counts, processing times
2. **Alerting**: Email/Slack on failures
3. **Dashboards**: Grafana for pipeline health
4. **Data Lineage**: Track data flow
5. **Cost Monitoring**: Track S3 and compute costs

## BI Tool Integration

### Amazon Athena
- Create external tables pointing to S3
- Query raw data directly
- No ETL needed for raw data access

### Amazon QuickSight
- Connect to PostgreSQL
- Use star schema for fast queries
- Create dashboards on fact/dimension tables

### Other BI Tools
- Any tool with PostgreSQL connector
- Standard SQL queries work
- Star schema optimized for analytics

## Error Recovery

### Ingestion Failures
- Retry logic in Airflow (2 retries)
- Partial success: Other retailers continue
- Manual re-run via Airflow UI

### Transformation Failures
- Transaction rollback on errors
- Idempotent design: Safe to re-run
- Checkpointing: Can resume from last successful date

## Performance Optimization

### Current Optimizations
- Database indexes on foreign keys
- Date partitioning in S3
- Batch inserts with transactions

### Future Optimizations
1. **Parallel Processing**: Multi-threaded ingestion
2. **Incremental Loading**: Only process new data
3. **Materialized Views**: ✅ Pre-compute aggregations (6 views implemented, see `docs/MATERIALIZED_VIEWS.md`)
4. **Columnar Storage**: Consider columnar format for S3
5. **Caching**: Cache dimension lookups

