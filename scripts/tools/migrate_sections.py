import sqlite3, sys, os

# Path to the SQLite database used by GescoApp
DB_PATH = r"c:/xampp2/htdocs/GescoApp/gescoapp.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ------------------------------------------------------------
# 1️⃣ Insert missing sections (if they do not already exist)
# ------------------------------------------------------------
sections = [
    ("LATIN PHILO", "3ème", "A"),
    ("ELECTRICITE", "2ème", "A"),
    ("CONSTRUCTION", "4ème", "A"),
]
for name, level, class_name in sections:
    cur.execute(
        """
        INSERT INTO sections (school_id, name, level, class_name)
        SELECT 1, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM sections WHERE school_id=1 AND name=? AND level=?
        )
        """,
        (name, level, class_name, name, level),
    )

# ------------------------------------------------------------
# 2️⃣ Corriger les class_name NULL ou vides
# ------------------------------------------------------------
cur.execute(
    """
    UPDATE sections
    SET class_name = 'A'
    WHERE school_id = 1 AND (class_name IS NULL OR TRIM(class_name) = '')
    """
)

# ------------------------------------------------------------
# 3️⃣ Lier les cours existants aux bonnes sections (exemple LATIN PHILO)
# ------------------------------------------------------------
cur.execute(
    """
    UPDATE courses
    SET section_id = (
        SELECT id FROM sections
        WHERE school_id = courses.school_id
          AND name = 'LATIN PHILO'
          AND level = '3ème'
    )
    WHERE title NOT LIKE 'Présence de classe%'
    """
)

# ------------------------------------------------------------
# 4️⃣ Assigner le professeur aux cours qui n’ont pas d‘ID professeur
# ------------------------------------------------------------
# On récupère le premier utilisateur de type 'professor' comme exemple
cur.execute("SELECT id FROM users WHERE role='professor' LIMIT 1")
row = cur.fetchone()
if row:
    professor_id = row[0]
    cur.execute(
        """
        UPDATE courses
        SET professor_id = ?
        WHERE professor_id IS NULL OR professor_id = 0
        """,
        (professor_id,),
    )

conn.commit()
conn.close()
print('Migration terminee avec succes')
