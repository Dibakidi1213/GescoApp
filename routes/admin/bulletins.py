import json
from datetime import datetime

from flask import render_template, request, jsonify, g, session, Response
from flask_login import login_required, current_user
from sqlalchemy import text

from models import (
    BulletinBranch,
    BulletinConfig,
    Course,
    School,
    Section,
    db,
)
from routes.admin.helpers import get_school_id_for_admin_context, resolve_admin_school_id
from routes.admin.services import (
    find_section_for_level,
    levels_payload_for_section_name,
    resolve_section_reference,
    _serialize_branches,
)
from routes.admin import admin_bp
from url_utils import decode_id_or_int


def _save_bulletin_config_data(school_id, section, level, branches_data, year, ige_number=None):
    if not section:
        raise ValueError('Section non trouvée')

    config = BulletinConfig.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        level=level,
        academic_year=year,
    ).first()
    
    preserve_validation = False
    if config and config.validated:
        preserve_validation = True
    
    if not config:
        db.session.expire_all()
        config = BulletinConfig.query.filter_by(
            school_id=school_id,
            section_id=section.id,
            level=level,
            academic_year=year,
        ).first()

    if not config:
        try:
            config = BulletinConfig(
                school_id=school_id,
                section_id=section.id,
                level=level,
                academic_year=year,
            )
            db.session.add(config)
            db.session.flush()
        except Exception:
            db.session.rollback()
            db.session.expire_all()
            config = BulletinConfig.query.filter_by(
                school_id=school_id,
                section_id=section.id,
                level=level,
                academic_year=year,
            ).first()
            if not config:
                row = db.session.execute(
                    text("SELECT id FROM bulletin_configs WHERE school_id=:sid AND section_id=:secid AND level=:lvl AND academic_year=:ay"),
                    {"sid": school_id, "secid": section.id, "lvl": level, "ay": year},
                ).fetchone()
                if row:
                    config = db.session.get(BulletinConfig, row[0])
        
        # Use provided IGE number or generate one for new configs
        if ige_number:
            config.ige_number = ige_number
        elif not config.ige_number:
            config.ige_number = config.generate_ige_number()
    else:
        # For existing configs, update IGE if provided
        if ige_number:
            config.ige_number = ige_number
        # Update section_id reference to the current section
        config.section_id = section.id

    config.academic_year = year
    
    # Only reset validation if this is a new config or if it wasn't previously validated
    if not preserve_validation:
        config.validated = False
        config.validated_at = None
        config.validated_by_user_id = None
    
    branch_ids = [b.id for b in BulletinBranch.query.filter_by(config_id=config.id).all()]
    if branch_ids:
        conn = db.session.connection()
        placeholders = ', '.join([str(bid) for bid in branch_ids])
        conn.execute(db.text(f"UPDATE courses SET branch_id = NULL WHERE branch_id IN ({placeholders})"))
        db.session.flush()
    BulletinBranch.query.filter_by(config_id=config.id).delete(synchronize_session=False)

    for index, branch_data in enumerate(branches_data):
        branch_type = branch_data.get('type', 'branch')
        branch = BulletinBranch(
            config_id=config.id,
            type=branch_type,
            category=branch_data.get('category', 'general'),
            name=branch_data.get('name') or '',
            domain=branch_data.get('domain') if branch_type in ('domain', 'branch') else '',
            subdomain=branch_data.get('subdomain') if branch_type in ('subdomain', 'branch') else '',
            order=index + 1,
            max_value=branch_data.get('max_value', 20),
            max_period_1=branch_data.get('max_period_1', branch_data.get('max_value', 10)),
            max_period_2=branch_data.get('max_period_2', branch_data.get('max_period_1', 10)),
            max_exam_1=branch_data.get('max_exam_1', 20),
            max_period_3=branch_data.get('max_period_3', branch_data.get('max_period_1', 10)),
            max_period_4=branch_data.get('max_period_4', branch_data.get('max_period_1', 10)),
            max_exam_2=branch_data.get('max_exam_2', branch_data.get('max_exam_1', 20)),
            include_period_1=branch_data.get('include_period_1', True),
            include_period_2=branch_data.get('include_period_2', True),
            include_comp_1=branch_data.get('include_comp_1', True),
            include_period_3=branch_data.get('include_period_3', True),
            include_period_4=branch_data.get('include_period_4', True),
            include_comp_2=branch_data.get('include_comp_2', True),
        )
        db.session.add(branch)

    db.session.commit()
    return config


