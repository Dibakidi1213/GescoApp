from collections import defaultdict

from models import (
    BulletinBranch,
    BulletinConfig,
    ConductGrade,
    Course,
    DeliberationResult,
    Grade,
    Section,
    Student,
    db,
)

from routes.admin.helpers import PERIODS, SCOPE_OPTIONS, normalize_text
from routes.secretary import _get_course_branch


def group_students_tree(school_id, year):
    students = (
        Student.query.filter_by(school_id=school_id, academic_year=year)
        .join(Section, Student.section_id == Section.id)
        .order_by(Section.name, Section.level, Section.class_name, Student.last_name, Student.first_name)
        .all()
    )

    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for student in students:
        section_name = student.section.name if student.section else 'Sans section'
        level_name = student.section.level if student.section else 'N.D.'
        class_name = student.section.class_name if student.section else 'N.D.'
        tree[section_name][level_name][class_name].append(student)

    grouped = []
    for section_name in sorted(tree.keys(), key=lambda value: value.lower()):
        levels_payload = []
        section_count = 0
        for level_name in sorted(tree[section_name].keys(), key=lambda value: (len(value), value)):
            classes_payload = []
            for class_name in sorted(tree[section_name][level_name].keys(), key=lambda value: value.lower()):
                class_students = tree[section_name][level_name][class_name]
                section_count += len(class_students)
                classes_payload.append({
                    'class_name': class_name,
                    'students': class_students,
                })
            levels_payload.append({
                'level_name': level_name,
                'classes': classes_payload,
            })
        grouped.append({
            'section_name': section_name,
            'student_count': section_count,
            'levels': levels_payload,
        })
    return grouped


def _get_bulletin_config_for_section(school_id, section, year):
    if not section:
        return None
    config = BulletinConfig.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        level=section.level,
        academic_year=year,
    ).order_by(BulletinConfig.updated_at.desc(), BulletinConfig.id.desc()).first()
    if config:
        return config
    config = BulletinConfig.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        level=section.level,
    ).order_by(BulletinConfig.updated_at.desc(), BulletinConfig.id.desc()).first()
    return config


def get_bulletin_config_for_student(student, school_id, year):
    """
    Get the bulletin configuration for a student's section.
    This ensures that all student bulletin visualizations use the configured model.
    
    Args:
        student: Student object
        school_id: School ID
        year: Academic year
        
    Returns:
        BulletinConfig object or None if student has no section
    """
    if not student or not student.section:
        return None
    
    return _get_bulletin_config_for_section(school_id, student.section, year)


def _is_sciences_section(section_name):
    """Check if a section is SCIENCES or SCIENTIFIQUE."""
    if not section_name:
        return False
    normalized = section_name.lower().strip()
    return 'science' in normalized or 'scientifique' in normalized


def _is_education_base_section(section_name):
    """Check if a section is EDUCATION DE BASE."""
    if not section_name:
        return False
    normalized = section_name.lower().strip()
    return 'education de base' in normalized or 'education base' in normalized


