"""
notes.py  --  Academix · Vue "Gestion des Notes" v3
====================================================
CORRECTIONS v3 :
  • _PanneauBulletins._afficher_bulletin() utilise la nouvelle structure
    retournée par get_bulletin_avec_penalite() v2 :
      total_pts_brut   = Σ(moy × coeff)  — total des points avant pénalité
      penalite_pts     = points retirés (pas de pts de moyenne)
      total_pts_nets   = total_pts_brut − penalite_pts
      moy_definitive   = total_pts_nets / Σ(coeff)
  • Affichage clair : ligne "Total points", ligne "Pénalité (pts)", ligne "Moyenne Définitive"
"""

from __future__ import annotations
import datetime
from tkinter import messagebox, ttk
from customtkinter import *
from utils.constant import *
from data.db_note import NotesDB
from data.db_vie_scolaire import VieScolaireDB
from tkinter import filedialog
import os


def getAnneScolaire():
    y = datetime.datetime.now().year
    m = datetime.datetime.now().month
    return f"{y}-{y+1}" if m >= 9 else f"{y-1}-{y}"

ANNEE = getAnneScolaire()

STATUT_ICONE = {
    "vide":        ("⬜", "gray",    "Aucune note saisie"),
    "prof":        ("🔵", "#1565C0", "Saisie par le prof (web)"),
    "secretariat": ("🟡", "#F57F17", "Saisie par le secrétariat"),
    "valide":      ("🟢", "#2E7D32", "Validé & verrouillé"),
}


# ══════════════════════════════════════════════════════════════════════════════
# Barre de filtres commune
# ══════════════════════════════════════════════════════════════════════════════

