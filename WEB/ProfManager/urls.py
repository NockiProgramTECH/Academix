from django.urls import path
from . import views

app_name = 'profmanager'

urlpatterns = [
    path('', views.ProfLogin, name='login'),
    path('logout/', views.ProfLogout, name='logout'),
    path('dashboard/<str:matricule>/', views.ProfDashBoard, name='dashboard'),
    path('dashboard/<str:matricule>/evaluer/<int:enseignement_id>/',
         views.CreerEvaluation, name='creer_evaluation'),
    path('dashboard/<str:matricule>/notes/<int:evaluation_id>/',
         views.SaisirNotes, name='saisir_notes'),
]