import sqlite3

conn = sqlite3.connect('gescoapp.db')
cur = conn.cursor()

print('=== COLONNES TABLE sections ===')
cur.execute('PRAGMA table_info(sections)')
for row in cur.fetchall():
    print(row)

print('\n=== SECTIONS (20 premieres) ===')
cur.execute('SELECT id, school_id, name, level, class_name FROM sections LIMIT 20')
rows = cur.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print('  [VIDE - aucune section]')

print('\n=== COLONNES TABLE courses ===')
cur.execute('PRAGMA table_info(courses)')
for row in cur.fetchall():
    print(row)

print('\n=== COURS AVEC professor_id ET section_id ===')
cur.execute('SELECT id, school_id, title, section_id, professor_id FROM courses WHERE professor_id IS NOT NULL AND section_id IS NOT NULL LIMIT 20')
rows = cur.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print('  [AUCUN cours avec professor_id ET section_id]')

print('\n=== COURS AVEC professor_id MAIS SANS section_id ===')
cur.execute('SELECT id, school_id, title, section_id, professor_id FROM courses WHERE professor_id IS NOT NULL AND section_id IS NULL LIMIT 10')
rows = cur.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print('  [aucun]')

print('\n=== TOTAUX ===')
cur.execute('SELECT COUNT(*) FROM courses')
print('Total cours:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM courses WHERE section_id IS NOT NULL')
print('Cours avec section_id:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM courses WHERE professor_id IS NOT NULL')
print('Cours avec professor_id:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM courses WHERE section_id IS NOT NULL AND professor_id IS NOT NULL')
print('Cours avec BOTH section_id ET professor_id:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM sections')
print('Total sections:', cur.fetchone()[0])

print('\n=== PROFESSEURS ===')
cur.execute("SELECT id, username, full_name, role, school_id FROM users WHERE role='professor'")
rows = cur.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print('  [Aucun professeur trouve]')

print('\n=== ECOLES ===')
cur.execute('SELECT id, name, slug, is_active FROM schools LIMIT 5')
for row in cur.fetchall():
    print(row)

print('\n=== BULLETIN_CONFIGS (5 premieres) ===')
cur.execute('SELECT id, school_id, section_id, level, academic_year FROM bulletin_configs LIMIT 5')
rows = cur.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print('  [VIDE]')

print('\n=== BULLETIN_BRANCHES (5 premieres) ===')
cur.execute('SELECT id, config_id, name, type FROM bulletin_branches LIMIT 5')
rows = cur.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print('  [VIDE]')

conn.close()
print('\n=== DIAGNOSTIC TERMINE ===')
