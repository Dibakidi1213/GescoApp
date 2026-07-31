"""
Test rapide des endpoints API du professeur en simulant la logique Python.
Verifie que _visible_sections_for_current_user retourne bien des sections
pour chaque professeur.
"""
import sys
sys.path.insert(0, '.')

# Simulation sans Flask context - on va directement tester avec SQLite
import sqlite3

DB_PATH = 'gescoapp.db'

def simulate_visible_sections(school_id, professor_id):
    """Simule _visible_sections_for_current_user pour un professeur."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Requete principale (avec professor_id)
    sql_main = (
        "SELECT DISTINCT s.id, s.name, s.level, s.class_name "
        "FROM sections s "
        "JOIN courses c ON c.section_id = s.id "
        "WHERE s.school_id = ? "
        "AND c.school_id = ? "
        "AND c.section_id IS NOT NULL "
        "AND c.title NOT LIKE 'Pr%sence de classe%' "
        "AND c.title NOT LIKE 'Presence de classe%' "
        "AND c.professor_id = ? "
        "ORDER BY s.name, s.level, s.class_name"
    )
    cur.execute(sql_main, (school_id, school_id, professor_id))
    sections = cur.fetchall()

    if not sections:
        # Fallback via BulletinConfig
        sql_fallback = (
            "SELECT DISTINCT s.id, s.name, s.level, s.class_name "
            "FROM sections s "
            "JOIN bulletin_configs bc ON bc.section_id = s.id "
            "WHERE s.school_id = ? "
            "AND bc.school_id = ? "
            "ORDER BY s.name, s.level, s.class_name"
        )
        cur.execute(sql_fallback, (school_id, school_id))
        sections = cur.fetchall()
        source = "FALLBACK BulletinConfig"
    else:
        source = "Cours directs (professor_id)"

    conn.close()
    return sections, source


def test_all_professors():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username, full_name, school_id FROM users WHERE role='professor'")
    profs = cur.fetchall()
    conn.close()

    print(f"Test de {len(profs)} professeur(s):\n")
    all_ok = True
    for pid, uname, fname, school_id in profs:
        sections, source = simulate_visible_sections(school_id, pid)
        status = "OK" if sections else "ECHEC"
        if not sections:
            all_ok = False
        print(f"  [{status}] Prof '{fname}' (id={pid}, school={school_id}): {len(sections)} section(s) via {source}")
        for s in sections[:3]:
            print(f"        -> id={s[0]} | {s[1]} / {s[2]} / {s[3]}")
        if len(sections) > 3:
            print(f"        ... et {len(sections)-3} autres")

    print()
    if all_ok:
        print("TOUS les professeurs ont des sections visibles !")
    else:
        print("ATTENTION : certains professeurs n'ont toujours pas de sections !")

    return all_ok


if __name__ == '__main__':
    test_all_professors()
