#!/usr/bin/env python
"""
Script to add PostgreSQL database connection to Superset
"""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, '/app')

from superset import app
from superset.extensions import db
from superset.models.core import Database

def add_database():
    with app.app_context():
        # Check if database already exists
        existing = db.session.query(Database).filter_by(database_name='Retail Analytics').first()
        if existing:
            print('✅ Database connection "Retail Analytics" already exists')
            return
        
        # Get connection details from environment
        postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
        postgres_port = os.getenv('POSTGRES_PORT', '5432')
        postgres_db = os.getenv('POSTGRES_DB', 'retail_analytics')
        superset_user = os.getenv('SUPERSET_DB_USER', 'superset_user')
        superset_password = os.getenv('SUPERSET_DB_PASSWORD', 'superset_password_123')
        
        # Create SQLAlchemy URI
        sqlalchemy_uri = f'postgresql+psycopg2://{superset_user}:{superset_password}@{postgres_host}:{postgres_port}/{postgres_db}'
        
        # Create database connection
        database = Database(
            database_name='Retail Analytics',
            sqlalchemy_uri=sqlalchemy_uri,
            extra='{"schemas_allowed_for_file_upload": ["public"]}'
        )
        db.session.add(database)
        db.session.commit()
        print('✅ Database connection "Retail Analytics" created successfully')
        print(f'   Connection: {postgres_db} on {postgres_host}:{postgres_port}')

if __name__ == '__main__':
    add_database()

