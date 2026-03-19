from django.urls import path
from . import views

app_name = 'inscriptions'

urlpatterns = [
    # Templates
    path('', views.inscription_template, name='inscription_form'),
    path('confirmation/<uuid:eleve_id>/', views.confirmation_template, name='confirmation'),
    path('liste/', views.liste_inscriptions_template, name='liste_inscriptions'),
    
    # APIs (pour AJAX)
    path('api/inscription/', views.inscription_api, name='inscription_api'),
    path('api/eleve/<uuid:eleve_id>/', views.eleve_detail_api, name='eleve_detail_api'),
    path('api/eleves/', views.liste_eleves_api, name='liste_eleves_api'),
]
