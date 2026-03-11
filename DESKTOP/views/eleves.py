"""
Module EleveView — Gestion des inscriptions en attente.

LOGIQUE DE POLLING :
  - Toutes les 30 s, interroge la BDD pour vérifier les dossiers EN_ATTENTE.
  - Si de nouveaux dossiers arrivent (inscrits depuis le web Django), le
    Treeview se met à jour automatiquement ET le badge de notifications
    dans le header d'Acceuil est mis à jour.
  - Le polling tourne même quand la vue est CACHÉE (contrairement aux autres
    vues) car c'est lui qui alimente le badge de notifications global.
    Seul le rafraîchissement du Treeview est suspendu quand la vue est cachée.

Pourquoi after() et non asyncio/threading ?
  Tkinter n'est PAS thread-safe. after() s'exécute dans la boucle principale
  → aucun risque de crash, aucun import supplémentaire.
"""

import pathlib
import threading
import datetime
from tkinter import messagebox, ttk
from customtkinter import *
from utils.constant import *
from data.db_manager import DbManager
from .documentView import DocView

INSCRIPTION_DIR = pathlib.Path(__file__).parent.parent.parent / "WEB" / "media"

# Intervalle de polling en millisecondes (30 secondes)
POLL_INTERVAL_MS = 30_000


