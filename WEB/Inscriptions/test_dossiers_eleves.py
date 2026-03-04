"""
Tests et exemples d'utilisation du système de gestion des dossiers d'élèves
Exécuter ces tests avec: python manage.py shell
"""

# ============================================
# EXEMPLE 1: Créer un élève et son dossier
# ============================================

from Inscriptions.models import Eleve
from Inscriptions.utils import check_eleve_folder_exists, get_eleve_directory
from django.core.files.base import ContentFile
import os

# Créer un nouvel élève
nouvel_eleve = Eleve.objects.create(
    nom="LANKOANDE",
    prenom="Eben Ezer",
    date_naissance="2009-05-20",
    classe="5EME",
    adresse="Ouagadougou, Burkina Faso"
)

print(f"✓ Élève créé: {nouvel_eleve.nom_complet}")
print(f"  Matricule: {nouvel_eleve.matricule}")
print(f"  Classe: {nouvel_eleve.classe}")

# Vérifier que le dossier a été créé
dossier_existe = check_eleve_folder_exists("5EME", "LANKOANDE-Eben Ezer")
if dossier_existe:
    print(f"✓ Dossier créé avec succès!")
    chemin_dossier = get_eleve_directory("5EME", "LANKOANDE-Eben Ezer")
    print(f"  Chemin: {chemin_dossier}")
else:
    print("✗ Erreur: le dossier n'a pas été créé")


# ============================================
# EXEMPLE 2: Ajouter une photo à un élève
# ============================================

from django.core.files.base import ContentFile

eleve = Eleve.objects.get(nom="LANKOANDE", prenom="Eben Ezer")

# Simuler l'ajout d'une photo
# (En production, ce serait un fichier uploadé)
contenu_photo = b"données binaires de la photo"
eleve.photo.save('photo.jpg', ContentFile(contenu_photo))

print(f"✓ Photo sauvegardée pour {eleve.nom_complet}")
print(f"  Chemin: {eleve.photo.path}")


# ============================================
# EXEMPLE 3: Lister tous les élèves d'une classe
# ============================================

from Inscriptions.models import Eleve

eleves_5eme = Eleve.objects.filter(classe="5EME")

print(f"\n5 élèves en 5ème:")
for eleve in eleves_5eme:
    dossier_existe = check_eleve_folder_exists(eleve.classe, eleve.nom_complet)
    statut = "✓" if dossier_existe else "✗"
    print(f"  {statut} {eleve.nom_complet} - Matricule: {eleve.matricule}")


# ============================================
# EXEMPLE 4: Vérifier la structure des dossiers
# ============================================

import os
from pathlib import Path
from django.conf import settings

media_path = Path(settings.MEDIA_ROOT) / 'inscriptions'

if media_path.exists():
    print(f"\nStructure des dossiers d'inscription:")
    for classe_dir in sorted(media_path.iterdir()):
        if classe_dir.is_dir():
            classe = classe_dir.name
            photos_dir = classe_dir / 'photos'
            if photos_dir.exists():
                eleves = [d.name for d in photos_dir.iterdir() if d.is_dir()]
                print(f"\n  {classe}/ (photos: {len(eleves)})")
                for eleve_nom in sorted(eleves):
                    print(f"    └── {eleve_nom}/")
else:
    print("✗ Le dossier inscriptions n'existe pas encore")


# ============================================
# EXEMPLE 5: Supprimer un élève et son dossier
# ============================================

from Inscriptions.models import Eleve

eleve_a_supprimer = Eleve.objects.get(nom="LANKOANDE", prenom="Eben Ezer")
dossier = get_eleve_directory(eleve_a_supprimer.classe, eleve_a_supprimer.nom_complet)

print(f"\nSuppression de {eleve_a_supprimer.nom_complet}...")

if check_eleve_folder_exists(eleve_a_supprimer.classe, eleve_a_supprimer.nom_complet):
    print(f"  Dossier trouvé: {dossier}")

# Supprimer l'élève (le dossier sera supprimé automatiquement)
eleve_a_supprimer.delete()
print(f"✓ Élève supprimé")

# Vérifier que le dossier a été supprimé
if not check_eleve_folder_exists(eleve_a_supprimer.classe, eleve_a_supprimer.nom_complet):
    print(f"✓ Dossier supprimé automatiquement")
else:
    print(f"✗ Erreur: le dossier existe toujours")


# ============================================
# EXEMPLE 6: Créer plusieurs élèves d'une classe
# ============================================

eleves_data = [
    {"nom": "KONE", "prenom": "Moussa", "classe": "6EME"},
    {"nom": "SANE", "prenom": "Fatou", "classe": "6EME"},
    {"nom": "DIALLO", "prenom": "Ibrahim", "classe": "6EME"},
]

print(f"\nCréation de {len(eleves_data)} élèves en 6ème...")

for data in eleves_data:
    try:
        eleve = Eleve.objects.create(
            nom=data['nom'],
            prenom=data['prenom'],
            date_naissance="2012-01-01",  # Date par défaut
            classe=data['classe'],
            adresse="Ouagadougou"
        )
        print(f"  ✓ {eleve.nom_complet} - Dossier: {data['classe']}/photos/{eleve.nom_complet}/")
    except Exception as e:
        print(f"  ✗ Erreur pour {data['nom']} {data['prenom']}: {str(e)}")


# ============================================
# EXEMPLE 7: Statistiques sur les dossiers
# ============================================

from pathlib import Path
from django.conf import settings
import os

def compter_tous_les_dossiers():
    media_path = Path(settings.MEDIA_ROOT) / 'inscriptions'
    
    if not media_path.exists():
        return 0, 0
    
    total_eleves = 0
    total_classes = 0
    
    for classe_dir in media_path.iterdir():
        if classe_dir.is_dir():
            photos_dir = classe_dir / 'photos'
            if photos_dir.exists():
                total_classes += 1
                eleves = [d for d in photos_dir.iterdir() if d.is_dir()]
                total_eleves += len(eleves)
    
    return total_classes, total_eleves

classes, eleves = compter_tous_les_dossiers()
print(f"\n📊 Statistiques:")
print(f"  Classes avec dossiers: {classes}")
print(f"  Dossiers d'élèves: {eleves}")
