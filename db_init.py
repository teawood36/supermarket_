# db_init.py
import sqlite3

conn = sqlite3.connect('inventory.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    warehouse TEXT NOT NULL,
    location TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0
)
''')

# 出入库记录表
c.execute('''
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- 入库 or 出库
    quantity INTEGER NOT NULL,
    category TEXT,
    warehouse TEXT,
    location TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
