# Materialized Views Documentation

This document describes the materialized views available in the retail analytics data warehouse. These views pre-aggregate common analytical queries to improve query performance for BI tools and reporting.

## Quick Start Guide

### 1. How to Verify Views Are Working Fine ✅

#### Option A: Automated Verification Script (Recommended)

**Run in Docker (recommended - has all dependencies):**
```bash
docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/verify_views.py
```

**Or run locally (requires dependencies):**
```bash
pip install -r requirements.txt
python materialized_views/verify_views.py
```

This script checks:
- ✅ All 6 views exist in the database
- ✅ Views contain data (row counts)
- ✅ Views are queryable
- ✅ Indexes are properly created
- ✅ View structure is correct

**What to look for:**
- All views should show "✅ View exists"
- All views should have data (row_count > 0)
- All views should be queryable
- Summary should show: "✅ All views are working correctly!"

#### Option B: Manual PostgreSQL Check

```bash
# Connect to database
docker exec -it retail_postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>

# List all materialized views
\dm+ mv_*

# Check row counts
SELECT 'mv_daily_sales_summary' as view_name, COUNT(*) as row_count FROM mv_daily_sales_summary
UNION ALL
SELECT 'mv_monthly_sales_by_category', COUNT(*) FROM mv_monthly_sales_by_category
UNION ALL
SELECT 'mv_top_products_by_revenue', COUNT(*) FROM mv_top_products_by_revenue
UNION ALL
SELECT 'mv_weekly_sales_trends', COUNT(*) FROM mv_weekly_sales_trends
UNION ALL
SELECT 'mv_quarterly_sales_summary', COUNT(*) FROM mv_quarterly_sales_summary
UNION ALL
SELECT 'mv_daily_sales_by_product', COUNT(*) FROM mv_daily_sales_by_product;

# Test a sample query
SELECT * FROM mv_daily_sales_summary LIMIT 5;
```

### 2. What Can You Do With Those Views? 📊

The materialized views enable fast analytical queries. Here are the main use cases:

#### A. Daily Sales Analysis
- **View**: `mv_daily_sales_summary`
- **Use for**: Daily dashboards, daily KPIs, retailer daily performance
- **Example**: "Show me daily revenue for the last 7 days"

#### B. Product Performance
- **Views**: `mv_top_products_by_revenue`, `mv_daily_sales_by_product`
- **Use for**: Top products, product rankings, product trends
- **Example**: "What are my top 10 products by revenue?"

#### C. Category Analysis
- **View**: `mv_monthly_sales_by_category`
- **Use for**: Category performance, category trends, category comparison
- **Example**: "Which categories performed best this month?"

#### D. Trend Analysis
- **Views**: `mv_weekly_sales_trends`, `mv_monthly_sales_by_category`
- **Use for**: Weekly patterns, seasonal trends, growth analysis
- **Example**: "Show me weekly sales trends for this year"

#### E. High-Level Reporting
- **View**: `mv_quarterly_sales_summary`
- **Use for**: Quarterly reviews, executive summaries, business reviews
- **Example**: "What's our quarterly performance by retailer?"

#### Try Example Queries

Run the interactive example queries script:

```bash
# In Docker
docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/example_queries.py

# Or locally
python materialized_views/example_queries.py
```

This shows 8 real-world examples:
1. Daily sales dashboard
2. Top products analysis
3. Category performance
4. Weekly trends
5. Quarterly summaries
6. Product daily trends
7. Retailer comparisons
8. Category growth analysis

#### Common Query Patterns

**Get daily sales for a retailer:**
```sql
SELECT date, total_revenue, transaction_count
FROM mv_daily_sales_summary
WHERE retailer_name = 'Retailer 1'
  AND date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC;
```

**Find top products:**
```sql
SELECT product_name, total_revenue, total_quantity_sold
FROM mv_top_products_by_revenue
ORDER BY total_revenue DESC
LIMIT 10;
```

**Compare retailers:**
```sql
SELECT 
    retailer_name,
    SUM(total_revenue) as total_revenue,
    AVG(total_revenue) as avg_daily_revenue
FROM mv_daily_sales_summary
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY retailer_name;
```

