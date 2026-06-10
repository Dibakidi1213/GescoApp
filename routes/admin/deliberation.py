from flask import render_template, request, redirect, url_for, flash, session
from flask_login import current_user
from models import db, DeliberationCriteria, DeliberationResult, Section, Student, BulletinConfig, Grade, Course, BulletinBranch
from routes.admin import admin_bp
from routes.admin.services import build_centralization_context

LEVEL_GROUPS = {
    '1ere_2eme': ['7è', '8è'],
    '3eme_humanites': ['1è'],
    '4eme_humanites': ['2è'],
    '5eme_humanites': ['3è'],
    '6eme_humanites': ['4è']
}

# Libellés lisibles pour l'affichage dans les templates
LEVEL_GROUP_LABELS = {
    '1ere_2eme': '7è & 8è année',
    '3eme_humanites': '1è Humanités',
    '4eme_humanites': '2è Humanités',
    '5eme_humanites': '3è Humanités',
    '6eme_humanites': '4è Humanités'
}

@admin_bp.route('/deliberation/config', methods=['GET', 'POST'])
def deliberation_config(school_slug=None):
    school_id = current_user.school_id
    year = session.get('academic_year', '2025 - 2026')
    
    if request.method == 'POST':
        for group in LEVEL_GROUPS.keys():
            criteria = DeliberationCriteria.query.filter_by(
                school_id=school_id, academic_year=year, level_group=group
            ).first()
            
            if not criteria:
                criteria = DeliberationCriteria(school_id=school_id, academic_year=year, level_group=group)
                db.session.add(criteria)
                
            criteria.min_percentage_auto = request.form.get(f'{group}_min_percentage_auto', 50, type=float)
            criteria.max_echecs_auto = request.form.get(f'{group}_max_echecs_auto', 0, type=int)
            criteria.min_percentage_repechage = request.form.get(f'{group}_min_percentage_repechage', 50, type=float)
            criteria.max_echecs_repechage = request.form.get(f'{group}_max_echecs_repechage', 6, type=int)
            criteria.min_score_specific_branch = request.form.get(f'{group}_min_score_specific_branch', 30, type=float)
            criteria.min_score_option_branch = request.form.get(f'{group}_min_score_option_branch', 35, type=float)
            criteria.min_percentage_redoublement = request.form.get(f'{group}_min_percentage_redoublement', 45, type=float)
            criteria.require_good_conduct = request.form.get(f'{group}_require_good_conduct') == '1'
            criteria.max_mauvaise_conduite = request.form.get(f'{group}_max_mauvaise_conduite', 2, type=int)
            criteria.min_percentage_exclusion = request.form.get(f'{group}_min_percentage_exclusion', 45, type=float)
            
        db.session.commit()
        flash("Critères de délibération mis à jour avec succès.", "success")
        return redirect(url_for('admin.deliberation_config'))
        
    criteria_list = DeliberationCriteria.query.filter_by(school_id=school_id, academic_year=year).all()
    criteria_dict = {c.level_group: c for c in criteria_list}
    
    return render_template('admin/deliberation_config.html',
                           criteria_dict=criteria_dict,
                           groups=LEVEL_GROUPS.keys(),
                           group_labels=LEVEL_GROUP_LABELS)