def _serialize_config_response(config, section_name=None):
    if not config:
        return {
            'id': None,
            'section_name': None,
            'level': None,
            'ige_number': None,
            'validated': False,
            'validated_at': None,
            'validated_by': None,
            'branches': _serialize_branches(None, section_name),
        }

    branches = _serialize_branches(config, section_name or (config.section.name if config.section else None))
    payload = {
        'id': config.id,
        'section_name': config.section.name if config.section else None,
        'level': config.level,
        'ige_number': config.ige_number,
        'validated': bool(config.validated),
        'validated_at': config.validated_at.isoformat() if config.validated_at else None,
        'validated_by': config.validated_by_user.full_name if config.validated_by_user else None,
        'branches': branches,
    }
    return payload


@admin_bp.route('/bulletins')
@admin_bp.route('/bulletins/config')
@login_required
def bulletins(school_slug=None):
    return _render_bulletins_page(school_slug)


@admin_bp.route('/bulletins/preview')
@login_required
def bulletin_preview(school_slug=None):
    return _render_bulletins_page(school_slug, preview_only=True)


@admin_bp.route('/bulletins-config')
@login_required
def bulletins_config(school_slug=None):
    return _render_bulletins_page(school_slug)


def _render_bulletins_page(school_slug=None, preview_only=False):
    school_id = get_school_id_for_admin_context()
    selected_school_id = decode_id_or_int(request.args.get('school_id'))
    raw_section_value = request.args.get('section_name') or request.args.get('section_id')
    selected_level = request.args.get('level')

    schools = []
    school = None
    sections = []
    selected_section_name = None

    if current_user.is_super_admin() and not school_id:
        # Superadmin: list all schools and show sections across all schools unless a school is selected
        schools = School.query.order_by(School.name).all()
        if selected_school_id:
            school_id = selected_school_id
            school = School.query.get(selected_school_id)
            sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level).all()
        else:
            sections = Section.query.order_by(Section.name, Section.level).all()
        section_names = sorted({section.name for section in sections})
    elif school_id:
        school = School.query.get(school_id)
        sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level).all()
        section_names = sorted({section.name for section in sections})
    else:
        # No school context available
        return render_template(
            'admin/bulletins.html',
            sections=[],
            section_names=[],
            schools=schools,
            school=school,
            selected_school_id=selected_school_id,
            selected_section_name=selected_section_name,
            selected_level=selected_level,
            g_school_slug=getattr(g, 'school_slug', None),
        )

    if raw_section_value:
        section = resolve_section_reference(school_id, raw_section_value)
        selected_section_name = section.name if section else raw_section_value

    return render_template(
        'admin/bulletins.html',
        sections=sections,
        section_names=section_names,
        schools=schools,
        school=school,
        selected_school_id=school_id,
        selected_section_name=selected_section_name,
        selected_level=selected_level,
        preview_only=preview_only,
        g_school_slug=getattr(g, 'school_slug', None),
    )


@admin_bp.route('/api/bulletin-levels/<section_ref>')
@login_required
def get_bulletin_levels(section_ref, school_slug=None):
    school_id = resolve_admin_school_id(decode_id_or_int(request.args.get('school_id')))
    is_super_admin = current_user.is_super_admin()

    if not school_id and is_super_admin:
        levels = levels_payload_for_section_name(section_ref)
        if not levels:
            return jsonify({'error': 'Section introuvable'}), 404
        return jsonify(levels)

    if not school_id:
        return jsonify({'error': 'École non spécifiée pour la configuration des bulletins.'}), 400

    section = resolve_section_reference(school_id, section_ref)
    if not section:
        return jsonify({'error': 'Section introuvable'}), 404

    return jsonify(levels_payload_for_section_name(section.name, school_id))