### 3. How to Show Them Visually? 📈

#### Option A: Automated Visualization Script (Recommended)

Generate charts automatically:

```bash
# In Docker (install matplotlib first if needed)
docker-compose exec airflow-scheduler pip install matplotlib
docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/visualize_views.py

# Or locally
pip install matplotlib
python materialized_views/visualize_views.py
```

**Note**: If you get permission errors in Docker, charts will be saved to `/tmp/materialized_views_charts` in the container. Copy them out with:
```bash
docker cp retail_airflow_scheduler:/tmp/materialized_views_charts ./materialized_views/charts
```

This creates 5 visualizations in `materialized_views/charts/`:
- 📊 `daily_sales_trend.png` - Daily revenue line chart
- 📊 `top_products.png` - Top 10 products bar chart
- 📊 `category_performance.png` - Category performance comparison
- 📊 `weekly_trends.png` - Weekly sales trends
- 📊 `retailer_comparison.png` - Retailer performance comparison

#### Option B: Connect BI Tools

**Grafana (✅ Pre-configured!)** - See `grafana/README.md` for details

**Metabase / Tableau / Power BI**
- Connect using PostgreSQL connection details from `.env`
- Import materialized views as data sources
- Build visualizations and dashboards

#### Option C: Python/Jupyter Notebooks

```python
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import text
from shared.database import get_postgres_engine

engine = get_postgres_engine()

# Option 1: Using stored procedure function (recommended)
query = """
SELECT period_start as date, total_revenue
FROM get_sales_trends(
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE,
    'daily',
    NULL
)
ORDER BY period_start;
"""

df = pd.read_sql(query, engine)
df['date'] = pd.to_datetime(df['date'])

# Create visualization
pivot_df = df.pivot(index='date', columns='retailer_name', values='total_revenue')
pivot_df.plot(kind='line', figsize=(12, 6))
plt.title('Daily Sales Revenue Trend')
plt.xlabel('Date')
plt.ylabel('Revenue ($)')
plt.legend()
plt.show()
```

#### Quick Reference

| Task | Command (Docker) | Command (Local) |
|------|------------------|----------------|
| Verify views | `docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/verify_views.py` | `python materialized_views/verify_views.py` |
| See examples | `docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/example_queries.py` | `python materialized_views/example_queries.py` |
| Generate charts | `docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/visualize_views.py` | `python materialized_views/visualize_views.py` |
| Refresh views | `docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/main.py` | `python materialized_views/main.py` |

---

## Overview

Materialized views are pre-computed query results stored as physical tables. They are automatically refreshed after each daily data pipeline run to ensure they contain the latest aggregated data.

## Available Materialized Views

### 1. `mv_daily_sales_summary`

**Purpose**: Daily aggregated sales metrics per retailer.

**Use Cases**:
- Daily sales dashboards
- Retailer performance comparison by day
- Daily revenue tracking

**Columns**:
- `date` - Sales date
- `year` - Year
- `month` - Month (1-12)
- `quarter` - Quarter (1-4)
- `retailer_id` - Retailer ID
- `retailer_name` - Retailer name
- `transaction_count` - Total number of transaction line items
- `unique_transactions` - Number of distinct transactions
- `total_quantity` - Total quantity sold
- `total_revenue` - Total revenue (sum of total_amount)
- `avg_unit_price` - Average unit price
- `min_transaction_amount` - Minimum transaction amount
- `max_transaction_amount` - Maximum transaction amount

**Example Query**:
```sql
-- Get daily sales for a specific retailer
SELECT date, total_revenue, transaction_count, total_quantity
FROM mv_daily_sales_summary
WHERE retailer_name = 'Retailer 1'
  AND date >= '2024-01-01'
ORDER BY date DESC;
```

**Indexes**:
- `idx_mv_daily_sales_summary_date` - On `date` column
- `idx_mv_daily_sales_summary_retailer` - On `retailer_id` column
- `idx_mv_daily_sales_summary_year_month` - On `(year, month)` columns

---

### 2. `mv_monthly_sales_by_category`

**Purpose**: Monthly aggregated sales by product category.

