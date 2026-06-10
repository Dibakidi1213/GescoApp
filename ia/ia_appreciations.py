from models import Student, Grade

def generate_appreciation(student_id, period):
    """
    Génère une appréciation textuelle automatique basée sur les résultats.
    """
    grades = Grade.query.filter_by(student_id=student_id, period=period).all()
    if not grades:
        return "Aucune donnée disponible pour cette période.", "Inconnu"

    avg = sum([g.value for g in grades]) / len(grades)

    # Échelle de 0 à 20
    if avg >= 17:
        level = "Excellent"
        text = "Travail exceptionnel. Félicitations pour votre investissement et votre rigueur."
    elif avg >= 14:
        level = "Bon"
        text = "Très bon ensemble. Continuez vos efforts pour atteindre l'excellence."
    elif avg >= 12:
        level = "Assez Bien"
        text = "Résultats satisfaisants. Vous avez le potentiel pour faire encore mieux."
    elif avg >= 10:
        level = "Passable"
        text = "Ensemble juste moyen. Un redoublement d'efforts est nécessaire pour consolider les acquis."
    else:
        level = "Insuffisant"
        text = "Résultats en dessous des attentes. Un soutien pédagogique est fortement recommandé."

    return text, level
