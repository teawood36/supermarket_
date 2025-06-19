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

import os
DATABASE = os.getenv('DATABASE', 'inventory.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
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

    # 插入记录日志
    conn.execute(
        'INSERT INTO records (name, type, quantity, category, warehouse, location) VALUES (?, ?, ?, ?, ?, ?)',
        (name, '入库', quantity, category, warehouse, location)
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

    if product:
        current_qty = product['quantity']
        if current_qty >= quantity:
            new_qty = current_qty - quantity
            if new_qty == 0:
                conn.execute('DELETE FROM products WHERE id = ?', (product['id'],))
            else:
                conn.execute('UPDATE products SET quantity = ? WHERE id = ?', (new_qty, product['id']))

            # 插入记录日志
            conn.execute(
                'INSERT INTO records (name, type, quantity, category, warehouse, location) VALUES (?, ?, ?, ?, ?, ?)',
                (product['name'], '出库', quantity, product['category'], product['warehouse'], product['location'])
            )
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
def adjust_product():
    product_id = request.form['product_id']
    name = request.form['name']
    quantity = int(request.form['quantity'])
    category = request.form['category']
    location = request.form['location']
    warehouse = CATEGORIES.get(category, '四仓库')

    conn = get_db_connection()

    # 获取旧数据（可选扩展：记录变更对比）
    old = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    # 执行更新
    conn.execute(
        'UPDATE products SET name = ?, quantity = ?, category = ?, warehouse = ?, location = ? WHERE id = ?',
        (name, quantity, category, warehouse, location, product_id)
    )

    # ✅ 插入更新记录（记录为“更新”类型）
    conn.execute(
        'INSERT INTO records (name, type, quantity, category, warehouse, location) VALUES (?, ?, ?, ?, ?, ?)',
        (name, '更新', quantity, category, warehouse, location)
    )

    conn.commit()
    conn.close()
    return redirect(url_for('inventory'))



@app.route('/records')
def view_records():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM records ORDER BY timestamp DESC').fetchall()
    conn.close()
    return render_template('records.html', logs=logs)

@app.route('/delete', methods=['POST'])
def delete_product():
    product_id = request.form['product_id']
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('inventory'))


if __name__ == '__main__':
    app.run(debug=True)
