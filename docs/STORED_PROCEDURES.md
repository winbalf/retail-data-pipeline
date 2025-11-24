# Stored Procedures Guide

This document describes the stored procedures and functions available in the retail analytics data warehouse. These procedures provide convenient ways to perform common analytics queries, data quality checks, and materialized view management.

## Table of Contents

1. [Overview](#overview)
2. [Materialized View Procedures](#materialized-view-procedures)
3. [Analytics Procedures](#analytics-procedures)
4. [Data Quality Procedures](#data-quality-procedures)
5. [Utility Procedures](#utility-procedures)
6. [Usage Examples](#usage-examples)
7. [Permissions](#permissions)

## Overview

The stored procedures are automatically created during database initialization (file: `database/init/04_create_stored_procedures.sql`). They are designed to:

- **Simplify common queries**: Encapsulate complex SQL logic into reusable procedures
- **Improve security**: Use `SECURITY DEFINER` where appropriate to allow users to perform operations they wouldn't normally have permission for
- **Enhance maintainability**: Centralize business logic in the database
- **Support BI tools**: Provide functions that can be easily called from Grafana, Tableau, or other BI tools

## Materialized View Procedures

### `refresh_materialized_view(view_name TEXT)`

Refreshes a specific materialized view by name.

**Parameters:**
- `view_name`: Name of the materialized view to refresh (e.g., 'mv_daily_sales_summary')

**Usage:**
```sql
CALL refresh_materialized_view('mv_daily_sales_summary');
```

**Available Views:**
- `mv_daily_sales_summary`
- `mv_monthly_sales_by_category`
- `mv_top_products_by_revenue`
- `mv_weekly_sales_trends`
- `mv_quarterly_sales_summary`
- `mv_daily_sales_by_product`

**Note:** This procedure attempts to use `REFRESH MATERIALIZED VIEW CONCURRENTLY` first, and falls back to regular refresh if concurrent refresh is not possible (e.g., missing unique index).

**Permissions:** Requires `EXECUTE` permission. Granted to `airflow_user`.

---

### `refresh_all_materialized_views()`

Refreshes all materialized views at once. This function is defined in `03_grant_materialized_view_permissions.sh` and is included here for reference.

**Usage:**
```sql
SELECT refresh_all_materialized_views();
```

**Permissions:** Granted to `airflow_user`.

## Analytics Procedures

### `get_sales_summary(start_date DATE, end_date DATE, retailer_id_param INTEGER DEFAULT NULL)`

Returns aggregated sales metrics for a specific date range.

**Parameters:**
- `start_date`: Start date of the period
- `end_date`: End date of the period
- `retailer_id_param`: Optional retailer ID filter (NULL for all retailers)

**Usage:**
```sql
CALL get_sales_summary('2024-01-01', '2024-01-31', NULL);
CALL get_sales_summary('2024-01-01', '2024-01-31', 1);  -- For specific retailer
```

**Output:** Prints summary statistics including:
- Total transactions
- Total revenue
- Total quantity
- Unique products, customers, stores
- Min/max transaction amounts

---

### `get_top_products_by_revenue(start_date DATE, end_date DATE, top_n INTEGER DEFAULT 10, retailer_id_param INTEGER DEFAULT NULL)`

Returns a table with the top N products by revenue for a date range.

**Parameters:**
- `start_date`: Start date of the period
- `end_date`: End date of the period
- `top_n`: Number of top products to return (default: 10)
- `retailer_id_param`: Optional retailer ID filter (NULL for all retailers)

**Returns:** Table with columns:
- `product_id`, `product_sku`, `product_name`, `category`
- `total_revenue`, `total_quantity_sold`, `transaction_count`, `avg_unit_price`

**Usage:**
```sql
-- Get top 10 products for January 2024
SELECT * FROM get_top_products_by_revenue('2024-01-01', '2024-01-31', 10, NULL);

-- Get top 5 products for a specific retailer
SELECT * FROM get_top_products_by_revenue('2024-01-01', '2024-01-31', 5, 1);
```

---

### `get_sales_trends(start_date DATE, end_date DATE, period_type TEXT DEFAULT 'daily', retailer_id_param INTEGER DEFAULT NULL)`

Returns sales trends aggregated by period (daily, weekly, monthly, or quarterly).

**Parameters:**
- `start_date`: Start date of the period
- `end_date`: End date of the period
- `period_type`: One of 'daily', 'weekly', 'monthly', 'quarterly' (default: 'daily')
- `retailer_id_param`: Optional retailer ID filter (NULL for all retailers)

**Returns:** Table with columns:
- `period_label`: Formatted period label (e.g., '2024-01', '2024-Q1')
- `period_start`, `period_end`: Date range for the period
- `total_revenue`, `total_quantity`, `transaction_count`, `avg_transaction_amount`

**Usage:**
```sql
-- Daily trends for January 2024
SELECT * FROM get_sales_trends('2024-01-01', '2024-01-31', 'daily', NULL);

-- Monthly trends for Q1 2024
SELECT * FROM get_sales_trends('2024-01-01', '2024-03-31', 'monthly', NULL);

-- Weekly trends for a specific retailer
SELECT * FROM get_sales_trends('2024-01-01', '2024-01-31', 'weekly', 1);
```

---

### `get_sales_by_category(start_date DATE, end_date DATE, retailer_id_param INTEGER DEFAULT NULL)`

Returns sales aggregated by product category.

**Parameters:**
- `start_date`: Start date of the period
- `end_date`: End date of the period
- `retailer_id_param`: Optional retailer ID filter (NULL for all retailers)

**Returns:** Table with columns:
- `category`: Product category name
- `total_revenue`, `total_quantity`, `transaction_count`, `unique_products`
- `avg_unit_price`, `revenue_percentage`: Percentage of total revenue

**Usage:**
```sql
SELECT * FROM get_sales_by_category('2024-01-01', '2024-01-31', NULL);
```

---

### `get_retailer_performance(start_date DATE, end_date DATE)`

Compares performance across all retailers for a date range.

**Parameters:**
- `start_date`: Start date of the period
- `end_date`: End date of the period

**Returns:** Table with columns:
- `retailer_id`, `retailer_name`
- `total_revenue`, `total_quantity`, `transaction_count`
- `unique_products`, `unique_customers`
- `avg_transaction_amount`, `revenue_percentage`: Market share percentage

**Usage:**
```sql
SELECT * FROM get_retailer_performance('2024-01-01', '2024-01-31');
```

---

### `get_recent_sales(days_back INTEGER DEFAULT 7, retailer_id_param INTEGER DEFAULT NULL)`

Returns sales data for the last N days.

**Parameters:**
- `days_back`: Number of days to look back (default: 7)
- `retailer_id_param`: Optional retailer ID filter (NULL for all retailers)

**Returns:** Table with columns:
- `date`, `total_revenue`, `total_quantity`, `transaction_count`, `avg_transaction_amount`

**Usage:**
```sql
-- Last 7 days
SELECT * FROM get_recent_sales(7, NULL);

-- Last 30 days for a specific retailer
SELECT * FROM get_recent_sales(30, 1);
```

## Data Quality Procedures

### `check_data_quality(start_date DATE, end_date DATE)`

Performs data quality checks and prints a report.

**Parameters:**
- `start_date`: Start date of the period to check
- `end_date`: End date of the period to check

**Usage:**
```sql
CALL check_data_quality('2024-01-01', '2024-01-31');
```

**Output:** Prints metrics including:
- Total records
- Records with customer/store information (completeness)
- Unique transactions
- Potential duplicates
- Data quality issues (null amounts, negative amounts, zero quantities)

---

### `get_data_quality_summary(start_date DATE, end_date DATE)`

Returns data quality metrics as a table (useful for BI tools).

**Parameters:**
- `start_date`: Start date of the period to check
- `end_date`: End date of the period to check

**Returns:** Table with columns:
- `metric_name`: Name of the quality metric
- `metric_value`: Count or value
- `metric_percentage`: Percentage when applicable

**Usage:**
```sql
SELECT * FROM get_data_quality_summary('2024-01-01', '2024-01-31');
```

**Example Output:**
```
metric_name              | metric_value | metric_percentage
------------------------|--------------|------------------
total_records           | 15000        | NULL
records_with_customer   | 12000        | 80.00
records_with_store      | 14000        | 93.33
unique_transactions     | 5000         | NULL
null_or_zero_amounts    | 0            | 0.00
negative_amounts        | 0            | 0.00
zero_quantities         | 0            | 0.00
```

## Utility Procedures

### `get_database_statistics()`

Provides an overview of data in the warehouse.

**Usage:**
```sql
CALL get_database_statistics();
```

**Output:** Prints:
- Total sales records
- Date range (min/max dates)
- Total revenue
- Counts of products, customers, stores, retailers

## Usage Examples

### Example 1: Daily Sales Dashboard Query

```sql
-- Get last 30 days of daily sales trends
SELECT * FROM get_sales_trends(
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE,
    'daily',
    NULL
);
```

### Example 2: Top Products Report

```sql
-- Get top 20 products for the current month
SELECT 
    product_name,
    category,
    total_revenue,
    total_quantity_sold,
    transaction_count
FROM get_top_products_by_revenue(
    DATE_TRUNC('month', CURRENT_DATE),
    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day',
    20,
    NULL
)
ORDER BY total_revenue DESC;
```

### Example 3: Category Performance Analysis

```sql
-- Compare category performance for Q1 2024
SELECT 
    category,
    total_revenue,
    revenue_percentage,
    unique_products
FROM get_sales_by_category('2024-01-01', '2024-03-31', NULL)
ORDER BY total_revenue DESC;
```

### Example 4: Retailer Comparison

```sql
-- Compare all retailers for the last quarter
SELECT 
    retailer_name,
    total_revenue,
    revenue_percentage as market_share,
    avg_transaction_amount,
    unique_customers
FROM get_retailer_performance(
    DATE_TRUNC('quarter', CURRENT_DATE) - INTERVAL '3 months',
    DATE_TRUNC('quarter', CURRENT_DATE) - INTERVAL '1 day'
)
ORDER BY total_revenue DESC;
```

### Example 5: Data Quality Check

```sql
-- Check data quality for the last week
CALL check_data_quality(
    CURRENT_DATE - INTERVAL '7 days',
    CURRENT_DATE
);

-- Or get as a table for reporting
SELECT * FROM get_data_quality_summary(
    CURRENT_DATE - INTERVAL '7 days',
    CURRENT_DATE
);
```

### Example 6: Using in Python (SQLAlchemy)

```python
from sqlalchemy import text
from shared.database import get_postgres_engine

engine = get_postgres_engine()

# Call a procedure
with engine.begin() as conn:
    conn.execute(text("CALL get_sales_summary('2024-01-01', '2024-01-31', NULL)"))

# Use a function that returns a table
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT * FROM get_top_products_by_revenue('2024-01-01', '2024-01-31', 10, NULL)
    """))
    for row in result:
        print(row)
```

### Example 7: Using in Grafana

In Grafana, you can use these functions directly in SQL queries:

```sql
-- Panel: Daily Sales Trend
SELECT 
    period_label as time,
    total_revenue as value
FROM get_sales_trends(
    $__timeFrom()::date,
    $__timeTo()::date,
    'daily',
    $retailer_id
)
ORDER BY period_start;
```

```sql
-- Panel: Top Products
SELECT 
    product_name,
    total_revenue
FROM get_top_products_by_revenue(
    $__timeFrom()::date,
    $__timeTo()::date,
    10,
    $retailer_id
)
ORDER BY total_revenue DESC;
```

## Permissions

The stored procedures have been granted appropriate permissions to different database users:

### `airflow_user`
- `refresh_materialized_view()` - For refreshing materialized views
- `refresh_all_materialized_views()` - For batch refresh operations

### `data_quality_user`
- `check_data_quality()` - For data quality checks
- `get_data_quality_summary()` - For quality reporting

### `grafana_user`
- All analytics functions (read-only)
- `get_database_statistics()` - For monitoring

### `transformation_user`
- `get_database_statistics()` - For monitoring
- `get_data_quality_summary()` - For validation

### `PUBLIC` (All Users)
- Read-only analytics functions:
  - `get_top_products_by_revenue()`
  - `get_sales_trends()`
  - `get_sales_by_category()`
  - `get_retailer_performance()`
  - `get_recent_sales()`

## Troubleshooting

### Procedure Not Found

If you get an error that a procedure doesn't exist, verify it was created:

```sql
-- List all procedures
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
ORDER BY routine_name;
```

### Permission Denied

If you get a permission error, check your user's permissions:

```sql
-- Check your current user
SELECT current_user;

-- Check if you have execute permission
SELECT has_function_privilege('current_user', 'get_top_products_by_revenue(date, date, integer, integer)', 'EXECUTE');
```

### Refresh Materialized View Fails

If `refresh_materialized_view()` fails with a concurrent refresh error, it will automatically fall back to a regular refresh. If both fail, check:

1. The view exists: `\dm+ mv_*`
2. You have the necessary permissions
3. The view name is spelled correctly

## Best Practices

1. **Use functions for queries**: Functions that return tables are easier to use in BI tools and can be composed with other SQL
2. **Use procedures for operations**: Procedures are better for operations that don't return data (like refresh operations)
3. **Filter by date range**: Always specify appropriate date ranges to avoid querying all historical data
4. **Use retailer filters**: When analyzing specific retailers, use the `retailer_id_param` parameter for better performance
5. **Monitor data quality**: Regularly run data quality checks, especially after data loads

## Integration & Implementation

### Implementation Status

Stored procedures are fully integrated and actively used throughout the pipeline:

1. ✅ **Grafana Dashboards** - Updated to use stored procedure functions
2. ✅ **Materialized View Refresh** - Uses stored procedures for individual view refreshes
3. ✅ **Python Examples** - Example scripts demonstrating stored procedure usage
4. ✅ **Documentation** - Comprehensive guides available

### Pipeline Integration

The materialized view refresh mechanism uses stored procedures:

1. ✅ **Batch Refresh** - Uses `refresh_all_materialized_views()` function
2. ✅ **Individual Refresh** - Uses `refresh_materialized_view()` procedure
3. ✅ **Fallback Logic** - Gracefully falls back to direct refresh if procedures unavailable

### Current Pipeline Flow

The pipeline follows this complete flow:

```
1. Data Ingestion ✅
   ↓
2. Data Transformation (loads into fact_sales) ✅
   ↓
3. Data Quality Check ✅
   ↓
4. Refresh Materialized Views (via stored procedure) ✅
   ↓
5. BI Tools query materialized views ✅
   ↓
6. Stored procedures provide convenient access patterns ✅
```

### Integration Examples

#### Grafana Integration

Grafana dashboards have been updated to use stored procedure functions:

```sql
-- Top products with date range
SELECT * FROM get_top_products_by_revenue($__timeFrom()::date, $__timeTo()::date, 10, NULL);

-- Sales trends
SELECT * FROM get_sales_trends($__timeFrom()::date, $__timeTo()::date, 'monthly', NULL);

-- Retailer performance
SELECT * FROM get_retailer_performance($__timeFrom()::date, $__timeTo()::date);
```

#### Materialized View Refresh

The refresh service (`materialized_views/refresh_views.py`) uses stored procedures:

**Flow:**
```
1. Try: CALL refresh_materialized_view('view_name')
2. If fails: REFRESH MATERIALIZED VIEW CONCURRENTLY view_name
3. If fails: REFRESH MATERIALIZED VIEW view_name
```

### Benefits Achieved

1. **Maintainability** - Business logic centralized in database
2. **Performance** - Query plans cached and reused
3. **Security** - Controlled access via stored procedures
4. **Consistency** - Same logic used across all tools
5. **Usability** - Simple function calls instead of complex SQL

### Next Steps (Optional Enhancements)

1. **Add More Stored Procedures**
   - Customer analytics procedures
   - Forecasting procedures
   - Anomaly detection procedures

2. **Performance Monitoring**
   - Track stored procedure execution times
   - Monitor usage patterns
   - Optimize based on usage

3. **Enhanced Error Handling**
   - Better error messages
   - Retry logic for transient failures
   - Alerting on procedure failures

## Related Documentation

- [Materialized Views Guide](MATERIALIZED_VIEWS.md)
- [Architecture Overview](ARCHITECTURE.md)

