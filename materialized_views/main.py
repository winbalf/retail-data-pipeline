"""
Main materialized views refresh service - refreshes all materialized views.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from materialized_views.refresh_views import MaterializedViewRefresher

def main():
    """Main function to refresh all materialized views."""
    print("=" * 60)
    print("Materialized Views Refresh Service")
    print("=" * 60)
    
    refresher = MaterializedViewRefresher()
    
    try:
        results = refresher.refresh_all_views()
        print(f"\n✅ Successfully refreshed all {results['successful']} materialized views")
        return results
    except Exception as e:
        print(f"\n❌ Error refreshing materialized views: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


