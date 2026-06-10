# ⚡ Quick Start Guide - IGE Numbering System

## Installation en 3 étapes

### 1️⃣ Appliquer la migration SQL (5 minutes)

**Option A: Ligne de commande**
```bash
mysql -u root -p your_database < migration_add_bulletin_ige_number.sql
```

**Option B: PhpMyAdmin ou client MySQL**
Copier-coller le contenu de `migration_add_bulletin_ige_number.sql` et exécuter.

**Option C: Utiliser le script de configuration**
```bash
python setup_ige_system.py
```
Le script vous guidera interactivement.

---

### 2️⃣ Générer les numéros IGE (2 minutes)

Pour les bulletins existants:
```bash
python generate_ige_numbers.py
```

**Output attendu:**
```
✅ Found 5 bulletin configurations without IGE numbers
✅ Config ID 1: Primaire Scientifique (1) → IGE/PS/001
✅ Config ID 2: Primaire Scientifique (2) → IGE/PS/002
✅ Config ID 3: Secondaire Scientifique (1) → IGE/SS/001
...
✅ Successfully generated 5 IGE numbers!
```

---

### 3️⃣ Redémarrer et tester (1 minute)

```bash
python run_app.py
```

Puis allez à: `http://localhost:5000/admin/bulletins-config`

✅ Vous devriez voir le numéro IGE affiché comme: **🔢 IGE/PS/026**

---

## 🎯 Format des Numéros IGE

| Exemple | Signification |
|---------|---|
| `IGE/PS/001` | 1er bulletin - Primaire Scientifique |
| `IGE/PS/026` | 26e bulletin - Primaire Scientifique |
| `IGE/SS/001` | 1er bulletin - Secondaire Scientifique |
| `IGE/SL/015` | 15e bulletin - Secondaire Littéraire |

### Abréviations des sections:
- **PS** = Primaire Scientifique
- **PL** = Primaire Littéraire
- **SS** = Secondaire Scientifique
- **SL** = Secondaire Littéraire
- **TS** = Technique Scientifique
- **TL** = Technique Littéraire

---

## ✅ Checklist de Vérification

- [ ] Migration SQL appliquée sans erreurs
- [ ] Script de génération exécuté avec succès
- [ ] Application redémarrée
- [ ] Naviguer vers `/admin/bulletins-config`
- [ ] Créer ou charger une configuration de bulletin
- [ ] Voir le numéro IGE dans le statut de validation
- [ ] Le format est `IGE/[ABBR]/[NUM]` (ex: IGE/PS/026)

---

## 🔧 Dépannage Rapide

**Problem:** "Column already exists"  
**Solution:** La colonne existe déjà, c'est normal. Passez à l'étape 2.

**Problem:** IGE numbers are NULL  
**Solution:** 
```bash
# Assurez-vous que la migration a été appliquée
mysql -u root -p your_db -e "DESC bulletin_configs;" | grep ige_number

# Si la colonne n'existe pas, appliquez la migration
# Si elle existe, lancez la génération
python generate_ige_numbers.py
```

**Problem:** Pas de numéro IGE dans l'interface  
**Solution:**
```bash
# Redémarrez Flask
python run_app.py

# Videz le cache du navigateur (Ctrl+Shift+Delete)
```

---

## 📚 Documentation Complète

Pour des informations détaillées:
👉 Consultez [IGE_NUMBERING_SYSTEM.md](IGE_NUMBERING_SYSTEM.md)

---

## 🎉 Vous êtes prêt!

Votre système de numérotation IGE est maintenant actif!

Chaque bulletin de configuration aura automatiquement un numéro unique au format `IGE/[SECTION]/[NUMERO]`.
