"""
Shared S3 client utilities.
"""
import os
import boto3
from botocore.exceptions import ClientError

def get_s3_client():
    """Create and return a boto3 S3 client."""
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )

def upload_to_s3(client, bucket_name, key, data, content_type='application/json'):
    """Upload data to S3 bucket."""
    try:
        client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type
        )
        return True
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return False

def download_from_s3(client, bucket_name, key):
    """Download data from S3 bucket."""
    try:
        response = client.get_object(Bucket=bucket_name, Key=key)
        return response['Body'].read()
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        return None

def list_s3_objects(client, bucket_name, prefix='', files_only=True):
    """List objects in S3 bucket with given prefix.
    
    Args:
        client: boto3 S3 client
        bucket_name: Name of the S3 bucket
        prefix: Prefix to filter objects
        files_only: If True, exclude directory prefixes (keys ending with /)
    
    Returns:
        List of object keys
    """
    try:
        response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            keys = [obj['Key'] for obj in response['Contents']]
            if files_only:
                # Filter out directory prefixes (keys ending with /)
                keys = [key for key in keys if not key.endswith('/')]
            return keys
        return []
    except ClientError as e:
        print(f"Error listing S3 objects: {e}")
        return []

