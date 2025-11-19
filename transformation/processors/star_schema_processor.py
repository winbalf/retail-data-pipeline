"""
Processor to transform raw data from S3 into star schema format for PostgreSQL.
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text
from shared.database import get_postgres_engine
from shared.s3_client import get_s3_client, download_from_s3, list_s3_objects, upload_to_s3

class StarSchemaProcessor:
    """Process raw data from S3 and load into star schema."""
    
    def __init__(self):
        self.engine = get_postgres_engine()
        self.s3_client = get_s3_client()
        self.s3_bucket_raw = os.getenv('S3_BUCKET_RAW')
        self.s3_bucket_processed = os.getenv('S3_BUCKET_PROCESSED')
    
    def get_or_create_date_id(self, date: datetime) -> int:
        """Get or create date dimension record and return date_id."""
        date_str = date.date()
        year = date.year
        quarter = (date.month - 1) // 3 + 1
        month = date.month
        week = date.isocalendar()[1]
        day = date.day
        day_of_week = date.weekday() + 1  # Monday = 1, Sunday = 7
        day_name = date.strftime('%A')
        is_weekend = day_of_week >= 6
        
        with self.engine.begin() as conn:
            # Check if date exists
            result = conn.execute(
                text("SELECT date_id FROM dim_date WHERE date = :date"),
                {"date": date_str}
            )
            row = result.fetchone()
            
            if row:
                return row[0]
            
            # Insert new date
            result = conn.execute(
                text("""
                    INSERT INTO dim_date (date, year, quarter, month, week, day, day_of_week, day_name, is_weekend)
                    VALUES (:date, :year, :quarter, :month, :week, :day, :day_of_week, :day_name, :is_weekend)
                    RETURNING date_id
                """),
                {
                    "date": date_str,
                    "year": year,
                    "quarter": quarter,
                    "month": month,
                    "week": week,
                    "day": day,
                    "day_of_week": day_of_week,
                    "day_name": day_name,
                    "is_weekend": is_weekend
                }
            )
            return result.fetchone()[0]
    
    def get_or_create_product_id(self, product_sku: str, product_name: str, category: str) -> int:
        """Get or create product dimension record and return product_id."""
        with self.engine.begin() as conn:
            # Check if product exists
            result = conn.execute(
                text("SELECT product_id FROM dim_product WHERE product_sku = :sku"),
                {"sku": product_sku}
            )
            row = result.fetchone()
            
            if row:
                # Update if needed
                conn.execute(
                    text("""
                        UPDATE dim_product 
                        SET product_name = :name, category = :category, updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = :product_id
                    """),
                    {"name": product_name, "category": category, "product_id": row[0]}
                )
                return row[0]
            
            # Insert new product
            result = conn.execute(
                text("""
                    INSERT INTO dim_product (product_sku, product_name, category)
                    VALUES (:sku, :name, :category)
                    RETURNING product_id
                """),
                {"sku": product_sku, "name": product_name, "category": category}
            )
            return result.fetchone()[0]
    
    def get_or_create_customer_id(self, customer_external_id: str = None) -> int:
        """Get or create customer dimension record and return customer_id."""
        if not customer_external_id:
            return None
        
        with self.engine.begin() as conn:
            # Check if customer exists
            result = conn.execute(
                text("SELECT customer_id FROM dim_customer WHERE customer_external_id = :ext_id"),
                {"ext_id": customer_external_id}
            )
            row = result.fetchone()
            
            if row:
                return row[0]
            
            # Insert new customer
            result = conn.execute(
                text("""
                    INSERT INTO dim_customer (customer_external_id)
                    VALUES (:ext_id)
                    RETURNING customer_id
                """),
                {"ext_id": customer_external_id}
            )
            return result.fetchone()[0]
    
    def get_or_create_store_id(self, store_external_id: str = None) -> int:
        """Get or create store dimension record and return store_id."""
        if not store_external_id:
            return None
        
        with self.engine.begin() as conn:
            # Check if store exists
            result = conn.execute(
                text("SELECT store_id FROM dim_store WHERE store_external_id = :ext_id"),
                {"ext_id": store_external_id}
            )
            row = result.fetchone()
            
            if row:
                return row[0]
            
            # Insert new store
            result = conn.execute(
                text("""
                    INSERT INTO dim_store (store_external_id)
                    VALUES (:ext_id)
                    RETURNING store_id
                """),
                {"ext_id": store_external_id}
            )
            return result.fetchone()[0]
    
    def get_retailer_id(self, retailer_code: str) -> int:
        """Get retailer_id from retailer code."""
        with self.engine.begin() as conn:
            result = conn.execute(
                text("SELECT retailer_id FROM dim_retailer WHERE retailer_code = :code"),
                {"code": retailer_code}
            )
            row = result.fetchone()
            if row:
                return row[0]
            raise ValueError(f"Retailer code {retailer_code} not found")
    
    def load_sales_fact(self, records: List[Dict[str, Any]]):
        """Load sales records into fact_sales table."""
        inserted_count = 0
        skipped_count = 0
        error_details = []
        
        with self.engine.begin() as conn:
            for idx, record in enumerate(records):
                try:
                    # Validate required fields
                    required_fields = ['transaction_date', 'product_id', 'product_name', 
                                     'transaction_id', 'quantity', 'unit_price', 
                                     'total_amount', 'retailer_id']
                    missing_fields = [f for f in required_fields if f not in record]
                    if missing_fields:
                        error_msg = f"Missing required fields: {missing_fields}"
                        error_details.append(f"Record {idx}: {error_msg}")
                        skipped_count += 1
                        continue
                    
                    # Get dimension IDs
                    transaction_date = datetime.fromisoformat(record['transaction_date'])
                    date_id = self.get_or_create_date_id(transaction_date)
                    product_id = self.get_or_create_product_id(
                        record['product_id'],
                        record['product_name'],
                        record.get('category', '')
                    )
                    customer_id = self.get_or_create_customer_id(record.get('customer_id'))
                    store_id = self.get_or_create_store_id(record.get('store_id'))
                    retailer_id = self.get_retailer_id(record['retailer_id'])
                    
                    # Insert fact record
                    result = conn.execute(
                        text("""
                            INSERT INTO fact_sales (
                                date_id, product_id, customer_id, store_id, retailer_id,
                                transaction_id, quantity, unit_price, total_amount
                            )
                            VALUES (
                                :date_id, :product_id, :customer_id, :store_id, :retailer_id,
                                :transaction_id, :quantity, :unit_price, :total_amount
                            )
                            ON CONFLICT (transaction_id, product_id, retailer_id) DO NOTHING
                            RETURNING transaction_id
                        """),
                        {
                            "date_id": date_id,
                            "product_id": product_id,
                            "customer_id": customer_id,
                            "store_id": store_id,
                            "retailer_id": retailer_id,
                            "transaction_id": record['transaction_id'],
                            "quantity": record['quantity'],
                            "unit_price": record['unit_price'],
                            "total_amount": record['total_amount']
                        }
                    )
                    # Check if row was actually inserted (not a duplicate)
                    if result.fetchone():
                        inserted_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    error_msg = f"Error loading record {record.get('transaction_id', f'#{idx}')}: {str(e)}"
                    error_details.append(error_msg)
                    skipped_count += 1
                    continue
        
        if error_details and len(error_details) <= 10:
            print(f"  ⚠️  Errors encountered:")
            for error in error_details[:10]:
                print(f"    - {error}")
            if len(error_details) > 10:
                print(f"    ... and {len(error_details) - 10} more errors")
        
        print(f"  ✅ Loaded {inserted_count} records, skipped {skipped_count} duplicates/errors")
        return inserted_count
    
    def upload_processed_data_to_s3(self, records: List[Dict[str, Any]], retailer_id: str, date_str: str) -> bool:
        """
        Upload processed/cleaned records to S3 processed bucket.
        
        Args:
            records: List of cleaned sales records
            retailer_id: Retailer identifier
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            True if upload successful, False otherwise
        """
        if not self.s3_bucket_processed:
            print(f"  ⚠️  S3_BUCKET_PROCESSED not configured, skipping processed data upload")
            return False
        
        if not records:
            print(f"  ⚠️  No records to upload to processed bucket")
            return False
        
        # Create S3 key with date partitioning (similar to raw bucket structure)
        year, month, day = date_str.split('-')
        s3_key = f"processed/{retailer_id}/year={year}/month={month}/day={day}/sales_data.json"
        
        # Serialize records to JSON
        data = json.dumps(records, indent=2, default=str)
        
        # Upload to S3
        success = upload_to_s3(self.s3_client, self.s3_bucket_processed, s3_key, data.encode('utf-8'))
        
        if success:
            print(f"  ✅ Uploaded {len(records)} processed records to s3://{self.s3_bucket_processed}/{s3_key}")
        else:
            print(f"  ❌ Failed to upload processed data to s3://{self.s3_bucket_processed}/{s3_key}")
        
        return success
    
    def process_s3_file(self, s3_key: str, retailer_id: str = None, date_str: str = None) -> int:
        """
        Process a single S3 file and load into star schema.
        
        Args:
            s3_key: S3 key of the file to process
            retailer_id: Retailer identifier (extracted from s3_key if not provided)
            date_str: Date string in YYYY-MM-DD format (extracted from s3_key if not provided)
        """
        print(f"Processing S3 file: {s3_key}")
        
        # Download from S3
        data = download_from_s3(self.s3_client, self.s3_bucket_raw, s3_key)
        if not data:
            print(f"❌ Failed to download {s3_key} - check S3 connection and permissions")
            return 0
        
        print(f"  Downloaded {len(data)} bytes from S3")
        
        # Parse JSON
        try:
            records = json.loads(data.decode('utf-8'))
            if not isinstance(records, list):
                print(f"❌ Error: Expected JSON array, got {type(records).__name__}")
                return 0
            print(f"  Parsed {len(records)} records from JSON")
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON from {s3_key}: {e}")
            return 0
        except Exception as e:
            print(f"❌ Unexpected error parsing JSON from {s3_key}: {e}")
            return 0
        
        if len(records) == 0:
            print(f"  ⚠️  File contains 0 records, skipping")
            return 0
        
        # Extract retailer_id and date from s3_key if not provided
        # s3_key format: raw/{retailer_id}/year={year}/month={month}/day={day}/sales_data.json
        if not retailer_id or not date_str:
            parts = s3_key.split('/')
            if not retailer_id:
                retailer_id = parts[1] if len(parts) > 1 else 'unknown'
            if not date_str and len(parts) >= 5:
                # Extract year, month, day from parts
                year = parts[2].split('=')[1] if '=' in parts[2] else None
                month = parts[3].split('=')[1] if '=' in parts[3] else None
                day = parts[4].split('=')[1] if '=' in parts[4] else None
                if year and month and day:
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Validate and clean records before processing
        cleaned_records = []
        for record in records:
            # Validate required fields
            required_fields = ['transaction_date', 'product_id', 'product_name', 
                             'transaction_id', 'quantity', 'unit_price', 
                             'total_amount', 'retailer_id']
            if all(f in record for f in required_fields):
                cleaned_records.append(record)
        
        # Upload cleaned/processed records to processed bucket
        if cleaned_records and date_str:
            self.upload_processed_data_to_s3(cleaned_records, retailer_id, date_str)
        
        # Load into star schema
        return self.load_sales_fact(records)
    
    def process_date(self, date_str: str):
        """Process all files for a specific date."""
        year, month, day = date_str.split('-')
        
        # List all files for this date across all retailers
        retailers = ['retailer_1', 'retailer_2', 'retailer_3']
        total_records = 0
        total_files_found = 0
        total_files_processed = 0
        
        print(f"\nSearching for files in S3 bucket: {self.s3_bucket_raw}")
        
        for retailer in retailers:
            prefix = f"raw/{retailer}/year={year}/month={month}/day={day}/"
            print(f"\nChecking retailer: {retailer} (prefix: {prefix})")
            files = list_s3_objects(self.s3_client, self.s3_bucket_raw, prefix)
            
            json_files = [f for f in files if f.endswith('.json')]
            total_files_found += len(json_files)
            
            if len(json_files) == 0:
                print(f"  No JSON files found for {retailer}")
            else:
                print(f"  Found {len(json_files)} JSON file(s)")
            
            for file_key in json_files:
                total_files_processed += 1
                records_loaded = self.process_s3_file(file_key, retailer_id=retailer, date_str=date_str)
                total_records += records_loaded
        
        print(f"\n📊 Summary:")
        print(f"  Files found: {total_files_found}")
        print(f"  Files processed: {total_files_processed}")
        print(f"  Total records loaded: {total_records}")
        print(f"\n✅ Transformation complete for {date_str}!")
        return total_records

