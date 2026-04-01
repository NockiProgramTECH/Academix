from django.db import models
from django.contrib.auth.models import User

# =========================================================================
# MODÈLES EXTERNES (LEGACY) GÉRÉS PAR L'APPLICATION DESKTOP
# =========================================================================

class Classe(models.Model):
    nom_classe = models.CharField(max_length=20, unique=True, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'classes'
        verbose_name = "Classe"
        verbose_name_plural = "Classes"

    def __str__(self):
        return self.nom_classe or str(self.id)


class Matiere(models.Model):
    id_matiere = models.AutoField(primary_key=True)
    nom_matiere = models.CharField(max_length=100, unique=True, null=True, blank=True)
    coefficient = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'matiere'

    def __str__(self):
        return self.nom_matiere or f"Matiere {self.id_matiere}"


class Evaluation(models.Model):
    titre = models.CharField(max_length=100)
    type_eval = models.CharField(max_length=15, default='Devoir')
    trimestre = models.IntegerField()
    date_eval = models.DateField()
    matiere = models.ForeignKey(Matiere, on_delete=models.DO_NOTHING, db_column='matiere_id')
    classe = models.ForeignKey(Classe, on_delete=models.DO_NOTHING, db_column='classe_id')
    annee_scolaire = models.CharField(max_length=20)
    verrouille = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'evaluations'

    def __str__(self):
        return self.titre


class Note(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.DO_NOTHING, db_column='evaluation_id')
    eleve = models.ForeignKey('Inscriptions.Eleve', on_delete=models.DO_NOTHING, db_column='eleve_id', related_name='desktop_notes')
    note = models.DecimalField(max_digits=5, decimal_places=2)
    appreciation = models.CharField(max_length=255, null=True, blank=True)
    saisi_par = models.CharField(max_length=50, default='SECRETARIAT')
    date_saisie = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'notes'
        unique_together = (('evaluation', 'eleve'),)


class Absence(models.Model):
    eleve = models.ForeignKey('Inscriptions.Eleve', on_delete=models.DO_NOTHING, db_column='eleve_id', related_name='desktop_absences')
    date_absence = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    statut = models.CharField(max_length=50, default='NON_JUSTIFIEE')
    motif = models.CharField(max_length=255, null=True, blank=True)
    trimestre = models.IntegerField(default=1)
    annee_scolaire = models.CharField(max_length=20)
    saisie_par = models.CharField(max_length=50, default='SECRETARIAT')
    date_saisie = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'absences'


# =========================================================================
# MODÈLES INTERNES (WEB) POUR LE PORTAIL PARENT
# =========================================================================

class ParentModel(models.Model):
    """
    Modèle du profil parent, lié au User Django.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    phone = models.CharField(max_length=100)
    address = models.TextField()
    profession = models.CharField(max_length=100, blank=True, null=True)
    
    # La relation avec l'élève réel dont les clés primaires (id UUID) lient le tout.
    children = models.ManyToManyField('Inscriptions.Eleve', related_name='parents')
    role = models.CharField(max_length=20, default='parent')

    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"
        ordering = ['user__first_name']
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def number_of_children(self):
        return self.children.count()

    @property
    def children_list(self):
        return self.children.all()
    
    def get_children_performance(self, trimestre=1, annee=None):
        """
        Génère un résumé des performances pour chaque enfant associé au parent.
        """
        performance_data = []
        for enfant in self.children_list:
            performance_data.append({
                'eleve': enfant,
                'moyenne': enfant.get_moyenne_generale(trimestre, annee),
                'absences': enfant.get_total_absences(trimestre, annee),
            })
        return performance_data
