# Workflow Complet - Sections et Professeurs

## Architecture

### 1. Création des Sections (Admin)
- URL: `/admin/sections`
- Créer la structure d'organisation: Section (nom) + Niveau + Classe
- Exemples:
  - Latin Philo + 1ère + A
  - Section Test + Primaire + P4

### 2. Importation des Cours (Admin)
- URL: `/admin/courses` 
- Importer les cours avec colonnes optionnelles:
  - `course_title` (obligatoire) - ex: Mathématiques
  - `section_name` (optionnel) - ex: Latin Philo  
  - `level` (optionnel) - ex: 1ère
  - `class_name` (optionnel) - ex: A
  - `professor_full_name` (optionnel) - ex: olivier dibakidi

### 3. Assignation Section + Professeur (Admin)
- URL: `/admin/courses/{id}/edit`
- Pour chaque cours, assigner:
  - **Section / Niveau / Classe** (obligatoire pour utilisation par professeur)
  - **Professeur** (optionnel - peut être assigné later)
- ⚠️ **Important**: Un cours doit avoir une section assignée avant qu'un professeur puisse l'utiliser

### 4. Utilisation par Professeur (Professor)
- URL: `/lyc-e-bankazi/professor/`
- Les professeurs voient uniquement les sections où ils ont des cours assignés
- Sélection hiérarchique: Section → Niveau → Classe → Cours
- Les cours sans section_id n'apparaissent pas (ne peuvent pas être utilisés)

## Schéma API

| Endpoint | Filtre | Retour |
|----------|--------|--------|
| `/api/sections` | Professeur + section_id NOT NULL | Sections avec cours |
| `/api/levels/{section_id}` | Professeur + section_id NOT NULL | Niveaux disponibles |
| `/api/classes/{section_id}/{level}` | Professeur + section_id NOT NULL | Classes disponibles |
| `/api/courses/{section_id}/{level}/{class_name}` | Professeur + section_id NOT NULL | Cours disponibles |

## Exemple Complet

```
1. Admin crée section: "Latin Philo" + "1ère" + "A"
2. Admin importe cours: Mathématiques  
3. Admin édite cours Mathématiques → assigne section "Latin Philo" + professeur "olivier"
4. Professeur olivier accède /professor/:
   - Dropdown sections affiche: "Latin Philo"
   - Sélectionne "1ère" 
   - Sélectionne "A"
   - Cours: "Mathématiques" apparaît
   - Peut saisir les notes
```

## Points Importants

✅ Les sections définies dans `/admin/sections` sont automatiquement disponibles quand assignées aux cours
✅ Chaque professeur ne voit que ses sections
✅ Les cours sans section_id sont invisibles pour les professeurs jusqu'à assignation
✅ La hiérarchie Section→Niveau→Classe garantit l'intégrité des données
