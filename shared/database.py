"""
Shared database connection utilities.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

def get_postgres_connection_string():
    """
    Get PostgreSQL connection string from environment variables.
    
    Supports service-specific user variables for role-based access:
    - TRANSFORMATION_DB_USER / TRANSFORMATION_DB_PASSWORD (for transformation service)
    - DATA_QUALITY_DB_USER / DATA_QUALITY_DB_PASSWORD (for data quality service)
    - AIRFLOW_DB_USER / AIRFLOW_DB_PASSWORD (for Airflow tasks like materialized views)
    - GRAFANA_DB_USER / GRAFANA_DB_PASSWORD (for Grafana)
    - SUPERSET_DB_USER / SUPERSET_DB_PASSWORD (for Superset)
    
    Priority: POSTGRES_USER (explicitly set) > service-specific > default
    """
    # Priority: POSTGRES_USER (if explicitly set) > service-specific > default
    # This allows tasks to explicitly set POSTGRES_USER for their specific user
    user = (
        os.getenv('POSTGRES_USER') or
        os.getenv('TRANSFORMATION_DB_USER') or
        os.getenv('DATA_QUALITY_DB_USER') or
        os.getenv('AIRFLOW_DB_USER') or
        os.getenv('GRAFANA_DB_USER') or
        os.getenv('SUPERSET_DB_USER') or
        'retail_user'
    )
    
    password = (
        os.getenv('POSTGRES_PASSWORD') or
        os.getenv('TRANSFORMATION_DB_PASSWORD') or
        os.getenv('DATA_QUALITY_DB_PASSWORD') or
        os.getenv('AIRFLOW_DB_PASSWORD') or
        os.getenv('GRAFANA_DB_PASSWORD') or
        os.getenv('SUPERSET_DB_PASSWORD') or
        'retail_password_123'
    )
    
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    db = os.getenv('POSTGRES_DB', 'retail_analytics')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

def get_postgres_engine():
    """Create and return a SQLAlchemy engine for PostgreSQL."""
    connection_string = get_postgres_connection_string()
    return create_engine(
        connection_string,
        poolclass=NullPool,
        echo=False
    )

def get_postgres_session():
    """Create and return a SQLAlchemy session."""
    engine = get_postgres_engine()
    Session = sessionmaker(bind=engine)
    return Session()

