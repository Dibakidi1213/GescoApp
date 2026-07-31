from types import SimpleNamespace
import os
import re
import shutil
import tempfile
from datetime import datetime
from io import BytesIO

from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

from models import AcademicYear, School, Section, Student, Course, ActivityLog, db


def _db_is_sqlite():
    return db.engine.dialect.name == 'sqlite'
from routes.admin.helpers import get_school_id_for_admin_context, group_sections_for_display, require_super_admin
from routes.admin.services import apply_section_hierarchy_config
from routes.admin import admin_bp


@admin_bp.route('/academic-years', methods=['GET', 'POST'])
@login_required
@require_super_admin
def academic_years(school_slug=None):
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if not name:
            flash('Le nom de l\'année scolaire est obligatoire.', 'danger')
        elif AcademicYear.query.filter_by(name=name).first():
            flash('Cette année scolaire existe déjà.', 'warning')
        else:
            year = AcademicYear(name=name, is_active=bool(request.form.get('is_active')))
            if year.is_active:
                AcademicYear.query.update({'is_active': False})
            db.session.add(year)
            db.session.commit()
            flash('Année scolaire créée avec succès.', 'success')
        return redirect(url_for('admin.academic_years', school_slug=school_slug))

    years = AcademicYear.query.order_by(AcademicYear.name.desc()).all()
    schools = School.query.order_by(School.name).all()
    return render_template('admin/academic_years.html', academic_years=years, schools=schools)


@admin_bp.route('/academic-years/<int:year_id>/toggle', methods=['POST'])
@login_required
@require_super_admin
def toggle_academic_year_active(year_id, school_slug=None):
    year = AcademicYear.query.get_or_404(year_id)
    if not year.is_active:
        AcademicYear.query.update({'is_active': False})
        year.is_active = True
        session['academic_year'] = year.name
        flash(f"L'année scolaire {year.name} est maintenant active.", 'success')
    else:
        year.is_active = False
        flash(f"L'année scolaire {year.name} a été désactivée.", 'info')
    db.session.commit()
    return redirect(url_for('admin.academic_years', school_slug=school_slug))


@admin_bp.route('/academic-years/<int:year_id>/delete', methods=['POST'])
@login_required
@require_super_admin
def delete_academic_year(year_id, school_slug=None):
    year = AcademicYear.query.get_or_404(year_id)
    if year.is_active:
        flash('Impossible de supprimer l\'année scolaire active.', 'warning')
        return redirect(url_for('admin.academic_years', school_slug=school_slug))
    db.session.delete(year)
    db.session.commit()
    flash('Année scolaire supprimée.', 'success')
    return redirect(url_for('admin.academic_years', school_slug=school_slug))


@admin_bp.route('/download-database', methods=['GET'])
@login_required
@require_super_admin
def download_database():
    """Télécharger la base de données complète du système"""
    # Feature-flag: allow or temporarily disable backup/download endpoints
    if not current_app.config.get('ALLOW_RESTORE_DOWNLOAD', False):
        flash('Les opérations de sauvegarde/restauration sont temporairement désactivées.', 'warning')
        return redirect(url_for('admin.academic_years'))
    if not _db_is_sqlite():
        flash('La sauvegarde/restauration par fichier .db est uniquement disponible avec SQLite.', 'warning')
        return redirect(url_for('admin.academic_years'))
    try:
        # Récupérer le chemin de la base de données
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        db_path = os.path.join(basedir, 'gescoapp.db')
        
        if not os.path.exists(db_path):
            flash('Fichier de base de données introuvable.', 'danger')
            return redirect(url_for('admin.academic_years'))
        
        # Créer un nom de fichier avec horodatage
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'gescoapp_backup_{timestamp}.db'
        
        # Créer une copie temporaire pour éviter les problèmes de verrou
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = tmp.name
        
        try:
            # Copier le fichier
            shutil.copy2(db_path, tmp_path)
            
            # Lire le fichier temporaire
            with open(tmp_path, 'rb') as f:
                data = f.read()
            
            response = Response(data, mimetype='application/octet-stream')
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.unlink(tmp_path)
            except:
                pass
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors du téléchargement: {str(e)}', 'danger')
        return redirect(url_for('admin.academic_years'))


