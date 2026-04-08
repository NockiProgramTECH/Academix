import json
import uuid
from django.shortcuts import render
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from .models import Eleve, DocumentEleve, Tuteur
from .forms import EleveForm, DocumentEleveForm, TuteurForm


def inscription_template(request):
    return render(request, 'inscriptions/inscription_form.html')


def confirmation_template(request, eleve_id):
    try:
        eleve = Eleve.objects.get(id=eleve_id)
        context = {
            'eleve': eleve,
            'matricule': eleve.matricule,
            'nom_complet': eleve.nom_complet
        }
        return render(request, 'inscriptions/confirmation.html', context)
    except Eleve.DoesNotExist:
        return render(request, 'inscriptions/erreur.html', {'message': 'Élève non trouvé'})


def liste_inscriptions_template(request):
    return render(request, 'inscriptions/liste_inscriptions.html')


@csrf_exempt
@require_http_methods(["POST"])
def inscription_api(request):
    try:
        content_type = request.content_type or ''
        if 'multipart/form-data' in content_type:
            return traiter_inscription_formdata(request)
        return JsonResponse({
            'success': False,
            'message': 'Le formulaire doit être envoyé avec enctype="multipart/form-data"',
            'debug': {'method': request.method, 'content_type': content_type}
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de l\'inscription: {str(e)}'
        }, status=500)


