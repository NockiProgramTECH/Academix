from django.contrib import admin

# Register your models here.
from .models import Eleve, DocumentEleve, Tuteur

@admin.register(Tuteur)
class TuteurAdmin(admin.ModelAdmin):
    list_display = ['id', 'pere_nom', 'pere_prenom', 'mere_nom', 'mere_prenom']
    search_fields = ['pere_nom', 'pere_prenom', 'mere_nom', 'mere_prenom']
    list_per_page = 25

@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ['id', 'nom', 'prenom','classe', 'adresse', 'photo']
    list_filter = ['statut', 'id','classe']
    search_fields = ['nom', 'prenom','matricule']
    list_per_page = 25
    readonly_fields = ['date_inscription']
    fieldsets = (
        (None, {
            'fields': ('nom', 'prenom','date_naissance',"adresse","matricule","classe", "photo", "tuteur")
        }),
        # ('Advanced options', {
        #     'classes': ('collapse',),
        #     'fields': ('i', 'metadata'),
        # }),
    )

@admin.register(DocumentEleve)
class DocumentEleveAdmin(admin.ModelAdmin):
    list_display =['eleve','est_valide']
    list_filter =['est_valide']
    search_fields =["eleve__nom",'eleve__prenom','eleve__matricule']
    list_per_page =25