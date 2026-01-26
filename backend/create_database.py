"""
Script to create the word_registry database.
Run this before init_db.py
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connection parameters - edit these
DB_USER = "postgres"
DB_PASSWORD = "your_password_here"  # CHANGE THIS
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "word_registry"

try:
    # Connect to PostgreSQL server (default 'postgres' database)
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cursor = conn.cursor()

    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    exists = cursor.fetchone()

    if exists:
        print(f"Database '{DB_NAME}' already exists!")
    else:
        # Create database
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"✓ Database '{DB_NAME}' created successfully!")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure to:")
    print("1. Edit DB_PASSWORD in this script")
    print("2. PostgreSQL server is running")
    print("3. Credentials are correct")
