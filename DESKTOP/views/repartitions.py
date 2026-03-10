"""
Module Repartitions — Affectation des élèves acceptés dans des classes réelles.

Séparation claire :
  __init__         → construction des widgets UNIQUEMENT
  refresh()        → vide + requêtes SQL + remplit (appelé par main.py)
  _poll_database() → polling silencieux toutes les 10 s

Pourquoi pas asyncio ?
  Même raison que EleveView : Tkinter n'est pas thread-safe.
  after() de Tkinter est la bonne solution — il s'exécute dans la boucle
  principale, sans conflit, sans import supplémentaire.
"""

import time
from tkinter import Menu, messagebox, ttk
from customtkinter import *
from utils.constant import *
from data.db_manager import DbManager


class Repartitions(CTkFrame):

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master   = master
        self.Database = DbManager()
        self.configure(fg_color=BACKGROUND_LIGHT)

        # ── Référence au job after() pour le polling ──────────────────────────
        self._refresh_job = None

        # ── Variables Tkinter ─────────────────────────────────────────────────
        self.niveau_var         = StringVar()
        self.search_var         = StringVar()
        self.typesearch_var     = StringVar()
        self.nnbrClasse         = IntVar()
        self.id_var             = StringVar()
        self.matricule_var      = StringVar()
        self.nom_var            = StringVar()
        self.prenom_var         = StringVar()
        self.date_naissance_var = StringVar()
        self.addresse_var       = StringVar()
        self.classe_var         = StringVar()
        self.classrel_var       = StringVar()

        # ── Menus contextuels ─────────────────────────────────────────────────
        self.menu_treeC = Menu(self, tearoff=0)
        self.menu_treeC.add_command(label="Voir détails",  command=self.voir_details)
        self.menu_treeC.add_command(label="Modifier",      command=self.modifier_eleve)
        self.menu_treeC.add_command(label="Supprimer",     command=self.supprimer_eleve)

        # Menu contextuel dynamique (rempli selon le niveau de l'élève)
        self.menu_treeL = Menu(self, tearoff=0)

        # ══════════════════════════════════════════════════════════════════════
        # CONSTRUCTION DES WIDGETS  (aucune requête SQL ici)
        # ══════════════════════════════════════════════════════════════════════

        # ── Conteneur HAUT (deux colonnes égales) ─────────────────────────────
        frameHaut = CTkFrame(self, fg_color="transparent")
        frameHaut.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=(10, 5))
        frameHaut.grid_columnconfigure(0, weight=1, uniform="g1")
        frameHaut.grid_columnconfigure(1, weight=1, uniform="g1")
        frameHaut.grid_rowconfigure(0, weight=1)

        # ── Colonne gauche : formulaire d'affectation ─────────────────────────
        frameAction = CTkFrame(frameHaut, fg_color=BACKGROUND_LIGHT,
                               border_width=1, border_color=PRIMARY_BLUE)
        frameAction.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        CTkLabel(frameAction, text="Affectation", font=FONT_TITLE,
                 text_color=BACKGROUND_LIGHT, fg_color=PRIMARY_BLUE,
                 anchor=CENTER, height=30).pack(fill=X, side=TOP)

        content_frame = CTkFrame(frameAction, fg_color="transparent")
        content_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Ligne 1 : Niveau + bouton affectation multiple + entrée nombre de classes
        ligne1 = CTkFrame(content_frame, fg_color="transparent")
        ligne1.pack(fill=X, pady=(5, 10))

        CTkLabel(ligne1, text="Niveau scolaire", font=FONT_TITLE,
                 text_color=PRIMARY_BLUE).pack(side=LEFT, padx=(0, 10))

        self.class_combobox = CTkComboBox(
            ligne1, values=["6eme", "5eme", "4eme", "3eme"],
            variable=self.niveau_var, fg_color=FRAME_WHITE,
            text_color=PRIMARY_BLUE, font=FONT_NORMAL, width=120
        )
        self.class_combobox.pack(side=LEFT, padx=(0, 10))

        CTkButton(
            ligne1, text="Affectation Multiple", font=FONT_NORMAL,
            fg_color=SECONDARY_BLUE, text_color=BACKGROUND_LIGHT,
            hover_color=PRIMARY_BLUE, command=self.repartitionGlobal, height=35
        ).pack(side=LEFT, padx=(0, 10))

        self.nbrClasse = CTkEntry(
            ligne1, placeholder_text="Nbr Cls", font=FONT_NORMAL,
            text_color=PRIMARY_BLUE, fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE, width=80, textvariable=self.nnbrClasse
        )
        self.nbrClasse.pack(side=LEFT)

        # Séparateur
        CTkFrame(content_frame, height=2, fg_color=PRIMARY_BLUE,
                 corner_radius=0).pack(fill=X, pady=10)

        # Grille formulaire (4 colonnes : label | entry | label | entry)
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill=BOTH, expand=True)
        for i, w in enumerate([1, 2, 1, 2]):
            form_frame.grid_columnconfigure(i, weight=w, uniform="col")

        def lbl(parent, text, row, col):
            CTkLabel(parent, text=text, font=FONT_TITLE,
                     text_color=PRIMARY_BLUE).grid(
                row=row, column=col, padx=5, pady=5, sticky=W)

        def ent(parent, var, ph, row, col):
            e = CTkEntry(parent, placeholder_text=ph, font=FONT_NORMAL,
                         text_color=PRIMARY_BLUE, fg_color=FRAME_WHITE,
                         border_color=PRIMARY_BLUE, textvariable=var)
            e.grid(row=row, column=col, padx=5, pady=5, sticky=EW)
            return e

        lbl(form_frame, "Matricule:",   0, 0);  self.matricule_entry      = ent(form_frame, self.matricule_var,      "Matricule",   0, 1)
        lbl(form_frame, "Nom:",         0, 2);  self.nom_entry            = ent(form_frame, self.nom_var,            "Nom",         0, 3)
        lbl(form_frame, "Prénom:",      1, 0);  self.prenom_entry         = ent(form_frame, self.prenom_var,         "Prénom",      1, 1)
        lbl(form_frame, "Date Naiss:",  1, 2);  self.date_naissance_entry = ent(form_frame, self.date_naissance_var, "JJ/MM/AAAA",  1, 3)
        lbl(form_frame, "Adresse:",     2, 0);  self.addresse_entry       = ent(form_frame, self.addresse_var,       "Adresse",     2, 1)
        lbl(form_frame, "Classe:",      2, 2);  self.classe_entry         = ent(form_frame, self.classe_var,         "Classe",      2, 3)

        # Bouton réinitialiser
        buttons_frame = CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill=X, pady=(20, 5))
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        CTkButton(
            buttons_frame, text="Réinitialiser", font=FONT_NORMAL,
            fg_color=INFO_GRAY, text_color=BACKGROUND_LIGHT,
            hover_color="red", command=self.reinitialiser_champs,
            height=40, corner_radius=8
        ).grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        # ── Colonne droite : tableau des élèves acceptés ───────────────────────
        frameListeAccepted = CTkFrame(frameHaut, fg_color=BACKGROUND_LIGHT,
                                      border_width=1, border_color=PRIMARY_BLUE)
        frameListeAccepted.grid(row=0, column=1, sticky="nsew", padx=(2, 0))

        CTkLabel(frameListeAccepted, text="Liste des Élèves Acceptés",
                 font=FONT_TITLE, text_color=BACKGROUND_LIGHT,
                 fg_color=PRIMARY_BLUE, anchor=CENTER,
                 height=30).pack(fill=X, side=TOP)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview.Heading", background=PRIMARY_BLUE,
                        foreground=BACKGROUND_LIGHT, font=("Arial", 12, "bold"))
        style.configure("Treeview", background="white", foreground="black",
                        fieldbackground="lightgrey", font=("Arial", 11))
        style.map("Treeview",
                  background=[("selected", "skyblue")],
                  foreground=[("selected", "black")])

        tree_container = CTkFrame(frameListeAccepted, fg_color="transparent")
        tree_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        cols1 = ("id", "Matricule", "Nom", "Prenom", "Date Naissance", "Addresse", "Classe")
        self.TableListe = ttk.Treeview(tree_container, columns=cols1, show="headings")
        self.TableListe.heading("id",             text='')
        self.TableListe.heading("Matricule",      text='Matricule')
        self.TableListe.heading("Nom",            text='Nom')
        self.TableListe.heading("Prenom",         text='Prénom')
        self.TableListe.heading("Date Naissance", text='Date Naissance')
        self.TableListe.heading("Addresse",       text='Adresse')
        self.TableListe.heading("Classe",         text='Classe')

        self.TableListe.column("id",             width=0, stretch=False)
        self.TableListe.column("Matricule",      width=80,  minwidth=80)
        self.TableListe.column("Nom",            width=100, minwidth=80)
        self.TableListe.column("Prenom",         width=100, minwidth=80)
        self.TableListe.column("Date Naissance", width=100, minwidth=80)
        self.TableListe.column("Addresse",       width=150, minwidth=100)
        self.TableListe.column("Classe",         width=80,  minwidth=60)

        xscroll1 = ttk.Scrollbar(tree_container, orient=HORIZONTAL, command=self.TableListe.xview)
        yscroll1 = ttk.Scrollbar(tree_container, orient=VERTICAL,   command=self.TableListe.yview)
        self.TableListe.configure(xscrollcommand=xscroll1.set, yscrollcommand=yscroll1.set)
        self.TableListe.bind("<ButtonRelease-1>", self.getDonnerAccepted)
        self.TableListe.bind("<Button-3>",        self.afficher_menu_contextuel)

        self.TableListe.grid(row=0, column=0, sticky="nsew")
        xscroll1.grid(row=1, column=0, sticky="ew")
        yscroll1.grid(row=0, column=1, sticky="ns")

        # ── Conteneur BAS : tableau par classe réelle ──────────────────────────
        frame3 = CTkFrame(self, fg_color=BACKGROUND_LIGHT,
                          border_width=1, border_color=PRIMARY_BLUE)
        frame3.pack(side=BOTTOM, fill=BOTH, expand=True, padx=5, pady=(5, 10))

        CTkLabel(frame3, text="Liste Par Classe Réelle", font=FONT_TITLE,
                 text_color=BACKGROUND_LIGHT, fg_color=PRIMARY_BLUE,
                 anchor=CENTER, height=30).pack(fill=X, side=TOP)

        # Combobox des classes réelles (valeurs chargées dans refresh())
        self.classReelCombox = CTkComboBox(
            frame3, values=["Sélectionner une classe"],
            fg_color=BACKGROUND_LIGHT, text_color=PRIMARY_BLUE,
            font=FONT_NORMAL, command=self.afficherClasse
        )
        self.classReelCombox.pack(fill=X, side=LEFT, anchor=N)

        tree_container2 = CTkFrame(frame3, fg_color="transparent")
        tree_container2.pack(fill=BOTH, expand=True, padx=10, pady=10)
        tree_container2.grid_rowconfigure(0, weight=1)
        tree_container2.grid_columnconfigure(0, weight=1)

        cols2 = ("id", "Matricule", "Nom", "Prenom", "Date Naissance", "Addresse", "Classe Reel")
        self.TableListeClasse = ttk.Treeview(tree_container2, columns=cols2, show="headings")
        self.TableListeClasse.heading("id",             text='')
        self.TableListeClasse.heading("Matricule",      text='Matricule')
        self.TableListeClasse.heading("Nom",            text='Nom')
        self.TableListeClasse.heading("Prenom",         text='Prénom')
        self.TableListeClasse.heading("Date Naissance", text='Date Naissance')
        self.TableListeClasse.heading("Addresse",       text='Adresse')
        self.TableListeClasse.heading("Classe Reel",    text='Classe Réelle')

        self.TableListeClasse.column("id",             width=0, stretch=False)
        self.TableListeClasse.column("Matricule",      width=80,  minwidth=80)
        self.TableListeClasse.column("Nom",            width=100, minwidth=80)
        self.TableListeClasse.column("Prenom",         width=100, minwidth=80)
        self.TableListeClasse.column("Date Naissance", width=100, minwidth=80)
        self.TableListeClasse.column("Addresse",       width=150, minwidth=100)
        self.TableListeClasse.column("Classe Reel",    width=100, minwidth=80)

        xscroll2 = ttk.Scrollbar(tree_container2, orient=HORIZONTAL, command=self.TableListeClasse.xview)
        yscroll2 = ttk.Scrollbar(tree_container2, orient=VERTICAL,   command=self.TableListeClasse.yview)
        self.TableListeClasse.configure(xscrollcommand=xscroll2.set, yscrollcommand=yscroll2.set)
        self.TableListeClasse.bind("<Button-3>", self.afficher_menuC)

        self.TableListeClasse.grid(row=0, column=0, sticky="nsew")
        xscroll2.grid(row=1, column=0, sticky="ew")
        yscroll2.grid(row=0, column=1, sticky="ns")

        # ── Indicateur de dernière mise à jour ────────────────────────────────
        self._status_label = CTkLabel(
            self, text="⏳ En attente de données...",
            font=("Arial", 10), text_color="gray", fg_color=BACKGROUND_LIGHT
        )
        self._status_label.pack(side=BOTTOM, anchor=E, padx=10, pady=2)

    # ══════════════════════════════════════════════════════════════════════════
    # CHARGEMENT DES DONNÉES
    # ══════════════════════════════════════════════════════════════════════════

    def getAccepted(self):
        """Requête SQL + remplissage du Treeview des élèves acceptés non affectés."""
        if not self.Database.connection:
            return
        try:
            data = self.Database.GetEleveAccepted()
            # Vide UNE SEULE FOIS avant la boucle (bug corrigé)
            self.TableListe.delete(*self.TableListe.get_children())
            if data:
                for row in data:
                    self.TableListe.insert("", END, values=row)
            self._update_status()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de connexion : {e}")

    def refresh(self):
        """Appelé par main.py quand cette vue devient visible.
        Vide le formulaire, recharge les deux tableaux et le combobox,
        puis démarre le polling.
        """
        self.reinitialiser_champs()
        self.getAccepted()

        # Recharge la liste des classes réelles dans le combobox
        classes = self.Database.getClasseReel()
        self.classReelCombox.configure(
            values=classes if classes else ["Aucune classe"]
        )
        # Vide le tableau du bas (sera rempli au choix du combobox)
        self.TableListeClasse.delete(*self.TableListeClasse.get_children())

        self._start_auto_refresh()   # ← démarre la boucle de polling

    # ══════════════════════════════════════════════════════════════════════════
    # POLLING — rafraîchissement automatique toutes les 10 s
    # ══════════════════════════════════════════════════════════════════════════

    def _poll_database(self):
        """Requête silencieuse : vérifie les deux tableaux et le combobox.
        Ne rafraîchit QUE si les données ont réellement changé.
        Ne touche PAS au formulaire ni à la sélection en cours.
        """
        if not self.Database.connection:
            return
        try:
            # ── 1. Tableau des élèves acceptés non affectés ────────────────────
            nouvelles_datas = self.Database.GetEleveAccepted()
            ids_affiches = {
                self.TableListe.item(i, "values")[0]
                for i in self.TableListe.get_children()
            }
            ids_bdd = {str(row[0]) for row in nouvelles_datas} if nouvelles_datas else set()

            if ids_affiches != ids_bdd:
                self.TableListe.delete(*self.TableListe.get_children())
                if nouvelles_datas:
                    for row in nouvelles_datas:
                        self.TableListe.insert("", END, values=row)

            # ── 2. Combobox des classes réelles ───────────────────────────────
            classes_actuelles = set(self.classReelCombox.cget("values"))
            classes_bdd       = set(self.Database.getClasseReel())
            if classes_actuelles != classes_bdd:
                self.classReelCombox.configure(
                    values=list(classes_bdd) if classes_bdd else ["Aucune classe"]
                )

            self._update_status()

        except Exception:
            # Silencieux : pas de popup toutes les 10 s
            pass

    def _start_auto_refresh(self):
        """Démarre le polling. Annule d'abord tout job existant."""
        self._stop_auto_refresh()
        self._auto_refresh()

    def _auto_refresh(self):
        """Interroge la BDD puis se replanifie dans 10 secondes (via after)."""
        self._poll_database()
        self._refresh_job = self.after(10_000, self._auto_refresh)

    def _stop_auto_refresh(self):
        """Stoppe le polling quand la vue est cachée."""
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None

    def _update_status(self):
        """Met à jour l'horodatage de la dernière synchronisation."""
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self._status_label.configure(text=f"✅ Dernière mise à jour : {now}")

    # ══════════════════════════════════════════════════════════════════════════
    # ÉVÉNEMENTS TREEVIEW
    # ══════════════════════════════════════════════════════════════════════════

    def getDonnerAccepted(self, ev):
        """Remplit le formulaire avec la ligne sélectionnée."""
        selected = self.TableListe.focus()
        try:
            values = self.TableListe.item(selected, 'values')
            self.id_var.set(values[0])
            self.matricule_var.set(values[1])
            self.nom_var.set(values[2])
            self.prenom_var.set(values[3])
            self.date_naissance_var.set(str(values[4]))
            self.addresse_var.set(values[5])
            self.classe_var.set(values[6])
        except IndexError:
            pass

    def afficherClasse(self, value):
        """Charge les élèves de la classe sélectionnée dans le combobox."""
        if not self.Database.connection:
            return
        try:
            classe_reel = self.classReelCombox.get()
            data = self.Database.GetEleveByClasse(classe_reel)
            self.TableListeClasse.delete(*self.TableListeClasse.get_children())
            if data:
                for row in data:
                    self.TableListeClasse.insert("", END, values=row)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de connexion : {e}")

    def afficher_menuC(self, event):
        """Menu contextuel clic droit sur le tableau des classes."""
        item = self.TableListeClasse.identify_row(event.y)
        if item:
            self.TableListeClasse.selection_set(item)
            self.selected_item = self.TableListeClasse.item(item, "values")
            self.menu_treeC.tk_popup(event.x_root, event.y_root)

    def afficher_menu_contextuel(self, event):
        """Menu contextuel dynamique clic droit sur le tableau des acceptés.
        Propose d'affecter l'élève dans les classes A/B/C/D de son niveau.
        """
        item_id = self.TableListe.identify_row(event.y)
        if not item_id:
            return
        self.TableListe.selection_set(item_id)
        self.selected_item = self.TableListe.item(item_id, 'values')

        self.menu_treeL.delete(0, END)
        niveau = self.selected_item[6]   # colonne Classe = niveau (ex: "6eme")

        for lettre in ["A", "B", "C", "D"]:
            nom_classe = f"{niveau} {lettre}"
            self.menu_treeL.add_command(
                label=f"Affecter en {nom_classe}",
                command=lambda c=nom_classe: self.Database.affectation_individuel(
                    c, self.selected_item, self.getAccepted
                )
            )
        self.menu_treeL.post(event.x_root, event.y_root)

    # ══════════════════════════════════════════════════════════════════════════
    # ACTIONS BOUTONS
    # ══════════════════════════════════════════════════════════════════════════

    def repartitionGlobal(self):
        """Répartition automatique (round-robin) pour le niveau sélectionné."""
        niveau = self.niveau_var.get().upper()
        if not niveau:
            messagebox.showwarning("Attention", "Veuillez sélectionner un niveau.")
            return
        try:
            nb = int(self.nnbrClasse.get())
        except (ValueError, TypeError):
            messagebox.showwarning("Attention", "Veuillez entrer un nombre de classes valide.")
            return

        if self.Database.connection:
            self.Database.affectation_global(niveau=niveau, nb=nb)
            self.getAccepted()
            self.reinitialiser_champs()
            classes = self.Database.getClasseReel()
            self.classReelCombox.configure(values=classes if classes else ["Aucune classe"])

    def reinitialiser_champs(self):
        """Vide tous les champs du formulaire."""
        for var in (self.matricule_var, self.nom_var, self.prenom_var,
                    self.date_naissance_var, self.addresse_var, self.classe_var):
            var.set("")
        self.niveau_var.set("")
        self.nnbrClasse.set(0)

    # ══════════════════════════════════════════════════════════════════════════
    # MENU CONTEXTUEL — actions
    # ══════════════════════════════════════════════════════════════════════════

    def voir_details(self):
        if hasattr(self, 'selected_item'):
            messagebox.showinfo("Détails", str(self.selected_item))

    def modifier_eleve(self):
        if hasattr(self, 'selected_item'):
            print("Modifier :", self.selected_item)

    def supprimer_eleve(self):
        if hasattr(self, 'selected_item'):
            confirm = messagebox.askyesno(
                "Confirmation", "Voulez-vous vraiment supprimer cet élève ?"
            )
            if confirm:
                print("Supprimer :", self.selected_item)