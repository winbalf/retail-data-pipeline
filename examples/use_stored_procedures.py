"""
Example script demonstrating how to use stored procedures in the retail data pipeline.

This script shows various ways to interact with the stored procedures and functions
available in the database for analytics and data quality checks.
"""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import text
from shared.database import get_postgres_engine

def example_get_top_products():
    """Example: Get top products using stored procedure function."""
    print("\n" + "="*60)
    print("Example 1: Get Top Products by Revenue")
    print("="*60)
    
    engine = get_postgres_engine()
    
    # Get top 10 products for the last 30 days
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM get_top_products_by_revenue(:start_date, :end_date, 10, NULL)
        """), {"start_date": start_date, "end_date": end_date})
        
        print(f"\nTop 10 Products (Last 30 days: {start_date} to {end_date}):")
        print("-" * 80)
        for row in result:
            print(f"  {row.product_name:40} | Revenue: ${row.total_revenue:>12,.2f} | "
                  f"Quantity: {row.total_quantity_sold:>6} | Transactions: {row.transaction_count:>5}")


def example_get_sales_trends():
    """Example: Get sales trends using stored procedure function."""
    print("\n" + "="*60)
    print("Example 2: Get Sales Trends (Monthly)")
    print("="*60)
    
    engine = get_postgres_engine()
    
    # Get monthly trends for the last quarter
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM get_sales_trends(:start_date, :end_date, 'monthly', NULL)
        """), {"start_date": start_date, "end_date": end_date})
        
        print(f"\nMonthly Sales Trends (Last 90 days: {start_date} to {end_date}):")
        print("-" * 80)
        for row in result:
            print(f"  {row.period_label:15} | Revenue: ${row.total_revenue:>12,.2f} | "
                  f"Transactions: {row.transaction_count:>8} | Avg Transaction: ${row.avg_transaction_amount:>10,.2f}")


def example_get_sales_by_category():
    """Example: Get sales by category using stored procedure function."""
    print("\n" + "="*60)
    print("Example 3: Get Sales by Category")
    print("="*60)
    
    engine = get_postgres_engine()
    
    # Get category breakdown for current month
    start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM get_sales_by_category(:start_date, :end_date, NULL)
        """), {"start_date": start_date, "end_date": end_date})
        
        print(f"\nSales by Category (Current Month: {start_date} to {end_date}):")
        print("-" * 80)
        for row in result:
            print(f"  {row.category:30} | Revenue: ${row.total_revenue:>12,.2f} | "
                  f"Market Share: {row.revenue_percentage:>5.2f}% | Products: {row.unique_products:>4}")


def example_get_retailer_performance():
    """Example: Get retailer performance comparison."""
    print("\n" + "="*60)
    print("Example 4: Get Retailer Performance Comparison")
    print("="*60)
    
    engine = get_postgres_engine()
    
    # Get performance for last 30 days
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM get_retailer_performance(:start_date, :end_date)
        """), {"start_date": start_date, "end_date": end_date})
        
        print(f"\nRetailer Performance (Last 30 days: {start_date} to {end_date}):")
        print("-" * 80)
        for row in result:
            print(f"  {row.retailer_name:20} | Revenue: ${row.total_revenue:>12,.2f} | "
                  f"Market Share: {row.revenue_percentage:>5.2f}% | "
                  f"Avg Transaction: ${row.avg_transaction_amount:>10,.2f}")


def example_get_recent_sales():
    """Example: Get recent sales using stored procedure function."""
    print("\n" + "="*60)
    print("Example 5: Get Recent Sales (Last 7 Days)")
    print("="*60)
    
    engine = get_postgres_engine()
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM get_recent_sales(7, NULL)
        """))
        
        print("\nDaily Sales Summary (Last 7 Days):")
        print("-" * 80)
        for row in result:
            print(f"  {row.date} | Revenue: ${row.total_revenue:>12,.2f} | "
                  f"Quantity: {row.total_quantity:>8} | "
                  f"Transactions: {row.transaction_count:>6} | "
                  f"Avg Transaction: ${row.avg_transaction_amount:>10,.2f}")


def example_check_data_quality():
    """Example: Check data quality using stored procedure."""
    print("\n" + "="*60)
    print("Example 6: Check Data Quality")
    print("="*60)
    
    engine = get_postgres_engine()
    
    # Check data quality for last 7 days
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    with engine.begin() as conn:
        # Call the procedure (it uses RAISE NOTICE, so output goes to logs)
        conn.execute(text("""
            CALL check_data_quality(:start_date, :end_date)
        """), {"start_date": start_date, "end_date": end_date})
        
    # Get structured quality summary
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM get_data_quality_summary(:start_date, :end_date)
        """), {"start_date": start_date, "end_date": end_date})
        
        print(f"\nData Quality Summary (Last 7 days: {start_date} to {end_date}):")
        print("-" * 80)
        for row in result:
            percentage = f" ({row.metric_percentage:.2f}%)" if row.metric_percentage else ""
            print(f"  {row.metric_name:30} | Value: {row.metric_value:>12,}{percentage}")


def example_refresh_materialized_view():
    """Example: Refresh a single materialized view using stored procedure."""
    print("\n" + "="*60)
    print("Example 7: Refresh Materialized View (via Stored Procedure)")
    print("="*60)
    
    engine = get_postgres_engine()
    
    view_name = 'mv_daily_sales_summary'
    
    print(f"\nRefreshing materialized view: {view_name}")
    with engine.begin() as conn:
        conn.execute(text("CALL refresh_materialized_view(:view_name)"), {"view_name": view_name})
    
    print(f"✅ Successfully refreshed {view_name}")


def example_get_database_statistics():
    """Example: Get database statistics using stored procedure."""
    print("\n" + "="*60)
    print("Example 8: Get Database Statistics")
    print("="*60)
    
    engine = get_postgres_engine()
    
    # Call the procedure (it uses RAISE NOTICE, so output goes to logs)
    with engine.begin() as conn:
        conn.execute(text("CALL get_database_statistics()"))
    
    print("\n✅ Database statistics retrieved (check logs for detailed output)")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("STORED PROCEDURES USAGE EXAMPLES")
    print("="*60)
    print("\nThis script demonstrates how to use stored procedures and functions")
    print("available in the retail analytics data warehouse.")
    
    try:
        # Run examples
        example_get_top_products()
        example_get_sales_trends()
        example_get_sales_by_category()
        example_get_retailer_performance()
        example_get_recent_sales()
        example_check_data_quality()
        example_get_database_statistics()
        # Note: Refresh example commented out to avoid unnecessary refreshes during demo
        # example_refresh_materialized_view()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