**Use Cases**:
- Category performance analysis
- Monthly category trends
- Category comparison across retailers

**Columns**:
- `year` - Year
- `month` - Month (1-12)
- `quarter` - Quarter (1-4)
- `category` - Product category
- `retailer_id` - Retailer ID
- `retailer_name` - Retailer name
- `transaction_count` - Total number of transaction line items
- `unique_transactions` - Number of distinct transactions
- `unique_products` - Number of distinct products in category
- `total_quantity` - Total quantity sold
- `total_revenue` - Total revenue
- `avg_unit_price` - Average unit price

**Example Query**:
```sql
-- Get monthly sales by category for a specific retailer
SELECT year, month, category, total_revenue, unique_products
FROM mv_monthly_sales_by_category
WHERE retailer_name = 'Retailer 1'
  AND year = 2024
ORDER BY year, month, total_revenue DESC;
```

**Indexes**:
- `idx_mv_monthly_sales_category_year_month` - On `(year, month, category)` columns
- `idx_mv_monthly_sales_category_retailer` - On `retailer_id` column

---

### 3. `mv_top_products_by_revenue`

**Purpose**: Product-level aggregated sales ranked by revenue.

**Use Cases**:
- Top products analysis
- Product performance comparison
- Product revenue ranking

**Columns**:
- `product_id` - Product ID
- `product_sku` - Product SKU
- `product_name` - Product name
- `category` - Product category
- `retailer_id` - Retailer ID
- `retailer_name` - Retailer name
- `transaction_count` - Total number of transaction line items
- `unique_transactions` - Number of distinct transactions
- `total_quantity_sold` - Total quantity sold
- `total_revenue` - Total revenue (all-time)
- `avg_unit_price` - Average unit price
- `min_unit_price` - Minimum unit price
- `max_unit_price` - Maximum unit price

**Example Query**:
```sql
-- Get top 10 products by revenue
SELECT product_name, category, total_revenue, total_quantity_sold
FROM mv_top_products_by_revenue
WHERE retailer_name = 'Retailer 1'
ORDER BY total_revenue DESC
LIMIT 10;
```

**Indexes**:
- `idx_mv_top_products_revenue` - On `total_revenue DESC` (for fast top-N queries)
- `idx_mv_top_products_category` - On `category` column
- `idx_mv_top_products_retailer` - On `retailer_id` column

---

### 4. `mv_weekly_sales_trends`

**Purpose**: Weekly aggregated sales for trend analysis.

**Use Cases**:
- Weekly sales trends
- Week-over-week comparisons
- Seasonal pattern analysis

**Columns**:
- `year` - Year
- `week` - Week number (1-52/53)
- `quarter` - Quarter (1-4)
- `retailer_id` - Retailer ID
- `retailer_name` - Retailer name
- `transaction_count` - Total number of transaction line items
- `unique_transactions` - Number of distinct transactions
- `days_with_sales` - Number of days with sales in the week
- `total_quantity` - Total quantity sold
- `total_revenue` - Total revenue
- `avg_transaction_amount` - Average transaction amount
- `week_start_date` - First date in the week
- `week_end_date` - Last date in the week

**Example Query**:
```sql
-- Get weekly sales trends for a retailer
SELECT year, week, total_revenue, avg_transaction_amount, days_with_sales
FROM mv_weekly_sales_trends
WHERE retailer_name = 'Retailer 1'
  AND year = 2024
ORDER BY year, week;
```

**Indexes**:
- `idx_mv_weekly_sales_year_week` - On `(year, week)` columns
- `idx_mv_weekly_sales_retailer` - On `retailer_id` column

---

### 5. `mv_quarterly_sales_summary`

**Purpose**: High-level quarterly aggregated sales.

**Use Cases**:
- Quarterly business reviews
- Quarter-over-quarter comparisons
- High-level performance metrics

**Columns**:
- `year` - Year
- `quarter` - Quarter (1-4)
- `retailer_id` - Retailer ID
- `retailer_name` - Retailer name
- `transaction_count` - Total number of transaction line items
- `unique_transactions` - Number of distinct transactions
- `days_with_sales` - Number of days with sales in the quarter
- `unique_products` - Number of distinct products sold
- `total_quantity` - Total quantity sold
- `total_revenue` - Total revenue
- `avg_transaction_amount` - Average transaction amount

