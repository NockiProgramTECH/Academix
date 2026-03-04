from django.db import models
import uuid
from .utils import create_eleve_folder_structure, delete_eleve_folder


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


def get_image(instance,filename):
    ext = filename.split(".")[-1]
    return f"inscriptions/{instance.classe}/{instance.id}/photo/{filename}"

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
    photo = models.ImageField(upload_to=get_image, blank=True, null=True, verbose_name="Photo d'identité")
    
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
        
        # Créer la structure de dossiers pour l'élève
        create_eleve_folder_structure(self.classe, self.nom_complet)

      
    
#creon une fonction qui va se charger de generer le matricule en fonction du date d'inscription et des deux dernier chiffres de l'i

    def generate_matricule(self):
        date_inscription = self.date_inscription
        year = date_inscription.year
        month = date_inscription.month
        day = date_inscription.day
        last_two_digits_id = str(self.id).replace("-","")[-2:]

        return f"{year}BT{last_two_digits_id}{month:02d}"
    


    @property
    def nom_complet(self):
        return f"{self.nom}-{self.prenom}"

    
    def delete(self, *args, **kwargs):
        """Supprime l'élève et son dossier"""
        delete_eleve_folder(self.classe, self.nom_complet)
        super().delete(*args, **kwargs)


#creation d'une fonction qui va se charger de chager les nom du documents en fonction 


def document_upload_path(instance,filename):  
    ext =filename.split(".")[-1]
    ext_ath =[".pdf",".docx"]
    return f"inscriptions/{instance.eleve.classe}/{instance.eleve.id}/{filename}"
class DocumentEleve(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='documents')
    TYPE_DOC = [
        ('ACTE', 'Acte de Naissance'),
        ('DIPLOME', 'Dernier Diplôme'),
        ('PHOTO', 'Photo d\'identité'),
    ]
    # type_a = models.CharField(max_length=10, choices=TYPE_DOC)
    acte_naissance = models.FileField(upload_to=document_upload_path,null =False,blank =False)
    last_bulletin =models.FileField(upload_to=document_upload_path,null =False,blank =False)
    diplome =models.FileField(upload_to=document_upload_path,null =False,blank =False)
    est_valide = models.BooleanField(default=False)

    def __file_name__(self):
        return self.fichier.name
    


##########################""Classes pour la partie affectation officielle (Scolarité) - Correspondent à la table Scolarite_Affectation créée par Tkinter

class Classe(models.Model):
    nom_classe = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = 'Classes' # On force Django à utiliser le nom créé par Tkinter

    def __str__(self):
        return self.nom_classe

class Affectation(models.Model):
    # On lie l'élève (ton modèle existant)
    eleve = models.ForeignKey('Eleve', on_delete=models.CASCADE, db_column='eleve_id')
    # On lie la classe
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, db_column='classe_id')
    annee_scolaire = models.CharField(max_length=20)

    class Meta:
        db_table = 'Scolarite_Affectation' # On force Django à utiliser la table Tkinter

    def __str__(self):
        return f"{self.eleve.nom} en {self.classe.nom_classe}"