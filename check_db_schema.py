#!/usr/bin/env python3
import sqlite3
import os

# Try to find the database
if os.path.exists('gescoapp.db'):
    db_path = 'gescoapp.db'
elif os.path.exists('instance/app.db'):
    db_path = 'instance/app.db'
else:
    print("Database not found")
    exit(1)
    
print(f"Using database: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='bulletin_branches'")
result = cursor.fetchone()
if result:
    print("Current Schema:")
    print(result[0])
else:
    print("Table not found")

# Get columns
cursor.execute("PRAGMA table_info(bulletin_branches)")
columns = cursor.fetchall()
print("\nColumns:")
for col in columns:
    print(f"  {col[1]}: {col[2]}")

conn.close()
