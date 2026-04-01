"""
═══════════════════════════════════════════════════════════════════════════════
ACADEMIX — MODULE VIE SCOLAIRE : GUIDE D'INTÉGRATION
═══════════════════════════════════════════════════════════════════════════════

FICHIERS FOURNIS
----------------
  data/db_vie_scolaire.py   → couche BDD (tables, absences, EDT, pénalité)
  views/vie_scolaire.py     → interface CustomTkinter (3 onglets)
  INTEGRATION.py            → ce fichier (instructions + patch bulletin)

ÉTAPE 1 — DÉPLACER LES FICHIERS
─────────────────────────────────
Placer les fichiers dans votre projet :

  Academix/
  ├── data/
  │   ├── db_manager.py          (existant)
  │   ├── db_note.py             (existant)
  │   └── db_vie_scolaire.py     ← NOUVEAU
  └── views/
      ├── notes.py               (existant — voir Étape 3 pour patch)
      ├── eleves.py              (existant)
      └── vie_scolaire.py        ← NOUVEAU


ÉTAPE 2 — INTÉGRATION DANS acceuil.py
──────────────────────────────────────
Apporter les 4 modifications suivantes dans Acceuil.__init__ :

  A) Ajouter le bouton dans le dict BTN (sidebar) :

      6: {"text": "📅 Vie Scolaire", "command": lambda: self.show_view("vie_scolaire")},

  B) Ajouter l'appel de création de la vue (après _create_notes_view) :

      self._create_vie_scolaire_view()

  C) Ajouter la méthode _create_vie_scolaire_view() dans la classe Acceuil :

      def _create_vie_scolaire_view(self):
          from views.vie_scolaire import VieScolaireView
          view = VieScolaireView(self.mainFrame, db=self.Database)
          view.pack_forget()
          self.views["vie_scolaire"] = view

  D) Optionnel — brancher le badge de notification de VieScolaireView
     (même principe qu'EleveView) dans __init__, après les lignes existantes :

      # Injection du label dans VieScolaireView pour les alertes d'absences web
      self.views["vie_scolaire"]._notif_label = self.notificationLabel
      self.views["vie_scolaire"].start_global_polling()

  E) Dans _on_close(), arrêter le polling Vie Scolaire :

      if "vie_scolaire" in self.views:
          self.views["vie_scolaire"].stop_global_polling()


ÉTAPE 3 — PATCH DU BULLETIN DANS notes.py
──────────────────────────────────────────
Le bulletin existant affiche seulement la moyenne pondérée par matière.
Pour afficher la pénalité d'absence et la Moyenne Définitive, il faut
modifier _PanneauBulletins.refresh() dans notes.py.

Localiser dans notes.py la méthode _PanneauBulletins.refresh() et
remplacer l'intégralité de la méthode _reload() par le code ci-dessous.
Ne pas toucher au reste de _PanneauBulletins.

---- DÉBUT DU PATCH ----
"""

# ─── PATCH notes.py · _PanneauBulletins._reload() ────────────────────────────
#
# Ajouter en haut de notes.py (dans les imports) :
#   from data.db_vie_scolaire import VieScolaireDB
#
# Modifier __init__ de NotesView pour passer db (DbManager) en plus de NotesDB :
#   self.ndb    = NotesDB(db.connection)
#   self.vs_db  = VieScolaireDB(db.connection)
# … et transmettre vs_db aux panneaux :
#   "bulletins": _PanneauBulletins(self, self.ndb, self.vs_db),
#
# Dans _PanneauBulletins.__init__, ajouter le paramètre vs_db :
#   def __init__(self, parent, db: NotesDB, vs_db: VieScolaireDB, **kw):
#       ...
#       self.vs_db = vs_db
#
# Puis remplacer _PanneauBulletins._reload() par la version ci-dessous :
# ─────────────────────────────────────────────────────────────────────────────

PATCH_PANNEAU_BULLETINS = '''
    def _reload(self):
        """
        Recharge le bulletin de l\'élève sélectionné.
        Intègre la pénalité d\'absence fournie par VieScolaireDB.
        """
        for r in self._tree.get_children():
            self._tree.delete(r)

        # Réinitialiser le résumé bas de page
        if hasattr(self, "_lbl_moy_pond"):
            self._lbl_moy_pond.configure(text="Moy. pondérée : —")
            self._lbl_penalite.configure(text="Pénalité absence : 0.00")
            self._lbl_moy_def.configure(text="Moy. Définitive : —")

        eleve_id = self._get_eleve_id()
        if not eleve_id or not self._classe_id:
            return

        # ── Données du bulletin (notes + pénalité) ────────────────────────
        bulletin = self.vs_db.get_bulletin_avec_penalite(
            eleve_id, self._trimestre, self.db, ANNEE
        )

        # ── Remplissage du Treeview ───────────────────────────────────────
        for ligne in bulletin["lignes"]:
            moy = float(ligne["moyenne"])
            self._tree.insert("", END, values=(
                ligne["nom"],
                ligne["coefficient"],
                f"{moy:.2f}",
                f"{float(ligne[\'points\']):.2f}",
            ))

        # ── Résumé bas de page ────────────────────────────────────────────
        moy_p = float(bulletin["moyenne_ponderee"])
        penali = float(bulletin["penalite"])
        moy_d  = float(bulletin["moyenne_definitive"])
        h_nj   = float(bulletin["heures_nj"])
        h_j    = float(bulletin["heures_j"])

        if hasattr(self, "_lbl_moy_pond"):
            self._lbl_moy_pond.configure(
                text=f"Moy. pondérée : {moy_p:.2f}/20"
            )
            couleur_pen = "#C62828" if penali > 0 else "#2E7D32"
            self._lbl_penalite.configure(
                text=f"Pénalité absence : −{penali:.2f} pt  "
                     f"({h_nj:.1f}h NJ · {h_j:.1f}h J)",
                text_color=couleur_pen
            )
            couleur_def = "#2E7D32" if moy_d >= 10 else "#C62828"
            self._lbl_moy_def.configure(
                text=f"Moyenne Définitive : {moy_d:.2f}/20",
                text_color=couleur_def
            )
'''

