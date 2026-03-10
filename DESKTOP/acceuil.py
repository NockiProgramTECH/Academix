"""
Module Acceuil — Fenêtre principale de l'application Academix.

Rôle :
  - Construit le header, la sidebar et la zone de contenu.
  - Pré-crée TOUTES les vues une seule fois au démarrage (perf).
  - Gère la navigation entre les vues via show_view().
  - Polling des notifications (badge rouge) toutes les 30 s via after().

Pourquoi after() et non asyncio/threading pour les notifications ?
  Tkinter n'est pas thread-safe : modifier un widget depuis un thread
  secondaire provoque des crashs aléatoires. after() s'exécute dans la
  boucle principale Tkinter → aucun risque, aucun import supplémentaire.
"""

import pathlib
from tkinter import messagebox
from customtkinter import *
from utils.constant import *
from PIL import Image, ImageTk
from data.db_manager import DbManager

IMAGE_DIR = pathlib.Path(__file__).parent / "images"


class Acceuil(CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}-1+0")
        self.title("Academix")
        self._set_appearance_mode("light")
        self.Database = DbManager()

        self.images = {}                 # stocke les CTkImage pour éviter le GC
        self._notif_job  = None          # job after() pour le badge notifications
        self.views        = {}           # dict {nom: CTkFrame}
        self.current_view = None         # clé de la vue actuellement affichée

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

        # Badge notifications (mis à jour toutes les 30 s)
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

        # Configuration des boutons de la sidebar
        # Pour ajouter une nouvelle vue : ajouter une entrée ici + _create_*_view()
        BTN = {
            1: {
                "text":    "Gestion Des Élèves",
                "command": lambda: self.show_view("eleve"),
                "image":   ""
            },
            2: {
                "text":    "Affectation Par Classe",
                "command": lambda: self.show_view("repartitions"),
                "image":   ""
            },
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
        # ZONE DE CONTENU (à droite de la sidebar)
        # ══════════════════════════════════════════════════════════════════════
        self.mainFrame = CTkFrame(self, fg_color=BACKGROUND_LIGHT,
                                  bg_color=BACKGROUND_LIGHT)
        self.mainFrame.pack(fill=BOTH, side=LEFT, expand=True)

        # ══════════════════════════════════════════════════════════════════════
        # PRÉ-CRÉATION DES VUES (widgets construits UNE SEULE FOIS)
        # Les données sont chargées par refresh() au premier show_view()
        # ══════════════════════════════════════════════════════════════════════
        self._create_eleve_view()
        self._create_repartitions_view()

        # ── Démarrage ─────────────────────────────────────────────────────────
        # Affiche la vue par défaut au lancement
        self.show_view("eleve")

        # Démarre le badge de notifications (toutes les 30 s)
        # Pourquoi 30 s et non 10 s ? Les inscriptions arrivent moins vite
        # que les changements d'affectation → 30 s est un bon compromis perf/réactivité.
        self._start_notification_polling()

        # Nettoie proprement les jobs after() à la fermeture de la fenêtre
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ══════════════════════════════════════════════════════════════════════════
    # CRÉATION DES VUES
    # ══════════════════════════════════════════════════════════════════════════

    def _create_eleve_view(self):
        """Instancie EleveView dans mainFrame et la cache immédiatement.
        Les données seront chargées au premier show_view('eleve').
        """
        from views.eleves import EleveView
        view = EleveView(self.mainFrame)
        view.pack_forget()          # cachée par défaut
        self.views["eleve"] = view

    def _create_repartitions_view(self):
        """Instancie Repartitions dans mainFrame et la cache immédiatement."""
        from views.repartitions import Repartitions
        view = Repartitions(self.mainFrame)
        view.pack_forget()
        self.views["repartitions"] = view

    # ══════════════════════════════════════════════════════════════════════════
    # NAVIGATION ENTRE LES VUES
    # ══════════════════════════════════════════════════════════════════════════

    def show_view(self, view_name: str):
        """Affiche une vue et recharge ses données via refresh().

        Workflow :
          1. Vérifie que la vue existe dans self.views
          2. Stoppe le polling de la vue quittée  (_stop_auto_refresh)
          3. Cache la vue courante               (pack_forget)
          4. Affiche la nouvelle vue             (pack)
          5. Appelle refresh() → données fraîches + démarre le polling

        Args:
            view_name: clé dans self.views ("eleve", "repartitions", ...)
        """
        if view_name not in self.views:
            print(f"[WARN] Vue introuvable : '{view_name}'")
            return

        # ── Quitter la vue actuelle ────────────────────────────────────────────
        if self.current_view and self.current_view in self.views:
            vue_quittee = self.views[self.current_view]

            # Stoppe le polling AVANT de cacher → aucune requête inutile en fond
            if hasattr(vue_quittee, "_stop_auto_refresh"):
                vue_quittee._stop_auto_refresh()

            vue_quittee.pack_forget()

        # ── Afficher la nouvelle vue ──────────────────────────────────────────
        self.views[view_name].pack(fill=BOTH, expand=True)
        self.current_view = view_name

        # ── Recharger les données (refresh démarre aussi le polling) ──────────
        if hasattr(self.views[view_name], "refresh"):
            self.views[view_name].refresh()
        else:
            print(f"[WARN] La vue '{view_name}' n'a pas de méthode refresh()")

    # ══════════════════════════════════════════════════════════════════════════
    # RACCOURCIS (compatibilité avec les anciens appels)
    # ══════════════════════════════════════════════════════════════════════════

    def show_eleve_view(self):
        self.show_view("eleve")

    def show_repartitions_view(self):
        self.show_view("repartitions")

    # ══════════════════════════════════════════════════════════════════════════
    # BADGE NOTIFICATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def showNotifications(self):
        """Met à jour le badge avec le nombre de dossiers EN_ATTENTE.
        Silencieux : pas de popup si la requête échoue.
        """
        try:
            if self.Database.connection:
                data = self.Database.refresh_pending_list()
                count = len(data) if data else 0
                # Couleur rouge si dossiers en attente, gris sinon
                color = "red" if count > 0 else "gray"
                self.notificationLabel.configure(
                    text=str(count), text_color=color
                )
        except Exception:
            pass   # silencieux, on réessaiera dans 30 s

    def _start_notification_polling(self):
        """Démarre le polling des notifications (toutes les 30 s)."""
        self.showNotifications()         # premier appel immédiat
        self._notif_job = self.after(30_000, self._start_notification_polling)

    def _stop_notification_polling(self):
        """Stoppe le polling des notifications."""
        if self._notif_job is not None:
            self.after_cancel(self._notif_job)
            self._notif_job = None

    # ══════════════════════════════════════════════════════════════════════════
    # FERMETURE PROPRE
    # ══════════════════════════════════════════════════════════════════════════

    def _on_close(self):
        """Annule TOUS les jobs after() avant de fermer pour éviter les erreurs
        'invalid command name' que Tkinter lève quand after() se déclenche
        après destruction de la fenêtre.
        """
        # Stoppe les notifications
        self._stop_notification_polling()

        # Stoppe le polling de la vue active
        if self.current_view and self.current_view in self.views:
            vue = self.views[self.current_view]
            if hasattr(vue, "_stop_auto_refresh"):
                vue._stop_auto_refresh()

        self.destroy()


if __name__ == "__main__":
    app = Acceuil()
    app.mainloop()