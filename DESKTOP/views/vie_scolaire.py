"""
vie_scolaire.py  --  Academix · Vue "Vie Scolaire" v2
======================================================
CORRECTIONS v2 :
  • _OngletEmploiDuTemps : grille reconstruite avec canvas tkinter natif pour
    gérer correctement les cellules multilignes (hauteur variable), le scroll
    horizontal+vertical, et les clics sur créneaux existants.
  • _OngletConfig : layout en deux colonnes (gauche = formulaire, droite = aperçu)
    avec le bouton Enregistrer côté droit — pas en bas.
"""

from __future__ import annotations
import datetime
from tkinter import messagebox, ttk, Canvas, Scrollbar, filedialog
import tkinter as tk
from customtkinter import *
from utils.constant import *
from data.db_vie_scolaire import VieScolaireDB

VS_VERT   = "#2E7D32"
VS_ROUGE  = "#C62828"
VS_ORANGE = "#E65100"
VS_BLEU   = "#1565C0"

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
# Créneaux demi-heures de 07:00 à 18:30
HEURES_DISPO = []
for _h in range(7, 19):
    HEURES_DISPO.append(f"{_h:02d}:00")
    HEURES_DISPO.append(f"{_h:02d}:30")
HEURES_DISPO.append("19:00")


def _annee_scolaire() -> str:
    now = datetime.datetime.now()
    return f"{now.year}-{now.year+1}" if now.month >= 9 else f"{now.year-1}-{now.year}"

ANNEE = _annee_scolaire()
TRIMESTRE_ACTUEL = (
    1 if datetime.datetime.now().month in range(9, 12)
    else 2 if datetime.datetime.now().month in range(1, 4)
    else 3
)

# Palettes couleurs par matière (cycle)
PALETTE = [
    "#BBDEFB", "#C8E6C9", "#FFE0B2", "#F8BBD0",
    "#E1BEE7", "#B2DFDB", "#FFF9C4", "#D7CCC8",
    "#B3E5FC", "#DCEDC8", "#FFE082", "#FFCCBC",
]


def _hm_to_min(hm: str) -> int:
    """'08:30' → 510 minutes depuis minuit."""
    try:
        h, m = str(hm)[:5].split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET A — EMPLOI DU TEMPS  (grille Canvas corrigée)
# ══════════════════════════════════════════════════════════════════════════════

