#!/usr/bin/env python
"""Direct database verification of IGE persistence"""

from app import app, db
from models import BulletinConfig, Section

def verify_ige_persistence():
    """Check direct database state"""
    print("=" * 60)
    print("✅ DIRECT DATABASE VERIFICATION")
    print("=" * 60)
    
    with app.app_context():
        # Get SCIENCES section level 1
        sections = Section.query.filter_by(name='SCIENCES').all()
        print(f"\nFound {len(sections)} SCIENCES sections:")
        for sec in sections:
            print(f"  - Section ID {sec.id}, Level {sec.level}")
        
        # Get bulletin config for SCIENCES sections
        configs = BulletinConfig.query.join(Section).filter(
            Section.name == 'SCIENCES'
        ).all()
        
        print(f"\nBulletin Configs for SCIENCES:")
        for config in configs:
            print(f"\n  Config ID: {config.id}")
            print(f"  Section ID: {config.section_id}")
            print(f"  Level: {config.level}")
            print(f"  IGE Number: {config.ige_number or '(NULL)'}")
        
        # Look specifically for SCIENCES level 1
        print(f"\n🔍 Specifically looking for SCIENCES level 1...")
        for config in configs:
            if config.level == 1:
                print(f"Found: Config ID {config.id}, IGE: {config.ige_number}")

if __name__ == '__main__':
    verify_ige_persistence()
