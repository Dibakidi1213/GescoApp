#!/usr/bin/env python
"""
Initialize IGE column if it doesn't exist, then generate IGE numbers
"""

import os
import sys
from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import BulletinConfig, Section

def ensure_ige_column():
    """Ensure the ige_number column exists"""
    with app.app_context():
        inspector = inspect(db.engine)
        
        if 'bulletin_configs' not in inspector.get_table_names():
            print("❌ bulletin_configs table doesn't exist!")
            return False
        
        columns = {column['name'] for column in inspector.get_columns('bulletin_configs')}
        
        if 'ige_number' in columns:
            print("✅ ige_number column already exists")
            return True
        
        print("🔄 Creating ige_number column...")
        try:
            with db.engine.begin() as conn:
                # SQLite doesn't allow UNIQUE constraints on NULL columns
                # So we add it without the UNIQUE constraint for now
                conn.execute(text('ALTER TABLE bulletin_configs ADD COLUMN ige_number VARCHAR(50) NULL'))
            print("✅ ige_number column created successfully!")
            return True
        except Exception as e:
            print(f"❌ Error creating column: {str(e)}")
            return False


def get_section_abbreviation(section_name):
    """Convert section name to 2-letter abbreviation"""
    mappings = {
        'primaire scientifique': 'PS',
        'primaire littéraire': 'PL',
        'secondaire scientifique': 'SS',
        'secondaire littéraire': 'SL',
        'technique scientifique': 'TS',
        'technique littéraire': 'TL',
    }
    
    section_lower = section_name.lower().strip()
    for key, abbr in mappings.items():
        if key in section_lower:
            return abbr
    
    words = section_name.split()
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    elif len(words) == 1:
        return (section_name[:2]).upper()
    
    return "XX"


def generate_ige_numbers():
    """Generate IGE numbers for all bulletin configs that don't have one yet"""
    
    with app.app_context():
        # Get all bulletin configs without IGE number
        configs_without_ige = BulletinConfig.query.filter(
            BulletinConfig.ige_number.is_(None)
        ).all()
        
        if not configs_without_ige:
            print("✅ All bulletin configurations already have IGE numbers.")
            return True
        
        print(f"\n🔄 Found {len(configs_without_ige)} bulletin configurations without IGE numbers.")
        print("🚀 Generating IGE numbers...\n")
        
        stats = {}
        generated_count = 0
        
        for config in configs_without_ige:
            try:
                section = Section.query.get(config.section_id)
                if not section:
                    print(f"⚠️  Section {config.section_id} not found for config {config.id}")
                    continue
                
                section_abbr = get_section_abbreviation(section.name)
                school_id = config.school_id
                
                key = f"{school_id}/{section_abbr}"
                if key not in stats:
                    stats[key] = {'section_name': section.name, 'count': 0, 'configs': []}
                
                # Get all existing IGE numbers for this section in this school
                prefix = f"IGE/{section_abbr}/"
                existing_configs = BulletinConfig.query.filter(
                    BulletinConfig.school_id == school_id,
                    BulletinConfig.ige_number.ilike(prefix + '%')
                ).all()
                
                max_num = 0
                for existing_config in existing_configs:
                    if existing_config.ige_number:
                        try:
                            num_str = existing_config.ige_number.split('/')[-1]
                            num = int(num_str)
                            max_num = max(max_num, num)
                        except (ValueError, IndexError):
                            pass
                
                next_num = max_num + 1
                ige_number = f"IGE/{section_abbr}/{next_num:03d}"
                
                config.ige_number = ige_number
                db.session.add(config)
                
                stats[key]['count'] += 1
                stats[key]['configs'].append({
                    'level': config.level,
                    'ige_number': ige_number,
                    'academic_year': config.academic_year
                })
                
                generated_count += 1
                print(f"✅ Config ID {config.id}: {section.name} ({config.level}) → {ige_number}")
                
            except Exception as e:
                print(f"❌ Error processing config {config.id}: {str(e)}")
        
        try:
            db.session.commit()
            print(f"\n✅ Successfully generated {generated_count} IGE numbers!")
            
            if stats:
                print("\n📊 Summary by section:\n")
                for key in sorted(stats.keys()):
                    stat = stats[key]
                    print(f"  {stat['section_name']}:")
                    print(f"    - Generated: {stat['count']} IGE numbers")
                    for cfg in stat['configs']:
                        print(f"      • Level {cfg['level']}: {cfg['ige_number']} ({cfg['academic_year']})")
                    print()
            
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving IGE numbers: {str(e)}")
            return False


def main():
    print("\n" + "="*70)
    print("🎓 IGE SYSTEM INITIALIZATION")
    print("="*70 + "\n")
    
    print("📝 STEP 1: Ensuring ige_number column exists...")
    if not ensure_ige_column():
        print("\n❌ Failed to create column!")
        return False
    
    print("\n🔢 STEP 2: Generating IGE numbers...")
    if not generate_ige_numbers():
        print("\n❌ Failed to generate IGE numbers!")
        return False
    
    print("\n" + "="*70)
    print("✅ IGE SYSTEM INITIALIZATION COMPLETE!")
    print("="*70)
    print("\n📌 Next steps:")
    print("   1. Restart your Flask application: python run_app.py")
    print("   2. Go to: http://localhost:5000/admin/bulletins-config")
    print("   3. You should now see IGE numbers (e.g., IGE/PS/026)")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
