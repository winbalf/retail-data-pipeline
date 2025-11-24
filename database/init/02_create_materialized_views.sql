-- Materialized Views for Retail Analytics
-- These views pre-aggregate common analytical queries for improved performance
-- Refresh these views after data transformation completes

-- 1. Daily Sales Summary by Retailer
-- Provides daily aggregated sales metrics per retailer
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_sales_summary AS
SELECT 
    d.date,
    d.year,
    d.month,
    d.quarter,
    r.retailer_id,
    r.retailer_name,
    COUNT(*) as transaction_count,
    COUNT(DISTINCT fs.transaction_id) as unique_transactions,
    SUM(fs.quantity) as total_quantity,
    SUM(fs.total_amount) as total_revenue,
    AVG(fs.unit_price) as avg_unit_price,
    MIN(fs.total_amount) as min_transaction_amount,
    MAX(fs.total_amount) as max_transaction_amount
FROM fact_sales fs
JOIN dim_date d ON fs.date_id = d.date_id
JOIN dim_retailer r ON fs.retailer_id = r.retailer_id
GROUP BY d.date, d.year, d.month, d.quarter, r.retailer_id, r.retailer_name;

-- Create index on date and retailer for fast lookups
CREATE INDEX IF NOT EXISTS idx_mv_daily_sales_summary_date ON mv_daily_sales_summary(date);
CREATE INDEX IF NOT EXISTS idx_mv_daily_sales_summary_retailer ON mv_daily_sales_summary(retailer_id);
CREATE INDEX IF NOT EXISTS idx_mv_daily_sales_summary_year_month ON mv_daily_sales_summary(year, month);

-- 2. Monthly Sales by Product Category
-- Aggregates sales by month and product category
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_sales_by_category AS
SELECT 
    d.year,
    d.month,
    d.quarter,
    p.category,
    r.retailer_id,
    r.retailer_name,
    COUNT(*) as transaction_count,
    COUNT(DISTINCT fs.transaction_id) as unique_transactions,
    COUNT(DISTINCT p.product_id) as unique_products,
    SUM(fs.quantity) as total_quantity,
    SUM(fs.total_amount) as total_revenue,
    AVG(fs.unit_price) as avg_unit_price
FROM fact_sales fs
JOIN dim_date d ON fs.date_id = d.date_id
JOIN dim_product p ON fs.product_id = p.product_id
JOIN dim_retailer r ON fs.retailer_id = r.retailer_id
WHERE p.category IS NOT NULL
GROUP BY d.year, d.month, d.quarter, p.category, r.retailer_id, r.retailer_name;

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_mv_monthly_sales_category_year_month ON mv_monthly_sales_by_category(year, month, category);
CREATE INDEX IF NOT EXISTS idx_mv_monthly_sales_category_retailer ON mv_monthly_sales_by_category(retailer_id);

-- 3. Top Products by Revenue
-- Shows top products ranked by total revenue (all-time or recent period)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_products_by_revenue AS
SELECT 
    p.product_id,
    p.product_sku,
    p.product_name,
    p.category,
    r.retailer_id,
    r.retailer_name,
    COUNT(*) as transaction_count,
    COUNT(DISTINCT fs.transaction_id) as unique_transactions,
    SUM(fs.quantity) as total_quantity_sold,
    SUM(fs.total_amount) as total_revenue,
    AVG(fs.unit_price) as avg_unit_price,
    MIN(fs.unit_price) as min_unit_price,
    MAX(fs.unit_price) as max_unit_price
FROM fact_sales fs
JOIN dim_product p ON fs.product_id = p.product_id
JOIN dim_retailer r ON fs.retailer_id = r.retailer_id
GROUP BY p.product_id, p.product_sku, p.product_name, p.category, r.retailer_id, r.retailer_name;

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_mv_top_products_revenue ON mv_top_products_by_revenue(total_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_mv_top_products_category ON mv_top_products_by_revenue(category);
CREATE INDEX IF NOT EXISTS idx_mv_top_products_retailer ON mv_top_products_by_revenue(retailer_id);

-- 4. Sales Trends Over Time (Weekly Aggregation)
-- Provides weekly aggregated sales for trend analysis
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_weekly_sales_trends AS
SELECT 
    d.year,
    d.week,
    d.quarter,
    r.retailer_id,
    r.retailer_name,
    COUNT(*) as transaction_count,
    COUNT(DISTINCT fs.transaction_id) as unique_transactions,
    COUNT(DISTINCT d.date) as days_with_sales,
    SUM(fs.quantity) as total_quantity,
    SUM(fs.total_amount) as total_revenue,
    AVG(fs.total_amount) as avg_transaction_amount,
    MIN(d.date) as week_start_date,
    MAX(d.date) as week_end_date
FROM fact_sales fs
JOIN dim_date d ON fs.date_id = d.date_id
JOIN dim_retailer r ON fs.retailer_id = r.retailer_id
GROUP BY d.year, d.week, d.quarter, r.retailer_id, r.retailer_name;

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_mv_weekly_sales_year_week ON mv_weekly_sales_trends(year, week);
CREATE INDEX IF NOT EXISTS idx_mv_weekly_sales_retailer ON mv_weekly_sales_trends(retailer_id);

-- 5. Quarterly Sales Summary
-- High-level quarterly aggregated sales
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_quarterly_sales_summary AS
SELECT 
    d.year,
    d.quarter,
    r.retailer_id,
    r.retailer_name,
    COUNT(*) as transaction_count,
    COUNT(DISTINCT fs.transaction_id) as unique_transactions,
    COUNT(DISTINCT d.date) as days_with_sales,
    COUNT(DISTINCT p.product_id) as unique_products,
    SUM(fs.quantity) as total_quantity,
    SUM(fs.total_amount) as total_revenue,
    AVG(fs.total_amount) as avg_transaction_amount
FROM fact_sales fs
JOIN dim_date d ON fs.date_id = d.date_id
JOIN dim_retailer r ON fs.retailer_id = r.retailer_id
JOIN dim_product p ON fs.product_id = p.product_id
GROUP BY d.year, d.quarter, r.retailer_id, r.retailer_name;

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_mv_quarterly_sales_year_quarter ON mv_quarterly_sales_summary(year, quarter);
CREATE INDEX IF NOT EXISTS idx_mv_quarterly_sales_retailer ON mv_quarterly_sales_summary(retailer_id);

-- 6. Daily Sales by Product
-- Daily aggregated sales per product (useful for product performance analysis)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_sales_by_product AS
SELECT 
    d.date,
    d.year,
    d.month,
    p.product_id,
    p.product_sku,
    p.product_name,
    p.category,
    r.retailer_id,
    r.retailer_name,
    COUNT(*) as transaction_count,
    SUM(fs.quantity) as total_quantity_sold,
    SUM(fs.total_amount) as total_revenue,
    AVG(fs.unit_price) as avg_unit_price
FROM fact_sales fs
JOIN dim_date d ON fs.date_id = d.date_id
JOIN dim_product p ON fs.product_id = p.product_id
JOIN dim_retailer r ON fs.retailer_id = r.retailer_id
GROUP BY d.date, d.year, d.month, p.product_id, p.product_sku, p.product_name, p.category, r.retailer_id, r.retailer_name;

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_mv_daily_sales_product_date ON mv_daily_sales_by_product(date);
CREATE INDEX IF NOT EXISTS idx_mv_daily_sales_product_id ON mv_daily_sales_by_product(product_id);
CREATE INDEX IF NOT EXISTS idx_mv_daily_sales_product_category ON mv_daily_sales_by_product(category);


