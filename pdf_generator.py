from xhtml2pdf import pisa
from flask import render_template
import io
import os
from models import db, Student, Grade, Subject, Class, School

class PDFGenerator:
    """Service de génération de PDF pour les bulletins officiels RDC."""

    @staticmethod
    def generate_bulletin(student_id):
        """Génère le bulletin officiel RDC pour un élève."""
        student = Student.query.get(student_id)
        if not student: return None

        class_obj = student.current_class
        school = class_obj.school
        subjects = Subject.query.filter_by(class_id=class_obj.id).all()

        # Récupérer toutes les notes de l'élève
        grades = Grade.query.filter_by(student_id=student.id).all()
        grade_map = {(g.subject_id, g.period): g.value for g in grades}

        # Organiser les données par domaines
        domains_dict = {}
        for s in subjects:
            d_name = s.domain or "AUTRES"
            if d_name not in domains_dict:
                domains_dict[d_name] = {'name': d_name, 'branches': [], 'max_p': 0, 'max_e': 0, 'max_t': 0, 'max_g': 0}

            m_p = s.max_1p or 10.0
            m_e = s.max_exa1 or 20.0
            m_t = (m_p * 2) + m_e
            m_g = m_t * 2

            p1 = grade_map.get((s.id, '1èP'))
            p2 = grade_map.get((s.id, '2èP'))
            exa1 = grade_map.get((s.id, 'EXA1'))
            tot1 = (p1 or 0) + (p2 or 0) + (exa1 or 0) if any(v is not None for v in [p1, p2, exa1]) else None

            p3 = grade_map.get((s.id, '3èP'))
            p4 = grade_map.get((s.id, '4èP'))
            exa2 = grade_map.get((s.id, 'EXA2'))
            tot2 = (p3 or 0) + (p4 or 0) + (exa2 or 0) if any(v is not None for v in [p3, p4, exa2]) else None

            tg = (tot1 or 0) + (tot2 or 0) if (tot1 is not None or tot2 is not None) else None

            domains_dict[d_name]['branches'].append({
                'name': s.name,
                'p1': p1, 'p2': p2, 'exa1': exa1, 'tot1': tot1,
                'p3': p3, 'p4': p4, 'exa2': exa2, 'tot2': tot2,
                'tg': tg
            })

            domains_dict[d_name]['max_p'] += m_p
            domains_dict[d_name]['max_e'] += m_e
            domains_dict[d_name]['max_t'] += m_t
            domains_dict[d_name]['max_g'] += m_g

        processed_data = list(domains_dict.values())

        # Calcul des totaux généraux
        totals = {
            'max_p': sum(d['max_p'] for d in processed_data),
            'max_e': sum(d['max_e'] for d in processed_data),
            'max_t': sum(d['max_t'] for d in processed_data),
            'max_g': sum(d['max_g'] for d in processed_data),
            'p1': 0, 'p2': 0, 'exa1': 0, 'tot1': 0,
            'p3': 0, 'p4': 0, 'exa2': 0, 'tot2': 0, 'tg': 0
        }

        for d in processed_data:
            for b in d['branches']:
                totals['p1'] += b['p1'] or 0
                totals['p2'] += b['p2'] or 0
                totals['exa1'] += b['exa1'] or 0
                totals['tot1'] += b['tot1'] or 0
                totals['p3'] += b['p3'] or 0
                totals['p4'] += b['p4'] or 0
                totals['exa2'] += b['exa2'] or 0
                totals['tot2'] += b['tot2'] or 0
                totals['tg'] += b['tg'] or 0

        # Pourcentages
        def get_pct(val, max_val):
            return round((val / max_val * 100), 1) if max_val > 0 else 0

        totals.update({
            'pct_p1': get_pct(totals['p1'], totals['max_p']),
            'pct_p2': get_pct(totals['p2'], totals['max_p']),
            'pct_exa1': get_pct(totals['exa1'], totals['max_e']),
            'pct_tot1': get_pct(totals['tot1'], totals['max_t']),
            'pct_p3': get_pct(totals['p3'], totals['max_p']),
            'pct_p4': get_pct(totals['p4'], totals['max_p']),
            'pct_exa2': get_pct(totals['exa2'], totals['max_e']),
            'pct_tot2': get_pct(totals['tot2'], totals['max_t']),
            'pct_tg': get_pct(totals['tg'], totals['max_g']),
        })

        ranking = {'count': Student.query.filter_by(class_id=class_obj.id).count(), 'tg': '...', 'tot1': '...', 'tot2': '...'}
        conduite = {'p1': 'E', 'p2': 'E', 'p3': 'E', 'p4': 'E'}
        application = {'p1': 'TB', 'p2': 'TB', 'p3': 'TB', 'p4': 'TB'}

        html = render_template('bulletin_rdc.html',
                               student=student,
                               class_obj=class_obj,
                               school=school,
                               processed_data=processed_data,
                               totals=totals,
                               ranking=ranking,
                               conduite=conduite,
                               application=application,
                               section_name=class_obj.section or "SCIENCES",
                               drc_flag_url="https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Flag_of_the_Democratic_Republic_of_the_Congo.svg/1200px-Flag_of_the_Democratic_Republic_of_the_Congo.svg.png",
                               drc_emblem_url="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Coat_of_arms_of_the_Democratic_Republic_of_the_Congo.svg/1200px-Coat_of_arms_of_the_Democratic_Republic_of_the_Congo.svg.png")

        pdf_out = io.BytesIO()
        pisa.CreatePDF(io.BytesIO(html.encode("utf-8")), dest=pdf_out)
        return pdf_out.getvalue()

    @staticmethod
    def save_pdf(pdf_content, filename):
        folder = 'bulletins'
        if not os.path.exists(folder): os.makedirs(folder)
        path = os.path.join(folder, filename)
        with open(path, 'wb') as f: f.write(pdf_content)
        return path
