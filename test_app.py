# test_app.py
import os
import tempfile
import pytest
import sqlite3
from app import app, get_db_connection

@pytest.fixture
def client():
    db_fd, temp_path = tempfile.mkstemp()
    os.environ['DATABASE'] = temp_path  # 告诉 app 使用这个测试数据库
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # 如果你后续启用 CSRF，先禁用

    with app.test_client() as client:
        conn = sqlite3.connect(temp_path)
        conn.row_factory = sqlite3.Row
        conn.execute('''CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            quantity INTEGER,
            category TEXT,
            warehouse TEXT,
            location TEXT
        )''')
        conn.execute('''CREATE TABLE records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,
            quantity INTEGER,
            category TEXT,
            warehouse TEXT,
            location TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        conn.close()
        yield client

    os.close(db_fd)
    os.unlink(temp_path)

def login_admin(client):
    return client.post('/login', data={
        'username': 'admin',
        'password': '123456'
    }, follow_redirects=True)

def test_add_product(client):
    login_admin(client)
    response = client.post('/add', data={
        'name': '测试商品',
        'quantity': 10,
        'category': '食品',
        'location': 'A区-1排'
    }, follow_redirects=True)

    assert response.status_code == 200

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE name = ?', ('测试商品',)).fetchone()
    conn.close()

    assert product is not None
    # assert product['quantity'] == 10
    assert product['category'] == '食品'

def test_remove_product(client):
    login_admin(client)
    client.post('/add', data={
        'name': '删除测试',
        'quantity': 5,
        'category': '工具',
        'location': 'B区-1排'
    })
    client.post('/remove', data={
        'name': '删除测试',
        'quantity': 5
    })

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE name = ?', ('删除测试',)).fetchone()
    conn.close()
    assert product is None

def test_adjust_product(client):
    login_admin(client)
    client.post('/add', data={
        'name': '编辑测试',
        'quantity': 5,
        'category': '日用品',
        'location': 'B区-2排'
    })

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE name = ?', ('编辑测试',)).fetchone()
    conn.close()

    client.post('/adjust', data={
        'product_id': product['id'],
        'name': '编辑测试已改',
        'quantity': 8,
        'category': '工具',
        'location': 'C区-1排'
    })

    conn = get_db_connection()
    updated = conn.execute('SELECT * FROM products WHERE id = ?', (product['id'],)).fetchone()
    conn.close()

    assert updated['name'] == '编辑测试已改'
    assert updated['quantity'] == 8
    assert updated['category'] == '工具'

def test_record_on_add(client):
    login_admin(client)
    client.post('/add', data={
        'name': '记录测试商品',
        'quantity': 3,
        'category': '食品',
        'location': 'A区-3排'
    })

    conn = get_db_connection()
    record = conn.execute('SELECT * FROM records WHERE name = ? AND type = ?', ('记录测试商品', '入库')).fetchone()
    conn.close()

    assert record is not None
    assert record['quantity'] == 3
    assert record['category'] == '食品'

# ✅ 未登录访问应重定向
def test_protected_redirect(client):
    response = client.get('/inventory')
    assert response.status_code == 302
    assert '/login' in response.location