class _OngletEmploiDuTemps(CTkFrame):
    """
    Grille hebdomadaire dessinée sur un Canvas tkinter.
    • Colonnes = jours (Lun→Sam)
    • Lignes   = tranches de 30 min de 07:00 à 18:30
    • Un créneau qui dure N tranches occupe N cases visuellement
    • Clic sur créneau existant → modifier/supprimer
    • Clic sur case vide        → ajouter avec jour+heure préremplis
    """

    COL_W   = 150   # largeur colonne jour (px)
    ROW_H   = 40    # hauteur d'une tranche 30 min (px)
    LABEL_W = 65    # largeur colonne "heure"
    HDR_H   = 36    # hauteur ligne en-tête

    def __init__(self, parent, db: VieScolaireDB, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(parent, **kw)
        self.db = db
        self._classe_id: int | None = None
        self._classes: list[dict] = []
        self._mat_couleur: dict[int, str] = {}
        self._creneau_items: dict[int, dict] = {}  # canvas_id → creneau dict
        self._build()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build(self):
        # Barre de sélection
        top = CTkFrame(self, fg_color=PRIMARY_BLUE, height=50)
        top.pack(fill=X)
        top.pack_propagate(False)

        CTkLabel(top, text="Classe :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(16,4), pady=12)
        self._classe_var = StringVar()
        self._classe_cb = CTkComboBox(
            top, variable=self._classe_var, state="readonly", width=160,
            command=lambda _: self._charger_grille(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE)
        self._classe_cb.pack(side=LEFT, padx=4)

        CTkButton(top, text="➕ Nouveau créneau", font=FONT_LABEL,
                  fg_color=VS_VERT, hover_color="#1B5E20", text_color="white",
                  width=170, command=self._ouvrir_form_ajout).pack(side=RIGHT, padx=12)

        CTkButton(top, text="🖨️ PDF", font=FONT_LABEL,
                  fg_color="#D81B60", hover_color="#C2185B", text_color="white",
                  width=90, command=self._imprimer_edt).pack(side=RIGHT, padx=4)

        # Canvas scrollable (double scroll : X et Y)
        container = tk.Frame(self, bg="#F0F4F8")
        container.pack(fill=BOTH, expand=True, padx=6, pady=6)

        self._canvas = Canvas(container, bg="white", highlightthickness=0)
        vbar = Scrollbar(container, orient=tk.VERTICAL,   command=self._canvas.yview)
        hbar = Scrollbar(container, orient=tk.HORIZONTAL, command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        vbar.pack(side=tk.RIGHT,  fill=tk.Y)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self._canvas.pack(side=tk.LEFT, fill=BOTH, expand=True)

        # Scroll molette
        self._canvas.bind("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-e.delta / 120), "units"))
        self._canvas.bind("<Shift-MouseWheel>",
            lambda e: self._canvas.xview_scroll(int(-e.delta / 120), "units"))

    # ── API publique ──────────────────────────────────────────────────────────

    def refresh(self):
        self._classes = self.db.get_classes()
        noms = [c["nom_classe"] for c in self._classes]
        self._classe_cb.configure(values=noms)
        if noms:
            if self._classe_var.get() not in noms:
                self._classe_var.set(noms[0])
            self._charger_grille()

    # ── Dessin de la grille ───────────────────────────────────────────────────

    def _get_classe_id(self) -> int | None:
        nom = self._classe_var.get()
        for c in self._classes:
            if c["nom_classe"] == nom:
                return c["id"]
        return None

    def _charger_grille(self):
        self._classe_id = self._get_classe_id()
        cv = self._canvas
        cv.delete("all")
        self._creneau_items.clear()

        if not self._classe_id:
            return

        creneaux = self.db.get_emploi_classe(self._classe_id, ANNEE)

        # Affecter une couleur à chaque matière
        for c in creneaux:
            mid = c["matiere_id"]
            if mid not in self._mat_couleur:
                idx = len(self._mat_couleur) % len(PALETTE)
                self._mat_couleur[mid] = PALETTE[idx]

        W = self.LABEL_W
        H = self.HDR_H
        RH = self.ROW_H
        CW = self.COL_W

        # Horaires affichés (toutes les 30 min de 07:00 à 18:30)
        START_MIN = 7 * 60      # 420
        END_MIN   = 18 * 60 + 30  # 1110
        slots = []
        t = START_MIN
        while t <= END_MIN:
            slots.append(t)
            t += 30

        total_w = W + CW * len(JOURS) + 2
        total_h = H + RH * len(slots) + 2

        # En-têtes colonnes (jours)
        cv.create_rectangle(0, 0, W, H, fill=PRIMARY_BLUE, outline="")
        cv.create_text(W // 2, H // 2, text="Heure",
                       fill="white", font=("Calibri", 10, "bold"))
        for col, jour in enumerate(JOURS):
            x0 = W + col * CW
            cv.create_rectangle(x0, 0, x0 + CW, H, fill=PRIMARY_BLUE, outline="")
            cv.create_text(x0 + CW // 2, H // 2, text=jour,
                           fill="white", font=("Calibri", 11, "bold"))

        # Lignes horaires + fond quadrillage
        for row, mins in enumerate(slots):
            y0 = H + row * RH
            hh = mins // 60
            mm = mins % 60
            lbl = f"{hh:02d}:{mm:02d}"
            # Fond alterné
            bg = "#EEF4FB" if row % 2 == 0 else "white"
            cv.create_rectangle(0, y0, W, y0 + RH, fill="#DDEEFF", outline="#CCCCCC")
            cv.create_text(W // 2, y0 + RH // 2, text=lbl,
                           fill="#1A237E", font=("Calibri", 9, "bold"))
            for col in range(len(JOURS)):
                x0 = W + col * CW
                cv.create_rectangle(x0, y0, x0 + CW, y0 + RH,
                                    fill=bg, outline="#DDDDDD", tags="cell")

        # Détecter les cases "couvertes" par un créneau multi-tranche
        occupied: set[tuple[int, int]] = set()  # (col_idx, slot_idx)

        for c in creneaux:
            jour_idx = JOURS.index(str(c["jour"])) if str(c["jour"]) in JOURS else -1
            if jour_idx < 0:
                continue
            min_deb = _hm_to_min(c["heure_debut"])
            min_fin = _hm_to_min(c["heure_fin"])
            # Trouver les indices de slots couverts
            slot_start = None
            slot_end   = None
            for i, s in enumerate(slots):
                if s == min_deb:
                    slot_start = i
                if s == min_fin:
                    slot_end = i
                    break
            if slot_start is None:
                continue
            if slot_end is None:
                slot_end = len(slots)  # jusqu'à la fin
            nb_slots = max(1, slot_end - slot_start)

            for si in range(slot_start, slot_start + nb_slots):
                occupied.add((jour_idx, si))

            # Dessiner le bloc créneau
            x0 = W + jour_idx * CW + 2
            y0 = H + slot_start * RH + 2
            x1 = x0 + CW - 4
            y1 = y0 + nb_slots * RH - 4

            couleur = self._mat_couleur.get(c["matiere_id"], "#BBDEFB")
            rect_id = cv.create_rectangle(x0, y0, x1, y1,
                                           fill=couleur, outline="#1565C0",
                                           width=2, tags="creneau")
            h_deb = str(c["heure_debut"])[:5]
            h_fin = str(c["heure_fin"])[:5]
            lines = [c["nom_matiere"], f"{h_deb} – {h_fin}"]
            if c.get("prof_nom", "").strip():
                lines.append(f"👤 {c['prof_nom'].strip()}")
            if c.get("salle"):
                lines.append(f"🏫 {c['salle']}")
            txt_content = "\n".join(lines)
            txt_id = cv.create_text(
                (x0 + x1) // 2, (y0 + y1) // 2,
                text=txt_content, fill="#0D1B5E",
                font=("Calibri", 10, "bold"),
                width=CW - 10, justify="center", tags="creneau")

            # Stocker le créneau associé aux items canvas
            for item_id in (rect_id, txt_id):
                self._creneau_items[item_id] = c
                cv.tag_bind(item_id, "<Button-1>",
                            lambda e, cr=c: self._ouvrir_form_modif(cr))
                cv.tag_bind(item_id, "<Enter>",
                            lambda e, i=rect_id: cv.itemconfig(i, outline="#FF6F00", width=3))
                cv.tag_bind(item_id, "<Leave>",
                            lambda e, i=rect_id, col=couleur: cv.itemconfig(
                                i, outline="#1565C0", width=2))

        # Rendre les cellules vides cliquables → ajouter créneau
        for col, jour in enumerate(JOURS):
            for row, mins in enumerate(slots):
                if (col, row) in occupied:
                    continue
                x0 = W + col * CW
                y0 = H + row * RH
                hh = mins // 60
                mm = mins % 60
                heure_str = f"{hh:02d}:{mm:02d}"
                zone_id = cv.create_rectangle(
                    x0, y0, x0 + CW, y0 + RH,
                    fill="", outline="", tags="empty_cell")
                cv.tag_bind(zone_id, "<Double-Button-1>",
                            lambda e, j=jour, h=heure_str: self._ouvrir_form_ajout(j, h))
                cv.tag_bind(zone_id, "<Enter>",
                            lambda e, i=zone_id: cv.itemconfig(i, fill="#E3F2FD"))
                cv.tag_bind(zone_id, "<Leave>",
                            lambda e, i=zone_id: cv.itemconfig(i, fill=""))

        cv.configure(scrollregion=(0, 0, total_w, total_h))

    # ── Formulaires CRUD ──────────────────────────────────────────────────────

    def _ouvrir_form_ajout(self, jour_pre: str = "", heure_pre: str = ""):
        if not self._classe_id:
            messagebox.showwarning("Classe", "Sélectionnez une classe.")
            return
        _FormCreneau(self, self.db, self._classe_id, ANNEE,
                     on_save=self._charger_grille,
                     jour_pre=jour_pre, heure_pre=heure_pre)

    def _ouvrir_form_modif(self, creneau: dict):
        _FormCreneau(self, self.db, self._classe_id, ANNEE,
                     on_save=self._charger_grille,
                     creneau=creneau)

    def _imprimer_edt(self):
        if not self._classe_id:
            messagebox.showwarning("Classe", "Sélectionnez une classe d'abord.")
            return
            
        classe_nom = self._classe_var.get()
        creneaux = self.db.get_emploi_classe(self._classe_id, ANNEE)
        
        if not creneaux:
            messagebox.showinfo("Vide", "Aucun créneau pour cette classe.")
            return
            
        fpath = filedialog.asksaveasfilename(
            title="Enregistrer l'emploi du temps",
            defaultextension=".pdf",
            initialfile=f"EDT_{classe_nom.replace(' ', '_')}_{ANNEE}.pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if fpath:
            try:
                from utils.pdf_generator import generate_timetable_pdf
                ok = generate_timetable_pdf(classe_nom, ANNEE, creneaux, fpath)
                if ok:
                    messagebox.showinfo("Succès", f"Emploi du temps enregistré sous :\n{fpath}")
                else:
                    messagebox.showerror("Erreur", "La création du PDF a échoué.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération PDF : {e}")


# ── Formulaire créneau ──────────────────────────────────────────────────────

class _FormCreneau(CTkToplevel):

    def __init__(self, parent, db: VieScolaireDB, classe_id: int,
                 annee: str, on_save, jour_pre="", heure_pre="",
                 creneau: dict | None = None):
        super().__init__(parent)
        self.db = db; self.classe_id = classe_id
        self.annee = annee; self.on_save = on_save; self.creneau = creneau

        titre = "Modifier le créneau" if creneau else "Nouveau créneau"
        self.title(titre); self.geometry("460x400"); self.grab_set(); self.resizable(False, False)

        self._matieres = db.get_matieres()
        self._profs    = db.get_professeurs()

        CTkLabel(self, text=titre, font=FONT_TITLE, text_color=PRIMARY_BLUE).pack(pady=(16,6))

        form = CTkFrame(self, fg_color="white", corner_radius=12)
        form.pack(fill=BOTH, padx=20, pady=4, expand=True)

        fields = [
            ("Jour :",         "jour"),
            ("Matière :",      "mat"),
            ("Début :",        "deb"),
            ("Fin :",          "fin"),
            ("Professeur :",   "prof"),
            ("Salle :",        "salle"),
        ]
        self._vars: dict[str, StringVar] = {}

        for i, (lbl, key) in enumerate(fields):
            CTkLabel(form, text=lbl, font=FONT_LABEL,
                     text_color=TEXT_DARK).grid(row=i, column=0, sticky="w", padx=16, pady=7)
            if key == "jour":
                v = StringVar(value=creneau["jour"] if creneau else (jour_pre or JOURS[0]))
                CTkComboBox(form, variable=v, values=JOURS,
                            state="readonly", width=200).grid(row=i, column=1, padx=8)
            elif key == "mat":
                noms = [m["nom_matiere"] for m in self._matieres]
                v = StringVar(value=creneau["nom_matiere"] if creneau else (noms[0] if noms else ""))
                CTkComboBox(form, variable=v, values=noms,
                            state="readonly", width=200).grid(row=i, column=1, padx=8)
            elif key in ("deb", "fin"):
                default = (str(creneau["heure_debut"])[:5] if creneau and key == "deb"
                           else str(creneau["heure_fin"])[:5] if creneau and key == "fin"
                           else heure_pre if key == "deb" else "09:00")
                v = StringVar(value=default)
                CTkComboBox(form, variable=v, values=HEURES_DISPO,
                            width=130).grid(row=i, column=1, padx=8, sticky="w")
            elif key == "prof":
                noms_p = ["— Aucun —"] + [f"{p['nom']} {p['prenom']}" for p in self._profs]
                default_p = "— Aucun —"
                if creneau and creneau.get("prof_nom", "").strip():
                    default_p = creneau["prof_nom"].strip()
                v = StringVar(value=default_p)
                CTkComboBox(form, variable=v, values=noms_p,
                            state="readonly", width=200).grid(row=i, column=1, padx=8)
            else:  # salle
                v = StringVar(value=creneau.get("salle", "") if creneau else "")
                CTkEntry(form, textvariable=v, width=200,
                         placeholder_text="ex: Salle B3").grid(row=i, column=1, padx=8)
            self._vars[key] = v

        btn_frame = CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill=X, padx=20, pady=10)
        CTkButton(btn_frame, text="💾 Enregistrer", font=FONT_LABEL,
                  fg_color=PRIMARY_BLUE, hover_color=SECONDARY_BLUE,
                  text_color="white", command=self._save).pack(side=LEFT, expand=True, padx=4)
        if creneau:
            CTkButton(btn_frame, text="🗑 Supprimer", font=FONT_LABEL,
                      fg_color=VS_ROUGE, hover_color="#B71C1C",
                      text_color="white", command=self._delete).pack(side=LEFT, expand=True, padx=4)
        CTkButton(btn_frame, text="Annuler", font=FONT_LABEL,
                  fg_color="gray", text_color="white",
                  command=self.destroy).pack(side=LEFT, expand=True, padx=4)

    def _get_mat_id(self) -> int | None:
        nom = self._vars["mat"].get()
        for m in self._matieres:
            if m["nom_matiere"] == nom: return m["id_matiere"]
        return None

    def _get_prof_id(self) -> int | None:
        nom = self._vars["prof"].get()
        if nom == "— Aucun —": return None
        for p in self._profs:
            if f"{p['nom']} {p['prenom']}" == nom: return p["id_professeur"]
        return None

    def _save(self):
        mid = self._get_mat_id()
        if not mid:
            messagebox.showwarning("Erreur", "Sélectionnez une matière."); return
        h_deb = self._vars["deb"].get()
        h_fin = self._vars["fin"].get()
        if h_fin <= h_deb:
            messagebox.showwarning("Heure", "La fin doit être après le début."); return
        jour  = self._vars["jour"].get()
        pid   = self._get_prof_id()
        salle = self._vars["salle"].get().strip()
        try:
            if self.creneau:
                self.db.update_creneau(self.creneau["id"], mid, pid, jour, h_deb, h_fin, salle)
                messagebox.showinfo("Succès", "Créneau modifié.")
            else:
                self.db.add_creneau(self.classe_id, mid, pid, jour, h_deb, h_fin, salle, self.annee)
                messagebox.showinfo("Succès", "Créneau ajouté.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e)); return
        self.on_save(); self.destroy()

    def _delete(self):
        if messagebox.askyesno("Confirmer", "Supprimer ce créneau ?"):
            self.db.delete_creneau(self.creneau["id"])
            self.on_save(); self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET B — ABSENCES
# ══════════════════════════════════════════════════════════════════════════════

class _OngletAbsences(CTkFrame):

    def __init__(self, parent, db: VieScolaireDB, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(parent, **kw)
        self.db = db
        self._classe_id: int | None = None
        self._classes:   list[dict] = []
        self._eleves:    list[dict] = []
        self._creneaux_edt: list[dict] = []
        self._absence_ids:  list[int]  = []
        self._build()

    def _build(self):
        top = CTkFrame(self, fg_color=PRIMARY_BLUE, height=54)
        top.pack(fill=X); top.pack_propagate(False)

        CTkLabel(top, text="Classe :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(12,4), pady=14)
        self._classe_var = StringVar()
        self._classe_cb = CTkComboBox(
            top, variable=self._classe_var, state="readonly", width=140,
            command=lambda _: self._on_classe_change(),
            fg_color=BACKGROUND_LIGHT, text_color=TEXT_DARK,
            border_color=PRIMARY_BLUE, button_color=PRIMARY_BLUE)
        self._classe_cb.pack(side=LEFT, padx=4)

        CTkLabel(top, text="Date :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(12,4))
        self._date_entry = CTkEntry(top, width=110, placeholder_text="AAAA-MM-JJ")
        self._date_entry.insert(0, datetime.date.today().isoformat())
        self._date_entry.pack(side=LEFT, padx=4)

        CTkLabel(top, text="Trim :", font=FONT_LABEL,
                 text_color="white", fg_color=PRIMARY_BLUE).pack(side=LEFT, padx=(12,4))
        self._trim_var = StringVar(value=str(TRIMESTRE_ACTUEL))
        for t in ("1", "2", "3"):
            CTkRadioButton(top, text=f"T{t}", variable=self._trim_var, value=t,
                           font=FONT_LABEL, text_color="white",
                           fg_color=BACKGROUND_LIGHT, border_color="white",
                           command=self._charger_absences).pack(side=LEFT, padx=3)

        CTkButton(top, text="🔍 Actualiser", font=FONT_LABEL,
                  fg_color=SUCCESS_GREEN, hover_color="#1B5E20",
                  text_color="white", width=120,
                  command=self._charger_absences).pack(side=RIGHT, padx=12)

        body = CTkFrame(self, fg_color=BACKGROUND_LIGHT)
        body.pack(fill=BOTH, expand=True, padx=8, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # ── Gauche : saisie ────────────────────────────────────────────────
        left = CTkFrame(body, fg_color="white", corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        CTkLabel(left, text="Saisir une absence", font=FONT_TITLE,
                 text_color=PRIMARY_BLUE).pack(pady=(14, 8))

        form = CTkFrame(left, fg_color="white")
        form.pack(fill=X, padx=16)

        lf = [
            ("Élève :",        "eleve"),
            ("Heure début :",  "deb"),
            ("Heure fin :",    "fin"),
            ("Statut :",       "statut"),
            ("Motif :",        "motif"),
            ("Créneau EDT :",  "creneau"),
        ]
        self._saisie_vars: dict[str, StringVar] = {}
        for i, (label, key) in enumerate(lf):
            CTkLabel(form, text=label, font=FONT_LABEL,
                     text_color=TEXT_DARK).grid(row=i, column=0, sticky="w", pady=6)
            if key == "eleve":
                v = StringVar()
                CTkComboBox(form, variable=v, state="readonly", width=200).grid(
                    row=i, column=1, padx=8, pady=6)
                self._eleve_cb = form.winfo_children()[-1]
            elif key in ("deb", "fin"):
                v = StringVar(value="08:00" if key == "deb" else "09:00")
                CTkComboBox(form, variable=v, values=HEURES_DISPO,
                            width=120).grid(row=i, column=1, padx=8, pady=6, sticky="w")
            elif key == "statut":
                v = StringVar(value="NON_JUSTIFIEE")
                CTkComboBox(form, variable=v, values=["NON_JUSTIFIEE", "JUSTIFIEE"],
                            state="readonly", width=170).grid(row=i, column=1, padx=8, pady=6)
            elif key == "motif":
                v = StringVar()
                CTkEntry(form, textvariable=v, width=200,
                         placeholder_text="(facultatif)").grid(row=i, column=1, padx=8, pady=6)
            elif key == "creneau":
                v = StringVar(value="— Manuel —")
                cb = CTkComboBox(form, variable=v, values=["— Manuel —"],
                                 state="readonly", width=200)
                cb.grid(row=i, column=1, padx=8, pady=6)
                self._creneau_cb = cb
            self._saisie_vars[key] = v

        CTkButton(left, text="➕ Enregistrer l'absence",
                  font=FONT_LABEL, fg_color=VS_ROUGE,
                  hover_color="#B71C1C", text_color="white",
                  command=self._sauver_absence).pack(pady=14, padx=20, fill=X)

        # ── Droite : tableau ───────────────────────────────────────────────
        right = CTkFrame(body, fg_color="white", corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew")

        CTkLabel(right, text="Absences du jour", font=FONT_TITLE,
                 text_color=PRIMARY_BLUE).pack(pady=(14, 6))

        style = ttk.Style()
        try: style.theme_use("clam")
        except: pass
        style.configure("Abs.Treeview",
            background="white", fieldbackground="white",
            foreground=TEXT_DARK, rowheight=28, font=FONT_LABEL)
        style.configure("Abs.Treeview.Heading",
            background=PRIMARY_BLUE, foreground="white", font=FONT_LABEL, relief="flat")

        wrap = CTkFrame(right, fg_color="white")
        wrap.pack(fill=BOTH, expand=True, padx=8, pady=4)

        cols = ("nom_prenom", "heure", "statut", "motif")
        self._tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                   style="Abs.Treeview", selectmode="browse")
        for col, lbl, w in [("nom_prenom","Élève",200),("heure","Horaire",120),
                              ("statut","Statut",130),("motif","Motif",200)]:
            self._tree.heading(col, text=lbl)
            self._tree.column(col, width=w)
        self._tree.tag_configure("NJ", foreground=VS_ROUGE)
        self._tree.tag_configure("J",  foreground=VS_VERT)

        sb = ttk.Scrollbar(wrap, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=LEFT, fill=Y)

        actions = CTkFrame(right, fg_color="white")
        actions.pack(fill=X, padx=8, pady=8)
        CTkButton(actions, text="✅ Justifier", font=FONT_LABEL,
                  fg_color=VS_VERT, hover_color="#1B5E20", text_color="white", width=140,
                  command=self._justifier_selection).pack(side=LEFT, padx=4)
        CTkButton(actions, text="❌ Annuler justif.", font=FONT_LABEL,
                  fg_color=VS_ORANGE, hover_color="#BF360C", text_color="white", width=160,
                  command=self._annuler_justif).pack(side=LEFT, padx=4)
        CTkButton(actions, text="🗑 Supprimer", font=FONT_LABEL,
                  fg_color=VS_ROUGE, hover_color="#B71C1C", text_color="white", width=130,
                  command=self._supprimer_selection).pack(side=LEFT, padx=4)

    # ── API ───────────────────────────────────────────────────────────────────

    def refresh(self):
        self._classes = self.db.get_classes()
        noms = [c["nom_classe"] for c in self._classes]
        self._classe_cb.configure(values=noms)
        if noms:
            if self._classe_var.get() not in noms:
                self._classe_var.set(noms[0])
            self._on_classe_change()

    def _get_classe_id(self):
        nom = self._classe_var.get()
        for c in self._classes:
            if c["nom_classe"] == nom: return c["id"]
        return None

    def _on_classe_change(self):
        self._classe_id = self._get_classe_id()
        if not self._classe_id: return
        self._eleves = self.db.get_eleves_classe(self._classe_id)
        noms = [f"{e['nom']} {e['prenom']}" for e in self._eleves]
        self._eleve_cb.configure(values=noms)
        if noms: self._saisie_vars["eleve"].set(noms[0])
        self._recharger_creneaux_edt()
        self._charger_absences()

    def _recharger_creneaux_edt(self):
        date_str = self._date_entry.get().strip()
        try:
            dt = datetime.date.fromisoformat(date_str)
            jour_fr = JOURS[dt.weekday()] if dt.weekday() < 6 else JOURS[-1]
        except ValueError:
            jour_fr = JOURS[0]
        if self._classe_id:
            self._creneaux_edt = self.db.get_creneaux_par_jour(self._classe_id, jour_fr, ANNEE)
            vals = ["— Manuel —"] + [
                f"{str(c['heure_debut'])[:5]}–{str(c['heure_fin'])[:5]} {c['nom_matiere']}"
                for c in self._creneaux_edt]
            self._creneau_cb.configure(values=vals)
            self._saisie_vars["creneau"].set(vals[0])
        else:
            self._creneaux_edt = []

    def _charger_absences(self):
        for r in self._tree.get_children(): self._tree.delete(r)
        self._absence_ids.clear()
        if not self._classe_id: return
        date_str = self._date_entry.get().strip()
        if not date_str: return
        rows = self.db.get_absences_classe_date(self._classe_id, date_str, ANNEE)
        for row in rows:
            h_deb = str(row["heure_debut"])[:5]
            h_fin = str(row["heure_fin"])[:5]
            tag = "NJ" if row["statut"] == "NON_JUSTIFIEE" else "J"
            statut_lbl = "⚠️ Non justifiée" if row["statut"] == "NON_JUSTIFIEE" else "✅ Justifiée"
            self._tree.insert("", END, tags=(tag,), values=(
                f"{row['nom']} {row['prenom']}", f"{h_deb} → {h_fin}",
                statut_lbl, row.get("motif") or "—"))
            self._absence_ids.append(row["id"])

    def _sauver_absence(self):
        if not self._eleves:
            messagebox.showwarning("Erreur", "Aucun élève."); return
        nom_sel = self._saisie_vars["eleve"].get()
        eleve = next((e for e in self._eleves if f"{e['nom']} {e['prenom']}" == nom_sel), None)
        if not eleve:
            messagebox.showwarning("Erreur", "Élève introuvable."); return
        date_str = self._date_entry.get().strip()
        try: datetime.date.fromisoformat(date_str)
        except ValueError:
            messagebox.showwarning("Date", "Format invalide (AAAA-MM-JJ)."); return
        h_deb = self._saisie_vars["deb"].get()
        h_fin = self._saisie_vars["fin"].get()
        if h_fin <= h_deb:
            messagebox.showwarning("Heure", "La fin doit être après le début."); return
        creneau_id = None
        creneau_sel = self._saisie_vars["creneau"].get()
        if creneau_sel != "— Manuel —":
            for c in self._creneaux_edt:
                lbl = f"{str(c['heure_debut'])[:5]}–{str(c['heure_fin'])[:5]} {c['nom_matiere']}"
                if lbl == creneau_sel:
                    creneau_id = c["id"]
                    h_deb = str(c["heure_debut"])[:5]
                    h_fin = str(c["heure_fin"])[:5]
                    break
        try:
            self.db.add_absence(
                eleve_id=eleve["id"], date_absence=date_str,
                heure_debut=h_deb, heure_fin=h_fin,
                trimestre=int(self._trim_var.get()), annee=ANNEE,
                statut=self._saisie_vars["statut"].get(),
                motif=self._saisie_vars["motif"].get().strip(),
                creneau_id=creneau_id)
            messagebox.showinfo("Succès", "Absence enregistrée.")
            self._charger_absences()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _get_selected_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez une absence."); return None
        idx = self._tree.index(sel[0])
        return self._absence_ids[idx] if idx < len(self._absence_ids) else None

    def _justifier_selection(self):
        aid = self._get_selected_id()
        if aid is None: return
        dlg = CTkInputDialog(text="Motif (facultatif) :", title="Justifier")
        motif = dlg.get_input() or ""
        self.db.justifier_absence(aid, motif)
        messagebox.showinfo("Succès", "Absence justifiée.")
        self._charger_absences()

    def _annuler_justif(self):
        aid = self._get_selected_id()
        if aid is None: return
        if messagebox.askyesno("Confirmer", "Repasser en NON JUSTIFIÉE ?"):
            self.db.annuler_justification(aid); self._charger_absences()

    def _supprimer_selection(self):
        aid = self._get_selected_id()
        if aid is None: return
        if messagebox.askyesno("Confirmer", "Supprimer cette absence ?"):
            self.db.delete_absence(aid); self._charger_absences()


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET C — CONFIGURATION  (layout gauche / droite)
# ══════════════════════════════════════════════════════════════════════════════

class _OngletConfig(CTkFrame):
    """
    Layout en deux colonnes :
      GAUCHE  : formulaire de saisie des paramètres
      DROITE  : aperçu de la règle + bouton Enregistrer
    """

    def __init__(self, parent, db: VieScolaireDB, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(parent, **kw)
        self.db = db
        self._build()

    def _build(self):
        CTkLabel(self, text="⚙️  Configuration des pénalités d'absence",
                 font=FONT_TITLE, text_color=PRIMARY_BLUE).pack(pady=(18, 4))
        CTkLabel(self,
                 text="La pénalité est soustraite du total de points (Σ moy×coeff) avant le calcul de la moyenne.",
                 font=FONT_LABEL, text_color=TEXT_DARK, wraplength=780).pack(pady=(0, 14))

        # Zone principale 2 colonnes
        body = CTkFrame(self, fg_color=BACKGROUND_LIGHT)
        body.pack(fill=BOTH, expand=True, padx=30, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── GAUCHE : formulaire ────────────────────────────────────────────
        left = CTkFrame(body, fg_color="white", corner_radius=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        CTkLabel(left, text="📋  Paramètres", font=FONT_TITLE,
                 text_color=PRIMARY_BLUE).pack(pady=(16, 10))

        form = CTkFrame(left, fg_color="white")
        form.pack(fill=X, padx=24)

        cfg_rows = [
            ("Tranche d'heures NJ", "tranche",
             "Nb d'heures déclenchant 1 palier (ex: 5)"),
            ("Points retirés / palier", "pts_pal",
             "Retrait en points sur le total (ex: 2)"),
            ("Plafond de retrait (pts)", "plafond",
             "Maximum de points pouvant être retirés (ex: 20)"),
        ]
        self._entries: dict[str, CTkEntry] = {}
        for i, (label, key, hint) in enumerate(cfg_rows):
            CTkLabel(form, text=label, font=FONT_LABEL,
                     text_color=TEXT_DARK).grid(row=i*2, column=0, sticky="w", pady=(10, 0))
            CTkLabel(form, text=hint, font=("Calibri", 10),
                     text_color="gray").grid(row=i*2, column=1, sticky="w", padx=8, pady=(10, 0))
            e = CTkEntry(form, width=100, font=FONT_LABEL,
                         border_color=PRIMARY_BLUE)
            e.grid(row=i*2+1, column=0, sticky="w", pady=(2, 6))
            self._entries[key] = e

        CTkLabel(form, text="Description", font=FONT_LABEL,
                 text_color=TEXT_DARK).grid(row=6, column=0, sticky="w", pady=(10, 0), columnspan=2)
        self._desc_entry = CTkEntry(form, width=340, font=FONT_LABEL,
                                     border_color=PRIMARY_BLUE)
        self._desc_entry.grid(row=7, column=0, columnspan=2, sticky="w", pady=(2, 6))

        # ── DROITE : aperçu + bouton enregistrer ───────────────────────────
        right = CTkFrame(body, fg_color="white", corner_radius=14)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)

        CTkLabel(right, text="📌  Aperçu de la règle", font=FONT_TITLE,
                 text_color=PRIMARY_BLUE).pack(pady=(16, 10))

        self._preview_lbl = CTkLabel(
            right, text="",
            font=("Calibri", 13),
            text_color=VS_BLEU,
            wraplength=340,
            justify="left",
            fg_color="#EEF4FB",
            corner_radius=10)
        self._preview_lbl.pack(fill=X, padx=20, pady=8, ipady=14)

        # Explication formule
        CTkLabel(right,
                 text="Formule trimestrielle :\n"
                      "① total_pts = Σ(moy_matière × coeff)\n"
                      "② pénalité  = paliers × pts_palier\n"
                      "③ pts_nets  = total_pts − pénalité\n"
                      "④ moy_trim  = pts_nets / Σ(coeff)",
                 font=("Calibri", 12),
                 text_color=TEXT_DARK,
                 justify="left",
                 fg_color="#F5F5F5",
                 corner_radius=8).pack(fill=X, padx=20, pady=(8, 12), ipady=10)

        # Bouton Enregistrer à DROITE (pas en bas de page)
        CTkButton(right,
                  text="💾  Enregistrer la configuration",
                  font=FONT_TITLE,
                  fg_color=PRIMARY_BLUE,
                  hover_color=SECONDARY_BLUE,
                  text_color="white",
                  height=44,
                  command=self._sauver).pack(fill=X, padx=20, pady=(4, 20))

    def refresh(self):
        cfg = self.db.get_config_discipline()
        if not cfg: return
        self._entries["tranche"].delete(0, END)
        self._entries["tranche"].insert(0, str(cfg["tranche_heures"]))
        self._entries["pts_pal"].delete(0, END)
        self._entries["pts_pal"].insert(0, str(cfg["points_par_palier"]))
        self._entries["plafond"].delete(0, END)
        self._entries["plafond"].insert(0, str(cfg["plafond_points"]))
        self._desc_entry.delete(0, END)
        self._desc_entry.insert(0, cfg.get("description") or "")
        self._update_preview(cfg)

    def _update_preview(self, cfg: dict):
        t = float(cfg.get("tranche_heures", 5))
        p = float(cfg.get("points_par_palier", 2))
        m = float(cfg.get("plafond_points", 20))
        ex1_h = t + 1
        ex2_h = t * 2 + 1
        txt = (f"Toutes les {t:.0f}h d'absence NJ\n"
               f"→  −{p:.1f} pt sur le total trimestriel\n\n"
               f"Plafond : −{m:.0f} pts maximum\n\n"
               f"Exemples :\n"
               f"  {ex1_h:.0f}h NJ  →  1 palier  →  −{p:.1f} pt\n"
               f"  {ex2_h:.0f}h NJ  →  2 paliers →  −{p*2:.1f} pts\n"
               f"  ≥{int(m/p)*t:.0f}h NJ →  plafonné →  −{m:.0f} pts")
        self._preview_lbl.configure(text=txt)

    def _sauver(self):
        try:
            tranche = float(self._entries["tranche"].get())
            pts_pal = float(self._entries["pts_pal"].get())
            plafond = float(self._entries["plafond"].get())
            desc    = self._desc_entry.get().strip()
        except ValueError:
            messagebox.showerror("Erreur", "Valeurs numériques requises."); return
        if tranche <= 0 or pts_pal <= 0 or plafond <= 0:
            messagebox.showerror("Erreur", "Les valeurs doivent être > 0."); return
        self.db.update_config_discipline(tranche, pts_pal, plafond, desc)
        messagebox.showinfo("Succès", "Configuration enregistrée.")
        self.refresh()


# ══════════════════════════════════════════════════════════════════════════════
# VUE PRINCIPALE — VieScolaireView
# ══════════════════════════════════════════════════════════════════════════════

class VieScolaireView(CTkFrame):

    POLL_INTERVAL_MS = 30_000

    def __init__(self, master, db, **kw):
        kw.setdefault("fg_color", BACKGROUND_LIGHT)
        super().__init__(master, **kw)
        self.vs_db = VieScolaireDB(db.connection)
        self._notif_label = None
        self._poll_job: str | None = None
        self._last_absence_ts: datetime.datetime | None = None
        self._build()

    def _build(self):
        titre = CTkFrame(self, fg_color="lightblue", height=50)
        titre.pack(fill=X, side=TOP); titre.pack_propagate(False)
        CTkLabel(titre, text="📅  Vie Scolaire — Emploi du Temps & Absences",
                 font=FONT_TITLE, text_color=PRIMARY_BLUE,
                 fg_color="lightblue").pack(pady=12)

        self._tabs = CTkTabview(self, fg_color=BACKGROUND_LIGHT,
                                segmented_button_fg_color=PRIMARY_BLUE,
                                segmented_button_selected_color=SECONDARY_BLUE,
                                segmented_button_unselected_color=PRIMARY_BLUE,
                                segmented_button_selected_hover_color=SECONDARY_BLUE,
                                text_color="white",
                                text_color_disabled="white")
        self._tabs.pack(fill=BOTH, expand=True, padx=8, pady=8)

        for tab in ("📅 Emploi du Temps", "📋 Absences", "⚙️ Configuration"):
            self._tabs.add(tab)

        self._ong_edt = _OngletEmploiDuTemps(self._tabs.tab("📅 Emploi du Temps"), self.vs_db)
        self._ong_edt.pack(fill=BOTH, expand=True)

        self._ong_abs = _OngletAbsences(self._tabs.tab("📋 Absences"), self.vs_db)
        self._ong_abs.pack(fill=BOTH, expand=True)

        self._ong_cfg = _OngletConfig(self._tabs.tab("⚙️ Configuration"), self.vs_db)
        self._ong_cfg.pack(fill=BOTH, expand=True)

    def refresh(self):
        self._ong_edt.refresh()
        self._ong_abs.refresh()
        self._ong_cfg.refresh()
        if self._last_absence_ts is None:
            self._last_absence_ts = self.vs_db.get_last_absence_ts(ANNEE)

    def start_global_polling(self):
        if self._poll_job is not None: return
        self._run_poll()

    def stop_global_polling(self):
        if self._poll_job:
            try: self.after_cancel(self._poll_job)
            except: pass
            self._poll_job = None

    def _run_poll(self):
        try:
            ts = self.vs_db.get_last_absence_ts(ANNEE)
            if ts and (self._last_absence_ts is None or ts > self._last_absence_ts):
                self._last_absence_ts = ts
                if self._notif_label:
                    try:
                        n = int(self._notif_label.cget("text"))
                        self._notif_label.configure(text=str(n + 1))
                    except: self._notif_label.configure(text="!")
                try: self._ong_abs._charger_absences()
                except: pass
        except Exception as e:
            print(f"[VieScolaire._run_poll] {e}")
        self._poll_job = self.after(self.POLL_INTERVAL_MS, self._run_poll)

    def _stop_auto_refresh(self):
        self.stop_global_polling()