from app import app
from routes.admin.services import levels_payload_for_section_name
from models import Section, db

with app.app_context():
    # Vérifier les sections disponibles
    school_id = 1  # Supposer que l'école 1 existe
    
    sections = Section.query.filter_by(school_id=school_id).distinct(Section.name).all()
    print(f"Sections trouvées pour l'école {school_id}:")
    for section in sections:
        print(f"  - {section.name}")
        levels_data = levels_payload_for_section_name(school_id, section.name)
        print(f"    Niveaux: {levels_data}")
        print()