**Example Query**:
```sql
-- Get quarterly summary for all retailers
SELECT retailer_name, year, quarter, total_revenue, unique_products
FROM mv_quarterly_sales_summary
WHERE year = 2024
ORDER BY retailer_name, quarter;
```

**Indexes**:
- `idx_mv_quarterly_sales_year_quarter` - On `(year, quarter)` columns
- `idx_mv_quarterly_sales_retailer` - On `retailer_id` column

---

### 6. `mv_daily_sales_by_product`

**Purpose**: Daily aggregated sales per product.

**Use Cases**:
- Product daily performance tracking
- Product sales trends over time
- Product-level daily analysis

**Columns**:
- `date` - Sales date
- `year` - Year
- `month` - Month (1-12)
- `product_id` - Product ID
- `product_sku` - Product SKU
- `product_name` - Product name
- `category` - Product category
- `retailer_id` - Retailer ID
- `retailer_name` - Retailer name
- `transaction_count` - Total number of transaction line items
- `total_quantity_sold` - Total quantity sold
- `total_revenue` - Total revenue
- `avg_unit_price` - Average unit price

**Example Query**:
```sql
-- Get daily sales for a specific product
SELECT date, total_revenue, total_quantity_sold, avg_unit_price
FROM mv_daily_sales_by_product
WHERE product_sku = 'SKU123'
  AND retailer_name = 'Retailer 1'
  AND date >= '2024-01-01'
ORDER BY date DESC;
```

**Indexes**:
- `idx_mv_daily_sales_product_date` - On `date` column
- `idx_mv_daily_sales_product_id` - On `product_id` column
- `idx_mv_daily_sales_product_category` - On `category` column

---

## Refresh Schedule

Materialized views are automatically refreshed after each daily data pipeline run. The refresh happens as the final step in the pipeline:

1. **Ingest** data from retailers → S3
2. **Transform** S3 data → PostgreSQL star schema
3. **Data Quality** checks
4. **Refresh Materialized Views** ← This step

The refresh is orchestrated by Airflow and runs automatically after successful data quality checks.

## Manual Refresh

If you need to manually refresh the materialized views, you can:

### Option 1: Using Python Script
```bash
python materialized_views/main.py
```

### Option 2: Using PostgreSQL Stored Procedures (Recommended)
```sql
-- Refresh a single view using stored procedure
CALL refresh_materialized_view('mv_daily_sales_summary');

-- Refresh all views at once using function
SELECT refresh_all_materialized_views();

-- Or refresh individually using procedures
CALL refresh_materialized_view('mv_daily_sales_summary');
CALL refresh_materialized_view('mv_monthly_sales_by_category');
CALL refresh_materialized_view('mv_top_products_by_revenue');
CALL refresh_materialized_view('mv_weekly_sales_trends');
CALL refresh_materialized_view('mv_quarterly_sales_summary');
CALL refresh_materialized_view('mv_daily_sales_by_product');
```

### Option 2b: Using PostgreSQL Direct Commands (Alternative)
```sql
-- Refresh a single view directly
REFRESH MATERIALIZED VIEW mv_daily_sales_summary;

-- Refresh all views (run each command)
REFRESH MATERIALIZED VIEW mv_daily_sales_summary;
REFRESH MATERIALIZED VIEW mv_monthly_sales_by_category;
REFRESH MATERIALIZED VIEW mv_top_products_by_revenue;
REFRESH MATERIALIZED VIEW mv_weekly_sales_trends;
REFRESH MATERIALIZED VIEW mv_quarterly_sales_summary;
REFRESH MATERIALIZED VIEW mv_daily_sales_by_product;
```

### Option 3: Using Airflow UI
1. Navigate to the `retail_data_pipeline` DAG
2. Trigger the `refresh_materialized_views` task manually

## Performance Considerations

### Query Performance
- Materialized views are pre-aggregated, so queries are typically **10-100x faster** than querying the fact table directly
- Use materialized views for dashboards and reports that need aggregated data
- For transaction-level detail, query the `fact_sales` table directly

