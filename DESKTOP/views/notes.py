"""
notes.py  --  Academix · Vue "Gestion des Notes" v1
====================================================
Module View piloté depuis acceuil.py comme EleveView.

Architecture : CTkFrame unique avec trois panneaux superposés
  ┌──────────────────────── HEADER ──────────────────────────┐
  │  Classe ▾   Matière ▾   Trimestre ▾   [Saisie] [Bulletins] [Classement]  │
  └──────────────────────────────────────────────────────────┘
  ╔══════════════ Onglet actif (swap via show_panel) ════════╗
  ║  A. _PanneauSaisie      — grille de saisie rapide        ║
  ║  B. _PanneauBulletins   — tableau moyennes + rang        ║
  ║  C. _PanneauClassement  — classement de la classe        ║
  ╚══════════════════════════════════════════════════════════╝

Intégration acceuil.py :
    self._create_notes_view()        # dans _create_*_view
    self.views["notes"]              # référence dans self.views
    self.show_view("notes")          # bouton sidebar
"""

from __future__ import annotations
import datetime
from tkinter import messagebox, ttk
from customtkinter import *
from utils.constant import *
from data.db_note import NotesDB

def getAnneScolaire():
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        if current_month >= 9:  # De septembre à décembre
            return f"{current_year}-{current_year + 1}"
        else:  # De janvier à août
            return f"{current_year - 1}-{current_year}"
ANNEE = getAnneScolaire()

# ─── Icônes d'état des évaluations ───────────────────────────────────────────
STATUT_ICONE = {
    "vide":        ("⬜", "gray",       "Aucune note saisie"),
    "prof":        ("🔵", "#1565C0",    "Saisie par le prof (web)"),
    "secretariat": ("🟡", "#F57F17",    "Saisie par le secrétariat"),
    "valide":      ("🟢", "#2E7D32",    "Validé & verrouillé"),
}


# ══════════════════════════════════════════════════════════════════════════════
# Barre de filtres commune (Classe / Matière / Trimestre)
# ══════════════════════════════════════════════════════════════════════════════

