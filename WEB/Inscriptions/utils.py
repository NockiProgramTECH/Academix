"""
Fonctions utilitaires pour gérer les dossiers et fichiers des inscriptions
"""
import os
from pathlib import Path
from django.conf import settings


def get_classe_photos_directory(classe,id):
    """
    Retourne le chemin du dossier photos pour une classe
    Ex: media/inscriptions/6EME/id/photos/
    """
    return os.path.join(settings.MEDIA_ROOT, 'inscriptions', classe,id,'photos')


def get_eleve_directory(classe, id):
    """
    Retourne le chemin du dossier pour un élève
    Ex: media/inscriptions/6EME/id/photos/id/
    """
    classe_photos_dir = get_classe_photos_directory(classe,id)
    return os.path.join(classe_photos_dir, id)


def create_eleve_folder_structure(classe, nom_complet):
    """
    Crée la structure de dossiers pour un élève
    - Crée le dossier photos de la classe s'il n'existe pas
    - Crée le dossier de l'élève s'il n'existe pas
    """
    try:
        # Créer le dossier photos de la classe
        classe_photos_dir = get_classe_photos_directory(classe,nom_complet)
        Path(classe_photos_dir).mkdir(parents=True, exist_ok=True)
        
        # Créer le dossier pour l'élève
        eleve_dir = get_eleve_directory(classe, nom_complet)
        Path(eleve_dir).mkdir(parents=True, exist_ok=True)
        
        return True, f"Dossiers créés avec succès pour {nom_complet} en classe {classe}"
    except Exception as e:
        return False, f"Erreur lors de la création des dossiers: {str(e)}"


def delete_eleve_folder(classe, nom_complet):
    """
    Supprime le dossier d'un élève
    """
    try:
        eleve_dir = get_eleve_directory(classe, id)
        if os.path.exists(eleve_dir):
            import shutil
            shutil.rmtree(eleve_dir)
        return True, "Dossier de l'élève supprimé avec succès"
    except Exception as e:
        return False, f"Erreur lors de la suppression du dossier: {str(e)}"


def check_eleve_folder_exists(classe,id):
    """
    Vérifie si le dossier d'un élève existe
    """
    eleve_dir = get_eleve_directory(classe,id)
    return os.path.exists(eleve_dir)