### Refresh Performance
- Refreshing all views typically takes **1-5 minutes** depending on data volume
- Views are refreshed sequentially (one at a time) to avoid database contention
- Refresh happens automatically after data quality checks pass

### Storage
- Materialized views require additional storage space (typically 5-20% of fact table size)
- Storage usage depends on aggregation level and number of dimensions

## BI Tool Integration

### Connection String
```
Host: <POSTGRES_HOST>
Port: 5432
Database: <POSTGRES_DB>
User: <POSTGRES_USER>
Password: <POSTGRES_PASSWORD>
```

### Recommended Views by Use Case

**Daily Dashboards**:
- `mv_daily_sales_summary` - For daily KPIs
- `mv_daily_sales_by_product` - For product-level daily metrics

**Monthly Reports**:
- `mv_monthly_sales_by_category` - For category analysis
- `mv_quarterly_sales_summary` - For high-level summaries

**Product Analysis**:
- `mv_top_products_by_revenue` - For product rankings
- `mv_daily_sales_by_product` - For product trends

**Trend Analysis**:
- `mv_weekly_sales_trends` - For weekly patterns
- `mv_monthly_sales_by_category` - For category trends

## Notes

- Materialized views are **read-only** - do not attempt to insert/update/delete
- Views are refreshed **after** data quality checks to ensure data integrity
- If a refresh fails, the pipeline will fail and you'll need to investigate
- Views contain **all historical data** (not just the latest date)
- For time-filtered queries, always include date filters for best performance

## Troubleshooting

### View Not Found Error
If you get a "relation does not exist" error:
1. Check that the database initialization script ran: `02_create_materialized_views.sql`
2. Verify the view exists: `\dm+ mv_*` in psql
3. Re-run the initialization script if needed

### Stale Data
If views contain stale data:
1. Check Airflow DAG run status
2. Verify the `refresh_materialized_views` task completed successfully
3. Manually refresh if needed (see Manual Refresh section)

### Slow Queries
If queries are still slow:
1. Verify indexes exist: `\d+ mv_*` in psql
2. Check query execution plan: `EXPLAIN ANALYZE <your_query>`
3. Ensure you're filtering on indexed columns

## Future Improvements & Enhancements

### ✅ What's Already Implemented

1. **6 Materialized Views** - Comprehensive analytical views covering:
   - Daily sales summaries
   - Monthly category performance
   - Top products by revenue
   - Weekly sales trends
   - Quarterly summaries
   - Daily sales by product

2. **Automated Refresh** - Integrated into Airflow DAG (runs after data quality checks)

3. **Indexes** - Optimized indexes on all views for fast queries

4. **Verification Tools** - Scripts to verify views are working correctly

5. **Example Queries** - Sample queries demonstrating view usage

6. **Visualization Scripts** - Python scripts to generate charts

7. **Grafana Integration** - Grafana container with pre-configured dashboards

### 🚀 Pending Improvements & Suggestions

#### 1. Grafana Enhancements (HIGH PRIORITY) ✅ PARTIALLY DONE

**Status**: Basic Grafana setup is complete. Additional enhancements needed.

**What's Done**:
- ✅ Grafana container added to docker-compose
- ✅ PostgreSQL datasource provisioning
- ✅ 3 pre-configured dashboards (Daily Sales, Product Performance, Trends)
- ✅ Dashboard auto-provisioning

**What's Pending**:
- [ ] **Alert Rules**: Create Grafana alert rules for:
  - Revenue drops below threshold
  - Missing data (no sales for expected date)
  - View refresh failures
  - Data quality issues