def _get_default_rdc_model():
    """
    Returns the default RDC (Official Democratic Republic of Congo) bulletin model for SCIENCES section.
    This is used when no configuration exists for a section.
    """
    return [
        {'type': 'domain', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': '', 'name': '', 'max_period_1': 0, 'max_exam_1': 0},
        {'type': 'subdomain', 'domain': '', 'subdomain': 'Sous domaine des mathématiques', 'name': '', 'max_period_1': 0, 'max_exam_1': 0},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine des mathématiques', 'name': 'Algèbre', 'max_period_1': 30, 'max_exam_1': 60},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine des mathématiques', 'name': 'Arithmétique', 'max_period_1': 10, 'max_exam_1': 20},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine des mathématiques', 'name': 'Géométrie', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine des mathématiques', 'name': 'Statistique', 'max_period_1': 10, 'max_exam_1': 20},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine des mathématiques', 'name': 'Sous total', 'max_period_1': 70, 'max_exam_1': 140},
        {'type': 'subdomain', 'domain': '', 'subdomain': 'Sous domaine des sciences de la vie et de la terre', 'name': '', 'max_period_1': 0, 'max_exam_1': 0},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine des sciences de la vie', 'name': 'Anatomie', 'max_period_1': 10, 'max_exam_1': 20},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine des sciences de la vie', 'name': 'Botanique', 'max_period_1': 10, 'max_exam_1': 20},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine des sciences de la vie', 'name': 'Zoologie', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine des sciences de la vie', 'name': 'Sous total', 'max_period_1': 40, 'max_exam_1': 80},
        {'type': 'subdomain', 'domain': '', 'subdomain': 'Sous domaine des sciences Physiques, Technologie et Tic', 'name': '', 'max_period_1': 0, 'max_exam_1': 0},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine Physique/TIC', 'name': 'Sciences Physiques', 'max_period_1': 10, 'max_exam_1': 20},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine Physique/TIC', 'name': 'Technologie', 'max_period_1': 10, 'max_exam_1': 20},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine Physique/TIC', 'name': "Techno d'info & Com(TIC)", 'max_period_1': 10, 'max_exam_1': 20},
        {'type': 'branch', 'domain': 'DOMAINE DES SCIENCES', 'subdomain': 'Sous domaine Physique/TIC', 'name': 'Sous total', 'max_period_1': 30, 'max_exam_1': 60},
        {'type': 'domain', 'domain': 'DOMAINE DES LANGUES', 'subdomain': '', 'name': '', 'max_period_1': 0, 'max_exam_1': 0},
        {'type': 'branch', 'domain': 'DOMAINE DES LANGUES', 'subdomain': '', 'name': 'Anglais', 'max_period_1': 30, 'max_exam_1': 60},
        {'type': 'branch', 'domain': 'DOMAINE DES LANGUES', 'subdomain': '', 'name': 'Français', 'max_period_1': 50, 'max_exam_1': 100},
        {'type': 'branch', 'domain': 'DOMAINE DES LANGUES', 'subdomain': '', 'name': 'Sous total', 'max_period_1': 80, 'max_exam_1': 160},
        {'type': 'domain', 'domain': "DOMAINE DE L'UNIVERS SOCIAL ET ENVIRONNEMENT", 'subdomain': '', 'name': '', 'max_period_1': 0, 'max_exam_1': 0},
        {'type': 'branch', 'domain': 'DOMAINE UNIVERS SOCIAL', 'subdomain': '', 'name': 'Religion', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': 'DOMAINE UNIVERS SOCIAL', 'subdomain': '', 'name': 'Éducation à la vie (1)', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': 'DOMAINE UNIVERS SOCIAL', 'subdomain': '', 'name': 'Éducation civique et moral', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': 'DOMAINE UNIVERS SOCIAL', 'subdomain': '', 'name': 'Géographie', 'max_period_1': 30, 'max_exam_1': 60},
        {'type': 'branch', 'domain': 'DOMAINE UNIVERS SOCIAL', 'subdomain': '', 'name': 'Histoire', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': 'DOMAINE UNIVERS SOCIAL', 'subdomain': '', 'name': 'Sous total', 'max_period_1': 110, 'max_exam_1': 220},
        {'type': 'domain', 'domain': 'DOMAINE DES ARTS', 'subdomain': '', 'name': '', 'max_period_1': 0, 'max_exam_1': 0},
        {'type': 'branch', 'domain': 'DOMAINE DES ARTS', 'subdomain': '', 'name': 'Dessin', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': 'DOMAINE DES ARTS', 'subdomain': '', 'name': 'Musique', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': 'DOMAINE DES ARTS', 'subdomain': '', 'name': 'Sous total', 'max_period_1': 40, 'max_exam_1': 80},
        {'type': 'domain', 'domain': 'DOMAINE DU DEVELOPPEMENT PERSONNEL', 'subdomain': '', 'name': '', 'max_period_1': 0, 'max_exam_1': 0},
        {'type': 'branch', 'domain': 'DOMAINE DEV PERSONNEL', 'subdomain': '', 'name': 'Éducation Physique', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': 'DOMAINE DEV PERSONNEL', 'subdomain': '', 'name': 'Sous total', 'max_period_1': 20, 'max_exam_1': 40}
    ]


def _get_default_humanites_model():
    """
    Returns the default RDC bulletin model for non-SCIENCES sections (Humanités, Latin-Philo, etc.).
    MODÈLE PLAT - Sans domaines ni sous-domaines (respecte l'image du bulletin RDC).
    """
    return [
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Français', 'max_period_1': 50, 'max_exam_1': 100},
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Anglais', 'max_period_1': 30, 'max_exam_1': 60},
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Latin', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Mathématiques', 'max_period_1': 50, 'max_exam_1': 100},
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Histoire', 'max_period_1': 30, 'max_exam_1': 60},
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Géographie', 'max_period_1': 30, 'max_exam_1': 60},
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Éducation civique et moral', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Religion', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Sciences Naturelles', 'max_period_1': 20, 'max_exam_1': 40},
        {'type': 'branch', 'domain': '', 'subdomain': '', 'name': 'Éducation Physique', 'max_period_1': 20, 'max_exam_1': 40}
    ]


def _serialize_branches(config, section_name=None):
    """
    Serialize bulletin branches from config or use appropriate default model.
    Selects the correct default model based on section type:
    - SCIENCES sections: detailed sciences model
    - Non-SCIENCES sections: humanités model
    - EDUCATION DE BASE: sciences model
    """
    if not config:
        # Choose the appropriate default model based on section name
        if section_name and _is_sciences_section(section_name):
            default_model = _get_default_rdc_model()
        elif section_name and _is_education_base_section(section_name):
            default_model = _get_default_rdc_model()
        else:
            # For all other sections (humanités, Latin-Philo, Electricité, Construction, etc.)
            default_model = _get_default_humanites_model()
        
        # Use default model as fallback
        branches = []
        for idx, branch_data in enumerate(default_model, 1):
            branches.append({
                'id': idx,  # Temporary ID for rendering
                'type': branch_data.get('type', 'branch'),
                'domain': branch_data.get('domain', ''),
                'subdomain': branch_data.get('subdomain', ''),
                'name': branch_data.get('name', ''),
                'order': idx,
                'max_value': float(branch_data.get('max_value', 20)),
                'max_period_1': float(branch_data.get('max_period_1', 10)),
                'max_period_2': float(branch_data.get('max_period_2', 10)),
                'max_exam_1': float(branch_data.get('max_exam_1', 10)),
                'max_period_3': float(branch_data.get('max_period_3', 10)),
                'max_period_4': float(branch_data.get('max_period_4', 10)),
                'max_exam_2': float(branch_data.get('max_exam_2', 10)),
                'include_period_1': True,
                'include_period_2': True,
                'include_comp_1': True,
                'include_period_3': True,
                'include_period_4': True,
                'include_comp_2': True,
            })
        return branches
    
    branches = []
    for branch in config.branches.order_by(BulletinBranch.order, BulletinBranch.id).all():
        # Use the stored type from the DB (maxima, domain, subdomain, branch)
        stored_type = branch.type or 'branch'
        if stored_type in ('maxima', 'domain', 'subdomain', 'branch'):
            branch_type = stored_type
        else:
            # Legacy fallback: infer from fields
            branch_type = 'branch'
            if branch.domain and not branch.name:
                branch_type = 'domain'
            elif branch.subdomain and not branch.name:
                branch_type = 'subdomain'
        branches.append({
            'id': branch.id,
            'type': branch_type,
            'domain': branch.domain,
            'subdomain': branch.subdomain,
            'name': branch.name,
            'order': branch.order,
            'max_value': float(branch.max_value if branch.max_value is not None else 20),
            'max_period_1': float(branch.max_period_1 if branch.max_period_1 is not None else 10),
            'max_period_2': float(branch.max_period_2 if branch.max_period_2 is not None else 10),
            'max_exam_1': float(branch.max_exam_1 if branch.max_exam_1 is not None else 10),
            'max_period_3': float(branch.max_period_3 if branch.max_period_3 is not None else 10),
            'max_period_4': float(branch.max_period_4 if branch.max_period_4 is not None else 10),
            'max_exam_2': float(branch.max_exam_2 if branch.max_exam_2 is not None else 10),
            'include_period_1': branch.include_period_1,
            'include_period_2': branch.include_period_2,
            'include_comp_1': branch.include_comp_1,
            'include_period_3': branch.include_period_3,
            'include_period_4': branch.include_period_4,
            'include_comp_2': branch.include_comp_2,
        })
    return branches


def build_grades_map_for_student(student, school_id, year):
    """
    Build the grades map for a student using their section's configured bulletin model.
    Ensures all visualizations use the configured branches.
    """
    section = student.section
    # Use the new function to get config for the student
    config = get_bulletin_config_for_student(student, school_id, year)
    section_name = section.name if section else None
    branches = _serialize_branches(config, section_name)

    courses = Course.query.filter_by(school_id=school_id, section_id=section.id).all() if section else []
    course_by_title = {normalize_text(course.title): course for course in courses}

    grades = Grade.query.filter_by(
        school_id=school_id,
        student_id=student.id,
        academic_year=year,
    ).all()
    grades_by_course_period = defaultdict(dict)
    for grade in grades:
        grades_by_course_period[grade.course_id][grade.period] = float(grade.value)

    grades_map = {}
    for branch in branches:
        if branch['type'] != 'branch':
            continue
        course = course_by_title.get(normalize_text(branch['name']))
        branch_grades = {}
        if course:
            # Ajouter le course_id à la branche pour vérification ultérieure
            branch['course_id'] = course.id
            for period, value in grades_by_course_period.get(course.id, {}).items():
                branch_grades[period] = value
        grades_map[branch['id']] = branch_grades
        grades_map[branch['name']] = branch_grades

    bulletin_totals = None
    if branches:
        max_period_1 = sum(float(b['max_period_1'] or 0) for b in branches if b['type'] == 'branch')
        max_exam_1 = sum(float(b['max_exam_1'] or 0) for b in branches if b['type'] == 'branch')
        semester_total = (max_period_1 * 2) + max_exam_1
        bulletin_totals = {
            'maxPeriod': max_period_1 * 2,
            'maxExam': max_exam_1,
            'semesterTotal': semester_total,
            'generalTotal': semester_total * 2,
        }

    return grades_map, branches, bulletin_totals


def get_student_conducts(student_id, school_id, year):
    """
    Returns a dict mapping period -> conduct value (E, TB, B, etc.)
    for a given student.
    """
    conducts = ConductGrade.query.filter_by(
        school_id=school_id,
        student_id=student_id,
        academic_year=year,
    ).all()
    return {cg.period: cg.value for cg in conducts}


def get_failed_courses_for_student(student_id, school_id, year):
    """
    Returns a list of course IDs where the student failed (score < 50% annual).
    """
    student = Student.query.get(student_id)
    if not student or not student.section:
        return []
    
    courses = Course.query.filter_by(
        school_id=school_id,
        section_id=student.section.id
    ).all()
    
    failed_course_ids = []
    for course in courses:
        if not course.branch:
            continue
        
        # Récupérer tous les grades de l'étudiant pour ce cours (sauf REPECHAGE)
        grades = Grade.query.filter_by(
            school_id=school_id,
            student_id=student_id,
            course_id=course.id,
            academic_year=year,
        ).all()
        
        # Calculer le score annuel
        total_score = sum(float(g.value) for g in grades if g.value and g.period != 'REPECHAGE')
        
        # Calculer le maximum annuel
        branch = course.branch
        max_annual = ((float(branch.max_period_1 or 0) * 2) + (float(branch.max_exam_1 or 0))) * 2
        
        if max_annual == 0:
            continue
        
        # Vérifier si l'élève a échoué (< 50%)
        if (total_score / max_annual) < 0.5:
            failed_course_ids.append(course.id)
    
    return failed_course_ids


def compute_class_ranks(school_id, section_id, year):
    """
    Computes the ranks of all students in a section for all periods and scopes.
    Returns: ranks_by_student (dict mapping student_id -> dict of ranks per scope), total_students
    """
    students = Student.query.filter_by(
        school_id=school_id,
        section_id=section_id,
        academic_year=year,
    ).all()
    
    total_students = len(students)
    if total_students == 0:
        return {}, 0
        
    class_students_data = []
    for s in students:
        g_map, b_branches, _ = build_grades_map_for_student(s, school_id, year)
        
        totals = {
            '1èP': 0, '2èP': 0, 'EXA1': 0, 'semester1': 0,
            '3èP': 0, '4èP': 0, 'EXA2': 0, 'semester2': 0,
            'annual': 0
        }
        has_grades = {k: False for k in totals}

        for branch in b_branches:
            if branch['type'] != 'branch':
                continue
            if branch['name'] and 'total' in branch['name'].lower():
                continue

            b_grades = g_map.get(branch['id'], {})
            p1 = b_grades.get('1èP')
            p2 = b_grades.get('2èP')
            exa1 = b_grades.get('EXA1')
            p3 = b_grades.get('3èP')
            p4 = b_grades.get('4èP')
            exa2 = b_grades.get('EXA2')

            if p1 is not None:
                totals['1èP'] += float(p1)
                has_grades['1èP'] = True
            if p2 is not None:
                totals['2èP'] += float(p2)
                has_grades['2èP'] = True
            if exa1 is not None:
                totals['EXA1'] += float(exa1)
                has_grades['EXA1'] = True
            
            t1 = None
            if p1 is not None or p2 is not None or exa1 is not None:
                t1 = float(p1 or 0) + float(p2 or 0) + float(exa1 or 0)
                totals['semester1'] += t1
                has_grades['semester1'] = True

            if p3 is not None:
                totals['3èP'] += float(p3)
                has_grades['3èP'] = True
            if p4 is not None:
                totals['4èP'] += float(p4)
                has_grades['4èP'] = True
            if exa2 is not None:
                totals['EXA2'] += float(exa2)
                has_grades['EXA2'] = True

            t2 = None
            if p3 is not None or p4 is not None or exa2 is not None:
                t2 = float(p3 or 0) + float(p4 or 0) + float(exa2 or 0)
                totals['semester2'] += t2
                has_grades['semester2'] = True
            
            if t1 is not None or t2 is not None:
                totals['annual'] += float(t1 or 0) + float(t2 or 0)
                has_grades['annual'] = True

        for k in totals:
            if not has_grades[k]:
                totals[k] = None
                
        class_students_data.append({
            'student_id': s.id,
            'totals': totals
        })

    period_keys = ['1èP', '2èP', 'EXA1', 'semester1', '3èP', '4èP', 'EXA2', 'semester2', 'annual']
    ranks_by_student = defaultdict(dict)
    
    for pk in period_keys:
        valid_students = [d for d in class_students_data if d['totals'][pk] is not None]
        valid_students.sort(key=lambda x: x['totals'][pk], reverse=True)
        
        current_rank = 1
        for i, sd in enumerate(valid_students):
            if i > 0 and valid_students[i]['totals'][pk] < valid_students[i-1]['totals'][pk]:
                current_rank = i + 1
            ranks_by_student[sd['student_id']][pk] = f"{current_rank} / {total_students}"
            
    return ranks_by_student, total_students


def _grade_value_for_scope(grades_by_period, scope):
    if scope == 'ANNEE':
        scope = 'annual'
    if scope in PERIODS:
        value = grades_by_period.get(scope)
        return float(value) if value is not None else None

    p1 = grades_by_period.get('1èP')
    p2 = grades_by_period.get('2èP')
    exa1 = grades_by_period.get('EXA1')
    p3 = grades_by_period.get('3èP')
    p4 = grades_by_period.get('4èP')
    exa2 = grades_by_period.get('EXA2')

    def _sum(values):
        if any(value is None for value in values):
            return None
        return sum(float(value) for value in values)

    if scope == 'semester1':
        return _sum([p1, p2, exa1])
    if scope == 'semester2':
        return _sum([p3, p4, exa2])
    if scope == 'annual':
        first = _sum([p1, p2, exa1])
        second = _sum([p3, p4, exa2])
        if first is None or second is None:
            return None
        return first + second
    return None


def _max_points_for_scope(branch, scope):
    if scope == 'ANNEE':
        scope = 'annual'
    if not branch or branch.get('type') != 'branch':
        return 0
    if scope in PERIODS:
        field_map = {
            '1èP': 'max_period_1',
            '2èP': 'max_period_2',
            'EXA1': 'max_exam_1',
            '3èP': 'max_period_3',
            '4èP': 'max_period_4',
            'EXA2': 'max_exam_2',
        }
        return float(branch.get(field_map.get(scope), 0) or 0)
    if scope == 'semester1':
        return float(branch.get('max_period_1', 0) or 0) * 2 + float(branch.get('max_exam_1', 0) or 0)
    if scope == 'semester2':
        return float(branch.get('max_period_3', 0) or 0) + float(branch.get('max_period_4', 0) or 0) + float(branch.get('max_exam_2', 0) or 0)
    if scope == 'annual':
        return (
            float(branch.get('max_period_1', 0) or 0)
            + float(branch.get('max_period_2', 0) or 0)
            + float(branch.get('max_exam_1', 0) or 0)
            + float(branch.get('max_period_3', 0) or 0)
            + float(branch.get('max_period_4', 0) or 0)
            + float(branch.get('max_exam_2', 0) or 0)
        )
    return 0


def build_centralization_context(school_id, section_id, scope, year):
    section = db.session.get(Section, section_id) if section_id else None
    if not section or section.school_id != school_id:
        return {
            'selected_section': None,
            'selected_section_id': None,
            'selected_scope': scope,
            'selected_scope_label': '',
            'sections': [],
            'scope_options': SCOPE_OPTIONS,
            'course_columns': [],
            'centralization_rows': [],
            'student_ids': [],
            'total_maxima_general': 0,
            'school': None,
        }

    school = section.school
    sections = Section.query.filter_by(school_id=school_id).order_by(
        Section.name, Section.level, Section.class_name
    ).all()
    students = Student.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        academic_year=year,
    ).order_by(Student.last_name, Student.first_name).all()
    courses = (
        Course.query.filter_by(school_id=school_id, section_id=section.id)
        .filter(
            ~Course.title.like('Présence de classe%'),
            ~Course.title.like('Pr_sence de classe%'),
            ~Course.title.like('Presence de classe%'),
        )
        .order_by(Course.title)
        .all()
    )

    config = _get_bulletin_config_for_section(school_id, section, year)
    branches = _serialize_branches(config)
    branch_by_name = {normalize_text(branch['name']): branch for branch in branches if branch['type'] == 'branch'}

    normalized_scope = 'annual' if scope == 'ANNEE' else scope

    course_columns = []
    total_maxima_general = 0
    for course in courses:
        branch = _get_course_branch(course) or branch_by_name.get(normalize_text(course.title))
        serialized_branch = None
        if branch:
            if isinstance(branch, BulletinBranch):
                serialized_branch = {
                    'type': 'branch',
                    'name': branch.name,
                    'max_period_1': float(branch.max_period_1 or 0),
                    'max_period_2': float(branch.max_period_2 or 0),
                    'max_exam_1': float(branch.max_exam_1 or 0),
                    'max_period_3': float(branch.max_period_3 or 0),
                    'max_period_4': float(branch.max_period_4 or 0),
                    'max_exam_2': float(branch.max_exam_2 or 0),
                }
            else:
                serialized_branch = branch
        max_points = _max_points_for_scope(serialized_branch, normalized_scope) if serialized_branch else 0
        is_ns = max_points <= 0
        if not is_ns:
            total_maxima_general += max_points
        course_columns.append({
            'course': course,
            'max_points': max_points,
            'is_ns': is_ns,
        })

    grades = Grade.query.filter(
        Grade.school_id == school_id,
        Grade.course_id.in_([course.id for course in courses]) if courses else False,
        Grade.academic_year == year,
    ).all() if courses else []
    grades_lookup = defaultdict(lambda: defaultdict(dict))
    for grade in grades:
        grades_lookup[grade.student_id][grade.course_id][grade.period] = float(grade.value)

    scope_label = dict(SCOPE_OPTIONS).get(normalized_scope, scope)
    centralization_rows = []
    for index, student in enumerate(students, start=1):
        course_points = []
        total_general = 0
        for column in course_columns:
            if column['is_ns']:
                course_points.append(None)
                continue
            period_map = grades_lookup.get(student.id, {}).get(column['course'].id, {})
            points = _grade_value_for_scope(period_map, normalized_scope)
            course_points.append(points)
            if points is not None:
                total_general += points
        percentage = (total_general / total_maxima_general * 100) if total_maxima_general > 0 else 0
        centralization_rows.append({
            'index': index,
            'student': student,
            'course_points': course_points,
            'total_general': total_general,
            'percentage': percentage,
        })

    return {
        'selected_section': section,
        'selected_section_id': section.id,
        'selected_scope': scope,
        'selected_scope_label': scope_label,
        'sections': sections,
        'scope_options': SCOPE_OPTIONS,
        'course_columns': course_columns,
        'centralization_rows': centralization_rows,
        'student_ids': [student.id for student in students],
        'total_maxima_general': total_maxima_general,
        'school': school,
    }