@admin_bp.route('/api/section/<section_name>')
@login_required
def get_section(section_name, school_slug=None):
    school_id = resolve_admin_school_id(decode_id_or_int(request.args.get('school_id')))
    is_super_admin = current_user.role == 'super_admin'
    
    if not school_id:
        if is_super_admin:
            # Super admin: resolve the section across all schools when no school is selected
            section = Section.query.filter_by(name=section_name).first()
            if not section:
                return jsonify({'error': 'Section non trouvée'}), 404
            school_id = section.school_id
        else:
            # School admin: use their school
            school_id = get_school_id_for_admin_context()
    
    if not school_id:
        return jsonify({'error': 'École non spécifiée.'}), 400

    section = Section.query.filter_by(school_id=school_id, name=section_name).first()
    if not section:
        return jsonify({'error': 'Section non trouvée'}), 404

    return jsonify({
        'id': section.id,
        'name': section.name,
        'level': section.level,
        'class_name': section.class_name,
        'school_id': section.school_id
    })


@admin_bp.route('/api/section/<int:section_id>', methods=['PUT'])
@login_required
def update_section(section_id, school_slug=None):
    school_id = resolve_admin_school_id(decode_id_or_int(request.args.get('school_id')))
    is_super_admin = current_user.role == 'super_admin'
    
    if not school_id:
        if is_super_admin:
            # Super admin: find section across all schools
            section = Section.query.get(section_id)
            if not section:
                return jsonify({'error': 'Section non trouvée'}), 404
            school_id = section.school_id
        else:
            # School admin: use their school
            school_id = get_school_id_for_admin_context()
    
    if not school_id:
        return jsonify({'error': 'École non spécifiée.'}), 400

    section = Section.query.filter_by(id=section_id, school_id=school_id).first()
    if not section:
        return jsonify({'error': 'Section non trouvée'}), 404

    data = request.json or {}
    name = data.get('name')
    level = data.get('level')
    class_name = data.get('class_name')

    if not name or not level or not class_name:
        return jsonify({'error': 'Nom, niveau et classe sont requis'}), 400

    # Check if another section with the same name/level/class_name exists in the same school
    existing = Section.query.filter(
        Section.school_id == school_id,
        Section.name == name,
        Section.level == level,
        Section.class_name == class_name,
        Section.id != section_id
    ).first()
    if existing:
        return jsonify({'error': 'Une section avec ce nom, niveau et classe existe déjà'}), 400

    section.name = name
    section.level = level
    section.class_name = class_name
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Section modifiée avec succès',
        'section': {
            'id': section.id,
            'name': section.name,
            'level': section.level,
            'class_name': section.class_name,
            'school_id': section.school_id
        }
    })


@admin_bp.route('/api/bulletin-config/<section_ref>/<level>')
@login_required
def get_bulletin_config(section_ref, level, school_slug=None):
    school_id = resolve_admin_school_id(decode_id_or_int(request.args.get('school_id')))
    is_super_admin = current_user.role == 'super_admin'
    
    if not school_id:
        if is_super_admin:
            # Super admin: resolve the section across all schools when no school is selected
            section = find_section_for_level(None, section_ref, level)
            if not section:
                return jsonify({'error': 'Section non trouvée'}), 404
            school_id = section.school_id
        else:
            # School admin: use their school
            school_id = get_school_id_for_admin_context()
    
    if not school_id:
        return jsonify({'error': 'École non spécifiée pour la configuration des bulletins.'}), 400

    year = session.get('academic_year', '2025 - 2026')
    section = find_section_for_level(school_id, section_ref, level)
    if not section:
        return jsonify({'error': 'Section non trouvée'}), 404

    config = BulletinConfig.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        level=level,
        academic_year=year,
    ).first()

    return jsonify(_serialize_config_response(config, section.name))


