-- Create star schema for retail analytics
-- This script initializes the data warehouse with fact and dimension tables

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    week INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Product
CREATE TABLE IF NOT EXISTS dim_product (
    product_id SERIAL PRIMARY KEY,
    product_sku VARCHAR(100) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Customer
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id SERIAL PRIMARY KEY,
    customer_external_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Store
CREATE TABLE IF NOT EXISTS dim_store (
    store_id SERIAL PRIMARY KEY,
    store_external_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Retailer
CREATE TABLE IF NOT EXISTS dim_retailer (
    retailer_id SERIAL PRIMARY KEY,
    retailer_code VARCHAR(50) UNIQUE NOT NULL,
    retailer_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Sales
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id BIGSERIAL PRIMARY KEY,
    date_id INTEGER NOT NULL REFERENCES dim_date(date_id),
    product_id INTEGER NOT NULL REFERENCES dim_product(product_id),
    customer_id INTEGER REFERENCES dim_customer(customer_id),
    store_id INTEGER REFERENCES dim_store(store_id),
    retailer_id INTEGER NOT NULL REFERENCES dim_retailer(retailer_id),
    transaction_id VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(transaction_id, product_id, retailer_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_fact_sales_date_id ON fact_sales(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product_id ON fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_id ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_store_id ON fact_sales(store_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_retailer_id ON fact_sales(retailer_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_transaction_id ON fact_sales(transaction_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_created_at ON fact_sales(created_at);

-- Insert initial retailer data
INSERT INTO dim_retailer (retailer_code, retailer_name) VALUES
    ('retailer_1', 'Retailer 1'),
    ('retailer_2', 'Retailer 2'),
    ('retailer_3', 'Retailer 3')
ON CONFLICT (retailer_code) DO NOTHING;

