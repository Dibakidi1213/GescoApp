#!/usr/bin/env python
import sqlite3

db_path = 'gescoapp.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print(f'=== Tables in gescoapp.db ===')
print(f'Total: {len(tables)} tables')

print(f'\n=== Bulletin configs for school 1 ===')
cursor.execute('SELECT id, school_id, section_id, level, ige_number FROM bulletin_configs WHERE school_id = 1 ORDER BY id')
rows = cursor.fetchall()
for row in rows:
    print(f'ID: {row[0]}, Section: {row[2]}, Level: {row[3]}, IGE: {row[4]}')

conn.close()
