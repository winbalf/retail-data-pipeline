#!/usr/bin/env python3
"""
Script to automatically generate .env file with all required parameters.
"""
import secrets
import os

def generate_fernet_key():
    """Generate a Fernet key for Airflow encryption."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()

def generate_secret_key():
    """Generate a random secret key."""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Create .env file with all required parameters."""
    env_content = f"""# PostgreSQL Configuration
POSTGRES_USER=retail_user
POSTGRES_PASSWORD=retail_password_123
POSTGRES_DB=retail_analytics
POSTGRES_PORT=5432

# Airflow Configuration
AIRFLOW_DB=airflow
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=admin
AIRFLOW_WEBSERVER_PORT=8080
AIRFLOW_FERNET_KEY={generate_fernet_key()}
AIRFLOW_WEBSERVER_SECRET_KEY={generate_secret_key()}

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=us-east-1

# S3 Buckets
S3_BUCKET_RAW=retail-raw-data
S3_BUCKET_PROCESSED=retail-processed-data

# Retailer 1 API Configuration (Local Simulated System)
RETAILER_1_API_URL=http://retailer1-api:5001
RETAILER_1_API_KEY=retailer1_api_key_123
RETAILER_1_DB_USER=retailer1_user
RETAILER_1_DB_PASSWORD=retailer1_pass
RETAILER_1_DB_NAME=retailer1_db
RETAILER_1_DB_PORT=5433
RETAILER_1_API_PORT=5001

# Retailer 2 API Configuration (Local Simulated System)
RETAILER_2_API_URL=http://retailer2-api:5002
RETAILER_2_API_KEY=retailer2_api_key_123
RETAILER_2_DB_USER=retailer2_user
RETAILER_2_DB_PASSWORD=retailer2_pass
RETAILER_2_DB_NAME=retailer2_db
RETAILER_2_DB_PORT=5434
RETAILER_2_API_PORT=5002

# Retailer 3 API Configuration (Local Simulated System)
RETAILER_3_API_URL=http://retailer3-api:5003
RETAILER_3_API_KEY=retailer3_api_key_123
RETAILER_3_DB_USER=retailer3_user
RETAILER_3_DB_PASSWORD=retailer3_pass
RETAILER_3_DB_NAME=retailer3_db
RETAILER_3_DB_PORT=5435
RETAILER_3_API_PORT=5003
"""
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ .env file created at {env_path}")
    print("⚠️  Please update the following values with your actual credentials:")
    print("   - AWS_ACCESS_KEY_ID")
    print("   - AWS_SECRET_ACCESS_KEY")
    print("   - S3_BUCKET_RAW")
    print("   - S3_BUCKET_PROCESSED")
    print("")
    print("ℹ️  Retailer APIs are configured to use local simulated systems.")
    print("   The retailers will be available at:")
    print("   - Retailer 1: http://localhost:5001")
    print("   - Retailer 2: http://localhost:5002")
    print("   - Retailer 3: http://localhost:5003")

if __name__ == "__main__":
    create_env_file()