@admin_bp.route('/download-school-database/<int:school_id>/<int:year_id>', methods=['GET'])
@login_required
@require_super_admin
def download_school_database(school_id, year_id):
    """Télécharger la base de données pour une école spécifique et une année donnée"""
    if not current_app.config.get('ALLOW_RESTORE_DOWNLOAD', False):
        flash('Les opérations de sauvegarde/restauration sont temporairement désactivées.', 'warning')
        return redirect(url_for('admin.academic_years'))
    if not _db_is_sqlite():
        flash('La sauvegarde/restauration par fichier .db est uniquement disponible avec SQLite.', 'warning')
        return redirect(url_for('admin.academic_years'))
    try:
        # Récupérer l'école et l'année
        school = School.query.get_or_404(school_id)
        year = AcademicYear.query.get_or_404(year_id)
        
        # Récupérer le chemin de la base de données source
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        source_db_path = os.path.join(basedir, 'gescoapp.db')
        
        if not os.path.exists(source_db_path):
            flash('Fichier de base de données introuvable.', 'danger')
            return redirect(url_for('admin.academic_years'))
        
        # Créer un nom de fichier avec la convention demandée: nomecole_BD_année_date.db
        # Nettoyer le nom de l'école (remplacer les espaces et caractères spéciaux)
        school_name_safe = re.sub(r'[^a-zA-Z0-9_-]', '', school.name.replace(' ', '_'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        year_formatted = year.name.replace(' ', '')  # Enlever les espaces de l'année (ex: 2025-2026)
        filename = f'{school_name_safe}_BD_{year_formatted}_{timestamp}.db'
        
        # Créer une copie temporaire pour éviter les problèmes de verrou
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = tmp.name
        
        try:
            # Copier le fichier source
            shutil.copy2(source_db_path, tmp_path)
            
            # Ouvrir la copie et supprimer les données des autres écoles
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()

            # Build allowed tables list from SQLAlchemy metadata (defensive whitelist)
            allowed_tables = []
            try:
                for tname, table in db.metadata.tables.items():
                    colnames = [c.name for c in table.columns]
                    if 'school_id' in colnames:
                        allowed_tables.append(tname)
            except Exception:
                # Fallback: allow core known tables
                allowed_tables = ['students', 'grades', 'conduct_grades', 'attendance_records', 'courses', 'sections']

            # Lister les tables existantes dans la copie
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            tables_to_clean = [t for t in tables if t in allowed_tables]

            # Supprimer les enregistrements des autres écoles (transactional)
            try:
                cursor.execute('BEGIN')
                for table_name in tables_to_clean:
                    # Validate identifier
                    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table_name):
                        continue
                    cursor.execute(f"DELETE FROM \"{table_name}\" WHERE school_id != ?", (school_id,))
                conn.commit()
            except Exception:
                conn.rollback()
                conn.close()
                raise
            conn.close()
            
            # Lire le fichier temporaire modifié
            with open(tmp_path, 'rb') as f:
                data = f.read()
            
            response = Response(data, mimetype='application/octet-stream')
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.unlink(tmp_path)
            except:
                pass
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors du téléchargement: {str(e)}', 'danger')
        return redirect(url_for('admin.academic_years'))


@admin_bp.route('/upload-school-database/<int:school_id>/<int:year_id>', methods=['POST'])
@login_required
@require_super_admin
def upload_school_database(school_id, year_id):
    """Restaurer une base de données pour une école spécifique"""
    if not current_app.config.get('ALLOW_RESTORE_DOWNLOAD', False):
        flash('Les opérations de sauvegarde/restauration sont temporairement désactivées.', 'warning')
        return redirect(url_for('admin.academic_years'))
    if not _db_is_sqlite():
        flash('La sauvegarde/restauration par fichier .db est uniquement disponible avec SQLite.', 'warning')
        return redirect(url_for('admin.academic_years'))
    try:
        # Valider que l'école et l'année existent
        school = School.query.get_or_404(school_id)
        year = AcademicYear.query.get_or_404(year_id)
        
        # Vérifier si un fichier a été uploadé
        if 'database_file' not in request.files:
            flash('Aucun fichier sélectionné.', 'danger')
            return redirect(url_for('admin.academic_years'))
        
        file = request.files['database_file']
        
        if file.filename == '':
            flash('Aucun fichier sélectionné.', 'danger')
            return redirect(url_for('admin.academic_years'))
        
        # Vérifier que c'est un fichier .db
        if not file.filename.endswith('.db'):
            flash('Le fichier doit être une base de données (.db).', 'danger')
            return redirect(url_for('admin.academic_years'))
        
        # Sauvegarder temporairement le fichier uploadé
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = tmp.name
        
        try:
            file.save(tmp_path)
            
            # Vérifier que c'est une DB SQLite valide
            try:
                conn_test = sqlite3.connect(tmp_path)
                cursor_test = conn_test.cursor()
                cursor_test.execute("SELECT name FROM sqlite_master WHERE type='table';")
                conn_test.close()
            except Exception as e:
                flash('Le fichier uploadé n\'est pas une base de données SQLite valide.', 'danger')
                return redirect(url_for('admin.academic_years'))
            
            # Importer les données de l'école depuis le fichier uploadé vers la DB principale
            basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            main_db_path = os.path.join(basedir, 'gescoapp.db')
            
            # Connexion à la DB source (fichier uploadé)
            conn_source = sqlite3.connect(tmp_path)
            cursor_source = conn_source.cursor()
            
            # Connexion à la DB principale
            conn_main = sqlite3.connect(main_db_path)
            cursor_main = conn_main.cursor()
            
            # Create a snapshot before restoring
            snapshot_dir = os.path.join(basedir, 'backups')
            os.makedirs(snapshot_dir, exist_ok=True)
            snapshot_name = f'{school.name.replace(" ", "_")}_pre_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            snapshot_path = os.path.join(snapshot_dir, secure_filename(snapshot_name))
            shutil.copy2(main_db_path, snapshot_path)
            
            # Récupérer la liste des tables avec school_id
            # Use SQLAlchemy metadata as whitelist
            allowed_tables = []
            try:
                for tname, table in db.metadata.tables.items():
                    colnames = [c.name for c in table.columns]
                    if 'school_id' in colnames:
                        allowed_tables.append(tname)
            except Exception:
                allowed_tables = ['students', 'grades', 'conduct_grades', 'attendance_records', 'courses', 'sections']

            # Determine tables present in main DB
            cursor_main.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [r[0] for r in cursor_main.fetchall()]

            tables_to_restore = [t for t in existing_tables if t in allowed_tables]
            
            # Restaurer les données de l'école
            # Pre-check: reject if source DB contains triggers/views or suspicious SQL
            cursor_source.execute("SELECT type, sql FROM sqlite_master WHERE type IN ('trigger','view') OR sql LIKE '%PRAGMA%' OR sql LIKE '%ATTACH%';")
            suspicious = cursor_source.fetchall()
            if suspicious:
                conn_source.close()
                conn_main.close()
                flash('Le fichier uploadé contient des objets non autorisés (triggers/views/PRAGMA). Restaurations bloquées.', 'danger')
                return redirect(url_for('admin.academic_years'))

            try:
                cursor_main.execute('BEGIN')
                for table_name in tables_to_restore:
                    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table_name):
                        continue

                    # Get allowed columns from metadata
                    try:
                        sa_table = db.metadata.tables.get(table_name)
                        allowed_cols = [c.name for c in sa_table.columns]
                    except Exception:
                        # fallback: infer from main DB
                        cursor_main.execute(f"PRAGMA table_info(\"{table_name}\")")
                        allowed_cols = [r[1] for r in cursor_main.fetchall()]

                    # Read rows from source for this school
                    cursor_source.execute(f"SELECT * FROM \"{table_name}\" WHERE school_id = ?", (school_id,))
                    rows = cursor_source.fetchall()
                    cols_info = [d[0] for d in cursor_source.description] if cursor_source.description else []

                    if not rows:
                        continue

                    # Validate column names and build insert
                    safe_cols = [c for c in cols_info if c in allowed_cols and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', c)]
                    if not safe_cols:
                        continue

                    # Delete old rows for this school
                    cursor_main.execute(f"DELETE FROM \"{table_name}\" WHERE school_id = ?", (school_id,))

                    placeholders = ','.join(['?' for _ in safe_cols])
                    quoted_cols = ','.join([f'\"{c}\"' for c in safe_cols])
                    insert_query = f"INSERT INTO \"{table_name}\" ({quoted_cols}) VALUES ({placeholders})"

                    # Map rows to safe_cols order
                    insert_rows = []
                    for r in rows:
                        # cursor_source.description gives order of columns in source select
                        row_map = dict(zip(cols_info, r))
                        insert_rows.append(tuple(row_map[c] for c in safe_cols))

                    if insert_rows:
                        cursor_main.executemany(insert_query, insert_rows)
                conn_main.commit()
            except Exception:
                conn_main.rollback()
                conn_source.close()
                conn_main.close()
                raise
            conn_source.close()
            conn_main.close()
            
            # Record activity log for restore
            try:
                activity = ActivityLog(
                    user_id=current_user.id,
                    action_type='restore_school_database',
                    action_description=f"Restauration de la base de données pour l'école {school.name} ({school.id}) et l'année {year.name}.",
                    related_model='School',
                    related_id=school.id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent') or None,
                )
                db.session.add(activity)
                db.session.commit()
            except Exception:
                db.session.rollback()
                # Continue even if logging fails
            
            flash(f'✅ Base de données restaurée avec succès pour {school.name} ({year.name})!', 'success')
            return redirect(url_for('admin.academic_years'))
            
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.unlink(tmp_path)
            except:
                pass
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors de la restauration: {str(e)}', 'danger')
        return redirect(url_for('admin.academic_years'))


@admin_bp.route('/sections', methods=['GET', 'POST'])
@login_required
def sections(school_slug=None):
    school_id = get_school_id_for_admin_context()
    schools = []
    selected_school_id = request.args.get('school_id', type=int)

    if current_user.is_super_admin() and not school_id:
        schools = School.query.order_by(School.name).all()
        if selected_school_id:
            school_id = selected_school_id

    if request.method == 'POST' and current_user.is_super_admin() and not school_id:
        school_id = request.form.get('school_id', type=int) or selected_school_id

    if not school_id:
        flash('Veuillez sélectionner une école pour gérer les sections.', 'info')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if request.is_json:
            data = request.get_json() or {}
            rows = data.get('rows') or []
        else:
            levels = request.form.getlist('level') or request.form.getlist('level[]')
            classes = request.form.getlist('class_name') or request.form.getlist('class_name[]')
            rows = list(zip(levels, classes)) if levels and classes else []

        if not name:
            flash('Le nom de section est obligatoire.', 'danger')
        else:
            if not rows:
                rows = [('1', 'A')]

            created = 0
            for level, class_name in rows:
                level = (level or '1').strip() or '1'
                class_name = (class_name or 'A').strip() or 'A'
                exists = Section.query.filter_by(
                    school_id=school_id,
                    name=name,
                    level=level,
                    class_name=class_name,
                ).first()
                if exists:
                    continue
                section = Section(
                    school_id=school_id,
                    name=name,
                    level=level,
                    class_name=class_name,
                )
                db.session.add(section)
                created += 1

            if created > 0:
                db.session.commit()
                flash('Section créée avec succès.', 'success')
            else:
                flash('Aucun nouvel enregistrement à créer. La structure existe déjà.', 'warning')
        return redirect(url_for('admin.sections', school_slug=school_slug))

    sections_query = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name)
    section_groups = group_sections_for_display(sections_query.all())
    return render_template(
        'admin/sections.html',
        sections=section_groups,
        schools=schools,
        selected_school_id=school_id,
    )


