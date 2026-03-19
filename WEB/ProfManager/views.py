from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal

from .models import Enseignement, Professeur, Evaluation, Note, ScolariteAffectation
from Inscriptions.models import Eleve


# ──────────────────────────────────────────────────────────────────────────────
def _get_prof_or_redirect(request, matricule):
    if request.session.get('prof_matricule') != matricule:
        return None
    return get_object_or_404(Professeur, matricule=matricule)


def _eleves_de_classe(classe):
    """
    Élèves affectés à une classe via scolarite_affectation.
    inscriptions_eleve.classe = niveau ('4EME'), pas la classe réelle.
    """
    eleve_ids = (
        ScolariteAffectation.objects
        .filter(classe=classe)
        .values_list('eleve_id', flat=True)
    )
    return Eleve.objects.filter(id__in=eleve_ids).order_by('nom', 'prenom')


def _stats_notes(notes_existantes):
    """Calcule min, max, moyenne à partir du dict {eleve_id: Note}."""
    valeurs = [float(n.note) for n in notes_existantes.values()]
    if not valeurs:
        return 0, None, None, None
    return (
        len(valeurs),
        round(max(valeurs), 2),
        round(min(valeurs), 2),
        round(sum(valeurs) / len(valeurs), 2),
    )


# ──────────────────────────────────────────────────────────────────────────────
# LOGIN / LOGOUT
# ──────────────────────────────────────────────────────────────────────────────

def ProfLogin(request):
    if request.method == "POST":
        nom       = request.POST.get("nom", "").strip()
        prenom    = request.POST.get("prenom", "").strip()
        matricule = request.POST.get("matricule", "").strip()
        try:
            professeur = Professeur.objects.get(
                nom=nom, prenom=prenom, matricule=matricule
            )
            request.session['prof_matricule'] = professeur.matricule
            return redirect('profmanager:dashboard', matricule=professeur.matricule)
        except Professeur.DoesNotExist:
            return render(request, 'ProfManager/login.html',
                          {'error': 'Identifiants invalides. Veuillez réessayer.'})
    return render(request, 'ProfManager/login.html')


def ProfLogout(request):
    request.session.flush()
    return redirect('profmanager:login')


# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────

def ProfDashBoard(request, matricule):
    professeur = _get_prof_or_redirect(request, matricule)
    if not professeur:
        return redirect('profmanager:login')

    enseignements = (
        Enseignement.objects
        .filter(professeur=professeur)
        .select_related('matiere', 'classe')
        .order_by('classe__nom_classe', 'matiere__nom_matiere')
    )

    for ens in enseignements:
        ens.eleves = _eleves_de_classe(ens.classe)
        ens.evaluations = (
            Evaluation.objects
            .filter(matiere=ens.matiere, classe=ens.classe)
            .order_by('-date_eval')
        )

    context = {
        'professeur':    professeur,
        'enseignements': enseignements,
    }
    return render(request, 'ProfManager/dashboard.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# CRÉER UNE ÉVALUATION
# ──────────────────────────────────────────────────────────────────────────────

def CreerEvaluation(request, matricule, enseignement_id):
    professeur = _get_prof_or_redirect(request, matricule)
    if not professeur:
        return redirect('profmanager:login')

    enseignement = get_object_or_404(
        Enseignement, pk=enseignement_id, professeur=professeur
    )

    if request.method == "POST":
        titre          = request.POST.get("titre", "").strip()
        type_eval      = request.POST.get("type_eval", "Devoir")
        trimestre      = request.POST.get("trimestre", 1)
        date_eval      = request.POST.get("date_eval")
        annee_scolaire = request.POST.get("annee_scolaire", "").strip()

        if not all([titre, date_eval, annee_scolaire]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
        else:
            evaluation = Evaluation.objects.create(
                titre=titre,
                type_eval=type_eval,
                trimestre=int(trimestre),
                date_eval=date_eval,
                matiere=enseignement.matiere,
                classe=enseignement.classe,
                annee_scolaire=annee_scolaire,
                verrouille=False,
            )
            messages.success(request, f"Evaluation '{titre}' creee.")
            return redirect('profmanager:saisir_notes',
                            matricule=matricule,
                            evaluation_id=evaluation.pk)

    context = {
        'professeur':   professeur,
        'enseignement': enseignement,
        'today':        timezone.now().date().isoformat(),
        'type_choices': Evaluation.TYPE_CHOICES,
    }
    return render(request, 'ProfManager/creer_evaluation.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# SAISIR / MODIFIER / VOIR LES NOTES
# ──────────────────────────────────────────────────────────────────────────────

def SaisirNotes(request, matricule, evaluation_id):
    professeur = _get_prof_or_redirect(request, matricule)
    if not professeur:
        return redirect('profmanager:login')

    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)

    get_object_or_404(
        Enseignement,
        professeur=professeur,
        matiere=evaluation.matiere,
        classe=evaluation.classe,
    )

    eleves = _eleves_de_classe(evaluation.classe)

    # Notes existantes {eleve_id: Note}
    notes_existantes = {
        n.eleve_id: n
        for n in Note.objects.filter(evaluation=evaluation)
    }

    saisi_par = f"Professeur-{professeur.nom}"

    # ── Traitement POST (sauvegarde / modification) ──────────────────────────
    if request.method == "POST" and not evaluation.verrouille:
        saved  = 0
        errors = []

        for eleve in eleves:
            value = request.POST.get(f"note_{eleve.pk}", "").strip()
            if value == "":
                continue
            try:
                note_val = float(value.replace(",", "."))
                if not (0 <= note_val <= 20):
                    raise ValueError
            except ValueError:
                errors.append(
                    f"{eleve.nom} {eleve.prenom} : valeur invalide '{value}'"
                )
                continue

            if eleve.pk in notes_existantes:
                # MODIFICATION de la note existante
                n           = notes_existantes[eleve.pk]
                n.note      = Decimal(str(note_val))
                n.saisi_par = saisi_par
                n.save(update_fields=['note', 'saisi_par'])
            else:
                # CRÉATION
                Note.objects.create(
                    evaluation=evaluation,
                    eleve=eleve,
                    note=Decimal(str(note_val)),
                    saisi_par=saisi_par,
                )
            saved += 1

        for err in errors:
            messages.error(request, err)
        if saved:
            messages.success(
                request,
                f"{saved} note(s) sauvegardee(s) / modifiee(s) par {saisi_par}."
            )

        # Recharger après sauvegarde
        notes_existantes = {
            n.eleve_id: n
            for n in Note.objects.filter(evaluation=evaluation)
        }

    # ── Préparation du contexte ───────────────────────────────────────────────
    eleves_notes = [
        {'eleve': eleve, 'note': notes_existantes.get(eleve.pk)}
        for eleve in eleves
    ]

    nb_saisies, note_max, note_min, note_moy = _stats_notes(notes_existantes)

    context = {
        'professeur':   professeur,
        'evaluation':   evaluation,
        'eleves_notes': eleves_notes,
        'saisi_par':    saisi_par,
        'nb_saisies':   nb_saisies,
        'note_max':     note_max,
        'note_min':     note_min,
        'note_moy':     note_moy,
    }
    return render(request, 'ProfManager/saisir_notes.html', context)