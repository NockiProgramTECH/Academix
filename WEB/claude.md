Je souhaite migrer mon logiciel de gestion scolaire actuel (fait en Python/CustomTkinter) vers une architecture 100% Web avec Django.

1. Analyse des fichiers fournis : Je vais te donner mes fichiers db_manager.py, db_compta_manager.py (pour la logique SQL) et mes fichiers de vues eleves.py, compta.py. Analyse bien comment les données sont traitées (calculs de soldes, gestion des tranches, validation des inscriptions).

2. Architecture Django cible : Crée un projet Django structuré en 3 applications principales :


school : Pour la gestion des élèves, classes et inscriptions (basé sur eleves.py).



finance : Pour les paiements, types de frais et dépenses (basé sur compta.py).



pedagogy : Pour les notes, moyennes et absences (nouveau module).

3. Tâches spécifiques :





Modèles (models.py) : Génère les modèles Django qui correspondent exactement à mes tables MySQL actuelles. Utilise db_table dans la classe Meta. Transforme les managed=False en managed=True.



Logique Métier : Déplace les fonctions complexes de mes db_managers (ex: calcul du reste à payer, génération de numéro de reçu) directement dans les méthodes des modèles Django ou dans des services.py.



Vues (Views) : Crée des ListView et DetailView Bootstrap pour remplacer mes Treeviews Tkinter.



API (Flutter Ready) : Installe Django REST Framework et prépare les premiers Serializers pour que je puisse plus tard connecter mon application mobile Flutter.

4. Contraintes :







Utilise tailwind css pour le design.



Garde la même base de données MySQL.



Assure-toi que le système de "Validation" de la secrétaire (statut EN_ATTENTE vers ACCEPTED) fonctionne exactement comme dans mon code actuel



SKILL: UI/UX Dashboard Designer

Objectif:
Transformer toutes les vues Django en interfaces modernes inspirées des dashboards SaaS (Admin Panel).

Contraintes:
- Sidebar verticale fixe à gauche
- Navbar en haut avec notifications et profil
- Cartes (cards) avec ombres, statistiques et icônes
- Tableaux modernes avec pagination, recherche et filtres
- Utiliser Tailwind CSS + Alpine.js

Attentes:
- Générer des templates HTML propres et réutilisables
- Créer des composants (cards, tables, modals)
- Respecter une hiérarchie visuelle claire (Admin Pro style)

Bonus:
- Ajouter dark mode
- Ajouter animations légères (hover, transition)