@admin_bp.route('/sections/<int:section_id>/students')
@login_required
def section_students(section_id, school_slug=None):
    section = Section.query.get_or_404(section_id)
    context_school_id = get_school_id_for_admin_context()

    if context_school_id and section.school_id != context_school_id:
        flash('Acces non autorise a cette section.', 'danger')
        return redirect(url_for('admin.sections', school_slug=school_slug))

    if not current_user.is_super_admin() and section.school_id != current_user.school_id:
        flash('Acces non autorise.', 'danger')
        return redirect(url_for('admin.sections', school_slug=school_slug))

    school_id = context_school_id or section.school_id
    academic_year = session.get('academic_year', '2025 - 2026')

    section_rows = (
        Section.query
        .filter_by(school_id=school_id, name=section.name)
        .order_by(Section.level, Section.class_name)
        .all()
    )
    section_ids = [item.id for item in section_rows]

    students_by_section_id = {}
    if section_ids:
        students = (
            Student.query
            .filter(
                Student.school_id == school_id,
                Student.academic_year == academic_year,
                Student.section_id.in_(section_ids),
            )
            .order_by(Student.last_name, Student.first_name)
            .all()
        )
        for student in students:
            students_by_section_id.setdefault(student.section_id, []).append(student)

    levels_map = {}
    total_students = 0
    for item in section_rows:
        level_name = item.level or 'N.D.'
        class_name = item.class_name or 'N.D.'
        class_students = students_by_section_id.get(item.id, [])
        total_students += len(class_students)

        level_entry = levels_map.setdefault(level_name, {})
        class_entry = level_entry.setdefault(class_name, {
            'class_name': class_name,
            'section_id': item.id,
            'students': [],
        })
        class_entry['students'].extend(class_students)

    levels_payload = []
    for level_name in sorted(levels_map.keys(), key=lambda value: (len(str(value)), str(value).lower())):
        classes_payload = []
        level_count = 0
        for class_name in sorted(levels_map[level_name].keys(), key=lambda value: str(value).lower()):
            class_payload = levels_map[level_name][class_name]
            class_students = sorted(
                class_payload['students'],
                key=lambda student: (
                    (student.last_name or '').lower(),
                    (student.first_name or '').lower(),
                ),
            )
            level_count += len(class_students)
            classes_payload.append({
                'class_name': class_payload['class_name'],
                'section_id': class_payload['section_id'],
                'students': class_students,
            })
        levels_payload.append({
            'level_name': level_name,
            'student_count': level_count,
            'classes': classes_payload,
        })

    back_url = url_for('admin.sections', school_slug=school_slug)
    if current_user.is_super_admin() and not school_slug:
        back_url = url_for('admin.sections', school_id=school_id)

    return render_template(
        'admin/section_students.html',
        section_group=SimpleNamespace(
            name=section.name,
            school=section.school,
            level_count=len(levels_payload),
            class_count=sum(len(level['classes']) for level in levels_payload),
            student_count=total_students,
            levels=levels_payload,
        ),
        academic_year=academic_year,
        back_url=back_url,
        student_actions_enabled=bool(context_school_id or not current_user.is_super_admin()),
    )