def apply_section_hierarchy_config(school_id, section_name, config, replace_existing=True):
    """Crée/met à jour les enregistrements Section à partir d'un dict niveau -> classes."""
    existing_sections = Section.query.filter_by(school_id=school_id, name=section_name).all()
    
    # Map key: (level, class_name) -> section object
    existing_map = {(s.level, s.class_name): s for s in existing_sections}
    
    # On détermine les combinaisons cibles demandées
    target_combinations = set()
    for level, classes in (config or {}).items():
        for class_name in classes or []:
            target_combinations.add((str(level).strip(), str(class_name).strip()))
            
    # Déterminer les sections à supprimer si replace_existing est vrai
    to_delete = []
    if replace_existing:
        for (level, class_name), section in existing_map.items():
            if (level, class_name) not in target_combinations:
                to_delete.append(section)
                
    # Valider les suppressions : interdire s'il y a des élèves
    for section in to_delete:
        student_count = Student.query.filter_by(section_id=section.id).count()
        if student_count > 0:
            raise ValueError(
                f"Impossible de supprimer le niveau {section.level} (classe {section.class_name}) "
                f"car {student_count} élève(s) y sont inscrit(s). "
                f"Veuillez d'abord réaffecter ces élèves ou réinitialiser la classe."
            )
            
        # Détacher les cours rattachés à cette section
        Course.query.filter_by(section_id=section.id).update({'section_id': None})
            
    # Effectuer les suppressions
    for section in to_delete:
        db.session.delete(section)
    if to_delete:
        db.session.flush()
        
    # Déterminer les sections à créer
    created = []
    for level, class_name in target_combinations:
        if (level, class_name) not in existing_map:
            section = Section(
                school_id=school_id,
                name=section_name,
                level=level,
                class_name=class_name,
            )
            db.session.add(section)
            created.append(section)
            
    return created


