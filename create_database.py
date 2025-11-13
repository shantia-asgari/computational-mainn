# create_database.py 
import sqlite3
from config import DB_NAME

def initialize_database():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print(f"Successfully connected to '{DB_NAME}'")
        
        # Drop the table if it exists to ensure a clean slate with the new schema
        cursor.execute("DROP TABLE IF EXISTS positions;")
        print("Old 'positions' table dropped if it existed.")

        create_table_query = """
        CREATE TABLE positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_order_id TEXT NOT NULL UNIQUE,
            symbol TEXT NOT NULL,
            status TEXT NOT NULL,
            quantity REAL NOT NULL,
            entry_price REAL NOT NULL,
            entry_time INTEGER NOT NULL,
            total_cost_tmn REAL NOT NULL,
            entry_fee REAL NOT NULL,
            limit_sell_order_id TEXT, -- ستون جدید برای پیگیری سفارش فروش
            exit_price REAL,
            exit_time INTEGER,
            pnl_tmn REAL
        );
        """
        cursor.execute(create_table_query)
        print("New 'positions' table with 'limit_sell_order_id' column created successfully.")
        conn.commit()
        conn.close()
        print(f"Database '{DB_NAME}' is ready.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    initialize_database()
