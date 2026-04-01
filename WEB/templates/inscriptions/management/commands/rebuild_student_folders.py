"""
Commande de gestion Django pour reconstruire les dossiers des élèves

Usage:
    python manage.py rebuild_student_folders
    python manage.py rebuild_student_folders --clean-all
    python manage.py rebuild_student_folders --class 6EME
    python manage.py rebuild_student_folders --statistics
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
import shutil
from Inscriptions.models import Eleve
from Inscriptions.utils import create_eleve_folder_structure, get_eleve_directory


class Command(BaseCommand):
    help = 'Reconstruit les dossiers des élèves ou affiche des statistiques'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean-all',
            action='store_true',
            help='Supprime tous les dossiers inscriptions avant de les recréer',
        )
        parser.add_argument(
            '--class',
            type=str,
            help='Reconstruire seulement pour une classe spécifique (ex: 6EME)',
        )
        parser.add_argument(
            '--statistics',
            action='store_true',
            help='Affiche les statistiques des dossiers sans rien modifier',
        )
        parser.add_argument(
            '--check',
            action='store_true',
            help='Vérifie la cohérence entre la DB et les dossiers',
        )

    def handle(self, *args, **options):
        if options['statistics']:
            self.afficher_statistiques()
        elif options['check']:
            self.verifier_coherence()
        elif options['clean_all']:
            self.nettoyer_tous_dossiers()
            self.reconstruire_tous_dossiers()
        elif options['class']:
            self.reconstruire_classe(options['class'])
        else:
            self.reconstruire_tous_dossiers()

    def reconstruire_tous_dossiers(self):
        """Reconstruit les dossiers pour tous les élèves"""
        self.stdout.write(
            self.style.SUCCESS('🔄 Reconstruction de tous les dossiers...')
        )

        eleves = Eleve.objects.all()
        total = eleves.count()
        success = 0
        errors = 0

        for i, eleve in enumerate(eleves, 1):
            try:
                create_eleve_folder_structure(eleve.classe, eleve.nom_complet)
                success += 1
                self.stdout.write(
                    f"  [{i}/{total}] ✓ {eleve.nom_complet} ({eleve.classe})"
                )
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  [{i}/{total}] ✗ {eleve.nom_complet} - {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Reconstruction terminée: {success}/{total} dossiers créés"
            )
        )
        if errors > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️  {errors} erreurs rencontrées")
            )

    def reconstruire_classe(self, classe):
        """Reconstruit les dossiers pour une classe spécifique"""
        # Vérifier que la classe est valide
        classes_valides = [choice[0] for choice in Eleve.CLASS_CHOICES]
        if classe.upper() not in classes_valides:
            raise CommandError(
                f"Classe invalide: {classe}. Classes valides: {', '.join(classes_valides)}"
            )

        self.stdout.write(
            self.style.SUCCESS(f'🔄 Reconstruction des dossiers de {classe}...')
        )

        eleves = Eleve.objects.filter(classe=classe.upper())
        total = eleves.count()

        if total == 0:
            self.stdout.write(
                self.style.WARNING(f"Aucun élève trouvé en {classe}")
            )
            return

        success = 0
        errors = 0

        for i, eleve in enumerate(eleves, 1):
            try:
                create_eleve_folder_structure(eleve.classe, eleve.nom_complet)
                success += 1
                self.stdout.write(f"  [{i}/{total}] ✓ {eleve.nom_complet}")
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"  [{i}/{total}] ✗ {eleve.nom_complet} - {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ {success}/{total} dossiers créés pour {classe}"
            )
        )
        if errors > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️  {errors} erreurs rencontrées")
            )

    def nettoyer_tous_dossiers(self):
        """Supprime tous les dossiers inscriptions"""
        media_path = Path(settings.MEDIA_ROOT) / 'inscriptions'

        if not media_path.exists():
            self.stdout.write(self.style.WARNING("📁 Aucun dossier à supprimer"))
            return

        self.stdout.write(
            self.style.WARNING('🗑️  Suppression de tous les dossiers inscriptions...')
        )

        try:
            shutil.rmtree(media_path)
            self.stdout.write(
                self.style.SUCCESS('✓ Tous les dossiers ont été supprimés')
            )
        except Exception as e:
            raise CommandError(f"Erreur lors de la suppression: {str(e)}")

    def afficher_statistiques(self):
        """Affiche les statistiques des dossiers"""
        media_path = Path(settings.MEDIA_ROOT) / 'inscriptions'

        self.stdout.write(self.style.SUCCESS('\n📊 STATISTIQUES DES DOSSIERS\n'))

        if not media_path.exists():
            self.stdout.write(self.style.WARNING("Aucun dossier d'inscription trouvé"))
            return

        classes_stats = {}
        total_eleves_db = Eleve.objects.count()
        total_dossiers = 0

        for classe_dir in sorted(media_path.iterdir()):
            if classe_dir.is_dir():
                classe = classe_dir.name
                photos_dir = classe_dir / 'photos'
                if photos_dir.exists():
                    eleves_dossiers = [d for d in photos_dir.iterdir() if d.is_dir()]
                    eleves_db = Eleve.objects.filter(classe=classe).count()

                    classes_stats[classe] = {
                        'dossiers': len(eleves_dossiers),
                        'db': eleves_db,
                    }
                    total_dossiers += len(eleves_dossiers)

        # Afficher les statistiques
        self.stdout.write(f"Élèves en base de données: {total_eleves_db}")
        self.stdout.write(f"Dossiers créés: {total_dossiers}\n")

        self.stdout.write("Par classe:")
        for classe in sorted(classes_stats.keys()):
            stats = classes_stats[classe]
            dossiers = stats['dossiers']
            db = stats['db']
            sync = "✓" if dossiers == db else "✗"
            self.stdout.write(
                f"  {sync} {classe:5} - Dossiers: {dossiers:2} | DB: {db:2}"
            )

        # Résumé
        if total_dossiers == total_eleves_db:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Tous les dossiers sont synchronisés!")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Désynchronisation détectée: "
                    f"{total_dossiers} dossiers vs {total_eleves_db} élèves"
                )
            )

    def verifier_coherence(self):
        """Vérifie la cohérence entre la BD et les dossiers"""
        media_path = Path(settings.MEDIA_ROOT) / 'inscriptions'

        self.stdout.write(self.style.SUCCESS('\n🔍 VÉRIFICATION DE LA COHÉRENCE\n'))

        if not media_path.exists():
            self.stdout.write(self.style.WARNING("Aucun dossier d'inscription trouvé"))
            return

        issues = []

        # Vérifier tous les élèves de la DB
        for eleve in Eleve.objects.all():
            dossier_path = get_eleve_directory(eleve.classe, eleve.nom_complet)
            if not Path(dossier_path).exists():
                issues.append(
                    f"❌ Élève DB trouvé mais dossier manquant: {eleve.nom_complet}"
                )

        # Vérifier tous les dossiers existants
        for classe_dir in media_path.iterdir():
            if classe_dir.is_dir():
                photos_dir = classe_dir / 'photos'
                if photos_dir.exists():
                    for eleve_dir in photos_dir.iterdir():
                        if eleve_dir.is_dir():
                            # Essayer de trouver cet élève en DB
                            nom_prenom = eleve_dir.name.split('-')
                            if len(nom_prenom) == 2:
                                eleves = Eleve.objects.filter(
                                    nom=nom_prenom[0],
                                    prenom=nom_prenom[1]
                                )
                                if not eleves.exists():
                                    issues.append(
                                        f"⚠️  Dossier orphelin: {eleve_dir.name}"
                                    )

        if not issues:
            self.stdout.write(
                self.style.SUCCESS('✅ Aucun problème de cohérence détecté!')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Problèmes trouvés ({len(issues)}):')
            )
            for issue in issues:
                self.stdout.write(f"  {issue}")
