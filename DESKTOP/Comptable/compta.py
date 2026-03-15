"""
compta.py  --  Academix Comptabilite & Caisse  v2
==================================================
Tkinter pur | constant.py | mysql-connector-python
Nouvelles fonctions : annulation, remises, cloture, recherche recu,
raccourcis clavier F1/F5/Entree, theme clair/sombre, filtres rapides.
"""
from tkinter import *
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading, datetime, os
import constant as C
from data.db_compta_manager import ComptaDB
from data.recu import generer_recu_pdf, generer_insolvables_pdf, open_pdf, montant_en_lettres

ANNEE = C.ANNEE_SCOLAIRE

# ══════════════════════════════════════════════════════════════════════════════
# Theme manager  -- applique les couleurs a tous les widgets enregistres
# ══════════════════════════════════════════════════════════════════════════════
_theme_listeners = []  # list of callables

def register_theme(fn):
    _theme_listeners.append(fn)

def apply_theme_all():
    C._load()
    for fn in _theme_listeners:
        try: fn()
        except Exception: pass
    _restyle_trees()

# ── Treeview style ────────────────────────────────────────────────────────────
_trees_registered = []

def _restyle_trees():
    s = ttk.Style()
    try: s.theme_use("clam")
    except: pass
    s.configure("A.Treeview",
        background=C.TREE_BG, fieldbackground=C.TREE_BG,
        foreground=C.TEXT_DARK, rowheight=C.ROW_HEIGHT, font=C.TEXT_SECONDARY)
    s.configure("A.Treeview.Heading",
        background=C.PRIMARY_BLUE, foreground=C.TEXT_WHITE,
        font=C.FONT_SECTION, relief="flat")
    s.map("A.Treeview",
        background=[("selected", C.ACCENT_BLUE)],
        foreground=[("selected", C.TEXT_WHITE)])

def _style_tree(tree):
    _restyle_trees()
    tree.configure(style="A.Treeview")
    _trees_registered.append(tree)

# ══════════════════════════════════════════════════════════════════════════════
# Widgets utilitaires
# ══════════════════════════════════════════════════════════════════════════════

class _W:
    """Namespace: fabrique des widgets avec les couleurs du theme actif."""
    @staticmethod
    def card(parent, **kw):
        kw.setdefault("bg", C.CARD_BG); kw.setdefault("relief", GROOVE); kw.setdefault("bd",1)
        return Frame(parent, **kw)

    @staticmethod
    def btn_primary(parent, **kw):
        kw.setdefault("font",C.TEXT_BOLD); kw.setdefault("fg",C.TEXT_WHITE)
        kw.setdefault("bg",C.PRIMARY_BLUE); kw.setdefault("activebackground",C.ACCENT_BLUE)
        kw.setdefault("activeforeground",C.TEXT_WHITE); kw.setdefault("relief",FLAT)
        kw.setdefault("cursor","hand2"); kw.setdefault("padx",10); kw.setdefault("pady",4)
        return Button(parent, **kw)

    @staticmethod
    def btn_danger(parent, **kw):
        kw.setdefault("font",C.TEXT_BOLD); kw.setdefault("fg",C.TEXT_WHITE)
        kw.setdefault("bg",C.DANGER_RED); kw.setdefault("activebackground","#A93226")
        kw.setdefault("activeforeground",C.TEXT_WHITE); kw.setdefault("relief",FLAT)
        kw.setdefault("cursor","hand2"); kw.setdefault("padx",8); kw.setdefault("pady",4)
        return Button(parent, **kw)

    @staticmethod
    def btn_success(parent, **kw):
        kw.setdefault("font",C.TEXT_BOLD); kw.setdefault("fg",C.TEXT_WHITE)
        kw.setdefault("bg",C.SUCCESS_GREEN); kw.setdefault("activebackground","#17753A")
        kw.setdefault("activeforeground",C.TEXT_WHITE); kw.setdefault("relief",FLAT)
        kw.setdefault("cursor","hand2"); kw.setdefault("padx",10); kw.setdefault("pady",4)
        return Button(parent, **kw)

    @staticmethod
    def section_bar(parent, text:str, color:str=None, **kw):
        color = color or C.PRIMARY_BLUE
        kw.setdefault("bg", color)
        f = Frame(parent, **kw)
        Label(f, text=text, font=C.FONT_SECTION, fg=C.TEXT_WHITE, bg=color
              ).pack(side=LEFT, padx=10, pady=5)
        return f

    @staticmethod
    def kpi_card(parent, title:str, icon:str, color:str):
        f = Frame(parent, bg=C.WHITE, relief=GROOVE, bd=2)
        f.configure(highlightbackground=color, highlightthickness=2)
        Label(f, text=icon, font=("Segoe UI",18), bg=C.WHITE, fg=color).pack(pady=(8,0))
        Label(f, text=title, font=C.FONT_KPI_LBL, bg=C.WHITE, fg=C.TEXT_GRAY).pack()
        val = Label(f, text="--", font=C.FONT_KPI, bg=C.WHITE, fg=color)
        val.pack(pady=(0,8))
        return f, val


# ══════════════════════════════════════════════════════════════════════════════
# Barre de recherche rapide (recu / eleve)
# ══════════════════════════════════════════════════════════════════════════════

class FenetreRecherche(Toplevel):
    def __init__(self, parent, db:ComptaDB):
        super().__init__(parent)
        self.db = db
        self.title("Recherche -- Recu / Eleve  [F1]")
        self.geometry("720x480")
        self.resizable(True,True)
        self.configure(bg=C.CARD_BG)
        self._build()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        top = Frame(self, bg=C.LIGHT_BLUE)
        top.pack(fill=X)
        Label(top, text="Recherche rapide", font=C.FONT_SUBTITLE,
              fg=C.PRIMARY_BLUE, bg=C.LIGHT_BLUE).pack(side=LEFT, padx=12, pady=8)

        bar = Frame(self, bg=C.CARD_BG)
        bar.pack(fill=X, padx=12, pady=8)
        Label(bar, text="N recu ou nom :", font=C.TEXT_BOLD,
              fg=C.TEXT_DARK, bg=C.CARD_BG).pack(side=LEFT)
        self._q = StringVar()
        e = Entry(bar, textvariable=self._q, font=C.TEXT_SECONDARY,
                  relief=SOLID, bd=1, width=30)
        e.pack(side=LEFT, padx=8)
        e.bind("<Return>", lambda _: self._search())
        e.focus_set()
        _W.btn_primary(bar, text="Rechercher", command=self._search).pack(side=LEFT)

        cols = ("recu","date","eleve","classe","type","montant","statut")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        _style_tree(self._tree)
        for c,w,lbl in [("recu",145,"N Recu"),("date",115,"Date"),("eleve",160,"Eleve"),
                         ("classe",75,"Classe"),("type",120,"Type"),("montant",95,"Montant"),
                         ("statut",70,"Statut")]:
            self._tree.heading(c, text=lbl)
            self._tree.column(c, width=w, anchor=CENTER)
        self._tree.tag_configure("annule", foreground=C.DANGER_RED)
        sb = ttk.Scrollbar(self, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=LEFT, fill=BOTH, expand=True, padx=(12,0), pady=(0,8))
        sb.pack(side=LEFT, fill=Y, pady=(0,8), padx=(0,8))

    def _search(self):
        for r in self._tree.get_children(): self._tree.delete(r)
        q = self._q.get().strip()
        if not q: return
        rows = self.db.rechercher_recu(q)
        for p in rows:
            dt = p["date_paiement"]
            dt_s = dt.strftime("%d/%m/%Y") if isinstance(dt,datetime.datetime) else str(dt)
            statut = "ANNULE" if p.get("annule") else "OK"
            tag = ("annule",) if p.get("annule") else ()
            self._tree.insert("", END, tags=tag, values=(
                p["recu_num"], dt_s,
                f"{p['eleve_nom']} {p['eleve_prenom']}",
                p.get("classe_reelle",""), p["type_nom"],
                f"{float(p['montant']):,.0f} FCFA", statut))


