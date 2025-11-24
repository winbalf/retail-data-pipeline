-- Stored Procedures for Retail Analytics Pipeline
-- This script creates useful stored procedures for common operations and analytics queries
-- These procedures can be called from Airflow tasks, Python services, or BI tools like Grafana

-- ============================================================================
-- MATERIALIZED VIEW REFRESH PROCEDURES
-- ============================================================================

-- Procedure to refresh a specific materialized view
-- Usage: CALL refresh_materialized_view('mv_daily_sales_summary');
CREATE OR REPLACE PROCEDURE refresh_materialized_view(view_name TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    CASE view_name
        WHEN 'mv_daily_sales_summary' THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales_summary;
        WHEN 'mv_monthly_sales_by_category' THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_sales_by_category;
        WHEN 'mv_top_products_by_revenue' THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_products_by_revenue;
        WHEN 'mv_weekly_sales_trends' THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_weekly_sales_trends;
        WHEN 'mv_quarterly_sales_summary' THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_quarterly_sales_summary;
        WHEN 'mv_daily_sales_by_product' THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales_by_product;
        ELSE
            RAISE EXCEPTION 'Unknown materialized view: %', view_name;
    END CASE;
EXCEPTION
    WHEN OTHERS THEN
        -- If CONCURRENTLY fails (e.g., no unique index), try without it
        CASE view_name
            WHEN 'mv_daily_sales_summary' THEN
                REFRESH MATERIALIZED VIEW mv_daily_sales_summary;
            WHEN 'mv_monthly_sales_by_category' THEN
                REFRESH MATERIALIZED VIEW mv_monthly_sales_by_category;
            WHEN 'mv_top_products_by_revenue' THEN
                REFRESH MATERIALIZED VIEW mv_top_products_by_revenue;
            WHEN 'mv_weekly_sales_trends' THEN
                REFRESH MATERIALIZED VIEW mv_weekly_sales_trends;
            WHEN 'mv_quarterly_sales_summary' THEN
                REFRESH MATERIALIZED VIEW mv_quarterly_sales_summary;
            WHEN 'mv_daily_sales_by_product' THEN
                REFRESH MATERIALIZED VIEW mv_daily_sales_by_product;
        END CASE;
END;
$$;

-- ============================================================================
-- ANALYTICS PROCEDURES
-- ============================================================================

-- Procedure: Get sales summary for a date range
-- Returns aggregated sales metrics for a specific date range
-- Usage: CALL get_sales_summary('2024-01-01', '2024-01-31', NULL);
CREATE OR REPLACE PROCEDURE get_sales_summary(
    start_date DATE,
    end_date DATE,
    retailer_id_param INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    result RECORD;
BEGIN
    SELECT 
        COUNT(DISTINCT fs.transaction_id) as total_transactions,
        COUNT(*) as total_line_items,
        SUM(fs.quantity) as total_quantity,
        SUM(fs.total_amount) as total_revenue,
        AVG(fs.total_amount) as avg_transaction_amount,
        MIN(fs.total_amount) as min_transaction_amount,
        MAX(fs.total_amount) as max_transaction_amount,
        COUNT(DISTINCT fs.product_id) as unique_products,
        COUNT(DISTINCT fs.customer_id) as unique_customers,
        COUNT(DISTINCT fs.store_id) as unique_stores
    INTO result
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
        AND (retailer_id_param IS NULL OR fs.retailer_id = retailer_id_param);
    
    RAISE NOTICE 'Sales Summary from % to %:', start_date, end_date;
    RAISE NOTICE 'Total Transactions: %', result.total_transactions;
    RAISE NOTICE 'Total Revenue: %', result.total_revenue;
    RAISE NOTICE 'Total Quantity: %', result.total_quantity;
    RAISE NOTICE 'Unique Products: %', result.unique_products;
END;
$$;

-- Function: Get top N products by revenue for a date range
-- Returns a table with top products
-- Usage: SELECT * FROM get_top_products_by_revenue('2024-01-01', '2024-01-31', 10, NULL);
CREATE OR REPLACE FUNCTION get_top_products_by_revenue(
    start_date DATE,
    end_date DATE,
    top_n INTEGER DEFAULT 10,
    retailer_id_param INTEGER DEFAULT NULL
)
RETURNS TABLE (
    product_id INTEGER,
    product_sku VARCHAR(100),
    product_name VARCHAR(255),
    category VARCHAR(100),
    total_revenue DECIMAL(10, 2),
    total_quantity_sold INTEGER,
    transaction_count BIGINT,
    avg_unit_price DECIMAL(10, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.product_id,
        p.product_sku,
        p.product_name,
        p.category,
        SUM(fs.total_amount) as total_revenue,
        SUM(fs.quantity)::INTEGER as total_quantity_sold,
        COUNT(*)::BIGINT as transaction_count,
        AVG(fs.unit_price) as avg_unit_price
    FROM fact_sales fs
    JOIN dim_product p ON fs.product_id = p.product_id
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
        AND (retailer_id_param IS NULL OR fs.retailer_id = retailer_id_param)
    GROUP BY p.product_id, p.product_sku, p.product_name, p.category
    ORDER BY total_revenue DESC
    LIMIT top_n;
END;
$$;

-- Function: Get sales trends by period (daily, weekly, monthly, quarterly)
-- Usage: SELECT * FROM get_sales_trends('2024-01-01', '2024-03-31', 'monthly', NULL);
CREATE OR REPLACE FUNCTION get_sales_trends(
    start_date DATE,
    end_date DATE,
    period_type TEXT DEFAULT 'daily',
    retailer_id_param INTEGER DEFAULT NULL
)
RETURNS TABLE (
    period_label TEXT,
    period_start DATE,
    period_end DATE,
    total_revenue DECIMAL(10, 2),
    total_quantity INTEGER,
    transaction_count BIGINT,
    avg_transaction_amount DECIMAL(10, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    CASE period_type
        WHEN 'daily' THEN
            RETURN QUERY
            SELECT 
                d.date::TEXT as period_label,
                d.date as period_start,
                d.date as period_end,
                SUM(fs.total_amount) as total_revenue,
                SUM(fs.quantity)::INTEGER as total_quantity,
                COUNT(DISTINCT fs.transaction_id)::BIGINT as transaction_count,
                AVG(fs.total_amount) as avg_transaction_amount
            FROM fact_sales fs
            JOIN dim_date d ON fs.date_id = d.date_id
            WHERE d.date BETWEEN start_date AND end_date
                AND (retailer_id_param IS NULL OR fs.retailer_id = retailer_id_param)
            GROUP BY d.date
            ORDER BY d.date;
        
        WHEN 'weekly' THEN
            RETURN QUERY
            SELECT 
                (d.year || '-W' || LPAD(d.week::TEXT, 2, '0'))::TEXT as period_label,
                MIN(d.date) as period_start,
                MAX(d.date) as period_end,
                SUM(fs.total_amount) as total_revenue,
                SUM(fs.quantity)::INTEGER as total_quantity,
                COUNT(DISTINCT fs.transaction_id)::BIGINT as transaction_count,
                AVG(fs.total_amount) as avg_transaction_amount
            FROM fact_sales fs
            JOIN dim_date d ON fs.date_id = d.date_id
            WHERE d.date BETWEEN start_date AND end_date
                AND (retailer_id_param IS NULL OR fs.retailer_id = retailer_id_param)
            GROUP BY d.year, d.week
            ORDER BY d.year, d.week;
        
        WHEN 'monthly' THEN
            RETURN QUERY
            SELECT 
                (d.year || '-' || LPAD(d.month::TEXT, 2, '0'))::TEXT as period_label,
                MIN(d.date) as period_start,
                MAX(d.date) as period_end,
                SUM(fs.total_amount) as total_revenue,
                SUM(fs.quantity)::INTEGER as total_quantity,
                COUNT(DISTINCT fs.transaction_id)::BIGINT as transaction_count,
                AVG(fs.total_amount) as avg_transaction_amount
            FROM fact_sales fs
            JOIN dim_date d ON fs.date_id = d.date_id
            WHERE d.date BETWEEN start_date AND end_date
                AND (retailer_id_param IS NULL OR fs.retailer_id = retailer_id_param)
            GROUP BY d.year, d.month
            ORDER BY d.year, d.month;
        
        WHEN 'quarterly' THEN
            RETURN QUERY
            SELECT 
                (d.year || '-Q' || d.quarter)::TEXT as period_label,
                MIN(d.date) as period_start,
                MAX(d.date) as period_end,
                SUM(fs.total_amount) as total_revenue,
                SUM(fs.quantity)::INTEGER as total_quantity,
                COUNT(DISTINCT fs.transaction_id)::BIGINT as transaction_count,
                AVG(fs.total_amount) as avg_transaction_amount
            FROM fact_sales fs
            JOIN dim_date d ON fs.date_id = d.date_id
            WHERE d.date BETWEEN start_date AND end_date
                AND (retailer_id_param IS NULL OR fs.retailer_id = retailer_id_param)
            GROUP BY d.year, d.quarter
            ORDER BY d.year, d.quarter;
        
        ELSE
            RAISE EXCEPTION 'Invalid period_type: %. Must be one of: daily, weekly, monthly, quarterly', period_type;
    END CASE;
END;
$$;

-- Function: Get sales by category for a date range
-- Usage: SELECT * FROM get_sales_by_category('2024-01-01', '2024-01-31', NULL);
CREATE OR REPLACE FUNCTION get_sales_by_category(
    start_date DATE,
    end_date DATE,
    retailer_id_param INTEGER DEFAULT NULL
)
RETURNS TABLE (
    category VARCHAR(100),
    total_revenue DECIMAL(10, 2),
    total_quantity INTEGER,
    transaction_count BIGINT,
    unique_products BIGINT,
    avg_unit_price DECIMAL(10, 2),
    revenue_percentage NUMERIC(5, 2)
)
LANGUAGE plpgsql
AS $$
DECLARE
    total_revenue_all DECIMAL(10, 2);
BEGIN
    -- Calculate total revenue for percentage calculation
    SELECT COALESCE(SUM(fs.total_amount), 0)
    INTO total_revenue_all
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    JOIN dim_product p ON fs.product_id = p.product_id
    WHERE d.date BETWEEN start_date AND end_date
        AND (retailer_id_param IS NULL OR fs.retailer_id = retailer_id_param)
        AND p.category IS NOT NULL;
    
    RETURN QUERY
    SELECT 
        p.category,
        SUM(fs.total_amount) as total_revenue,
        SUM(fs.quantity)::INTEGER as total_quantity,
        COUNT(DISTINCT fs.transaction_id)::BIGINT as transaction_count,
        COUNT(DISTINCT p.product_id)::BIGINT as unique_products,
        AVG(fs.unit_price) as avg_unit_price,
        CASE 
            WHEN total_revenue_all > 0 THEN 
                (SUM(fs.total_amount) / total_revenue_all * 100)::NUMERIC(5, 2)
            ELSE 0
        END as revenue_percentage
    FROM fact_sales fs
    JOIN dim_product p ON fs.product_id = p.product_id
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
        AND (retailer_id_param IS NULL OR fs.retailer_id = retailer_id_param)
        AND p.category IS NOT NULL
    GROUP BY p.category
    ORDER BY total_revenue DESC;
END;
$$;

-- Function: Get retailer performance comparison
-- Usage: SELECT * FROM get_retailer_performance('2024-01-01', '2024-01-31');
CREATE OR REPLACE FUNCTION get_retailer_performance(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    retailer_id INTEGER,
    retailer_name VARCHAR(100),
    total_revenue DECIMAL(10, 2),
    total_quantity INTEGER,
    transaction_count BIGINT,
    unique_products BIGINT,
    unique_customers BIGINT,
    avg_transaction_amount DECIMAL(10, 2),
    revenue_percentage NUMERIC(5, 2)
)
LANGUAGE plpgsql
AS $$
DECLARE
    total_revenue_all DECIMAL(10, 2);
BEGIN
    -- Calculate total revenue for percentage calculation
    SELECT COALESCE(SUM(fs.total_amount), 0)
    INTO total_revenue_all
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date;
    
    RETURN QUERY
    SELECT 
        r.retailer_id,
        r.retailer_name,
        SUM(fs.total_amount) as total_revenue,
        SUM(fs.quantity)::INTEGER as total_quantity,
        COUNT(DISTINCT fs.transaction_id)::BIGINT as transaction_count,
        COUNT(DISTINCT fs.product_id)::BIGINT as unique_products,
        COUNT(DISTINCT fs.customer_id)::BIGINT as unique_customers,
        AVG(fs.total_amount) as avg_transaction_amount,
        CASE 
            WHEN total_revenue_all > 0 THEN 
                (SUM(fs.total_amount) / total_revenue_all * 100)::NUMERIC(5, 2)
            ELSE 0
        END as revenue_percentage
    FROM fact_sales fs
    JOIN dim_retailer r ON fs.retailer_id = r.retailer_id
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
    GROUP BY r.retailer_id, r.retailer_name
    ORDER BY total_revenue DESC;
END;
$$;

-- ============================================================================
-- DATA QUALITY PROCEDURES
-- ============================================================================

-- Procedure: Check data quality metrics
-- Returns information about data completeness and quality
-- Usage: CALL check_data_quality('2024-01-01', '2024-01-31');
CREATE OR REPLACE PROCEDURE check_data_quality(
    start_date DATE,
    end_date DATE
)
LANGUAGE plpgsql
AS $$
DECLARE
    total_records BIGINT;
    records_with_customer BIGINT;
    records_with_store BIGINT;
    unique_transactions BIGINT;
    duplicate_transactions BIGINT;
    null_amounts BIGINT;
    negative_amounts BIGINT;
    zero_quantities BIGINT;
BEGIN
    -- Total records in date range
    SELECT COUNT(*)
    INTO total_records
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date;
    
    -- Records with customer information
    SELECT COUNT(*)
    INTO records_with_customer
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
        AND fs.customer_id IS NOT NULL;
    
    -- Records with store information
    SELECT COUNT(*)
    INTO records_with_store
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
        AND fs.store_id IS NOT NULL;
    
    -- Unique transactions
    SELECT COUNT(DISTINCT transaction_id)
    INTO unique_transactions
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date;
    
    -- Potential duplicate transactions (same transaction_id, product_id, retailer_id)
    SELECT COUNT(*) - COUNT(DISTINCT (transaction_id, product_id, retailer_id))
    INTO duplicate_transactions
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date;
    
    -- Records with null or zero amounts
    SELECT COUNT(*)
    INTO null_amounts
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
        AND (fs.total_amount IS NULL OR fs.total_amount = 0);
    
    -- Records with negative amounts
    SELECT COUNT(*)
    INTO negative_amounts
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
        AND fs.total_amount < 0;
    
    -- Records with zero quantities
    SELECT COUNT(*)
    INTO zero_quantities
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
        AND fs.quantity <= 0;
    
    -- Output results
    RAISE NOTICE 'Data Quality Report for % to %:', start_date, end_date;
    RAISE NOTICE 'Total Records: %', total_records;
    RAISE NOTICE 'Records with Customer: % (%.2f%%)', records_with_customer, 
        CASE WHEN total_records > 0 THEN (records_with_customer::NUMERIC / total_records * 100) ELSE 0 END;
    RAISE NOTICE 'Records with Store: % (%.2f%%)', records_with_store,
        CASE WHEN total_records > 0 THEN (records_with_store::NUMERIC / total_records * 100) ELSE 0 END;
    RAISE NOTICE 'Unique Transactions: %', unique_transactions;
    RAISE NOTICE 'Potential Duplicates: %', duplicate_transactions;
    RAISE NOTICE 'Null/Zero Amounts: %', null_amounts;
    RAISE NOTICE 'Negative Amounts: %', negative_amounts;
    RAISE NOTICE 'Zero Quantities: %', zero_quantities;
END;
$$;

-- Function: Get data quality summary as a table
-- Usage: SELECT * FROM get_data_quality_summary('2024-01-01', '2024-01-31');
CREATE OR REPLACE FUNCTION get_data_quality_summary(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    metric_name TEXT,
    metric_value BIGINT,
    metric_percentage NUMERIC(5, 2)
)
LANGUAGE plpgsql
AS $$
DECLARE
    total_records BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO total_records
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date;
    
    RETURN QUERY
    SELECT 
        'total_records'::TEXT,
        total_records,
        NULL::NUMERIC(5, 2)
    UNION ALL
    SELECT 
        'records_with_customer'::TEXT,
        COUNT(*),
        CASE WHEN total_records > 0 THEN (COUNT(*)::NUMERIC / total_records * 100) ELSE 0 END
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date AND fs.customer_id IS NOT NULL
    UNION ALL
    SELECT 
        'records_with_store'::TEXT,
        COUNT(*),
        CASE WHEN total_records > 0 THEN (COUNT(*)::NUMERIC / total_records * 100) ELSE 0 END
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date AND fs.store_id IS NOT NULL
    UNION ALL
    SELECT 
        'unique_transactions'::TEXT,
        COUNT(DISTINCT transaction_id),
        NULL::NUMERIC(5, 2)
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date
    UNION ALL
    SELECT 
        'null_or_zero_amounts'::TEXT,
        COUNT(*),
        CASE WHEN total_records > 0 THEN (COUNT(*)::NUMERIC / total_records * 100) ELSE 0 END
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date AND (fs.total_amount IS NULL OR fs.total_amount = 0)
    UNION ALL
    SELECT 
        'negative_amounts'::TEXT,
        COUNT(*),
        CASE WHEN total_records > 0 THEN (COUNT(*)::NUMERIC / total_records * 100) ELSE 0 END
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date AND fs.total_amount < 0
    UNION ALL
    SELECT 
        'zero_quantities'::TEXT,
        COUNT(*),
        CASE WHEN total_records > 0 THEN (COUNT(*)::NUMERIC / total_records * 100) ELSE 0 END
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date BETWEEN start_date AND end_date AND fs.quantity <= 0;
END;
$$;

-- ============================================================================
-- UTILITY PROCEDURES
-- ============================================================================

-- Procedure: Get database statistics
-- Provides overview of data in the warehouse
-- Usage: CALL get_database_statistics();
CREATE OR REPLACE PROCEDURE get_database_statistics()
LANGUAGE plpgsql
AS $$
DECLARE
    total_sales_records BIGINT;
    date_range_start DATE;
    date_range_end DATE;
    total_products BIGINT;
    total_customers BIGINT;
    total_stores BIGINT;
    total_retailers BIGINT;
    total_revenue DECIMAL(10, 2);
BEGIN
    -- Get fact table statistics
    SELECT COUNT(*), MIN(d.date), MAX(d.date), SUM(fs.total_amount)
    INTO total_sales_records, date_range_start, date_range_end, total_revenue
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id;
    
    -- Get dimension table counts
    SELECT COUNT(*) INTO total_products FROM dim_product;
    SELECT COUNT(*) INTO total_customers FROM dim_customer;
    SELECT COUNT(*) INTO total_stores FROM dim_store;
    SELECT COUNT(*) INTO total_retailers FROM dim_retailer;
    
    -- Output results
    RAISE NOTICE 'Database Statistics:';
    RAISE NOTICE 'Total Sales Records: %', total_sales_records;
    RAISE NOTICE 'Date Range: % to %', date_range_start, date_range_end;
    RAISE NOTICE 'Total Revenue: %', total_revenue;
    RAISE NOTICE 'Total Products: %', total_products;
    RAISE NOTICE 'Total Customers: %', total_customers;
    RAISE NOTICE 'Total Stores: %', total_stores;
    RAISE NOTICE 'Total Retailers: %', total_retailers;
END;
$$;

-- Function: Get last N days of sales
-- Useful for recent sales analysis
-- Usage: SELECT * FROM get_recent_sales(7, NULL);
CREATE OR REPLACE FUNCTION get_recent_sales(
    days_back INTEGER DEFAULT 7,
    retailer_id_param INTEGER DEFAULT NULL
)
RETURNS TABLE (
    date DATE,
    total_revenue DECIMAL(10, 2),
    total_quantity INTEGER,
    transaction_count BIGINT,
    avg_transaction_amount DECIMAL(10, 2)
)
LANGUAGE plpgsql
AS $$
DECLARE
    start_date DATE;
BEGIN
    start_date := CURRENT_DATE - (days_back - 1);
    
    RETURN QUERY
    SELECT 
        d.date,
        SUM(fs.total_amount) as total_revenue,
        SUM(fs.quantity)::INTEGER as total_quantity,
        COUNT(DISTINCT fs.transaction_id)::BIGINT as transaction_count,
        AVG(fs.total_amount) as avg_transaction_amount
    FROM fact_sales fs
    JOIN dim_date d ON fs.date_id = d.date_id
    WHERE d.date >= start_date
        AND (retailer_id_param IS NULL OR fs.retailer_id = retailer_id_param)
    GROUP BY d.date
    ORDER BY d.date DESC;
END;
$$;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant EXECUTE permissions on all procedures and functions to appropriate users

-- Grant to airflow_user (for materialized view refresh)
GRANT EXECUTE ON PROCEDURE refresh_materialized_view(TEXT) TO airflow_user;
GRANT EXECUTE ON FUNCTION refresh_all_materialized_views() TO airflow_user;

-- Grant to data_quality_user (for data quality checks)
GRANT EXECUTE ON PROCEDURE check_data_quality(DATE, DATE) TO data_quality_user;
GRANT EXECUTE ON FUNCTION get_data_quality_summary(DATE, DATE) TO data_quality_user;

-- Grant to grafana_user (for analytics and reporting)
GRANT EXECUTE ON PROCEDURE get_sales_summary(DATE, DATE, INTEGER) TO grafana_user;
GRANT EXECUTE ON FUNCTION get_top_products_by_revenue(DATE, DATE, INTEGER, INTEGER) TO grafana_user;
GRANT EXECUTE ON FUNCTION get_sales_trends(DATE, DATE, TEXT, INTEGER) TO grafana_user;
GRANT EXECUTE ON FUNCTION get_sales_by_category(DATE, DATE, INTEGER) TO grafana_user;
GRANT EXECUTE ON FUNCTION get_retailer_performance(DATE, DATE) TO grafana_user;
GRANT EXECUTE ON FUNCTION get_recent_sales(INTEGER, INTEGER) TO grafana_user;
GRANT EXECUTE ON PROCEDURE get_database_statistics() TO grafana_user;

-- Grant to transformation_user (for monitoring and validation)
GRANT EXECUTE ON PROCEDURE get_database_statistics() TO transformation_user;
GRANT EXECUTE ON FUNCTION get_data_quality_summary(DATE, DATE) TO transformation_user;

-- Grant to superset_user (for BI analytics and reporting)
GRANT EXECUTE ON PROCEDURE get_sales_summary(DATE, DATE, INTEGER) TO superset_user;
GRANT EXECUTE ON FUNCTION get_top_products_by_revenue(DATE, DATE, INTEGER, INTEGER) TO superset_user;
GRANT EXECUTE ON FUNCTION get_sales_trends(DATE, DATE, TEXT, INTEGER) TO superset_user;
GRANT EXECUTE ON FUNCTION get_sales_by_category(DATE, DATE, INTEGER) TO superset_user;
GRANT EXECUTE ON FUNCTION get_retailer_performance(DATE, DATE) TO superset_user;
GRANT EXECUTE ON FUNCTION get_recent_sales(INTEGER, INTEGER) TO superset_user;
GRANT EXECUTE ON PROCEDURE get_database_statistics() TO superset_user;

-- Grant to all users (read-only analytics functions)
GRANT EXECUTE ON FUNCTION get_top_products_by_revenue(DATE, DATE, INTEGER, INTEGER) TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_sales_trends(DATE, DATE, TEXT, INTEGER) TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_sales_by_category(DATE, DATE, INTEGER) TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_retailer_performance(DATE, DATE) TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_recent_sales(INTEGER, INTEGER) TO PUBLIC;

