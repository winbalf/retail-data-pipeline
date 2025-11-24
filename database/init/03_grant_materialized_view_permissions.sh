#!/bin/bash
# Grant REFRESH permissions on materialized views to airflow_user
# This script runs after materialized views are created

set -e

DB_NAME="${POSTGRES_DB:-retail_analytics}"

echo "Granting REFRESH permissions on materialized views to airflow_user..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Grant REFRESH permission on all materialized views to airflow_user
    -- Note: REFRESH MATERIALIZED VIEW requires ownership or explicit grant
    DO \$\$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN 
            SELECT schemaname, matviewname 
            FROM pg_matviews 
            WHERE schemaname = 'public'
        LOOP
            EXECUTE format('GRANT SELECT ON %I.%I TO airflow_user', r.schemaname, r.matviewname);
            -- Note: REFRESH requires ownership, so we'll use a function or grant ownership
            -- For now, we grant SELECT and will handle REFRESH via a function owned by airflow_user
            RAISE NOTICE 'Granted SELECT on materialized view: %.%', r.schemaname, r.matviewname;
        END LOOP;
    END
    \$\$;

    -- Create a function to refresh materialized views that airflow_user can execute
    -- This function will be owned by the admin user but executable by airflow_user
    CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
    RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET search_path = public
    AS \$\$
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales_summary;
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_sales_by_category;
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_products_by_revenue;
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_weekly_sales_trends;
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_quarterly_sales_summary;
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales_by_product;
    EXCEPTION
        WHEN OTHERS THEN
            -- If CONCURRENTLY fails (e.g., no unique index), try without it
            REFRESH MATERIALIZED VIEW mv_daily_sales_summary;
            REFRESH MATERIALIZED VIEW mv_monthly_sales_by_category;
            REFRESH MATERIALIZED VIEW mv_top_products_by_revenue;
            REFRESH MATERIALIZED VIEW mv_weekly_sales_trends;
            REFRESH MATERIALIZED VIEW mv_quarterly_sales_summary;
            REFRESH MATERIALIZED VIEW mv_daily_sales_by_product;
    END;
    \$\$;

    -- Grant EXECUTE on the function to airflow_user
    GRANT EXECUTE ON FUNCTION refresh_all_materialized_views() TO airflow_user;
EOSQL

echo "✅ Granted REFRESH permissions on materialized views"

echo "✅ Materialized view permissions granted successfully!"