class _BarreFiltres(CTkFrame):
    def __init__(self, parent, db: NotesDB, on_change, **kw):
        kw.setdefault("fg_color", PRIMARY_BLUE)
        kw.setdefault("height", 60)
        super().__init__(parent, **kw)
        self.pack_propagate(False)
        self.db = db; self.on_change = on_change
        self._classes = []; self._matieres = []

        CTkLabel(self, text="Classe :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(18,4), pady=10)
        self._classe_var = StringVar()
        self._classe_cb = CTkComboBox(self, variable=self._classe_var, state="readonly", width=120,
            command=lambda _: self._on_classe_change(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE)
        self._classe_cb.pack(side=LEFT, padx=4)

        CTkLabel(self, text="Matière :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(12,4))
        self._matiere_var = StringVar()
        self._matiere_cb = CTkComboBox(self, variable=self._matiere_var, state="readonly", width=180,
            command=lambda _: self._emit(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE)
        self._matiere_cb.pack(side=LEFT, padx=4)

        CTkLabel(self, text="Trimestre :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(12,4))
        self._trim_var = StringVar(value="1")
        for t in ("1", "2", "3"):
            CTkRadioButton(self, text=f"T{t}", variable=self._trim_var, value=t,
                font=FONT_LABEL, text_color="white", fg_color=BACKGROUND_LIGHT,
                border_color="white", command=self._emit).pack(side=LEFT, padx=4)

    def reload(self):
        self._classes = self.db.get_classes()
        noms = [c["nom_classe"] for c in self._classes]
        self._classe_cb.configure(values=noms)
        if noms:
            if self._classe_var.get() not in noms: self._classe_var.set(noms[0])
            self._on_classe_change()

    def get_selection(self):
        return self._get_classe_id(), self._get_matiere_id(), int(self._trim_var.get())

    def _get_classe_id(self):
        nom = self._classe_var.get()
        for c in self._classes:
            if c["nom_classe"] == nom: return c["id"]
        return None

    def _get_matiere_id(self):
        nom = self._matiere_var.get()
        for m in self._matieres:
            if m["nom"] == nom: return m["id"]
        return None

    def _on_classe_change(self):
        cid = self._get_classe_id()
        if cid is None: return
        self._matieres = self.db.get_matieres_classe(cid)
        noms = [m["nom"] for m in self._matieres]
        self._matiere_cb.configure(values=noms)
        if noms:
            if self._matiere_var.get() not in noms: self._matiere_var.set(noms[0])
        self._emit()

    def _emit(self):
        cid, mid, trim = self.get_selection()
        if cid and mid: self.on_change(cid, mid, trim)


# ══════════════════════════════════════════════════════════════════════════════
# PANNEAU A — Saisie rapide
# ══════════════════════════════════════════════════════════════════════════════

class _PanneauSaisie(CTkFrame):

    def __init__(self, parent, db: NotesDB, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(parent, **kw)
        self.db = db
        self._classe_id = None; self._matiere_id = None; self._trimestre = 1
        self._eval_id = None; self._evals_data = []
        self._entry_map: dict[str, CTkEntry] = {}
        self._eleve_ids: list[str] = []
        self._build()

    def _build(self):
        top = CTkFrame(self, fg_color="white", height=44)
        top.pack(fill=X, padx=10, pady=(10,0)); top.pack_propagate(False)

        CTkLabel(top, text="Évaluation :", font=FONT_LABEL,
                 text_color=TEXT_DARK, fg_color="white").pack(side=LEFT, padx=(10,4))
        self._eval_var = StringVar()
        self._eval_cb = CTkComboBox(top, variable=self._eval_var, state="readonly", width=260,
            command=lambda _: self._charger_grille(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE)
        self._eval_cb.pack(side=LEFT, padx=4)

        self._statut_lbl = CTkLabel(top, text="", font=FONT_LABEL,
                                    fg_color="white", text_color="gray")
        self._statut_lbl.pack(side=LEFT, padx=8)

        for txt, col, cmd in [
            ("+ Nouvelle éval.", SUCCESS_GREEN, self._nouvelle_eval),
            ("🗑 Supprimer",     DANGER_RED,    self._supprimer_eval),
            ("🔒 Verrouiller",   PRIMARY_BLUE,  self._verrouiller_eval),
        ]:
            CTkButton(top, text=txt, font=FONT_LABEL, fg_color=col,
                      text_color="white", width=130, command=cmd).pack(side=LEFT, padx=4)

        CTkButton(top, text="💾 Enregistrer tout", font=FONT_LABEL,
                  fg_color=SUCCESS_GREEN, text_color="white", width=160,
                  command=self._enregistrer_tout).pack(side=RIGHT, padx=10)

        self._scroll = CTkScrollableFrame(self, fg_color=BACKGROUND_LIGHT)
        self._scroll.pack(fill=BOTH, expand=True, padx=10, pady=8)

        hdr = CTkFrame(self._scroll, fg_color=PRIMARY_BLUE, height=32)
        hdr.pack(fill=X, pady=(0,2)); hdr.pack_propagate(False)
        for txt, w in [("#",40),("Matricule",100),("Nom & Prénom",240),
                       ("Note /20",90),("Appréciation",220),("Saisi par",110)]:
            CTkLabel(hdr, text=txt, font=FONT_LABEL, text_color="white",
                     fg_color=PRIMARY_BLUE, width=w, anchor="w").pack(side=LEFT, padx=4)

        self._rows_frame = CTkFrame(self._scroll, fg_color=BACKGROUND_LIGHT)
        self._rows_frame.pack(fill=BOTH, expand=True)

    def refresh(self, classe_id, matiere_id, trimestre):
        self._classe_id = classe_id; self._matiere_id = matiere_id; self._trimestre = trimestre
        self._reload_evals()

    def _reload_evals(self):
        evals = self.db.get_evaluations(self._classe_id, self._matiere_id, self._trimestre, ANNEE)
        noms = [f"{e['titre']}  [{e.get('type_eval') or e.get('type','')}  {e['date_eval']}]"
                for e in evals]
        self._evals_data = evals
        self._eval_cb.configure(values=noms if noms else ["— Aucune évaluation —"])
        if noms:
            if self._eval_var.get() not in noms: self._eval_var.set(noms[0])
            self._eval_id = evals[0]["id"]
        else:
            self._eval_var.set("— Aucune évaluation —"); self._eval_id = None
        self._charger_grille()

    def _charger_grille(self):
        sel = self._eval_var.get()
        self._eval_id = None
        for e in self._evals_data:
            lbl = f"{e['titre']}  [{e.get('type_eval') or e.get('type','')}  {e['date_eval']}]"
            if lbl == sel: self._eval_id = e["id"]; break

        if self._eval_id:
            statut = self.db.get_statut_evaluation(self._eval_id)
            ic, col, tip = STATUT_ICONE.get(statut, ("⬜","gray",""))
            self._statut_lbl.configure(text=f"{ic}  {tip}", text_color=col)
        else:
            self._statut_lbl.configure(text="", text_color="gray")

        for w in self._rows_frame.winfo_children(): w.destroy()
        self._entry_map.clear(); self._eleve_ids.clear()
        if not self._eval_id or not self._classe_id: return

        notes_map = {n["eleve_id"]: n for n in self.db.get_notes_evaluation(self._eval_id)}
        eleves = self.db.get_eleves_classe(self._classe_id)
        for i, e in enumerate(eleves, 1):
            eid = e["id"]; note_r = notes_map.get(eid)
            self._eleve_ids.append(eid)
            bg = "#F5F5F5" if i % 2 == 0 else "white"
            row = CTkFrame(self._rows_frame, fg_color=bg, height=34)
            row.pack(fill=X, pady=1); row.pack_propagate(False)

            CTkLabel(row, text=str(i), font=FONT_LABEL, fg_color=bg, text_color=TEXT_GRAY, width=40).pack(side=LEFT, padx=4)
            CTkLabel(row, text=e.get("matricule",""), font=FONT_LABEL, fg_color=bg, text_color=TEXT_DARK, width=100).pack(side=LEFT, padx=4)
            CTkLabel(row, text=f"{e['nom']} {e['prenom']}", font=FONT_LABEL, fg_color=bg,
                     text_color=TEXT_DARK, width=240, anchor="w").pack(side=LEFT, padx=4)

            note_entry = CTkEntry(row, width=80, font=FONT_LABEL,
                                  fg_color="white", text_color=TEXT_DARK, border_color=PRIMARY_BLUE)
            note_entry.insert(0, str(float(note_r["note"])) if note_r else "")
            note_entry.pack(side=LEFT, padx=4)
            note_entry.bind("<Return>", lambda ev, idx=i-1: self._focus_next(idx))
            self._entry_map[eid] = note_entry

            appr_entry = CTkEntry(row, width=200, font=FONT_LABEL,
                                  fg_color="white", text_color=TEXT_DARK, border_color=PRIMARY_BLUE)
            appr_entry.insert(0, note_r.get("appreciation","") if note_r else "")
            appr_entry.pack(side=LEFT, padx=4)
            note_entry._appr_entry = appr_entry

            saisi = note_r.get("saisi_par","") if note_r else ""
            ic_s = "🔵" if (saisi and saisi != "SECRETARIAT") else ("🟡" if saisi == "SECRETARIAT" else "⬜")
            CTkLabel(row, text=f"{ic_s} {saisi or '—'}", font=FONT_LABEL,
                     fg_color=bg, text_color=TEXT_GRAY, width=110).pack(side=LEFT, padx=4)

    def _focus_next(self, idx):
        nxt = idx + 1
        if nxt < len(self._eleve_ids):
            eid = self._eleve_ids[nxt]
            if eid in self._entry_map: self._entry_map[eid].focus_set()

    def _enregistrer_tout(self):
        if not self._eval_id:
            messagebox.showwarning("Attention", "Sélectionnez d'abord une évaluation."); return
        err = []; ok = 0
        for eid, entry in self._entry_map.items():
            val = entry.get().strip().replace(",",".")
            if not val: continue
            try: note = float(val)
            except ValueError: err.append(f"Invalide : '{val}'"); continue
            if not 0 <= note <= 20: err.append(f"Hors plage : {note}"); continue
            appr = entry._appr_entry.get().strip() if hasattr(entry, "_appr_entry") else ""
            try: self.db.upsert_note(self._eval_id, eid, note, appr, "SECRETARIAT"); ok += 1
            except PermissionError as ex: messagebox.showerror("Verrouillé", str(ex)); return
            except Exception as ex: err.append(str(ex))
        if err: messagebox.showwarning("Erreurs", f"{len(err)} erreur(s) :\n" + "\n".join(err[:5]))
        else:   messagebox.showinfo("Enregistré", f"{ok} note(s) enregistrée(s).")
        self._charger_grille()

    def _nouvelle_eval(self):
        if not self._classe_id or not self._matiere_id:
            messagebox.showwarning("Attention", "Sélectionnez classe et matière."); return
        win = CTkToplevel(self); win.title("Nouvelle évaluation")
        win.geometry("420x300"); win.grab_set()
        CTkLabel(win, text="Titre *", font=FONT_LABEL).pack(anchor=W, padx=20, pady=(16,0))
        titre_e = CTkEntry(win, width=360); titre_e.pack(padx=20, pady=4)
        CTkLabel(win, text="Type", font=FONT_LABEL).pack(anchor=W, padx=20)
        type_var = StringVar(value="Devoir")
        CTkComboBox(win, variable=type_var, values=["Interrogation","Devoir","Examen"],
                    state="readonly", width=360).pack(padx=20, pady=4)
        CTkLabel(win, text="Date (AAAA-MM-JJ) *", font=FONT_LABEL).pack(anchor=W, padx=20)
        date_e = CTkEntry(win, width=360, placeholder_text=str(datetime.date.today()))
        date_e.pack(padx=20, pady=4)
        def _creer():
            titre = titre_e.get().strip(); date_ = date_e.get().strip() or str(datetime.date.today())
            if not titre: messagebox.showwarning("Requis","Titre obligatoire.", parent=win); return
            try: datetime.date.fromisoformat(date_)
            except ValueError: messagebox.showwarning("Erreur","Date invalide.", parent=win); return
            self.db.create_evaluation(titre, type_var.get(), self._trimestre,
                                       date_, self._matiere_id, self._classe_id, ANNEE)
            win.destroy(); self._reload_evals()
        CTkButton(win, text="Créer l'évaluation", fg_color=PRIMARY_BLUE,
                  text_color="white", command=_creer).pack(pady=16)

    def _supprimer_eval(self):
        if not self._eval_id: return
        ev = self.db.get_evaluation(self._eval_id)
        if ev and ev.get("verrouille"):
            messagebox.showerror("Verrouillé", "Évaluation verrouillée."); return
        if messagebox.askyesno("Confirmer", f"Supprimer '{ev['titre']}' et toutes ses notes ?"):
            self.db.delete_evaluation(self._eval_id); self._reload_evals()

    def _verrouiller_eval(self):
        if not self._eval_id: return
        ev = self.db.get_evaluation(self._eval_id)
        if ev and ev.get("verrouille"):
            messagebox.showinfo("Déjà verrouillé", "Évaluation déjà verrouillée."); return
        if messagebox.askyesno("Confirmer",
            f"Verrouiller '{ev['titre']}' ?\nLes profs ne pourront plus modifier leurs notes."):
            self.db.verrouiller_evaluation(self._eval_id); self._charger_grille()


# ══════════════════════════════════════════════════════════════════════════════
# PANNEAU B — Bulletins  (v3 : nouvelle formule pénalité sur total des points)
# ══════════════════════════════════════════════════════════════════════════════

class _PanneauBulletins(CTkFrame):

    def __init__(self, parent, db: NotesDB, vs_db: VieScolaireDB, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(parent, **kw)
        self.db    = db
        self.vs_db = vs_db
        self._classe_id = None; self._trimestre = 1; self._eleves_data = []
        self._build()

    def _build(self):
        top = CTkFrame(self, fg_color="white", height=44)
        top.pack(fill=X, padx=10, pady=(10,0)); top.pack_propagate(False)
        CTkLabel(top, text="Élève :", font=FONT_LABEL,
                 text_color=TEXT_DARK, fg_color="white").pack(side=LEFT, padx=(10,4))
        self._eleve_var = StringVar()
        self._eleve_cb = CTkComboBox(top, variable=self._eleve_var, state="readonly", width=240,
            command=lambda _: self._afficher_bulletin(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE)
        self._eleve_cb.pack(side=LEFT, padx=4)

        self._scroll = CTkScrollableFrame(self, fg_color=BACKGROUND_LIGHT)
        self._scroll.pack(fill=BOTH, expand=True, padx=10, pady=(8,0))

        # Bandeau de résumé en bas
        summary = CTkFrame(self, fg_color="#E3F2FD", corner_radius=8)
        summary.pack(fill=X, padx=10, pady=(4,8))

        self._lbl_total_brut = CTkLabel(summary, text="Total pts brut : —",
            font=FONT_LABEL, text_color=TEXT_DARK, fg_color="#E3F2FD")
        self._lbl_total_brut.pack(side=LEFT, padx=12, pady=8)

        self._lbl_penalite = CTkLabel(summary, text="Pénalité : 0.00 pt",
            font=FONT_LABEL, text_color="#C62828", fg_color="#E3F2FD")
        self._lbl_penalite.pack(side=LEFT, padx=12, pady=8)

        self._lbl_total_net = CTkLabel(summary, text="Total pts nets : —",
            font=FONT_LABEL, text_color=TEXT_DARK, fg_color="#E3F2FD")
        self._lbl_total_net.pack(side=LEFT, padx=12, pady=8)

        self._lbl_moy_def = CTkLabel(summary, text="📋 Moyenne Trimestrielle : —",
            font=("goudy old style", 14, "bold"), text_color="#1565C0", fg_color="#E3F2FD")
        self._lbl_moy_def.pack(side=RIGHT, padx=16, pady=8)

        self._btn_print = CTkButton(summary, text="🖨️ PDF",
                                    font=FONT_LABEL, fg_color="#D81B60", hover_color="#C2185B", 
                                    text_color="white", width=90, command=self._imprimer_pdf)
        self._btn_print.pack(side=RIGHT, padx=4, pady=8)

    def refresh(self, classe_id, _matiere_id, trimestre):
        self._classe_id = classe_id; self._trimestre = trimestre
        eleves = self.db.get_eleves_classe(classe_id)
        self._eleves_data = eleves
        noms = [f"{e['nom']} {e['prenom']}" for e in eleves]
        self._eleve_cb.configure(values=noms if noms else ["— Aucun élève —"])
        if noms:
            if self._eleve_var.get() not in noms: self._eleve_var.set(noms[0])
            self._afficher_bulletin()

    def _afficher_bulletin(self):
        for w in self._scroll.winfo_children(): w.destroy()
        # Réinitialiser bandeau
        self._lbl_total_brut.configure(text="Total pts brut : —", text_color=TEXT_DARK)
        self._lbl_penalite.configure(text="Pénalité : 0.00 pt", text_color="#C62828")
        self._lbl_total_net.configure(text="Total pts nets : —", text_color=TEXT_DARK)
        self._lbl_moy_def.configure(text="📋 Moyenne Trimestrielle : —", text_color="#1565C0")

        nom_sel = self._eleve_var.get()
        eleve = next((e for e in self._eleves_data
                      if f"{e['nom']} {e['prenom']}" == nom_sel), None)
        if not eleve: return

        # ── Données bulletin (nouvelle formule v2) ────────────────────────
        bul = self.vs_db.get_bulletin_avec_penalite(
            eleve["id"], self._trimestre, self.db, ANNEE)

        # ── En-tête élève ─────────────────────────────────────────────────
        hdr = CTkFrame(self._scroll, fg_color=PRIMARY_BLUE, corner_radius=8)
        hdr.pack(fill=X, pady=(0,8))
        CTkLabel(hdr, text=f"  {eleve['nom']} {eleve['prenom']}",
                 font=FONT_TITLE, text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=10, pady=8)
        CTkLabel(hdr, text=f"Trimestre {self._trimestre}  |  {ANNEE}",
                 font=FONT_LABEL, text_color="lightblue", fg_color=PRIMARY_BLUE).pack(side=RIGHT, padx=10)

        lignes = bul["lignes"]
        if not lignes:
            CTkLabel(self._scroll, text="Aucune note saisie pour ce trimestre.",
                     font=FONT_LABEL, text_color=TEXT_GRAY,
                     fg_color=BACKGROUND_LIGHT).pack(pady=30)
            return

        # ── En-têtes colonnes ─────────────────────────────────────────────
        col_hdr = CTkFrame(self._scroll, fg_color=SECONDARY_BLUE, height=30)
        col_hdr.pack(fill=X, pady=(0,2)); col_hdr.pack_propagate(False)
        for txt, w in [("Matière",240),("Coeff.",60),("Moy. /20",110),("Points (moy×coeff)",180)]:
            CTkLabel(col_hdr, text=txt, font=FONT_LABEL, text_color="white",
                     fg_color=SECONDARY_BLUE, width=w, anchor="w").pack(side=LEFT, padx=6)

        # ── Lignes matières ───────────────────────────────────────────────
        for i, r in enumerate(lignes):
            bg = "#F5F5F5" if i % 2 == 0 else "white"
            row = CTkFrame(self._scroll, fg_color=bg, height=32)
            row.pack(fill=X, pady=1); row.pack_propagate(False)
            moy = float(r["moyenne"])
            color = SUCCESS_GREEN if moy >= 10 else (WARNING_ORANGE if moy >= 6 else DANGER_RED)
            CTkLabel(row, text=r["nom"], font=FONT_LABEL, fg_color=bg,
                     text_color=TEXT_DARK, width=240, anchor="w").pack(side=LEFT, padx=6)
            CTkLabel(row, text=str(r["coefficient"]), font=FONT_LABEL,
                     fg_color=bg, text_color=TEXT_GRAY, width=60).pack(side=LEFT, padx=4)
            CTkLabel(row, text=f"{moy:.2f}", font=FONT_LABEL,
                     fg_color=bg, text_color=color, width=110).pack(side=LEFT, padx=4)
            CTkLabel(row, text=f"{float(r['points']):.2f} pts", font=FONT_LABEL,
                     fg_color=bg, text_color=TEXT_DARK, width=180).pack(side=LEFT, padx=4)

        # ── Séparateur ────────────────────────────────────────────────────
        CTkFrame(self._scroll, fg_color=TEXT_GRAY, height=2).pack(fill=X, pady=4)

        # ── Ligne total des points bruts ──────────────────────────────────
        total_brut = float(bul["total_pts_brut"])
        total_coeff = float(bul["total_coeff"])
        moy_brute = float(bul["moy_brute"])
        r1 = CTkFrame(self._scroll, fg_color="#E8F5E9", height=34, corner_radius=4)
        r1.pack(fill=X, pady=(0,2)); r1.pack_propagate(False)
        CTkLabel(r1, text="  Σ Total points bruts (toutes matières)",
                 font=FONT_LABEL, text_color="#1B5E20", fg_color="#E8F5E9",
                 anchor="w").pack(side=LEFT, padx=6)
        CTkLabel(r1, text=f"{total_brut:.2f} pts  (moy brute : {moy_brute:.2f}/20)",
                 font=FONT_LABEL, text_color="#1B5E20", fg_color="#E8F5E9").pack(side=RIGHT, padx=16)

        # ── Ligne pénalité ────────────────────────────────────────────────
        penalite = float(bul["penalite_pts"])
        h_nj = float(bul["heures_nj"]); h_j = float(bul["heures_j"])
        c_pen = "#C62828" if penalite > 0 else "#2E7D32"
        r2 = CTkFrame(self._scroll, fg_color="#FFEBEE", height=36, corner_radius=4)
        r2.pack(fill=X, pady=(0,2)); r2.pack_propagate(False)
        pen_txt = f"  ⚠️  Pénalité absences NJ  ({h_nj:.1f}h NJ · {h_j:.1f}h J)"
        CTkLabel(r2, text=pen_txt, font=FONT_LABEL, text_color=c_pen,
                 fg_color="#FFEBEE", anchor="w").pack(side=LEFT, padx=6)
        CTkLabel(r2, text=f"−{penalite:.2f} pts", font=("goudy old style", 13, "bold"),
                 text_color=c_pen, fg_color="#FFEBEE").pack(side=RIGHT, padx=16)

        # ── Ligne total net ───────────────────────────────────────────────
        total_net = float(bul["total_pts_nets"])
        r3 = CTkFrame(self._scroll, fg_color="#E3F2FD", height=34, corner_radius=4)
        r3.pack(fill=X, pady=(0,2)); r3.pack_propagate(False)
        CTkLabel(r3, text="  Total points nets  (brut − pénalité)",
                 font=FONT_LABEL, text_color="#1565C0", fg_color="#E3F2FD",
                 anchor="w").pack(side=LEFT, padx=6)
        CTkLabel(r3, text=f"{total_net:.2f} pts",
                 font=FONT_LABEL, text_color="#1565C0", fg_color="#E3F2FD").pack(side=RIGHT, padx=16)

        # ── Ligne Moyenne Trimestrielle Définitive ────────────────────────
        moy_def = float(bul["moy_definitive"])
        c_def = SUCCESS_GREEN if moy_def >= 10 else (WARNING_ORANGE if moy_def >= 6 else "#FF6B6B")
        mention = ("Excellent" if moy_def >= 16 else "Très Bien" if moy_def >= 14 else
                   "Bien" if moy_def >= 12 else "Assez Bien" if moy_def >= 10 else "Insuffisant")
        r4 = CTkFrame(self._scroll, fg_color=PRIMARY_BLUE, height=48, corner_radius=8)
        r4.pack(fill=X, pady=(4,8)); r4.pack_propagate(False)
        CTkLabel(r4, text="  🎓 Moyenne Trimestrielle Définitive",
                 font=("goudy old style", 14, "bold"), text_color="white",
                 fg_color=PRIMARY_BLUE, anchor="w").pack(side=LEFT, padx=10)
        CTkLabel(r4, text=mention, font=FONT_LABEL, text_color="lightblue",
                 fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=8)
        CTkLabel(r4, text=f"{moy_def:.2f} / 20",
                 font=("goudy old style", 17, "bold"), text_color=c_def,
                 fg_color=PRIMARY_BLUE).pack(side=RIGHT, padx=20)

        # ── Mise à jour bandeau bas ───────────────────────────────────────
        self._lbl_total_brut.configure(
            text=f"Total pts brut : {total_brut:.2f}", text_color=TEXT_DARK)
        self._lbl_penalite.configure(
            text=f"Pénalité : −{penalite:.2f} pts  ({h_nj:.1f}h NJ)", text_color=c_pen)
        self._lbl_total_net.configure(
            text=f"Total pts nets : {total_net:.2f}", text_color="#1565C0")
        self._lbl_moy_def.configure(
            text=f"📋 Moy. Trim. : {moy_def:.2f}/20 — {mention}", text_color=c_def)

    def _imprimer_pdf(self):
        nom_sel = self._eleve_var.get()
        eleve = next((e for e in self._eleves_data if f"{e['nom']} {e['prenom']}" == nom_sel), None)
        if not eleve: return
        bul = self.vs_db.get_bulletin_avec_penalite(eleve["id"], self._trimestre, self.db, ANNEE)
        if not bul["lignes"]:
            messagebox.showwarning("Vide", "Rien à imprimer.")
            return
        
        classe_nom = "Classe inconnue"
        classes = self.db.get_classes()
        for c in classes:
            if c["id"] == self._classe_id:
                classe_nom = c["nom_classe"]
                break
                
        fpath = filedialog.asksaveasfilename(
            title="Enregistrer le bulletin",
            defaultextension=".pdf",
            initialfile=f"Bulletin_{eleve['nom']}_{eleve['prenom']}_T{self._trimestre}.pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if fpath:
            try:
                from utils.pdf_generator import generate_bulletin_pdf
                ok = generate_bulletin_pdf(eleve, classe_nom, self._trimestre, ANNEE, bul, fpath)
                if ok:
                    messagebox.showinfo("Succès", f"Bulletin enregistré sous :\n{fpath}")
                else:
                    messagebox.showerror("Erreur", "La création du PDF a échoué.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération PDF : {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PANNEAU C — Classement
# ══════════════════════════════════════════════════════════════════════════════

class _PanneauClassement(CTkFrame):

    def __init__(self, parent, db: NotesDB, vs_db: VieScolaireDB, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(parent, **kw)
        self.db = db; self.vs_db = vs_db; self._build()

    def _build(self):
        bar = CTkFrame(self, fg_color=PRIMARY_BLUE, height=42)
        bar.pack(fill=X, padx=10, pady=(10,0)); bar.pack_propagate(False)
        CTkLabel(bar, text="🏆  Classement de la classe", font=FONT_TITLE,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=12, pady=8)
        CTkButton(bar, text="Actualiser", font=FONT_LABEL,
                  fg_color=SUCCESS_GREEN, text_color="white", width=110,
                  command=self._reload).pack(side=RIGHT, padx=10)

        wrap = CTkFrame(self, fg_color=BACKGROUND_LIGHT)
        wrap.pack(fill=BOTH, expand=True, padx=10, pady=8)
        style = ttk.Style()
        try: style.theme_use("clam")
        except: pass
        style.configure("Rang.Treeview", background="white", fieldbackground="white",
            foreground=TEXT_DARK, rowheight=30, font=FONT_LABEL)
        style.configure("Rang.Treeview.Heading", background=PRIMARY_BLUE, foreground="white",
            font=FONT_LABEL, relief="flat")
        style.map("Rang.Treeview",
            background=[("selected", PRIMARY_BLUE)], foreground=[("selected", "white")])

        cols = ("rang", "matricule", "nom_prenom", "moy_gen", "mention")
        self._tree = ttk.Treeview(wrap, columns=cols, show="headings", style="Rang.Treeview")
        for col, lbl, w in [("rang","Rang",60),("matricule","Matricule",110),
                              ("nom_prenom","Nom & Prénom",260),
                              ("moy_gen","Moy. Gén./20",110),("mention","Mention",130)]:
            self._tree.heading(col, text=lbl); self._tree.column(col, width=w, anchor=CENTER)
        for tag, bg, fg in [("or","#FFF9C4","#F57F17"),("argent","#F5F5F5","#455A64"),
                              ("bronze","#FBE9E7","#BF360C"),("faible","#FFEBEE",DANGER_RED)]:
            self._tree.tag_configure(tag, background=bg, foreground=fg)
        sb = ttk.Scrollbar(wrap, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=LEFT, fill=BOTH, expand=True); sb.pack(side=LEFT, fill=Y)
        self._classe_id = None; self._trimestre = 1

    def refresh(self, classe_id, _matiere_id, trimestre):
        self._classe_id = classe_id; self._trimestre = trimestre; self._reload()

    def _reload(self):
        for r in self._tree.get_children(): self._tree.delete(r)
        if not self._classe_id: return
        
        eleves = self.db.get_eleves_classe(self._classe_id)
        if not eleves:
            self._tree.insert("","end",values=("","","Aucune note saisie","","")); return
        
        resultats = []
        for e in eleves:
            bul = self.vs_db.get_bulletin_avec_penalite(e["id"], self._trimestre, self.db, ANNEE)
            if bul["lignes"]:  # Si au moins une note
                resultats.append({
                    "eleve": e,
                    "moy_gen": float(bul["moy_definitive"])
                })
        
        if not resultats:
            self._tree.insert("","end",values=("","","Aucune note saisie","","")); return
            
        # Trier par moyenne décroissante
        resultats.sort(key=lambda x: x["moy_gen"], reverse=True)
        
        # Insérer dans le treeview avec calcul du rang
        for i, res in enumerate(resultats):
            rang = i + 1
            moy = res["moy_gen"]
            r = res["eleve"]
            mention = ("Excellent" if moy>=16 else "Très Bien" if moy>=14 else
                       "Bien" if moy>=12 else "Assez Bien" if moy>=10 else "Insuffisant")
            tag = ("or" if rang==1 else "argent" if rang==2 else
                   "bronze" if rang==3 else "faible" if moy<10 else "")
            med = "🥇" if rang==1 else "🥈" if rang==2 else "🥉" if rang==3 else ""
            self._tree.insert("","end", tags=(tag,), values=(
                f"{med} {rang}", r.get("matricule",""),
                f"{r['nom']} {r['prenom']}", f"{moy:.2f}", mention))


# ══════════════════════════════════════════════════════════════════════════════
# VUE PRINCIPALE — NotesView
# ══════════════════════════════════════════════════════════════════════════════

class NotesView(CTkFrame):

    def __init__(self, master, db, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(master, **kw)
        self.ndb   = NotesDB(db.connection)
        self.vs_db = VieScolaireDB(db.connection)
        self._current_panel = "saisie"
        self._build()

    def _build(self):
        titre = CTkFrame(self, fg_color="lightblue", height=50)
        titre.pack(fill=X, side=TOP); titre.pack_propagate(False)
        CTkLabel(titre, text="Gestion des Notes & Évaluations",
                 font=FONT_TITLE, text_color=PRIMARY_BLUE,
                 fg_color="lightblue").pack(pady=12)

        self._filtres = _BarreFiltres(self, db=self.ndb, on_change=self._on_filtre_change)
        self._filtres.pack(fill=X)

        onglets = CTkFrame(self, fg_color=BACKGROUND_LIGHT, height=40)
        onglets.pack(fill=X, padx=10, pady=(6,0)); onglets.pack_propagate(False)

        self._btn_onglets: dict[str, CTkButton] = {}
        for key, label in [("saisie","✏️  Saisie rapide"),
                            ("bulletins","📋  Bulletins"),
                            ("classement","🏆  Classement")]:
            b = CTkButton(onglets, text=label, font=FONT_LABEL,
                fg_color=PRIMARY_BLUE if key=="saisie" else BACKGROUND_LIGHT,
                text_color="white" if key=="saisie" else TEXT_DARK,
                hover_color=SECONDARY_BLUE, border_width=2,
                border_color=PRIMARY_BLUE, corner_radius=6, width=180,
                command=lambda k=key: self._switch_panel(k))
            b.pack(side=LEFT, padx=4); self._btn_onglets[key] = b

        self._panels: dict[str, CTkFrame] = {
            "saisie":     _PanneauSaisie(self, self.ndb),
            "bulletins":  _PanneauBulletins(self, self.ndb, self.vs_db),
            "classement": _PanneauClassement(self, self.ndb, self.vs_db),
        }
        for p in self._panels.values(): p.pack_forget()
        self._panels["saisie"].pack(fill=BOTH, expand=True)

    def _switch_panel(self, key):
        if key == self._current_panel: return
        self._panels[self._current_panel].pack_forget()
        self._panels[key].pack(fill=BOTH, expand=True)
        self._current_panel = key
        for k, btn in self._btn_onglets.items():
            btn.configure(fg_color=PRIMARY_BLUE if k==key else BACKGROUND_LIGHT,
                          text_color="white" if k==key else TEXT_DARK)
        cid, mid, trim = self._filtres.get_selection()
        if cid and mid: self._panels[key].refresh(cid, mid, trim)

    def _on_filtre_change(self, classe_id, matiere_id, trimestre):
        panel = self._panels[self._current_panel]
        if hasattr(panel, "refresh"): panel.refresh(classe_id, matiere_id, trimestre)

    def refresh(self):
        self._filtres.reload()