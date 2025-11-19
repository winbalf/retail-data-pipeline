"""
Main transformation service - transforms S3 data to star schema in PostgreSQL.
"""
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformation.processors.star_schema_processor import StarSchemaProcessor

def main():
    """Main transformation function."""
    # Get date from command line or use yesterday
    date_str = None
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    
    print(f"Starting transformation for date: {date_str}")
    
    processor = StarSchemaProcessor()
    processor.process_date(date_str)

if __name__ == "__main__":
    main()

