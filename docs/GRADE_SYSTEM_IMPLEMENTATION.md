# Système de Saisie des Notes - Documentation

## Vue d'ensemble
Un système complet de gestion des notes pour les professeurs a été implémenté. Le professeur peut désormais entrer des notes pour chaque période et voir les calculs instantanés des totaux et pourcentages.

## Accès
**URL**: `http://localhost:5000/professor/`

## Fonctionnalités

### 1. Sélection Hiérarchique (Section → Niveau → Classe → Cours)

Le système utilise une sélection en cascade avec 4 niveaux:

#### Étape 1: Sélection de la Section
- Menu déroulant avec toutes les sections du professeur
- Affiche le nom de la section
- Charge automatiquement les niveaux disponibles

#### Étape 2: Sélection du Niveau
- Menu déroulant actif après sélection de la section
- Affiche les niveaux (p.ex. "6ème", "5ème", "4ème", etc.)
- Charge automatiquement les classes du niveau sélectionné

#### Étape 3: Sélection de la Classe
- Menu déroulant actif après sélection du niveau
- Affiche les classes disponibles (p.ex. "A", "B", "C")
- Charge automatiquement les cours de la classe sélectionnée

#### Étape 4: Sélection du Cours
- Menu déroulant final avec les cours disponibles
- Une fois sélectionné, affiche le tableau d'entrée des notes
- Charge les étudiants et les notes existantes

### 2. Sélection de la Période (Interface)
- 6 boutons radio pour sélectionner la période active (1èP, 2èP, EXA1, 3èP, 4èP, EXA2)
- La sélection met en surbrillance l'affichage de la période
- Permet au professeur de se concentrer sur une période à la fois

### 3. Saisie des Notes
Le tableau affiche tous les étudiants avec 6 colonnes d'entrée pour les notes:

| Colonne | Période | Plage | Description |
|---------|---------|-------|-------------|
| 1 | 1èP | 0-20 | Première période |
| 2 | 2èP | 0-20 | Deuxième période |
| 3 | EXA1 | 0-20 | Premier examen |
| 4 | **Total 1** | Auto | (1èP + 2èP + EXA1) / 3 |
| 5 | 3èP | 0-20 | Troisième période |
| 6 | 4èP | 0-20 | Quatrième période |
| 7 | EXA2 | 0-20 | Deuxième examen |
| 8 | **Total 2** | Auto | (3èP + 4èP + EXA2) / 3 |
| 9 | **Total Général** | Auto | (Total 1 + Total 2) / 2 |
| 10 | **Pourcentage** | Auto | (Total Général / 20) × 100 |

### 4. Calculs Instantanés

#### Total 1 (Fond gris)
```
Total 1 = (1èP + 2èP + EXA1) / 3
```

#### Total 2 (Fond gris)
```
Total 2 = (3èP + 4èP + EXA2) / 3
```

#### Total Général (Fond jaune)
```
Total Général = (Total 1 + Total 2) / 2
```

#### Pourcentage Annuel (Fond jaune)
```
Pourcentage = (Total Général / 20) × 100
```

### 5. Codage Couleur du Pourcentage
- 🟢 **Vert**: ≥ 80% (Excellent)
- 🟠 **Orange**: 60% - 79% (Bon)
- 🔴 **Rouge**: < 60% (À améliorer)

## Comportement Utilisateur

### Saisie d'une Note
1. Le professeur entre une note (0-20, décimales acceptées)
2. Les totaux et pourcentages se mettent à jour **en temps réel**
3. À la sortie du champ (blur), la note est **automatiquement sauvegardée** en base de données
4. Un message de confirmation s'affiche brièvement
5. La note est persistée et sera rechargée au prochain accès

### Modification d'une Note
- Cliquer sur un champ existant et modifier la valeur
- Les calculs se mettent à jour en temps réel
- La note est sauvegardée au blur

### Changement de Cours
- Utiliser le menu déroulant "Sélection du Cours"
- La page recharge avec les données du nouveau cours

## Architecture Technique

### Backend (Flask)
**Fichier**: `routes/professor.py`

#### Route GET `/professor/`
```python
- Récupère le cours sélectionné à partir des paramètres de requête
- Charge les notes groupées par étudiant et période
- Passe les données au template
```

#### API Routes pour la Sélection Hiérarchique

**1. GET `/professor/api/sections`**
Retourne toutes les sections où le professeur enseigne
```json
[
  {
    "id": 1,
    "name": "6ème",
    "level": "6ème",
    "class_name": "A"
  }
]
```

**2. GET `/professor/api/levels/<section_id>`**
Retourne tous les niveaux d'une section
```json
["6ème", "5ème", "4ème", "3ème"]
```

