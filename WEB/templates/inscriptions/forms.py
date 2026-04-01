from django import forms
from .models import Eleve, DocumentEleve, Tuteur
import uuid

class TuteurForm(forms.ModelForm):
    """Formulaire pour les informations des parents/tuteurs"""
    class Meta:
        model = Tuteur
        fields = [
            # Père
            'pere_nom', 'pere_prenom', 'pere_profession', 'pere_telephone', 'pere_adresse',
            # Mère
            'mere_nom', 'mere_prenom', 'mere_profession', 'mere_telephone', 'mere_adresse',
            # Personne à prévenir
            'personne_prevenir_nom', 'personne_prevenir_prenom', 'personne_prevenir_telephone', 'personne_prevenir_lien'
        ]
        widgets = {
            'pere_adresse': forms.Textarea(attrs={'rows': 2}),
            'mere_adresse': forms.Textarea(attrs={'rows': 2}),
        }

class EleveForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = ['nom', 'prenom', 'date_naissance', 'classe', 'adresse', 'photo']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'adresse': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class DocumentEleveForm(forms.ModelForm):
    class Meta:
        model = DocumentEleve
        fields = ['acte_naissance', 'last_bulletin', 'diplome']

    def clean_acte_naissance(self):
        fichier = self.cleaned_data.get('acte_naissance')
        return self.valider_fichier(fichier)

    def clean_last_bulletin(self):
        fichier = self.cleaned_data.get('last_bulletin')
        return self.valider_fichier(fichier)

    def clean_diplome(self):
        fichier = self.cleaned_data.get('diplome')
        return self.valider_fichier(fichier)

    def valider_fichier(self, fichier):
        if fichier:
            ext = fichier.name.split('.')[-1].lower()
            extensions_autorisees = ['pdf', 'docx']
            if ext not in extensions_autorisees:
                raise forms.ValidationError(f"Format de fichier non autorisé. Formats acceptés : {', '.join(extensions_autorisees)}")
            
            # Limite de taille (ex: 5MB)
            if fichier.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Le fichier ne doit pas dépasser 5MB")
        
        return fichier