class EleveView(CTkFrame):

    def __init__(self, master, db: DbManager = None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master

        # Instance DB partagée (passée depuis Acceuil)
        self.Database = db if db is not None else DbManager()

        self.configure(fg_color=BACKGROUND_LIGHT)

        # ── Jobs after() ──────────────────────────────────────────────────────
        # _poll_job  : tourne EN PERMANENCE (alimente le badge, même vue cachée)
        # _refresh_job : réservé pour un futur polling local rapide
        self._poll_job    = None
        self._refresh_job = None

        # Référence vers le label de notifications dans Acceuil.
        # Injecté par Acceuil juste après la création :
        #   self.views["eleve"]._notif_label = self.notificationLabel
        self._notif_label = None

        # ── Variables Tkinter ─────────────────────────────────────────────────
        self.id_var             = StringVar()
        self.matricule_var      = StringVar()
        self.nom_var            = StringVar()
        self.prenom_var         = StringVar()
        self.date_naissance_var = StringVar()
        self.addresse_var       = StringVar()
        self.classe_var         = StringVar()
        self.search_var         = StringVar()
        self.imagePath          = StringVar()
        self.typesearch_var     = StringVar()

        self.docActeNaissance = None
        self.docDiplome       = None
        self.docBulletin      = None

        # ══════════════════════════════════════════════════════════════════════
        # CONSTRUCTION DES WIDGETS  (aucune requête SQL ici)
        # ══════════════════════════════════════════════════════════════════════

        titreFrame = CTkFrame(self, fg_color='lightblue', border_width=0, height=50)
        titreFrame.pack(fill=X, side=TOP)
        CTkLabel(titreFrame, text="Gestion des Inscriptions",
                 font=FONT_TITLE, text_color=PRIMARY_BLUE,
                 fg_color="lightblue").pack(pady=20)

        infoFrame = CTkFrame(self, fg_color=BACKGROUND_LIGHT, width=500, border_width=1)
        infoFrame.pack(fill=Y, side=LEFT)
        infoFrame.pack_propagate(False)

        CTkLabel(infoFrame, text="Information Élève", font=FONT_TITLE,
                 text_color=BACKGROUND_LIGHT, fg_color=PRIMARY_BLUE,
                 bg_color=BACKGROUND_LIGHT).pack(fill=X, side=TOP)

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
        self.searchEntry.bind("<Return>", lambda e: self.Search())

        CTkButton(
            frameSearch, text="Rechercher", font=FONT_LABEL,
            fg_color=PRIMARY_BLUE, hover_color=SECONDARY_BLUE,
            border_width=0, text_color=BACKGROUND_LIGHT,
            command=self.Search
        ).pack(side=LEFT, anchor=N, padx=20, pady=10)

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

        row1 = make_row(mainContentFrame)
        make_field(row1, "Matricule",      self.matricule_var,      "Matricule")
        make_field(row1, "Nom",            self.nom_var,            "Nom")

        row2 = make_row(mainContentFrame)
        make_field(row2, "Prénom",         self.prenom_var,         "Prénom")
        make_field(row2, "Date Naissance", self.date_naissance_var, "JJ/MM/AAAA")

        row3 = make_row(mainContentFrame)
        make_field(row3, "Adresse",        self.addresse_var,       "Adresse")

        imageFrame = CTkFrame(row3, fg_color="blue", border_width=1)
        imageFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        imageFrame.pack_propagate(False)
        self.ImageEleve = CTkLabel(imageFrame, text="Photo", fg_color="lightgray")
        self.ImageEleve.place(x=0, y=0, relwidth=1, relheight=1)

        row4 = make_row(mainContentFrame)
        make_field(row4, "Classe", self.classe_var, "Classe")

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

        tableFrame = CTkFrame(self, fg_color=BACKGROUND_LIGHT, border_width=1)
        tableFrame.pack(fill=BOTH, side=LEFT, expand=True)

        CTkLabel(tableFrame, text="Liste des Élèves en attente",
                 font=FONT_TITLE, text_color=BACKGROUND_LIGHT,
                 fg_color=PRIMARY_BLUE).pack(fill=X, side=TOP)

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

        self._status_label = CTkLabel(
            self, text="⏳ En attente de la première vérification...",
            font=("Arial", 10), text_color="gray", fg_color=BACKGROUND_LIGHT
        )
        self._status_label.pack(side=BOTTOM, anchor=E, padx=10, pady=2)

        self.pack(fill=BOTH, expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # POLLING GLOBAL — tourne en permanence, même vue cachée
    # ══════════════════════════════════════════════════════════════════════════

    def start_global_polling(self):
        print("[ELEVE] start_global_polling() appelé")
        """Lance le polling permanent toutes les 30 s.

        Appelé UNE SEULE FOIS depuis Acceuil.__init__() après la création
        de la vue. Ce polling survit aux changements de vue.

        Il réalise deux choses :
          1. Met à jour le badge de notifications dans le header.
          2. Si la vue EleveView est visible, met aussi à jour le Treeview.
        """
        if self._poll_job is not None:
            self.after_cancel(self._poll_job)
            self._poll_job = None
        self._run_poll()

    def _run_poll(self):
        """Corps du cycle de polling : requête BDD → badge → Treeview."""
        try:
            self.Database._ensure_connection()
            if not self.Database.connection:
                print("[POLL] Pas de connexion DB")
                return

            data  = self.Database.refresh_pending_list()
            count = len(data) if data else 0
            print(f"[POLL] {count} dossier(s) EN_ATTENTE récupérés")

            # 1. Badge
            self._update_badge(count)

            # 2. Treeview — toujours, sans condition
            self._refresh_treeview(data)
            self._update_status(count)

        except Exception as e:
            import traceback
            print(f"[POLL] ERREUR : {e}")
            traceback.print_exc()

        finally:
            self._poll_job = self.after(POLL_INTERVAL_MS, self._run_poll)

    def _update_badge(self, count: int):
        """Met à jour le bouton de notifications dans le header d'Acceuil."""
        if self._notif_label is None:
            return
        try:
            color = "red" if count > 0 else "gray"
            self._notif_label.configure(text=str(count), text_color=color)
        except Exception:
            pass

    def _refresh_treeview(self, data):
        """Compare IDs affichés vs IDs BDD, ne redessine QUE si besoin."""
        ids_affiches = {
            self.TableListe.item(i, "values")[0]
            for i in self.TableListe.get_children()
        }
        ids_bdd = {str(row[0]) for row in data} if data else set()

        print(f"[TREEVIEW] ids_affiches={ids_affiches}  ids_bdd={ids_bdd}  diff={ids_affiches != ids_bdd}")

        if ids_affiches != ids_bdd:
            print("[TREEVIEW] Mise à jour du tableau...")
            self.TableListe.delete(*self.TableListe.get_children())
            if data:
                for row in data:
                    self.TableListe.insert("", END, values=row)
            print("[TREEVIEW] Tableau mis à jour.")

    def _update_status(self, count: int):
        """Met à jour la barre de statut en bas de la vue."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        if count > 0:
            self._status_label.configure(
                text=f"🔴 {count} dossier(s) en attente — {now}",
                text_color="red"
            )
        else:
            self._status_label.configure(
                text=f"✅ Aucun dossier en attente — {now}",
                text_color="gray"
            )

    def stop_global_polling(self):
        """Stoppe définitivement le polling.
        À appeler UNIQUEMENT depuis Acceuil._on_close().
        """
        if self._poll_job is not None:
            self.after_cancel(self._poll_job)
            self._poll_job = None

    # ══════════════════════════════════════════════════════════════════════════
    # refresh() — appelé par show_view() au changement de vue
    # ══════════════════════════════════════════════════════════════════════════

    def refresh(self):
        """Rechargement immédiat sans attendre le prochain cycle de 30 s."""
        self.clear()
        try:
            self.Database._ensure_connection()
            if self.Database.connection:
                data  = self.Database.refresh_pending_list()
                count = len(data) if data else 0
                self.TableListe.delete(*self.TableListe.get_children())
                if data:
                    for row in data:
                        self.TableListe.insert("", END, values=row)
                self._update_badge(count)
                self._update_status(count)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les dossiers : {e}")

    # Stubs de compatibilité avec show_view() (qui appelle _stop/_start)
    def _start_auto_refresh(self):
        pass   # Le polling global tourne déjà en permanence

    def _stop_auto_refresh(self):
        """Marqué comme non-visible + stoppe l'éventuel polling local rapide."""
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None

    # ══════════════════════════════════════════════════════════════════════════
    # ÉVÉNEMENTS TREEVIEW
    # ══════════════════════════════════════════════════════════════════════════

    def getListeData(self, ev):
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
        if not self.matricule_var.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner un élève.")
            return
        if self.Database.connection:
            self.Database.AcceptedInscription(
                self.matricule_var.get(), self.id_var.get()
            )
            self.clear()
            self.refresh()   # rechargement immédiat après acceptation

    def Search(self):
        if not self.search_var.get().strip():
            self.refresh()
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
        documents = self.GetEleveDocument()
        if not documents:
            return

        acte_path, diplome_path, bulletin_path = documents

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

        lbl_acte     = CTkLabel(tabview.tab("Acte de Naissance"), text="⏳ Chargement...")
        lbl_diplome  = CTkLabel(tabview.tab("Diplôme"),           text="⏳ Chargement...")
        lbl_bulletin = CTkLabel(tabview.tab("Dernier Bulletin"),  text="⏳ Chargement...")
        for lbl in (lbl_acte, lbl_diplome, lbl_bulletin):
            lbl.pack(expand=True)

        def _load_docs():
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
            docWindow.after(0, lambda: _apply_docs(results))

        def _apply_docs(results):
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

        threading.Thread(target=_load_docs, daemon=True).start()