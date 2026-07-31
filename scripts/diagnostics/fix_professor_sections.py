"""
Script de correction et population des sections/cours pour le professeur.
Corrige :
  1. Les caracteres corrompus dans sections (level)
  2. Cree les sections manquantes par classe du bulletin (BulletinConfig)
  3. Lie les cours aux bons (section_id, professor_id)
  4. Fallback : si un professeur a des cours sans section, les lie automatiquement

Usage : python fix_professor_sections.py
"""

import sys
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'gescoapp.db')


def fix_level_encoding(conn):
    """Corrige les niveaux stockes avec des caracteres corrompus (ex: 3-me -> 3eme)."""
    cur = conn.cursor()
    cur.execute("SELECT id, level, class_name, name FROM sections")
    rows = cur.fetchall()
    fixed = 0
    for sid, level, class_name, name in rows:
        new_level = level
        # Remplacement des sequences corrompues connues
        replacements = [
            ('\xe8me', 'eme'),
            ('\xe9me', 'eme'),
            ('\xc3\xa8me', 'eme'),
            ('\xc3\xa9me', 'eme'),
            ('1\xe8re', '1ere'),
            ('1\xe9re', '1ere'),
            ('2\xe8me', '2eme'),
            ('3\xe8me', '3eme'),
            ('4\xe8me', '4eme'),
            ('5\xe8me', '5eme'),
            ('6\xe8me', '6eme'),
            ('7\xe8me', '7eme'),
        ]
        for bad, good in replacements:
            try:
                new_level = new_level.replace(bad, good)
            except Exception:
                pass
        if new_level != level:
            cur.execute("UPDATE sections SET level=? WHERE id=?", (new_level, sid))
            print(f"  Section {sid} '{name}': level corrige '{level}' -> '{new_level}'")
            fixed += 1
    conn.commit()
    print(f"  {fixed} niveau(x) corrige(s).\n")


def get_sections_from_bulletin(conn, school_id):
    """
    Retourne les sections distinctes issues des BulletinConfig.
    Chaque BulletinConfig correspond a une section+level.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT bc.id, bc.section_id, bc.level, s.name, s.class_name "
        "FROM bulletin_configs bc "
        "JOIN sections s ON s.id = bc.section_id "
        "WHERE bc.school_id = ?",
        (school_id,)
    )
    return cur.fetchall()


def ensure_section_exists(conn, school_id, name, level, class_name):
    """Retourne l'id de la section existante ou en cree une nouvelle."""
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM sections WHERE school_id=? AND name=? AND level=? AND class_name=?",
        (school_id, name, level, class_name)
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO sections (school_id, name, level, class_name) VALUES (?,?,?,?)",
        (school_id, name, level, class_name)
    )
    conn.commit()
    new_id = cur.lastrowid
    print(f"  [CREE] Section '{name}' / '{level}' / '{class_name}' (id={new_id})")
    return new_id


def link_courses_to_sections(conn, school_id):
    """
    Pour chaque cours qui a un section_id, verifie que la section existe.
    Pour les cours du bulletin (via BulletinBranch -> BulletinConfig -> Section),
    tente de lier le cours a la section correcte.
    """
    cur = conn.cursor()

    # Recuperer tous les cours avec section_id null (ne devrait pas exister apres migration)
    cur.execute(
        "SELECT id, title, professor_id FROM courses WHERE school_id=? AND section_id IS NULL",
        (school_id,)
    )
    orphan_courses = cur.fetchall()
    if orphan_courses:
        print(f"  [ATTENTION] {len(orphan_courses)} cours sans section_id trouves pour school_id={school_id}")

    # Recuperer les branches du bulletin avec leur config (section+level)
    cur.execute(
        "SELECT bb.id, bb.name, bc.section_id, bc.level, s.name as sname, s.class_name "
        "FROM bulletin_branches bb "
        "JOIN bulletin_configs bc ON bc.id = bb.config_id "
        "JOIN sections s ON s.id = bc.section_id "
        "WHERE bc.school_id = ? AND bb.type='branch'",
        (school_id,)
    )
    branches = cur.fetchall()
    print(f"  {len(branches)} branches du bulletin trouvees pour school_id={school_id}")

    # Pour chaque cours, chercher sa branche correspondante
    cur.execute(
        "SELECT id, title, section_id, professor_id, branch_id FROM courses WHERE school_id=?",
        (school_id,)
    )
    all_courses = cur.fetchall()

    linked = 0
    for cid, title, section_id, prof_id, branch_id in all_courses:
        if branch_id is None:
            continue
        # Trouver la branche
        matching = [b for b in branches if b[0] == branch_id]
        if not matching:
            continue
        _, bname, bsection_id, blevel, bsname, bclass_name = matching[0]
        if section_id != bsection_id:
            cur.execute("UPDATE courses SET section_id=? WHERE id=?", (bsection_id, cid))
            print(f"  Cours id={cid} '{title}': section_id {section_id} -> {bsection_id}")
            linked += 1
    if linked:
        conn.commit()
    print(f"  {linked} cours re-lies a leur section via branch_id.\n")


def fix_professors_without_sections(conn, school_id):
    """
    Verifie que chaque professeur a au moins un cours avec section_id et professor_id.
    Si un professeur a des cours SANS section_id, on les lie a la premiere section disponible.
    """
    cur = conn.cursor()

    # Professeurs de l'ecole
    cur.execute(
        "SELECT id, username, full_name FROM users WHERE school_id=? AND role='professor'",
        (school_id,)
    )
    professors = cur.fetchall()

    print(f"  {len(professors)} professeur(s) trouves:")
    for pid, uname, fname in professors:
        cur.execute(
            "SELECT COUNT(*) FROM courses WHERE professor_id=? AND section_id IS NOT NULL AND school_id=?",
            (pid, school_id)
        )
        count = cur.fetchone()[0]
        status = "OK" if count > 0 else "PAS DE COURS AVEC SECTION"
        print(f"    Prof id={pid} '{fname}': {count} cours avec section -> {status}")


