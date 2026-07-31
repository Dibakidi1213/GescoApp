import sqlite3

conn = sqlite3.connect('gescoapp.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info('notifications')")
cols = cur.fetchall()
for c in cols:
    print(c)
conn.close()