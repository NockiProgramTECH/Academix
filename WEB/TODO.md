
# TODO - Ajout des modèles Parent/Tuteur et Photo

## Plan Steps:
- [x] Ajouter le modèle Tuteur (parents + personne à prévenir)
- [x] Ajouter le champ photo dans le modèle Eleve
- [x] Créer les formulaires (TuteurForm, mise à jour EleveForm)
- [x] Mettre à jour les views pour gérer les données des parents
- [x] Mettre à jour l'admin Django
- [x] Créer et appliquer les migrations
- [x] Mettre à jour le template d'inscription avec les nouveaux champs

## Status: Terminé

## Résumé des changements:

### 1. Inscriptions/models.py:
- Ajout de la fonction `photo_upload_path()` pour le chemin de la photo
- Création du modèle `Tuteur` avec:
  - Informations du père (nom, prénom, profession, téléphone, adresse)
  - Informations de la mère (nom, prénom, profession, téléphone, adresse)
  - Personne à prévenir (nom, prénom, téléphone, lien avec l'élève)
- Ajout du champ `photo` dans Eleve (ImageField, optionnel)
- Ajout de la relation `tuteur` (OneToOneField) dans Eleve

### 2. Inscriptions/forms.py:
- Création de `TuteurForm` pour les informations des parents
- Mise à jour de `EleveForm` pour inclure le champ photo

### 3. Inscriptions/views.py:
- Mise à jour de `traiter_inscription_formdata()` pour:
  - Valider la photo (format: jpg, jpeg, png, webp; taille max: 2MB)
  - Gérer l'upload de la photo
  - Créer le Tuteur si des données sont présentes

### 4. Inscriptions/admin.py:
- Enregistrement du modèle Tuteur
- Mise à jour de EleveAdmin pour afficher photo et tuteur

### 5. Migrations:
- `0003_tuteur_eleve_photo_eleve_tuteur.py` créée et appliquée avec succès

### 6. templates/inscriptions/inscription_form.html:
- Ajout du champ photo d'identité (optionnel)
- Ajout de la section "Informations des parents/tuteurs":
  - Père: nom, prénom, profession, téléphone, adresse
  - Mère: nom, prénom, profession, téléphone, adresse
  - Personne à prévenir: nom, prénom, téléphone, lien
- Validation JavaScript pour la photo
- Mise en page responsive avec grille

