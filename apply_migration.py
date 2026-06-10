#!/usr/bin/env python3
import sqlite3
import os

db_path = 'gescoapp.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if type column already exists
    cursor.execute("PRAGMA table_info(bulletin_branches)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'type' in columns:
        print("Column 'type' already exists")
    else:
        print("Adding 'type' column to bulletin_branches...")
        cursor.execute("ALTER TABLE bulletin_branches ADD COLUMN type VARCHAR(20) DEFAULT 'branch'")
        conn.commit()
        print("✓ Column 'type' added successfully")
        
        # Verify
        cursor.execute("PRAGMA table_info(bulletin_branches)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columns now: {columns}")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
