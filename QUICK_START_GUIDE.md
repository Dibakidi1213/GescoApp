# GUIDE DE DÉMARRAGE RAPIDE - Système de Saisie des Notes v2

## 🎬 Avant de Commencer

1. **Connexion Professeur**
   - Accédez à: `http://localhost:5000/login`
   - Entrez vos identifiants de professeur
   - Cliquez sur "Connexion"

2. **Accès à la Saisie des Notes**
   - Allez à: `http://localhost:5000/professor/`

---

## 📖 GUIDE UTILISATEUR ÉTAPE PAR ÉTAPE

### Étape 1: Sélectionner la Section
```
1. Regardez le premier dropdown: "1. Sélection de la Section"
2. Cliquez dessus
3. Choisissez une section (Ex: "6ème", "5ème", etc.)
4. Les options du "Niveau" se remplissent automatiquement
```

### Étape 2: Sélectionner le Niveau
```
1. Le deuxième dropdown "2. Sélection du Niveau" s'active
2. Cliquez dessus
3. Choisissez un niveau (Ex: "6ème", "5ème", etc.)
4. Les options de la "Classe" se remplissent automatiquement
```

### Étape 3: Sélectionner la Classe
```
1. Le troisième dropdown "3. Sélection de la Classe" s'active
2. Cliquez dessus
3. Choisissez une classe (Ex: "A", "B", "C", etc.)
4. Les options du "Cours" se remplissent automatiquement
```

### Étape 4: Sélectionner le Cours
```
1. Le quatrième dropdown "4. Sélection du Cours" s'active
2. Cliquez dessus
3. Choisissez un cours (Ex: "Mathématiques", "Français", etc.)
4. Le tableau des notes apparaît immédiatement
```

### Étape 5: Saisir les Notes
```
1. Vous voyez maintenant le tableau avec tous les étudiants
2. Colonne "Période": 1èP, 2èP, EXA1, 3èP, 4èP, EXA2
3. Cliquez sur une cellule de note pour un étudiant et une période
4. Tapez la note (0 à 20, virgule décimale acceptée)
5. Appuyez sur Tab ou cliquez ailleurs
6. La note est sauvegardée automatiquement 💾
```

### Étape 6: Vérifier les Calculs
```
Automatiques et instantanés:

1. Total 1 (gris): (1èP + 2èP + EXA1) ÷ 3
2. Total 2 (gris): (3èP + 4èP + EXA2) ÷ 3
3. Total Général (jaune): (Total 1 + Total 2) ÷ 2
4. Pourcentage (jaune): (Total Général ÷ 20) × 100

Couleurs:
- 🟢 Vert: ≥ 80%
- 🟠 Orange: 60-79%
- 🔴 Rouge: < 60%
```

---

## 🔧 DÉPANNAGE RAPIDE

### Les dropdowns sont vides
→ Vérifier que vous êtes connecté en tant que professeur  
→ Vérifier que vous avez au moins un cours assigné

### Je ne vois pas mes niveaux
→ Cliquer d'abord sur une section  
→ Attendre 1-2 secondes que les données se chargent

### Les calculs ne s'affichent pas
→ Rafraîchir la page (F5)  
→ Vérifier que JavaScript est activé  
→ Vérifier la console (F12) pour les erreurs

### Les notes ne se sauvegardent pas
→ Vérifier la connexion internet  
→ Vérifier que le serveur Flask est en cours d'exécution  
→ Essayer de saisir une note et attendre la notification

---

## 💡 ASTUCES

1. **Raccourci Clavier**
   - Tab: Passer à la note suivante
   - Maj + Tab: Revenir à la note précédente

2. **Saisie Rapide**
   - Vous pouvez utiliser des décimales: 15.5, 18.25
   - Les totaux se calculent en temps réel pendant la frappe

3. **Changement de Cours**
   - Pour changer de cours rapidement, modifiez juste le dropdown "Cours"
   - Pas besoin de recommencer depuis la section

4. **État Persistant**
   - La page se souvient de votre sélection
   - Vous pouvez marquer la page et y revenir directement

---

## 📋 EXEMPLE COMPLET

```
1. Login → superadmin / password
2. Aller à: http://localhost:5000/professor/
3. Section: "6ème" ↓
4. Niveau: "6ème" ↓
5. Classe: "A" ↓
6. Cours: "Mathématiques" ↓
   
   Tableau apparaît avec étudiants:
   - Jean Dupont
   - Marie Lemaire
   - Pierre Martin

7. Pour Jean Dupont, 1èP: [Cliquer] → [Taper 15] → [Tab]
   → Note sauvegardée ✓

8. Attendre les calculs automatiques:
   - Total 1 s'affiche
   - Total 2 s'affiche
   - Pourcentage s'affiche en couleur

9. Continuer pour les autres périodes et étudiants
```

---

## 📞 SUPPORT

Pour toute question ou problème:
1. Vérifier le fichier `GRADE_SYSTEM_IMPLEMENTATION.md`
2. Vérifier la console du navigateur (F12)
3. Vérifier les logs du serveur Flask

---

## ✨ NOUVEAUTÉS v2

✅ **Sélection hiérarchique**: Section → Niveau → Classe → Cours  
✅ **Interface plus intuitive**: Navigation pas à pas  
✅ **Validation en cascade**: Chaque étape valide la précédente  
✅ **Tous les calculs conservés**: Total 1, 2, Général, %  
✅ **Sécurité améliorée**: Isolation par professeur  

---

Bonne utilisation! 🎉
