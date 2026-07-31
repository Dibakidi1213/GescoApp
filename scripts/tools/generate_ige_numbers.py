"""
Script to generate IGE numbers for existing bulletin configurations.
Format: IGE/[SECTION_ABBR]/[NUMERO] (e.g., IGE/PS/026)
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app directly
from app import app, db
from models import BulletinConfig, Section

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
    
    # Fallback: take first letter of first two words
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
        
        print(f"🔄 Found {len(configs_without_ige)} bulletin configurations without IGE numbers.")
        print("🚀 Generating IGE numbers...\n")
        
        # Group by school and section
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
                
                # Initialize stats for this school/section combo
                key = f"{school_id}/{section_abbr}"
                if key not in stats:
                    stats[key] = {'section_name': section.name, 'count': 0, 'configs': []}
                
                # Get all existing IGE numbers for this section in this school
                prefix = f"IGE/{section_abbr}/"
                existing_configs = BulletinConfig.query.filter(
                    BulletinConfig.school_id == school_id,
                    BulletinConfig.ige_number.ilike(prefix + '%')
                ).all()
                
                # Find max number
                max_num = 0
                for existing_config in existing_configs:
                    if existing_config.ige_number:
                        try:
                            num_str = existing_config.ige_number.split('/')[-1]
                            num = int(num_str)
                            max_num = max(max_num, num)
                        except (ValueError, IndexError):
                            pass
                
                # Generate new number
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
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully generated {generated_count} IGE numbers!")
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


if __name__ == '__main__':
    print("=" * 70)
    print("🎓 IGE Number Generation Script")
    print("=" * 70)
    print()
    
    success = generate_ige_numbers()
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
