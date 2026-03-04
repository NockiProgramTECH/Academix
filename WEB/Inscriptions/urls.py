from django.urls import path
from . import views

app_name = 'inscriptions'

urlpatterns = [
    # Templates
    path('inscriptions/', views.inscription_template, name='inscription_form'),
    path('inscriptions/confirmation/<uuid:eleve_id>/', views.confirmation_template, name='confirmation'),
    path('inscriptions/liste/', views.liste_inscriptions_template, name='liste_inscriptions'),
    
    # APIs (pour AJAX)
    path('inscriptions/api/inscription/', views.inscription_api, name='inscription_api'),
    path('inscriptions/api/eleve/<uuid:eleve_id>/', views.eleve_detail_api, name='eleve_detail_api'),
    path('inscriptions/api/eleves/', views.liste_eleves_api, name='liste_eleves_api'),
]
