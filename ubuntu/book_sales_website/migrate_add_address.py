"""
Add address columns to users table
"""
import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'booksales.db')

if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
    exit(1)

print(f"Updating database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add address columns one by one
columns_to_add = [
    ('address', 'VARCHAR(255)'),
    ('city', 'VARCHAR(100)'),
    ('state', 'VARCHAR(100)'),
    ('zip_code', 'VARCHAR(20)'),
    ('country', 'VARCHAR(100)')
]

for column_name, column_type in columns_to_add:
    try:
        cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
        print(f"✓ Added '{column_name}' column")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print(f"  '{column_name}' column already exists")
        else:
            print(f"  Error adding '{column_name}': {e}")

conn.commit()
conn.close()

print("\n✓ Database migration completed!")