# ══════════════════════════════════════════════════════════════════════════════
# Fenetre : Remise pour un eleve
# ══════════════════════════════════════════════════════════════════════════════

class FenetreRemise(Toplevel):
    def __init__(self, parent, db:ComptaDB, eleve:dict, on_success=None):
        super().__init__(parent)
        self.db=db; self.eleve=eleve; self.on_success=on_success
        self.title(f"Remises -- {eleve['nom']} {eleve['prenom']}")
        self.geometry("540x420"); self.resizable(False,False)
        self.grab_set(); self.configure(bg=C.WHITE); self._build()

    def _build(self):
        Label(self, text=f"Remises / Reductions  --  {self.eleve['nom']} {self.eleve['prenom']}",
              font=C.FONT_SUBTITLE, fg=C.PRIMARY_BLUE, bg=C.WHITE).pack(pady=(12,4))

        types = self.db.get_types_frais()
        remises_act = {r["type_frais_id"]: r
                       for r in self.db.get_remises_eleve(self.eleve["id"], ANNEE)}
        self._rows = []
        form = Frame(self, bg=C.WHITE)
        form.pack(fill=X, padx=20)
        Label(form, text="Type de frais", font=C.TEXT_BOLD, fg=C.TEXT_DARK, bg=C.WHITE
              ).grid(row=0,column=0,sticky=W,padx=4,pady=(8,2))
        Label(form, text="Remise (FCFA)", font=C.TEXT_BOLD, fg=C.TEXT_DARK, bg=C.WHITE
              ).grid(row=0,column=1,sticky=W,padx=4,pady=(8,2))
        Label(form, text="Motif", font=C.TEXT_BOLD, fg=C.TEXT_DARK, bg=C.WHITE
              ).grid(row=0,column=2,sticky=W,padx=4,pady=(8,2))
        for i,tf in enumerate(types,1):
            act = remises_act.get(tf["id"])
            Label(form, text=tf["nom"], font=C.TEXT_SECONDARY, fg=C.TEXT_DARK, bg=C.WHITE
                  ).grid(row=i,column=0,sticky=W,padx=4,pady=3)
            mnt = StringVar(value=str(int(float(act["montant_remise"]))) if act else "0")
            motif = StringVar(value=act["motif"] if act else "")
            Entry(form, textvariable=mnt, font=C.TEXT_SECONDARY, relief=SOLID,bd=1,width=14
                  ).grid(row=i,column=1,padx=4,pady=3)
            Entry(form, textvariable=motif, font=C.TEXT_SECONDARY, relief=SOLID,bd=1,width=22
                  ).grid(row=i,column=2,padx=4,pady=3)
            self._rows.append({"tf_id":tf["id"],"mnt":mnt,"motif":motif})

        _W.btn_primary(self, text="Enregistrer les remises",
                       command=self._save).pack(pady=12)

    def _save(self):
        for r in self._rows:
            try: m=float(r["mnt"].get().replace(",",".").replace(" ",""))
            except: m=0.0
            if m>0:
                self.db.upsert_remise(self.eleve["id"],r["tf_id"],m,
                                      r["motif"].get().strip(),ANNEE)
            else:
                try: self.db.delete_remise(self.eleve["id"],r["tf_id"],ANNEE)
                except: pass
        messagebox.showinfo("Enregistre","Remises mises a jour.",parent=self)
        if callable(self.on_success): self.on_success()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# Panneau detail eleve  (colonne droite)
# ══════════════════════════════════════════════════════════════════════════════

