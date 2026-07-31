from datetime import date, datetime, timedelta

from models import Course, SchoolHoliday, Student, db


ATTENDANCE_STATUSES = {'present', 'absent', 'malade'}
ATTENDANCE_STATUS_OPTIONS = [
    ('present', 'Present'),
    ('absent', 'Absent'),
    ('malade', 'Malade'),
]
ATTENDANCE_STATUS_LABELS = dict(ATTENDANCE_STATUS_OPTIONS)

CONDUCT_PERIODS = ['1\u00e8P', '2\u00e8P', '3\u00e8P', '4\u00e8P']
CONDUCT_VALUE_OPTIONS = ['E', 'TB', 'B', 'AB', 'MA', 'ME']
CONDUCT_VALUES = set(CONDUCT_VALUE_OPTIONS)

ATTENDANCE_COURSE_TITLE_PREFIX = 'Presence de classe'


def parse_iso_date(raw_value):
    raw = str(raw_value or '').strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date()
    except ValueError:
        return None


def parse_month(raw_value):
    raw = str(raw_value or '').strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, '%Y-%m').date().replace(day=1)
    except ValueError:
        return None


def month_key_for_day(day):
    return day.strftime('%Y-%m') if day else ''


def month_bounds(month_start):
    if not month_start:
        return None, None
    if month_start.month == 12:
        next_month = date(month_start.year + 1, 1, 1)
    else:
        next_month = date(month_start.year, month_start.month + 1, 1)
    return month_start, next_month - timedelta(days=1)


def month_label(month_value):
    month_start = parse_month(month_value) if isinstance(month_value, str) else month_value
    if not month_start:
        return ''
    return month_start.strftime('%m/%Y')


def class_label(section):
    if not section:
        return ''
    return ' / '.join(part for part in [section.name, section.level, section.class_name] if part)


def attendance_course_title(month_value):
    month_key = month_value if isinstance(month_value, str) else month_key_for_day(month_value)
    return f'{ATTENDANCE_COURSE_TITLE_PREFIX} - {month_key}'


def get_attendance_course_for_section(section, school_id, month_value, professor_id=None, create=False):
    if not section:
        return None

    title = attendance_course_title(month_value)
    course = Course.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        title=title,
    ).first()
    if course or not create:
        return course

    course = Course(
        school_id=school_id,
        section_id=section.id,
        title=title,
        professor_id=professor_id,
    )
    db.session.add(course)
    db.session.flush()
    return course


def holidays_between(school_id, start_day, end_day):
    if not school_id or not start_day or not end_day:
        return []
    return SchoolHoliday.query.filter(
        SchoolHoliday.school_id == school_id,
        SchoolHoliday.holiday_date >= start_day,
        SchoolHoliday.holiday_date <= end_day,
    ).order_by(SchoolHoliday.holiday_date).all()


def holiday_map(school_id, start_day, end_day):
    return {holiday.holiday_date: holiday for holiday in holidays_between(school_id, start_day, end_day)}


def is_working_day(day, holidays=None):
    if not day:
        return False
    if day.weekday() == 6:
        return False
    if holidays and day in holidays:
        return False
    return True


def working_days_for_month(school_id, month_value):
    month_start = parse_month(month_value) if isinstance(month_value, str) else month_value
    start_day, end_day = month_bounds(month_start)
    holidays = holiday_map(school_id, start_day, end_day)
    days = []
    current_day = start_day
    while current_day and current_day <= end_day:
        if is_working_day(current_day, holidays):
            days.append(current_day)
        current_day += timedelta(days=1)
    return days


def validate_attendance_scope(attendance_day, month_value, school_id):
    if not attendance_day:
        return None, 'Date de presence invalide.'

    month_start = parse_month(month_value) if isinstance(month_value, str) else month_value
    if not month_start:
        return None, 'Periode mensuelle invalide.'

    start_day, end_day = month_bounds(month_start)
    if not (start_day <= attendance_day <= end_day):
        return None, 'La date doit appartenir au mois selectionne.'

    holidays = holiday_map(school_id, attendance_day, attendance_day)
    if attendance_day.weekday() == 6:
        return None, 'La presence ne se prend pas le dimanche.'
    if attendance_day in holidays:
        return None, f'Jour ferie: {holidays[attendance_day].label}.'

    return month_key_for_day(month_start), None


def students_for_section_year(school_id, section_id, academic_year):
    base_query = Student.query.filter_by(school_id=school_id, section_id=section_id)
    year_students = base_query.filter_by(academic_year=academic_year).order_by(
        Student.last_name,
        Student.first_name,
    ).all()
    if year_students:
        return year_students
    return base_query.order_by(Student.last_name, Student.first_name).all()


def holiday_payload(holiday):
    return {
        'id': holiday.id,
        'holiday_date': holiday.holiday_date.isoformat() if holiday.holiday_date else '',
        'label': holiday.label,
        'academic_year': holiday.academic_year,
    }