@admin_bp.route('/sections/config/save', methods=['POST'])
@login_required
def save_section_config(school_slug=None):
    school_id = get_school_id_for_admin_context()
    if not school_id:
        return jsonify({'success': False, 'error': 'École non spécifiée.'}), 400

    data = request.get_json() or {}
    section_id = data.get('section_id')
    config = data.get('config') or {}
    section = Section.query.filter_by(id=section_id, school_id=school_id).first()
    if not section:
        return jsonify({'success': False, 'error': 'Section introuvable.'}), 404

    try:
        apply_section_hierarchy_config(school_id, section.name, config, replace_existing=True)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(exc)}), 500


@admin_bp.route('/sections/<int:section_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_section(section_id, school_slug=None):
    section = Section.query.get_or_404(section_id)
    school_id = get_school_id_for_admin_context() or section.school_id
    if not current_user.is_super_admin() and section.school_id != current_user.school_id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('admin.sections', school_slug=school_slug))

    if request.method == 'POST' and request.is_json:
        data = request.get_json() or {}
        section_name = (data.get('name') or section.name).strip()
        config = data.get('config') or {}
        try:
            apply_section_hierarchy_config(section.school_id, section_name, config, replace_existing=True)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as exc:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(exc)}), 500

    related_sections = Section.query.filter_by(school_id=section.school_id, name=section.name).all()
    config = {}
    for item in related_sections:
        config.setdefault(item.level, [])
        if item.class_name not in config[item.level]:
            config[item.level].append(item.class_name)

    available_levels = [str(i) for i in range(1, 9)]
    return render_template(
        'admin/edit_section.html',
        section=section,
        section_config=config,
        available_levels=available_levels,
    )


