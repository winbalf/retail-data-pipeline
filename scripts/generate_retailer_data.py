#!/usr/bin/env python3
"""
Generate random sample data for all retailers with:
- 10 records on the 1st of each month
- 15 records on the 15th of each month
- From 2024-01-01 to 2025-12-31 (600 records total per retailer)
"""

import random
from datetime import datetime, timedelta
from calendar import monthrange

def generate_monthly_dates(start_year=2024, start_month=1, end_year=2025, end_month=12, 
                           records_first_day=10, records_15th_day=15):
    """
    Generate dates with:
    - 10 records on the 1st of each month
    - 15 records on the 15th of each month
    Returns a list of timestamps sorted chronologically.
    """
    dates = []
    current_year = start_year
    current_month = start_month
    
    while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
        # Generate 10 records on the 1st of the month
        for _ in range(records_first_day):
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            timestamp = datetime(current_year, current_month, 1, hour, minute, 0)
            dates.append(timestamp)
        
        # Generate 15 records on the 15th of the month
        # Check if the month has at least 15 days
        _, days_in_month = monthrange(current_year, current_month)
        if days_in_month >= 15:
            for _ in range(records_15th_day):
                hour = random.randint(8, 20)
                minute = random.randint(0, 59)
                timestamp = datetime(current_year, current_month, 15, hour, minute, 0)
                dates.append(timestamp)
        
        # Move to next month
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    
    # Sort all dates chronologically
    dates.sort()
    return dates

# Product data for each retailer
retailer1_products = [
    ('SKU-1001', 'Wireless Headphones', 'Electronics', 49.99),
    ('SKU-2001', 'Running Shoes', 'Footwear', 89.99),
    ('SKU-3001', 'Coffee Maker', 'Appliances', 129.99),
    ('SKU-1002', 'USB Cable', 'Electronics', 9.99),
    ('SKU-4001', 'Yoga Mat', 'Fitness', 24.99),
    ('SKU-2002', 'Sneakers', 'Footwear', 79.99),
    ('SKU-3002', 'Blender', 'Appliances', 59.99),
    ('SKU-1003', 'Phone Case', 'Electronics', 12.99),
    ('SKU-5001', 'Water Bottle', 'Fitness', 15.99),
    ('SKU-2003', 'Sandals', 'Footwear', 34.99),
    ('SKU-1004', 'Laptop', 'Electronics', 899.99),
    ('SKU-3003', 'Microwave', 'Appliances', 149.99),
    ('SKU-4002', 'Dumbbells', 'Fitness', 39.99),
    ('SKU-2004', 'Boots', 'Footwear', 119.99),
    ('SKU-1005', 'Tablet', 'Electronics', 299.99),
]

retailer2_products = [
    ('ITEM-1001', 'Laptop Computer', 'Electronics', 899.99),
    ('ITEM-2001', 'Office Chair', 'Furniture', 199.99),
    ('ITEM-3001', 'Desk Lamp', 'Home & Garden', 29.99),
    ('ITEM-1002', 'Wireless Mouse', 'Electronics', 24.99),
    ('ITEM-4001', 'Monitor Stand', 'Electronics', 49.99),
    ('ITEM-2002', 'Bookshelf', 'Furniture', 149.99),
    ('ITEM-5001', 'Plant Pot', 'Home & Garden', 12.99),
    ('ITEM-1003', 'Keyboard', 'Electronics', 79.99),
    ('ITEM-3002', 'Wall Clock', 'Home & Garden', 39.99),
    ('ITEM-2003', 'Coffee Table', 'Furniture', 249.99),
    ('ITEM-1004', 'Monitor', 'Electronics', 299.99),
    ('ITEM-2004', 'Dining Table', 'Furniture', 399.99),
    ('ITEM-3003', 'Vase', 'Home & Garden', 19.99),
    ('ITEM-1005', 'Webcam', 'Electronics', 59.99),
    ('ITEM-2005', 'Sofa', 'Furniture', 599.99),
]

retailer3_products = [
    ('PROD-1001', 'Smartphone', 'Electronics', 699.99),
    ('PROD-2001', 'Tablet', 'Electronics', 399.99),
    ('PROD-3001', 'Smart Watch', 'Electronics', 199.99),
    ('PROD-4001', 'Laptop Bag', 'Accessories', 49.99),
    ('PROD-1002', 'Phone Charger', 'Accessories', 19.99),
    ('PROD-5001', 'Bluetooth Speaker', 'Electronics', 79.99),
    ('PROD-2002', 'Tablet Stand', 'Accessories', 29.99),
    ('PROD-3002', 'Fitness Tracker', 'Electronics', 89.99),
    ('PROD-6001', 'Camera Lens', 'Electronics', 299.99),
    ('PROD-4002', 'USB Hub', 'Accessories', 24.99),
    ('PROD-1003', 'Power Bank', 'Accessories', 34.99),
    ('PROD-2003', 'E-Reader', 'Electronics', 129.99),
    ('PROD-3003', 'Gaming Mouse', 'Electronics', 69.99),
    ('PROD-4003', 'Laptop Sleeve', 'Accessories', 29.99),
    ('PROD-5002', 'Headphones', 'Electronics', 149.99),
]