# ─── Ajout des labels dans _PanneauBulletins._build() ────────────────────────
#
# À la fin de _build(), ajouter un panneau de résumé sous le Treeview :
# ─────────────────────────────────────────────────────────────────────────────

PATCH_BUILD_SUMMARY = '''
        # ── Résumé financier bas de page (ajouter à la fin de _build) ────────
        summary = CTkFrame(self, fg_color="#E3F2FD", corner_radius=8)
        summary.pack(fill=X, padx=10, pady=(0, 8))

        self._lbl_moy_pond = CTkLabel(
            summary, text="Moy. pondérée : —",
            font=FONT_LABEL, text_color=TEXT_DARK, fg_color="#E3F2FD"
        )
        self._lbl_moy_pond.pack(side=LEFT, padx=16, pady=8)

        self._lbl_penalite = CTkLabel(
            summary, text="Pénalité absence : 0.00",
            font=FONT_LABEL, text_color="#C62828", fg_color="#E3F2FD"
        )
        self._lbl_penalite.pack(side=LEFT, padx=16, pady=8)

        self._lbl_moy_def = CTkLabel(
            summary, text="Moy. Définitive : —",
            font=("goudy old style", 14, "bold"), text_color="#1565C0",
            fg_color="#E3F2FD"
        )
        self._lbl_moy_def.pack(side=RIGHT, padx=16, pady=8)
'''


"""
ÉTAPE 4 — TABLES MySQL CRÉÉES AUTOMATIQUEMENT
─────────────────────────────────────────────
VieScolaireDB._create_tables() crée les tables au premier démarrage.
Aucune migration manuelle nécessaire.

Tables créées :
  ┌──────────────────────────────────────────────────────────────────────────┐
  │ absences                                                                  │
  │   id, eleve_id, date_absence, heure_debut, heure_fin,                    │
  │   statut ENUM('JUSTIFIEE','NON_JUSTIFIEE'), motif,                        │
  │   trimestre, annee_scolaire, creneau_id, saisie_par, date_saisie         │
  ├──────────────────────────────────────────────────────────────────────────┤
  │ configuration_discipline                                                  │
  │   id, tranche_heures, points_par_palier, plafond_points, description     │
  │   (initialisé avec : 5h → -0.5 pt, plafond 5 pts)                       │
  ├──────────────────────────────────────────────────────────────────────────┤
  │ emploi_du_temps                                                           │
  │   id, classe_id, matiere_id, professeur_id,                              │
  │   jour ENUM(Lundi…Samedi), heure_debut, heure_fin, salle, annee_scolaire │
  └──────────────────────────────────────────────────────────────────────────┘


ÉTAPE 5 — INTÉGRATION CÔTÉ DJANGO (Web)
────────────────────────────────────────
Le polling Desktop détecte les absences ajoutées depuis Django en comparant
MAX(date_saisie) de la table absences.

Côté Django, insérez dans la table `absences` avec :
  saisie_par = 'DJANGO'   (ou tout autre valeur ≠ 'SECRETARIAT')

Le Desktop détectera automatiquement les nouvelles lignes dans les 30 s.


RÉCAPITULATIF DE L'ARCHITECTURE
────────────────────────────────

  acceuil.py
    └─ VieScolaireView (views/vie_scolaire.py)
         ├─ _OngletEmploiDuTemps
         │    └─ _FormCreneau (popup CRUD)
         ├─ _OngletAbsences
         │    ├─ Formulaire saisie rapide
         │    └─ Tableau absences + Justifier / Supprimer
         └─ _OngletConfig (règle pénalité)
              └─ Aperçu de la règle active

  data/db_vie_scolaire.py (VieScolaireDB)
    ├─ get_config_discipline() / update_config_discipline()
    ├─ add_absence() / justifier_absence() / delete_absence()
    ├─ get_absences_classe_date() / get_nb_absences_classe()
    ├─ calculer_penalite_absence(eleve_id, trimestre) ← FONCTION CLÉ
    ├─ get_bulletin_avec_penalite(eleve_id, trimestre, notes_db)
    │    ├─ notes_db.get_bulletin_eleve()   ← module Notes non modifié ✓
    │    ├─ notes_db.get_moyenne_generale() ← module Notes non modifié ✓
    │    └─ calculer_penalite_absence()     ← module Vie Scolaire
    ├─ add_creneau() / update_creneau() / delete_creneau()
    └─ get_last_absence_ts()               ← utilisé par le polling
"""