@admin_bp.route('/sections/<int:section_id>/delete', methods=['POST'])
@login_required
def delete_section(section_id, school_slug=None):
    section = Section.query.get_or_404(section_id)
    if not current_user.is_super_admin() and section.school_id != current_user.school_id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('admin.sections', school_slug=school_slug))

    sections = Section.query.filter_by(school_id=section.school_id, name=section.name).all()
    section_ids = [s.id for s in sections]
    
    if section_ids:
        student_count = Student.query.filter(Student.section_id.in_(section_ids)).count()
        if student_count > 0:
            flash(f"Impossible de supprimer cette section car {student_count} élève(s) y sont inscrit(s). Veuillez d'abord les réaffecter ou réinitialiser les classes.", 'danger')
            return redirect(url_for('admin.sections', school_slug=school_slug))
            
        # Détacher les cours rattachés à cette section
        Course.query.filter(Course.section_id.in_(section_ids)).update({'section_id': None}, synchronize_session=False)

    Section.query.filter_by(school_id=section.school_id, name=section.name).delete(synchronize_session=False)
    db.session.commit()
    flash('Section supprimée.', 'success')
    return redirect(url_for('admin.sections', school_slug=school_slug))


@admin_bp.route('/class-promotion', methods=['GET', 'POST'])
@login_required
def class_promotion(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    if not school_id:
        flash('Aucune école associée.', 'danger')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    current_year = session.get('academic_year', '2025 - 2026')
    years = AcademicYear.query.order_by(AcademicYear.name.desc()).all()
    prev_year = None
    for index, year in enumerate(years):
        if year.name == current_year and index + 1 < len(years):
            prev_year = SimpleNamespace(year=years[index + 1].name, obj=years[index + 1])
            break

    prev_students = []
    dest_sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name).all()
    if prev_year:
        prev_students = Student.query.filter_by(school_id=school_id, academic_year=prev_year.year).order_by(Student.last_name).all()

    if request.method == 'POST':
        student_ids = request.form.getlist('student_ids')
        dest_section_id = request.form.get('dest_section_id', type=int)
        if not student_ids or not dest_section_id:
            flash('Sélectionnez des élèves et une classe de destination.', 'warning')
            return redirect(url_for('admin.class_promotion', school_slug=school_slug))

        promoted = 0
        for student_id in student_ids:
            student = Student.query.filter_by(id=student_id, school_id=school_id).first()
            if not student:
                continue
            student.section_id = dest_section_id
            student.academic_year = current_year
            promoted += 1
        db.session.commit()
        flash(f'{promoted} élève(s) promu(s) vers la nouvelle année scolaire.', 'success')
        return redirect(url_for('admin.class_promotion', school_slug=school_slug))

    return render_template(
        'admin/class_promotion.html',
        prev_year=prev_year,
        prev_students=prev_students,
        dest_sections=dest_sections,
    )