@admin_bp.route('/api/bulletin-config', methods=['POST'])
@login_required
def save_bulletin_config(school_slug=None):
    data = request.json or {}
    section_id = data.get('section_id')
    section_name = data.get('section_name')
    level = data.get('level')
    branches_data = data.get('branches', [])
    ige_number = data.get('ige_number')
    year = session.get('academic_year', '2025 - 2026')

    school_id = resolve_admin_school_id(decode_id_or_int(request.args.get('school_id')))
    
    # Check if current user is super_admin
    is_super_admin = current_user.role == 'super_admin'
    
    if is_super_admin:
        # Superadmin: Apply configuration to ALL schools
        if not section_name or not level:
            return jsonify({'error': 'Section ou niveau manquant pour la configuration globale.'}), 400
        
        try:
            schools = School.query.filter_by(is_active=True).all()
            if not schools:
                return jsonify({'error': 'Aucune école active trouvée.'}), 404
            
            configs_saved = 0
            for school in schools:
                # For each school, find the matching section
                section = Section.query.filter_by(
                    school_id=school.id,
                    name=section_name,
                    level=level
                ).first()
                
                if section:
                    _save_bulletin_config_data(school.id, section, level, branches_data, year, ige_number)
                    configs_saved += 1
            
            if configs_saved == 0:
                return jsonify({'error': f'Aucune section "{section_name}" niveau {level} trouvée dans les écoles.'}), 404
            
            return jsonify({
                'success': True,
                'message': f'Configuration appliquée à {configs_saved} école(s) avec succès',
            })
        except ValueError as exc:
            db.session.rollback()
            return jsonify({'error': str(exc)}), 404
        except Exception as exc:
            db.session.rollback()
            return jsonify({'error': str(exc)}), 500
    else:
        # School admin: Apply configuration to their school only
        if not school_id:
            return jsonify({'error': 'École non spécifiée pour la configuration des bulletins.'}), 400

        section = None
        if section_id:
            section = Section.query.filter_by(id=section_id, school_id=school_id).first()
        elif section_name and level:
            section = Section.query.filter_by(school_id=school_id, name=section_name, level=level).first()

        if not section or not level:
            return jsonify({'error': 'Section ou niveau manquant.'}), 400

        try:
            _save_bulletin_config_data(school_id, section, level, branches_data, year, ige_number)
            return jsonify({
                'success': True,
                'message': 'Configuration mise à jour avec succès',
            })
        except ValueError as exc:
            db.session.rollback()
            return jsonify({'error': str(exc)}), 404
        except Exception as exc:
            db.session.rollback()
            return jsonify({'error': str(exc)}), 500


@admin_bp.route('/api/bulletin-config/validate', methods=['POST'])
@login_required
def validate_bulletin_config(school_slug=None):
    data = request.json or {}
    section_id = data.get('section_id')
    section_name = data.get('section_name')
    level = data.get('level')
    year = session.get('academic_year', '2025 - 2026')

    school_id = resolve_admin_school_id(decode_id_or_int(request.args.get('school_id')))
    if not school_id:
        return jsonify({'error': 'École non spécifiée.'}), 400

    section = None
    if section_id:
        section = Section.query.filter_by(id=section_id, school_id=school_id).first()
    elif section_name and level:
        section = Section.query.filter_by(school_id=school_id, name=section_name, level=level).first()

    if not section or not level:
        return jsonify({'error': 'Section ou niveau manquant.'}), 400

    config = BulletinConfig.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        level=level,
        academic_year=year,
    ).first()
    if not config:
        return jsonify({'error': 'Configuration introuvable. Sauvegardez d\'abord la configuration.'}), 404

    config.validated = True
    config.validated_at = datetime.now()
    config.validated_by_user_id = current_user.id
    db.session.commit()
    return jsonify(_serialize_config_response(config, section.name))


