from flask import Flask, jsonify
import sqlite3
import os

app = Flask(__name__)

# Database configuration
DB_PATH = os.getenv('DB_PATH', '/tmp/inventory.db')

# Connection pool settings
MAX_CONNECTIONS = int(os.getenv('MAX_DB_CONNECTIONS', '10'))
CONNECTION_TIMEOUT = int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))

def get_db_connection():
    """
    Get a database connection with proper timeout settings.
    """
    conn = sqlite3.connect(DB_PATH, timeout=CONNECTION_TIMEOUT)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database with sample inventory data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            product_id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    ''')
    
    # Insert sample data if table is empty
    cursor.execute('SELECT COUNT(*) FROM inventory')
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ('PROD001', 'Laptop', 50, 999.99),
            ('PROD002', 'Mouse', 200, 29.99),
            ('PROD003', 'Keyboard', 150, 79.99),
            ('PROD004', 'Monitor', 75, 299.99),
            ('PROD005', 'Headphones', 100, 149.99)
        ]
        cursor.executemany(
            'INSERT INTO inventory (product_id, product_name, quantity, price) VALUES (?, ?, ?, ?)',
            sample_data
        )
    
    conn.commit()
    conn.close()

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    """
    return jsonify({'status': 'healthy', 'service': 'inventory-service'}), 200

@app.route('/inventory/<product_id>', methods=['GET'])
def check_inventory(product_id):
    """
    Check inventory for a specific product.
    Fixed: Removed random failure injection that was causing connection pool exhaustion.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inventory WHERE product_id = ?', (product_id,))
        product = cursor.fetchone()
        
        if product:
            return jsonify({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'quantity': product['quantity'],
                'price': product['price'],
                'available': product['quantity'] > 0
            }), 200
        else:
            return jsonify({'error': 'Product not found'}), 404
    
    except sqlite3.OperationalError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    finally:
        if conn:
            conn.close()

@app.route('/inventory', methods=['GET'])
def list_inventory():
    """
    List all inventory items.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inventory')
        products = cursor.fetchall()
        
        inventory_list = [
            {
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'quantity': product['quantity'],
                'price': product['price'],
                'available': product['quantity'] > 0
            }
            for product in products
        ]
        
        return jsonify({'inventory': inventory_list}), 200
    
    except sqlite3.OperationalError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