- [ ] **Additional Dashboards**:
  - [ ] Retailer comparison dashboard (side-by-side metrics)
  - [ ] Product category deep-dive dashboard
  - [ ] Time-series forecasting dashboard (using Grafana's prediction features)
  - [ ] Executive summary dashboard (high-level KPIs)

- [ ] **Dashboard Variables**: Add template variables for:
  - Date range selection
  - Retailer filter
  - Category filter
  - Product filter

- [ ] **Annotations**: Add annotations for:
  - View refresh times
  - Pipeline execution events
  - Data quality check results

#### 2. Materialized View Refresh Optimization (MEDIUM PRIORITY)

**Current Status**: Views refresh sequentially using `REFRESH MATERIALIZED VIEW`

**Improvements**:
- [ ] **Concurrent Refresh**: Implement `REFRESH MATERIALIZED VIEW CONCURRENTLY`
  - Requires unique indexes on each view
  - Allows queries during refresh (zero downtime)
  - Better for production environments

- [ ] **Incremental Refresh**: For large datasets, consider:
  - Only refresh views for recent date ranges
  - Partition-based refresh strategies
  - Track last refresh timestamp per view

- [ ] **Parallel Refresh**: Refresh independent views in parallel
  - Some views don't depend on others
  - Can use Airflow's `ParallelTaskGroup` or Python threading

- [ ] **Refresh Monitoring**: Add metrics for:
  - Refresh duration per view
  - Refresh success/failure rates
  - View size (row counts, disk usage)

#### 3. Additional Materialized Views (MEDIUM PRIORITY)

**Potential New Views**:
- [ ] **`mv_hourly_sales_summary`**: For intraday analysis
- [ ] **`mv_customer_lifetime_value`**: Customer analytics
- [ ] **`mv_product_seasonality`**: Seasonal patterns
- [ ] **`mv_retailer_performance_metrics`**: Retailer KPIs
- [ ] **`mv_slow_moving_products`**: Inventory insights
- [ ] **`mv_cross_category_analysis`**: Category relationships

#### 4. View Metadata & Monitoring (MEDIUM PRIORITY)

**Current Gap**: No tracking of view metadata or refresh history

**Improvements**:
- [ ] **Metadata Table**: Create `mv_refresh_log` table to track refresh history
- [ ] **View Health Checks**: Automated checks for staleness, row count anomalies, query performance
- [ ] **Grafana Metrics**: Expose refresh metrics to Grafana dashboards

#### 5. Query Performance Optimization (LOW PRIORITY)

**Improvements**:
- [ ] **Composite Indexes**: Add multi-column indexes for common query patterns
- [ ] **Partial Indexes**: For filtered queries on recent data
- [ ] **View Statistics**: Regularly run `ANALYZE` on views
- [ ] **Query Plan Analysis**: Monitor slow queries using `pg_stat_statements`

#### 6. Data Quality Integration (MEDIUM PRIORITY)

**Improvements**:
- [ ] **Quality Metrics in Views**: Add data quality indicators
- [ ] **Quality Dashboard**: Grafana dashboard showing quality scores over time
- [ ] **Conditional Refresh**: Only refresh views if data quality passes

#### 7. Security & Access Control (MEDIUM PRIORITY)

**Improvements**:
- [ ] **View-Level Permissions**: Create read-only users for analytics
- [ ] **Grafana User Management**: Configure role-based access control
- [ ] **Audit Logging**: Track who accessed which views

### 📊 Priority Summary

#### High Priority (Do Next)
1. ✅ **Grafana Setup** - DONE
2. **Grafana Alerts** - Set up alerting for critical metrics
3. **Dashboard Variables** - Make dashboards more interactive
4. **Concurrent Refresh** - Implement zero-downtime refreshes

#### Medium Priority (Production Readiness)
5. **Metadata Tracking** - Track refresh history and view health
6. **Additional Dashboards** - More comprehensive visualizations
7. **Data Quality Integration** - Better integration with quality checks
8. **Security Enhancements** - Access control and permissions

#### Low Priority (Nice to Have)
9. **Additional Views** - New analytical views
10. **Performance Optimization** - Advanced indexing strategies
11. **Advanced Analytics** - Predictive features

### 🎯 Recommended Implementation Order

1. **Week 1**: Grafana alerts + Dashboard variables
2. **Week 2**: Concurrent refresh implementation
3. **Week 3**: Metadata tracking + Health checks
4. **Week 4**: Additional dashboards + Security setup
5. **Ongoing**: New views as business needs arise

### 📝 Notes

- All improvements should maintain backward compatibility
- Test changes in development before production
- Document all new features
- Consider performance impact of new views
- Monitor resource usage (CPU, memory, disk) as views grow

