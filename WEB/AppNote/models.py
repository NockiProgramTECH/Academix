from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


from Inscriptions.models import Eleve
class Matiere(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    coefficient = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.nom} (Coeff: {self.coefficient})"

class Evaluation(models.Model):
    TYPE_EVAL = [
        ('DEVOIR', 'Devoir simple'),
        ('COMPOSITION', 'Composition / Examen'),
    ]
    TRIMESTRE = [(1, '1er Trimestre'), (2, '2ème Trimestre'), (3, '3ème Trimestre')]
    
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    classe = models.CharField(max_length=10, choices=Eleve.CLASS_CHOICES)
    type_eval = models.CharField(max_length=20, choices=TYPE_EVAL)
    trimestre = models.IntegerField(choices=TRIMESTRE)
    date_eval = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.matiere.nom} - {self.get_trimestre_display()} ({self.classe})"

class Note(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='notes')
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    valeur = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    commentaire = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('eleve', 'evaluation') # Un élève ne peut avoir qu'une note par éval