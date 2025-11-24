# Materialized Views Tools

This directory contains tools to verify, query, and visualize the materialized views in your retail data pipeline.

## Quick Start

### Running the Scripts

**Option 1: Run in Docker Container (Recommended - has all dependencies)**

```bash
# Verify views
docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/verify_views.py

# Example queries
docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/example_queries.py

# Visualize
docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/visualize_views.py
```

**Option 2: Run Locally (requires dependencies)**

First install dependencies:
```bash
pip install -r requirements.txt
```

Then run:
```bash
python materialized_views/verify_views.py
python materialized_views/example_queries.py
python materialized_views/visualize_views.py
```

### 1. Verify Views Are Working

Check if all materialized views exist, have data, and are queryable:

```bash
# In Docker
docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/verify_views.py

# Or locally (after installing dependencies)
python materialized_views/verify_views.py
```

This will:
- ✅ Check if all 6 views exist
- ✅ Verify they contain data
- ✅ Test that queries work
- ✅ Check indexes are in place
- ✅ Display a summary report

**Example Output:**
```
📊 Verifying: mv_daily_sales_summary
   ✅ View exists
   ✅ Has data: 1,234 rows
   ✅ Structure: 13 columns
   ✅ Indexes: 3 found
   ✅ Queryable: Sample query successful
```

### 2. See What You Can Do With Views

Run example queries to see the analytical capabilities:

```bash
# In Docker
docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/example_queries.py

# Or locally
python materialized_views/example_queries.py
```

This interactive script shows 8 different use cases:
1. **Daily Sales Dashboard** - Last 7 days of sales
2. **Top Products** - Top 10 products by revenue
3. **Category Performance** - Monthly category analysis
4. **Weekly Trends** - Weekly sales patterns
5. **Quarterly Summary** - High-level quarterly metrics
6. **Product Daily Trends** - Daily performance for top products
7. **Retailer Comparison** - Compare retailer performance
8. **Category Growth** - Quarter-over-quarter category analysis

### 3. Visualize the Data

Generate charts and graphs:

```bash
# In Docker (first install matplotlib if not already installed)
docker-compose exec airflow-scheduler pip install matplotlib
docker-compose exec airflow-scheduler python /opt/airflow/materialized_views/visualize_views.py

# Or locally
python materialized_views/visualize_views.py
```

**Note**: If you get permission errors in Docker, charts will be saved to `/tmp/materialized_views_charts` in the container. You can copy them out with:
```bash
docker cp retail_airflow_scheduler:/tmp/materialized_views_charts ./materialized_views/charts
```

This creates 5 visualizations saved to `materialized_views/charts/`:
- `daily_sales_trend.png` - Daily revenue trends over time
- `top_products.png` - Top 10 products bar chart
- `category_performance.png` - Category performance by retailer
- `weekly_trends.png` - Weekly sales trends
- `retailer_comparison.png` - Side-by-side retailer comparison

## Available Materialized Views

1. **mv_daily_sales_summary** - Daily aggregated sales per retailer
2. **mv_monthly_sales_by_category** - Monthly sales by product category
3. **mv_top_products_by_revenue** - Top products ranked by revenue
4. **mv_weekly_sales_trends** - Weekly aggregated sales
5. **mv_quarterly_sales_summary** - Quarterly high-level summaries
6. **mv_daily_sales_by_product** - Daily sales per product

See `docs/MATERIALIZED_VIEWS.md` for detailed documentation.

## Common Use Cases

### Check if views need refreshing

```bash
python materialized_views/verify_views.py
```

If views show 0 rows, refresh them:

```bash
python materialized_views/main.py
```

### Query views directly in PostgreSQL

```bash
# Connect to database
docker exec -it retail_postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>

# Example query
SELECT * FROM mv_daily_sales_summary 
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC;
```

### Export data to CSV

```python
import pandas as pd
from sqlalchemy import text
from shared.database import get_postgres_engine

engine = get_postgres_engine()
query = "SELECT * FROM mv_daily_sales_summary WHERE date >= '2024-01-01'"
df = pd.read_sql(query, engine)
df.to_csv('sales_data.csv', index=False)
```

## Troubleshooting

### Views don't exist
- Check database initialization: `database/init/02_create_materialized_views.sql` should have run
- Verify in PostgreSQL: `\dm+ mv_*` in psql

### Views have no data
- Refresh the views: `python materialized_views/main.py`
- Check if fact_sales table has data
- Verify the pipeline ran successfully

### Queries are slow
- Ensure indexes exist (verify_views.py checks this)
- Use date filters in your queries
- Check query execution plan: `EXPLAIN ANALYZE <your_query>`

### Visualization errors
- **matplotlib not installed in Docker**: 
  ```bash
  docker-compose exec airflow-scheduler pip install matplotlib
  ```
- **Permission denied errors**: Charts will automatically be saved to `/tmp` in the container. Copy them out with:
  ```bash
  docker cp retail_airflow_scheduler:/tmp/materialized_views_charts ./materialized_views/charts
  ```
- Check database connection
- Ensure views have data

## Integration with BI Tools

### Metabase / Tableau / Power BI

Connect using PostgreSQL connection:
- Host: `localhost` (or your PostgreSQL host)
- Port: `5432` (or your POSTGRES_PORT)
- Database: `<POSTGRES_DB>`
- User: `<POSTGRES_USER>`
- Password: `<POSTGRES_PASSWORD>`

Recommended views for dashboards:
- **Daily KPIs**: `mv_daily_sales_summary`
- **Product Analysis**: `mv_top_products_by_revenue`
- **Category Trends**: `mv_monthly_sales_by_category`
- **Weekly Patterns**: `mv_weekly_sales_trends`

## Next Steps

1. **Verify views are working**: Run `verify_views.py`
2. **Explore example queries**: Run `example_queries.py`
3. **Generate visualizations**: Run `visualize_views.py`
4. **Connect BI tool**: Use the connection details above
5. **Create custom dashboards**: Build on the example queries

For more details, see `docs/MATERIALIZED_VIEWS.md`.

