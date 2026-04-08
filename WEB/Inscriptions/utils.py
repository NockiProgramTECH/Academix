import uuid
from typing import Optional


def _safe_ext(filename: str) -> str:
    return filename.split('.')[-1].lower() if filename and '.' in filename else ''


def _document_filename(prefix: str, instance, filename: str) -> str:
    """Construit un nom de fichier sûr pour un document d'élève.

    Priorité: `eleve.matricule` > `eleve.id` > génération UUID.
    """
    extension = _safe_ext(filename)
    eleve = getattr(instance, 'eleve', None)
    identifier: Optional[str] = None

    if eleve is not None:
        matricule = getattr(eleve, 'matricule', None)
        if matricule:
            identifier = str(matricule)
        else:
            eid = getattr(eleve, 'id', None)
            if eid:
                identifier = str(eid)

    if not identifier:
        identifier = str(uuid.uuid4())

    return f"{prefix}{identifier}.{extension}" if extension else f"{prefix}{identifier}"


def _photo_filename(prefix: str, instance, filename: str) -> str:
    """Construit un nom de fichier pour la photo d'un élève.

    `instance` peut être soit un `Eleve` (pour `photo_upload_path`) soit
    un `DocumentEleve` contenant un `.eleve`.
    """
    extension = _safe_ext(filename)
    # si instance est l'élève lui-même
    matricule = getattr(instance, 'matricule', None)
    if matricule:
        identifier = str(matricule)
    else:
        # sinon essayer instance.id puis instance.eleve.id
        iid = getattr(instance, 'id', None)
        if not iid:
            eleve = getattr(instance, 'eleve', None)
            iid = getattr(eleve, 'id', None) if eleve is not None else None
        identifier = str(iid) if iid else str(uuid.uuid4())

    return f"{prefix}{identifier}.{extension}" if extension else f"{prefix}{identifier}"


def _eleve_metadata_from_instance(instance):
    """Retourne (classe, eleve_id) en étant tolérant aux attributs manquants."""
    eleve = getattr(instance, 'eleve', instance)
    classe = getattr(eleve, 'classe', None)
    eleve_id = getattr(eleve, 'id', None)
    classe_str = str(classe).replace(' ', '_') if classe else 'unknown_classe'
    eleve_id_str = str(eleve_id) if eleve_id else str(uuid.uuid4())
    return classe_str, eleve_id_str


def acte_upload_path(instance, filename: str) -> str:
    """Chemin virtuel pour l'acte de naissance (DocumentEleve).

    Si l'instance n'a pas encore d'élève ou d'ID, retourne un chemin `temp/` unique.
    """
    ext = _safe_ext(filename)
    eleve = getattr(instance, 'eleve', None)
    if eleve is None or not getattr(eleve, 'id', None):
        # garder le nom original si possible, mais éviter collisions
        name = f"acte_naissance_{uuid.uuid4()}.{ext}" if ext else f"acte_naissance_{uuid.uuid4()}"
        return f"temp/{name}"

    classe, eleve_id = _eleve_metadata_from_instance(instance)
    name = _document_filename('acte_naissance_', instance, filename)
    return f"inscriptions/{classe}/{eleve_id}/documents/{name}"


def bulletin_upload_path(instance, filename: str) -> str:
    """Chemin virtuel pour le bulletin (DocumentEleve)."""
    ext = _safe_ext(filename)
    eleve = getattr(instance, 'eleve', None)
    if eleve is None or not getattr(eleve, 'id', None):
        name = f"bulletin_{uuid.uuid4()}.{ext}" if ext else f"bulletin_{uuid.uuid4()}"
        return f"temp/{name}"

    classe, eleve_id = _eleve_metadata_from_instance(instance)
    name = _document_filename('bulletin_', instance, filename)
    return f"inscriptions/{classe}/{eleve_id}/documents/{name}"


def diplome_upload_path(instance, filename: str) -> str:
    """Chemin virtuel pour le diplôme (DocumentEleve)."""
    ext = _safe_ext(filename)
    eleve = getattr(instance, 'eleve', None)
    if eleve is None or not getattr(eleve, 'id', None):
        name = f"diplome_{uuid.uuid4()}.{ext}" if ext else f"diplome_{uuid.uuid4()}"
        return f"temp/{name}"

    classe, eleve_id = _eleve_metadata_from_instance(instance)
    name = _document_filename('diplome_', instance, filename)
    return f"inscriptions/{classe}/{eleve_id}/documents/{name}"


def photo_upload_path(instance, filename: str) -> str:
    """Chemin virtuel pour la photo d'identité.

    Ici `instance` est généralement un `Eleve`. Si l'ID n'existe pas encore,
    on retourne un chemin `temp/` unique pour éviter d'échouer.
    """
    ext = _safe_ext(filename)
    # si l'instance est DocumentEleve, get eleve, sinon utiliser instance
    eleve = getattr(instance, 'eleve', instance)
    if not getattr(eleve, 'id', None):
        name = _photo_filename('photo_identite_', instance, filename)
        return f"temp/{name}"

    classe, eleve_id = _eleve_metadata_from_instance(instance)
    name = _photo_filename('photo_identite_', instance, filename)
    return f"inscriptions/{classe}/{eleve_id}/photos/{name}"