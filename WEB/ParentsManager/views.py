from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import ParentSignUpForm
from .models import ParentModel

class ParentSignUpView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('parent_dashboard')
        form = ParentSignUpForm()
        return render(request, 'ParentsManager/signup.html', {'form': form})
        
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('parent_dashboard')
            
        form = ParentSignUpForm(request.POST)
        if form.is_valid():
            # 1. Enregistrement Utilisateur
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # 2. Création du profil Parent dynamique
            parent = ParentModel.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )
            
            # 3. Association de l'enfant (validé par clean_matricule_enfant du form)
            eleve = form.cleaned_data['matricule_enfant']
            parent.children.add(eleve)
            
            # 4. Connexion automatique tel que décidé au plan !
            login(request, user)
            return redirect('parent_dashboard')
            
        return render(request, 'ParentsManager/signup.html', {'form': form})


class ParentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ParentsManager/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Le login_required assure qu'on est au moins authentifié,
        # mais il faut s'assurer d'avoir un profil Parent
        try:
            parent_profile = self.request.user.parent_profile
            trimestre_actuel = 1  # Pourrait être configuré dynamiquement
            annee_actuelle = "2025-2026" # À configurer selon votre session scolaire
            
            context['parent'] = parent_profile
            # Appel dynamique avec les méthodes de l'élève !
            context['performances'] = parent_profile.get_children_performance(
                trimestre=trimestre_actuel,
                annee=None # Laisser None permet de filtrer uniquement sur le trimestre et pas l'année pr l'instant
            )
            
        except ParentModel.DoesNotExist:
            context['erreur'] = "Vous n'êtes pas reconnu comme un Parent par l'application."
            
        return context
