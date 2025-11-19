#!/usr/bin/env python3
"""
Test script to verify S3 bucket connectivity and check uploaded data.
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.s3_client import get_s3_client, list_s3_objects, download_from_s3
from botocore.exceptions import ClientError

def test_s3_connection():
    """Test basic S3 connection."""
    print("🔍 Testing S3 connection...")
    try:
        client = get_s3_client()
        # Try to list buckets (this will fail if credentials are wrong)
        client.list_buckets()
        print("✅ S3 connection successful!")
        return client
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        print("\n💡 Make sure you have:")
        print("   - AWS_ACCESS_KEY_ID set in .env")
        print("   - AWS_SECRET_ACCESS_KEY set in .env")
        print("   - AWS_DEFAULT_REGION set in .env")
        return None

def check_bucket_exists(client, bucket_name):
    """Check if bucket exists and is accessible."""
    print(f"\n🔍 Checking if bucket '{bucket_name}' exists...")
    try:
        client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' exists and is accessible!")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '404' or error_code == 'NoSuchBucket':
            print(f"❌ Bucket '{bucket_name}' does not exist!")
            print(f"💡 Create the bucket in AWS Console or using: aws s3 mb s3://{bucket_name}")
        else:
            print(f"❌ Error accessing bucket: {e}")
        return False
    except Exception as e:
        print(f"❌ Error accessing bucket: {e}")
        return False

def list_uploaded_files(client, bucket_name, retailer_id=None, date_str=None):
    """List files uploaded to S3."""
    if date_str is None:
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    
    print(f"\n🔍 Listing files in bucket '{bucket_name}'...")
    
    if retailer_id:
        prefix = f"raw/{retailer_id}/"
    else:
        prefix = "raw/"
    
    # List only actual files (exclude directory prefixes)
    objects = list_s3_objects(client, bucket_name, prefix, files_only=True)
    
    if objects:
        print(f"✅ Found {len(objects)} file(s):")
        for obj in sorted(objects):
            # Show file size if available
            try:
                response = client.head_object(Bucket=bucket_name, Key=obj)
                size = response.get('ContentLength', 0)
                size_str = f" ({size:,} bytes)" if size > 0 else ""
                print(f"   📄 {obj}{size_str}")
            except:
                print(f"   📄 {obj}")
    else:
        print(f"⚠️  No files found with prefix '{prefix}'")
        print(f"💡 Run ingestion first: make test-ingestion")
    
    return objects

def download_and_verify_file(client, bucket_name, s3_key):
    """Download a file from S3 and verify its contents."""
    print(f"\n🔍 Downloading and verifying: {s3_key}")
    
    # Skip directory prefixes
    if s3_key.endswith('/'):
        print(f"⚠️  Skipping directory prefix: {s3_key}")
        return False
    
    try:
        data = download_from_s3(client, bucket_name, s3_key)
        if data:
            try:
                content = json.loads(data.decode('utf-8'))
                print(f"✅ File downloaded successfully!")
                print(f"   📊 Records in file: {len(content)}")
                if content:
                    print(f"   📋 Sample record keys: {list(content[0].keys())}")
                    # Show a sample record (first few fields)
                    sample = content[0]
                    print(f"   📝 Sample record (first 3 fields):")
                    for i, (key, value) in enumerate(list(sample.items())[:3]):
                        print(f"      {key}: {value}")
                return True
            except json.JSONDecodeError:
                print(f"⚠️  File is not valid JSON, showing first 200 characters:")
                print(f"   {data.decode('utf-8')[:200]}...")
                return True
        else:
            print(f"❌ Failed to download file")
            return False
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 S3 Bucket Testing Tool")
    print("=" * 60)
    
    # Test connection
    client = test_s3_connection()
    if not client:
        sys.exit(1)
    
    # Check bucket
    bucket_name = os.getenv('S3_BUCKET_RAW')
    if not bucket_name:
        print("\n❌ S3_BUCKET_RAW environment variable not set!")
        print("💡 Set it in your .env file")
        sys.exit(1)
    
    if not check_bucket_exists(client, bucket_name):
        sys.exit(1)
    
    # List files
    retailer_id = None
    date_str = None
    
    if len(sys.argv) > 1:
        retailer_id = sys.argv[1]
    if len(sys.argv) > 2:
        date_str = sys.argv[2]
    
    objects = list_uploaded_files(client, bucket_name, retailer_id, date_str)
    
    # If files exist, download and verify the first one
    if objects:
        print("\n" + "=" * 60)
        print("📥 Verifying file contents...")
        print("=" * 60)
        download_and_verify_file(client, bucket_name, objects[0])
    
    print("\n" + "=" * 60)
    print("✅ S3 test complete!")
    print("=" * 60)
    
    # Summary
    print("\n📋 Summary:")
    print(f"   Bucket: {bucket_name}")
    print(f"   Files found: {len(objects)}")
    if objects:
        print(f"   Latest file: {objects[-1]}")
    
    print("\n💡 To test with AWS CLI:")
    print(f"   aws s3 ls s3://{bucket_name}/raw/ --recursive")
    print(f"   aws s3 cp s3://{bucket_name}/{objects[0] if objects else 'raw/retailer_1/year=2024/month=01/day=01/sales_data.json'} -")

if __name__ == "__main__":
    main()

