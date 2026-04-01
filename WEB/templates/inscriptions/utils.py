"""
Fonctions utilitaires pour gérer les dossiers et fichiers des inscriptions
"""
import os
import uuid
from pathlib import Path
from typing import Tuple, Union

from django.conf import settings


# chemins -----------------------------------------------------------------------

def get_classe_directory(classe: str) -> str:
    """Retourne le dossier d'une classe sous MEDIA_ROOT/inscriptions."""
    return os.path.join(settings.MEDIA_ROOT, 'inscriptions', classe)


def get_eleve_directory(classe: str, eleve_id: Union[str, uuid.UUID]) -> str:
    """Dossier racine d'un élève (UUID) dans une classe."""
    return os.path.join(get_classe_directory(classe), str(eleve_id))


def get_photos_directory(classe: str, eleve_id: Union[str, uuid.UUID]) -> str:
    """Sous-dossier `photos` pour un élève."""
    return os.path.join(get_eleve_directory(classe, eleve_id), 'photos')


def get_documents_directory(classe: str, eleve_id: Union[str, uuid.UUID]) -> str:
    """Sous-dossier `documents` pour un élève."""
    return os.path.join(get_eleve_directory(classe, eleve_id), 'documents')


# opérations --------------------------------------------------------------------

def create_eleve_folder_structure(classe: str, eleve_id: Union[str, uuid.UUID]) -> Tuple[bool, str]:
    """Crée l'arborescence de dossiers pour un élève.

    La structure finale ressemble à :

        media/inscriptions/{classe}/{uuid}/
            photos/
            documents/

    Retourne (success, message).
    """
    try:
        # dossier de classe
        classe_dir = get_classe_directory(classe)
        Path(classe_dir).mkdir(parents=True, exist_ok=True)

        # dossier de l'élève
        eleve_dir = get_eleve_directory(classe, eleve_id)
        Path(eleve_dir).mkdir(parents=True, exist_ok=True)

        # sous-dossiers optionnels
        Path(get_photos_directory(classe, eleve_id)).mkdir(parents=True, exist_ok=True)
        Path(get_documents_directory(classe, eleve_id)).mkdir(parents=True, exist_ok=True)

        return True, f"Dossiers créés avec succès pour élève {eleve_id} en classe {classe}"
    except Exception as e:
        return False, f"Erreur lors de la création des dossiers: {e}"


def delete_eleve_folder(classe: str, eleve_id: Union[str, uuid.UUID]) -> Tuple[bool, str]:
    """Supprime le dossier d'un élève et tout son contenu."""
    try:
        eleve_dir = get_eleve_directory(classe, eleve_id)
        if os.path.exists(eleve_dir):
            import shutil

            shutil.rmtree(eleve_dir)
        return True, "Dossier de l'élève supprimé avec succès"
    except Exception as e:
        return False, f"Erreur lors de la suppression du dossier: {e}"


def check_eleve_folder_exists(classe: str, eleve_id: Union[str, uuid.UUID]) -> bool:
    """Vérifie l'existence du dossier racine d'un élève."""
    return os.path.exists(get_eleve_directory(classe, eleve_id))