payment_methods = ['Credit Card', 'Debit Card', 'Cash', 'PayPal', 'Apple Pay']
promotion_codes = ['PROMO-5', 'PROMO-10', 'PROMO-15', None, None, None]
suppliers = ['SUP-001', 'SUP-002', 'SUP-003']
sales_reps = ['REP-001', 'REP-002', 'REP-003']

def generate_retailer1_data(dates):
    """Generate data for Retailer 1"""
    lines = []
    for i, date in enumerate(dates, 1):
        sku, product_name, category, base_price = random.choice(retailer1_products)
        order_id = f'ORD-{i:03d}-{date.strftime("%Y-%m-%d")}'
        customer_id = f'CUST-{random.randint(1, 50):03d}'
        store_id = f'STORE-{random.randint(1, 5):03d}'
        quantity = random.randint(1, 5)
        discount = random.choice([0, 0, 0, 5, 10, 15])  # More likely no discount
        price = round(base_price * (1 - discount / 100), 2)
        total = round(price * quantity, 2)
        payment_method = random.choice(payment_methods)
        
        date_str = date.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"('{order_id}', '{date_str}', '{customer_id}', '{store_id}', '{sku}', '{product_name}', '{category}', {quantity}, {price:.2f}, {total:.2f}, {discount:.2f}, '{payment_method}')")
    return ',\n'.join(lines)

def generate_retailer2_data(dates):
    """Generate data for Retailer 2"""
    lines = []
    for i, date in enumerate(dates, 1):
        item_code, item_name, department, base_cost = random.choice(retailer2_products)
        txn_num = f'TXN-2024-{i:03d}-{random.randint(1, 999):03d}'
        member_id = f'MEM-{random.randint(1, 50):03d}'
        location_id = f'LOC-{random.randint(1, 5):03d}'
        qty = random.randint(1, 3)
        unit_cost = base_cost
        amount = round(unit_cost * qty, 2)
        tax_amount = round(amount * 0.08, 2)  # 8% tax
        loyalty_points = int(amount / 10)  # 1 point per $10
        promo = random.choice(promotion_codes)
        promo_str = f"'{promo}'" if promo else 'NULL'
        sales_rep = random.choice(sales_reps)
        
        date_str = date.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"('{txn_num}', '{date_str}', '{member_id}', '{location_id}', '{item_code}', '{item_name}', '{department}', {qty}, {unit_cost:.2f}, {amount:.2f}, {tax_amount:.2f}, {loyalty_points}, {promo_str}, '{sales_rep}')")
    return ',\n'.join(lines)

def generate_retailer3_data(dates):
    """Generate data for Retailer 3"""
    lines = []
    for i, date in enumerate(dates, 1):
        product_code, name, type_name, base_price = random.choice(retailer3_products)
        sale_id = f'SALE-2024-{i:03d}'
        buyer_id = f'BUY-{random.randint(1, 50):03d}'
        outlet_id = f'OUT-{random.randint(1, 5):03d}'
        count = random.randint(1, 3)
        price_per_unit = base_price
        revenue = round(price_per_unit * count, 2)
        shipping_cost = round(random.uniform(3.99, 9.99), 2)
        warranty = random.choice([0, 6, 12, 24])
        return_policy = random.choice([30, 60, 90])
        supplier_id = random.choice(suppliers)
        
        date_str = date.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"('{sale_id}', '{date_str}', '{buyer_id}', '{outlet_id}', '{product_code}', '{name}', '{type_name}', {count}, {price_per_unit:.2f}, {revenue:.2f}, {shipping_cost:.2f}, {warranty}, {return_policy}, '{supplier_id}')")
    return ',\n'.join(lines)

# Generate dates: 10 records on 1st + 15 records on 15th per month from 2024-01 to 2025-12 (600 records total)
random.seed(42)  # For reproducibility
dates = generate_monthly_dates(start_year=2024, start_month=1, end_year=2025, end_month=12, 
                               records_first_day=10, records_15th_day=15)

# Generate SQL for each retailer
retailer1_sql = generate_retailer1_data(dates)
retailer2_sql = generate_retailer2_data(dates)
retailer3_sql = generate_retailer3_data(dates)

