# app.py
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

CATEGORIES = {
    '食品': '一仓库',
    '日用品': '二仓库',
    '工具': '三仓库',
    '其他类': '四仓库'
}

def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return redirect(url_for('inventory'))

@app.route('/inventory')
def inventory():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('inventory.html', products=products)

@app.route('/add', methods=['POST'])
def add_product():
    name = request.form['name']
    quantity = int(request.form['quantity'])
    category = request.form['category']
    warehouse = CATEGORIES.get(category, '四仓库')
    location = request.form['location']

    conn = get_db_connection()
    # 检查是否已存在相同商品和库位
    existing = conn.execute(
        'SELECT * FROM products WHERE name = ? AND location = ?', (name, location)
    ).fetchone()
    if existing:
        conn.execute(
            'UPDATE products SET quantity = quantity + ? WHERE id = ?', (quantity, existing['id'])
        )
    else:
        conn.execute(
            'INSERT INTO products (name, quantity, category, warehouse, location) VALUES (?, ?, ?, ?, ?)',
            (name, quantity, category, warehouse, location)
        )
    conn.commit()
    conn.close()
    return redirect(url_for('inventory'))

@app.route('/remove', methods=['POST'])
def remove_product():
    name = request.form['name']
    quantity = int(request.form['quantity'])

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE name = ?', (name,)).fetchone()
    if product and product['quantity'] >= quantity:
        conn.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?', (quantity, product['id']))
    conn.commit()
    conn.close()
    return redirect(url_for('inventory'))

@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')

    conn = get_db_connection()
    if keyword and category:
        products = conn.execute(
            'SELECT * FROM products WHERE name LIKE ? AND category = ?',
            (f'%{keyword}%', category)
        ).fetchall()
    elif keyword:
        products = conn.execute(
            'SELECT * FROM products WHERE name LIKE ?', (f'%{keyword}%',)
        ).fetchall()
    elif category:
        products = conn.execute(
            'SELECT * FROM products WHERE category = ?', (category,)
        ).fetchall()
    else:
        products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('inventory.html', products=products)

@app.route('/adjust', methods=['POST'])
def adjust_quantity():
    product_id = request.form['product_id']
    new_quantity = int(request.form['new_quantity'])

    conn = get_db_connection()
    conn.execute('UPDATE products SET quantity = ? WHERE id = ?', (new_quantity, product_id))
    conn.commit()
    conn.close()
    return redirect(url_for('inventory'))

if __name__ == '__main__':
    app.run(debug=True)