class _PanneauDetail(Frame):
    def __init__(self, parent, db:ComptaDB, **kw):
        kw.setdefault("bg", C.WHITE)
        super().__init__(parent, **kw)
        self.db=db; self.eleve=None; self._tranche_data=[]
        self._build_vide()

    def _bg(self): return C.WHITE

    def _build_vide(self):
        for w in self.winfo_children(): w.destroy()
        Label(self, text="Selectionnez un eleve\ndans la liste",
              font=C.FONT_SUBTITLE, fg=C.GRAY_BORDER, bg=self._bg(),
              justify=CENTER).pack(expand=True)

    def charger(self, eleve:dict):
        self.eleve = eleve; self._afficher()

    def _afficher(self):
        for w in self.winfo_children(): w.destroy()
        if not self.eleve: self._build_vide(); return
        e = self.eleve

        # bandeau
        hdr = Frame(self, bg=C.PRIMARY_BLUE)
        hdr.pack(fill=X)
        Label(hdr, text=f"{e['nom']} {e['prenom']}", font=C.FONT_SUBTITLE,
              fg=C.TEXT_WHITE, bg=C.PRIMARY_BLUE).pack(side=LEFT,padx=10,pady=6)
        Label(hdr, text=f"{e.get('classe_reelle','')}  |  {e.get('matricule','')}",
              font=C.TEXT_SMALL, fg=C.LIGHT_BLUE, bg=C.PRIMARY_BLUE).pack(side=RIGHT,padx=10)

        # boutons actions rapides
        act = Frame(self, bg=C.CARD_BG)
        act.pack(fill=X)
        _W.btn_success(act, text="Enregistrer paiement",
                       command=self._focus_form).pack(side=LEFT,padx=6,pady=4)
        _W.btn_primary(act, text="Remises",
                       command=lambda: FenetreRemise(self, self.db, e,
                                                     on_success=lambda: self.charger(self.db.get_eleve(e["id"])))).pack(side=LEFT,pady=4)

        # zone scrollable
        wrap = Frame(self, bg=C.WHITE)
        wrap.pack(fill=BOTH, expand=True)
        cv = Canvas(wrap, bg=C.WHITE, highlightthickness=0)
        sb = Scrollbar(wrap, orient=VERTICAL, command=cv.yview)
        cv.configure(yscrollcommand=sb.set); sb.pack(side=RIGHT,fill=Y)
        cv.pack(fill=BOTH, expand=True)
        self._inner = Frame(cv, bg=C.WHITE)
        wid = cv.create_window((0,0), window=self._inner, anchor=NW)
        self._inner.bind("<Configure>", lambda ev: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda ev: cv.itemconfig(wid, width=ev.width))

        self._build_detail(self._inner)
        self._build_historique(self._inner)
        self._build_form(self._inner)

    def _build_detail(self, parent):
        _W.section_bar(parent,"Detail des frais").pack(fill=X,pady=(8,4))
        rows = self.db.get_total_par_type(self.eleve["id"], ANNEE)
        for r in rows:
            mt   = float(r["montant_total"])
            paye = float(r["total_paye"])
            rem  = float(r.get("remise",0))
            reste= float(r.get("reste",0))
            pct  = (paye/mt) if mt>0 else 0.0
            color= C.SUCCESS_GREEN if reste<=0 else (C.DANGER_RED if pct<0.01 else C.WARNING_ORANGE)

            card = Frame(parent, bg=C.CARD_BG, relief=GROOVE, bd=1)
            card.pack(fill=X, padx=10, pady=3)
            top = Frame(card, bg=C.CARD_BG)
            top.pack(fill=X, padx=8, pady=(6,1))
            Label(top, text=r["nom"], font=C.TEXT_BOLD, fg=C.TEXT_DARK, bg=C.CARD_BG).pack(side=LEFT)
            lbl = "Solde" if reste<=0 else f"Reste : {reste:,.0f} FCFA"
            Label(top, text=lbl, font=C.TEXT_BOLD, fg=color, bg=C.CARD_BG).pack(side=RIGHT)
            if rem>0:
                Label(top, text=f"(-{rem:,.0f} remise)", font=C.TEXT_SMALL,
                      fg=C.SUCCESS_GREEN, bg=C.CARD_BG).pack(side=RIGHT,padx=6)
            # barre
            bar_host = Frame(card, bg=C.GRAY_BORDER, height=8)
            bar_host.pack(fill=X, padx=8, pady=2)
            def _draw(h=bar_host,p=pct,c=color):
                h.update_idletasks(); w2=h.winfo_width()
                cv2=Canvas(h,bg=C.GRAY_BORDER,height=8,highlightthickness=0)
                cv2.pack(fill=X)
                cv2.create_rectangle(0,0,int(w2*min(p,1.0)),8,fill=c,outline="")
            bar_host.after(30, _draw)
            bot = Frame(card, bg=C.CARD_BG)
            bot.pack(fill=X, padx=8, pady=(0,6))
            Label(bot, text=f"Total : {mt:,.0f}  Paye : {paye:,.0f}  {pct*100:.0f}%  (FCFA)",
                  font=C.TEXT_SMALL, fg=C.TEXT_GRAY, bg=C.CARD_BG).pack(side=LEFT)

    def _build_historique(self, parent):
        _W.section_bar(parent,"Historique paiements").pack(fill=X, pady=(10,4))
        hist = self.db.get_paiements_eleve(self.eleve["id"], ANNEE)
        if hist:
            cols=("date","type","tranche","montant","recu")
            th = ttk.Treeview(parent, columns=cols, show="headings", height=4)
            _style_tree(th)
            for c2,w2,l2 in [("date",95,"Date"),("type",105,"Type"),
                              ("tranche",85,"Tranche"),("montant",85,"Montant"),("recu",135,"N Recu")]:
                th.heading(c2,text=l2); th.column(c2,width=w2,anchor=CENTER)
            # clic droit -> annuler
            th.bind("<Button-3>", lambda ev,t=th: self._menu_annuler(ev,t))
            for h in hist:
                dt=h["date_paiement"]
                dt_s=dt.strftime("%d/%m/%Y") if isinstance(dt,datetime.datetime) else str(dt)
                th.insert("",END,iid=str(h["id"]),values=(
                    dt_s, h.get("type_nom",""), h.get("nom_tranche","") or "-",
                    f"{float(h['montant']):,.0f} FCFA", h.get("recu_num","")))
            th.pack(fill=X, padx=10, pady=(0,6))
        else:
            Label(parent, text="Aucun paiement enregistre.",
                  font=C.TEXT_SMALL, fg=C.TEXT_GRAY, bg=C.WHITE).pack(anchor=W,padx=14,pady=4)

    def _menu_annuler(self, event, tree):
        item = tree.identify_row(event.y)
        if not item: return
        m = Menu(self, tearoff=0)
        m.add_command(label="Annuler ce paiement",
                      command=lambda: self._annuler(int(item), tree))
        m.post(event.x_root, event.y_root)

    def _annuler(self, pmt_id:int, tree):
        motif = simpledialog.askstring("Motif d'annulation",
                                       "Motif (obligatoire) :", parent=self)
        if not motif: return
        self.db.annuler_paiement(pmt_id, motif)
        tree.delete(str(pmt_id))
        messagebox.showinfo("Annule","Paiement annule (conserve pour audit).",parent=self)
        self.charger(self.db.get_eleve(self.eleve["id"]))

    def _build_form(self, parent):
        bar = _W.section_bar(parent,"Enregistrer un paiement",color=C.SUCCESS_GREEN)
        bar.pack(fill=X, pady=(10,4))
        self._form_frame = Frame(parent, bg=C.WHITE)
        self._form_frame.pack(fill=X, padx=10, pady=4)
        self._form_frame.columnconfigure(1, weight=1)

        def lbl(text, row):
            Label(self._form_frame, text=text, font=C.TEXT_BOLD,
                  fg=C.TEXT_DARK, bg=C.WHITE).grid(row=row,column=0,sticky=W,padx=(0,8),pady=(6,0))

        lbl("Type de frais *", 0)
        types = self.db.get_types_frais()
        self._types_map = {t["nom"]:t for t in types}
        self._type_var = StringVar()
        type_cb = ttk.Combobox(self._form_frame, textvariable=self._type_var,
                               values=[t["nom"] for t in types], state="readonly", width=22)
        type_cb.grid(row=0,column=1,sticky=EW,pady=(6,0))
        type_cb.bind("<<ComboboxSelected>>", self._on_type)

        lbl("Tranche", 1)
        self._tranche_var = StringVar()
        self._tranche_cb = ttk.Combobox(self._form_frame, textvariable=self._tranche_var,
                                         state="readonly", width=22)
        self._tranche_cb.grid(row=1,column=1,sticky=EW,pady=(4,0))
        self._tranche_cb.bind("<<ComboboxSelected>>", self._on_tranche)

        lbl("Montant (FCFA) *", 2)
        self._montant_var = StringVar()
        self._montant_entry = Entry(self._form_frame, textvariable=self._montant_var,
                                    font=C.TEXT_SECONDARY, relief=SOLID,bd=1,width=22)
        self._montant_entry.grid(row=2,column=1,sticky=EW,pady=(4,0))
        self._montant_entry.bind("<Return>", lambda _: self._enregistrer())

        lbl("Notes", 3)
        self._notes_var = StringVar()
        Entry(self._form_frame, textvariable=self._notes_var,
              font=C.TEXT_SECONDARY, relief=SOLID,bd=1,width=22).grid(
            row=3,column=1,sticky=EW,pady=(4,0))

        bf = Frame(parent, bg=C.WHITE)
        bf.pack(anchor=W, padx=10, pady=8)
        _W.btn_success(bf, text="Enregistrer + Recu PDF  [Entree]",
                       command=self._enregistrer).pack(side=LEFT,padx=(0,8))

        if types:
            type_cb.current(0); self._on_type()

    def _focus_form(self):
        """Scroll vers le formulaire et mettre le focus sur montant."""
        try: self._montant_entry.focus_set()
        except: pass

    def _on_type(self, event=None):
        tf = self._types_map.get(self._type_var.get())
        if not tf: return
        tranches = self.db.get_tranches(tf["id"])
        self._tranche_data = tranches
        vals = [f"{t['nom_tranche']}  ({float(t['montant']):,.0f} FCFA)" for t in tranches]
        self._tranche_cb.configure(values=vals)
        if vals:
            self._tranche_cb.current(0)
            self._montant_var.set(str(int(float(tranches[0]["montant"]))))
        else:
            self._tranche_cb.set(""); self._montant_var.set("")

    def _on_tranche(self, event=None):
        sel = self._tranche_var.get()
        vals = list(self._tranche_cb.cget("values"))
        if sel in vals and self._tranche_data:
            idx = vals.index(sel)
            self._montant_var.set(str(int(float(self._tranche_data[idx]["montant"]))))

    def _enregistrer(self):
        if not self.eleve: return
        tf = self._types_map.get(self._type_var.get())
        if not tf:
            messagebox.showwarning("Champ requis","Selectionnez un type.",parent=self); return
        try:
            montant = float(self._montant_var.get().replace(" ","").replace(",","."))
        except ValueError:
            messagebox.showwarning("Montant invalide","Entrez un nombre.",parent=self); return

        tranche_id = None
        sel = self._tranche_var.get()
        vals = list(self._tranche_cb.cget("values"))
        if self._tranche_data and sel in vals:
            tranche_id = self._tranche_data[vals.index(sel)]["id"]

        try:
            result = self.db.enregistrer_paiement(
                self.eleve["id"], tf["id"], tranche_id, montant,
                self._notes_var.get().strip(), ANNEE)
        except Exception as ex:
            messagebox.showerror("Erreur BDD", str(ex), parent=self); return

        pmt   = self.db.get_paiement_by_recu(result["recu_num"]) or {
            "recu_num":result["recu_num"],"montant":montant,"notes":"",
            "date_paiement":datetime.datetime.now(),"annee_scolaire":ANNEE}
        det   = self.db.get_total_par_type(self.eleve["id"], ANNEE)
        reste = sum(float(r.get("reste",0)) for r in det)
        pdf_dir = os.path.join(os.path.dirname(__file__), "recus")
        try:
            path = generer_recu_pdf(pmt, self.eleve, det, reste, pdf_dir)
            messagebox.showinfo("Paiement enregistre",
                                f"Recu {result['recu_num']} genere!\n{path}", parent=self)
            open_pdf(path)
        except Exception as ex:
            messagebox.showwarning("PDF echec",str(ex),parent=self)

        self.charger(self.db.get_eleve(self.eleve["id"]))


