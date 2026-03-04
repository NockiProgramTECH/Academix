# Diagramme de flux - Système de gestion des dossiers

## 1️⃣ Flux d'inscription d'un élève

```
┌─────────────────────────────────────────────────────────────┐
│              INSCRIPTION D'UN ÉLÈVE                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌──────────────────────┐
                  │ Formulaire rempli   │
                  │ (HTML - Frontend)   │
                  └──────────────────────┘
                              │
                              ▼
                  ┌──────────────────────┐
                  │ POST /api/inscription│
                  │ (multipart/form-data)│
                  └──────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────────┐
        │ traiter_inscription_formdata(request)       │
        │ (views.py)                                   │
        └──────────────────────────────────────────────┘
        Étapes:
        1. Valider EleveForm
        2. Vérifier les documents
        3. Valider les fichiers/photos
        4. Créer Eleve (save())
        5. Créer DocumentEleve
        6. Créer Tuteur
                              │
                              ▼
                  ┌──────────────────────┐
                  │ eleve.save()         │
                  │ (models.py - Eleve)  │
                  └──────────────────────┘
                              │
                              ▼
            ┌────────────────────────────────┐
            │ Génération du matricule        │
            │ (si non existant)              │
            └────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ ✨ CRÉATION AUTOMATIQUE DES DOSSIERS       │
        │ create_eleve_folder_structure()            │
        │ (utils.py)                                  │
        └────────────────────────────────────────────┘
        Crée:
        1. media/inscriptions/{CLASSE}/photos/
        2. media/inscriptions/{CLASSE}/photos/{NOM-PRENOM}/
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ Sauvegarde des fichiers:                   │
        │ - Photo → media/.../photos/{NOM}/{fichier} │
        │ - ACte naissance → même dossier            │
        │ - Bulletins → même dossier                 │
        │ - Diplômes → même dossier                  │
        └────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ JSON Response:                             │
        │ {                                          │
        │   "success": true,                         │
        │   "data": {                                │
        │     "eleve_id": "...",                     │
        │     "matricule": "2026BT1203",             │
        │     "nom_complet": "LANKOANDE-Tierry"      │
        │   }                                        │
        │ }                                          │
        └────────────────────────────────────────────┘
                              │
                              ▼
                  ┌──────────────────────┐
                  │ Redirection vers     │
                  │ Page de confirmation │
                  │ (confirmation.html)  │
                  └──────────────────────┘
```

---

## 2️⃣ Flux de suppression d'un élève

```
┌─────────────────────────────────────────────────────────────┐
│              SUPPRESSION D'UN ÉLÈVE                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌──────────────────────┐
                  │ Admin Django ou      │
                  │ Code personnalisé    │
                  │ eleve.delete()       │
                  └──────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ Méthode delete() du modèle Eleve           │
        │ (models.py)                                │
        └────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ ✨ SUPPRESSION AUTOMATIQUE DES DOSSIERS    │
        │ delete_eleve_folder()                      │
        │ (utils.py)                                 │
        └────────────────────────────────────────────┘
        Supprime:
        ├── media/inscriptions/{CLASSE}/photos/{NOM-PRENOM}/
        │   ├── photo_identite.jpg
        │   ├── acte_naissance.pdf
        │   ├── last_bulletin.pdf
        │   └── diplome.pdf
        (dossier entièrement supprimé)
                              │
                              ▼
                  ┌──────────────────────┐
                  │ Suppression dans la   │
                  │ base de données      │
                  └──────────────────────┘
                              │
                              ▼
                  ┌──────────────────────┐
                  │ ✅ Suppression        │
                  │    complète          │
                  └──────────────────────┘
```

---

## 3️⃣ Flux de l'ajout de documents/photos à un élève existant

```
┌─────────────────────────────────────────────────────────────┐
│         AJOUT DE DOCUMENTS/PHOTOS À UN ÉLÈVE EXISTANT        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌──────────────────────┐
                  │ Upload de photo      │
                  │ eleve.photo = file   │
                  │ eleve.save()         │
                  └──────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ get_image(instance, filename)              │
        │ Défine le chemin de destination            │
        └────────────────────────────────────────────┘
        Retourne:
        inscriptions/{CLASSE}/photos/{NOM-PRENOM}/{filename}
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ ImageField de Django:                      │
        │ Sauvegarde le fichier au chemin retourné   │
        └────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ Fichier sauvegardé:                        │
        │ media/inscriptions/6EME/photos/            │
        │        LANKOANDE-Tierry/photo.jpg          │
        └────────────────────────────────────────────┘

Note: Le dossier a déjà été créé lors de l'inscription.
```

---

## 4️⃣ Structure des dossiers créés

