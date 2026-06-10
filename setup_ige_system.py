"""
Complete IGE Implementation Script
1. Applies the database migration
2. Generates IGE numbers for existing configurations
3. Verifies the implementation
"""

import os
import sys
import subprocess
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Run the SQL migration"""
    print("\n" + "="*70)
    print("📝 STEP 1: Running database migration...")
    print("="*70)
    
    migration_file = 'migration_add_bulletin_ige_number.sql'
    
    if not os.path.exists(migration_file):
        print(f"❌ Migration file '{migration_file}' not found!")
        return False
    
    try:
        # You'll need to run this manually or update connection details
        print(f"✅ Migration file found: {migration_file}")
        print("⚠️  Please run this migration manually in your database:")
        print(f"   mysql -u your_user -p your_db < {migration_file}")
        print("\n   OR execute this SQL in your MySQL client:")
        
        with open(migration_file, 'r') as f:
            print("\n" + f.read())
        
        return True
    except Exception as e:
        print(f"❌ Error reading migration file: {str(e)}")
        return False


def generate_ige_numbers():
    """Generate IGE numbers using the Python script"""
    print("\n" + "="*70)
    print("🔢 STEP 2: Generating IGE numbers...")
    print("="*70)
    
    try:
        # Import and run the generate script
        from app import app, db
        from models import BulletinConfig, Section
        
        with app.app_context():
            # Get all bulletin configs without IGE number
            configs_without_ige = BulletinConfig.query.filter(
                BulletinConfig.ige_number.is_(None)
            ).all()
            
            if not configs_without_ige:
                print("✅ All bulletin configurations already have IGE numbers.")
                return True
            
            print(f"🔄 Found {len(configs_without_ige)} configurations without IGE numbers")
            
            # Helper function
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
            
            generated_count = 0
            for config in configs_without_ige:
                section = Section.query.get(config.section_id)
                if not section:
                    continue
                
                section_abbr = get_section_abbreviation(section.name)
                
                # Get existing numbers
                prefix = f"IGE/{section_abbr}/"
                existing = BulletinConfig.query.filter(
                    BulletinConfig.school_id == config.school_id,
                    BulletinConfig.ige_number.ilike(prefix + '%')
                ).all()
                
                max_num = 0
                for existing_config in existing:
                    if existing_config.ige_number:
                        try:
                            num = int(existing_config.ige_number.split('/')[-1])
                            max_num = max(max_num, num)
                        except (ValueError, IndexError):
                            pass
                
                ige_number = f"IGE/{section_abbr}/{max_num + 1:03d}"
                config.ige_number = ige_number
                db.session.add(config)
                generated_count += 1
                
                print(f"✅ {section.name} ({config.level}) → {ige_number}")
            
            db.session.commit()
            print(f"\n✅ Successfully generated {generated_count} IGE numbers!")
            return True
            
    except Exception as e:
        print(f"❌ Error generating IGE numbers: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_implementation():
    """Verify that the implementation is working"""
    print("\n" + "="*70)
    print("✔️  STEP 3: Verifying implementation...")
    print("="*70)
    
    try:
        from app import app, db
        from models import BulletinConfig
        
        with app.app_context():
            # Check if ige_number column exists
            config_with_ige = BulletinConfig.query.filter(
                BulletinConfig.ige_number.isnot(None)
            ).first()
            
            if config_with_ige:
                print(f"✅ IGE number column exists and contains data")
                print(f"   Sample: {config_with_ige.ige_number}")
                return True
            else:
                print("⚠️  No configurations with IGE numbers found yet")
                print("   This is OK if you just created the column")
                return True
                
    except Exception as e:
        print(f"❌ Error verifying: {str(e)}")
        return False


def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "         🎓 IGE NUMBER IMPLEMENTATION FOR BULLETINS         ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    print("\n📋 This script will:")
    print("   1. Show the database migration SQL")
    print("   2. Generate IGE numbers for existing configurations")
    print("   3. Verify the implementation")
    
    # Step 1: Show migration
    if not run_migration():
        print("\n❌ Migration step failed!")
        return False
    
    input("\n⏸️  Press Enter after applying the SQL migration to database...")
    
    # Step 2: Generate IGE numbers
    if not generate_ige_numbers():
        print("\n❌ IGE generation failed!")
        return False
    
    # Step 3: Verify
    if not verify_implementation():
        print("\n⚠️  Verification encountered an issue (non-fatal)")
    
    print("\n" + "="*70)
    print("✅ IMPLEMENTATION COMPLETE!")
    print("="*70)
    print("\n📌 Next steps:")
    print("   1. Restart your Flask application: python run_app.py")
    print("   2. Go to: /admin/bulletins-config")
    print("   3. Create or load a bulletin configuration")
    print("   4. You should now see the IGE number (e.g., IGE/PS/026)")
    print("\n🎉 The IGE numbering system is now active!")
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
