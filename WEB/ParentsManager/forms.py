from django import forms
from django.contrib.auth.models import User
from Inscriptions.models import Eleve

class ParentSignUpForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True, label="Prénom")
    last_name = forms.CharField(max_length=100, required=True, label="Nom")
    email = forms.EmailField(required=True, label="Email")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Mot de passe")
    
    matricule_enfant = forms.CharField(
        max_length=20, 
        required=True, 
        label="Matricule de votre enfant",
        help_text="Retrouvez-le sur sa carte scolaire ou ses anciens bulletins (ex: 2026BT00103)."
    )
    phone = forms.CharField(max_length=20, required=True, label="Téléphone")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False, label="Adresse complète")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        
    def clean_matricule_enfant(self):
        matricule = self.cleaned_data.get('matricule_enfant')
        try:
            # Recherche stricte du matricule dans la base Django Inscriptions
            eleve = Eleve.objects.get(matricule=matricule)
        except Eleve.DoesNotExist:
            raise forms.ValidationError("Matricule invalide. Aucun élève enregistré avec ce matricule.")
        return eleve
