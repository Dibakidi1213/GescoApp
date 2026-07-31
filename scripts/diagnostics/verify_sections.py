from app import app
from models import BulletinConfig, Section, db

with app.app_context():
    print("=== Configurations de bulletins ===")
    configs = BulletinConfig.query.all()
    for config in configs:
        section = Section.query.get(config.section_id)
        if section:
            print(f"Config {config.id}: Section '{section.name}' Level '{config.level}' (Section ID: {config.section_id})")
        else:
            print(f"Config {config.id}: ⚠️ Section ID {config.section_id} NOT FOUND!")
    
    print("\n=== Toutes les sections ===")
    sections = Section.query.filter_by(school_id=1).all()
    print(f"Nombre de sections: {len(sections)}")
    for section in sections:
        print(f"  ID {section.id}: {section.name} - Level {section.level} - Class {section.class_name}")
