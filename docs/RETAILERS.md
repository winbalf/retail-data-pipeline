# Simulated Retailer Systems

This document describes the 3 simulated retailer systems that provide data to the pipeline.

## Overview

Each retailer system consists of:
- **PostgreSQL 14 Database**: Stores the retailer's sales data
- **Flask API**: Exposes REST endpoints to query sales data
- **Sample Data**: Pre-populated with realistic sales transactions

## Retailer 1

### Database Schema
- **Table**: `sales`
- **Key Columns**:
  - `order_id` (VARCHAR) - Unique order identifier
  - `order_date` (TIMESTAMP) - Transaction timestamp
  - `customer_id` (VARCHAR) - Customer identifier
  - `store_id` (VARCHAR) - Store identifier
  - `sku` (VARCHAR) - Product SKU
  - `product_name` (VARCHAR) - Product name
  - `category` (VARCHAR) - Product category
  - `quantity` (INTEGER) - Quantity sold
  - `price` (DECIMAL) - Unit price
  - `total` (DECIMAL) - Total amount
  - **Extra Columns**:
    - `discount_percentage` (DECIMAL) - Discount applied
    - `payment_method` (VARCHAR) - Payment method used

### API Endpoints
- **GET** `/health` - Health check
- **GET** `/sales` - Get sales data
  - Query params: `start_date`, `end_date` (YYYY-MM-DD)
  - Auth: Bearer token in `Authorization` header
  - Response: `{"data": [...], "count": N, "retailer": "retailer_1"}`

### Access
- **API**: http://localhost:5001
- **Database**: localhost:5433
- **API Key**: `retailer1_api_key_123`

## Retailer 2

### Database Schema
- **Table**: `transactions`
- **Key Columns**:
  - `transaction_number` (VARCHAR) - Unique transaction ID
  - `date` (TIMESTAMP) - Transaction timestamp
  - `member_id` (VARCHAR) - Member/customer ID
  - `location_id` (VARCHAR) - Store location ID
  - `item_code` (VARCHAR) - Product item code
  - `item_name` (VARCHAR) - Product name
  - `department` (VARCHAR) - Product department
  - `qty` (INTEGER) - Quantity sold
  - `unit_cost` (DECIMAL) - Unit cost
  - `amount` (DECIMAL) - Total amount
  - **Extra Columns**:
    - `tax_amount` (DECIMAL) - Tax amount
    - `loyalty_points_earned` (INTEGER) - Loyalty points
    - `promotion_code` (VARCHAR) - Promotion code
    - `sales_rep_id` (VARCHAR) - Sales representative ID

### API Endpoints
- **GET** `/health` - Health check
- **GET** `/transactions` - Get transaction data
  - Query params: `from`, `to` (YYYY-MM-DD)
  - Auth: API key in `X-API-Key` header
  - Response: `{"transactions": [...], "count": N, "retailer": "retailer_2"}`

### Access
- **API**: http://localhost:5002
- **Database**: localhost:5434
- **API Key**: `retailer2_api_key_123`

## Retailer 3

### Database Schema
- **Table**: `purchases`
- **Key Columns**:
  - `sale_id` (VARCHAR) - Unique sale identifier
  - `timestamp` (TIMESTAMP) - Transaction timestamp
  - `buyer_id` (VARCHAR) - Buyer/customer ID
  - `outlet_id` (VARCHAR) - Outlet/store ID
  - `product_code` (VARCHAR) - Product code
  - `name` (VARCHAR) - Product name
  - `type` (VARCHAR) - Product type
  - `count` (INTEGER) - Quantity sold
  - `price_per_unit` (DECIMAL) - Price per unit
  - `revenue` (DECIMAL) - Total revenue
  - **Extra Columns**:
    - `shipping_cost` (DECIMAL) - Shipping cost
    - `warranty_months` (INTEGER) - Warranty period
    - `return_policy_days` (INTEGER) - Return policy
    - `supplier_id` (VARCHAR) - Supplier identifier

### API Endpoints
- **GET** `/health` - Health check
- **POST** `/sales/query` - Query sales data
  - Body: `{"dateFrom": "YYYY-MM-DD", "dateTo": "YYYY-MM-DD"}`
  - Auth: API key in `apikey` header
  - Response: `{"results": [...], "count": N, "retailer": "retailer_3"}`

### Access
- **API**: http://localhost:5003
- **Database**: localhost:5435
- **API Key**: `retailer3_api_key_123`

## Data Differences Summary

| Aspect | Retailer 1 | Retailer 2 | Retailer 3 |
|--------|-----------|-----------|-----------|
| Table Name | `sales` | `transactions` | `purchases` |
| Transaction ID | `order_id` | `transaction_number` | `sale_id` |
| Date Column | `order_date` | `date` | `timestamp` |
| Customer ID | `customer_id` | `member_id` | `buyer_id` |
| Store ID | `store_id` | `location_id` | `outlet_id` |
| Product ID | `sku` | `item_code` | `product_code` |
| Product Name | `product_name` | `item_name` | `name` |
| Category | `category` | `department` | `type` |
| Quantity | `quantity` | `qty` | `count` |
| Price | `price` | `unit_cost` | `price_per_unit` |
| Total | `total` | `amount` | `revenue` |
| Extra Fields | discount_percentage, payment_method | tax_amount, loyalty_points, promotion_code, sales_rep_id | shipping_cost, warranty_months, return_policy_days, supplier_id |

## Testing the APIs

### Retailer 1
```bash
curl -H "Authorization: Bearer retailer1_api_key_123" \
  "http://localhost:5001/sales?start_date=2024-01-15&end_date=2024-01-15"
```

### Retailer 2
```bash
curl -H "X-API-Key: retailer2_api_key_123" \
  "http://localhost:5002/transactions?from=2024-01-15&to=2024-01-15"
```

### Retailer 3
```bash
curl -X POST -H "apikey: retailer3_api_key_123" \
  -H "Content-Type: application/json" \
  -d '{"dateFrom": "2024-01-15", "dateTo": "2024-01-15"}' \
  "http://localhost:5003/sales/query"
```

## Database Access

### Retailer 1 Database
```bash
docker-compose exec retailer1-postgres psql -U retailer1_user -d retailer1_db
```

### Retailer 2 Database
```bash
docker-compose exec retailer2-postgres psql -U retailer2_user -d retailer2_db
```

### Retailer 3 Database
```bash
docker-compose exec retailer3-postgres psql -U retailer3_user -d retailer3_db
```

## Sample Queries

### Count records in each retailer
```sql
-- Retailer 1
SELECT COUNT(*) FROM sales;

-- Retailer 2
SELECT COUNT(*) FROM transactions;

-- Retailer 3
SELECT COUNT(*) FROM purchases;
```

### View sample data
```sql
-- Retailer 1
SELECT * FROM sales LIMIT 5;

-- Retailer 2
SELECT * FROM transactions LIMIT 5;

-- Retailer 3
SELECT * FROM purchases LIMIT 5;
```