@admin_bp.route('/deliberation/execute', methods=['GET', 'POST'])
def deliberation_execute(school_slug=None):
    school_id = current_user.school_id
    year = session.get('academic_year', '2025 - 2026')
    sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name).all()
    
    selected_section_id = request.values.get('section_id', type=int)
    selected_period = request.values.get('period', 'ANNEE')
    
    context = {
        'sections': sections,
        'selected_section_id': selected_section_id,
        'selected_period': selected_period,
        'periods': ['1èP', '2èP', 'EXA1', '3èP', '4èP', 'EXA2', 'ANNEE'],
        'deliberation_rows': [],
        'criteria': None
    }
    
    if selected_section_id:
        section = Section.query.get(selected_section_id)
        context['selected_section'] = section
        
        # Trouver le level_group
        level_group = '1ere_2eme'
        for group, levels in LEVEL_GROUPS.items():
            if any(str(section.level).startswith(l) for l in levels):
                level_group = group
                break
                
        criteria = DeliberationCriteria.query.filter_by(
            school_id=school_id, academic_year=year, level_group=level_group
        ).first()
        context['criteria'] = criteria
        
        # On utilise le même contexte que la centralisation pour récupérer les pourcentages et échecs
        centralization_context = build_centralization_context(school_id, selected_section_id, selected_period, year)
        
        if request.method == 'POST' and criteria:
            # Effectuer la délibération
            for row in centralization_context.get('centralization_rows', []):
                decision = calculate_deliberation(row, criteria, centralization_context['course_columns'])
                
                # Sauvegarder
                result = DeliberationResult.query.filter_by(
                    student_id=row['student'].id, academic_year=year, period=selected_period
                ).first()
                
                if not result:
                    result = DeliberationResult(
                        school_id=school_id, student_id=row['student'].id,
                        academic_year=year, period=selected_period
                    )
                    db.session.add(result)
                    
                result.total_percentage = row['percentage']
                # Count echecs manually based on category and capture failed course titles
                echecs_count = 0
                failed_courses = []
                for i, col in enumerate(centralization_context['course_columns']):
                    pts = row['course_points'][i]
                    max_pts = col['max_points']
                    if pts is not None and max_pts and (pts / max_pts) < 0.5:
                        echecs_count += 1
                        # col is a dict with 'course' key
                        course = col.get('course')
                        if course and hasattr(course, 'title') and course.title:
                            # Format course name: capitalize first letter, trim whitespace
                            course_name = course.title.strip()
                            if course_name:
                                failed_courses.append(course_name)
                
                result.echecs_count = echecs_count
                # Join course names with semicolon + space for better readability
                result.notes = '; '.join(failed_courses) if failed_courses else None
                result.decision = decision
                
            db.session.commit()
            flash(f"Délibération effectuée pour {section.name} {section.level}.", "success")
            
        # Charger les résultats
        results = DeliberationResult.query.filter_by(
            school_id=school_id, academic_year=year, period=selected_period
        ).all()
        results_by_student = {r.student_id: r for r in results}
        
        deliberation_rows = []
        for row in centralization_context.get('centralization_rows', []):
            d_row = row.copy()
            
            # Recalculate echecs to show
            echecs = []
            for i, col in enumerate(centralization_context['course_columns']):
                pts = row['course_points'][i]
                max_pts = col['max_points']
                if pts is not None and max_pts and (pts / max_pts) < 0.5:
                    echecs.append({
                        'course': col['course'].title,
                        'category': col['course'].branch.category if col['course'].branch else 'general',
                        'percent': (pts / max_pts) * 100
                    })
            
            d_row['echecs'] = echecs
            d_row['result'] = results_by_student.get(row['student'].id)
            deliberation_rows.append(d_row)
            
        context['deliberation_rows'] = deliberation_rows
        
    return render_template('admin/deliberation.html', **context)

def calculate_deliberation(row, criteria, course_columns):
    percentage = float(row['percentage'] or 0)
    
    # Evaluer les échecs
    echecs = []
    has_echec_specifique_critique = False
    has_echec_option_critique = False
    
    for i, col in enumerate(course_columns):
        pts = row['course_points'][i]
        max_pts = col['max_points']
        if pts is not None and max_pts and (pts / max_pts) < 0.5:
            percent_branch = (pts / max_pts) * 100
            course = col.get('course')
            category = 'general'
            if course and hasattr(course, 'branch') and course.branch:
                category = course.branch.category
            echecs.append({'category': category, 'percent': percent_branch})
            
            if category == 'specifique' and percent_branch < float(criteria.min_score_specific_branch):
                has_echec_specifique_critique = True
            if category == 'option' and percent_branch < float(criteria.min_score_option_branch):
                has_echec_option_critique = True

    echecs_count = len(echecs)
    
    # Exclusion
    if percentage < float(criteria.min_percentage_exclusion):
        return 'EXCLUSION'
        
    # Passage Automatique
    if percentage >= float(criteria.min_percentage_auto) and echecs_count <= criteria.max_echecs_auto:
        return 'PASSAGE AUTOMATIQUE'
        
    # Repêchage
    if percentage >= float(criteria.min_percentage_repechage) and echecs_count <= criteria.max_echecs_repechage:
        if has_echec_specifique_critique or has_echec_option_critique:
            return 'ECHEC DELIBERABLE (REFUSE POUR BRANCHE SPECIFIQUE/OPTION)'
        return 'PASSAGE APRES REPECHAGE'
        
    # Redoublement
    if percentage >= float(criteria.min_percentage_redoublement):
        return 'REDOUBLEMENT'
        
    return 'EXCLUSION'
