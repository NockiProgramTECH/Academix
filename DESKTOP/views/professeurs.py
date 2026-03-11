"""
Module Professeurs — Gestion complète des professeurs et leurs affectations.

CORRECTIONS APPLIQUÉES :
  1. Accepte db= en paramètre (instance partagée depuis Acceuil)
  2. refresh() vide systématiquement les Treeviews avant toute requête SQL
  3. _start_auto_refresh() annule le job précédent → pas de doublons de polling
"""

import datetime
from tkinter import Menu, messagebox, ttk
from customtkinter import *
from utils.constant import *
from data.db_manager import DbManager


class ProfesseursView(CTkFrame):

    # CORRECTION 1 : accepte db= (instance partagée) en paramètre optionnel
    def __init__(self, master, db: DbManager = None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master

        # CORRECTION 1 : utilise l'instance partagée si fournie
        self.Database = db if db is not None else DbManager()

        self.configure(fg_color=BACKGROUND_LIGHT)

        self._refresh_job = None

        self.id_var = StringVar()
        self.matricule_var = StringVar()
        self.nom_var = StringVar()
        self.prenom_var = StringVar()
        self.telephone_var = StringVar()
        self.specialite_var = StringVar()
        self.statut_var = StringVar(value="Permanent")
        self.email_var = StringVar()
        self.password_var = StringVar()

        self.search_var = StringVar()
        self.search_type_var = StringVar(value="nom")

        self.selected_prof_id = None
        self.selected_prof_nom = None
        self.affectation_classe_var = StringVar()
        self.affectation_matiere_var = StringVar()

        self._create_context_menus()

        # ── Titre de la vue ───────────────────────────────────────────────────
        title_frame = CTkFrame(self, fg_color=PRIMARY_BLUE, height=50, corner_radius=0)
        title_frame.pack(fill=X, side=TOP)
        title_frame.pack_propagate(False)

        CTkLabel(
            title_frame,
            text="Gestion des Professeurs",
            font=FONT_H1,
            text_color=BACKGROUND_LIGHT,
            fg_color=PRIMARY_BLUE
        ).pack(expand=True)

        main_container = CTkFrame(self, fg_color="transparent")
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)

        main_container.grid_columnconfigure(0, weight=6)
        main_container.grid_columnconfigure(1, weight=4)
        main_container.grid_rowconfigure(0, weight=1)

        left_panel = CTkFrame(main_container, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_panel.grid_rowconfigure(0, weight=2)
        left_panel.grid_rowconfigure(1, weight=3)
        left_panel.grid_columnconfigure(0, weight=1)

        self._create_professeurs_table(left_panel)
        self._create_affectations_table(left_panel)

        right_panel = CTkFrame(main_container, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        self._create_professeur_form(right_panel)
        self._create_affectation_form(right_panel)

        self._status_label = CTkLabel(
            self,
            text="⏳ En attente de données...",
            font=("Arial", 10),
            text_color="gray",
            fg_color=BACKGROUND_LIGHT
        )
        self._status_label.pack(side=BOTTOM, anchor=E, padx=10, pady=2)

    # ══════════════════════════════════════════════════════════════════════════
    # CRÉATION DES COMPOSANTS INTERFACE
    # ══════════════════════════════════════════════════════════════════════════

    def _create_context_menus(self):
        self.menu_prof = Menu(self, tearoff=0)
        self.menu_prof.add_command(label="✏️ Modifier", command=self._edit_selected_prof)
        self.menu_prof.add_command(label="🗑️ Supprimer", command=self._delete_selected_prof)
        self.menu_prof.add_separator()
        self.menu_prof.add_command(label="📋 Voir détails", command=self._show_prof_details)
        self.menu_prof.add_command(label="🔗 Affectations", command=self._show_prof_affectations)

        self.menu_affect = Menu(self, tearoff=0)
        self.menu_affect.add_command(label="❌ Supprimer affectation", command=self._delete_affectation)

    def _create_professeurs_table(self, parent):
        table_frame = CTkFrame(parent, fg_color=BACKGROUND_LIGHT,
                               border_width=1, border_color=PRIMARY_BLUE)
        table_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        CTkLabel(
            table_frame,
            text="Liste des Professeurs",
            font=FONT_TITLE,
            text_color=BACKGROUND_LIGHT,
            fg_color=PRIMARY_BLUE,
            anchor=CENTER,
            height=30
        ).grid(row=0, column=0, sticky="ew")

        search_frame = CTkFrame(table_frame, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        search_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(search_frame, text="Rechercher:", font=FONT_NORMAL, text_color=PRIMARY_BLUE).grid(row=0, column=0, padx=(0, 5))

        self.search_entry = CTkEntry(
            search_frame,
            placeholder_text="Tapez pour rechercher...",
            textvariable=self.search_var,
            font=FONT_NORMAL,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE,
            text_color=PRIMARY_BLUE
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        self.search_var.trace('w', lambda *args: self._filter_professeurs())

        self.search_combo = CTkComboBox(
            search_frame,
            values=["nom", "prenom", "matricule", "specialite"],
            variable=self.search_type_var,
            width=120,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE
        )
        self.search_combo.grid(row=0, column=2, padx=(0, 5))

        CTkButton(
            search_frame,
            text="↺",
            width=30,
            fg_color=SECONDARY_BLUE,
            hover_color=PRIMARY_BLUE,
            command=self.refresh
        ).grid(row=0, column=3)

        tree_container = CTkFrame(table_frame, fg_color="transparent")
        tree_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview.Heading",
                        background=PRIMARY_BLUE,
                        foreground=BACKGROUND_LIGHT,
                        font=("Arial", 12, "bold"))
        style.configure("Treeview",
                        background="white",
                        foreground="black",
                        fieldbackground="lightgrey",
                        font=("Arial", 11))
        style.map("Treeview",
                  background=[("selected", ACCENT_BLUE)],
                  foreground=[("selected", "white")])

        columns = ("id", "matricule", "nom", "prenom", "telephone", "specialite", "statut", "email")
        self.tree_prof = ttk.Treeview(tree_container, columns=columns, show="headings", height=8)

        self.tree_prof.heading("id", text="ID")
        self.tree_prof.heading("matricule", text="Matricule")
        self.tree_prof.heading("nom", text="Nom")
        self.tree_prof.heading("prenom", text="Prénom")
        self.tree_prof.heading("telephone", text="Téléphone")
        self.tree_prof.heading("specialite", text="Spécialité")
        self.tree_prof.heading("statut", text="Statut")
        self.tree_prof.heading("email", text="Email")

        self.tree_prof.column("id", width=0, stretch=False)
        self.tree_prof.column("matricule", width=100, minwidth=80)
        self.tree_prof.column("nom", width=120, minwidth=80)
        self.tree_prof.column("prenom", width=120, minwidth=80)
        self.tree_prof.column("telephone", width=100, minwidth=80)
        self.tree_prof.column("specialite", width=150, minwidth=100)
        self.tree_prof.column("statut", width=80, minwidth=60)
        self.tree_prof.column("email", width=150, minwidth=100)

        xscroll = ttk.Scrollbar(tree_container, orient=HORIZONTAL, command=self.tree_prof.xview)
        yscroll = ttk.Scrollbar(tree_container, orient=VERTICAL, command=self.tree_prof.yview)
        self.tree_prof.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        self.tree_prof.bind("<ButtonRelease-1>", self._on_prof_select)
        self.tree_prof.bind("<Button-3>", self._show_prof_context_menu)

        self.tree_prof.grid(row=0, column=0, sticky="nsew")
        xscroll.grid(row=1, column=0, sticky="ew")
        yscroll.grid(row=0, column=1, sticky="ns")

    def _create_affectations_table(self, parent):
        table_frame = CTkFrame(parent, fg_color=BACKGROUND_LIGHT,
                               border_width=1, border_color=PRIMARY_BLUE)
        table_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        CTkLabel(
            table_frame,
            text="Affectations Actuelles",
            font=FONT_TITLE,
            text_color=BACKGROUND_LIGHT,
            fg_color=PRIMARY_BLUE,
            anchor=CENTER,
            height=30
        ).grid(row=0, column=0, sticky="ew")

        tree_container = CTkFrame(table_frame, fg_color="transparent")
        tree_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        columns = ("id", "professeur", "matiere", "classe")
        self.tree_affect = ttk.Treeview(tree_container, columns=columns, show="headings", height=6)

        self.tree_affect.heading("id", text="ID")
        self.tree_affect.heading("professeur", text="Professeur")
        self.tree_affect.heading("matiere", text="Matière")
        self.tree_affect.heading("classe", text="Classe")

        self.tree_affect.column("id", width=0, stretch=False)
        self.tree_affect.column("professeur", width=200, minwidth=150)
        self.tree_affect.column("matiere", width=150, minwidth=100)
        self.tree_affect.column("classe", width=150, minwidth=100)

        xscroll = ttk.Scrollbar(tree_container, orient=HORIZONTAL, command=self.tree_affect.xview)
        yscroll = ttk.Scrollbar(tree_container, orient=VERTICAL, command=self.tree_affect.yview)
        self.tree_affect.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        self.tree_affect.bind("<Button-3>", self._show_affect_context_menu)

        self.tree_affect.grid(row=0, column=0, sticky="nsew")
        xscroll.grid(row=1, column=0, sticky="ew")
        yscroll.grid(row=0, column=1, sticky="ns")

    def _create_professeur_form(self, parent):
        form_frame = CTkFrame(parent, fg_color=BACKGROUND_LIGHT,
                              border_width=1, border_color=PRIMARY_BLUE)
        form_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        form_frame.grid_rowconfigure(7, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(
            form_frame,
            text="📝 Formulaire Professeur",
            font=FONT_TITLE,
            text_color=BACKGROUND_LIGHT,
            fg_color=PRIMARY_BLUE,
            anchor=CENTER,
            height=30
        ).grid(row=0, column=0, columnspan=2, sticky="ew")

        labels = ["Matricule:", "Nom:", "Prénom:", "Téléphone:", "Spécialité:", "Statut:", "Email:"]
        vars = [self.matricule_var, self.nom_var, self.prenom_var,
                self.telephone_var, self.specialite_var, self.statut_var, self.email_var]
        placeholders = ["PROF-2024-001", "Dupont", "Jean", "01 23 45 67 89", "Mathématiques", "", "email@exemple.com"]

        for i, (label, var, placeholder) in enumerate(zip(labels, vars, placeholders), start=1):
            CTkLabel(form_frame, text=label, font=FONT_NORMAL,
                     text_color=PRIMARY_BLUE).grid(row=i, column=0, padx=10, pady=5, sticky=W)

            if label == "Statut:":
                CTkComboBox(
                    form_frame,
                    values=["Permanent", "Vacataire"],
                    variable=var,
                    font=FONT_NORMAL,
                    fg_color=FRAME_WHITE,
                    border_color=PRIMARY_BLUE,
                    width=200,
                    text_color=PRIMARY_BLUE,
                    dropdown_fg_color=FRAME_WHITE,
                ).grid(row=i, column=1, padx=10, pady=5, sticky=EW)
            else:
                CTkEntry(
                    form_frame,
                    placeholder_text=placeholder,
                    textvariable=var,
                    font=FONT_NORMAL,
                    fg_color=FRAME_WHITE,
                    border_color=PRIMARY_BLUE,
                    text_color=PRIMARY_BLUE,
                ).grid(row=i, column=1, padx=10, pady=5, sticky=EW)

        button_frame = CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=8, column=0, columnspan=2, pady=15)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        CTkButton(
            button_frame, text="💾 Ajouter", font=FONT_NORMAL,
            fg_color=SUCCESS_GREEN, text_color=BACKGROUND_LIGHT,
            hover_color=PRIMARY_BLUE, command=self.add_professeur,
            width=120, height=35
        ).grid(row=0, column=0, padx=5)

        CTkButton(
            button_frame, text="🔄 Modifier", font=FONT_NORMAL,
            fg_color=WARNING_ORANGE, text_color=BACKGROUND_LIGHT,
            hover_color=PRIMARY_BLUE, command=self.update_professeur,
            width=120, height=35
        ).grid(row=0, column=1, padx=5)

        CTkButton(
            button_frame, text="🗑️ Supprimer", font=FONT_NORMAL,
            fg_color=DANGER_RED, text_color=BACKGROUND_LIGHT,
            hover_color=PRIMARY_BLUE, command=self.delete_professeur,
            width=120, height=35
        ).grid(row=1, column=0, padx=5, pady=5)

        CTkButton(
            button_frame, text="🧹 Réinitialiser", font=FONT_NORMAL,
            fg_color=INFO_GRAY, text_color=BACKGROUND_LIGHT,
            hover_color=PRIMARY_BLUE, command=self._clear_form,
            width=120, height=35
        ).grid(row=1, column=1, padx=5, pady=5)

    def _create_affectation_form(self, parent):
        form_frame = CTkFrame(parent, fg_color=BACKGROUND_LIGHT,
                              border_width=1, border_color=PRIMARY_BLUE)
        form_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        form_frame.grid_rowconfigure(4, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(
            form_frame,
            text="🔗 Affectation Classe/Matière",
            font=FONT_TITLE,
            text_color=BACKGROUND_LIGHT,
            fg_color=PRIMARY_BLUE,
            anchor=CENTER,
            height=30
        ).grid(row=0, column=0, columnspan=2, sticky="ew")

        CTkLabel(form_frame, text="Professeur:", font=FONT_NORMAL,
                 text_color=PRIMARY_BLUE).grid(row=1, column=0, padx=10, pady=5, sticky=W)

        self.selected_prof_label = CTkLabel(
            form_frame,
            text="Aucun professeur sélectionné",
            font=FONT_NORMAL,
            text_color=TEXT_MUTED,
            anchor=W
        )
        self.selected_prof_label.grid(row=1, column=1, padx=10, pady=5, sticky=EW)

        CTkLabel(form_frame, text="Classe:", font=FONT_NORMAL,
                 text_color=PRIMARY_BLUE).grid(row=2, column=0, padx=10, pady=5, sticky=W)

        self.classe_combo = CTkComboBox(
            form_frame,
            values=["Chargement..."],
            variable=self.affectation_classe_var,
            font=FONT_NORMAL,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE
        )
        self.classe_combo.grid(row=2, column=1, padx=10, pady=5, sticky=EW)

        CTkLabel(form_frame, text="Matière:", font=FONT_NORMAL,
                 text_color=PRIMARY_BLUE).grid(row=3, column=0, padx=10, pady=5, sticky=W)

        self.matiere_combo = CTkComboBox(
            form_frame,
            values=["Chargement..."],
            variable=self.affectation_matiere_var,
            font=FONT_NORMAL,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE
        )
        self.matiere_combo.grid(row=3, column=1, padx=10, pady=5, sticky=EW)

        CTkButton(
            form_frame,
            text="✅ Enregistrer l'affectation",
            font=FONT_NORMAL,
            fg_color=SUCCESS_GREEN,
            text_color=BACKGROUND_LIGHT,
            hover_color=PRIMARY_BLUE,
            command=self._save_affectation,
            height=40
        ).grid(row=4, column=0, columnspan=2, pady=15, padx=20, sticky=EW)

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTHODES DE RAFRAÎCHISSEMENT DES DONNÉES
    # ══════════════════════════════════════════════════════════════════════════

    def refresh(self):
        """Appelé par Acceuil.show_view() à chaque changement de vue.
        CORRECTION 2 : vide les Treeviews AVANT les requêtes SQL.
        CORRECTION 5 : _start_auto_refresh() annule le job précédent.
        """
        # CORRECTION 2 : vider les tableaux avant de charger les nouvelles données
        self.tree_prof.delete(*self.tree_prof.get_children())
        self.tree_affect.delete(*self.tree_affect.get_children())

        self.load_professeurs()
        self.load_affectations()
        self.load_classes()
        self.load_matieres()
        self._start_auto_refresh()
        self._update_status("Données actualisées")

    def load_professeurs(self):
        """Charge la liste des professeurs depuis la base de données.
        CORRECTION 2 : delete() systématique avant toute insertion.
        """
        if not self.Database.connection:
            return
        try:
            data = self.Database._load_professeurs()
            # CORRECTION 2 : vider avant d'insérer
            self.tree_prof.delete(*self.tree_prof.get_children())
            if data:
                for row in data:
                    self.tree_prof.insert("", END, values=row)
        except Exception as e:
            print(f"Erreur chargement professeurs: {e}")
            messagebox.showerror("Erreur", f"Impossible de charger les professeurs: {e}")

    def load_affectations(self):
        """Charge la liste des affectations.
        CORRECTION 2 : delete() systématique avant toute insertion.
        """
        if not self.Database.connection:
            return
        try:
            data = self.Database._load_affectations()
            # CORRECTION 2 : vider avant d'insérer
            self.tree_affect.delete(*self.tree_affect.get_children())
            if data:
                for row in data:
                    self.tree_affect.insert("", END, values=row)
        except Exception as e:
            print(f"Erreur chargement affectations: {e}")

    def load_classes(self):
        """Charge la liste des classes pour le combobox."""
        if not self.Database.connection:
            return
        try:
            data = self.Database._load_classes()
            classes = [row[0] for row in data] if data else ["Aucune classe"]
            self.classe_combo.configure(values=classes)
        except Exception as e:
            print(f"Erreur chargement classes: {e}")

    def load_matieres(self):
        """Charge la liste des matières pour le combobox."""
        if not self.Database.connection:
            return
        try:
            data = self.Database._load_matieres()
            matieres = [row[0] for row in data] if data else ["Aucune matière"]
            self.matiere_combo.configure(values=matieres)
        except Exception as e:
            print(f"Erreur chargement matières: {e}")

    def _filter_professeurs(self):
        """Filtre le tableau des professeurs en fonction de la recherche."""
        search_term = self.search_var.get().lower()
        search_type = self.search_type_var.get()

        if not search_term:
            self.load_professeurs()
            return

        all_items = []
        for item in self.tree_prof.get_children():
            values = self.tree_prof.item(item, 'values')
            all_items.append((item, values))

        col_map = {'nom': 2, 'prenom': 3, 'matricule': 1, 'specialite': 5}
        col_index = col_map.get(search_type, 2)

        for item, values in all_items:
            if col_index < len(values) and search_term in str(values[col_index]).lower():
                self.tree_prof.reattach(item, '', 0)
            else:
                self.tree_prof.detach(item)

    # ══════════════════════════════════════════════════════════════════════════
    # POLLING AUTOMATIQUE
    # ══════════════════════════════════════════════════════════════════════════

    def _start_auto_refresh(self):
        """Démarre le rafraîchissement automatique toutes les 10 secondes.
        CORRECTION 5 : annule le job précédent avant d'en créer un nouveau.
        """
        self._stop_auto_refresh()   # CORRECTION 5
        self._auto_refresh()

    def _auto_refresh(self):
        """Fonction de rafraîchissement automatique."""
        if self.Database.connection:
            self._poll_database()
        self._refresh_job = self.after(10000, self._auto_refresh)

    def _stop_auto_refresh(self):
        """Arrête le rafraîchissement automatique."""
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None

    def _poll_database(self):
        """Vérifie silencieusement si les données ont changé."""
        try:
            cursor = self.Database.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM Professeur")
            new_count = cursor.fetchone()[0]
            cursor.close()

            current_count = len(self.tree_prof.get_children())

            if new_count != current_count:
                self.load_professeurs()
                self._update_status("Mise à jour automatique")

            self.load_affectations()

        except Exception:
            pass  # Silencieux

    def _update_status(self, message):
        """Met à jour le label de statut avec l'heure."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self._status_label.configure(text=f"✅ {message} - {now}")

    # ══════════════════════════════════════════════════════════════════════════
    # GESTION DES ÉVÉNEMENTS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_prof_select(self, event):
        """Remplit le formulaire avec les données du professeur sélectionné."""
        selected = self.tree_prof.focus()
        if not selected:
            return

        values = self.tree_prof.item(selected, 'values')
        if values:
            self.id_var.set(values[0])
            self.matricule_var.set(values[1])
            self.nom_var.set(values[2])
            self.prenom_var.set(values[3])
            self.telephone_var.set(values[4])
            self.specialite_var.set(values[5])
            self.statut_var.set(values[6])
            self.email_var.set(values[7])

            self.selected_prof_id = values[0]
            self.selected_prof_nom = f"{values[2]} {values[3]}"
            self.selected_prof_label.configure(
                text=self.selected_prof_nom,
                text_color=PRIMARY_BLUE
            )

    def _show_prof_context_menu(self, event):
        item = self.tree_prof.identify_row(event.y)
        if item:
            self.tree_prof.selection_set(item)
            self.menu_prof.tk_popup(event.x_root, event.y_root)

    def _show_affect_context_menu(self, event):
        item = self.tree_affect.identify_row(event.y)
        if item:
            self.tree_affect.selection_set(item)
            self.menu_affect.tk_popup(event.x_root, event.y_root)

    # ══════════════════════════════════════════════════════════════════════════
    # OPÉRATIONS CRUD PROFESSEURS
    # ══════════════════════════════════════════════════════════════════════════

    def add_professeur(self):
        if not self.nom_var.get() or not self.prenom_var.get():
            messagebox.showwarning("Attention", "Le nom et le prénom sont obligatoires.")
            return
        if not self.matricule_var.get():
            messagebox.showwarning("Attention", "Le matricule est obligatoire.")
            return

        try:
            self.Database._add_professeur(
                matricule=self.matricule_var.get(),
                nom=self.nom_var.get(),
                prenom=self.prenom_var.get(),
                telephone=self.telephone_var.get() or None,
                specialite=self.specialite_var.get() or None,
                statut=self.statut_var.get(),
                email=self.email_var.get() or None,
            )
            self._clear_form()
            # CORRECTION 2 : recharger après écriture
            self.load_professeurs()

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ajouter le professeur: {e}")

    def update_professeur(self):
        if not self.id_var.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner un professeur à modifier.")
            return

        try:
            self.Database._update_professeur(
                id=self.id_var.get(),
                matricule=self.matricule_var.get(),
                nom=self.nom_var.get(),
                prenom=self.prenom_var.get(),
                telephone=self.telephone_var.get() or None,
                specialite=self.specialite_var.get() or None,
                statut=self.statut_var.get(),
                email=self.email_var.get() or None,
            )
            self._clear_form()
            # CORRECTION 2 : recharger après écriture
            self.load_professeurs()

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier le professeur: {e}")

    def delete_professeur(self):
        if not self.id_var.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner un professeur à supprimer.")
            return

        if not messagebox.askyesno("Confirmation",
                                   f"Voulez-vous vraiment supprimer {self.nom_var.get()} {self.prenom_var.get()} ?\n"
                                   "Toutes ses affectations seront également supprimées."):
            return

        try:
            self.Database._delete_professeur(id=self.id_var.get(), nom=self.nom_var.get(), prenom=self.prenom_var.get())
            self._clear_form()
            # CORRECTION 2 : recharger après écriture
            self.load_professeurs()
            self.load_affectations()

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer le professeur: {e}")

    def _clear_form(self):
        """Vide tous les champs du formulaire."""
        for var in [self.id_var, self.matricule_var, self.nom_var, self.prenom_var,
                    self.telephone_var, self.specialite_var, self.email_var,
                    self.password_var]:
            var.set("")
        self.statut_var.set("Permanent")
        self.selected_prof_id = None
        self.selected_prof_nom = None
        self.selected_prof_label.configure(text="Aucun professeur sélectionné", text_color=TEXT_MUTED)

    # ══════════════════════════════════════════════════════════════════════════
    # GESTION DES AFFECTATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _save_affectation(self):
        if not self.selected_prof_id:
            messagebox.showwarning("Attention", "Veuillez sélectionner un professeur.")
            return

        classe = self.affectation_classe_var.get()
        matiere = self.affectation_matiere_var.get()

        if not classe or classe == "Aucune classe":
            messagebox.showwarning("Attention", "Veuillez sélectionner une classe.")
            return

        if not matiere or matiere == "Aucune matière":
            messagebox.showwarning("Attention", "Veuillez sélectionner une matière.")
            return

        try:
            cursor = self.Database.connection.cursor()

            cursor.execute("SELECT id FROM Classes WHERE nom_classe = %s", (classe,))
            id_classe = cursor.fetchone()
            if not id_classe:
                messagebox.showerror("Erreur", "Classe non trouvée.")
                cursor.close()
                return

            cursor.execute("SELECT id_matiere FROM Matiere WHERE nom_matiere = %s", (matiere,))
            id_matiere = cursor.fetchone()
            if not id_matiere:
                messagebox.showerror("Erreur", "Matière non trouvée.")
                cursor.close()
                return

            cursor.execute("""
                SELECT id_enseignement FROM Enseignement 
                WHERE id_professeur = %s AND id_matiere = %s AND id_classe = %s
            """, (self.selected_prof_id, id_matiere[0], id_classe[0]))

            if cursor.fetchone():
                messagebox.showwarning("Attention", "Cette affectation existe déjà.")
                cursor.close()
                return

            cursor.execute("""
                INSERT INTO Enseignement (id_professeur, id_matiere, id_classe)
                VALUES (%s, %s, %s)
            """, (self.selected_prof_id, id_matiere[0], id_classe[0]))

            self.Database.connection.commit()  # CORRECTION 3
            cursor.close()

            messagebox.showinfo("Succès", "Affectation enregistrée avec succès!")
            # CORRECTION 2 : recharger après écriture
            self.load_affectations()

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer l'affectation: {e}")

    def _delete_affectation(self):
        selected = self.tree_affect.focus()
        if not selected:
            return

        values = self.tree_affect.item(selected, 'values')
        if not values:
            return

        if messagebox.askyesno("Confirmation", "Voulez-vous supprimer cette affectation ?"):
            try:
                cursor = self.Database.connection.cursor()
                cursor.execute("DELETE FROM Enseignement WHERE id_enseignement = %s", (values[0],))
                self.Database.connection.commit()  # CORRECTION 3
                cursor.close()

                # CORRECTION 2 : recharger après suppression
                self.load_affectations()
                messagebox.showinfo("Succès", "Affectation supprimée!")

            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTHODES DES MENUS CONTEXTUELS
    # ══════════════════════════════════════════════════════════════════════════

    def _edit_selected_prof(self):
        selected = self.tree_prof.focus()
        if selected:
            self._on_prof_select(None)

    def _delete_selected_prof(self):
        selected = self.tree_prof.focus()
        if selected:
            self._on_prof_select(None)
            self.delete_professeur()

    def _show_prof_details(self):
        selected = self.tree_prof.focus()
        if selected:
            values = self.tree_prof.item(selected, 'values')
            details = f"""
            📋 Détails du Professeur
            ========================
            ID: {values[0]}
            Matricule: {values[1]}
            Nom complet: {values[2]} {values[3]}
            Téléphone: {values[4] or 'Non renseigné'}
            Spécialité: {values[5] or 'Non renseignée'}
            Statut: {values[6]}
            Email: {values[7] or 'Non renseigné'}
            """
            messagebox.showinfo("Détails Professeur", details)

    def _show_prof_affectations(self):
        selected = self.tree_prof.focus()
        if selected:
            self._on_prof_select(None)
            messagebox.showinfo("Info", f"Sélectionnez une classe et matière pour {self.selected_prof_nom}")