# Write Retailer 1 SQL file
retailer1_content = """-- Retailer 1 Database Schema
-- This retailer uses a "sales" table with order-based structure

CREATE TABLE IF NOT EXISTS sales (
    order_id VARCHAR(50) PRIMARY KEY,
    order_date TIMESTAMP NOT NULL,
    customer_id VARCHAR(50),
    store_id VARCHAR(50),
    sku VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    discount_percentage DECIMAL(5, 2) DEFAULT 0,
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_order_date ON sales(order_date);
CREATE INDEX idx_sales_customer_id ON sales(customer_id);
CREATE INDEX idx_sales_store_id ON sales(store_id);
CREATE INDEX idx_sales_sku ON sales(sku);

-- Insert sample data (600 records: 10 on 1st + 15 on 15th per month from 2024-01 to 2025-12)
INSERT INTO sales (order_id, order_date, customer_id, store_id, sku, product_name, category, quantity, price, total, discount_percentage, payment_method) VALUES
""" + retailer1_sql + """
ON CONFLICT (order_id) DO NOTHING;

"""

# Write Retailer 2 SQL file
retailer2_content = """-- Retailer 2 Database Schema
-- This retailer uses a "transactions" table with transaction-based structure
-- Different column names and some extra fields

CREATE TABLE IF NOT EXISTS transactions (
    transaction_number VARCHAR(50) PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    member_id VARCHAR(50),
    location_id VARCHAR(50),
    item_code VARCHAR(100) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    qty INTEGER NOT NULL,
    unit_cost DECIMAL(10, 2) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    loyalty_points_earned INTEGER DEFAULT 0,
    promotion_code VARCHAR(50),
    sales_rep_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_member_id ON transactions(member_id);
CREATE INDEX idx_transactions_location_id ON transactions(location_id);
CREATE INDEX idx_transactions_item_code ON transactions(item_code);

-- Insert sample data (600 records: 10 on 1st + 15 on 15th per month from 2024-01 to 2025-12)
INSERT INTO transactions (transaction_number, date, member_id, location_id, item_code, item_name, department, qty, unit_cost, amount, tax_amount, loyalty_points_earned, promotion_code, sales_rep_id) VALUES
""" + retailer2_sql + """
ON CONFLICT (transaction_number) DO NOTHING;

"""

# Write Retailer 3 SQL file
retailer3_content = """-- Retailer 3 Database Schema
-- This retailer uses a "purchases" table with purchase-based structure
-- Different column names, types, and extra fields

CREATE TABLE IF NOT EXISTS purchases (
    sale_id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    buyer_id VARCHAR(50),
    outlet_id VARCHAR(50),
    product_code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    count INTEGER NOT NULL,
    price_per_unit DECIMAL(10, 2) NOT NULL,
    revenue DECIMAL(10, 2) NOT NULL,
    shipping_cost DECIMAL(10, 2) DEFAULT 0,
    warranty_months INTEGER DEFAULT 0,
    return_policy_days INTEGER DEFAULT 30,
    supplier_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_purchases_timestamp ON purchases(timestamp);
CREATE INDEX idx_purchases_buyer_id ON purchases(buyer_id);
CREATE INDEX idx_purchases_outlet_id ON purchases(outlet_id);
CREATE INDEX idx_purchases_product_code ON purchases(product_code);

-- Insert sample data (600 records: 10 on 1st + 15 on 15th per month from 2024-01 to 2025-12)
INSERT INTO purchases (sale_id, timestamp, buyer_id, outlet_id, product_code, name, type, count, price_per_unit, revenue, shipping_cost, warranty_months, return_policy_days, supplier_id) VALUES
""" + retailer3_sql + """
ON CONFLICT (sale_id) DO NOTHING;

"""

# Write files
import os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(base_dir, 'retailers/retailer1/database/init_schema.sql'), 'w') as f:
    f.write(retailer1_content)

with open(os.path.join(base_dir, 'retailers/retailer2/database/init_schema.sql'), 'w') as f:
    f.write(retailer2_content)

with open(os.path.join(base_dir, 'retailers/retailer3/database/init_schema.sql'), 'w') as f:
    f.write(retailer3_content)

print("✅ Generated SQL data for all retailers!")
print(f"   Date range: {dates[0].date()} to {dates[-1].date()}")
print(f"   Total records per retailer: {len(dates)} (10 on 1st + 15 on 15th per month × 24 months = 600)")
print(f"   Files updated:")
print(f"   - retailers/retailer1/database/init_schema.sql")
print(f"   - retailers/retailer2/database/init_schema.sql")
print(f"   - retailers/retailer3/database/init_schema.sql")

