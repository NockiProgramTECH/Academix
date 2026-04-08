import time

from django.db import models
import uuid

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


class Eleve(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matricule = models.CharField(max_length=50, unique=True, blank=True)

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()

    CLASS_CHOICES = [
        ('6EME', '6ème'),
        ('5EME', '5ème'),
        ('4EME', '4ème'),
        ('3EME', '3ème'),
        ('2nd', '2nde'),
    ]
    classe = models.CharField(max_length=10, choices=CLASS_CHOICES)
    classe_reelle = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Classe Affectée (ex: 6ème A)"
    )
    adresse = models.TextField()

    # ── CORRECTIF MYSQL ──────────────────────────────────────────────────────
    # max_length=100 (défaut Django) → MySQL VARCHAR(100).
    # Une URL Cloudinary dépasse souvent 150 caractères.
    # Avec STRICT_TRANS_TABLES actif, MySQL lève une erreur "Data too long"
    # → Erreur 500. On passe à 500 pour absorber n'importe quelle URL Cloudinary.
    # ─────────────────────────────────────────────────────────────────────────
    photo = models.ImageField(
        upload_to=photo_upload_path,
        blank=True,
        null=True,
        max_length=500,          # ← CORRECTIF : était implicitement 100
        verbose_name="Photo d'identité"
    )

    tuteur = models.OneToOneField(
        Tuteur,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='eleve'
    )

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
        # ── CORRECTIF : on empêche la re-génération du matricule ─────────────
        # Avant le correctif, chaque appel à save() re-testait `not self.matricule`.
        # Si save() était appelé deux fois de suite (ex: ajout photo), le matricule
        # existait déjà → pas de régénération, mais la double sauvegarde pouvait
        # déclencher des effets de bord sur les upload_to des fichiers liés.
        # On isole clairement la logique de première création.
        # ────────────────────────────────────────────────────────────────────
        is_new = self._state.adding  # True uniquement lors du premier INSERT
        super().save(*args, **kwargs)

        if is_new and not self.matricule:
            self.matricule = self.generate_matricule()
            # update_fields évite de re-déclencher toute la logique save()
            # et empêche un re-upload accidentel des fichiers déjà stockés.
            super().save(update_fields=["matricule"])

    def generate_matricule(self):
        date_inscription = self.date_inscription
        year = date_inscription.year
        month = date_inscription.month
        last_three = str(self.id).replace("-", "")[-3:]
        digit = int(time.time() % 100000)
        return f"{year}BT{last_three}{month:02d}{digit}"

    def get_moyenne_generale(self, trimestre=1, annee=None):
        try:
            from ParentsManager.models import Note
            notes_qs = Note.objects.filter(eleve=self, evaluation__trimestre=trimestre)
            if annee:
                notes_qs = notes_qs.filter(evaluation__annee_scolaire=annee)
            if not notes_qs.exists():
                return 0.0
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

    @property
    def nom_complet(self):
        return f"{self.nom}-{self.prenom}"

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


class DocumentEleve(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='documents')

    # ── CORRECTIF MYSQL ──────────────────────────────────────────────────────
    # Même raison que pour Eleve.photo : les URLs Cloudinary dépassent VARCHAR(100).
    # Les PDF et DOCX sont stockés via resource_type='raw' dans Cloudinary,
    # ce qui génère des URLs de la forme :
    #   https://res.cloudinary.com/<cloud>/raw/upload/v<ts>/<path>/<filename>
    # Ces URLs peuvent facilement atteindre 180–220 caractères.
    # ─────────────────────────────────────────────────────────────────────────
    acte_naissance = models.FileField(upload_to=acte_upload_path, max_length=500)
    last_bulletin = models.FileField(upload_to=bulletin_upload_path, max_length=500)
    diplome = models.FileField(upload_to=diplome_upload_path, max_length=500)
    est_valide = models.BooleanField(default=False)

    def __str__(self):
        return f"Documents de {self.eleve.nom_complet}"