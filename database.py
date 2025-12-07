# database.py
import psycopg2
from psycopg2 import pool
import os

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_zsbQNiH92vkl@ep-floral-hill-a1sq9ye6-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&connect_timeout=30')

# Create the Pool (Global Variable)
db_pool = None

try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DATABASE_URL)
    if db_pool:
        print("✅ Fast Connection Pool Created in database.py!")
except Exception as e:
    print(f"❌ Error creating pool: {e}")

def get_db_connection():
    """Get a connection from the pool"""
    return db_pool.getconn()

def return_db_connection(conn):
    """Return the connection to the pool"""
    if conn:
        db_pool.putconn(conn)