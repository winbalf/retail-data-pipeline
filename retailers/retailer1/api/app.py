"""
Retailer 1 API - Flask application to expose sales data
"""
from flask import Flask, jsonify, request
import psycopg2
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Database connection
def get_db_connection():
    """Get PostgreSQL connection for Retailer 1."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'retailer1_db'),
        user=os.getenv('POSTGRES_USER', 'retailer1_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'retailer1_pass')
    )

def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        expected_key = os.getenv('RETAILER_1_API_KEY', 'retailer1_api_key_123')
        
        if api_key != expected_key:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'retailer': 'retailer_1'})

@app.route('/sales', methods=['GET'])
@require_api_key
def get_sales():
    """
    Get sales data with optional date filtering.
    Query params: start_date, end_date (YYYY-MM-DD format)
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "SELECT order_id, order_date, customer_id, store_id, sku, product_name, category, quantity, price, total, discount_percentage, payment_method FROM sales WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND DATE(order_date) >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND DATE(order_date) <= %s"
            params.append(end_date)
        
        query += " ORDER BY order_date"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        sales_data = []
        for row in rows:
            sales_data.append({
                'order_id': row[0],
                'order_date': row[1].isoformat() if row[1] else None,
                'customer_id': row[2],
                'store_id': row[3],
                'sku': row[4],
                'product_name': row[5],
                'category': row[6],
                'quantity': row[7],
                'price': float(row[8]),
                'total': float(row[9]),
                'discount_percentage': float(row[10]) if row[10] else 0.0,
                'payment_method': row[11]
            })
        
        return jsonify({
            'data': sales_data,
            'count': len(sales_data),
            'retailer': 'retailer_1'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)

