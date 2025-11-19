#!/bin/bash
# Script to add sample data for additional dates to retailer databases
# This allows testing the pipeline with dates other than 2024-01-15

DATE=${1:-2024-01-16}  # Default to 2024-01-16 if not provided

echo "Adding sample data for date: $DATE"
echo ""

# Retailer 1 - Add sample data
echo "Adding data to Retailer 1..."
docker-compose exec -T retailer1-postgres psql -U retailer1_user -d retailer1_db <<EOF
INSERT INTO sales (order_id, order_date, customer_id, store_id, sku, product_name, category, quantity, price, total, discount_percentage, payment_method) VALUES
('ORD-001-$DATE', '$DATE 10:30:00', 'CUST-001', 'STORE-001', 'SKU-1001', 'Wireless Headphones', 'Electronics', 2, 49.99, 99.98, 0.00, 'Credit Card'),
('ORD-002-$DATE', '$DATE 11:15:00', 'CUST-002', 'STORE-001', 'SKU-2001', 'Running Shoes', 'Footwear', 1, 89.99, 89.99, 10.00, 'Debit Card'),
('ORD-003-$DATE', '$DATE 12:00:00', 'CUST-003', 'STORE-002', 'SKU-3001', 'Coffee Maker', 'Appliances', 1, 129.99, 129.99, 0.00, 'Cash')
ON CONFLICT (order_id) DO NOTHING;
EOF

# Retailer 2 - Add sample data
echo "Adding data to Retailer 2..."
docker-compose exec -T retailer2-postgres psql -U retailer2_user -d retailer2_db <<EOF
INSERT INTO transactions (transaction_number, date, member_id, location_id, item_code, item_name, department, qty, unit_cost, amount, tax_amount, loyalty_points_earned, promotion_code, sales_rep_id) VALUES
('TXN-$DATE-001', '$DATE 10:30:00', 'MEM-001', 'LOC-001', 'ITEM-1001', 'Wireless Headphones', 'Electronics', 2, 49.99, 99.98, 8.00, 10, NULL, 'REP-001'),
('TXN-$DATE-002', '$DATE 11:15:00', 'MEM-002', 'LOC-001', 'ITEM-2001', 'Running Shoes', 'Footwear', 1, 89.99, 89.99, 7.20, 9, 'PROMO-10', 'REP-002'),
('TXN-$DATE-003', '$DATE 12:00:00', 'MEM-003', 'LOC-002', 'ITEM-3001', 'Coffee Maker', 'Appliances', 1, 129.99, 129.99, 10.40, 13, NULL, 'REP-001')
ON CONFLICT (transaction_number) DO NOTHING;
EOF

# Retailer 3 - Add sample data
echo "Adding data to Retailer 3..."
docker-compose exec -T retailer3-postgres psql -U retailer3_user -d retailer3_db <<EOF
INSERT INTO purchases (sale_id, timestamp, buyer_id, outlet_id, product_code, name, type, count, price_per_unit, revenue, shipping_cost, warranty_months, return_policy_days, supplier_id) VALUES
('SALE-$DATE-001', '$DATE 10:30:00', 'BUY-001', 'OUT-001', 'PROD-1001', 'Wireless Headphones', 'Electronics', 2, 49.99, 99.98, 5.99, 12, 30, 'SUP-001'),
('SALE-$DATE-002', '$DATE 11:15:00', 'BUY-002', 'OUT-001', 'PROD-2001', 'Running Shoes', 'Footwear', 1, 89.99, 89.99, 4.99, 0, 30, 'SUP-002'),
('SALE-$DATE-003', '$DATE 12:00:00', 'BUY-003', 'OUT-002', 'PROD-3001', 'Coffee Maker', 'Appliances', 1, 129.99, 129.99, 7.99, 12, 30, 'SUP-001')
ON CONFLICT (sale_id) DO NOTHING;
EOF

echo ""
echo "✅ Sample data added for date: $DATE"
echo ""
echo "You can now test ingestion with:"
echo "  make test-ingestion DATE=$DATE"
echo ""
echo "Or trigger the DAG in Airflow UI for this date"

