#!/bin/bash
# Create database users with specific permissions
# This script runs during database initialization

set -e

# Get database name from environment (set by docker-compose)
DB_NAME="${POSTGRES_DB:-retail_analytics}"

# Get passwords from environment variables with defaults
AIRFLOW_DB_PASSWORD="${AIRFLOW_DB_PASSWORD:-airflow_password_123}"
TRANSFORMATION_DB_PASSWORD="${TRANSFORMATION_DB_PASSWORD:-transformation_password_123}"
DATA_QUALITY_DB_PASSWORD="${DATA_QUALITY_DB_PASSWORD:-data_quality_password_123}"
GRAFANA_DB_PASSWORD="${GRAFANA_DB_PASSWORD:-grafana_password_123}"
SUPERSET_DB_PASSWORD="${SUPERSET_DB_PASSWORD:-superset_password_123}"

echo "Creating database users with specific permissions..."

# Connect as postgres superuser (POSTGRES_USER from environment)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- 1. Airflow user - for Airflow metadata database and materialized view refresh
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'airflow_user') THEN
            CREATE USER airflow_user WITH PASSWORD '$AIRFLOW_DB_PASSWORD';
            RAISE NOTICE 'Created user airflow_user';
        ELSE
            RAISE NOTICE 'User airflow_user already exists';
        END IF;
    END
    \$\$;

    -- Grant connection to retail database
    GRANT CONNECT ON DATABASE $DB_NAME TO airflow_user;

    -- Grant usage on schema (public is default)
    GRANT USAGE ON SCHEMA public TO airflow_user;

    -- Grant SELECT on all existing tables for monitoring
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO airflow_user;

    -- Grant SELECT on all sequences
    GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO airflow_user;

    -- Set default privileges for future tables
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO airflow_user;

    -- 2. Transformation user - for ETL operations (INSERT, UPDATE, SELECT)
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'transformation_user') THEN
            CREATE USER transformation_user WITH PASSWORD '$TRANSFORMATION_DB_PASSWORD';
            RAISE NOTICE 'Created user transformation_user';
        ELSE
            RAISE NOTICE 'User transformation_user already exists';
        END IF;
    END
    \$\$;

    -- Grant connection to retail database
    GRANT CONNECT ON DATABASE $DB_NAME TO transformation_user;

    -- Grant usage on schema
    GRANT USAGE ON SCHEMA public TO transformation_user;

    -- Grant INSERT, UPDATE, SELECT on all existing tables
    GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO transformation_user;

    -- Grant USAGE on all sequences (needed for SERIAL columns)
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO transformation_user;

    -- Set default privileges for future tables
    ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT SELECT, INSERT, UPDATE ON TABLES TO transformation_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT USAGE, SELECT ON SEQUENCES TO transformation_user;

    -- 3. Data Quality user - read-only access for quality checks
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'data_quality_user') THEN
            CREATE USER data_quality_user WITH PASSWORD '$DATA_QUALITY_DB_PASSWORD';
            RAISE NOTICE 'Created user data_quality_user';
        ELSE
            RAISE NOTICE 'User data_quality_user already exists';
        END IF;
    END
    \$\$;

    -- Grant connection to retail database
    GRANT CONNECT ON DATABASE $DB_NAME TO data_quality_user;

    -- Grant usage on schema
    GRANT USAGE ON SCHEMA public TO data_quality_user;

    -- Grant SELECT on all existing tables
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO data_quality_user;

    -- Set default privileges for future tables
    ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT SELECT ON TABLES TO data_quality_user;

    -- 4. Grafana user - read-only access for visualization
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'grafana_user') THEN
            CREATE USER grafana_user WITH PASSWORD '$GRAFANA_DB_PASSWORD';
            RAISE NOTICE 'Created user grafana_user';
        ELSE
            RAISE NOTICE 'User grafana_user already exists';
        END IF;
    END
    \$\$;

    -- Grant connection to retail database
    GRANT CONNECT ON DATABASE $DB_NAME TO grafana_user;

    -- Grant usage on schema
    GRANT USAGE ON SCHEMA public TO grafana_user;

    -- Grant SELECT on all existing tables
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_user;

    -- Set default privileges for future tables
    ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT SELECT ON TABLES TO grafana_user;

    -- 5. Superset user - read-only access for BI analytics
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'superset_user') THEN
            CREATE USER superset_user WITH PASSWORD '$SUPERSET_DB_PASSWORD';
            RAISE NOTICE 'Created user superset_user';
        ELSE
            RAISE NOTICE 'User superset_user already exists';
        END IF;
    END
    \$\$;

    -- Create Superset metadata database
    SELECT 'CREATE DATABASE superset' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'superset')\gexec

    -- Grant connection to retail database
    GRANT CONNECT ON DATABASE $DB_NAME TO superset_user;

    -- Grant connection and creation privileges on superset metadata database
    GRANT CONNECT, CREATE ON DATABASE superset TO superset_user;

    -- Grant usage on schema
    GRANT USAGE ON SCHEMA public TO superset_user;

    -- Grant SELECT on all existing tables (read-only for analytics)
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO superset_user;

    -- Grant SELECT on all sequences
    GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO superset_user;

    -- Set default privileges for future tables
    ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT SELECT ON TABLES TO superset_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT SELECT ON SEQUENCES TO superset_user;

EOSQL

echo "✅ Database users created successfully!"

