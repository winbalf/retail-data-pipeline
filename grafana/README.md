# Grafana Setup for Retail Analytics

This directory contains Grafana configuration for visualizing materialized views from the retail analytics data warehouse.

## Quick Start

1. **Start Grafana** (with docker-compose):
   ```bash
   docker-compose up -d grafana
   ```

2. **Access Grafana**:
   - URL: http://localhost:3000
   - Default username: `admin`
   - Default password: `admin` (change on first login)

3. **Configure PostgreSQL Datasource**:
   
   **Option A: Use setup script (recommended)**:
   ```bash
   ./grafana/setup_datasource.sh
   docker-compose restart grafana
   ```
   
   **Option B: Manual update**:
   - The datasource is auto-provisioned, but you may need to update credentials
   - Go to Configuration → Data Sources → Retail Analytics PostgreSQL
   - Update database, user, and password to match your `.env` file values
   - Click "Save & Test" to verify connection

4. **View Dashboards**:
   - Pre-configured dashboards are available in the "Retail Analytics" folder
   - Navigate to Dashboards → Browse → Retail Analytics

## Available Dashboards

### 1. Daily Sales Dashboard
- Daily revenue trends (last 30 days)
- Transaction counts
- Retailer comparisons
- Today's revenue breakdown

### 2. Product Performance Dashboard
- Top 10 products by revenue
- Top products by quantity sold
- Monthly sales by category

### 3. Sales Trends & Analytics
- Weekly sales trends
- Quarterly summaries
- Monthly category performance heatmap

## Customization

### Adding New Dashboards

1. Create a JSON file in `grafana/dashboards/`
2. Use Grafana UI to create/edit dashboards
3. Export dashboard JSON and save to this directory
4. Dashboards are auto-provisioned on Grafana startup

### Updating Datasource

The datasource configuration is in `grafana/provisioning/datasources/postgres.yml`. 

**Important**: Grafana provisioning files don't support environment variable substitution directly. You have two options:

1. **Manual Update**: After Grafana starts, update the datasource in the UI with your actual credentials
2. **Script Update**: Use a script to generate the datasource config from environment variables

Example script to update datasource:
```bash
#!/bin/bash
source .env
sed -i "s/database:.*/database: ${POSTGRES_DB}/" grafana/provisioning/datasources/postgres.yml
sed -i "s/user:.*/user: ${POSTGRES_USER}/" grafana/provisioning/datasources/postgres.yml
# Password is in secureJsonData, update manually or use envsubst
```

## Environment Variables

Add these to your `.env` file (optional, defaults shown):
```bash
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

## Troubleshooting

**Grafana can't connect to PostgreSQL?**
- Check that PostgreSQL container is running: `docker ps | grep postgres`
- Verify network connectivity: `docker network inspect retail_retail_network`
- Update datasource credentials in Grafana UI to match your `.env` values

**Dashboards not showing?**
- Check Grafana logs: `docker logs retail_grafana`
- Verify dashboard files are in `grafana/dashboards/`
- Check provisioning config: `grafana/provisioning/dashboards/dashboards.yml`

**Permission errors?**
- Ensure Grafana has read access to dashboard files
- Check file permissions: `ls -la grafana/dashboards/`

## Query Examples

You can create custom panels using these materialized views:

```sql
-- Daily sales summary
SELECT date, retailer_name, total_revenue 
FROM mv_daily_sales_summary 
WHERE date >= CURRENT_DATE - INTERVAL '7 days';

-- Top products
SELECT product_name, total_revenue 
FROM mv_top_products_by_revenue 
ORDER BY total_revenue DESC 
LIMIT 10;

-- Category performance
SELECT category, SUM(total_revenue) as revenue 
FROM mv_monthly_sales_by_category 
WHERE year = EXTRACT(YEAR FROM NOW()) 
GROUP BY category;
```

## Integration Summary

### ✅ What's Been Added

1. **Grafana Service**
   - Added Grafana container to `docker-compose.yml`
   - Configured with PostgreSQL datasource
   - Pre-configured dashboards for materialized views
   - Auto-provisioning of datasources and dashboards

2. **Pre-configured Dashboards**
   Three ready-to-use dashboards:
   - **Daily Sales Dashboard**: Revenue trends, transaction counts, retailer comparisons
   - **Product Performance Dashboard**: Top products, category performance
   - **Sales Trends & Analytics**: Weekly trends, quarterly summaries, heatmaps

3. **Configuration Files**
   - `grafana/provisioning/datasources/postgres.yml` - PostgreSQL datasource config
   - `grafana/provisioning/dashboards/dashboards.yml` - Dashboard provisioning config
   - `grafana/dashboards/*.json` - Dashboard definitions

4. **Helper Scripts**
   - `grafana/setup_datasource.sh` - Script to update datasource with environment variables

### 🚀 Quick Start

1. **Start Grafana**:
   ```bash
   docker-compose up -d grafana
   ```

2. **Configure datasource** (if your .env values differ from defaults):
   ```bash
   ./grafana/setup_datasource.sh
   docker-compose restart grafana
   ```

3. **Access Grafana**:
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin` (change on first login)

4. **View Dashboards**:
   - Navigate to: Dashboards → Browse → Retail Analytics

### 📊 Available Dashboards

#### Daily Sales Dashboard
- Daily revenue trends (last 30 days)
- Transaction counts over time
- Retailer revenue comparison (last 7 days)
- Today's revenue breakdown by retailer

#### Product Performance Dashboard
- Top 10 products by revenue
- Top products by quantity sold
- Monthly sales by category (time series)

#### Sales Trends & Analytics
- Weekly sales trends
- Quarterly summary table
- Monthly category performance heatmap

### 📝 Next Steps

#### Immediate Improvements (High Priority)
1. **Set up alerts** for revenue thresholds and data quality issues
2. **Add dashboard variables** for date range, retailer, and category filters
3. **Configure concurrent refresh** for zero-downtime view updates

#### Medium Priority
4. Create additional dashboards (retailer comparison, executive summary)
5. Implement metadata tracking for view refresh history
6. Add data quality integration to dashboards

For comprehensive improvement suggestions, see:
- `docs/MATERIALIZED_VIEWS.md` (Future Improvements section)

### 🐛 Troubleshooting

**Grafana won't start?**
- Check logs: `docker logs retail_grafana`
- Verify port 3000 is not in use
- Check docker-compose syntax

**Can't connect to PostgreSQL?**
- Verify PostgreSQL is running: `docker ps | grep postgres`
- Check network: `docker network inspect retail_retail_network`
- Update datasource credentials in Grafana UI

**Dashboards not showing?**
- Check dashboard files exist: `ls grafana/dashboards/`
- Check Grafana logs for provisioning errors
- Verify provisioning config: `cat grafana/provisioning/dashboards/dashboards.yml`

### 📚 Related Documentation

- `docs/MATERIALIZED_VIEWS.md` - Complete materialized views documentation
- `docs/STORED_PROCEDURES.md` - Stored procedures guide (used in dashboards)
- `docs/ARCHITECTURE.md` - System architecture

## Next Steps

- Create alerts for revenue thresholds
- Add more dashboards for specific use cases
- Set up scheduled reports
- Configure user authentication (LDAP, OAuth, etc.)

