#!/usr/bin/env python
"""Test script to verify IGE API and database state"""

from app import app, db
from models import BulletinConfig, Section

def test_database_ige():
    """Check if IGE numbers are in database"""
    print("=" * 60)
    print("🔍 CHECKING DATABASE IGE NUMBERS")
    print("=" * 60)
    
    with app.app_context():
        configs = BulletinConfig.query.all()
        print(f"\nTotal configs: {len(configs)}\n")
        
        for config in configs:
            section = Section.query.get(config.section_id)
            section_name = section.name if section else "Unknown"
            print(f"Config ID {config.id}:")
            print(f"  Section: {section_name} (ID: {config.section_id})")
            print(f"  Level: {config.level}")
            print(f"  IGE Number: {config.ige_number or 'NULL'}")
            print()

if __name__ == '__main__':
    test_database_ige()