**3. GET `/professor/api/classes/<section_id>/<level>`**
Retourne toutes les classes d'un niveau
```json
["A", "B", "C", "D"]
```

**4. GET `/professor/api/courses/<section_id>/<level>/<class_name>`**
Retourne tous les cours du professeur pour cette classe
```json
[
  {
    "id": 1,
    "title": "Mathématiques",
    "section_id": 1
  }
]
```

#### Route POST `/professor/grade`
```json
{
  "student_id": 123,
  "period": "1èP",
  "value": 15.5,
  "course_id": 456
}
```

**Réponse**:
```json
{
  "success": true,
  "student_id": 123,
  "period": "1èP",
  "value": 15.5
}
```

### Frontend (JavaScript)
**Fichier**: `static/js/grades.js`

#### Fonction Principal
- `calculateTotals(studentId)`: Calcule tous les totaux pour un étudiant
- `saveGrade(studentId, period, value)`: Sauvegarde une note en base
- Écouteurs d'événements pour les changements d'entrée
- Initialisation des calculs au chargement de la page

### Base de Données
**Modèle**: `models.Grade`

Chaque note est stockée avec:
- `school_id`: École
- `student_id`: Étudiant
- `course_id`: Cours
- `period`: Période (1èP, 2èP, EXA1, 3èP, 4èP, EXA2)
- `value`: Valeur numérique (0-20)

## Exemples de Calculau

### Exemple 1: Bon Étudiant
| Période | Note |
|---------|------|
| 1èP | 18 |
| 2èP | 17 |
| EXA1 | 19 |
| **Total 1** | **18.00** |
| 3èP | 16 |
| 4èP | 17 |
| EXA2 | 18 |
| **Total 2** | **17.00** |
| **Total Général** | **17.50** |
| **Pourcentage** | **87.5%** 🟢 |

### Exemple 2: Étudiant Moyen
| Période | Note |
|---------|------|
| 1èP | 12 |
| 2èP | 13 |
| EXA1 | 11 |
| **Total 1** | **12.00** |
| 3èP | 13 |
| 4èP | 12 |
| EXA2 | 14 |
| **Total 2** | **13.00** |
| **Total Général** | **12.50** |
| **Pourcentage** | **62.5%** 🟠 |

## Sécurité

- ✅ Vérification que le professeur est authentifié
- ✅ Vérification que le cours appartient au professeur
- ✅ Vérification que le cours appartient à l'école du professeur
- ✅ Les notes ne peuvent être sauvegardées que pour les cours du professeur

## Prochaines Améliorations Possibles

1. **Mémorisation des Sélections**
   - Enregistrer la dernière section/niveau/classe sélectionnés
   - Restaurer au rechargement de la page

2. **Recherche Rapide**
   - Champ de recherche pour les cours
   - Autocomplete sur les niveaux/classes

3. **Export des Notes**
   - Exporter en Excel/CSV
   - Générer des bulletins de notes

4. **Historique des Notes**
   - Voir les modifications précédentes
   - Restaurer une note antérieure

5. **Statistiques**
   - Moyenne de la classe par période
   - Distribution des notes
   - Élèves à suivre (< 10/20)

6. **Validations**
   - Périodes de saisie fermées
   - Validations personnalisées
   - Approvals workflow

7. **Notifications**
   - Notifications par email aux parents
   - Notifications des élèves

## Dépannage

### Les sélecteurs sont vides
- Vérifier que le professeur a au moins un cours assigné
- Vérifier que les sections, niveaux et classes sont correctement configurés
- Vérifier les permissions du professeur dans la base de données

### Les niveaux ne s'affichent pas
- Cliquer sur une section d'abord
- Vérifier que la section a des niveaux dans la base de données
- Vérifier que le professeur a des cours dans cette section

### Les classes ne s'affichent pas
- Cliquer sur un niveau d'abord
- Vérifier que le professeur a des cours pour ce niveau

### Les cours ne s'affichent pas
- Cliquer sur une classe d'abord
- Vérifier que le professeur a des cours pour cette classe
- Vérifier l'association cours-professeur-section

### Les notes ne s'affichent pas
- Vérifier que le professeur est associé à au moins un cours
- Vérifier que le cours est associé à une section
- Vérifier que des étudiants existent dans la section

### Les calculs ne se mettent pas à jour
- Vérifier que JavaScript est activé
- Vérifier la console du navigateur pour les erreurs
- Rafraîchir la page (F5)

### Les notes ne sont pas sauvegardées
- Vérifier la connexion réseau
- Vérifier la console du navigateur pour les erreurs
- Vérifier que le serveur Flask est en cours d'exécution
- Vérifier les logs du serveur pour plus de détails

## Contact & Support
Pour toute question, contacter l'administrateur du système.
