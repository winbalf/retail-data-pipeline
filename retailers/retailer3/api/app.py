"""
Retailer 3 API - Flask application to expose purchase data
"""
from flask import Flask, jsonify, request
import psycopg2
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Database connection
def get_db_connection():
    """Get PostgreSQL connection for Retailer 3."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'retailer3_db'),
        user=os.getenv('POSTGRES_USER', 'retailer3_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'retailer3_pass')
    )

def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('apikey', '')
        expected_key = os.getenv('RETAILER_3_API_KEY', 'retailer3_api_key_123')
        
        if api_key != expected_key:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'retailer': 'retailer_3'})

@app.route('/sales/query', methods=['POST'])
@require_api_key
def query_sales():
    """
    Query sales data with optional date filtering.
    POST body: {"dateFrom": "YYYY-MM-DD", "dateTo": "YYYY-MM-DD"}
    """
    data = request.get_json() or {}
    date_from = data.get('dateFrom')
    date_to = data.get('dateTo')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """SELECT sale_id, timestamp, buyer_id, outlet_id, product_code, name, 
                   type, count, price_per_unit, revenue, shipping_cost, warranty_months, 
                   return_policy_days, supplier_id 
                   FROM purchases WHERE 1=1"""
        params = []
        
        if date_from:
            query += " AND DATE(timestamp) >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(timestamp) <= %s"
            params.append(date_to)
        
        query += " ORDER BY timestamp"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        results = []
        for row in rows:
            results.append({
                'sale_id': row[0],
                'timestamp': row[1].isoformat() if row[1] else None,
                'buyer_id': row[2],
                'outlet_id': row[3],
                'product_code': row[4],
                'name': row[5],
                'type': row[6],
                'count': row[7],
                'price_per_unit': float(row[8]),
                'revenue': float(row[9]),
                'shipping_cost': float(row[10]) if row[10] else 0.0,
                'warranty_months': row[11] if row[11] else 0,
                'return_policy_days': row[12] if row[12] else 30,
                'supplier_id': row[13]
            })
        
        return jsonify({
            'results': results,
            'count': len(results),
            'retailer': 'retailer_3'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)

