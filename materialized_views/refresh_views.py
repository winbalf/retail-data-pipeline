"""
Service to refresh materialized views in PostgreSQL.
"""
import os
import sys
from sqlalchemy import text
from shared.database import get_postgres_engine

# List of all materialized views to refresh
MATERIALIZED_VIEWS = [
    'mv_daily_sales_summary',
    'mv_monthly_sales_by_category',
    'mv_top_products_by_revenue',
    'mv_weekly_sales_trends',
    'mv_quarterly_sales_summary',
    'mv_daily_sales_by_product',
]

class MaterializedViewRefresher:
    """Handles refreshing of materialized views."""
    
    def __init__(self):
        """Initialize the refresher with database connection."""
        self.engine = get_postgres_engine()
    
    def refresh_view(self, view_name: str):
        """
        Refresh a single materialized view using stored procedure.
        
        Args:
            view_name: Name of the materialized view to refresh
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"🔄 Refreshing materialized view: {view_name}")
            with self.engine.begin() as conn:
                # Try to use the new stored procedure first (preferred method)
                try:
                    conn.execute(text(f"CALL refresh_materialized_view(:view_name)"), {"view_name": view_name})
                    print(f"✅ Successfully refreshed {view_name} via stored procedure")
                    return True
                except Exception as proc_error:
                    # If procedure doesn't exist or user doesn't have permission, try direct refresh
                    print(f"⚠️  Stored procedure not available, trying direct refresh: {proc_error}")
                    try:
                        conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
                        print(f"✅ Successfully refreshed {view_name} via concurrent refresh")
                        return True
                    except Exception as concurrent_error:
                        # If concurrent refresh fails (e.g., no unique index), try regular refresh
                        print(f"⚠️  Concurrent refresh failed, trying regular refresh: {concurrent_error}")
                        conn.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                        print(f"✅ Successfully refreshed {view_name} via regular refresh")
                        return True
        except Exception as e:
            print(f"❌ Error refreshing {view_name}: {str(e)}")
            raise
    
    def refresh_all_views(self):
        """
        Refresh all materialized views.
        
        Uses the secure refresh_all_materialized_views() function if available,
        otherwise refreshes each view individually.
        
        Returns:
            dict: Results of refresh operation with success/failure status
        """
        results = {
            'total_views': len(MATERIALIZED_VIEWS),
            'successful': 0,
            'failed': 0,
            'failed_views': []
        }
        
        print(f"🔄 Starting refresh of {results['total_views']} materialized views...")
        
        # Try to use the secure function first (refreshes all views at once - most efficient)
        try:
            with self.engine.begin() as conn:
                conn.execute(text("SELECT refresh_all_materialized_views()"))
            print(f"✅ Successfully refreshed all views via secure function")
            results['successful'] = results['total_views']
            return results
        except Exception as func_error:
            # If function doesn't exist or user doesn't have permission, refresh individually using stored procedures
            print(f"⚠️  Batch refresh function not available, refreshing views individually using stored procedures: {func_error}")
            for view_name in MATERIALIZED_VIEWS:
                try:
                    self.refresh_view(view_name)
                    results['successful'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['failed_views'].append({
                        'view': view_name,
                        'error': str(e)
                    })
                    # Continue with other views even if one fails
                    print(f"⚠️  Continuing with other views despite failure of {view_name}")
        
        print(f"\n📊 Refresh Summary:")
        print(f"   Total views: {results['total_views']}")
        print(f"   Successful: {results['successful']}")
        print(f"   Failed: {results['failed']}")
        
        if results['failed'] > 0:
            print(f"\n❌ Failed views:")
            for failure in results['failed_views']:
                print(f"   - {failure['view']}: {failure['error']}")
            raise Exception(f"Failed to refresh {results['failed']} out of {results['total_views']} materialized views")
        
        return results
    
    def get_view_info(self, view_name: str):
        """
        Get information about a materialized view.
        
        Args:
            view_name: Name of the materialized view
            
        Returns:
            dict: View information including row count
        """
        try:
            with self.engine.connect() as conn:
                # Get row count
                result = conn.execute(text(f"SELECT COUNT(*) FROM {view_name}"))
                row_count = result.scalar()
                
                # Get last refresh time (if available in PostgreSQL metadata)
                # Note: PostgreSQL doesn't track this by default, but we can check if view exists
                return {
                    'view_name': view_name,
                    'row_count': row_count,
                    'exists': True
                }
        except Exception as e:
            return {
                'view_name': view_name,
                'error': str(e),
                'exists': False
            }
    
    def get_all_views_info(self):
        """
        Get information about all materialized views.
        
        Returns:
            list: List of view information dictionaries
        """
        views_info = []
        for view_name in MATERIALIZED_VIEWS:
            info = self.get_view_info(view_name)
            views_info.append(info)
        return views_info