```
media/
│
└── inscriptions/
    │
    ├── 6EME/
    │   └── photos/                    ← Créé par create_eleve_folder_structure()
    │       ├── LANKOANDE-Tierry/      ← Créé par create_eleve_folder_structure()
    │       │   ├── photo.jpg
    │       │   ├── acte_naissance.pdf
    │       │   ├── last_bulletin.pdf
    │       │   └── diplome.pdf
    │       ├── KONE-Moussa/
    │       │   ├── photo.jpg
    │       │   ├── acte_naissance.pdf
    │       │   ├── last_bulletin.pdf
    │       │   └── diplome.pdf
    │       └── ... (autres élèves)
    │
    ├── 5EME/
    │   └── photos/
    │       ├── SANE-Fatou/
    │       │   └── ...fichiers...
    │       └── ...
    │
    ├── 4EME/
    ├── 3EME/
    └── 2nd/

Légende:
✨ = Créé automatiquement par le système
```

---

## 5️⃣ Intégration avec le modèle de données Django

```
┌──────────────────────────────────────────────────────────┐
│           MODÈLE ELEVE (models.py)                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  class Eleve(models.Model):                             │
│      id              (UUID)                             │
│      matricule       (CharField)    - Généré            │
│      nom             (CharField)    ┐                   │
│      prenom          (CharField)    ├─► nom_complet     │
│      date_naissance  (DateField)    │   "NOM-PRENOM"    │
│      classe          (CharField)    ┘   Utilisé pour    │
│      adresse         (TextField)        les dossiers    │
│      photo           (ImageField)   ───► Chemin auto    │
│      tuteur          (OneToOne)         get_image()     │
│      statut          (CharField)                        │
│      date_inscription(DateTimeField)                    │
│                                                          │
│  Methods:                                               │
│      save()         ──► Crée dossiers               ✨   │
│      delete()       ──► Supprime dossiers          ✨   │
│      nom_complet    ──► Property pour le dossier       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 6️⃣ Commandes de maintenance

```
┌──────────────────────────────────────────────────────────────┐
│     COMMANDES DE GESTION (management/commands/...)           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  rebuild_student_folders.py                                 │
│  ├─ (sans args)    → rebuild_student_folders              │
│  ├─ --class XXX    → rebuild_student_folders --class 6EME │
│  ├─ --statistics   → Affiche les stats                    │
│  ├─ --check        → Vérifie la cohérence                 │
│  └─ --clean-all    → Nettoie et reconstruit              │
│                                                              │
│  Utilisation:                                               │
│  $ python manage.py rebuild_student_folders                │
│  $ python manage.py rebuild_student_folders --statistics    │
│  $ python manage.py rebuild_student_folders --check         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7️⃣ Fichiers principaux et leurs rôles

```
┌─────────────────────────────────────┐
│ FICHIERS IMPLIQUÉS                  │
├─────────────────────────────────────┤
│                                     │
│ ✨ NEW → Inscriptions/utils.py      │
│    └─ Fonctions de gestion dossiers │
│                                     │
│ 🔧 MODIFIÉ → Inscriptions/models.py │
│    └─ Methods save() et delete()     │
│                                     │
│ 📋 EXISTANT → Inscriptions/views.py │
│    └─ Appelle save() automatiquement │
│                                     │
│ 📋 EXISTANT → Inscriptions/forms.py │
│    └─ Validation des données        │
│                                     │
│ 📚 NEW → DOSSIERS_ELEVES_README.md  │
│    └─ Documentation complète        │
│                                     │
│ 📚 NEW → RESUME_MODIFICATIONS.md    │
│    └─ Résumé des changements        │
│                                     │
│ 📚 NEW → GUIDE_COMMANDE_REBUILD.md  │
│    └─ Guide d'utilisation commandes │
│                                     │
│ ✨ NEW → test_dossiers_eleves.py    │
│    └─ 7 exemples d'utilisation      │
│                                     │
│ ✨ NEW → rebuild_student_folders.py │
│    └─ Commande Django de maintenance│
│                                     │
└─────────────────────────────────────┘
```

---

## 8️⃣ Flux d'erreur et gestion d'exception

```
Opération
   │
   ▼
┌─────────────────────────────┐
│ Tentative de création/suppression │
│ du dossier                  │
└─────────────────────────────┘
   │
   ├─ ✓ Succès
   │   └─► Return (True, "Message de succès")
   │
   └─ ✗ Erreur
       ├─ Dossier parent inexistant?
       │  └─► Path.mkdir(parents=True) ─► Créé!
       │
       ├─ Permission refusée?
       │  └─► Exception capturée
       │      └─► Return (False, "Erreur de permissions")
       │
       ├─ Dossier existant?
       │  └─► Path.mkdir(exist_ok=True) ─► OK!
       │
       └─ Autre erreur?
           └─► Return (False, "Erreur: ...")
```

---

## 📊 Synthèse

| Étape | Qui | Quoi | Où |
|-------|-----|------|-----|
| 1 | Frontend | Submit formulaire | HTML/JS |
| 2 | Django | Valide données | views.py |
| 3 | Django | Crée Eleve | models.py |
| 4 | **✨ AUTO** | **Crée dossiers** | **utils.py** |
| 5 | Django | Sauvegarde fichiers | FileField |
| 6 | Frontend | Affiche confirmation | HTML |

---

**Dernière mise à jour:** 3 mars 2026 | **Auteur:** Système automatisé
