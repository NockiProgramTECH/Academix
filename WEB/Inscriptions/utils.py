import os
import uuid

def _document_filename(prefix, instance, filename):
    """Génère un nom de fichier propre sans toucher au disque."""
    extension = filename.split('.')[-1].lower()
    # On utilise l'ID de l'élève pour que le nom soit unique
    unique_id = getattr(instance.eleve, 'id', uuid.uuid4())
    return f"{prefix}{unique_id}.{extension}"


def _photo_filename(prefix, instance, filename):
    """
    Variante pour la photo : ici `instance` EST l'Eleve lui-même,
    donc pas d'attribut `.eleve`.
    """
    extension = filename.split('.')[-1].lower()
    unique_id = getattr(instance, 'id', uuid.uuid4())
    return f"{prefix}{unique_id}.{extension}"


def acte_upload_path(instance, filename):
    """Chemin virtuel pour l'acte de naissance."""
    classe = str(instance.eleve.classe).replace(" ", "_")
    eleve_id = str(instance.eleve.id)
    name = _document_filename('acte_naissance_', instance, filename)
    return f"inscriptions/{classe}/{eleve_id}/documents/{name}"


def bulletin_upload_path(instance, filename):
    """Chemin virtuel pour le bulletin."""
    classe = str(instance.eleve.classe).replace(" ", "_")
    eleve_id = str(instance.eleve.id)
    name = _document_filename('bulletin_', instance, filename)
    return f"inscriptions/{classe}/{eleve_id}/documents/{name}"


def diplome_upload_path(instance, filename):
    """Chemin virtuel pour le diplôme."""
    classe = str(instance.eleve.classe).replace(" ", "_")
    eleve_id = str(instance.eleve.id)
    name = _document_filename('diplome_', instance, filename)
    return f"inscriptions/{classe}/{eleve_id}/documents/{name}"


def photo_upload_path(instance, filename):
    """
    Chemin virtuel pour la photo d'identité.
    ATTENTION : ici `instance` est directement un Eleve (pas un DocumentEleve),
    donc on utilise `_photo_filename` qui lit `instance.id` au lieu de `instance.eleve.id`.
    """
    classe = str(instance.classe).replace(" ", "_")
    eleve_id = str(instance.id)
    name = _photo_filename('photo_identite_', instance, filename)
    return f"inscriptions/{classe}/{eleve_id}/photos/{name}"