class _BarreFiltres(CTkFrame):
    """
    Émet un callback on_change(classe_id, matiere_id, trimestre)
    dès que l'un des trois sélecteurs change.
    """

    def __init__(self, parent, db: NotesDB, on_change, **kw):
        kw.setdefault("fg_color", PRIMARY_BLUE)
        kw.setdefault("height", 60)
        super().__init__(parent, **kw)
        self.pack_propagate(False)

        self.db        = db
        self.on_change = on_change

        # ── Classe ────────────────────────────────────────────────────────────
        CTkLabel(self, text="Classe :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(18, 4), pady=10)
        self._classes   = []  # list[dict]
        self._classe_var = StringVar()
        self._classe_cb  = CTkComboBox(
            self, variable=self._classe_var, state="readonly", width=120,
            command=lambda _: self._on_classe_change(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE
        )
        self._classe_cb.pack(side=LEFT, padx=4)

        # ── Matière ───────────────────────────────────────────────────────────
        CTkLabel(self, text="Matière :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(12, 4))
        self._matieres   = []  # list[dict]
        self._matiere_var = StringVar()
        self._matiere_cb  = CTkComboBox(
            self, variable=self._matiere_var, state="readonly", width=180,
            command=lambda _: self._emit(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE
        )
        self._matiere_cb.pack(side=LEFT, padx=4)

        # ── Trimestre ─────────────────────────────────────────────────────────
        CTkLabel(self, text="Trimestre :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(12, 4))
        self._trim_var = StringVar(value="1")
        for t in ("1", "2", "3"):
            CTkRadioButton(
                self, text=f"T{t}", variable=self._trim_var, value=t,
                font=FONT_LABEL, text_color="white", fg_color=BACKGROUND_LIGHT,
                border_color="white", command=self._emit
            ).pack(side=LEFT, padx=4)

    # ── API publique ──────────────────────────────────────────────────────────

    def reload(self):
        """Recharge classes + matières depuis la BDD."""
        self._classes = self.db.get_classes()
        noms = [c["nom_classe"] for c in self._classes]
        self._classe_cb.configure(values=noms)
        if noms:
            if self._classe_var.get() not in noms:
                self._classe_var.set(noms[0])
            self._on_classe_change()

    def get_selection(self) -> tuple[int | None, int | None, int]:
        """Retourne (classe_id, matiere_id, trimestre)."""
        classe_id  = self._get_classe_id()
        matiere_id = self._get_matiere_id()
        trimestre  = int(self._trim_var.get())
        return classe_id, matiere_id, trimestre

    # ── Privé ─────────────────────────────────────────────────────────────────

    def _get_classe_id(self) -> int | None:
        nom = self._classe_var.get()
        for c in self._classes:
            if c["nom_classe"] == nom:
                return c["id"]
        return None

    def _get_matiere_id(self) -> int | None:
        nom = self._matiere_var.get()
        for m in self._matieres:
            if m["nom"] == nom:
                return m["id"]
        return None

    def _on_classe_change(self):
        cid = self._get_classe_id()
        if cid is None:
            return
        self._matieres = self.db.get_matieres_classe(cid)
        noms = [m["nom"] for m in self._matieres]
        self._matiere_cb.configure(values=noms)
        if noms:
            if self._matiere_var.get() not in noms:
                self._matiere_var.set(noms[0])
        self._emit()

    def _emit(self):
        cid, mid, trim = self.get_selection()
        if cid and mid:
            self.on_change(cid, mid, trim)


# ══════════════════════════════════════════════════════════════════════════════
# PANNEAU A — Saisie rapide
# ══════════════════════════════════════════════════════════════════════════════

class _PanneauSaisie(CTkFrame):

    def __init__(self, parent, db: NotesDB, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(parent, **kw)
        self.db         = db
        self._classe_id  = None
        self._matiere_id = None
        self._trimestre  = 1
        self._eval_id    = None
        self._entry_map: dict[str, CTkEntry] = {}   # eleve_id -> Entry widget
        self._eleve_ids: list[str] = []              # ordre d'affichage
        self._build()

    def _build(self):
        # ── Barre évaluations ─────────────────────────────────────────────────
        top = CTkFrame(self, fg_color="white", height=44)
        top.pack(fill=X, padx=10, pady=(10, 0))
        top.pack_propagate(False)

        CTkLabel(top, text="Évaluation :", font=FONT_LABEL,
                 text_color=TEXT_DARK, fg_color="white").pack(side=LEFT, padx=(10, 4))
        self._eval_var = StringVar()
        self._eval_cb  = CTkComboBox(
            top, variable=self._eval_var, state="readonly", width=260,
            command=lambda _: self._charger_grille(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE
        )
        self._eval_cb.pack(side=LEFT, padx=4)

        # Indicateur statut de l'évaluation sélectionnée
        self._statut_lbl = CTkLabel(top, text="", font=FONT_LABEL,
                                    fg_color="white", text_color="gray")
        self._statut_lbl.pack(side=LEFT, padx=8)

        # Bouton nouvelle évaluation
        CTkButton(
            top, text="+ Nouvelle éval.", font=FONT_LABEL,
            fg_color=SUCCESS_GREEN, hover_color="#1B5E20",
            text_color="white", width=140,
            command=self._nouvelle_eval
        ).pack(side=LEFT, padx=6)

        # Bouton supprimer
        CTkButton(
            top, text="🗑 Supprimer", font=FONT_LABEL,
            fg_color=DANGER_RED, hover_color="#7B241C",
            text_color="white", width=120,
            command=self._supprimer_eval
        ).pack(side=LEFT, padx=4)

        # Bouton verrouiller
        CTkButton(
            top, text="🔒 Verrouiller", font=FONT_LABEL,
            fg_color=PRIMARY_BLUE, hover_color=SECONDARY_BLUE,
            text_color="white", width=130,
            command=self._verrouiller_eval
        ).pack(side=LEFT, padx=4)

        # Bouton enregistrer tout
        CTkButton(
            top, text="💾 Enregistrer tout", font=FONT_LABEL,
            fg_color=SUCCESS_GREEN, hover_color="#1B5E20",
            text_color="white", width=160,
            command=self._enregistrer_tout
        ).pack(side=RIGHT, padx=10)

        # ── Zone de saisie scrollable ─────────────────────────────────────────
        self._scroll = CTkScrollableFrame(self, fg_color=BACKGROUND_LIGHT)
        self._scroll.pack(fill=BOTH, expand=True, padx=10, pady=8)

        # En-têtes de colonnes
        hdr = CTkFrame(self._scroll, fg_color=PRIMARY_BLUE, height=32)
        hdr.pack(fill=X, pady=(0, 2))
        hdr.pack_propagate(False)
        for txt, w in [("#", 40), ("Matricule", 100), ("Nom & Prénom", 240),
                       ("Note /20", 90), ("Appréciation", 220), ("Saisi par", 110)]:
            CTkLabel(hdr, text=txt, font=FONT_LABEL, text_color="white",
                     fg_color=PRIMARY_BLUE, width=w, anchor="w").pack(side=LEFT, padx=4)

        self._rows_frame = CTkFrame(self._scroll, fg_color=BACKGROUND_LIGHT)
        self._rows_frame.pack(fill=BOTH, expand=True)

    # ── Rechargement ─────────────────────────────────────────────────────────

    def refresh(self, classe_id: int, matiere_id: int, trimestre: int):
        self._classe_id  = classe_id
        self._matiere_id = matiere_id
        self._trimestre  = trimestre
        self._reload_evals()

    def _reload_evals(self):
        evals = self.db.get_evaluations(
            self._classe_id, self._matiere_id, self._trimestre, ANNEE
        )
        noms = [
            f"{e['titre']}  [{e.get('type_eval') or e.get('type', '')}  {e['date_eval']}]"
            for e in evals
        ]
        self._evals_data = evals
        self._eval_cb.configure(values=noms if noms else ["— Aucune évaluation —"])
        if noms:
            if self._eval_var.get() not in noms:
                self._eval_var.set(noms[0])
            self._eval_id = evals[0]["id"]
        else:
            self._eval_var.set("— Aucune évaluation —")
            self._eval_id = None
        self._charger_grille()

    def _charger_grille(self):
        """Charge les élèves + leurs notes dans la grille de saisie."""
        # Retrouver l'id de l'éval sélectionnée
        sel = self._eval_var.get()
        self._eval_id = None
        for e in self._evals_data:
            label = f"{e['titre']}  [{e.get('type_eval') or e.get('type', '')}  {e['date_eval']}]"
            if label == sel:
                self._eval_id = e["id"]
                break

        # Mettre à jour l'indicateur de statut
        if self._eval_id:
            statut = self.db.get_statut_evaluation(self._eval_id)
            icone, couleur, tooltip = STATUT_ICONE.get(statut, ("⬜", "gray", ""))
            self._statut_lbl.configure(text=f"{icone}  {tooltip}", text_color=couleur)
        else:
            self._statut_lbl.configure(text="", text_color="gray")

        # Vider la grille précédente
        for w in self._rows_frame.winfo_children():
            w.destroy()
        self._entry_map.clear()
        self._eleve_ids.clear()

        if not self._eval_id or not self._classe_id:
            return

        # Notes déjà saisies → dict eleve_id → row
        notes_map = {
            n["eleve_id"]: n
            for n in self.db.get_notes_evaluation(self._eval_id)
        }

        eleves = self.db.get_eleves_classe(self._classe_id)
        for i, e in enumerate(eleves, 1):
            eid    = e["id"]
            note_r = notes_map.get(eid)
            self._eleve_ids.append(eid)

            row_bg = "#F5F5F5" if i % 2 == 0 else "white"
            row = CTkFrame(self._rows_frame, fg_color=row_bg, height=34)
            row.pack(fill=X, pady=1)
            row.pack_propagate(False)

            CTkLabel(row, text=str(i), font=FONT_LABEL,
                     fg_color=row_bg, text_color=TEXT_GRAY, width=40).pack(side=LEFT, padx=4)
            CTkLabel(row, text=e.get("matricule", ""), font=FONT_LABEL,
                     fg_color=row_bg, text_color=TEXT_DARK, width=100).pack(side=LEFT, padx=4)
            CTkLabel(row, text=f"{e['nom']} {e['prenom']}", font=FONT_LABEL,
                     fg_color=row_bg, text_color=TEXT_DARK, width=240,
                     anchor="w").pack(side=LEFT, padx=4)

            # Champ Note
            note_val = str(float(note_r["note"])) if note_r else ""
            note_entry = CTkEntry(row, width=80, font=FONT_LABEL,
                                  fg_color="white", text_color=TEXT_DARK,
                                  border_color=PRIMARY_BLUE)
            note_entry.insert(0, note_val)
            note_entry.pack(side=LEFT, padx=4)
            # Touche Entrée → focus sur ligne suivante
            note_entry.bind("<Return>", lambda ev, idx=i - 1: self._focus_next(idx))
            self._entry_map[eid] = note_entry

            # Champ Appréciation
            appr_val = note_r.get("appreciation", "") if note_r else ""
            appr_entry = CTkEntry(row, width=200, font=FONT_LABEL,
                                  fg_color="white", text_color=TEXT_DARK,
                                  border_color=PRIMARY_BLUE)
            appr_entry.insert(0, appr_val or "")
            appr_entry.pack(side=LEFT, padx=4)
            # On stocke la ref appréciation dans l'Entry note pour l'enregistrement
            note_entry._appr_entry = appr_entry

            # Saisi par
            saisi = note_r.get("saisi_par", "") if note_r else ""
            icone_saisi = "🔵" if (saisi and saisi != "SECRETARIAT") else (
                          "🟡" if saisi == "SECRETARIAT" else "⬜")
            CTkLabel(row, text=f"{icone_saisi} {saisi or '—'}", font=FONT_LABEL,
                     fg_color=row_bg, text_color=TEXT_GRAY, width=110).pack(side=LEFT, padx=4)

    def _focus_next(self, current_idx: int):
        """Déplace le focus sur le champ note de la ligne suivante."""
        next_idx = current_idx + 1
        if next_idx < len(self._eleve_ids):
            eid = self._eleve_ids[next_idx]
            if eid in self._entry_map:
                self._entry_map[eid].focus_set()

    # ── Actions ──────────────────────────────────────────────────────────────

    def _enregistrer_tout(self):
        if not self._eval_id:
            messagebox.showwarning("Attention", "Sélectionnez d'abord une évaluation.")
            return
        erreurs = []
        sauvegardees = 0
        for eid, entry in self._entry_map.items():
            val = entry.get().strip().replace(",", ".")
            if not val:
                continue
            try:
                note = float(val)
            except ValueError:
                erreurs.append(f"Note invalide pour un élève : '{val}'")
                continue
            if not (0 <= note <= 20):
                erreurs.append(f"Note hors plage [0-20] : {note}")
                continue
            appr = entry._appr_entry.get().strip() if hasattr(entry, "_appr_entry") else ""
            try:
                self.db.upsert_note(self._eval_id, eid, note, appr, "SECRETARIAT")
                sauvegardees += 1
            except PermissionError as ex:
                messagebox.showerror("Verrouillé", str(ex))
                return
            except Exception as ex:
                erreurs.append(str(ex))

        if erreurs:
            messagebox.showwarning("Erreurs de saisie",
                                   f"{len(erreurs)} erreur(s) :\n" + "\n".join(erreurs[:5]))
        else:
            messagebox.showinfo("Enregistré",
                                f"{sauvegardees} note(s) enregistrée(s) avec succès.")
        self._charger_grille()  # Actualise les indicateurs "saisi par"

    def _nouvelle_eval(self):
        if not self._classe_id or not self._matiere_id:
            messagebox.showwarning("Attention", "Sélectionnez classe et matière d'abord.")
            return
        win = CTkToplevel(self)
        win.title("Nouvelle évaluation")
        win.geometry("420x300")
        win.grab_set()

        CTkLabel(win, text="Titre *", font=FONT_LABEL, text_color=TEXT_DARK).pack(anchor=W, padx=20, pady=(16, 0))
        titre_e = CTkEntry(win, font=FONT_LABEL, width=360)
        titre_e.pack(padx=20, pady=4)

        CTkLabel(win, text="Type", font=FONT_LABEL, text_color=TEXT_DARK).pack(anchor=W, padx=20)
        type_var = StringVar(value="Devoir")
        CTkComboBox(win, variable=type_var, values=["Interrogation", "Devoir", "Examen"],
                    state="readonly", width=360, font=FONT_LABEL).pack(padx=20, pady=4)

        CTkLabel(win, text="Date (AAAA-MM-JJ) *", font=FONT_LABEL, text_color=TEXT_DARK).pack(anchor=W, padx=20)
        date_e = CTkEntry(win, font=FONT_LABEL, width=360,
                          placeholder_text=str(datetime.date.today()))
        date_e.pack(padx=20, pady=4)

        def _creer():
            titre = titre_e.get().strip()
            date_ = date_e.get().strip() or str(datetime.date.today())
            if not titre:
                messagebox.showwarning("Requis", "Le titre est obligatoire.", parent=win)
                return
            try:
                datetime.date.fromisoformat(date_)
            except ValueError:
                messagebox.showwarning("Erreur", "Format de date invalide.", parent=win)
                return
            self.db.create_evaluation(
                titre, type_var.get(), self._trimestre,
                date_, self._matiere_id, self._classe_id, ANNEE
            )
            win.destroy()
            self._reload_evals()

        CTkButton(win, text="Créer l'évaluation", font=FONT_LABEL,
                  fg_color=PRIMARY_BLUE, text_color="white",
                  command=_creer).pack(pady=16)

    def _supprimer_eval(self):
        if not self._eval_id:
            return
        ev = self.db.get_evaluation(self._eval_id)
        if ev and ev.get("verrouille"):
            messagebox.showerror("Verrouillé",
                                 "Cette évaluation est verrouillée. Impossible de la supprimer.")
            return
        if messagebox.askyesno("Confirmer",
                               f"Supprimer l'évaluation '{ev['titre']}' et toutes ses notes ?"):
            self.db.delete_evaluation(self._eval_id)
            self._reload_evals()

    def _verrouiller_eval(self):
        if not self._eval_id:
            return
        ev = self.db.get_evaluation(self._eval_id)
        if ev and ev.get("verrouille"):
            messagebox.showinfo("Déjà verrouillé", "Cette évaluation est déjà verrouillée.")
            return
        if messagebox.askyesno("Confirmer",
                               f"Verrouiller '{ev['titre']}' ?\n"
                               "Les profs ne pourront plus modifier leurs notes."):
            self.db.verrouiller_evaluation(self._eval_id)
            self._charger_grille()


# ══════════════════════════════════════════════════════════════════════════════
# PANNEAU B — Bulletins / Tableau récapitulatif
# ══════════════════════════════════════════════════════════════════════════════

class _PanneauBulletins(CTkFrame):

    def __init__(self, parent, db: NotesDB, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(parent, **kw)
        self.db = db
        self._classe_id  = None
        self._trimestre  = 1
        self._build()

    def _build(self):
        top = CTkFrame(self, fg_color="white", height=44)
        top.pack(fill=X, padx=10, pady=(10, 0))
        top.pack_propagate(False)

        CTkLabel(top, text="Élève :", font=FONT_LABEL,
                 text_color=TEXT_DARK, fg_color="white").pack(side=LEFT, padx=(10, 4))
        self._eleve_var = StringVar()
        self._eleve_cb  = CTkComboBox(
            top, variable=self._eleve_var, state="readonly", width=240,
            command=lambda _: self._afficher_bulletin(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE
        )
        self._eleve_cb.pack(side=LEFT, padx=4)
        self._eleves_data = []

        # zone scrollable
        self._scroll = CTkScrollableFrame(self, fg_color=BACKGROUND_LIGHT)
        self._scroll.pack(fill=BOTH, expand=True, padx=10, pady=8)

    def refresh(self, classe_id: int, _matiere_id: int, trimestre: int):
        self._classe_id = classe_id
        self._trimestre = trimestre
        eleves = self.db.get_eleves_classe(classe_id)
        self._eleves_data = eleves
        noms = [f"{e['nom']} {e['prenom']}" for e in eleves]
        self._eleve_cb.configure(values=noms if noms else ["— Aucun élève —"])
        if noms:
            if self._eleve_var.get() not in noms:
                self._eleve_var.set(noms[0])
            self._afficher_bulletin()

    def _afficher_bulletin(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        nom_sel = self._eleve_var.get()
        eleve = next((e for e in self._eleves_data
                      if f"{e['nom']} {e['prenom']}" == nom_sel), None)
        if not eleve:
            return

        bulletin = self.db.get_bulletin_eleve(eleve["id"], self._trimestre, ANNEE)
        moy_gen  = self.db.get_moyenne_generale(eleve["id"], self._trimestre, ANNEE)

        # ── En-tête élève ─────────────────────────────────────────────────────
        hdr = CTkFrame(self._scroll, fg_color=PRIMARY_BLUE, corner_radius=8)
        hdr.pack(fill=X, pady=(0, 8))
        CTkLabel(hdr, text=f"  {eleve['nom']} {eleve['prenom']}",
                 font=FONT_TITLE, text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=10, pady=8)
        CTkLabel(hdr, text=f"Trimestre {self._trimestre}  |  {ANNEE}",
                 font=FONT_LABEL, text_color="lightblue", fg_color=PRIMARY_BLUE).pack(side=RIGHT, padx=10)

        if not bulletin:
            CTkLabel(self._scroll, text="Aucune note saisie pour ce trimestre.",
                     font=FONT_LABEL, text_color=TEXT_GRAY,
                     fg_color=BACKGROUND_LIGHT).pack(pady=30)
            return

        # ── Colonnes ─────────────────────────────────────────────────────────
        col_hdr = CTkFrame(self._scroll, fg_color=SECONDARY_BLUE, height=30)
        col_hdr.pack(fill=X, pady=(0, 2))
        col_hdr.pack_propagate(False)
        for txt, w in [("Matière", 240), ("Coeff.", 60), ("Moyenne /20", 110), ("Points", 90)]:
            CTkLabel(col_hdr, text=txt, font=FONT_LABEL, text_color="white",
                     fg_color=SECONDARY_BLUE, width=w, anchor="w").pack(side=LEFT, padx=6)

        total_coeff = 0
        total_pts   = 0.0
        for i, r in enumerate(bulletin):
            bg = "#F5F5F5" if i % 2 == 0 else "white"
            row = CTkFrame(self._scroll, fg_color=bg, height=32)
            row.pack(fill=X, pady=1)
            row.pack_propagate(False)
            moy = float(r["moyenne"])
            color = (SUCCESS_GREEN if moy >= 10
                     else (WARNING_ORANGE if moy >= 6 else DANGER_RED))
            CTkLabel(row, text=r["nom"], font=FONT_LABEL,
                     fg_color=bg, text_color=TEXT_DARK, width=240, anchor="w").pack(side=LEFT, padx=6)
            CTkLabel(row, text=str(r["coefficient"]), font=FONT_LABEL,
                     fg_color=bg, text_color=TEXT_GRAY, width=60).pack(side=LEFT, padx=4)
            CTkLabel(row, text=f"{moy:.2f}", font=FONT_LABEL,
                     fg_color=bg, text_color=color, width=110).pack(side=LEFT, padx=4)
            CTkLabel(row, text=f"{float(r['points']):.2f}", font=FONT_LABEL,
                     fg_color=bg, text_color=TEXT_DARK, width=90).pack(side=LEFT, padx=4)
            total_coeff += r["coefficient"]
            total_pts   += float(r["points"])

        # ── Ligne moyenne générale ────────────────────────────────────────────
        CTkFrame(self._scroll, fg_color=TEXT_GRAY, height=2).pack(fill=X, pady=4)
        moy_row = CTkFrame(self._scroll, fg_color=PRIMARY_BLUE, height=38, corner_radius=6)
        moy_row.pack(fill=X)
        moy_row.pack_propagate(False)
        color_gen = (SUCCESS_GREEN if float(moy_gen) >= 10
                     else (WARNING_ORANGE if float(moy_gen) >= 6 else "#FF6B6B"))
        CTkLabel(moy_row, text="  Moyenne Générale", font=FONT_TITLE,
                 text_color="white", fg_color=PRIMARY_BLUE, width=240,
                 anchor="w").pack(side=LEFT, padx=6)
        CTkLabel(moy_row, text=str(total_coeff), font=FONT_LABEL,
                 text_color="lightblue", fg_color=PRIMARY_BLUE, width=60).pack(side=LEFT, padx=4)
        CTkLabel(moy_row, text=f"{float(moy_gen):.2f} / 20", font=FONT_TITLE,
                 text_color=color_gen, fg_color=PRIMARY_BLUE, width=130).pack(side=LEFT, padx=4)
        CTkLabel(moy_row, text=f"{total_pts:.2f}", font=FONT_LABEL,
                 text_color="lightblue", fg_color=PRIMARY_BLUE, width=90).pack(side=LEFT, padx=4)


# ══════════════════════════════════════════════════════════════════════════════
# PANNEAU C — Classement de la classe
# ══════════════════════════════════════════════════════════════════════════════

class _PanneauClassement(CTkFrame):

    def __init__(self, parent, db: NotesDB, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(parent, **kw)
        self.db = db
        self._build()

    def _build(self):
        # En-tête
        bar = CTkFrame(self, fg_color=PRIMARY_BLUE, height=42)
        bar.pack(fill=X, padx=10, pady=(10, 0))
        bar.pack_propagate(False)
        CTkLabel(bar, text="🏆  Classement de la classe", font=FONT_TITLE,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=12, pady=8)
        CTkButton(bar, text="Actualiser", font=FONT_LABEL,
                  fg_color=SUCCESS_GREEN, hover_color="#1B5E20",
                  text_color="white", width=110,
                  command=self._reload).pack(side=RIGHT, padx=10)

        # Treeview
        wrap = CTkFrame(self, fg_color=BACKGROUND_LIGHT)
        wrap.pack(fill=BOTH, expand=True, padx=10, pady=8)

        style = ttk.Style()
        try: style.theme_use("clam")
        except: pass
        style.configure("Rang.Treeview",
            background="white", fieldbackground="white",
            foreground=TEXT_DARK, rowheight=30, font=FONT_LABEL)
        style.configure("Rang.Treeview.Heading",
            background=PRIMARY_BLUE, foreground="white",
            font=FONT_LABEL, relief="flat")
        style.map("Rang.Treeview",
            background=[("selected", PRIMARY_BLUE)],
            foreground=[("selected", "white")])

        cols = ("rang", "matricule", "nom_prenom", "moy_gen", "mention")
        self._tree = ttk.Treeview(wrap, columns=cols,
                                  show="headings", style="Rang.Treeview")
        for col, lbl, w in [
            ("rang",      "Rang",          60),
            ("matricule", "Matricule",     110),
            ("nom_prenom","Nom & Prénom",  260),
            ("moy_gen",   "Moy. Gén./20", 110),
            ("mention",   "Mention",       130),
        ]:
            self._tree.heading(col, text=lbl)
            self._tree.column(col, width=w, anchor=CENTER)

        self._tree.tag_configure("or",      background="#FFF9C4", foreground="#F57F17")
        self._tree.tag_configure("argent",  background="#F5F5F5", foreground="#455A64")
        self._tree.tag_configure("bronze",  background="#FBE9E7", foreground="#BF360C")
        self._tree.tag_configure("faible",  background="#FFEBEE", foreground=DANGER_RED)

        sb = ttk.Scrollbar(wrap, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=LEFT, fill=Y)

        self._classe_id = None
        self._trimestre = 1

    def refresh(self, classe_id: int, _matiere_id: int, trimestre: int):
        self._classe_id = classe_id
        self._trimestre = trimestre
        self._reload()

    def _reload(self):
        for r in self._tree.get_children():
            self._tree.delete(r)
        if not self._classe_id:
            return
        rows = self.db.get_classement_classe(self._classe_id, self._trimestre, ANNEE)
        if not rows:
            self._tree.insert("", END, values=("", "", "Aucune note saisie", "", ""))
            return
        for r in rows:
            rang  = int(r["rang"])
            moy   = float(r.get("moy_gen") or 0)
            mention = (
                "Excellent"     if moy >= 16 else
                "Très Bien"     if moy >= 14 else
                "Bien"          if moy >= 12 else
                "Assez Bien"    if moy >= 10 else
                "Insuffisant"
            )
            tag = ("or" if rang == 1 else "argent" if rang == 2 else
                   "bronze" if rang == 3 else "faible" if moy < 10 else "")
            medaille = "🥇" if rang == 1 else "🥈" if rang == 2 else "🥉" if rang == 3 else ""
            self._tree.insert("", END, tags=(tag,), values=(
                f"{medaille} {rang}",
                r.get("matricule", ""),
                f"{r['nom']} {r['prenom']}",
                f"{moy:.2f}",
                mention
            ))


# ══════════════════════════════════════════════════════════════════════════════
# VUE PRINCIPALE — NotesView  (pilotée depuis acceuil.py)
# ══════════════════════════════════════════════════════════════════════════════

class NotesView(CTkFrame):
    """
    Point d'entrée du module Notes.
    Instanciation :
        view = NotesView(self.mainFrame, db=self.Database)
    où self.Database est l'instance DbManager (db_manager.py).
    """

    def __init__(self, master, db, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(master, **kw)

        # NotesDB utilise la connexion MySQL de DbManager
        self.ndb = NotesDB(db.connection)

        self._current_panel: str = "saisie"
        self._build()

    def _build(self):
        # ── TITRE ─────────────────────────────────────────────────────────────
        titre = CTkFrame(self, fg_color="lightblue", height=50)
        titre.pack(fill=X, side=TOP)
        titre.pack_propagate(False)
        CTkLabel(titre, text="Gestion des Notes & Évaluations",
                 font=FONT_TITLE, text_color=PRIMARY_BLUE,
                 fg_color="lightblue").pack(pady=12)

        # ── BARRE DE FILTRES ──────────────────────────────────────────────────
        self._filtres = _BarreFiltres(self, db=self.ndb,
                                      on_change=self._on_filtre_change)
        self._filtres.pack(fill=X)

        # ── ONGLETS ───────────────────────────────────────────────────────────
        onglets = CTkFrame(self, fg_color=BACKGROUND_LIGHT, height=40)
        onglets.pack(fill=X, padx=10, pady=(6, 0))
        onglets.pack_propagate(False)

        self._btn_onglets: dict[str, CTkButton] = {}
        for key, label in [("saisie", "✏️  Saisie rapide"),
                            ("bulletins", "📋  Bulletins"),
                            ("classement", "🏆  Classement")]:
            b = CTkButton(
                onglets, text=label, font=FONT_LABEL,
                fg_color=PRIMARY_BLUE if key == "saisie" else BACKGROUND_LIGHT,
                text_color="white" if key == "saisie" else TEXT_DARK,
                hover_color=SECONDARY_BLUE,
                border_width=2, border_color=PRIMARY_BLUE,
                corner_radius=6, width=180,
                command=lambda k=key: self._switch_panel(k)
            )
            b.pack(side=LEFT, padx=4)
            self._btn_onglets[key] = b

        # ── PANNEAUX ──────────────────────────────────────────────────────────
        self._panels: dict[str, CTkFrame] = {
            "saisie":      _PanneauSaisie(self, self.ndb),
            "bulletins":   _PanneauBulletins(self, self.ndb),
            "classement":  _PanneauClassement(self, self.ndb),
        }
        for panel in self._panels.values():
            panel.pack_forget()

        self._panels["saisie"].pack(fill=BOTH, expand=True)

    # ── Navigation entre panneaux ─────────────────────────────────────────────

    def _switch_panel(self, key: str):
        if key == self._current_panel:
            return
        self._panels[self._current_panel].pack_forget()
        self._panels[key].pack(fill=BOTH, expand=True)
        self._current_panel = key

        # Mise à jour visuelle des onglets
        for k, btn in self._btn_onglets.items():
            if k == key:
                btn.configure(fg_color=PRIMARY_BLUE, text_color="white")
            else:
                btn.configure(fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK)

        # Rafraîchir le panneau nouvellement visible
        cid, mid, trim = self._filtres.get_selection()
        if cid and mid:
            self._panels[key].refresh(cid, mid, trim)

    # ── Callback filtres ──────────────────────────────────────────────────────

    def _on_filtre_change(self, classe_id: int, matiere_id: int, trimestre: int):
        panel = self._panels[self._current_panel]
        if hasattr(panel, "refresh"):
            panel.refresh(classe_id, matiere_id, trimestre)

    # ── API publique (appelée par acceuil.show_view) ──────────────────────────

    def refresh(self):
        """Rechargement complet : classes, matières, puis panneau actif."""
        self._filtres.reload()