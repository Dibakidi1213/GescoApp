from xhtml2pdf import pisa
from flask import render_template
import io
import os
from models import db, Student, Grade, Subject, Class, School

def generate_bulletin_pdf(student_id, period=None, output_path=None):
    """
    Génère un PDF du bulletin pour un élève.
    Si output_path est fourni, le fichier est sauvegardé sur le disque.
    Retourne le contenu binaire ou True si sauvegardé.
    """
    student = Student.query.get(student_id)
    if not student: return None
    class_obj = Student.query.get(student_id).current_class # via relationship or id
    if not class_obj: class_obj = Class.query.get(student.class_id)

    school = class_obj.school
    subjects = Subject.query.filter_by(class_id=class_obj.id).all()
    grades = Grade.query.filter_by(student_id=student.id).all()
    grade_map = {(g.subject_id, g.period): g.value for g in grades}

    domains_dict = {}
    for s in subjects:
        d_name = s.domain or "AUTRES"
        sd_name = s.sub_domain or ""
        if d_name not in domains_dict:
            domains_dict[d_name] = {'name': d_name, 'sub_domains': {}}
        if sd_name not in domains_dict[d_name]['sub_domains']:
            domains_dict[d_name]['sub_domains'][sd_name] = {'name': sd_name, 'branches': [],
                                                          'max_p': 0, 'max_e': 0, 'max_t': 0,
                                                          'p1': 0, 'p2': 0, 'exa1': 0, 'tot1': 0,
                                                          'p3': 0, 'p4': 0, 'exa2': 0, 'tot2': 0, 'tg': 0}

        m_p = s.max_1p or 10.0
        m_e = s.max_exa1 or 20.0
        m_t = (m_p * 2) + m_e

        p1 = grade_map.get((s.id, '1èP'), 0)
        p2 = grade_map.get((s.id, '2èP'), 0)
        exa1 = grade_map.get((s.id, 'EXA1'), 0)
        t1 = p1 + p2 + exa1

        p3 = grade_map.get((s.id, '3èP'), 0)
        p4 = grade_map.get((s.id, '4èP'), 0)
        exa2 = grade_map.get((s.id, 'EXA2'), 0)
        t2 = p3 + p4 + exa2

        tg = t1 + t2

        sd = domains_dict[d_name]['sub_domains'][sd_name]
        sd['branches'].append({'name': s.name, 'max_p': m_p, 'max_e': m_e, 'max_t': m_t,
                              'p1': p1, 'p2': p2, 'exa1': exa1, 'tot1': t1,
                              'p3': p3, 'p4': p4, 'exa2': exa2, 'tot2': t2, 'tg': tg})

        sd['max_p'] += m_p
        sd['max_e'] += m_e
        sd['max_t'] += m_t
        sd['p1'] += p1; sd['p2'] += p2; sd['exa1'] += exa1; sd['tot1'] += t1
        sd['p3'] += p3; sd['p4'] += p4; sd['exa2'] += exa2; sd['tot2'] += t2
        sd['tg'] += tg

    processed_domains = []
    totals = {'max_p': 0, 'max_e': 0, 'max_t': 0, 'max_g': 0,
              'p1': 0, 'p2': 0, 'exa1': 0, 'tot1': 0,
              'p3': 0, 'p4': 0, 'exa2': 0, 'tot2': 0, 'tg': 0}

    for d_name, d_val in domains_dict.items():
        sds = list(d_val['sub_domains'].values())
        processed_domains.append({'name': d_name, 'sub_domains': sds})
        for sd in sds:
            totals['max_p'] += sd['max_p']
            totals['max_e'] += sd['max_e']
            totals['max_t'] += sd['max_t']
            totals['p1'] += sd['p1']; totals['p2'] += sd['p2']; totals['exa1'] += sd['exa1']; totals['tot1'] += sd['tot1']
            totals['p3'] += sd['p3']; totals['p4'] += sd['p4']; totals['exa2'] += sd['exa2']; totals['tot2'] += sd['tot2']
            totals['tg'] += sd['tg']

    totals['max_g'] = totals['max_t'] * 2
    def get_pct(v, m): return round(v/m*100, 1) if m > 0 else 0
    totals['pct_tot1'] = get_pct(totals['tot1'], totals['max_t'])
    totals['pct_tot2'] = get_pct(totals['tot2'], totals['max_t'])
    totals['pct_tg'] = get_pct(totals['tg'], totals['max_g'])

    ranking = {'count': Student.query.filter_by(class_id=class_obj.id).count(), 'tg': '...', 'tot1': '...', 'tot2': '...', 'p1': '...', 'p2': '...', 'p3': '...', 'p4': '...'}

    title = f"BULLETIN DE LA {class_obj.level}ème ANNEE CTEB" if class_obj.level in ['7', '8'] else f"BULLETIN DE LA {class_obj.name}"

    html = render_template('bulletin_rdc.html', student=student, class_obj=class_obj, school=school,
                           domains=processed_domains, totals=totals, ranking=ranking, title=title,
                           drc_flag_url="https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Flag_of_the_Democratic_Republic_of_the_Congo.svg/1200px-Flag_of_the_Democratic_Republic_of_the_Congo.svg.png",
                           drc_emblem_url="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Coat_of_arms_of_the_Democratic_Republic_of_the_Congo.svg/1200px-Coat_of_arms_of_the_Democratic_Republic_of_the_Congo.svg.png")

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            pisa.CreatePDF(io.BytesIO(html.encode("utf-8")), dest=f)
        return True

    pdf_out = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(html.encode("utf-8")), dest=pdf_out)
    return pdf_out.getvalue()