# ══════════════════════════════════════════════════════════════════════════════
# Fenetre : Parametres types de frais
# ══════════════════════════════════════════════════════════════════════════════

class FenetreParamFrais(Toplevel):
    def __init__(self, parent, db:ComptaDB, on_close=None):
        super().__init__(parent)
        self.db=db; self.on_close=on_close
        self.title("Parametres -- Types de frais & Tranches")
        self.geometry("800x560"); self.resizable(True,True)
        self.grab_set(); self.protocol("WM_DELETE_WINDOW", self._fermer)
        self._tf_id_sel=None; self._tranche_rows=[]
        self.configure(bg=C.CARD_BG); self._build(); self._load_liste()

    def _build(self):
        left = Frame(self, bg=C.LIGHT_BLUE, width=220)
        left.pack(side=LEFT, fill=Y); left.pack_propagate(False)
        Label(left, text="Types de frais", font=C.FONT_SUBTITLE,
              fg=C.PRIMARY_BLUE, bg=C.LIGHT_BLUE).pack(pady=12)
        self._liste_frame = Frame(left, bg=C.LIGHT_BLUE)
        self._liste_frame.pack(fill=BOTH, expand=True, padx=6)
        _W.btn_primary(left, text="+ Nouveau type",
                       command=self._nouveau).pack(fill=X,padx=10,pady=10)
        right_wrap = Frame(self, bg=C.WHITE)
        right_wrap.pack(side=LEFT, fill=BOTH, expand=True)
        cv = Canvas(right_wrap, bg=C.WHITE, highlightthickness=0)
        sb = Scrollbar(right_wrap, orient=VERTICAL, command=cv.yview)
        cv.configure(yscrollcommand=sb.set); sb.pack(side=RIGHT,fill=Y); cv.pack(fill=BOTH,expand=True)
        self._right = Frame(cv, bg=C.WHITE)
        wid = cv.create_window((0,0), window=self._right, anchor=NW)
        self._right.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(wid, width=e.width))

    def _load_liste(self):
        for w in self._liste_frame.winfo_children(): w.destroy()
        for tf in self.db.get_types_frais():
            Button(self._liste_frame,
                   text=f"  {tf['nom']}\n  {float(tf['montant_total']):,.0f} FCFA",
                   font=C.TEXT_SECONDARY, fg=C.TEXT_DARK, bg=C.LIGHT_BLUE,
                   relief=FLAT, anchor=W, justify=LEFT, cursor="hand2",
                   command=lambda t=tf: self._select(t)).pack(fill=X,pady=2)

    def _select(self, tf):
        self._tf_id_sel=tf["id"]; self._afficher_form(tf)

    def _afficher_form(self, tf):
        for w in self._right.winfo_children(): w.destroy()
        self._tranche_rows=[]
        Label(self._right, text=f"Modifier : {tf['nom']}", font=C.FONT_SUBTITLE,
              fg=C.PRIMARY_BLUE, bg=C.WHITE).pack(anchor=W,padx=16,pady=(12,4))
        self._nom_var=StringVar(value=tf["nom"])
        self._mt_var=StringVar(value=str(int(float(tf["montant_total"]))))
        self._render_fields(tf.get("description") or "")
        for t in self.db.get_tranches(tf["id"]):
            self._add_row(t.get("nom_tranche",""), t.get("montant",""))
        bf=Frame(self._right,bg=C.WHITE); bf.pack(anchor=W,padx=16,pady=10)
        _W.btn_primary(bf,text="Enregistrer",command=self._save).pack(side=LEFT,padx=(0,8))
        _W.btn_danger(bf,text="Supprimer",command=lambda:self._suppr(tf["id"])).pack(side=LEFT)

    def _render_fields(self, desc_init=""):
        r=self._right
        for txt,var in [("Nom *",self._nom_var),("Montant total (FCFA) *",self._mt_var)]:
            Label(r,text=txt,font=C.TEXT_BOLD,fg=C.TEXT_DARK,bg=C.WHITE).pack(anchor=W,padx=16)
            Entry(r,textvariable=var,font=C.TEXT_SECONDARY,relief=SOLID,bd=1,width=40).pack(anchor=W,padx=16,pady=(2,8))
        Label(r,text="Description",font=C.TEXT_BOLD,fg=C.TEXT_DARK,bg=C.WHITE).pack(anchor=W,padx=16)
        self._desc=Text(r,height=3,font=C.TEXT_SECONDARY,relief=SOLID,bd=1,width=40)
        self._desc.insert("1.0",desc_init); self._desc.pack(anchor=W,padx=16,pady=(2,10))
        Label(r,text="Tranches",font=C.TEXT_BOLD,fg=C.TEXT_DARK,bg=C.WHITE).pack(anchor=W,padx=16)
        self._tranches_host=Frame(r,bg=C.WHITE); self._tranches_host.pack(anchor=W,padx=16)
        Button(r,text="+ Ajouter tranche",font=C.TEXT_SECONDARY,fg=C.PRIMARY_BLUE,
               bg=C.LIGHT_BLUE,relief=FLAT,cursor="hand2",
               command=self._add_row).pack(anchor=W,padx=16,pady=4)

    def _add_row(self, nom="", montant=""):
        row=Frame(self._tranches_host,bg=C.WHITE); row.pack(fill=X,pady=2)
        n=StringVar(value=nom); m=StringVar(value=str(montant))
        Entry(row,textvariable=n,font=C.TEXT_SECONDARY,relief=SOLID,bd=1,width=20).pack(side=LEFT,padx=(0,4))
        Entry(row,textvariable=m,font=C.TEXT_SECONDARY,relief=SOLID,bd=1,width=14).pack(side=LEFT,padx=(0,4))
        _W.btn_danger(row,text="X",width=2,padx=4,command=lambda r=row:self._del_row(r)).pack(side=LEFT)
        self._tranche_rows.append({"row":row,"nom":n,"montant":m})

    def _del_row(self, row):
        self._tranche_rows=[r for r in self._tranche_rows if r["row"] is not row]; row.destroy()

    def _save(self):
        if not self._tf_id_sel: return
        nom=self._nom_var.get().strip()
        if not nom: messagebox.showwarning("Requis","Nom obligatoire.",parent=self); return
        try: mt=float(self._mt_var.get().replace(",",".").replace(" ",""))
        except: messagebox.showwarning("Erreur","Montant invalide.",parent=self); return
        desc=self._desc.get("1.0",END).strip() if self._desc else ""
        tranches=[{"nom":r["nom"].get().strip(),"montant":float(r["montant"].get().replace(",",".").replace(" ",""))}
                  for r in self._tranche_rows if r["nom"].get().strip()]
        self.db.update_type_frais(self._tf_id_sel,nom,mt,desc)
        self.db.replace_tranches(self._tf_id_sel,tranches)
        messagebox.showinfo("Enregistre",f"'{nom}' mis a jour.",parent=self)
        self._load_liste()

    def _nouveau(self):
        for w in self._right.winfo_children(): w.destroy()
        self._tranche_rows=[]; self._tf_id_sel=None
        self._nom_var=StringVar(); self._mt_var=StringVar()
        Label(self._right,text="Nouveau type de frais",font=C.FONT_SUBTITLE,
              fg=C.PRIMARY_BLUE,bg=C.WHITE).pack(anchor=W,padx=16,pady=(12,4))
        self._render_fields(); self._add_row()
        _W.btn_primary(self._right,text="Creer",command=self._creer).pack(anchor=W,padx=16,pady=10)

    def _creer(self):
        nom=self._nom_var.get().strip()
        if not nom: messagebox.showwarning("Requis","Nom obligatoire.",parent=self); return
        try: mt=float(self._mt_var.get().replace(",",".").replace(" ",""))
        except: messagebox.showwarning("Erreur","Montant invalide.",parent=self); return
        desc=self._desc.get("1.0",END).strip() if self._desc else ""
        tranches=[{"nom":r["nom"].get().strip(),"montant":float(r["montant"].get().replace(",",".").replace(" ",""))}
                  for r in self._tranche_rows if r["nom"].get().strip()]
        tf_id=self.db.create_type_frais(nom,mt,desc)
        self.db.replace_tranches(tf_id,tranches)
        messagebox.showinfo("Cree",f"Type '{nom}' cree.",parent=self); self._load_liste()

    def _suppr(self, tf_id):
        if messagebox.askyesno("Confirmer","Desactiver ce type ?",parent=self):
            self.db.delete_type_frais(tf_id)
            for w in self._right.winfo_children(): w.destroy()
            self._load_liste()

    def _fermer(self):
        if callable(self.on_close): self.on_close()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# VUE ELEVES  --  vue principale avec split gauche/droite
