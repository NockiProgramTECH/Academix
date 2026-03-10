# Documentation: Gestion automatique des dossiers d'inscription

## Vue d'ensemble
Ce système crée automatiquement une structure de dossiers pour chaque élève inscrit, organisée par classe.

## Structure créée
```
media/
└── inscriptions/
    ├── 6EME/
    │     ├── id(uiid)/
    |       └── photos/
    |       |__documents/
    |     ├── id(uuid)/
            |_phot_matricule.( en fonction de l'extension autoriser)
    |         |_acte_naissance_matricule{matricule}.( en fonction de l'extension autoriser)  #fichieracte de naissance
    |         |diplome{matricule}.( en fonction de l'extension autoriser)   #fichier de diplome
    |
    |         |bulletin{matricule}.( en fonction de l'extension autoriser)   #fichier de bulletin
    ├── 5EME/
         # meme logique
    

       
     
```

## Fichiers créés/modifiés

### 1. `Inscriptions/utils.py` (NOUVEAU)
Contient les fonctions utilitaires pour manipuler les chemins et mener les opérations de création/suppression.

- **`get_classe_directory(classe)`**
  - Renvoie le répertoire racine d'une classe (sans `photos` ni `documents`).
  - Exemple : `media/inscriptions/6EME`

- **`get_eleve_directory(classe, eleve_id)`**
  - Chemin vers le dossier d'un élève identifié par son UUID.
  - Exemple : `media/inscriptions/6EME/629ba533-dacd-45a2-9057-5e3df497902c`

- **`get_photos_directory(classe, eleve_id)`**
  - Retourne le sous-dossier `photos` à l'intérieur du dossier de l'élève.

- **`get_documents_directory(classe, eleve_id)`**
  - Retourne le sous-dossier `documents` de l'élève.

- **`create_eleve_folder_structure(classe, eleve_id)`** ⭐
  - Crée l'arborescence complète pour un élève (classe, dossier élève, photos, documents).
  - Retourne `(True, message)` ou `(False, erreur)`.
  - Appelée automatiquement dans `Eleve.save()` après l'enregistrement en base.

- **`delete_eleve_folder(classe, eleve_id)`**
  - Supprime entièrement le répertoire de l'élève (utilisé dans `Eleve.delete()`).

- **`check_eleve_folder_exists(classe, eleve_id)`**
  - Vérifie la présence du dossier racine de l'élève.

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
    create_eleve_folder_structure(self.classe, self.id)
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
   - Le dossier de la classe est créé : `media/inscriptions/{classe}` (si nécessaire)
   - Le dossier de l'élève est créé sous son UUID :
     `media/inscriptions/{classe}/{uuid}/`
   - Deux sous‑répertoires sont préparés : `photos/` et `documents/`
   - Les fichiers sont ensuite stockés grâce aux utilitaires :
     - `get_image()` pour les photos
     - `acte_upload_path`/`bulletin_upload_path`/`diplome_upload_path` pour les documents

### Lors de la suppression d'un élève :
1. La méthode `delete()` du modèle est appelée
2. Le dossier de l'élève est supprimé
3. L'élève est supprimé de la base de données

## Exemple d'utilisation en Python

```python
from Inscriptions.models import Eleve
from Inscriptions.utils import check_eleve_folder_exists

# Créer un élève - les dossiers (uuid) seront créés automatiquement
eleve = Eleve.objects.create(
    nom="LANKOANDE",
    prenom="tierry",
    date_naissance="2010-01-15",
    classe="6EME",
    adresse="Ouagadougou, Burkina Faso"
)

# Vérifier que le dossier a été créé
if check_eleve_folder_exists(eleve.classe, eleve.id):
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
