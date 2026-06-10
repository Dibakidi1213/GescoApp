# 🧪 Guide de Vérification - Système IGE

## ✅ Points de Vérification

### 1. Application en Cours d'Exécution
```bash
# L'application doit être accessible à:
http://localhost:5000
```

✅ **Vérification:** L'application Flask est en cours d'exécution
```
 * Serving Flask app 'app'
 * Debug mode: on
```

---

### 2. Colonne IGE Créée
```bash
# La colonne a été auto-créée lors du démarrage de l'application
```

✅ **Vérification:** Dans la base de données
```sql
DESC bulletin_configs;
-- Vous devez voir: ige_number | varchar(50) | YES | ... | NULL | ...
```

---

### 3. Bulletins Numérotés
```bash
# 11 bulletins ont reçu leurs numéros IGE
```

✅ **Vérification:** 
```
✅ Config ID 1: SCIENCES (1) → IGE/SC/001
✅ Config ID 2: LATIN PHILO (1) → IGE/LP/001
✅ Config ID 3: SCIENCES (4) → IGE/SC/002
... (et 8 autres)
✅ Config ID 11: LATIN PHILO (4) → IGE/LP/007
```

---

## 🎮 Test Interactif dans l'Interface

### Étape 1: Accéder à la Configuration des Bulletins
1. Ouvrez: `http://localhost:5000/admin/bulletins-config`
2. Connectez-vous avec vos identifiants admin

### Étape 2: Charger une Configuration Existante
1. Sélectionnez une **Section** (ex: "SCIENCES")
2. Sélectionnez un **Niveau** (ex: "1")
3. Attendez le chargement

### Étape 3: Vérifier le Numéro IGE
Vous devez voir le numéro IGE affichée comme suit:

```
🔢 IGE/SC/001  ✔ Validé le 2024-01-15 par Admin
```

---

## 🔍 Test via l'API

### Tester l'API de Configuration

```bash
# Terminal PowerShell
$url = "http://localhost:5000/admin/api/bulletin-config/SCIENCES/1?school_id=1"
(Invoke-WebRequest -Uri $url -UseBasicParsing).Content | ConvertFrom-Json | Select-Object ige_number
```

**Réponse attendue:**
```
ige_number
-----------
IGE/SC/001
```

### Exemple Complet
```bash
Invoke-WebRequest -Uri "http://localhost:5000/admin/api/bulletin-config/SCIENCES/1?school_id=1" `
  -UseBasicParsing | ForEach-Object { $_.Content | ConvertFrom-Json }
```

**Résultat:**
```json
{
  "id": 1,
  "section_name": "SCIENCES",
  "level": "1",
  "ige_number": "IGE/SC/001",
  "validated": true,
  "branches": [...]
}
```

---

## 🗄️ Test Base de Données

### Requête SQL pour Vérifier les Numéros IGE

```sql
SELECT 
  bc.id,
  bc.school_id,
  s.name as section_name,
  bc.level,
  bc.ige_number,
  bc.validated,
  bc.academic_year
FROM bulletin_configs bc
LEFT JOIN sections s ON bc.section_id = s.id
WHERE bc.ige_number IS NOT NULL
ORDER BY bc.ige_number;
```

**Résultat attendu:**
```
| id  | school_id | section_name  | level | ige_number | validated | academic_year |
|-----|-----------|---------------|-------|-----------|-----------|--------------|
| 1   | 1         | SCIENCES      | 1     | IGE/SC/001| 1         | 2025 - 2026  |
| 2   | 1         | LATIN PHILO   | 1     | IGE/LP/001| 1         | 2025 - 2026  |
| 3   | 1         | SCIENCES      | 4     | IGE/SC/002| 1         | 2025 - 2026  |
...
```

---

## 🧪 Test de Création Nouvelle Configuration

### Créer une Nouvelle Configuration et Vérifier le Numéro IGE

1. **Accédez** à `/admin/bulletins-config`
2. **Sélectionnez** une section et niveau **non encore configurés**
3. **Ajoutez** quelques branches
4. **Cliquez** "SAUVEGARDER"

### Résultat Attendu
- ✅ La nouvelle configuration est créée
- ✅ Un numéro IGE est généré automatiquement
- ✅ Le format est `IGE/[SECTION]/[NUMERO]`
- ✅ Le numéro s'affiche dans l'interface

---

## ⚠️ Diagnostique des Problèmes

### Problème: Pas de Numéro IGE Affiché

**Vérifications:**
1. ✅ L'application a-t-elle redémarré après l'initialisation?
   ```bash
   # Redémarrez si nécessaire
   python run_app.py
   ```

2. ✅ La colonne existe-t-elle?
   ```sql
   DESC bulletin_configs;
   ```

3. ✅ Les bulletins ont-ils des numéros?
   ```sql
   SELECT COUNT(*) as total, COUNT(ige_number) as avec_ige 
   FROM bulletin_configs;
   ```

### Problème: Numéros IGE Dupliqués

Ce ne devrait **pas** arriver car le système génère automatiquement des séquences uniques. Mais si c'est le cas:

```sql
-- Vérifier les doublons
SELECT ige_number, COUNT(*) as count
FROM bulletin_configs
WHERE ige_number IS NOT NULL
GROUP BY ige_number
HAVING COUNT(*) > 1;

