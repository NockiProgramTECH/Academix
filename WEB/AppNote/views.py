from django.shortcuts import render,redirect


from .models import Note,Evaluation,Matiere
from Inscriptions.models import Eleve

# Create your views here.
# Vue simplifiée pour la saisie de masse
def saisie_notes_vue(request, evaluation_id):
    evaluation = Evaluation.objects.get(id=evaluation_id)
    eleves = Eleve.objects.filter(classe=evaluation.classe, statut='VALIDE')
    
    if request.method == 'POST':
        for eleve in eleves:
            note_valeur = request.POST.get(f'note_{eleve.id}')
            if note_valeur:
                Note.objects.update_or_create(
                    eleve=eleve, 
                    evaluation=evaluation, 
                    defaults={'valeur': note_valeur}
                )
        return redirect('tableau_bord_prof')
        
    return render(request, 'saisie_notes.html', {'eleves': eleves, 'evaluation': evaluation})