def resolve_section_reference(school_id, identifier):
    if identifier is None or identifier == '':
        return None
    try:
        section_id = int(identifier)
        query = Section.query.filter_by(id=section_id)
        if school_id is not None:
            query = query.filter_by(school_id=school_id)
        return query.first()
    except (TypeError, ValueError):
        query = Section.query.filter_by(name=str(identifier))
        if school_id is not None:
            query = query.filter_by(school_id=school_id)
        return query.order_by(Section.school_id, Section.level, Section.class_name).first()


def levels_payload_for_section_name(section_name, school_id=None):
    query = Section.query.filter_by(name=section_name)
    if school_id is not None:
        query = query.filter_by(school_id=school_id)
    sections = query.order_by(Section.level, Section.class_name).all()
    levels = defaultdict(set)
    for section in sections:
        if section.level:
            levels[section.level].add(section.class_name)
    return [
        {'level': level, 'classes': sorted(classes)}
        for level, classes in sorted(levels.items(), key=lambda item: (len(item[0]), item[0]))
    ]


def find_section_for_level(school_id, section_ref, level):
    section = resolve_section_reference(school_id, section_ref)
    if not section:
        return None
    query = Section.query.filter_by(name=section.name, level=level)
    if school_id is not None:
        query = query.filter_by(school_id=school_id)
    match = query.order_by(Section.id).first()
    return match or section