-- Régénérer si nécessaire
python init_ige_system.py
```

### Problème: Erreur "Column doesn't exist"

```bash
# Relancer l'initialisation
python init_ige_system.py
```

---

## 📝 Checklist de Vérification Complète

### Installation
- [ ] Application Flask redémarrée
- [ ] Colonne `ige_number` existe dans DB
- [ ] 11 bulletins numérotés avec succès
- [ ] Pas d'erreurs dans les logs

### Fonctionnalité
- [ ] Interface affiche les numéros IGE
- [ ] API retourne les numéros IGE
- [ ] Nouvelle configuration génère un numéro
- [ ] Format est `IGE/[SECTION]/[NUMERO]`

### Performance
- [ ] Aucun délai excessif de chargement
- [ ] Génération des numéros rapide
- [ ] Interface réactive

---

## 🎯 Tests Finaux Recommandés

### Test 1: Charger Configuration Existante
1. Accédez à `/admin/bulletins-config`
2. Sélectionnez SCIENCES, niveau 1
3. ✅ Vérifiez: `IGE/SC/001` s'affiche

### Test 2: Créer Nouvelle Configuration
1. Accédez à `/admin/bulletins-config`  
2. Sélectionnez une section non configurée
3. Ajoutez quelques branches
4. Sauvegardez
5. ✅ Vérifiez: Nouveau numéro IGE généré

### Test 3: Valider la Configuration
1. Chargez une configuration
2. Cliquez "VALIDER" (si non validée)
3. ✅ Vérifiez: Statut change, IGE persiste

### Test 4: Exporter/Importer
1. Chargez une configuration avec IGE
2. Cliquez "TÉLÉCHARGER"
3. ✅ Vérifiez: JSON contient le numéro IGE

---

## 📊 Données de Test

### Sample Configuration avec IGE

```json
{
  "id": 1,
  "section_name": "SCIENCES",
  "level": "1",
  "ige_number": "IGE/SC/001",
  "academic_year": "2025 - 2026",
  "validated": true,
  "validated_at": "2024-01-15T10:30:00",
  "validated_by": "Admin",
  "branches": [
    {
      "id": 1,
      "name": "Mathématiques",
      "order": 1,
      "max_value": 20,
      "include_period_1": true,
      "include_period_2": true
    },
    {
      "id": 2,
      "name": "Français",
      "order": 2,
      "max_value": 20,
      "include_period_1": true,
      "include_period_2": true
    }
  ]
}
```

---

## ✅ Validation Finale

Tous les tests ci-dessus devraient **réussir** ✅

Si vous rencontrez des problèmes, consultez:
- 📖 [IGE_NUMBERING_SYSTEM.md](IGE_NUMBERING_SYSTEM.md) - Documentation technique
- 🚀 [QUICK_START_IGE.md](QUICK_START_IGE.md) - Guide rapide
- 📋 [IMPLEMENTATION_SUMMARY_IGE.md](IMPLEMENTATION_SUMMARY_IGE.md) - Résumé implémentation

---

**Status:** ✅ Système Prêt pour Test  
**Date:** 15 Janvier 2024  
**Version:** 1.0