# ══════════════════════════════════════════════════════════════════════════════

class _VueEleves(Frame):
    def __init__(self, parent, db:ComptaDB):
        super().__init__(parent, bg=C.CARD_BG)
        self.db=db
        # Cache des ids nouveaux inscrits (ACCEPTED sans paiement)
        self._ids_nouveaux: set = set()
        self._build()

    def _build(self):
        # barre filtres
        bar = Frame(self, bg=C.LIGHT_BLUE, relief=GROOVE, bd=1)
        bar.pack(fill=X)
        Label(bar,text="Classe :",font=C.TEXT_BOLD,fg=C.TEXT_DARK,bg=C.LIGHT_BLUE
              ).pack(side=LEFT,padx=(12,4),pady=6)
        self._classe_var=StringVar()
        self._classe_cb=ttk.Combobox(bar,textvariable=self._classe_var,state="readonly",width=14)
        self._classe_cb.pack(side=LEFT,padx=4)
        self._classe_cb.bind("<<ComboboxSelected>>",lambda _:self._refresh_list())

        # Filtres rapides -- boutons
        self._filtre_var=StringVar(value="Tous")
        for lbl,val,color in [("Tous","Tous",C.PRIMARY_BLUE),
                               ("Impayes","Impaye",C.DANGER_RED),
                               ("A jour","A jour",C.SUCCESS_GREEN)]:
            b=Button(bar,text=lbl,font=C.TEXT_SMALL,fg=C.TEXT_WHITE,bg=color,
                     relief=FLAT,cursor="hand2",padx=8,pady=3,
                     command=lambda v=val:self._set_filtre(v))
            b.pack(side=LEFT,padx=3)

        # Filtre "Nouveaux uniquement" — isole les élèves sans aucun paiement
        Button(bar, text="★ Nouveaux uniquement",
               font=C.TEXT_SMALL, fg=C.TEXT_WHITE, bg="#7B1FA2",
               relief=FLAT, cursor="hand2", padx=8, pady=3,
               command=lambda: self._set_filtre("Nouveau")
               ).pack(side=LEFT, padx=3)

        _W.btn_primary(bar,text="F5 Actualiser",command=self.refresh).pack(side=LEFT,padx=8)
        self._count_lbl=Label(bar,text="",font=C.TEXT_SMALL,fg=C.TEXT_GRAY,bg=C.LIGHT_BLUE)
        self._count_lbl.pack(side=LEFT,padx=6)
        _W.btn_primary(bar,text="PDF insolvables",command=self._export_pdf).pack(side=RIGHT,padx=10)

        # split
        split=Frame(self,bg=C.CARD_BG)
        split.pack(fill=BOTH,expand=True)

        # colonne gauche
        left=Frame(split,bg=C.WHITE,width=C.LEFT_W)
        left.pack(side=LEFT,fill=Y); left.pack_propagate(False)

        # ── Badge "Nouveaux dossiers à traiter" ──────────────────────────────
        self._badge_frame=Frame(left, bg="#F3E5F5", relief=FLAT, bd=0)
        self._badge_frame.pack(fill=X, padx=6, pady=(6,0))
        self._badge_lbl=Label(
            self._badge_frame,
            text="",
            font=C.TEXT_BOLD,
            fg="#7B1FA2", bg="#F3E5F5",
            cursor="hand2",
            anchor=W, padx=8, pady=4
        )
        self._badge_lbl.pack(fill=X)
        # Cliquer sur le badge active directement le filtre "Nouveau"
        self._badge_lbl.bind("<Button-1>", lambda _: self._set_filtre("Nouveau"))
        self._badge_frame.pack_forget()   # masqué tant qu'il n'y a rien

        # recherche rapide dans la liste
        sb2=Frame(left,bg=C.WHITE)
        sb2.pack(fill=X,padx=8,pady=4)
        self._search_var=StringVar()
        e2=Entry(sb2,textvariable=self._search_var,font=C.TEXT_SECONDARY,
                 relief=SOLID,bd=1,width=22)
        e2.pack(side=LEFT,fill=X,expand=True)
        e2.bind("<KeyRelease>",lambda _:self._refresh_list())
        Label(sb2,text="Filtrer",font=C.TEXT_SMALL,fg=C.TEXT_GRAY,bg=C.WHITE).pack(side=LEFT,padx=4)

        cols=("nom_prenom","statut")
        self._tree=ttk.Treeview(left,columns=cols,show="headings",selectmode="browse")
        _style_tree(self._tree)
        self._tree.heading("nom_prenom",text="Nom & Prenom")
        self._tree.heading("statut",text="Statut")
        self._tree.column("nom_prenom",width=210,anchor=W)
        self._tree.column("statut",width=72,anchor=CENTER)
        self._tree.tag_configure("ok", background=C.LIGHT_GREEN, foreground=C.SUCCESS_GREEN)
        self._tree.tag_configure("imp",background=C.LIGHT_RED,   foreground=C.DANGER_RED)
        self._tree.tag_configure("par",background=C.LIGHT_ORANGE,foreground=C.WARNING_ORANGE)
        self._tree.tag_configure("nouveau", background="#EDE7F6", foreground="#7B1FA2")
        sb3=ttk.Scrollbar(left,orient=VERTICAL,command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb3.set)
        self._tree.pack(side=LEFT,fill=BOTH,expand=True,padx=(6,0),pady=(0,6))
        sb3.pack(side=LEFT,fill=Y,pady=(0,6))
        self._tree.bind("<<TreeviewSelect>>",self._on_select)

        # separateur
        Frame(split,bg=C.SEP_COLOR,width=2).pack(side=LEFT,fill=Y)

        # colonne droite
        self._panneau=_PanneauDetail(split,db=self.db)
        self._panneau.pack(side=LEFT,fill=BOTH,expand=True)

    def _set_filtre(self, val):
        self._filtre_var.set(val); self._refresh_list()

    def refresh(self):
        # ── Charge les nouveaux inscrits sans paiement ────────────────────────
        nouveaux = self.db.get_nouveaux_inscrits_sans_paiement(ANNEE)
        self._ids_nouveaux = {e["id"] for e in nouveaux}
        nb_nouveaux = len(self._ids_nouveaux)
        if nb_nouveaux > 0:
            self._badge_lbl.configure(
                text=f"🔔  Nouveaux dossiers à traiter : {nb_nouveaux}  (cliquer pour filtrer)")
            self._badge_frame.pack(fill=X, padx=6, pady=(6,0))
        else:
            self._badge_frame.pack_forget()

        classes=self.db.get_classes()
        noms=[c["nom_classe"] for c in classes]
        self._classe_cb.configure(values=noms)
        if noms and self._classe_var.get() not in noms:
            self._classe_var.set(noms[0])
        self._refresh_list()

    def _refresh_list(self):
        classe=self._classe_var.get()
        if not classe: return
        filtre=self._filtre_var.get()
        search=self._search_var.get().strip().lower()
        for r in self._tree.get_children(): self._tree.delete(r)
        n_tot=n_imp=n_par=0
        for e in self.db.get_eleves(classe):
            est_nouveau = e["id"] in self._ids_nouveaux

            # Filtre "Nouveaux uniquement" — élèves ACCEPTED sans aucun versement
            if filtre == "Nouveau" and not est_nouveau:
                continue

            rows=self.db.get_total_par_type(e["id"],ANNEE)
            paye_total=sum(float(r["total_paye"]) for r in rows)
            mt_total=sum(float(r["montant_total"]) for r in rows)
            reste_total=sum(float(r.get("reste",0)) for r in rows)
            if reste_total<=0:   statut="A jour"; tag="ok"
            elif paye_total==0:  statut="Non paye"; tag="imp"
            else:                statut="Partiel"; tag="par"

            # Les nouveaux inscrits sans paiement reçoivent leur propre tag visuel
            if est_nouveau:
                statut = "Nouveau"
                tag = "nouveau"

            if filtre=="Impaye" and statut not in ("Non paye","Partiel","Nouveau"): continue
            if filtre=="A jour" and statut!="A jour": continue
            nom_full=f"{e['nom']} {e['prenom']}".lower()
            if search and search not in nom_full and search not in e.get("matricule","").lower():
                continue
            n_tot+=1
            if statut!="A jour":
                n_imp+=1 if statut in ("Non paye","Nouveau") else 0
                n_par+=1 if statut=="Partiel" else 0
            self._tree.insert("",END,iid=e["id"],values=(f"{e['nom']} {e['prenom']}",statut),tags=(tag,))
        suffix = f" | {len(self._ids_nouveaux)} nouveau(x)" if self._ids_nouveaux else ""
        self._count_lbl.configure(text=f"{n_tot} eleve(s) | {n_imp+n_par} impaye(s){suffix}")

    def _on_select(self, _=None):
        sel=self._tree.selection()
        if not sel: return
        eleve=self.db.get_eleve(sel[0])
        if eleve: self._panneau.charger(eleve)

    def _export_pdf(self):
        classe=self._classe_var.get()
        if not classe: return
        ins=self.db.get_insolvables(classe,ANNEE)
        if not ins:
            messagebox.showinfo("OK",f"Tous les eleves de {classe} sont a jour!"); return
        d=filedialog.askdirectory(title="Dossier de sauvegarde")
        if not d: return
        path=generer_insolvables_pdf(classe,ins,ANNEE,d)
        messagebox.showinfo("PDF genere",f"Fichier :\n{path}"); open_pdf(path)


