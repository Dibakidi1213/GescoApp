# 🎓 IGE Numbering System for Bulletins

## Overview
Each bulletin configuration (section + level) now has a unique **IGE (Identification Générale d'Établissement) number** in the format: `IGE/[SECTION_ABBR]/[NUMERO]`

**Example:** `IGE/PS/026` (IGE number 26 for Primaire Scientifique section)

---

## 📊 Format Specification

### IGE Number Structure
```
IGE / [SECTION_CODE] / [SEQUENCE_NUMBER]
     |                |
     |                └─ Automatically incremented (3 digits, zero-padded)
     └────────────────── 2-letter section abbreviation
```

### Section Abbreviations
| Section Name | Abbreviation |
|---|---|
| Primaire Scientifique | PS |
| Primaire Littéraire | PL |
| Secondaire Scientifique | SS |
| Secondaire Littéraire | SL |
| Technique Scientifique | TS |
| Technique Littéraire | TL |

### Example Numbers
- `IGE/PS/001` - First bulletin for Primaire Scientifique
- `IGE/PS/002` - Second bulletin for Primaire Scientifique
- `IGE/SS/001` - First bulletin for Secondaire Scientifique
- `IGE/SL/026` - Twenty-sixth bulletin for Secondaire Littéraire

---

## 🚀 Implementation Steps

### Step 1: Database Migration
Apply the SQL migration to add the `ige_number` column:

```sql
-- migration_add_bulletin_ige_number.sql
ALTER TABLE bulletin_configs 
ADD COLUMN ige_number VARCHAR(50) NULL UNIQUE AFTER level;

CREATE INDEX idx_ige_number ON bulletin_configs(ige_number);
CREATE INDEX idx_config_section ON bulletin_configs(school_id, section_id);
```

**Execute in MySQL:**
```bash
mysql -u root -p your_database < migration_add_bulletin_ige_number.sql
```

### Step 2: Model Updates
The `BulletinConfig` model now includes:
- `ige_number` column (unique, nullable)
- `generate_ige_number()` method - generates new IGE numbers
- `_get_section_abbreviation()` - converts section name to 2-letter code
- `_get_next_ige_sequence()` - gets next sequence number

### Step 3: Generate IGE Numbers for Existing Bulletins

**Option A: Using the setup script**
```bash
python setup_ige_system.py
```

**Option B: Using the generation script directly**
```bash
python generate_ige_numbers.py
```

**Option C: Manual generation in Python shell**
```python
from app import create_app, db
from models import BulletinConfig

app = create_app()
with app.app_context():
    configs = BulletinConfig.query.filter(BulletinConfig.ige_number.is_(None)).all()
    for config in configs:
        config.ige_number = config.generate_ige_number()
    db.session.commit()
```

### Step 4: Restart Application
```bash
python run_app.py
```

---

## 🎮 How It Works

### Automatic Generation
When a new bulletin configuration is created:
1. System gets the section name (e.g., "Primaire Scientifique")
2. Converts to abbreviation (e.g., "PS")
3. Finds the highest existing IGE number for that section
4. Generates the next number (e.g., "026")
5. Stores as `IGE/PS/026`

### Viewing IGE Numbers
In the bulletin configuration interface (`/admin/bulletins-config`):
1. Select a section
2. Select a level
3. The IGE number displays in the validation status area

**Display format:**
```
🔢 IGE/PS/026  ✔ Validé le 2024-01-15 par Admin
```

### API Response
The configuration API now returns the IGE number:
```json
{
  "id": 1,
  "section_name": "Primaire Scientifique",
  "level": "1",
  "ige_number": "IGE/PS/026",
  "validated": true,
  "validated_at": "2024-01-15T10:30:00",
  "validated_by": "Admin User",
  "branches": [...]
}
```

---

## 📁 Files Modified/Created

### New Files
- `migration_add_bulletin_ige_number.sql` - Database migration
- `generate_ige_numbers.py` - Script to generate IGE numbers
- `setup_ige_system.py` - Complete setup wizard

### Modified Files
1. **models/__init__.py**
   - Added `ige_number` column to `BulletinConfig`
   - Added `generate_ige_number()` method
   - Added helper methods for abbreviation and sequencing

2. **routes/admin/bulletins.py**
   - Updated `_save_bulletin_config_data()` to generate IGE numbers
   - Updated `_serialize_config_response()` to include IGE number

3. **templates/admin/bulletins.html**
   - Updated `updateValidationStatus()` to display IGE number
   - Added badge styling for IGE display

---

## 🔍 Database Schema

### bulletin_configs Table Changes
```sql
ALTER TABLE bulletin_configs 
ADD COLUMN ige_number VARCHAR(50) NULL UNIQUE;

-- Indexes for performance
CREATE INDEX idx_ige_number ON bulletin_configs(ige_number);
CREATE INDEX idx_config_section ON bulletin_configs(school_id, section_id);
```

### Sample Data
| id | school_id | section_id | level | ige_number | validated | created_at |
|---|---|---|---|---|---|---|
| 1 | 1 | 5 | 1 | IGE/PS/001 | 1 | 2024-01-15 |
| 2 | 1 | 5 | 2 | IGE/PS/002 | 1 | 2024-01-16 |
| 3 | 1 | 6 | 1 | IGE/SS/001 | 1 | 2024-01-17 |

---

## 🧪 Testing

### Test Scenario 1: Create New Bulletin
1. Go to `/admin/bulletins-config`
2. Select "Primaire Scientifique" section
3. Select "Level 1"
4. Click "SAUVEGARDER"
5. ✅ Verify: IGE number `IGE/PS/XXX` appears in status bar

### Test Scenario 2: Generate for Existing
1. Run `python generate_ige_numbers.py`
2. ✅ Verify: All bulletins now have IGE numbers

### Test Scenario 3: Uniqueness
1. Try creating two bulletins with same section/level
2. ✅ Verify: They should have different IGE numbers (different sequence)

### Test Scenario 4: Section Abbreviations
1. Create bulletins for different sections
2. ✅ Verify: Each section uses correct abbreviation
   - PS for Primaire Scientifique
   - SS for Secondaire Scientifique
   - etc.

---

## ⚙️ Configuration

### Customizing Section Abbreviations
To customize section abbreviations, edit in `models/__init__.py`:

```python
@staticmethod
def _get_section_abbreviation(section_name):
    mappings = {
        'primaire scientifique': 'PS',
        'your custom section': 'YC',  # Add here
        # ...
    }
```

### Customizing Sequence Format
To change the number format (e.g., from `026` to just `26`):

```python
def generate_ige_number(self):
    # Change from:
    ige_num = f"IGE/{section_abbr}/{next_num:03d}"
    
    # To:
    ige_num = f"IGE/{section_abbr}/{next_num}"
```

---

## 🐛 Troubleshooting

### Issue: Migration fails with "Column already exists"
**Solution:** The column may already exist from a previous attempt
```sql
-- Check if column exists:
DESC bulletin_configs;

-- If it exists, no need to run migration again
```

### Issue: IGE numbers not generating
**Solution:** Check if database migration was applied
```bash
# Verify the column exists:
mysql -u root -p your_db -e "DESC bulletin_configs;" | grep ige_number
```

### Issue: IGE numbers are NULL for existing bulletins
**Solution:** Run the generation script
```bash
python generate_ige_numbers.py
```

### Issue: Duplicate IGE numbers
**Solution:** This shouldn't happen due to UNIQUE constraint. If it occurs:
```sql
-- Find duplicates:
SELECT ige_number, COUNT(*) 
FROM bulletin_configs 
WHERE ige_number IS NOT NULL 
GROUP BY ige_number 
HAVING COUNT(*) > 1;

-- Regenerate IGE numbers by setting to NULL and running script:
UPDATE bulletin_configs SET ige_number = NULL;
```

---

## 📝 API Documentation

### GET /admin/api/bulletin-config/<section>/<level>
Returns bulletin configuration including IGE number:

**Response:**
```json
{
  "id": 1,
  "section_name": "Primaire Scientifique",
  "level": "1",
  "ige_number": "IGE/PS/026",
  "validated": true,
  "branches": [...]
}
```

### POST /admin/api/bulletin-config
Creates/updates bulletin configuration and auto-generates IGE number.

**Auto-generation happens when:**
- New configuration is created
- First time configuration is saved

---

## 🎯 Future Enhancements

Possible future improvements:
1. ✅ **Manual IGE Number Input** - Allow admins to set custom IGE numbers
2. ✅ **IGE History** - Track IGE number changes
3. ✅ **Report Export** - Include IGE numbers in bulletin exports
4. ✅ **Search by IGE** - Quick lookup by IGE number
5. ✅ **IGE Statistics** - Dashboard showing IGE number usage

---

## 📞 Support

For issues or questions about the IGE numbering system:
1. Check the troubleshooting section above
2. Review the test scenarios
3. Check application logs: `instance/logs/`

---

## 📄 Version History

### v1.0 (2024-01-15)
- ✅ Initial IGE numbering system
- ✅ Automatic sequence generation
- ✅ Section abbreviation mapping
- ✅ Database migration
- ✅ Frontend display integration
- ✅ Generation scripts

---

**Last Updated:** January 15, 2024  
**System Version:** 1.0  
**Status:** ✅ Production Ready
