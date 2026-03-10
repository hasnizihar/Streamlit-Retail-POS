import sqlite3
import os
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")

@st.cache_resource
def get_db_connection():
    """Returns a SQLite connection object that is cached by Streamlit."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Enable accessing columns by name
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER,
        barcode TEXT
    )
    """)

    # 2. Sales Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_no INTEGER,
        product TEXT,
        qty INTEGER,
        price REAL,
        total REAL,
        date TEXT,
        customer_id INTEGER
    )
    """)

    # 3. Returns Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS returns(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        qty INTEGER,
        date TEXT
    )
    """)

    # 4. Users Table (for Authentication)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)
    
    # Insert default admin if no users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users(username, password, role) VALUES(?, ?, ?)", ("admin", "admin", "Admin"))
        cursor.execute("INSERT INTO users(username, password, role) VALUES(?, ?, ?)", ("cashier", "cashier", "Cashier"))


    # 5. Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT UNIQUE,
        points INTEGER DEFAULT 0
    )
    """)

    # --- SCHEMA MIGRATIONS FOR EXISTING DB ---
    # Add customer_id to sales if it doesn't exist
    try:
        cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER")
    except sqlite3.OperationalError:
        pass # Column already exists

    conn.commit()

# Ensure DB is initialized when this file is imported
init_db()