# ══════════════════════════════════════════════════════════════════════════════
# VUE DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

class _VueDashboard(Frame):
    def __init__(self, parent, db:ComptaDB):
        super().__init__(parent, bg=C.CARD_BG)
        self.db=db; self._kpi_vals=[]; self._build()

    def _build(self):
        kpi_row=Frame(self,bg=C.CARD_BG)
        kpi_row.pack(fill=X,padx=C.PAD_X,pady=C.PAD_Y)
        kpi_defs=[("Recettes totales","FCFA",C.PRIMARY_BLUE),
                  ("Recettes du jour","Auj.",C.SUCCESS_GREEN),
                  ("Depenses","Dep.",C.DANGER_RED),
                  ("Solde net","Sol.",C.ACCENT_BLUE),
                  ("Eleves inscrits","Elv.","#7B1FA2"),
                  ("Impayes","!","#E67E22")]
        for title,icon,color in kpi_defs:
            f,val=_W.kpi_card(kpi_row,title,icon,color)
            f.pack(side=LEFT,fill=BOTH,expand=True,padx=3)
            self._kpi_vals.append(val)

        split=Frame(self,bg=C.CARD_BG)
        split.pack(fill=BOTH,expand=True,padx=C.PAD_X,pady=(4,C.PAD_Y))

        # paiements recents
        left=Frame(split,bg=C.WHITE,relief=GROOVE,bd=1)
        left.pack(side=LEFT,fill=BOTH,expand=True,padx=(0,6))
        _W.section_bar(left,"Paiements recents").pack(fill=X)
        cols=("date","eleve","type","montant")
        self._tree_pmt=ttk.Treeview(left,columns=cols,show="headings",height=16)
        _style_tree(self._tree_pmt)
        for c,w,lbl in [("date",100,"Date"),("eleve",170,"Eleve"),("type",130,"Type"),("montant",95,"Montant")]:
            self._tree_pmt.heading(c,text=lbl); self._tree_pmt.column(c,width=w,anchor=CENTER)
        sb=ttk.Scrollbar(left,orient=VERTICAL,command=self._tree_pmt.yview)
        self._tree_pmt.configure(yscrollcommand=sb.set)
        self._tree_pmt.pack(side=LEFT,fill=BOTH,expand=True,padx=(6,0),pady=6)
        sb.pack(side=LEFT,fill=Y,pady=6)

        # recettes par type + cloture
        right=Frame(split,bg=C.WHITE,relief=GROOVE,bd=1,width=240)
        right.pack(side=LEFT,fill=Y); right.pack_propagate(False)
        _W.section_bar(right,"Recettes / Type").pack(fill=X)
        self._types_frame=Frame(right,bg=C.WHITE)
        self._types_frame.pack(fill=X,padx=10,pady=8)
        # cloture
        sep=Frame(right,bg=C.SEP_COLOR,height=1); sep.pack(fill=X,padx=10)
        _W.section_bar(right,"Cloture de caisse",color="#5D4037").pack(fill=X,pady=(8,4))
        Label(right,text=f"Date du jour :\n{datetime.date.today().strftime('%d/%m/%Y')}",
              font=C.TEXT_SECONDARY,fg=C.TEXT_DARK,bg=C.WHITE).pack(pady=4)
        _W.btn_danger(right,text="Cloturer la caisse",command=self._cloturer).pack(fill=X,padx=10,pady=4)
        self._cloture_info=Label(right,text="",font=C.TEXT_SMALL,fg=C.TEXT_GRAY,bg=C.WHITE)
        self._cloture_info.pack(padx=10)

    def refresh(self):
        stats=self.db.get_stats(ANNEE)
        vals=[f"{float(stats['recettes']):,.0f}", f"{float(stats['recettes_jour']):,.0f}",
              f"{float(stats['depenses']):,.0f}", f"{float(stats['solde']):,.0f}",
              str(stats["nb_eleves"]), str(stats["nb_impayes"])]
        for lbl,val in zip(self._kpi_vals,vals): lbl.configure(text=val)

        for r in self._tree_pmt.get_children(): self._tree_pmt.delete(r)
        for p in self.db.get_paiements_recents(20,ANNEE):
            dt=p["date_paiement"]
            dt_s=dt.strftime("%d/%m/%Y") if isinstance(dt,datetime.datetime) else str(dt)
            self._tree_pmt.insert("",END,values=(dt_s,
                f"{p['eleve_nom']} {p['eleve_prenom']}",p["type_nom"],
                f"{float(p['montant']):,.0f} FCFA"))

        for w in self._types_frame.winfo_children(): w.destroy()
        for r in self.db.get_recettes_par_type(ANNEE):
            row=Frame(self._types_frame,bg=C.WHITE); row.pack(fill=X,pady=2)
            Label(row,text=r["nom"],font=C.TEXT_SECONDARY,fg=C.TEXT_DARK,bg=C.WHITE).pack(side=LEFT)
            Label(row,text=f"{float(r['total']):,.0f} FCFA",font=C.TEXT_BOLD,
                  fg=C.PRIMARY_BLUE,bg=C.WHITE).pack(side=RIGHT)
            Frame(self._types_frame,bg=C.SEP_COLOR,height=1).pack(fill=X)

        today=datetime.date.today().isoformat()
        if self.db.jour_est_cloture(today):
            self._cloture_info.configure(text="Caisse cloturee aujourd'hui",fg=C.SUCCESS_GREEN)
        else:
            self._cloture_info.configure(text="Caisse non cloturee",fg=C.WARNING_ORANGE)

    def _cloturer(self):
        today=datetime.date.today().isoformat()
        if self.db.jour_est_cloture(today):
            messagebox.showinfo("Deja cloturee",f"La caisse du {today} est deja cloturee."); return
        if not messagebox.askyesno("Confirmer",
            f"Cloturer definitivement la caisse du {today} ?\nCette action est irreversible."):
            return
        notes=simpledialog.askstring("Notes","Notes de cloture (optionnel) :") or ""
        try:
            res=self.db.cloturer_caisse(today,notes)
            messagebox.showinfo("Cloture effectuee",
                f"Caisse du {today} cloturee.\n"
                f"Recettes : {float(res['recettes']):,.0f} FCFA\n"
                f"Depenses : {float(res['depenses']):,.0f} FCFA\n"
                f"Solde    : {float(res['solde']):,.0f} FCFA")
            self.refresh()
        except Exception as ex:
            messagebox.showerror("Erreur",str(ex))


