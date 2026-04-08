import time

from django.db import models
import uuid

# models.py
from .utils import (
    acte_upload_path, 
    bulletin_upload_path, 
    diplome_upload_path, 
    photo_upload_path
)


class Tuteur(models.Model):
    """Modèle pour les parents/tuteurs de l'élève"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Père
    pere_nom = models.CharField(max_length=100, blank=True, verbose_name="Nom du père")
    pere_prenom = models.CharField(max_length=100, blank=True, verbose_name="Prénom du père")
    pere_profession = models.CharField(max_length=100, blank=True, verbose_name="Profession du père")
    pere_telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone du père")
    pere_adresse = models.TextField(blank=True, verbose_name="Adresse du père")
    
    # Mère
    mere_nom = models.CharField(max_length=100, blank=True, verbose_name="Nom de la mère")
    mere_prenom = models.CharField(max_length=100, blank=True, verbose_name="Prénom de la mère")
    mere_profession = models.CharField(max_length=100, blank=True, verbose_name="Profession de la mère")
    mere_telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone de la mère")
    mere_adresse = models.TextField(blank=True, verbose_name="Adresse de la mère")
    
    # Personne à prévenir en cas d'urgence
    personne_prevenir_nom = models.CharField(max_length=100, blank=True, verbose_name="Nom")
    personne_prevenir_prenom = models.CharField(max_length=100, blank=True, verbose_name="Prénom")
    personne_prevenir_telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    personne_prevenir_lien = models.CharField(max_length=50, blank=True, verbose_name="Lien avec l'élève")
    
    def __str__(self):
        return f"Tuteur - {self.pere_nom} {self.pere_prenom} / {self.mere_nom} {self.mere_prenom}"


# def get_image(instance, filename):
#     """Upload d'image dans le sous‑répertoire ``photos`` de l'élève."""
#     ext = filename.split(".")[-1]
#     # on conserve le nom d'origine, la structure de dossier suffit
#     return f"inscriptions/{instance.classe}/{instance.id}/photos/{filename}"

class Eleve(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) #l'uid unique n'es pa modfiable
    matricule = models.CharField(max_length=20, unique=True, blank=True)    #le matricule n'es pa modifiable,unique pour un eleve
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    CLASS_CHOICES =[
        ('6EME', '6ème'),
        ('5EME', '5ème'),
        ('4EME', '4ème'),
        ('3EME', '3ème'),
        ('2nd', '2nde'),
    ]
    classe =models.CharField(max_length=10,choices=CLASS_CHOICES)
    classe_reelle = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Classe Affectée (ex: 6ème A)"
    )
    adresse = models.TextField()
    
    # Nouveau: Photo de l'élève (optionnelle)
    photo = models.ImageField(upload_to=photo_upload_path, blank=True, null=True, verbose_name="Photo d'identité")
    
    # Nouveau: Lien vers les parents/tuteurs
    tuteur = models.OneToOneField(Tuteur, on_delete=models.CASCADE, blank=True, null=True, related_name='eleve')

    
    # Statut pour l'app Desktop de la secrétaire
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    date_inscription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"


    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if self.date_inscription and not self.matricule:
            self.matricule = self.generate_matricule()
            super().save(update_fields=["matricule"])

        # Créer la structure de dossiers pour l'élève en utilisant son uuid

    def get_moyenne_generale(self, trimestre=1, annee=None):
        try:
            from ParentsManager.models import Note
            notes_qs = Note.objects.filter(eleve=self, evaluation__trimestre=trimestre)
            if annee:
                notes_qs = notes_qs.filter(evaluation__annee_scolaire=annee)
                
            if not notes_qs.exists(): return 0.0
            
            total_points = 0.0
            total_coefs = 0
            for no in notes_qs:
                coef = no.evaluation.matiere.coefficient or 1
                total_points += float(no.note) * coef
                total_coefs += coef
            return round(total_points / total_coefs, 2) if total_coefs else 0.0
        except Exception:
            return 0.0

    def get_total_absences(self, trimestre=1, annee=None):
        try:
            from ParentsManager.models import Absence
            abs_qs = Absence.objects.filter(eleve=self, trimestre=trimestre)
            if annee:
                abs_qs = abs_qs.filter(annee_scolaire=annee)
                
            non_just = abs_qs.filter(statut='NON_JUSTIFIEE').count()
            just = abs_qs.filter(statut='JUSTIFIEE').count()
            return {'non_justifiees': non_just, 'justifiees': just, 'total': non_just + just}
        except Exception:
            return {'non_justifiees': 0, 'justifiees': 0, 'total': 0}
   

      
    
#creon une fonction qui va se charger de generer le matricule en fonction du date d'inscription et des deux dernier chiffres de l'i

    def generate_matricule(self):
        date_inscription = self.date_inscription
        year = date_inscription.year
        month = date_inscription.month 
        last_two_digits_id = str(self.id).replace("-","")[-3:]
        digit =int (time.time() % 100000)

        return f"{year}BT{last_two_digits_id}{month:02d}{digit}"
    


    @property
    def nom_complet(self):
        return f"{self.nom}-{self.prenom}"

    
    def delete(self, *args, **kwargs):
        """Supprime l'élève et son dossier (uuid utilisé pour localiser)."""
       
        super().delete(*args, **kwargs)


#creation d'une fonction qui va se charger de chager les nom du documents en fonction 


# helpers pour enregistrer les fichiers de l'élève dans le dossier `documents`

def _document_filename(prefix: str, instance, filename: str) -> str:
    """Construit un nom de fichier avec le préfixe et le matricule de l'élève."""
    ext = filename.split('.')[-1]
    matricule = instance.eleve.matricule or ''
    return f"{prefix}{matricule}.{ext}"

class DocumentEleve(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='documents')

    acte_naissance = models.FileField(upload_to='acte_naissance', null=False, blank=False)
    last_bulletin = models.FileField(upload_to='bulletins', null=False, blank=False)
    diplome = models.FileField(upload_to='diplomes', null=False, blank=False)
    est_valide = models.BooleanField(default=False)

    def __str__(self):
        # utile pour l'admin
        return f"Documents de {self.eleve.nom_complet}"
    
