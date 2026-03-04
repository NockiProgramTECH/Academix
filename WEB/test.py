import os
import django
import random
from datetime import datetime, timedelta
from faker import Faker
from django.core.files import File
from django.core.files.base import ContentFile

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AcademixWeb.settings')  # Remplacez par le nom de votre projet
django.setup()

from Inscriptions.models import *  # Remplacez 'votre_app' par le nom de votre application

fake = Faker('fr_FR')  # Utilisation de la locale française

def create_eleves_with_faker(nombre_eleves=300):
    """
    Crée des élèves factices avec leurs tuteurs et documents
    """
    
    # Classes disponibles
    classes = ['6EME', '5EME', '4EME', '3EME', '2nd']
    
    # Chemins pour les fichiers
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    photo_path = os.path.join(base_dir, 'photos', 'img.png')
    
    # Vérifier si la photo existe
    if not os.path.exists(photo_path):
        print(f"Attention: La photo {photo_path} n'existe pas. Création d'un répertoire photos/ avec une image par défaut.")
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        # Créer une image vide si elle n'existe pas (vous pouvez ajouter votre propre image)
        with open(photo_path, 'wb') as f:
            f.write(b'')  # Image vide, à remplacer par une vraie image
    
    eleves_crees = 0
    
    for i in range(nombre_eleves):
        try:
            print(f"Création de l'élève {i+1}/{nombre_eleves}")
            
            # Création du tuteur
            tuteur = Tuteur.objects.create(
                # Père
                pere_nom=fake.last_name(),
                pere_prenom=fake.first_name(),
                pere_profession=fake.job(),
                pere_telephone=fake.phone_number(),
                pere_adresse=fake.address(),
                
                # Mère
                mere_nom=fake.last_name(),
                mere_prenom=fake.first_name(),
                mere_profession=fake.job(),
                mere_telephone=fake.phone_number(),
                mere_adresse=fake.address(),
                
                # Personne à prévenir
                personne_prevenir_nom=fake.last_name(),
                personne_prevenir_prenom=fake.first_name(),
                personne_prevenir_telephone=fake.phone_number(),
                personne_prevenir_lien=random.choice(['Parent', 'Oncle', 'Tante', 'Grand-parent', 'Voisin'])
            )
            
            # Date de naissance entre 2006 et 2018
            date_naissance = fake.date_of_birth(minimum_age=6, maximum_age=18)
            
            # Création de l'élève
            eleve = Eleve.objects.create(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                date_naissance=date_naissance,
                classe=random.choice(classes),
                classe_reelle=None,  # Laisser à null comme demandé
                adresse=fake.address(),
                tuteur=tuteur,
                statut="ACCEPTED",
                date_inscription=fake.date_time_between(start_date='-1y', end_date='now')
            )
            
            # Ajout de la photo (la même pour tous)
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as img_file:
                    eleve.photo.save('photo_identite.png', File(img_file), save=True)
            
            # Création des documents
            document = DocumentEleve.objects.create(
                eleve=eleve,
                est_valide=random.choice([True, False])
            )
            
            # Création de fichiers PDF factices pour les documents
            # Acte de naissance
            acte_content = fake.text()
            document.acte_naissance.save(
                f'acte_naissance_{eleve.nom}_{eleve.prenom}.pdf',
                ContentFile(acte_content.encode('utf-8')),
                save=True
            )
            
            # Dernier bulletin
            bulletin_content = fake.text()
            document.last_bulletin.save(
                f'bulletin_{eleve.nom}_{eleve.prenom}.pdf',
                ContentFile(bulletin_content.encode('utf-8')),
                save=True
            )
            
            # Diplôme
            diplome_content = fake.text()
            document.diplome.save(
                f'diplome_{eleve.nom}_{eleve.prenom}.pdf',
                ContentFile(diplome_content.encode('utf-8')),
                save=True
            )
            
            eleves_crees += 1
            
        except Exception as e:
            print(f"Erreur lors de la création de l'élève {i+1}: {str(e)}")
            continue
    
    print(f"\n✅ {eleves_crees} élèves créés avec succès sur {nombre_eleves} demandés")

def verify_data():
    """
    Vérifie les données créées
    """
    total_eleves = Eleve.objects.count()
    total_tuteurs = Tuteur.objects.count()
    total_documents = DocumentEleve.objects.count()
    
    print("\n=== VÉRIFICATION DES DONNÉES ===")
    print(f"Nombre total d'élèves: {total_eleves}")
    print(f"Nombre total de tuteurs: {total_tuteurs}")
    print(f"Nombre total de documents: {total_documents}")
    
    # Répartition par classe
    print("\nRépartition par classe:")
    for classe in ['6EME', '5EME', '4EME', '3EME', '2nd']:
        count = Eleve.objects.filter(classe=classe).count()
        print(f"  {classe}: {count} élèves")
    
    # Répartition par statut
    print("\nRépartition par statut:")
    for statut, label in Eleve.STATUT_CHOICES:
        count = Eleve.objects.filter(statut=statut).count()
        print(f"  {label}: {count} élèves")

if __name__ == "__main__":
    # Installation de Faker si nécessaire
    try:
        import faker
    except ImportError:
        print("Installation de Faker...")
        os.system("pip install faker")
        import faker
    
    print("=== CRÉATION DES ÉLÈVES FACTICES ===\n")
    
    # Demander le nombre d'élèves à créer
    try:
        nombre = int(input("Combien d'élèves voulez-vous créer? (défaut: 300): ") or "300")
    except ValueError:
        nombre = 300
    
    create_eleves_with_faker(nombre)
    verify_data()