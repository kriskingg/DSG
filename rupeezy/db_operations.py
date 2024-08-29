import sqlite3
import logging

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

DB_FILE = "beest-orders.db"

def create_connection(db_file):
    """Create a database connection to SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logging.info(f"Connected to SQLite database: {db_file}")
    except sqlite3.Error as e:
        logging.error(f"SQLite connection error: {e}")
    return conn

def create_table(conn):
    """Create orders table if it does not exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        symbol TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        product TEXT NOT NULL,
        ltp REAL NOT NULL,
        executed_at TEXT NOT NULL
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()
        logging.info("Orders table created or already exists.")
    except sqlite3.Error as e:
        logging.error(f"SQLite table creation error: {e}")

def insert_order(conn, order):
    """Insert a new order into the orders table."""
    insert_order_sql = """
    INSERT INTO orders(symbol, quantity, price, transaction_type, product, ltp, executed_at)
    VALUES(?, ?, ?, ?, ?, ?, datetime('now', 'localtime', '+05:30'));
    """
    try:
        cursor = conn.cursor()
        cursor.execute(insert_order_sql, order)
        conn.commit()
        logging.info("Order inserted into the orders table.")
    except sqlite3.Error as e:
        logging.error(f"SQLite insertion error: {e}")
