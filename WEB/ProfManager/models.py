"""
models.py  ──  Academix · Modèles Django
Corrigé pour correspondre EXACTEMENT aux tables SQL réelles (dump 2026-03-16).

Corrections majeures :
  • db_table en minuscules partout  (enseignement, professeur, matiere…)
  • Eleve.classe_reelle → vraie classe affectée (ex : '4EME A')
  • Note.eleve_id → varchar(60) / UUID  (pas IntegerField)
  • ScolariteAffectation → table de référence pour lier élève ↔ classe
  • verrouille → présent dans evaluations (tinyint DEFAULT 0) -> BooleanField OK
  • Tous les champs nullable alignés sur le DDL réel
"""

from django.db import models
from Inscriptions.models import Eleve   # table inscriptions_eleve


# ─── CLASSES ──────────────────────────────────────────────────────────────────
# DDL: id INT AUTO_INCREMENT PK, nom_classe VARCHAR(20) UNIQUE NULL

class Classes(models.Model):
    id         = models.AutoField(primary_key=True, db_column='id')
    nom_classe = models.CharField(max_length=20, unique=True, null=True,
                                  db_column='nom_classe')

    class Meta:
        managed  = False
        db_table = 'classes'
        ordering = ['nom_classe']

    def __str__(self):
        return self.nom_classe or ''


# ─── SCOLARITE_AFFECTATION ────────────────────────────────────────────────────
# DDL: id, eleve_id varchar(60), classe_id int NULL, annee_scolaire varchar(20)
# REFERENCE pour savoir dans quelle classe est un élève (pas inscriptions_eleve.classe)

class ScolariteAffectation(models.Model):
    id             = models.AutoField(primary_key=True, db_column='id')
    eleve          = models.ForeignKey(
        Eleve, on_delete=models.CASCADE,
        db_column='eleve_id', related_name='affectations'
    )
    classe         = models.ForeignKey(
        Classes, on_delete=models.CASCADE,
        db_column='classe_id', related_name='affectations', null=True
    )
    annee_scolaire = models.CharField(max_length=20, null=True,
                                      db_column='annee_scolaire')

    class Meta:
        managed  = False
        db_table = 'scolarite_affectation'

    def __str__(self):
        return f"{self.eleve} -> {self.classe} ({self.annee_scolaire})"


# ─── MATIERE ──────────────────────────────────────────────────────────────────
# DDL: id_matiere PK, nom_matiere VARCHAR(100) UNIQUE NULL, coefficient INT NULL

class Matiere(models.Model):
    id_matiere  = models.AutoField(primary_key=True, db_column='id_matiere')
    nom_matiere = models.CharField(max_length=100, unique=True, null=True,
                                   db_column='nom_matiere')
    coefficient = models.IntegerField(null=True, db_column='coefficient')

    class Meta:
        managed  = False
        db_table = 'matiere'
        ordering = ['nom_matiere']

    def __str__(self):
        return f"{self.nom_matiere} (coeff. {self.coefficient})"


# ─── PROFESSEUR ───────────────────────────────────────────────────────────────
# DDL: id_professeur PK, matricule UNIQUE NULL, nom NULL, prenom NULL, ...

class Professeur(models.Model):
    id_professeur = models.AutoField(primary_key=True, db_column='id_professeur')
    matricule     = models.CharField(max_length=20, unique=True, null=True,
                                     db_column='matricule')
    nom           = models.CharField(max_length=50, null=True, db_column='nom')
    prenom        = models.CharField(max_length=50, null=True, db_column='prenom')
    telephone     = models.CharField(max_length=20, null=True, blank=True,
                                     db_column='telephone')
    specialite    = models.CharField(max_length=100, null=True, blank=True,
                                     db_column='specialite')
    statut        = models.CharField(max_length=20, null=True, blank=True,
                                     db_column='statut')
    email         = models.CharField(max_length=100, null=True, blank=True,
                                     db_column='email')
    password      = models.CharField(max_length=255, null=True, blank=True,
                                     db_column='password')

    class Meta:
        managed  = False
        db_table = 'professeur'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"


# ─── ENSEIGNEMENT ─────────────────────────────────────────────────────────────
# DDL: id_enseignement PK, id_professeur NULL, id_matiere NULL, id_classe NULL

