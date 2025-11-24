"""
Example queries demonstrating what you can do with materialized views.
These queries showcase common analytical use cases.
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

import pandas as pd
from sqlalchemy import text
from shared.database import get_postgres_engine

def run_query(query, description):
    """Run a query and display results."""
    print(f"\n{'='*70}")
    print(f"📊 {description}")
    print(f"{'='*70}")
    print(f"\nQuery:\n{query}\n")
    
    engine = get_postgres_engine()
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        print(f"Results ({len(df)} rows):")
        print(df.to_string(index=False))
        if len(df) == 0:
            print("⚠️  No data returned. Make sure views are refreshed and contain data.")
    print()

def example_1_daily_sales_dashboard():
    """Example 1: Daily Sales Dashboard - Last 7 days"""
    query = """
    SELECT 
        date,
        retailer_name,
        total_revenue,
        transaction_count,
        total_quantity,
        avg_unit_price
    FROM mv_daily_sales_summary
    WHERE date >= CURRENT_DATE - INTERVAL '7 days'
    ORDER BY date DESC, total_revenue DESC
    LIMIT 20;
    """
    run_query(query, "Daily Sales Dashboard (Last 7 Days)")

def example_2_top_products():
    """Example 2: Top 10 Products by Revenue"""
    query = """
    SELECT 
        product_name,
        category,
        retailer_name,
        total_revenue,
        total_quantity_sold,
        avg_unit_price
    FROM mv_top_products_by_revenue
    ORDER BY total_revenue DESC
    LIMIT 10;
    """
    run_query(query, "Top 10 Products by Revenue (All Time)")

def example_3_category_performance():
    """Example 3: Monthly Category Performance"""
    query = """
    SELECT 
        year,
        month,
        category,
        retailer_name,
        total_revenue,
        unique_products,
        avg_unit_price
    FROM mv_monthly_sales_by_category
    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
    ORDER BY year DESC, month DESC, total_revenue DESC
    LIMIT 20;
    """
    run_query(query, "Monthly Category Performance (Current Year)")

def example_4_weekly_trends():
    """Example 4: Weekly Sales Trends"""
    query = """
    SELECT 
        year,
        week,
        retailer_name,
        total_revenue,
        avg_transaction_amount,
        days_with_sales,
        week_start_date,
        week_end_date
    FROM mv_weekly_sales_trends
    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
    ORDER BY year DESC, week DESC
    LIMIT 10;
    """
    run_query(query, "Weekly Sales Trends (Current Year)")

def example_5_quarterly_summary():
    """Example 5: Quarterly Summary by Retailer"""
    query = """
    SELECT 
        retailer_name,
        year,
        quarter,
        total_revenue,
        unique_products,
        transaction_count,
        avg_transaction_amount
    FROM mv_quarterly_sales_summary
    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
    ORDER BY retailer_name, quarter;
    """
    run_query(query, "Quarterly Summary by Retailer (Current Year)")

def example_6_product_daily_trends():
    """Example 6: Daily Sales Trends for Top Products"""
    query = """
    WITH top_products AS (
        SELECT product_id, product_name
        FROM mv_top_products_by_revenue
        ORDER BY total_revenue DESC
        LIMIT 5
    )
    SELECT 
        dsp.date,
        tp.product_name,
        dsp.retailer_name,
        dsp.total_revenue,
        dsp.total_quantity_sold,
        dsp.avg_unit_price
    FROM mv_daily_sales_by_product dsp
    JOIN top_products tp ON dsp.product_id = tp.product_id
    WHERE dsp.date >= CURRENT_DATE - INTERVAL '30 days'
    ORDER BY dsp.date DESC, dsp.total_revenue DESC
    LIMIT 20;
    """
    run_query(query, "Daily Sales Trends for Top 5 Products (Last 30 Days)")

def example_7_retailer_comparison():
    """Example 7: Retailer Performance Comparison"""
    query = """
    SELECT 
        retailer_name,
        COUNT(DISTINCT date) as days_active,
        SUM(total_revenue) as total_revenue,
        SUM(transaction_count) as total_transactions,
        AVG(total_revenue) as avg_daily_revenue,
        MAX(total_revenue) as max_daily_revenue
    FROM mv_daily_sales_summary
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY retailer_name
    ORDER BY total_revenue DESC;
    """
    run_query(query, "Retailer Performance Comparison (Last 30 Days)")

def example_8_category_growth():
    """Example 8: Category Growth Analysis"""
    query = """
    SELECT 
        category,
        retailer_name,
        SUM(CASE WHEN month <= 3 THEN total_revenue ELSE 0 END) as q1_revenue,
        SUM(CASE WHEN month > 3 AND month <= 6 THEN total_revenue ELSE 0 END) as q2_revenue,
        SUM(CASE WHEN month > 6 AND month <= 9 THEN total_revenue ELSE 0 END) as q3_revenue,
        SUM(CASE WHEN month > 9 THEN total_revenue ELSE 0 END) as q4_revenue,
        SUM(total_revenue) as total_revenue
    FROM mv_monthly_sales_by_category
    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
    GROUP BY category, retailer_name
    HAVING SUM(total_revenue) > 0
    ORDER BY total_revenue DESC
    LIMIT 15;
    """
    run_query(query, "Category Growth Analysis by Quarter (Current Year)")

def main():
    """Run all example queries."""
    print("=" * 70)
    print("Materialized Views - Example Queries")
    print("=" * 70)
    print("\nThis script demonstrates various analytical queries you can run")
    print("on the materialized views. Each example shows a different use case.\n")
    
    examples = [
        ("Daily Sales Dashboard", example_1_daily_sales_dashboard),
        ("Top Products", example_2_top_products),
        ("Category Performance", example_3_category_performance),
        ("Weekly Trends", example_4_weekly_trends),
        ("Quarterly Summary", example_5_quarterly_summary),
        ("Product Daily Trends", example_6_product_daily_trends),
        ("Retailer Comparison", example_7_retailer_comparison),
        ("Category Growth", example_8_category_growth),
    ]
    
    print("Available Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print("  0. Run all examples")
    print()
    
    try:
        choice = input("Enter example number (or press Enter for all): ").strip()
        
        if choice == "" or choice == "0":
            # Run all
            for name, func in examples:
                try:
                    func()
                except Exception as e:
                    print(f"❌ Error running {name}: {e}\n")
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                name, func = examples[idx]
                func()
            else:
                print("Invalid choice")
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

