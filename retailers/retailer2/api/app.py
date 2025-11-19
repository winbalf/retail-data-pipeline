"""
Retailer 2 API - Flask application to expose transaction data
"""
from flask import Flask, jsonify, request
import psycopg2
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Database connection
def get_db_connection():
    """Get PostgreSQL connection for Retailer 2."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'retailer2_db'),
        user=os.getenv('POSTGRES_USER', 'retailer2_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'retailer2_pass')
    )

def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')
        expected_key = os.getenv('RETAILER_2_API_KEY', 'retailer2_api_key_123')
        
        if api_key != expected_key:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'retailer': 'retailer_2'})

@app.route('/transactions', methods=['GET'])
@require_api_key
def get_transactions():
    """
    Get transaction data with optional date filtering.
    Query params: from, to (YYYY-MM-DD format)
    """
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """SELECT transaction_number, date, member_id, location_id, item_code, item_name, 
                   department, qty, unit_cost, amount, tax_amount, loyalty_points_earned, 
                   promotion_code, sales_rep_id 
                   FROM transactions WHERE 1=1"""
        params = []
        
        if from_date:
            query += " AND DATE(date) >= %s"
            params.append(from_date)
        
        if to_date:
            query += " AND DATE(date) <= %s"
            params.append(to_date)
        
        query += " ORDER BY date"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        transactions_data = []
        for row in rows:
            transactions_data.append({
                'transaction_number': row[0],
                'date': row[1].isoformat() if row[1] else None,
                'member_id': row[2],
                'location_id': row[3],
                'item_code': row[4],
                'item_name': row[5],
                'department': row[6],
                'qty': row[7],
                'unit_cost': float(row[8]),
                'amount': float(row[9]),
                'tax_amount': float(row[10]) if row[10] else 0.0,
                'loyalty_points_earned': row[11] if row[11] else 0,
                'promotion_code': row[12],
                'sales_rep_id': row[13]
            })
        
        return jsonify({
            'transactions': transactions_data,
            'count': len(transactions_data),
            'retailer': 'retailer_2'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)

