import sqlite3

conn = sqlite3.connect('gescoapp.db')
cur = conn.cursor()

print('=== REPARTITION des cours par professor_id ===')
cur.execute('SELECT professor_id, COUNT(*) as nb FROM courses GROUP BY professor_id ORDER BY professor_id')
for row in cur.fetchall():
    print(row)

print('\n=== Section id=57 details ===')
cur.execute('SELECT id, school_id, name, level, class_name FROM sections WHERE id=57')
for row in cur.fetchall():
    print(row)

print('\n=== TOUS les cours du professeur 12 (KANGA) ===')
cur.execute('SELECT id, title, section_id, professor_id FROM courses WHERE professor_id=12')
for row in cur.fetchall():
    print(row)

print('\n=== Simulation _visible_sections pour prof id=12 (school_id=1) ===')
sql = (
    "SELECT DISTINCT s.id, s.name, s.level, s.class_name "
    "FROM sections s "
    "JOIN courses c ON c.section_id = s.id "
    "WHERE s.school_id = 1 "
    "AND c.school_id = 1 "
    "AND c.section_id IS NOT NULL "
    "AND c.title NOT LIKE 'Pr%sence de classe%' "
    "AND c.professor_id = 12 "
    "ORDER BY s.name, s.level, s.class_name"
)
cur.execute(sql)
rows = cur.fetchall()
print('Sections visibles pour prof 12:', rows)

print('\n=== Verif : le filtre ATTENDANCE_COURSE_TITLE_PREFIX (valeur exacte) ===')
cur.execute("SELECT id, title FROM courses WHERE title LIKE 'Pr%sence de classe%'")
att_rows = cur.fetchall()
print('Cours attendance trouves:', att_rows)

print('\n=== Tous les cours de la section 57 ===')
cur.execute('SELECT id, title, professor_id FROM courses WHERE section_id=57')
for row in cur.fetchall():
    print(row)

conn.close()
print('\n=== DONE ===')
