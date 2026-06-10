from xhtml2pdf import pisa
from flask import render_template
import io
import os

class PDFGenerator:
    """Service de génération de PDF pour les documents scolaires."""

    @staticmethod
    def generate_bulletin(student, subjects, grades, school, class_obj):
        """Génère le bulletin officiel RDC en PDF."""

        # Organisation des données par domaine et sous-domaine
        data = {}
        for subject in subjects:
            d = subject.domain or "AUTRES"
            sd = subject.sub_domain or ""
            if d not in data:
                data[d] = {}
            if sd not in data[d]:
                data[d][sd] = []

            # Récupération des notes pour ce sujet
            subject_grades = {g.period: g.value for g in grades if g.subject_id == subject.id}

            branch_data = {
                'name': subject.name,
                'p1': subject_grades.get('1èP'),
                'p2': subject_grades.get('2èP'),
                'exa1': subject_grades.get('EXA1'),
                'p3': subject_grades.get('3èP'),
                'p4': subject_grades.get('4èP'),
                'exa2': subject_grades.get('EXA2'),
            }

            # Calcul des totaux
            t1 = sum(filter(None, [branch_data['p1'], branch_data['p2'], branch_data['p1']])) # Exemple simplifié
            # En réalité, on ferait des calculs plus complexes selon les coefficients
            branch_data['total1'] = (branch_data['p1'] or 0) + (branch_data['p2'] or 0) + (branch_data['exa1'] or 0)
            branch_data['total2'] = (branch_data['p3'] or 0) + (branch_data['p4'] or 0) + (branch_data['exa2'] or 0)
            branch_data['grand_total'] = branch_data['total1'] + branch_data['total2']

            data[d][sd].append(branch_data)

        # Rendu du template HTML
        html = render_template('bulletin_rdc.html',
                               student=student,
                               school=school,
                               class_obj=class_obj,
                               data=data,
                               school_logo=school.logo)

        # Conversion HTML -> PDF
        pdf_out = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.BytesIO(html.encode("utf-8")), dest=pdf_out)

        if pisa_status.err:
            return None

        return pdf_out.getvalue()

    @staticmethod
    def save_pdf(pdf_content, filename, folder='bulletins'):
        """Sauvegarde le PDF sur le disque."""
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = os.path.join(folder, filename)
        with open(path, 'wb') as f:
            f.write(pdf_content)
        return path
