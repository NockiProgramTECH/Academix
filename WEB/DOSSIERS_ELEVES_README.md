# Documentation: Gestion automatique des dossiers d'inscription

## Vue d'ensemble
Ce système crée automatiquement une structure de dossiers pour chaque élève inscrit, organisée par classe.

## Structure créée
```
media/
└── inscriptions/
    ├── 6EME/
    │   └── photos/
    │       ├── LANKOANDE-tierry/
    │       ├── LANKOANDE-Piere/
    │       └── ...autres élèves...
    ├── 5EME/
    │   └── photos/
    │       └── ...élèves 5ème...
    ├── 4EME/
    │   └── photos/
    │       └── ...élèves 4ème...
    ├── 3EME/
    │   └── photos/
    │       └── ...élèves 3ème...
    └── 2nd/
        └── photos/
            └── ...élèves 2nde...
```

## Fichiers créés/modifiés

### 1. `Inscriptions/utils.py` (NOUVEAU)
Contient les fonctions utilitaires pour gérer les dossiers :

- **`get_classe_photos_directory(classe)`**
  - Retourne le chemin du dossier photos pour une classe
  - Exemple: `media/inscriptions/6EME/photos/`

- **`get_eleve_directory(classe, nom_complet)`**
  - Retourne le chemin du dossier pour un élève spécifique
  - Exemple: `media/inscriptions/6EME/photos/LANKOANDE-tierry/`

- **`create_eleve_folder_structure(classe, nom_complet)`** ⭐
  - Crée automatiquement :
    - Le dossier `media/inscriptions/{classe}/photos/` (s'il n'existe pas)
    - Le dossier `media/inscriptions/{classe}/photos/{nom_complet}/` (s'il n'existe pas)
  - Retourne un tuple `(bool, messages_ou_erreur)`
  - Cette fonction est appelée automatiquement lors de la sauvegarde d'un élève

- **`delete_eleve_folder(classe, nom_complet)`**
  - Supprime le dossier de l'élève quand celui-ci est supprimé de la base de données

- **`check_eleve_folder_exists(classe, nom_complet)`**
  - Vérifie si un dossier d'élève existe

### 2. `Inscriptions/models.py` (MODIFIÉ)
Modifications du modèle `Eleve` :

#### Ajout de l'import
```python
from .utils import create_eleve_folder_structure, delete_eleve_folder
```

#### Modification de la méthode `save()`
```python
def save(self, *args, **kwargs):
    is_new = self.pk is None
    super().save(*args, **kwargs)

    if self.date_inscription and not self.matricule:
        self.matricule = self.generate_matricule()
        super().save(update_fields=["matricule"])
    
    # ✨ Créer la structure de dossiers pour l'élève
    create_eleve_folder_structure(self.classe, self.nom_complet)
```

#### Ajout de la méthode `delete()`
```python
def delete(self, *args, **kwargs):
    """Supprime l'élève et son dossier"""
    delete_eleve_folder(self.classe, self.nom_complet)
    super().delete(*args, **kwargs)
```

## Fonctionnement automatique

### Lors de l'inscription d'un élève :
1. L'utilisateur remplit le formulaire d'inscription
2. La méthode `save()` du modèle `Eleve` est appelée
3. Automatiquement :
   - Le dossier de la classe est créé : `media/inscriptions/{classe}/photos/`
   - Le dossier de l'élève est créé : `media/inscriptions/{classe}/photos/{nom_complet}/`
   - Les photos et documents de l'élève y sont sauvegardés via les chemins définis dans :
     - `get_image()` pour les photos
     - `document_upload_path()` pour les documents

### Lors de la suppression d'un élève :
1. La méthode `delete()` du modèle est appelée
2. Le dossier de l'élève est supprimé
3. L'élève est supprimé de la base de données

## Exemple d'utilisation en Python

```python
from Inscriptions.models import Eleve
from Inscriptions.utils import check_eleve_folder_exists

# Créer un élève - les dossiers seront créés automatiquement
eleve = Eleve.objects.create(
    nom="LANKOANDE",
    prenom="tierry",
    date_naissance="2010-01-15",
    classe="6EME",
    adresse="Ouagadougou, Burkina Faso"
)

# Vérifier que le dossier a été créé
if check_eleve_folder_exists("6EME", "LANKOANDE-tierry"):
    print("✓ Dossier créé avec succès!")
    
# Ajouter une photo - elle sera automatiquement sauvegardée dans :
# media/inscriptions/6EME/photos/LANKOANDE-tierry/
with open("photo.jpg", "rb") as f:
    eleve.photo = f
    eleve.save()
```

## Avantages du système

✅ **Automatique** : Les dossiers sont créés sans intervention manuelle
✅ **Organisé** : Structure claire par classe et élève
✅ **Nettoyage** : Les dossiers sont supprimés quand l'élève est supprimé
✅ **Sécurisé** : Utilise `pathlib.Path` pour la gestion des chemins
✅ **Évolutif** : Facile à adapter ou étendre
✅ **Intégré** : Fonctionne parfaitement avec Django et les champs FileField/ImageField

## Points techniques

- Les dossiers sont créés avec `Path.mkdir(parents=True, exist_ok=True)`
  - `parents=True` : crée tous les dossiers parents si nécessaire
  - `exist_ok=True` : n'échoue pas si le dossier existe déjà
  
- Les opérations utilisant `shutil.rmtree()` pour supprimer les dossiers et leurs contenus

- Les chemins utilisent `settings.MEDIA_ROOT` pour être indépendants du système d'exploitation