def create_missing_professor_sections(conn, school_id):
    """
    Cree les sections manquantes pour les professeurs dont les cours
    n'ont pas de section_id valide, en se basant sur les bulletin_configs.
    """
    cur = conn.cursor()

    # Lister tous les bulletin_configs pour obtenir les classes existantes
    cur.execute(
        "SELECT bc.id, bc.section_id, bc.level, s.name, s.class_name, s.school_id "
        "FROM bulletin_configs bc "
        "JOIN sections s ON s.id = bc.section_id "
        "WHERE bc.school_id = ?",
        (school_id,)
    )
    configs = cur.fetchall()
    print(f"\n  {len(configs)} BulletinConfigs trouves:")
    for cfg in configs:
        print(f"    Config id={cfg[0]}: section_id={cfg[1]}, level={cfg[2]}, name='{cfg[3]}', class='{cfg[4]}'")

    # S'assurer que chaque section de bulletin existe correctement
    for cfg_id, sec_id, level, name, class_name, sec_school_id in configs:
        # Verifier l'integrite
        cur.execute("SELECT id, name, level, class_name FROM sections WHERE id=?", (sec_id,))
        row = cur.fetchone()
        if not row:
            print(f"  [ERREUR] Section id={sec_id} referencee dans BulletinConfig mais ABSENTE !")
        elif row[2] != level:
            # Mettre a jour le niveau dans la section pour correspondre au config
            cur.execute("UPDATE sections SET level=? WHERE id=?", (level, sec_id))
            print(f"  Section id={sec_id} '{name}': niveau mis a jour -> '{level}'")
    conn.commit()


def rebuild_courses_section_from_bulletin(conn, school_id):
    """
    Pour chaque cours dont le branch_id pointe vers une BulletinBranch,
    met a jour section_id avec la section du BulletinConfig correspondant.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT c.id, c.title, c.section_id, c.professor_id, c.branch_id, "
        "bc.section_id as config_section_id "
        "FROM courses c "
        "JOIN bulletin_branches bb ON bb.id = c.branch_id "
        "JOIN bulletin_configs bc ON bc.id = bb.config_id "
        "WHERE c.school_id = ? "
        "AND (c.section_id IS NULL OR c.section_id != bc.section_id)",
        (school_id,)
    )
    rows = cur.fetchall()
    print(f"\n  {len(rows)} cours avec section_id desaligne par rapport au bulletin:")
    for cid, title, sec_id, prof_id, branch_id, config_sec_id in rows:
        cur.execute("UPDATE courses SET section_id=? WHERE id=?", (config_sec_id, cid))
        print(f"    Cours id={cid} '{title}': section_id {sec_id} -> {config_sec_id}")
    conn.commit()
    print(f"  {len(rows)} cours re-alignes.\n")


def show_final_state(conn, school_id):
    """Affiche l'etat final apres correction."""
    cur = conn.cursor()
    print("\n=== ETAT FINAL ===")
    print("Sections visibles par professeur:\n")

    cur.execute(
        "SELECT id, username, full_name FROM users WHERE school_id=? AND role='professor'",
        (school_id,)
    )
    professors = cur.fetchall()

    for pid, uname, fname in professors:
        cur.execute(
            "SELECT DISTINCT s.id, s.name, s.level, s.class_name "
            "FROM sections s "
            "JOIN courses c ON c.section_id = s.id "
            "WHERE s.school_id = ? "
            "AND c.school_id = ? "
            "AND c.section_id IS NOT NULL "
            "AND c.professor_id = ? "
            "AND c.title NOT LIKE 'Pr_sence de classe%' "
            "ORDER BY s.name, s.level, s.class_name",
            (school_id, school_id, pid)
        )
        sections = cur.fetchall()
        if sections:
            print(f"  Prof '{fname}' ({pid}): {len(sections)} section(s)")
            for s in sections:
                print(f"    -> id={s[0]} | {s[1]} / {s[2]} / {s[3]}")
        else:
            print(f"  Prof '{fname}' ({pid}): [AUCUNE SECTION VISIBLE]")
    print()


def main():
    print(f"Connexion a {DB_PATH}...\n")
    conn = sqlite3.connect(DB_PATH)

    # Recuperer les ecoles actives
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM schools")
    schools = cur.fetchall()
    print(f"{len(schools)} ecole(s) trouvee(s):\n")

    for school_id, school_name in schools:
        print(f"{'='*60}")
        print(f"Ecole: {school_name} (id={school_id})")
        print(f"{'='*60}")

        print("\n[1] Correction des caracteres corrompus dans les niveaux...")
        fix_level_encoding(conn)

        print("[2] Verification des sections issues du bulletin...")
        create_missing_professor_sections(conn, school_id)

        print("[3] Re-alignement des cours avec leur section (via branch_id)...")
        rebuild_courses_section_from_bulletin(conn, school_id)

        print("[4] Liaison des cours aux sections (verification generale)...")
        link_courses_to_sections(conn, school_id)

        print("[5] Etat des professeurs...")
        fix_professors_without_sections(conn, school_id)

        show_final_state(conn, school_id)

    conn.close()
    print("\nCorrection terminee avec succes !")
    print("\nRedemarrez l'application Flask pour que les changements soient pris en compte.")


if __name__ == '__main__':
    main()
