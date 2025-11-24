"""
Script to verify materialized views are working correctly.
Checks existence, data presence, and query performance.
"""
import os
import sys

# Add paths for both Docker and local execution
if '/opt/airflow' in os.path.abspath(__file__):
    # Running in Docker
    if '/opt/airflow' not in sys.path:
        sys.path.insert(0, '/opt/airflow')
    if '/opt/airflow/shared' not in sys.path:
        sys.path.insert(0, '/opt/airflow/shared')
else:
    # Running locally
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from shared.database import get_postgres_engine
from materialized_views.refresh_views import MATERIALIZED_VIEWS

def verify_view_exists(conn, view_name):
    """Check if a materialized view exists."""
    try:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 
                FROM pg_matviews 
                WHERE matviewname = :view_name
            )
        """), {"view_name": view_name})
        return result.scalar()
    except Exception as e:
        print(f"   ❌ Error checking existence: {e}")
        return False

def verify_view_has_data(conn, view_name):
    """Check if a materialized view has data."""
    try:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {view_name}"))
        count = result.scalar()
        return count, count > 0
    except Exception as e:
        print(f"   ❌ Error checking data: {e}")
        return 0, False

def verify_view_structure(conn, view_name):
    """Get column information for a view."""
    try:
        result = conn.execute(text(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = :view_name
            ORDER BY ordinal_position
        """), {"view_name": view_name})
        return result.fetchall()
    except Exception as e:
        print(f"   ❌ Error checking structure: {e}")
        return []

def verify_view_indexes(conn, view_name):
    """Check if indexes exist on the view."""
    try:
        result = conn.execute(text(f"""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = :view_name
        """), {"view_name": view_name})
        return [row[0] for row in result.fetchall()]
    except Exception as e:
        print(f"   ❌ Error checking indexes: {e}")
        return []

def test_sample_query(conn, view_name):
    """Test a sample query on the view."""
    try:
        # Try a simple SELECT with LIMIT
        result = conn.execute(text(f"SELECT * FROM {view_name} LIMIT 1"))
        row = result.fetchone()
        return True, row is not None
    except Exception as e:
        return False, str(e)

def verify_all_views():
    """Verify all materialized views."""
    print("=" * 70)
    print("Materialized Views Verification Report")
    print("=" * 70)
    print()
    
    engine = get_postgres_engine()
    results = {
        'total': len(MATERIALIZED_VIEWS),
        'exists': 0,
        'has_data': 0,
        'queryable': 0,
        'details': []
    }
    
    with engine.connect() as conn:
        for view_name in MATERIALIZED_VIEWS:
            print(f"📊 Verifying: {view_name}")
            print("-" * 70)
            
            view_result = {
                'name': view_name,
                'exists': False,
                'row_count': 0,
                'has_data': False,
                'queryable': False,
                'columns': [],
                'indexes': [],
                'errors': []
            }
            
            # Check existence
            exists = verify_view_exists(conn, view_name)
            view_result['exists'] = exists
            if exists:
                print(f"   ✅ View exists")
                results['exists'] += 1
            else:
                print(f"   ❌ View does NOT exist")
                view_result['errors'].append("View does not exist")
                results['details'].append(view_result)
                print()
                continue
            
            # Check data
            row_count, has_data = verify_view_has_data(conn, view_name)
            view_result['row_count'] = row_count
            view_result['has_data'] = has_data
            if has_data:
                print(f"   ✅ Has data: {row_count:,} rows")
                results['has_data'] += 1
            else:
                print(f"   ⚠️  No data: {row_count} rows")
            
            # Check structure
            columns = verify_view_structure(conn, view_name)
            view_result['columns'] = [col[0] for col in columns]
            if columns:
                print(f"   ✅ Structure: {len(columns)} columns")
                print(f"      Columns: {', '.join([col[0] for col in columns[:5]])}{'...' if len(columns) > 5 else ''}")
            
            # Check indexes
            indexes = verify_view_indexes(conn, view_name)
            view_result['indexes'] = indexes
            if indexes:
                print(f"   ✅ Indexes: {len(indexes)} found")
            else:
                print(f"   ⚠️  No indexes found")
            
            # Test query
            queryable, query_result = test_sample_query(conn, view_name)
            view_result['queryable'] = queryable
            if queryable:
                print(f"   ✅ Queryable: Sample query successful")
                results['queryable'] += 1
            else:
                print(f"   ❌ Queryable: Sample query failed - {query_result}")
                view_result['errors'].append(f"Query failed: {query_result}")
            
            results['details'].append(view_result)
            print()
    
    # Summary
    print("=" * 70)
    print("Verification Summary")
    print("=" * 70)
    print(f"Total views: {results['total']}")
    print(f"✅ Exist: {results['exists']}/{results['total']}")
    print(f"✅ Have data: {results['has_data']}/{results['total']}")
    print(f"✅ Queryable: {results['queryable']}/{results['total']}")
    print()
    
    # Issues
    issues = [v for v in results['details'] if v['errors'] or not v['exists'] or not v['has_data'] or not v['queryable']]
    if issues:
        print("⚠️  Issues Found:")
        for issue in issues:
            print(f"   - {issue['name']}:")
            if not issue['exists']:
                print(f"     • View does not exist")
            if not issue['has_data']:
                print(f"     • No data (0 rows)")
            if not issue['queryable']:
                print(f"     • Cannot query view")
            if issue['errors']:
                for error in issue['errors']:
                    print(f"     • {error}")
        print()
        return False
    else:
        print("✅ All views are working correctly!")
        print()
        return True

if __name__ == "__main__":
    try:
        success = verify_all_views()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

