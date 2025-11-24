"""
Visualization tool for materialized views.
Creates charts and graphs to visualize sales data.
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

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib not installed. Install with: pip install matplotlib")
    print("   Charts will be displayed as tables instead.\n")

def create_output_dir():
    """Create output directory for charts."""
    # Determine base path based on execution context
    if '/opt/airflow' in os.path.abspath(__file__):
        # Running in Docker - use /tmp which is always writable, then copy to mounted volume
        # Try to use the mounted volume first, fallback to /tmp if permission denied
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "charts")
        try:
            os.makedirs(output_dir, exist_ok=True)
            # Test write permissions
            test_file = os.path.join(output_dir, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except (PermissionError, OSError):
                # Fallback to /tmp
                output_dir = '/tmp/materialized_views_charts'
                os.makedirs(output_dir, exist_ok=True)
                print(f"⚠️  Using /tmp for charts due to permission restrictions")
                print(f"   Charts will be saved to: {output_dir}")
        except (PermissionError, OSError):
            # Fallback to /tmp
            output_dir = '/tmp/materialized_views_charts'
            os.makedirs(output_dir, exist_ok=True)
            print(f"⚠️  Using /tmp for charts due to permission restrictions")
            print(f"   Charts will be saved to: {output_dir}")
    else:
        # Running locally - use project root
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_path, "materialized_views", "charts")
        os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def plot_daily_sales_trend(output_dir):
    """Plot daily sales trends."""
    query = """
    SELECT 
        date,
        retailer_name,
        total_revenue
    FROM mv_daily_sales_summary
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    ORDER BY date, retailer_name;
    """
    
    engine = get_postgres_engine()
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    if df.empty:
        print("⚠️  No data for daily sales trend")
        return
    
    if MATPLOTLIB_AVAILABLE:
        df['date'] = pd.to_datetime(df['date'])
        pivot_df = df.pivot(index='date', columns='retailer_name', values='total_revenue')
        
        plt.figure(figsize=(12, 6))
        for retailer in pivot_df.columns:
            plt.plot(pivot_df.index, pivot_df[retailer], marker='o', label=retailer, linewidth=2)
        
        plt.title('Daily Sales Revenue Trend (Last 30 Days)', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Revenue ($)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        filepath = os.path.join(output_dir, 'daily_sales_trend.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"✅ Saved: {filepath}")
        plt.close()
    else:
        print("\nDaily Sales Trend (Last 30 Days):")
        print(df.to_string(index=False))

def plot_top_products(output_dir):
    """Plot top products by revenue."""
    query = """
    SELECT 
        product_name,
        total_revenue,
        retailer_name
    FROM mv_top_products_by_revenue
    ORDER BY total_revenue DESC
    LIMIT 10;
    """
    
    engine = get_postgres_engine()
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    if df.empty:
        print("⚠️  No data for top products")
        return
    
    if MATPLOTLIB_AVAILABLE:
        # Truncate long product names
        df['product_name_short'] = df['product_name'].apply(
            lambda x: x[:30] + '...' if len(x) > 30 else x
        )
        
        plt.figure(figsize=(12, 8))
        colors = plt.cm.Set3(range(len(df)))
        bars = plt.barh(range(len(df)), df['total_revenue'], color=colors)
        plt.yticks(range(len(df)), df['product_name_short'])
        plt.xlabel('Total Revenue ($)', fontsize=12)
        plt.title('Top 10 Products by Revenue', fontsize=14, fontweight='bold')
        plt.gca().invert_yaxis()
        plt.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (idx, row) in enumerate(df.iterrows()):
            plt.text(row['total_revenue'], i, f"${row['total_revenue']:,.0f}", 
                    va='center', ha='left', fontsize=9)
        
        plt.tight_layout()
        filepath = os.path.join(output_dir, 'top_products.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"✅ Saved: {filepath}")
        plt.close()
    else:
        print("\nTop 10 Products by Revenue:")
        print(df[['product_name', 'total_revenue', 'retailer_name']].to_string(index=False))

def plot_category_performance(output_dir):
    """Plot category performance."""
    query = """
    SELECT 
        category,
        retailer_name,
        SUM(total_revenue) as total_revenue
    FROM mv_monthly_sales_by_category
    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
    GROUP BY category, retailer_name
    HAVING SUM(total_revenue) > 0
    ORDER BY total_revenue DESC
    LIMIT 15;
    """
    
    engine = get_postgres_engine()
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    if df.empty:
        print("⚠️  No data for category performance")
        return
    
    if MATPLOTLIB_AVAILABLE:
        pivot_df = df.pivot(index='category', columns='retailer_name', values='total_revenue').fillna(0)
        pivot_df = pivot_df.sort_values(by=pivot_df.columns[0], ascending=True)
        
        plt.figure(figsize=(12, 8))
        pivot_df.plot(kind='barh', stacked=False, width=0.8)
        plt.title('Category Performance by Retailer (Current Year)', fontsize=14, fontweight='bold')
        plt.xlabel('Total Revenue ($)', fontsize=12)
        plt.ylabel('Category', fontsize=12)
        plt.legend(title='Retailer')
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        filepath = os.path.join(output_dir, 'category_performance.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"✅ Saved: {filepath}")
        plt.close()
    else:
        print("\nCategory Performance (Current Year):")
        print(df.to_string(index=False))

def plot_weekly_trends(output_dir):
    """Plot weekly sales trends."""
    query = """
    SELECT 
        year,
        week,
        retailer_name,
        total_revenue
    FROM mv_weekly_sales_trends
    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
    ORDER BY year, week, retailer_name;
    """
    
    engine = get_postgres_engine()
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    if df.empty:
        print("⚠️  No data for weekly trends")
        return
    
    if MATPLOTLIB_AVAILABLE:
        pivot_df = df.pivot(index='week', columns='retailer_name', values='total_revenue')
        
        plt.figure(figsize=(12, 6))
        for retailer in pivot_df.columns:
            plt.plot(pivot_df.index, pivot_df[retailer], marker='o', label=retailer, linewidth=2)
        
        plt.title('Weekly Sales Trends (Current Year)', fontsize=14, fontweight='bold')
        plt.xlabel('Week Number', fontsize=12)
        plt.ylabel('Revenue ($)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        filepath = os.path.join(output_dir, 'weekly_trends.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"✅ Saved: {filepath}")
        plt.close()
    else:
        print("\nWeekly Sales Trends (Current Year):")
        print(df.to_string(index=False))

def plot_retailer_comparison(output_dir):
    """Plot retailer comparison."""
    query = """
    SELECT 
        retailer_name,
        SUM(total_revenue) as total_revenue,
        SUM(transaction_count) as total_transactions,
        AVG(total_revenue) as avg_daily_revenue
    FROM mv_daily_sales_summary
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY retailer_name
    ORDER BY total_revenue DESC;
    """
    
    engine = get_postgres_engine()
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    if df.empty:
        print("⚠️  No data for retailer comparison")
        return
    
    if MATPLOTLIB_AVAILABLE:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Revenue comparison
        ax1.bar(df['retailer_name'], df['total_revenue'], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        ax1.set_title('Total Revenue (Last 30 Days)', fontweight='bold')
        ax1.set_ylabel('Revenue ($)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Transaction count comparison
        ax2.bar(df['retailer_name'], df['total_transactions'], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        ax2.set_title('Total Transactions (Last 30 Days)', fontweight='bold')
        ax2.set_ylabel('Transaction Count')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        filepath = os.path.join(output_dir, 'retailer_comparison.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"✅ Saved: {filepath}")
        plt.close()
    else:
        print("\nRetailer Comparison (Last 30 Days):")
        print(df.to_string(index=False))

def main():
    """Generate all visualizations."""
    print("=" * 70)
    print("Materialized Views Visualization Tool")
    print("=" * 70)
    print()
    
    output_dir = create_output_dir()
    print(f"📁 Output directory: {output_dir}\n")
    
    visualizations = [
        ("Daily Sales Trend", plot_daily_sales_trend),
        ("Top Products", plot_top_products),
        ("Category Performance", plot_category_performance),
        ("Weekly Trends", plot_weekly_trends),
        ("Retailer Comparison", plot_retailer_comparison),
    ]
    
    print("Generating visualizations...\n")
    for name, func in visualizations:
        try:
            print(f"📊 Creating: {name}...")
            func(output_dir)
        except Exception as e:
            print(f"❌ Error creating {name}: {e}\n")
    
    print("\n" + "=" * 70)
    print("✅ Visualization complete!")
    print(f"📁 Charts saved to: {output_dir}/")
    if '/tmp' in output_dir:
        print(f"\n⚠️  Note: Charts are in /tmp. To access them from host:")
        print(f"   docker cp retail_airflow_scheduler:{output_dir} ./materialized_views/charts")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

