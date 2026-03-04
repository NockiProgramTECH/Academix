# Guide d'utilisation: Commande `rebuild_student_folders`

## 📝 Description

La commande `rebuild_student_folders` permet de gérer et reconstruire les dossiers des élèves. Elle est utile pour:
- Reconstruire tous les dossiers (ex: après une migration ou un problème)
- Reconstruire les dossiers d'une classe spécifique
- Afficher les statistiques
- Vérifier la cohérence entre la base de données et les dossiers

## 🚀 Utilisation

### 1. Reconstruire TOUS les dossiers
Crée les dossiers pour tous les élèves en base de données.

```bash
python manage.py rebuild_student_folders
```

**Exemple de sortie:**
```
🔄 Reconstruction de tous les dossiers...
  [1/25] ✓ LANKOANDE-tierry (6EME)
  [2/25] ✓ LANKOANDE-Piere (2nd)
  ...
✅ Reconstruction terminée: 25/25 dossiers créés
```

### 2. Reconstruire les dossiers d'une classe spécifique
Crée les dossiers seulement pour une classe.

```bash
python manage.py rebuild_student_folders --class 6EME
```

**Classes disponibles:**
- `6EME`
- `5EME`
- `4EME`
- `3EME`
- `2nd`

**Exemple:**
```bash
python manage.py rebuild_student_folders --class 5EME
```

### 3. Afficher les statistiques
Affiche les statistiques sans modifier les dossiers.

```bash
python manage.py rebuild_student_folders --statistics
```

**Exemple de sortie:**
```
📊 STATISTIQUES DES DOSSIERS

Élèves en base de données: 30
Dossiers créés: 30

Par classe:
  ✓ 6EME  - Dossiers:  8 | DB:  8
  ✓ 5EME  - Dossiers:  7 | DB:  7
  ✓ 4EME  - Dossiers:  6 | DB:  6
  ✓ 3EME  - Dossiers:  5 | DB:  5
  ✓ 2nd   - Dossiers:  4 | DB:  4

✅ Tous les dossiers sont synchronisés!
```

### 4. Vérifier la cohérence
Vérifie que tous les élèves en BD ont des dossiers et vice versa.

```bash
python manage.py rebuild_student_folders --check
```

**Exemple de sortie (sans probleme):**
```
🔍 VÉRIFICATION DE LA COHÉRENCE

✅ Aucun problème de cohérence détecté!
```

**Exemple de sortie (avec problèmes):**
```
🔍 VÉRIFICATION DE LA COHÉRENCE

Problèmes trouvés (3):
  ❌ Élève DB trouvé mais dossier manquant: KONE-Moussa
  ⚠️  Dossier orphelin: SANE-Fatou
  ...
```

### 5. Nettoyer et reconstruire complètement
Supprime TOUS les dossiers d'inscription puis les reconstruit. **À utiliser avec prudence!**

```bash
python manage.py rebuild_student_folders --clean-all
```

**Avertissement:**
```
🗑️  Suppression de tous les dossiers inscriptions...
✓ Tous les dossiers ont été supprimés
🔄 Reconstruction de tous les dossiers...
...
```

---

## 💡 Cas d'utilisation

### Situation 1: Problème après une migration
```bash
# Vérifier l'état
python manage.py rebuild_student_folders --statistics

# Si tout est désynchronisé
python manage.py rebuild_student_folders --clean-all
```

### Situation 2: Ajouter des élèves manuels
```bash
# Après avoir ajouté des élèves en admin
python manage.py rebuild_student_folders
```

### Situation 3: Vérifier avant un backup
```bash
python manage.py rebuild_student_folders --check
```

### Situation 4: Reporter une classe entière
```bash
# Les élèves de 6ème montent en 5ème
python manage.py rebuild_student_folders --class 5EME
```

---

## 📊 Statistiques détaillées

Pour obtenir un rapport complet du système:

```bash
#!/bin/bash
echo "=== STATISTIQUES ACTUELLES ==="
python manage.py rebuild_student_folders --statistics

echo -e "\n=== VÉRIFICATION DE LA COHÉRENCE ==="
python manage.py rebuild_student_folders --check

echo -e "\n=== PRÊT POUR LA PRODUCTION ==="
```

---

## 🔧 Options combinées

### Option 1: Reconstruire une classe après importation
```bash
python manage.py rebuild_student_folders --class 6EME
```

### Option 2: Nettoyer tout et démarrer de zéro
```bash
python manage.py rebuild_student_folders --clean-all
```

### Option 3: Diagnostiquer les problèmes
```bash
python manage.py rebuild_student_folders --check
python manage.py rebuild_student_folders --statistics
```

---

## ⚙️ Exemple de script de maintenance

**`maintenance.sh`**
```bash
#!/bin/bash

cd /path/to/GESTION\ ECOLE/WEB

echo "╔════════════════════════════════════════╗"
echo "║ Maintenance des dossiers d'élèves     ║"
echo "╚════════════════════════════════════════╝"

# 1. Vérifier la cohérence
echo -e "\n1. Vérification de la cohérence..."
python manage.py rebuild_student_folders --check

# 2. Afficher les statistiques
echo -e "\n2. Statistiques actuelles..."
python manage.py rebuild_student_folders --statistics

# 3. Si des problèmes -> Reconstruire
read -p "Reconstruire les dossiers manquants? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py rebuild_student_folders
fi

echo -e "\n✅ Maintenance terminée!"
```

**Utilisation:**
```bash
chmod +x maintenance.sh
./maintenance.sh
```

---

## 🚨 Messages d'erreur courants

### "Classe invalide: XXX"
```
Classes valides: 6EME, 5EME, 4EME, 3EME, 2nd
```
**Solution:** Vérifiez l'orthographe exacte de la classe.

### Aucun élève trouvé en {classe}
**Solution:** Vérifiez qu'il existe des élèves inscrits pour cette classe.

### Erreur lors de la suppression/création
**Solution:** 
```bash
# Vérifier les permissions
ls -la media/
chmod -R 755 media/
```

---

## 📞 Support

Pour plus d'informations:
- Consultez `RESUME_MODIFICATIONS.md`
- Consultez `DOSSIERS_ELEVES_README.md`
- Consultez `Inscriptions/utils.py` pour le code source
