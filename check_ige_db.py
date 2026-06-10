#!/usr/bin/env python
import sqlite3

db_path = 'instance/gescoapp.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print('=== Tables in database ===')
    for table in tables:
        print(f'  {table[0]}')
    
    print('\n=== Bulletin Configs for School 1 ===')
    if any('bulletin_config' in t[0].lower() for t in tables):
        try:
            cursor.execute('''SELECT id, school_id, section_id, level, ige_number, academic_year 
                            FROM bulletin_configs WHERE school_id = 1 ORDER BY id''')
            rows = cursor.fetchall()
            for row in rows:
                print(f'ID: {row[0]}, School: {row[1]}, Section: {row[2]}, Level: {row[3]}, IGE: {row[4]}, Year: {row[5]}')
        except Exception as e:
            print(f'Error querying bulletin_configs: {e}')
    else:
        print('bulletin_configs table not found')
        
    conn.close()
except Exception as e:
    print(f'Error: {e}')