# ══════════════════════════════════════════════════════════════════════════════
# VUE PAIEMENTS
# ══════════════════════════════════════════════════════════════════════════════

class _VuePaiements(Frame):
    def __init__(self, parent, db:ComptaDB):
        super().__init__(parent, bg=C.CARD_BG)
        self.db=db; self._build()

    def _build(self):
        bar=_W.section_bar(self,"Historique des paiements"); bar.pack(fill=X)
        _W.btn_primary(bar,text="F5 Actualiser",command=self.refresh).pack(side=RIGHT,padx=10,pady=4)

        wrap=Frame(self,bg=C.CARD_BG)
        wrap.pack(fill=BOTH,expand=True,padx=C.PAD_X,pady=C.PAD_Y)
        cols=("recu","date","eleve","classe","type","montant","statut")
        self._tree=ttk.Treeview(wrap,columns=cols,show="headings")
        _style_tree(self._tree)
        for c,w,lbl in [("recu",150,"N Recu"),("date",120,"Date"),("eleve",185,"Eleve"),
                         ("classe",80,"Classe"),("type",140,"Type"),("montant",100,"Montant"),
                         ("statut",70,"Statut")]:
            self._tree.heading(c,text=lbl); self._tree.column(c,width=w,anchor=CENTER)
        self._tree.tag_configure("annule", foreground=C.DANGER_RED)
        sb=ttk.Scrollbar(wrap,orient=VERTICAL,command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=LEFT,fill=BOTH,expand=True); sb.pack(side=LEFT,fill=Y)

    def refresh(self):
        for r in self._tree.get_children(): self._tree.delete(r)
        for p in self.db.get_paiements_recents(300,ANNEE):
            dt=p["date_paiement"]
            dt_s=dt.strftime("%d/%m/%Y %H:%M") if isinstance(dt,datetime.datetime) else str(dt)
            statut="ANNULE" if p.get("annule") else "OK"
            tag=("annule",) if p.get("annule") else ()
            self._tree.insert("",END,tags=tag,values=(
                p["recu_num"],dt_s,f"{p['eleve_nom']} {p['eleve_prenom']}",
                p.get("classe_reelle",""),p["type_nom"],
                f"{float(p['montant']):,.0f} FCFA",statut))


# ══════════════════════════════════════════════════════════════════════════════
# VUE DEPENSES
# ══════════════════════════════════════════════════════════════════════════════

class _VueDepenses(Frame):
    def __init__(self, parent, db:ComptaDB):
        super().__init__(parent, bg=C.CARD_BG)
        self.db=db; self._build()

    def _build(self):
        split=Frame(self,bg=C.CARD_BG); split.pack(fill=BOTH,expand=True)
        # gauche
        left=Frame(split,bg=C.WHITE,relief=GROOVE,bd=1)
        left.pack(side=LEFT,fill=BOTH,expand=True,padx=(C.PAD_X,6),pady=C.PAD_Y)
        hdr=_W.section_bar(left,"Depenses enregistrees"); hdr.pack(fill=X)
        _W.btn_primary(hdr,text="F5 Actualiser",command=self.refresh).pack(side=RIGHT,padx=8,pady=4)
        cols=("date","motif","categorie","montant")
        self._tree=ttk.Treeview(left,columns=cols,show="headings")
        _style_tree(self._tree)
        for c,w,lbl in [("date",105,"Date"),("motif",230,"Motif"),
                         ("categorie",130,"Categorie"),("montant",110,"Montant")]:
            self._tree.heading(c,text=lbl); self._tree.column(c,width=w,anchor=CENTER)
        sb=ttk.Scrollbar(left,orient=VERTICAL,command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=LEFT,fill=BOTH,expand=True,padx=(6,0),pady=6)
        sb.pack(side=LEFT,fill=Y,pady=6)

        # separateur
        Frame(split,bg=C.SEP_COLOR,width=2).pack(side=LEFT,fill=Y,pady=C.PAD_Y)

        # droite formulaire
        right=Frame(split,bg=C.WHITE,width=290)
        right.pack(side=LEFT,fill=Y,padx=(0,C.PAD_X),pady=C.PAD_Y); right.pack_propagate(False)
        _W.section_bar(right,"Nouvelle depense").pack(fill=X)
        form=Frame(right,bg=C.WHITE); form.pack(fill=X,padx=12,pady=8); form.columnconfigure(0,weight=1)
        fields=[("Motif *","motif",""),("Montant (FCFA) *","montant",""),
                ("Categorie","categorie","General"),("Date (YYYY-MM-DD)","date",str(datetime.date.today()))]
        self._dep_vars={}
        for i,(lbl,key,default) in enumerate(fields):
            Label(form,text=lbl,font=C.TEXT_BOLD,fg=C.TEXT_DARK,bg=C.WHITE
                  ).grid(row=i*2,column=0,sticky=W,pady=(6,0))
            var=StringVar(value=default)
            Entry(form,textvariable=var,font=C.TEXT_SECONDARY,relief=SOLID,bd=1
                  ).grid(row=i*2+1,column=0,sticky=EW)
            self._dep_vars[key]=var
        Label(form,text="Notes",font=C.TEXT_BOLD,fg=C.TEXT_DARK,bg=C.WHITE
              ).grid(row=len(fields)*2,column=0,sticky=W,pady=(6,0))
        self._dep_notes=Text(form,height=4,font=C.TEXT_SECONDARY,relief=SOLID,bd=1)
        self._dep_notes.grid(row=len(fields)*2+1,column=0,sticky=EW)
        _W.btn_primary(right,text="Enregistrer la depense  [Entree]",
                       command=self._save).pack(pady=10,padx=12,fill=X)
        self._dep_vars["montant"] and right.bind_all("<Return>",lambda e:None)

    def refresh(self):
        for r in self._tree.get_children(): self._tree.delete(r)
        for d in self.db.get_depenses():
            self._tree.insert("",END,values=(str(d["date_depense"]),d["motif"],
                d.get("categorie",""),f"{float(d['montant']):,.0f} FCFA"))

    def _save(self):
        motif=self._dep_vars["motif"].get().strip()
        if not motif: messagebox.showwarning("Requis","Motif obligatoire."); return
        try: montant=float(self._dep_vars["montant"].get().replace(",",".").replace(" ",""))
        except: messagebox.showwarning("Erreur","Montant invalide."); return
        cat=self._dep_vars["categorie"].get().strip() or "General"
        date_=self._dep_vars["date"].get().strip()
        try: datetime.date.fromisoformat(date_)
        except: messagebox.showwarning("Erreur","Date invalide (YYYY-MM-DD)."); return
        notes=self._dep_notes.get("1.0",END).strip()
        self.db.create_depense(motif,montant,cat,date_,notes)
        for k,v in self._dep_vars.items(): v.set("" if k!="date" else str(datetime.date.today()))
        self._dep_notes.delete("1.0",END)
        messagebox.showinfo("Enregistre","Depense enregistree.")
        self.refresh()


