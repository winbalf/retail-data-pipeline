"""
Main ingestion service - ingests data from 3 retailers and uploads to S3.
"""
import os
import json
from datetime import datetime, timedelta
from typing import List
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.services.retailer1_service import Retailer1Service
from ingestion.services.retailer2_service import Retailer2Service
from ingestion.services.retailer3_service import Retailer3Service
from ingestion.models.retailer_data import SalesRecord
from shared.s3_client import get_s3_client, upload_to_s3

def serialize_sales_record(record: SalesRecord) -> dict:
    """Convert SalesRecord to dictionary for JSON serialization."""
    return {
        'retailer_id': record.retailer_id,
        'transaction_id': record.transaction_id,
        'product_id': record.product_id,
        'product_name': record.product_name,
        'category': record.category,
        'quantity': record.quantity,
        'unit_price': record.unit_price,
        'total_amount': record.total_amount,
        'transaction_date': record.transaction_date.isoformat(),
        'customer_id': record.customer_id,
        'store_id': record.store_id,
        'raw_data': record.raw_data
    }

def ingest_retailer_data(retailer_service, date_str: str = None) -> List[SalesRecord]:
    """
    Ingest data from a retailer service.
    
    Args:
        retailer_service: Retailer service instance
        date_str: Date string in YYYY-MM-DD format (defaults to yesterday)
        
    Returns:
        List of normalized SalesRecord objects
    """
    if date_str is None:
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    
    print(f"Fetching data from {retailer_service.retailer_id} for date: {date_str}")
    raw_data = retailer_service.fetch_sales_data(start_date=date_str, end_date=date_str)
    
    normalized_records = []
    for raw_record in raw_data:
        try:
            normalized = retailer_service.normalize_sales_record(raw_record)
            normalized_records.append(normalized)
        except Exception as e:
            print(f"Error normalizing record: {e}")
            continue
    
    print(f"Successfully normalized {len(normalized_records)} records from {retailer_service.retailer_id}")
    return normalized_records

def upload_to_s3_raw(records: List[SalesRecord], retailer_id: str, date_str: str):
    """
    Upload records to S3 raw bucket.
    
    Args:
        records: List of SalesRecord objects
        retailer_id: Retailer identifier
        date_str: Date string in YYYY-MM-DD format
    """
    bucket_name = os.getenv('S3_BUCKET_RAW')
    if not bucket_name:
        raise ValueError("S3_BUCKET_RAW environment variable not set")
    
    # Create S3 key with date partitioning
    year, month, day = date_str.split('-')
    s3_key = f"raw/{retailer_id}/year={year}/month={month}/day={day}/sales_data.json"
    
    # Serialize records
    serialized_records = [serialize_sales_record(record) for record in records]
    data = json.dumps(serialized_records, indent=2)
    
    # Upload to S3
    s3_client = get_s3_client()
    success = upload_to_s3(s3_client, bucket_name, s3_key, data.encode('utf-8'))
    
    if success:
        print(f"✅ Uploaded {len(records)} records to s3://{bucket_name}/{s3_key}")
    else:
        raise Exception(f"Failed to upload to S3: {s3_key}")

def main():
    """Main ingestion function."""
    # Get date from command line or use yesterday
    date_str = None
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    
    print(f"Starting ingestion for date: {date_str}")
    
    # Initialize retailer services
    retailer1 = Retailer1Service()
    retailer2 = Retailer2Service()
    retailer3 = Retailer3Service()
    
    # Ingest from all retailers
    all_records = []
    
    try:
        records1 = ingest_retailer_data(retailer1, date_str)
        if records1:
            upload_to_s3_raw(records1, retailer1.retailer_id, date_str)
            all_records.extend(records1)
    except Exception as e:
        print(f"Error processing Retailer 1: {e}")
    
    try:
        records2 = ingest_retailer_data(retailer2, date_str)
        if records2:
            upload_to_s3_raw(records2, retailer2.retailer_id, date_str)
            all_records.extend(records2)
    except Exception as e:
        print(f"Error processing Retailer 2: {e}")
    
    try:
        records3 = ingest_retailer_data(retailer3, date_str)
        if records3:
            upload_to_s3_raw(records3, retailer3.retailer_id, date_str)
            all_records.extend(records3)
    except Exception as e:
        print(f"Error processing Retailer 3: {e}")
    
    print(f"\n✅ Ingestion complete! Total records ingested: {len(all_records)}")
    return len(all_records)

if __name__ == "__main__":
    main()