def build_bulletins_batch_for_section(school_id, section_id, year):
    """
    Batch build bulletins for all students in a section.
    Optimized to avoid N+1 queries by loading all data in bulk.
    Returns: list of dicts with student data, grades, ranks, conducts, deliberation results
    """
    section = db.session.get(Section, section_id)
    if not section or section.school_id != school_id:
        return []
    
    students = Student.query.filter_by(
        school_id=school_id,
        section_id=section_id,
        academic_year=year,
    ).order_by(Student.last_name, Student.first_name).all()
    
    if not students:
        return []
    
    student_ids = [s.id for s in students]
    
    # 1. Get bulletin config (same for all students in section)
    bulletin_config = get_bulletin_config_for_student(students[0], school_id, year)
    branches = _serialize_branches(bulletin_config, section.name)
    branch_list = [b for b in branches if b['type'] == 'branch']
    
    # 2. Get all courses for this section
    courses = Course.query.filter_by(school_id=school_id, section_id=section_id).all()
    course_by_title = {normalize_text(course.title): course for course in courses}
    course_by_id = {course.id: course for course in courses}
    
    # 3. Batch load ALL grades for all students in this section
    all_grades = Grade.query.filter(
        Grade.school_id == school_id,
        Grade.student_id.in_(student_ids),
        Grade.academic_year == year,
    ).all()
    
    # Build grades_by_student_course_period: student_id -> course_id -> period -> value
    grades_by_student = defaultdict(lambda: defaultdict(dict))
    for grade in all_grades:
        grades_by_student[grade.student_id][grade.course_id][grade.period] = float(grade.value)
    
    # 4. Batch load ALL conducts for all students
    all_conducts = ConductGrade.query.filter(
        ConductGrade.school_id == school_id,
        ConductGrade.student_id.in_(student_ids),
        ConductGrade.academic_year == year,
    ).all()
    conducts_by_student = defaultdict(dict)
    for cg in all_conducts:
        conducts_by_student[cg.student_id][cg.period] = cg.value
    
    # 5. Batch load ALL deliberation results
    all_deliberations = DeliberationResult.query.filter(
        DeliberationResult.school_id == school_id,
        DeliberationResult.student_id.in_(student_ids),
        DeliberationResult.academic_year == year,
        DeliberationResult.period == 'ANNEE',
    ).all()
    deliberations_by_student = {r.student_id: r for r in all_deliberations}
    
    # 6. Compute class ranks once for all students
    class_ranks, total_students = compute_class_ranks(school_id, section_id, year)
    
    # 7. Compute failed courses for all students
    # Build branch lookup by course
    branch_by_course_id = {}
    for course in courses:
        branch = _get_course_branch(course)
        if branch:
            # Convert BulletinBranch model to dict if needed
            if hasattr(branch, 'max_period_1'):  # It's a model object
                branch = {
                    'max_period_1': branch.max_period_1,
                    'max_exam_1': branch.max_exam_1,
                }
            branch_by_course_id[course.id] = branch
    
    failed_courses_by_student = defaultdict(list)
    for student_id in student_ids:
        for course in courses:
            branch = branch_by_course_id.get(course.id)
            max_p1 = branch.get('max_period_1') if branch else None
            max_e1 = branch.get('max_exam_1') if branch else None
            if not branch or (not max_p1 and not max_e1):
                continue
            
            student_grades = grades_by_student[student_id].get(course.id, {})
            total_score = sum(float(v) for k, v in student_grades.items() if v and k != 'REPECHAGE')
            
            max_annual = ((float(max_p1 or 0) * 2) + 
                         (float(max_e1 or 0))) * 2
            
            if max_annual > 0 and (total_score / max_annual) < 0.5:
                failed_courses_by_student[student_id].append(course.id)
    
    # 8. Build grades_map for each student using pre-loaded data
    bulletins = []
    for student in students:
        # Build grades_map for this student
        grades_map = {}
        for branch in branch_list:
            course = course_by_title.get(normalize_text(branch['name']))
            branch_grades = {}
            if course:
                branch['course_id'] = course.id
                branch_grades = grades_by_student[student.id].get(course.id, {})
            grades_map[branch['id']] = branch_grades
            grades_map[branch['name']] = branch_grades
        
        # Calculate bulletin totals
        max_period_1 = sum(float(b['max_period_1'] or 0) for b in branch_list)
        max_exam_1 = sum(float(b['max_exam_1'] or 0) for b in branch_list)
        semester_total = (max_period_1 * 2) + max_exam_1
        bulletin_totals = {
            'maxPeriod': max_period_1 * 2,
            'maxExam': max_exam_1,
            'semesterTotal': semester_total,
            'generalTotal': semester_total * 2,
        }
        
        # Get failed course titles for this student
        failed_course_ids = failed_courses_by_student.get(student.id, [])
        failed_courses = [course_by_id[cid].title for cid in failed_course_ids if cid in course_by_id]
        
        bulletins.append({
            'student': student,
            'school': student.school,
            'branches': branches,
            'grades_map': grades_map,
            'bulletin_totals': bulletin_totals,
            'config': bulletin_config,
            'student_ranks': class_ranks.get(student.id, {}),
            'total_students': total_students,
            'conducts': conducts_by_student.get(student.id, {}),
            'deliberation_result': deliberations_by_student.get(student.id),
            'failed_courses': failed_courses,
        })
    
    return bulletins
