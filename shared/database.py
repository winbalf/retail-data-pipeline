"""
Shared database connection utilities.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

def get_postgres_connection_string():
    """Get PostgreSQL connection string from environment variables."""
    user = os.getenv('POSTGRES_USER', 'retail_user')
    password = os.getenv('POSTGRES_PASSWORD', 'retail_password_123')
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

