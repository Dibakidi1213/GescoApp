#!/usr/bin/env python
"""Test IGE generation and persistence"""
from app import app, db
from models import BulletinConfig, Section
from flask import session

def test_ige_full_flow():
    """Test the complete IGE flow: generation -> save -> verify"""
    with app.app_context():
        # Get SCIENCES section
        section = Section.query.filter_by(name='SCIENCES', school_id=1).first()
        if not section:
            print("❌ SCIENCES section not found")
            return
        
        print(f"✅ Found SCIENCES section: {section.name} (ID: {section.id})")
        
        # Test 1: Generate a new IGE number
        print("\n[Test 1] Generating new IGE...")
        abbr = BulletinConfig._get_section_abbreviation(section.name)
        print(f"  Section abbreviation: {abbr}")
        
        # Find max existing
        prefix = f"IGE/{abbr}/"
        existing = BulletinConfig.query.filter(
            BulletinConfig.school_id == 1,
            BulletinConfig.ige_number.ilike(prefix + '%')
        ).all()
        
        max_num = 0
        for config in existing:
            if config.ige_number:
                try:
                    num_str = config.ige_number.split('/')[-1]
                    num = int(num_str)
                    max_num = max(max_num, num)
                except:
                    pass
        
        next_num = max_num + 1
        new_ige = f"IGE/{abbr}/{next_num:03d}"
        print(f"  Generated IGE: {new_ige}")
        
        # Test 2: Create a new config with this IGE
        print(f"\n[Test 2] Creating new config with IGE...")
        new_config = BulletinConfig(
            school_id=1,
            section_id=section.id,
            level=5,  # New level to avoid conflicts
            academic_year='2025 - 2026',
            ige_number=new_ige,
            validated=False
        )
        db.session.add(new_config)
        db.session.commit()
        print(f"  ✅ Created config ID: {new_config.id} with IGE: {new_config.ige_number}")
        
        # Test 3: Verify persistence
        print(f"\n[Test 3] Verifying persistence...")
        verify_config = BulletinConfig.query.filter_by(id=new_config.id).first()
        if verify_config and verify_config.ige_number == new_ige:
            print(f"  ✅ IGE persisted correctly: {verify_config.ige_number}")
        else:
            print(f"  ❌ IGE not persisted! Got: {verify_config.ige_number if verify_config else 'None'}")
        
        # Test 4: Update existing config with different IGE
        print(f"\n[Test 4] Updating existing config...")
        existing_config = BulletinConfig.query.filter_by(
            school_id=1,
            section_id=section.id,
            level=1
        ).first()
        
        if existing_config:
            old_ige = existing_config.ige_number
            update_ige = f"IGE/{abbr}/999"
            existing_config.ige_number = update_ige
            db.session.commit()
            print(f"  Updated: {old_ige} -> {update_ige}")
            
            # Verify update
            verify_update = BulletinConfig.query.filter_by(id=existing_config.id).first()
            if verify_update.ige_number == update_ige:
                print(f"  ✅ Update persisted correctly")
            else:
                print(f"  ❌ Update failed! Got: {verify_update.ige_number}")
            
            # Restore original
            existing_config.ige_number = old_ige
            db.session.commit()
            print(f"  ✅ Restored original IGE")
        
        print("\n[✅ All tests complete!]")

if __name__ == '__main__':
    test_ige_full_flow()
