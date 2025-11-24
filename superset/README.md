# Apache Superset Configuration

This directory contains configuration files for Apache Superset, a modern, open-source business intelligence tool.

## Directory Structure

```
superset/
├── config/
│   └── superset_config.py    # Superset configuration file
├── datasources/
│   └── postgres_datasource.yaml  # Documentation for PostgreSQL datasource
└── README.md                 # This file
```

## Configuration

### Superset Config (`config/superset_config.py`)

The main configuration file for Superset. It includes:
- Database connection settings
- Feature flags
- Security settings
- Performance tuning

### Datasource Configuration

Superset doesn't support automatic datasource provisioning like Grafana. You need to add datasources manually through the UI or API.

## Accessing Superset

1. **Start the services:**
   ```bash
   docker-compose up -d
   ```

2. **Access Superset UI:**
   - URL: `http://localhost:8088`
   - Default credentials:
     - Username: `admin`
     - Password: `admin`

3. **Change default credentials:**
   Update these in your `.env` file:
   ```bash
   SUPERSET_ADMIN_USER=your_username
   SUPERSET_ADMIN_PASSWORD=your_password
   ```

## Adding PostgreSQL Datasource

After logging into Superset:

1. Go to **Data** → **Databases** → **+ Database**
2. Fill in the connection details:
   - **Database Name**: Retail Analytics
   - **SQLAlchemy URI**: 
     ```
     postgresql://superset_user:superset_password_123@postgres:5432/retail_analytics
     ```
   - **Display Name**: Retail Analytics PostgreSQL
3. Click **Test Connection** to verify
4. Click **Connect**

## Available Tables and Views

Once connected, you can explore:

### Fact Tables
- `fact_sales` - Main sales fact table

### Dimension Tables
- `dim_date` - Date dimension with time attributes
- `dim_product` - Product dimension (SKU, name, category)
- `dim_customer` - Customer dimension
- `dim_store` - Store dimension
- `dim_retailer` - Retailer dimension

### Materialized Views
- `mv_daily_sales_summary` - Daily aggregated sales by retailer
- `mv_monthly_sales_by_category` - Monthly sales by product category

## Creating Your First Dashboard

1. **Create a Chart:**
   - Go to **Charts** → **+ Chart**
   - Select your datasource
   - Choose a visualization type
   - Build your query

2. **Create a Dashboard:**
   - Go to **Dashboards** → **+ Dashboard**
   - Add charts to your dashboard
   - Save and share

## Example Queries

### Daily Sales by Retailer
```sql
SELECT 
    d.date,
    r.retailer_name,
    SUM(fs.total_amount) as total_revenue,
    COUNT(*) as transaction_count
FROM fact_sales fs
JOIN dim_date d ON fs.date_id = d.date_id
JOIN dim_retailer r ON fs.retailer_id = r.retailer_id
GROUP BY d.date, r.retailer_name
ORDER BY d.date DESC;
```

### Top Products by Revenue
```sql
SELECT 
    p.product_name,
    p.category,
    SUM(fs.total_amount) as total_revenue,
    SUM(fs.quantity) as total_quantity
FROM fact_sales fs
JOIN dim_product p ON fs.product_id = p.product_id
GROUP BY p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 20;
```

### Monthly Sales Trend
```sql
SELECT 
    d.year,
    d.month,
    SUM(fs.total_amount) as monthly_revenue
FROM fact_sales fs
JOIN dim_date d ON fs.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
```

## Troubleshooting

### Superset won't start
- Check logs: `docker-compose logs superset`
- Ensure PostgreSQL is running: `docker-compose ps postgres`
- Verify database user exists (created in database init scripts)

### Can't connect to PostgreSQL
- Verify connection string format
- Check that `superset_user` has proper permissions
- Test connection from Superset container: 
  ```bash
  docker-compose exec superset psql -h postgres -U superset_user -d retail_analytics
  ```

### Forgot admin password
- Reset via command:
  ```bash
  docker-compose exec superset superset fab reset-password \
    --username admin \
    --password new_password
  ```

## Port Configuration

Default port: `8088`

To change the port, update in `.env`:
```bash
SUPERSET_PORT=8088
```

## Security Notes

- Change default admin credentials in production
- Update `SUPERSET_SECRET_KEY` in `.env` for production
- Consider enabling authentication providers (LDAP, OAuth, etc.)
- Review and restrict database user permissions

## Additional Resources

- [Superset Documentation](https://superset.apache.org/docs/)
- [Superset SQL Lab Guide](https://superset.apache.org/docs/intro)
- [Creating Dashboards](https://superset.apache.org/docs/creating-charts-dashboards/creating-dashboards)

