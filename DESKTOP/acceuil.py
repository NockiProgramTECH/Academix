"""
Module Acceuil — Fenêtre principale de l'application Academix.

CORRECTIONS APPLIQUÉES :
  1. Instance DbManager UNIQUE transmise à toutes les vues.
  2. show_view() appelle refresh() immédiatement après .pack().
  3. Le polling de notifications EST DÉLÉGUÉ à EleveView.start_global_polling().
  4. VieScolaireView intégrée avec son propre polling d'absences.
  5. Fermeture propre : stop_global_polling() appelé sur EleveView et VieScolaireView.
"""

import pathlib
from tkinter import messagebox
from customtkinter import *
from utils.constant import *
from PIL import Image, ImageTk
from data.db_manager import DbManager, get_shared_db

IMAGE_DIR = pathlib.Path(__file__).parent / "images"


class Acceuil(CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}-1+0")
        self.title("Academix")
        self._set_appearance_mode("light")

        # Instance DB partagée entre toutes les vues
        self.Database = get_shared_db()

        self.images       = {}
        self.views        = {}
        self.current_view = None

        # ══════════════════════════════════════════════════════════════════════
        # HEADER
        # ══════════════════════════════════════════════════════════════════════
        header = CTkFrame(self, fg_color=PRIMARY_BLUE, height=75,
                          border_width=0, bg_color=PRIMARY_BLUE)
        header.pack(fill=X, side=TOP)
        header.pack_propagate(False)

        self.images['logo'] = CTkImage(
            Image.open(IMAGE_DIR / "logo.png"), size=(50, 50)
        )
        CTkLabel(header, image=self.images['logo'], text="").pack(side=LEFT, padx=20)

        self.images['notification_icon'] = CTkImage(
            Image.open(IMAGE_DIR / "notification.png"), size=(50, 50)
        )
        self.notificationLabel = CTkButton(
            header,
            image=self.images['notification_icon'],
            text="0",
            font=("goudy old style", 30, "bold"),
            fg_color=PRIMARY_BLUE,
            text_color="red"
        )
        self.notificationLabel.pack(side=RIGHT, padx=20)

        # ══════════════════════════════════════════════════════════════════════
        # SIDEBAR
        # ══════════════════════════════════════════════════════════════════════
        sidebar = CTkFrame(self, fg_color=SIDEBAR_BG, width=SIDEBAR_WIDTH,
                           border_width=0)
        sidebar.pack(fill=Y, side=LEFT)
        sidebar.pack_propagate(False)

        CTkLabel(sidebar, text="Tableau de bord", font=FONT_TITLE,
                 fg_color=SIDEBAR_BG, text_color=SIDEBAR_TEXT).pack(pady=20)

        BTN = {
            1: {"text": "Gestion Des Élèves",     "command": lambda: self.show_view("eleve")},
            2: {"text": "Affectation Par Classe",  "command": lambda: self.show_view("repartitions")},
            3: {"text": "Gestion Des Professeurs", "command": lambda: self.show_view("professeurs")},
            4: {"text": "📝 Gestion des Notes",    "command": lambda: self.show_view("notes")},
            5: {"text": "📅 Vie Scolaire",          "command": lambda: self.show_view("vie_scolaire")},
            6: {"text": "💰 Caisse & Scolarité",   "command": lambda: self.show_view("caisse")},
        }

        for _, value in BTN.items():
            CTkButton(
                sidebar,
                text=value['text'],
                font=FONT_TITLE,
                fg_color=SIDEBAR_BG,
                text_color=SIDEBAR_TEXT,
                command=value['command'],
                hover_color=SIDEBAR_HOVER,
                border_width=5
            ).pack(fill=X, pady=5, padx=10)

        # ══════════════════════════════════════════════════════════════════════
        # ZONE DE CONTENU
        # ══════════════════════════════════════════════════════════════════════
        self.mainFrame = CTkFrame(self, fg_color=BACKGROUND_LIGHT,
                                  bg_color=BACKGROUND_LIGHT)
        self.mainFrame.pack(fill=BOTH, side=LEFT, expand=True)

        # ══════════════════════════════════════════════════════════════════════
        # PRÉ-CRÉATION DES VUES
        # ══════════════════════════════════════════════════════════════════════
        self._create_eleve_view()
        self._create_repartitions_view()
        self._create_professeurs_view()
        self._create_notes_view()
        self._create_vie_scolaire_view()      # ← NOUVEAU
        # self._create_caisse_view()

        # ── Injection du label de notifications dans EleveView ────────────────
        self.views["eleve"]._notif_label = self.notificationLabel

        # ── Injection du label dans VieScolaireView (alertes absences web) ───
        self.views["vie_scolaire"]._notif_label = self.notificationLabel

        # ── Démarrage des pollings ────────────────────────────────────────────
        print("[ACCEUIL] Démarrage du polling global élèves...")
        self.views["eleve"].start_global_polling()

        print("[ACCEUIL] Démarrage du polling absences...")
        self.views["vie_scolaire"].start_global_polling()

        print("[ACCEUIL] Pollings démarrés.")

        # Affiche la vue par défaut
        self.show_view("eleve")
        print("[ACCEUIL] Vue eleve affichée.")

        # Fermeture propre
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ══════════════════════════════════════════════════════════════════════════
    # CRÉATION DES VUES
    # ══════════════════════════════════════════════════════════════════════════

    def _create_eleve_view(self):
        from views.eleves import EleveView
        view = EleveView(self.mainFrame, db=self.Database)
        view.pack_forget()
        self.views["eleve"] = view

    def _create_repartitions_view(self):
        from views.repartitions import Repartitions
        view = Repartitions(self.mainFrame, db=self.Database)
        view.pack_forget()
        self.views["repartitions"] = view

    def _create_professeurs_view(self):
        from views.professeurs import ProfesseursView
        view = ProfesseursView(self.mainFrame, db=self.Database)
        view.pack_forget()
        self.views["professeurs"] = view

    def _create_notes_view(self):
        from views.notes import NotesView
        view = NotesView(self.mainFrame, db=self.Database)
        view.pack_forget()
        self.views["notes"] = view

    def _create_vie_scolaire_view(self):
        from views.vie_scolaire import VieScolaireView
        view = VieScolaireView(self.mainFrame, db=self.Database)
        view.pack_forget()
        self.views["vie_scolaire"] = view

    # def _create_caisse_view(self):
    #     from caisse import CaisseView
    #     view = CaisseView(self.mainFrame, db=self.Database)
    #     view.pack_forget()
    #     self.views["caisse"] = view

    # ══════════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ══════════════════════════════════════════════════════════════════════════

    def show_view(self, view_name: str):
        """Affiche une vue et recharge ses données via refresh() immédiatement."""
        if view_name not in self.views:
            print(f"[WARN] Vue introuvable : '{view_name}'")
            return

        if view_name == self.current_view:
            return

        # Quitter la vue actuelle
        if self.current_view and self.current_view in self.views:
            vue_quittee = self.views[self.current_view]
            if hasattr(vue_quittee, "_stop_auto_refresh"):
                vue_quittee._stop_auto_refresh()
            vue_quittee.pack_forget()

        # Afficher la nouvelle vue
        self.views[view_name].pack(fill=BOTH, expand=True)
        self.current_view = view_name

        # Rechargement immédiat
        if hasattr(self.views[view_name], "refresh"):
            self.views[view_name].refresh()

    # ══════════════════════════════════════════════════════════════════════════
    # RACCOURCIS
    # ══════════════════════════════════════════════════════════════════════════

    def show_eleve_view(self):           self.show_view("eleve")
    def show_repartitions_view(self):    self.show_view("repartitions")
    def show_professeurs_view(self):     self.show_view("professeurs")
    def show_notes_view(self):           self.show_view("notes")
    def show_vie_scolaire_view(self):    self.show_view("vie_scolaire")
    def show_caisse_view(self):          self.show_view("caisse")

    # ══════════════════════════════════════════════════════════════════════════
    # FERMETURE PROPRE
    # ══════════════════════════════════════════════════════════════════════════

    def _on_close(self):
        """Arrête tous les jobs after() avant de fermer la fenêtre."""
        if "eleve" in self.views:
            self.views["eleve"].stop_global_polling()

        if "vie_scolaire" in self.views:
            self.views["vie_scolaire"].stop_global_polling()

        if self.current_view and self.current_view in self.views:
            vue = self.views[self.current_view]
            if hasattr(vue, "_stop_auto_refresh"):
                vue._stop_auto_refresh()

        self.destroy()


if __name__ == "__main__":
    app = Acceuil()
    app.mainloop()