@admin_bp.route('/api/bulletin-config/export/<section_name>/<level>')
@login_required
def export_bulletin_config(section_name, level, school_slug=None):
    school_id = resolve_admin_school_id(decode_id_or_int(request.args.get('school_id')))
    is_super_admin = current_user.role == 'super_admin'
    if not school_id:
        if is_super_admin:
            section = find_section_for_level(None, section_name, level)
            if not section:
                return jsonify({'error': 'Section introuvable'}), 404
            school_id = section.school_id
        else:
            school_id = get_school_id_for_admin_context()

    if not school_id:
        return jsonify({'error': 'École non spécifiée pour l\'exportation des bulletins.'}), 400

    section = find_section_for_level(school_id, section_name, level)
    if not section:
        return jsonify({'error': 'Section introuvable'}), 404

    config = BulletinConfig.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        level=level,
        academic_year=session.get('academic_year', '2025 - 2026'),
    ).first()

    if not config:
        return jsonify({'error': 'Configuration introuvable. Sauvegardez d\'abord la configuration.'}), 404

    payload = _serialize_config_response(config)
    payload['section_name'] = section.name
    payload['level'] = level
    payload['academic_year'] = config.academic_year
    filename = f"Bulletin_{section.name.replace(' ', '_')}_{level}.json"
    response = Response(json.dumps(payload, ensure_ascii=False, indent=2), mimetype='application/json')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# Endpoint de génération automatique supprimé - saisie manuelle uniquement

def _normalize_imported_bulletin_data(data):
    if not isinstance(data, dict):
        return None, None, None, None

    section_name = data.get('section_name') or data.get('section') or data.get('sectionName')
    level = data.get('level') or data.get('niveau')
    ige_number = data.get('ige_number')

    branches_data = data.get('branches')
    if branches_data is None:
        config_payload = data.get('config') or data.get('payload') or data.get('bulletin')
        if isinstance(config_payload, dict):
            branches_data = config_payload.get('branches')
            if not ige_number:
                ige_number = config_payload.get('ige_number')

    if branches_data is None:
        for key in ('data', 'bulletin', 'bulletin_config'):
            maybe = data.get(key)
            if isinstance(maybe, dict) and 'branches' in maybe:
                branches_data = maybe.get('branches')
                if not ige_number:
                    ige_number = maybe.get('ige_number')
                break

    return section_name, level, branches_data, ige_number


@admin_bp.route('/api/bulletin-config/import', methods=['POST'])
@login_required
def import_bulletin_config(school_slug=None):
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400

    file = request.files['file']
    try:
        data = json.load(file)
    except json.JSONDecodeError:
        return jsonify({'error': 'Le fichier JSON importé est mal formé. Vérifiez la syntaxe du fichier.'}), 400

    school_id = resolve_admin_school_id(decode_id_or_int(request.args.get('school_id')))
    if not school_id:
        return jsonify({'error': 'École non spécifiée pour l\'importation des bulletins.'}), 400

    year = session.get('academic_year', '2025 - 2026')
    file_section_name, file_level, branches_data, file_ige_number = _normalize_imported_bulletin_data(data)

    target_section_name = request.form.get('section_name') or file_section_name
    target_level = request.form.get('level') or file_level
    target_ige_number = request.form.get('ige_number') or file_ige_number

    missing_fields = []
    if not target_section_name:
        missing_fields.append('section_name')
    if not target_level:
        missing_fields.append('level')
    if not isinstance(branches_data, list) or len(branches_data) == 0:
        missing_fields.append('branches')

    if missing_fields:
        return jsonify({
            'error': 'Le fichier JSON importé est mal formé ou incomplet.',
            'missing': missing_fields,
            'details': {
                'file_section_name': file_section_name,
                'file_level': file_level,
                'branches_found': isinstance(branches_data, list),
                'branches_count': len(branches_data) if isinstance(branches_data, list) else 0,
            }
        }), 400

    section = Section.query.filter_by(school_id=school_id, name=target_section_name, level=target_level).first()
    if not section:
        return jsonify({'error': f'Section "{target_section_name}" et niveau "{target_level}" introuvables pour cette école.'}), 404

    try:
        _save_bulletin_config_data(school_id, section, target_level, branches_data, year, target_ige_number)
        return jsonify({
            'success': True,
            'message': 'Configuration importée avec succès.',
            'section_name': target_section_name,
            'level': target_level,
        })
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 404
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 500
