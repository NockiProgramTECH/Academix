"""
Module EleveView — Gestion des inscriptions en attente.

Séparation claire :
  __init__   → construction des widgets UNIQUEMENT
  refresh()  → vide + requête SQL + remplit (appelé par main.py au changement de vue)
  _poll_database() → requête silencieuse toutes les 10 s (polling)

Pourquoi pas asyncio ?
  Tkinter n'est PAS thread-safe. On ne peut pas modifier des widgets depuis
  un thread secondaire. La bonne approche est after() qui s'exécute dans la
  boucle principale Tkinter → aucun risque de conflit, aucun import supplémentaire.
"""

import pathlib
import threading                          # utilisé UNIQUEMENT pour charger les PDFs en arrière-plan
                                          # (DocView peut bloquer plusieurs secondes sur un gros PDF)
from tkinter import messagebox, ttk
from customtkinter import *
from utils.constant import *
from data.db_manager import DbManager
from .documentView import DocView

INSCRIPTION_DIR = pathlib.Path(__file__).parent.parent.parent / "WEB" / "media"


class EleveView(CTkFrame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.Database = DbManager()
        self.configure(fg_color=BACKGROUND_LIGHT)

        # ── Référence au job after() pour le polling ──────────────────────────
        # None = polling arrêté. Valeur entière = polling actif (ID annulable).
        self._refresh_job = None

        # ── Variables Tkinter ─────────────────────────────────────────────────
        self.id_var            = StringVar()
        self.matricule_var     = StringVar()
        self.nom_var           = StringVar()
        self.prenom_var        = StringVar()
        self.date_naissance_var= StringVar()
        self.addresse_var      = StringVar()
        self.classe_var        = StringVar()
        self.search_var        = StringVar()
        self.imagePath         = StringVar()
        self.typesearch_var    = StringVar()

        # Chemins documents (remplis par GetEleveDocument)
        self.docActeNaissance = None
        self.docDiplome       = None
        self.docBulletin      = None

        # ══════════════════════════════════════════════════════════════════════
        # CONSTRUCTION DES WIDGETS  (aucune requête SQL ici)
        # ══════════════════════════════════════════════════════════════════════

        # ── Titre ─────────────────────────────────────────────────────────────
        titreFrame = CTkFrame(self, fg_color='lightblue', border_width=0, height=50)
        titreFrame.pack(fill=X, side=TOP)
        CTkLabel(titreFrame, text="Gestion des Inscriptions",
                 font=FONT_TITLE, text_color=PRIMARY_BLUE,
                 fg_color="lightblue").pack(pady=20)

        # ── Frame gauche : formulaire ──────────────────────────────────────────
        infoFrame = CTkFrame(self, fg_color=BACKGROUND_LIGHT, width=500, border_width=1)
        infoFrame.pack(fill=Y, side=LEFT)
        infoFrame.pack_propagate(False)

        CTkLabel(infoFrame, text="Information Élève", font=FONT_TITLE,
                 text_color=BACKGROUND_LIGHT, fg_color=PRIMARY_BLUE,
                 bg_color=BACKGROUND_LIGHT).pack(fill=X, side=TOP)

        # ── Barre de recherche ────────────────────────────────────────────────
        frameSearch = CTkFrame(infoFrame, fg_color=BACKGROUND_LIGHT, border_width=0)
        frameSearch.pack(fill=X, side=TOP)

        self.combo = CTkComboBox(
            frameSearch, width=140, corner_radius=10, border_width=5,
            button_hover_color=PRIMARY_BLUE,
            values=['matricule', 'nom', 'prenom'],
            border_color=PRIMARY_BLUE, text_color=BACKGROUND_LIGHT
        )
        self.combo.pack(side=LEFT, anchor=N, pady=10)

        self.searchEntry = CTkEntry(
            frameSearch, placeholder_text="Rechercher",
            font=FONT_LABEL, fg_color=BACKGROUND_LIGHT,
            border_width=2, text_color=PRIMARY_BLUE,
            border_color=PRIMARY_BLUE, textvariable=self.search_var
        )
        self.searchEntry.pack(side=LEFT, anchor=N, expand=True, pady=10, padx=10)
        # Recherche aussi en appuyant sur Entrée
        self.searchEntry.bind("<Return>", lambda e: self.Search())

        CTkButton(
            frameSearch, text="Rechercher", font=FONT_LABEL,
            fg_color=PRIMARY_BLUE, hover_color=SECONDARY_BLUE,
            border_width=0, text_color=BACKGROUND_LIGHT,
            command=self.Search
        ).pack(side=LEFT, anchor=N, padx=20, pady=10)

        # ── Champs du formulaire ───────────────────────────────────────────────
        mainContentFrame = CTkFrame(infoFrame, fg_color=BACKGROUND_LIGHT)
        mainContentFrame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        def make_row(parent):
            f = CTkFrame(parent, fg_color=BACKGROUND_LIGHT)
            f.pack(fill=X, expand=True, pady=5)
            return f

        def make_field(parent, label_text, textvariable, placeholder):
            frame = CTkFrame(parent, fg_color=BACKGROUND_LIGHT)
            frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
            CTkLabel(frame, text=label_text, font=FONT_LABEL,
                     text_color=TEXT_DARK, fg_color=BACKGROUND_LIGHT).pack(anchor=W, pady=(0, 2))
            entry = CTkEntry(
                frame, textvariable=textvariable,
                font=("times new roman", 15, "bold"),
                fg_color=BACKGROUND_LIGHT, border_width=2,
                placeholder_text=placeholder, text_color=PRIMARY_BLUE,
                border_color=PRIMARY_BLUE
            )
            entry.pack(fill=X, anchor=W)
            return entry

        # Row 1 : Matricule | Nom
        row1 = make_row(mainContentFrame)
        make_field(row1, "Matricule",      self.matricule_var,      "Matricule")
        make_field(row1, "Nom",            self.nom_var,            "Nom")

        # Row 2 : Prénom | Date Naissance
        row2 = make_row(mainContentFrame)
        make_field(row2, "Prénom",         self.prenom_var,         "Prénom")
        make_field(row2, "Date Naissance", self.date_naissance_var, "JJ/MM/AAAA")

        # Row 3 : Adresse | Photo
        row3 = make_row(mainContentFrame)
        make_field(row3, "Adresse",        self.addresse_var,       "Adresse")

        imageFrame = CTkFrame(row3, fg_color="blue", border_width=1)
        imageFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        imageFrame.pack_propagate(False)
        self.ImageEleve = CTkLabel(imageFrame, text="Photo", fg_color="lightgray")
        self.ImageEleve.place(x=0, y=0, relwidth=1, relheight=1)

        # Row 4 : Classe
        row4 = make_row(mainContentFrame)
        make_field(row4, "Classe", self.classe_var, "Classe")

        # ── Boutons d'action ───────────────────────────────────────────────────
        buttonsFrame = CTkFrame(mainContentFrame, fg_color=BACKGROUND_LIGHT)
        buttonsFrame.pack(fill=X, expand=True, pady=10)

        CTkButton(buttonsFrame, text="ACCEPTER", font=FONT_LABEL,
                  fg_color=SUCCESS_GREEN, hover_color="#27AE60",
                  border_width=0, width=100,
                  command=self.Accepted).pack(side=LEFT, padx=5, fill=X, expand=True)

        CTkButton(buttonsFrame, text="Modifier", font=FONT_LABEL,
                  fg_color=WARNING_ORANGE, hover_color="#D35400",
                  border_width=0, width=100).pack(side=LEFT, padx=5, fill=X, expand=True)

        CTkButton(buttonsFrame, text="Supprimer", font=FONT_LABEL,
                  fg_color=DANGER_RED, hover_color="#C0392B",
                  border_width=0, width=100).pack(side=LEFT, padx=5, fill=X, expand=True)

        CTkButton(buttonsFrame, text="Voir Documents", font=FONT_LABEL,
                  fg_color=INFO_GRAY, hover_color="#95A5A6",
                  border_width=0, width=100,
                  command=self.ShowEleveDocument).pack(side=LEFT, padx=5, fill=X, expand=True)

        # ── Frame droite : tableau ─────────────────────────────────────────────
        tableFrame = CTkFrame(self, fg_color=BACKGROUND_LIGHT, border_width=1)
        tableFrame.pack(fill=BOTH, side=LEFT, expand=True)

        CTkLabel(tableFrame, text="Liste des Élèves en attente",
                 font=FONT_TITLE, text_color=BACKGROUND_LIGHT,
                 fg_color=PRIMARY_BLUE).pack(fill=X, side=TOP)

        # Style Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview.Heading", background=PRIMARY_BLUE,
                        foreground=BACKGROUND_LIGHT, font=("Arial", 12, "bold"))
        style.configure("Treeview", background="white", foreground="black",
                        fieldbackground="lightgrey", font=("Arial", 11))
        style.map("Treeview",
                  background=[("selected", "skyblue")],
                  foreground=[("selected", "black")])

        cols = ("id", "Matricule", "Nom", "Prenom", "Date Naissance", "Addresse", "Classe", "Photo")
        self.TableListe = ttk.Treeview(tableFrame, columns=cols, show="headings")

        for col in cols:
            self.TableListe.heading(col, text='' if col in ("id", "Photo") else col)

        self.TableListe.column("id",             width=0,   stretch=False)
        self.TableListe.column("Photo",          width=0,   stretch=False)
        self.TableListe.column("Matricule",      width=80)
        self.TableListe.column("Nom",            width=100)
        self.TableListe.column("Prenom",         width=100)
        self.TableListe.column("Date Naissance", width=110)
        self.TableListe.column("Addresse",       width=150)
        self.TableListe.column("Classe",         width=80)

        xscroll = ttk.Scrollbar(tableFrame, orient=HORIZONTAL, command=self.TableListe.xview)
        yscroll = ttk.Scrollbar(tableFrame, orient=VERTICAL,   command=self.TableListe.yview)
        self.TableListe.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        xscroll.pack(side=BOTTOM, fill=X)
        yscroll.pack(side=RIGHT,  fill=Y)

        self.TableListe.bind("<ButtonRelease-1>", self.getListeData)
        self.TableListe.pack(fill=BOTH, expand=True, pady=10, padx=10)

        # ── Indicateur de dernière mise à jour (polling) ───────────────────────
        # Informe l'utilisateur que les données sont bien synchronisées.
        self._status_label = CTkLabel(
            self, text="⏳ En attente de données...",
            font=("Arial", 10), text_color="gray", fg_color=BACKGROUND_LIGHT
        )
        self._status_label.pack(side=BOTTOM, anchor=E, padx=10, pady=2)

        self.pack(fill=BOTH, expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # CHARGEMENT DES DONNÉES
    # ══════════════════════════════════════════════════════════════════════════

    def GetEleves(self):
        """Requête SQL complète + remplissage du Treeview.
        Appelé par refresh() (changement de vue) et par Accepted().
        """
        if not self.Database.connection:
            return
        data = self.Database.refresh_pending_list()
        self.TableListe.delete(*self.TableListe.get_children())
        if data:
            for row in data:
                self.TableListe.insert("", END, values=row)
        self._update_status()

    def refresh(self):
        """Appelé par main.py à chaque fois que cette vue devient visible.
        Vide le formulaire, recharge les données, démarre le polling.
        """
        self.clear()
        self.GetEleves()
        self._start_auto_refresh()   # ← démarre la boucle de polling

    # ══════════════════════════════════════════════════════════════════════════
    # POLLING — rafraîchissement automatique toutes les 10 s
    # ══════════════════════════════════════════════════════════════════════════

    def _poll_database(self):
        """Requête silencieuse : compare les IDs BDD vs IDs affichés.
        Ne rafraîchit le Treeview QUE si les données ont réellement changé
        → évite le scintillement inutile.
        Ne touche PAS aux champs du formulaire ni à la sélection en cours.
        """
        if not self.Database.connection:
            return
        try:
            nouvelles_datas = self.Database.refresh_pending_list()

            ids_affiches = {
                self.TableListe.item(i, "values")[0]
                for i in self.TableListe.get_children()
            }
            ids_bdd = {str(row[0]) for row in nouvelles_datas} if nouvelles_datas else set()

            if ids_affiches != ids_bdd:
                # Les données ont changé : on recharge le tableau
                self.TableListe.delete(*self.TableListe.get_children())
                if nouvelles_datas:
                    for row in nouvelles_datas:
                        self.TableListe.insert("", END, values=row)

            self._update_status()

        except Exception:
            # Silencieux : pas de popup toutes les 10 s
            pass

    def _start_auto_refresh(self):
        """Démarre le polling. Annule un éventuel job précédent
        pour éviter d'avoir deux boucles parallèles.
        """
        self._stop_auto_refresh()
        self._auto_refresh()

    def _auto_refresh(self):
        """Interroge la BDD puis se replanifie dans 10 secondes.
        Utilise after() → s'exécute dans le thread Tkinter → pas de conflit UI.
        """
        self._poll_database()
        self._refresh_job = self.after(10_000, self._auto_refresh)

    def _stop_auto_refresh(self):
        """Stoppe le polling quand la vue est cachée → aucune requête inutile."""
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None

    def _update_status(self):
        """Met à jour l'horodatage affiché en bas de la vue."""
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self._status_label.configure(text=f"✅ Dernière mise à jour : {now}")

    # ══════════════════════════════════════════════════════════════════════════
    # ÉVÉNEMENTS TREEVIEW
    # ══════════════════════════════════════════════════════════════════════════

    def getListeData(self, ev):
        """Remplit le formulaire avec la ligne sélectionnée dans le Treeview."""
        selected = self.TableListe.focus()
        values   = self.TableListe.item(selected, 'values')
        if not values:
            return
        try:
            self.id_var.set(values[0])
            self.matricule_var.set(values[1])
            self.nom_var.set(values[2])
            self.prenom_var.set(values[3])
            self.date_naissance_var.set(values[4])
            self.addresse_var.set(values[5])
            self.classe_var.set(values[6])
            self.imagePath.set(values[7])
            self.showImage(self.imagePath.get())
        except IndexError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # ACTIONS BOUTONS
    # ══════════════════════════════════════════════════════════════════════════

    def Accepted(self):
        """Accepte l'inscription de l'élève sélectionné."""
        if not self.matricule_var.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner un élève.")
            return
        if self.Database.connection:
            self.Database.AcceptedInscription(
                self.matricule_var.get(), self.id_var.get()
            )
            self.GetEleves()
            self.clear()

    def Search(self):
        """Recherche dans la BDD selon le critère et la valeur saisis."""
        if not self.search_var.get().strip():
            # Si la recherche est vide, recharger toute la liste
            self.GetEleves()
            return
        if self.Database.connection:
            data = self.Database.SearchEleveInscription(
                self.combo.get(), self.search_var.get()
            )
            if data:
                self.TableListe.delete(*self.TableListe.get_children())
                self.clear()
                for row in data:
                    self.TableListe.insert("", END, values=row)
            else:
                messagebox.showinfo("Recherche", "Aucun résultat trouvé.")

    def clear(self):
        """Vide tous les champs du formulaire."""
        self.id_var.set("")
        self.matricule_var.set("")
        self.nom_var.set("")
        self.prenom_var.set("")
        self.date_naissance_var.set("")
        self.classe_var.set("")
        self.addresse_var.set("")
        self.imagePath.set("")
        self.ImageEleve.configure(image="", text="Photo", fg_color="lightgray")

    def showImage(self, path):
        """Charge et affiche la photo de l'élève."""
        if not path:
            return
        try:
            from PIL import Image
            img = Image.open(INSCRIPTION_DIR / path)
            img = CTkImage(img, size=(250, 250))
            self.ImageEleve.configure(text="", image=img)
        except Exception:
            self.ImageEleve.configure(image="", text="Photo introuvable")

    # ══════════════════════════════════════════════════════════════════════════
    # DOCUMENTS
    # ══════════════════════════════════════════════════════════════════════════

    def GetEleveDocument(self):
        """Récupère les chemins des 3 documents depuis la BDD."""
        if not self.id_var.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner un élève.")
            return None
        if self.Database.connection:
            documents = self.Database.GetDocuments(self.id_var.get())
            if documents:
                self.docActeNaissance, self.docDiplome, self.docBulletin = documents
                return documents
            else:
                messagebox.showinfo("Documents", "Aucun document trouvé pour cet élève.")
        return None

    def ShowEleveDocument(self):
        """Ouvre une fenêtre avec les 3 documents PDF de l'élève.

        Pourquoi threading ici ?
          DocView (PyMuPDF) peut prendre 1-3 secondes pour rasteriser un PDF.
          Si on l'appelle directement, l'UI freeze pendant ce temps.
          On charge les images dans un thread secondaire, puis on les affiche
          dans le thread principal via after(0, callback) → thread-safe.
        """
        documents = self.GetEleveDocument()
        if not documents:
            return

        acte_path, diplome_path, bulletin_path = documents

        # Création de la fenêtre modale
        docWindow = CTkToplevel(self, fg_color=BACKGROUND_LIGHT)
        docWindow.geometry("600x800+750+10")
        docWindow.title("Documents de l'élève")
        docWindow.resizable(False, False)
        docWindow.grab_set()

        tabview = CTkTabview(docWindow, fg_color="black",
                             bg_color=PRIMARY_BLUE, text_color=BACKGROUND_LIGHT)
        tabview.place(x=0, y=0, relwidth=1, relheight=0.9)
        tabview.add("Acte de Naissance")
        tabview.add("Diplôme")
        tabview.add("Dernier Bulletin")

        # Labels de chargement (spinners textuels)
        lbl_acte     = CTkLabel(tabview.tab("Acte de Naissance"), text="⏳ Chargement...")
        lbl_diplome  = CTkLabel(tabview.tab("Diplôme"),           text="⏳ Chargement...")
        lbl_bulletin = CTkLabel(tabview.tab("Dernier Bulletin"),  text="⏳ Chargement...")
        for lbl in (lbl_acte, lbl_diplome, lbl_bulletin):
            lbl.pack(expand=True)

        def _load_docs():
            """Chargement des PDFs dans un thread secondaire → pas de freeze UI."""
            results = {}
            for key, path in [("acte", acte_path),
                               ("diplome", diplome_path),
                               ("bulletin", bulletin_path)]:
                if path:
                    try:
                        results[key] = DocView(documentpath=INSCRIPTION_DIR / path)
                    except Exception:
                        results[key] = None
                else:
                    results[key] = None
            # Retour dans le thread principal via after(0)
            docWindow.after(0, lambda: _apply_docs(results))

        def _apply_docs(results):
            """Affiche les images chargées — s'exécute dans le thread Tkinter."""
            mapping = {
                "acte":     (lbl_acte,     "Acte de Naissance"),
                "diplome":  (lbl_diplome,  "Diplôme"),
                "bulletin": (lbl_bulletin, "Dernier Bulletin"),
            }
            for key, (lbl, tab_name) in mapping.items():
                img = results.get(key)
                if img:
                    lbl.configure(text="", image=img)
                else:
                    lbl.configure(text=f"⚠ Aucun {tab_name} disponible")

        # Lance le chargement en arrière-plan
        threading.Thread(target=_load_docs, daemon=True).start()