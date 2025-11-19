"""
Main data quality service - performs quality checks on transformed data.
"""
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_quality.quality_checks import DataQualityChecker

def main():
    """Main data quality function."""
    # Get date from command line or use yesterday
    date_str = None
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    
    print(f"Starting data quality checks for date: {date_str}")
    
    checker = DataQualityChecker()
    results = checker.run_all_checks(date_str)
    
    # Raise exception if any checks failed (Airflow will handle this properly)
    if not results['all_passed']:
        print(f"\n❌ Data quality checks failed for {date_str}")
        print(f"   {results['failed_checks']} out of {results['total_checks']} checks failed")
        raise Exception(f"Data quality checks failed: {results['failed_checks']} out of {results['total_checks']} checks failed")
    else:
        print(f"\n✅ All data quality checks passed for {date_str}")
    
    # Return results for potential XCom usage
    return results

if __name__ == "__main__":
    try:
        results = main()
        # When run directly (not from Airflow), exit with proper code
        sys.exit(0 if results['all_passed'] else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