# ══════════════════════════════════════════════════════════════════════════════
# APPLICATION PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════

class Comptable(Tk):

    def __init__(self, db_connection=None):
        super().__init__()
        self.title("Academix-Comptable")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        self.configure(bg=C.CARD_BG)
        self.db=ComptaDB(db_connection) if db_connection else None
        self.views={}; self.current_view=""; self._poll_id=None
        self._last_ts={}; self._btn_map={}
        self._build_ui()
        if self.db:
            self._create_views(); self.show_view("dashboard"); self._start_polling()
        self.protocol("WM_DELETE_WINDOW",self._on_close)
        self._bind_shortcuts()

    def _build_ui(self):
        # HEADER
        self._header=Frame(self,bg=C.HEADER_BG,height=C.HEADER_H)
        self._header.pack(side=TOP,fill=X,anchor=N)
        self._header.pack_propagate(False)
        Label(self._header,text="Comptabilite Academix",font=C.FONT_TITLE,
              fg=C.TEXT_WHITE,bg=C.HEADER_BG).pack(pady=(8,2))
        # theme toggle + sync
        top_right=Frame(self._header,bg=C.HEADER_BG)
        top_right.place(relx=1.0,rely=0,anchor=NE,x=-10,y=6)
        self._theme_btn=Button(top_right,text="Mode sombre",font=C.TEXT_SMALL,
                               fg=C.TEXT_WHITE,bg=C.ACCENT_BLUE,relief=FLAT,
                               cursor="hand2",padx=8,pady=2,command=self._toggle_theme)
        self._theme_btn.pack(side=LEFT,padx=4)
        self._sync_lbl=Label(top_right,text="Synchronise",font=C.TEXT_SMALL,
                              fg="#90CAF9",bg=C.HEADER_BG)
        self._sync_lbl.pack(side=LEFT,padx=4)

        btn_row=Frame(self._header,bg=C.HEADER_BG); btn_row.pack()
        BTNS=[("Tableau de bord","dashboard"),("Eleves","eleves"),
              ("Paiements","paiements"),("Depenses","depenses"),("Parametres","params")]
        for text,key in BTNS:
            b=Button(btn_row,text=text,font=C.TEXT_SECONDARY,fg=C.TEXT_WHITE,
                     bg=C.HEADER_BG,activebackground=C.ACCENT_BLUE,
                     activeforeground=C.TEXT_WHITE,relief=FLAT,cursor="hand2",
                     width=C.BTN_WIDTH,command=lambda k=key:self._nav(k))
            b.pack(side=LEFT,anchor=S); self._btn_map[key]=b

        self.main_frame=Frame(self,bg=C.CARD_BG)
        self.main_frame.pack(fill=BOTH,expand=True)

        self._footer=Frame(self,bg=C.FOOTER_BG,height=C.FOOTER_H,relief=GROOVE,bd=2)
        self._footer.pack(fill=X,side=BOTTOM,anchor=S)
        self._footer_lbl=Label(self._footer,
              text="Developpe par Lankoande Enock   (c) 2024 Academix. Tous droits reserves.",
              font=C.TEXT_SMALL,fg=C.FOOTER_FG,bg=C.FOOTER_BG)
        self._footer_lbl.pack(pady=6,expand=True)

    def _create_views(self):
        self.views["dashboard"]=_VueDashboard(self.main_frame,self.db)
        self.views["eleves"]   =_VueEleves(self.main_frame,self.db)
        self.views["paiements"]=_VuePaiements(self.main_frame,self.db)
        self.views["depenses"] =_VueDepenses(self.main_frame,self.db)
        for v in self.views.values(): v.pack_forget()

    # ── Raccourcis clavier ────────────────────────────────────────────────────

    def _bind_shortcuts(self):
        self.bind_all("<F1>", lambda e: self._open_recherche())
        self.bind_all("<F5>", lambda e: self._refresh_current())
        # Entree global -- valide le paiement si focus dans entry montant
        # (gere dans le panneau detail directement)

    def _open_recherche(self):
        if self.db: FenetreRecherche(self, self.db)

    def _refresh_current(self):
        if self.current_view in self.views:
            v=self.views[self.current_view]
            if hasattr(v,"refresh"): v.refresh()

    # ── Navigation ────────────────────────────────────────────────────────────

    def _nav(self, key:str):
        if key=="params":
            if self.db:
                FenetreParamFrais(self,self.db,on_close=lambda:self.show_view(self.current_view))
            return
        self.show_view(key)

    def show_view(self, view_name:str):
        if not self.db or view_name not in self.views: return
        if view_name==self.current_view:
            if hasattr(self.views[view_name],"refresh"): self.views[view_name].refresh()
            return
        if self.current_view and self.current_view in self.views:
            old=self.views[self.current_view]
            if hasattr(old,"_stop_auto_refresh"): old._stop_auto_refresh()
            old.pack_forget()
        for k,b in self._btn_map.items():
            b.configure(bg=C.ACCENT_BLUE if k==view_name else C.HEADER_BG,
                        font=C.TEXT_BOLD if k==view_name else C.TEXT_SECONDARY)
        self.views[view_name].pack(fill=BOTH,expand=True)
        self.current_view=view_name
        if hasattr(self.views[view_name],"refresh"): self.views[view_name].refresh()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        theme=C.toggle_theme()
        apply_theme_all()
        self._theme_btn.configure(text="Mode clair" if C.is_dark() else "Mode sombre")
        # Re-appliquer les couleurs aux elements non-enregistres
        self._header.configure(bg=C.HEADER_BG)
        for w in self._header.winfo_children():
            try: w.configure(bg=C.HEADER_BG)
            except: pass
        self.main_frame.configure(bg=C.MAIN_BG)
        self._footer.configure(bg=C.FOOTER_BG)
        self._footer_lbl.configure(bg=C.FOOTER_BG,fg=C.FOOTER_FG)
        self.configure(bg=C.MAIN_BG)
        # Forcer le re-rendu des vues
        if self.current_view in self.views:
            v=self.views[self.current_view]
            if hasattr(v,"refresh"): v.refresh()

    # ── Synchronisation ───────────────────────────────────────────────────────

    def _start_polling(self):
        self._poll_id=self.after(C.POLL_INTERVAL,self._poll)

    def _poll(self):
        threading.Thread(target=self._check_changes,daemon=True).start()

    def _check_changes(self):
        try:
            ts=self.db.get_timestamps()
            if ts!=self._last_ts:
                self._last_ts=ts; self.after(0,self._on_db_changed)
        except Exception as ex:
            print(f"[Polling] {ex}")
        finally:
            self._poll_id=self.after(C.POLL_INTERVAL,self._poll)

    def _on_db_changed(self):
        self._sync_lbl.configure(
            text=f"Maj {datetime.datetime.now().strftime('%H:%M:%S')}",fg="#FFE082")
        if self.current_view in self.views:
            v=self.views[self.current_view]
            if hasattr(v,"refresh"): v.refresh()
        self.after(3000,lambda:self._sync_lbl.configure(text="Synchronise",fg="#90CAF9"))

    def _stop_auto_refresh(self):
        if self._poll_id: self.after_cancel(self._poll_id); self._poll_id=None

    def _on_close(self):
        self._stop_auto_refresh(); self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# Point d'entree
# ══════════════════════════════════════════════════════════════════════════════

if __name__=="__main__":
    import mysql.connector
    conn=mysql.connector.connect(
        host="localhost", user="root",
        password="root",  # <- adapter
        database="academix", charset="utf8mb4")
    app=Comptable(db_connection=conn)
    app.mainloop()
    conn.close()