class Enseignement(models.Model):
    id_enseignement = models.AutoField(primary_key=True,
                                       db_column='id_enseignement')
    professeur      = models.ForeignKey(
        Professeur, on_delete=models.CASCADE,
        db_column='id_professeur', related_name='enseignements', null=True
    )
    matiere         = models.ForeignKey(
        Matiere, on_delete=models.CASCADE,
        db_column='id_matiere', related_name='enseignements', null=True
    )
    classe          = models.ForeignKey(
        Classes, on_delete=models.CASCADE,
        db_column='id_classe', related_name='enseignements', null=True
    )

    class Meta:
        managed  = False
        db_table = 'enseignement'

    def __str__(self):
        return f"{self.professeur} . {self.matiere} . {self.classe}"


# ─── CLASSE_MATIERE ───────────────────────────────────────────────────────────
# DDL: PK composite (classe_id, matiere_id)

class ClasseMatiere(models.Model):
    id      = models.AutoField(primary_key=True)   # fictif pour Django
    classe  = models.ForeignKey(
        Classes, on_delete=models.CASCADE,
        db_column='classe_id', related_name='matieres_liees'
    )
    matiere = models.ForeignKey(
        Matiere, on_delete=models.CASCADE,
        db_column='matiere_id', related_name='classes_liees'
    )

    class Meta:
        managed         = False
        db_table        = 'classe_matiere'
        unique_together = [('classe', 'matiere')]

    def __str__(self):
        return f"{self.classe} <-> {self.matiere}"


# ─── EVALUATIONS ──────────────────────────────────────────────────────────────
# DDL: id, titre, type_eval ENUM, trimestre, date_eval, matiere_id,
#       classe_id, annee_scolaire, verrouille TINYINT(1) NOT NULL DEFAULT 0
# CONFIRMED: colonne verrouille EXISTS dans le dump SQL reel

class Evaluation(models.Model):
    TYPE_CHOICES = [
        ('Interrogation', 'Interrogation'),
        ('Devoir',        'Devoir'),
        ('Examen',        'Examen'),
    ]

    id             = models.AutoField(primary_key=True, db_column='id')
    titre          = models.CharField(max_length=100, db_column='titre')
    type_eval      = models.CharField(max_length=15, choices=TYPE_CHOICES,
                                      default='Devoir', db_column='type_eval')
    trimestre      = models.IntegerField(db_column='trimestre')
    date_eval      = models.DateField(db_column='date_eval')
    matiere        = models.ForeignKey(
        Matiere, on_delete=models.PROTECT,
        db_column='matiere_id', related_name='evaluations'
    )
    classe         = models.ForeignKey(
        Classes, on_delete=models.PROTECT,
        db_column='classe_id', related_name='evaluations'
    )
    annee_scolaire = models.CharField(max_length=20, db_column='annee_scolaire')
    verrouille     = models.BooleanField(default=False, db_column='verrouille')

    class Meta:
        managed  = False
        db_table = 'evaluations'
        ordering = ['date_eval']

    def __str__(self):
        return f"{self.titre} [{self.type_eval}] - {self.classe} T{self.trimestre}"


# ─── NOTES ────────────────────────────────────────────────────────────────────
# DDL: id, evaluation_id INT, eleve_id VARCHAR(60) <- UUID !,
#       note DECIMAL(5,2), appreciation VARCHAR(255) NULL,
#       saisi_par VARCHAR(50) DEFAULT 'SECRETARIAT',
#       date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# UNIQUE: (evaluation_id, eleve_id)

class Note(models.Model):
    id           = models.AutoField(primary_key=True, db_column='id')
    evaluation   = models.ForeignKey(
        Evaluation, on_delete=models.CASCADE,
        db_column='evaluation_id', related_name='notes'
    )
    # eleve_id est VARCHAR(60)/UUID dans la table notes -> to_field='id' (char(32))
    eleve        = models.ForeignKey(
        Eleve, on_delete=models.PROTECT,
        db_column='eleve_id', related_name='notes',
        to_field='id'
    )
    note         = models.DecimalField(max_digits=5, decimal_places=2,
                                       db_column='note')
    appreciation = models.CharField(max_length=255, null=True, blank=True,
                                    db_column='appreciation')
    saisi_par    = models.CharField(max_length=50, default='SECRETARIAT',
                                    null=True, db_column='saisi_par')
    date_saisie  = models.DateTimeField(auto_now_add=True,
                                        db_column='date_saisie')

    class Meta:
        managed         = False
        db_table        = 'notes'
        unique_together = [('evaluation', 'eleve')]
        ordering        = ['evaluation', 'eleve__nom']

    def __str__(self):
        return f"{self.eleve} . {self.evaluation} -> {self.note}"