@transaction.atomic
def traiter_inscription_formdata(request):
    try:
        # Étape 1 : Valider les données élève
        eleve_form = EleveForm(request.POST, request.FILES)
        if not eleve_form.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'Erreur de validation des données élève',
                'errors': eleve_form.errors.get_json_data()
            }, status=400)

        # Étape 2 : Vérifier la présence des fichiers obligatoires
        fichiers_requis = ['acte_naissance', 'last_bulletin', 'diplome']
        fichiers_presents = {}
        fichiers_manquants = []

        for fichier in fichiers_requis:
            if fichier in request.FILES:
                fichiers_presents[fichier] = request.FILES[fichier]
            else:
                fichiers_manquants.append(fichier)

        if fichiers_manquants:
            return JsonResponse({
                'success': False,
                'message': 'Documents manquants',
                'fichiers_manquants': fichiers_manquants
            }, status=400)

        # Étape 3 : Valider format et taille des fichiers
        for champ, fichier in fichiers_presents.items():
            ext = fichier.name.split('.')[-1].lower()
            if ext not in ['pdf', 'docx']:
                return JsonResponse({
                    'success': False,
                    'message': f'Format non autorisé pour {fichier.name}. Utilisez PDF ou DOCX',
                    'champ_erreur': champ
                }, status=400)
            if fichier.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'message': f'Le fichier {fichier.name} dépasse 5 MB',
                    'champ_erreur': champ
                }, status=400)

        # Étape 4 : Valider la photo (optionnelle)
        photo = request.FILES.get('photo')
        if photo:
            ext_photo = photo.name.split('.')[-1].lower()
            if ext_photo not in ['jpg', 'jpeg', 'png', 'webp']:
                return JsonResponse({
                    'success': False,
                    'message': 'Format photo non autorisé. Utilisez JPG, PNG ou WEBP',
                    'champ_erreur': 'photo'
                }, status=400)
            if photo.size > 2 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'message': 'La photo ne doit pas dépasser 2 MB',
                    'champ_erreur': 'photo'
                }, status=400)

        # ── CORRECTIF DÉPENDANCE CIRCULAIRE ─────────────────────────────────
        # PROBLÈME ORIGINAL (étapes 5 et 6 dans l'ancien code) :
        #
        #   eleve.save()          → 1er INSERT, matricule généré par save()
        #   eleve.photo = photo
        #   eleve.save()          → 2ème UPDATE complet de tout l'objet
        #
        # Le 2ème save() sans `update_fields` re-déclenche tous les signaux
        # et re-évalue les upload_to. Comme `photo` est un nouvel objet fichier
        # (pas encore persisté), Django tente de le re-uploader. Cloudinary
        # répond 200 mais Django plante en insérant le chemin retourné dans
        # MySQL (trop long → STRICT_TRANS_TABLES → IntegrityError → 500).
        #
        # SOLUTION : on attache la photo à l'instance AVANT le premier save().
        # Ainsi un seul INSERT couvre tout. Le matricule est généré dans save()
        # avec `update_fields=["matricule"]` (voir models.py), ce qui ne
        # re-déclenche pas l'upload de la photo.
        # ────────────────────────────────────────────────────────────────────
        eleve = eleve_form.save(commit=False)
        eleve.id = uuid.uuid4()
        eleve.statut = 'EN_ATTENTE'

        if photo:
            # Attacher la photo AVANT le save() initial
            eleve.photo = photo

        eleve.save()  # ← Un seul INSERT. Le matricule est généré ici.

        # Étape 6 : Créer les documents APRÈS que l'élève a son matricule
        # On force un refresh pour s'assurer que document_eleve.eleve.matricule
        # est bien disponible au moment où les upload_to sont évalués.
        eleve.refresh_from_db()

        document_eleve = DocumentEleve(eleve=eleve)
        for champ, fichier in fichiers_presents.items():
            setattr(document_eleve, champ, fichier)
        document_eleve.save()

        # Étape 7 : Créer le tuteur si des données sont présentes
        tuteur_data = {
            'pere_nom':                   request.POST.get('pere_nom', ''),
            'pere_prenom':                request.POST.get('pere_prenom', ''),
            'pere_profession':            request.POST.get('pere_profession', ''),
            'pere_telephone':             request.POST.get('pere_telephone', ''),
            'pere_adresse':               request.POST.get('pere_adresse', ''),
            'mere_nom':                   request.POST.get('mere_nom', ''),
            'mere_prenom':                request.POST.get('mere_prenom', ''),
            'mere_profession':            request.POST.get('mere_profession', ''),
            'mere_telephone':             request.POST.get('mere_telephone', ''),
            'mere_adresse':               request.POST.get('mere_adresse', ''),
            'personne_prevenir_nom':      request.POST.get('personne_prevenir_nom', ''),
            'personne_prevenir_prenom':   request.POST.get('personne_prevenir_prenom', ''),
            'personne_prevenir_telephone':request.POST.get('personne_prevenir_telephone', ''),
            'personne_prevenir_lien':     request.POST.get('personne_prevenir_lien', ''),
        }

        if any(tuteur_data.values()):
            tuteur = Tuteur.objects.create(**tuteur_data)
            eleve.tuteur = tuteur
            eleve.save(update_fields=['tuteur'])  # update_fields ciblé

        confirmation_url = reverse('inscriptions:confirmation', args=[str(eleve.id)])
        return JsonResponse({
            'success': True,
            'message': 'Inscription réussie !',
            'data': {
                'eleve_id':   str(eleve.id),
                'matricule':  eleve.matricule,
                'nom_complet': eleve.nom_complet,
                'statut':     eleve.statut,
                'redirect_url': confirmation_url
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de l\'inscription: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def eleve_detail_api(request, eleve_id):
    try:
        eleve = Eleve.objects.get(id=eleve_id)
        try:
            documents = DocumentEleve.objects.get(eleve=eleve)
            documents_data = {
                'acte_naissance': documents.acte_naissance.name if documents.acte_naissance else None,
                'last_bulletin':  documents.last_bulletin.name if documents.last_bulletin else None,
                'diplome':        documents.diplome.name if documents.diplome else None,
            }
        except DocumentEleve.DoesNotExist:
            documents_data = None

        return JsonResponse({
            'success': True,
            'data': {
                'id':             str(eleve.id),
                'matricule':      eleve.matricule,
                'nom':            eleve.nom,
                'prenom':         eleve.prenom,
                'nom_complet':    eleve.nom_complet,
                'date_naissance': eleve.date_naissance.isoformat(),
                'classe':         eleve.get_classe_display(),
                'adresse':        eleve.adresse,
                'statut':         eleve.statut,
                'documents':      documents_data,
            }
        })
    except Eleve.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Élève non trouvé'}, status=404)


@require_http_methods(["GET"])
def liste_eleves_api(request):
    try:
        statut = request.GET.get('statut')
        classe = request.GET.get('classe')

        queryset = Eleve.objects.all().order_by('-date_inscription')
        if statut:
            queryset = queryset.filter(statut=statut)
        if classe:
            queryset = queryset.filter(classe=classe)

        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        eleves = queryset[start:end]

        data = [{
            'id':               str(e.id),
            'matricule':        e.matricule,
            'nom_complet':      e.nom_complet,
            'classe':           e.get_classe_display(),
            'statut':           e.statut,
            'date_inscription': e.date_inscription.strftime('%d/%m/%Y %H:%M'),
        } for e in eleves]

        return JsonResponse({
            'success': True,
            'data': data,
            'pagination': {
                'total':       total,
                'page':        page,
                'page_size':   page_size,
                'total_pages': (total + page_size - 1) // page_size,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)