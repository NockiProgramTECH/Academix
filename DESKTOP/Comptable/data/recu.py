"""
recu_pdf.py  --  Academix Comptabilite v2
PDF recus + listes insolvables. Montant en lettres. Latin-1 safe.
"""
from __future__ import annotations
import os, datetime, subprocess, sys
from decimal import Decimal
from fpdf import FPDF

_PRI=(13,71,161); _ACC=(21,101,192); _LBG=(232,240,254)
_TDK=(30,30,30);  _TGR=(80,80,80);  _GRN=(27,139,69)
_ORG=(230,126,34);_WH=(255,255,255); _RED=(192,57,43)

def _safe(s:str)->str:
    rep={'\u2013':'-','\u2014':'-','\u2019':"'",'\u201c':'"','\u201d':'"',
         '\u2026':'...','\u202f':' ','\u00e9':'e','\u00e8':'e','\u00ea':'e',
         '\u00e0':'a','\u00e2':'a','\u00e7':'c','\u00ee':'i','\u00f4':'o',
         '\u00fb':'u','\u00e3':'a','\u00fc':'u','\u00f6':'o','\u00e4':'a'}
    for k,v in rep.items(): s=s.replace(k,v)
    return ''.join(c if ord(c)<256 else '?' for c in s)

def _fc(v)->str:
    return f"{float(v):,.0f} FCFA".replace(","," ")

# ── Montant en lettres (Francs CFA) ─────────────────────────────────────────
_U=["","un","deux","trois","quatre","cinq","six","sept","huit","neuf","dix",
    "onze","douze","treize","quatorze","quinze","seize","dix-sept","dix-huit","dix-neuf"]
_D=["","","vingt","trente","quarante","cinquante","soixante","soixante","quatre-vingt","quatre-vingt"]

def _cent(n:int)->str:
    if n==0: return ""
    if n<20: return _U[n]
    d,u=divmod(n,10)
    if d==7: base="soixante"; u+=10
    elif d==9: base="quatre-vingt"; u+=10
    else: base=_D[d]
    if d in(7,9): return base+("-"+_U[u] if u else ("s" if d==9 else ""))
    lien="-et-" if u==1 and d not in(8,) else ("-" if u else "")
    return base+(lien+_U[u] if u else ("s" if d==8 else ""))

def _milliers(n:int)->str:
    if n==0: return "zero"
    parts=[]
    mil,c=divmod(n,1000)
    if mil==1: parts.append("mille")
    elif mil>1: parts.append(_cent(mil)+" mille" if mil<100 else _groupe(mil)+" mille")
    if c: parts.append(_cent(c))
    return " ".join(p for p in parts if p)

def _groupe(n:int)->str:
    c,r=divmod(n,100)
    if c==0: return _cent(r)
    if c==1: h="cent"
    else: h=_cent(c)+" cent"
    if r==0 and c>1: h+="s"
    return (h+" "+_cent(r)).strip() if r else h

def montant_en_lettres(montant)->str:
    try: n=int(round(float(montant)))
    except: return ""
    if n==0: return "zero franc CFA"
    mil,c=divmod(n,1000000)
    mil2,c2=divmod(c,1000)
    parts=[]
    if mil: parts.append((_groupe(mil)+" million" if mil==1 else _groupe(mil)+" millions"))
    if mil2==1: parts.append("mille")
    elif mil2>1: parts.append(_groupe(mil2)+" mille")
    if c2: parts.append(_groupe(c2))
    return " ".join(parts)+" franc CFA"

# ── PDF Recu ──────────────────────────────────────────────────────────────────
class _RecuPDF(FPDF):
    def __init__(self,pmt,eleve,detail,reste):
        super().__init__()
        self.pmt=pmt; self.eleve=eleve; self.detail=detail; self.reste=reste
        self.set_auto_page_break(True,15); self.add_page(); self._draw()

    def _draw(self):
        p=self
        p.set_fill_color(*_PRI); p.rect(0,0,210,30,"F")
        p.set_font("Helvetica","B",18); p.set_text_color(*_WH)
        p.set_xy(10,7); p.cell(120,9,"ACADEMIX")
        p.set_font("Helvetica","",9); p.set_xy(10,18); p.cell(120,6,"Systeme de gestion scolaire")
        p.set_font("Helvetica","B",10); p.set_xy(135,7); p.set_text_color(210,230,255)
        p.cell(65,6,_safe(f"RECU  {self.pmt.get('recu_num','')}"),align="R")
        p.set_font("Helvetica","",8); p.set_xy(135,14)
        dt=self.pmt.get("date_paiement",datetime.datetime.now())
        p.cell(65,5,_safe(dt.strftime("%d/%m/%Y %H:%M") if isinstance(dt,datetime.datetime) else str(dt)),align="R")
        p.set_xy(135,21); p.cell(65,5,_safe(f"Annee : {self.pmt.get('annee_scolaire','')}"),align="R")
        p.ln(34)
        # annule ?
        if self.pmt.get("annule"):
            p.set_fill_color(*_RED); p.set_text_color(*_WH); p.set_font("Helvetica","B",14)
            p.cell(190,12,"  !! PAIEMENT ANNULE !!",fill=True,ln=True)
            p.ln(2)
        p.set_text_color(*_TDK); p.set_fill_color(*_LBG)
        p.set_font("Helvetica","B",14); p.cell(190,10,"  RECU DE PAIEMENT",fill=True,ln=True); p.ln(4)
        # eleve
        p.set_font("Helvetica","B",11); p.set_text_color(*_PRI)
        p.cell(190,7,"Informations de l'eleve",ln=True)
        p.set_draw_color(*_PRI); p.line(10,p.get_y(),200,p.get_y()); p.ln(2)
        e=self.eleve
        for lbl,val in [("Nom & Prenom",_safe(f"{e.get('nom','')} {e.get('prenom','')}".strip())),
                        ("Matricule",_safe(str(e.get("matricule","")))),
                        ("Classe",_safe(str(e.get("classe_reelle",""))))]:
            p.set_font("Helvetica","B",10); p.set_text_color(*_TDK)
            p.cell(55,7,f"  {lbl} :"); p.set_font("Helvetica","",10); p.cell(135,7,val,ln=True)
        p.ln(4)
        # tableau frais
        p.set_font("Helvetica","B",11); p.set_text_color(*_PRI)
        p.cell(190,7,"Detail des frais",ln=True)
        p.set_draw_color(*_PRI); p.line(10,p.get_y(),200,p.get_y()); p.ln(2)
        p.set_fill_color(*_PRI); p.set_text_color(*_WH); p.set_font("Helvetica","B",9)
        for w,l in [(72,"  Type de frais"),(30,"Brut"),(26,"Remise"),(32,"Net"),(30,"Paye"),(30,"Reste")]:
            p.cell(w,8,l,fill=True,align="C")
        p.ln()
        fill=False
        for r in self.detail:
            bg=(232,240,254) if fill else (255,255,255)
            p.set_fill_color(*bg); p.set_text_color(*_TDK); p.set_font("Helvetica","",9)
            reste_l=float(r.get("reste",0))
            p.cell(72,7,f"  {_safe(r['nom'])}",fill=fill)
            p.cell(30,7,_fc(r.get("montant_brut",r["montant_total"])),fill=fill,align="C")
            p.cell(26,7,_fc(r.get("remise",0)),fill=fill,align="C")
            p.cell(32,7,_fc(r["montant_total"]),fill=fill,align="C")
            p.cell(30,7,_fc(r["total_paye"]),fill=fill,align="C")
            p.set_text_color(*(_GRN if reste_l<=0 else _ORG))
            p.cell(30,7,_fc(reste_l),fill=fill,align="C",ln=True)
            p.set_text_color(*_TDK); fill=not fill
        p.ln(3)
        # montant encaisse
        p.set_fill_color(*_PRI); p.set_text_color(*_WH); p.set_font("Helvetica","B",11)
        p.cell(140,10,"  Montant encaisse ce paiement :",fill=True)
        p.cell(50,10,_fc(self.pmt.get("montant",0)),fill=True,align="C",ln=True)
        # montant en lettres
        p.set_fill_color(*_LBG); p.set_text_color(*_TDK); p.set_font("Helvetica","I",9)
        lettres=_safe(montant_en_lettres(self.pmt.get("montant",0)).upper())
        p.cell(190,7,f"  Soit : {lettres}",fill=True,ln=True); p.ln(2)
        # reste
        color=_ORG if float(self.reste)>0 else _GRN
        p.set_fill_color(*color); p.set_text_color(*_WH); p.set_font("Helvetica","B",10)
        lbl2="  Reste global a payer :" if float(self.reste)>0 else "  Situation : TOUS FRAIS SOLDES"
        p.cell(140,9,lbl2,fill=True); p.cell(50,9,_fc(self.reste),fill=True,align="C",ln=True); p.ln(5)
        notes=_safe(str(self.pmt.get("notes","") or ""))
        if notes:
            p.set_font("Helvetica","I",9); p.set_text_color(*_TGR)
            p.multi_cell(190,6,f"Notes : {notes}"); p.ln(2)
        p.set_y(-32); p.set_draw_color(*_ACC); p.line(10,p.get_y(),200,p.get_y()); p.ln(2)
        p.set_font("Helvetica","I",8); p.set_text_color(*_TGR)
        p.cell(130,5,"Conservez ce recu comme preuve de paiement.")
        p.cell(60,5,f"Imprime le {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",align="R",ln=True)
        p.set_font("Helvetica","B",8); p.set_text_color(*_PRI)
        p.cell(190,5,"Developpe par Lankoande Enock  -  (c) 2024 Academix. Tous droits reserves.",align="C")

def generer_recu_pdf(pmt,eleve,detail,reste,output_dir=".") -> str:
    os.makedirs(output_dir,exist_ok=True)
    path=os.path.join(output_dir,f"recu_{pmt.get('recu_num','X')}.pdf")
    _RecuPDF(pmt,eleve,detail,reste).output(path); return path

def generer_insolvables_pdf(classe,eleves,annee="2025-2026",output_dir=".") -> str:
    os.makedirs(output_dir,exist_ok=True)
    path=os.path.join(output_dir,f"insolvables_{_safe(classe).replace(' ','_')}_{annee}.pdf")
    pdf=FPDF(); pdf.add_page(); pdf.set_auto_page_break(True,15)
    pdf.set_fill_color(*_PRI); pdf.rect(0,0,210,28,"F")
    pdf.set_font("Helvetica","B",15); pdf.set_text_color(*_WH)
    pdf.set_xy(10,6); pdf.cell(190,8,"ACADEMIX - Eleves insolvables")
    pdf.set_font("Helvetica","",9); pdf.set_xy(10,17)
    pdf.cell(190,6,_safe(f"Classe : {classe} | Annee : {annee} | Edite le {datetime.date.today().strftime('%d/%m/%Y')}"))
    pdf.set_y(33); pdf.set_fill_color(*_LBG); pdf.set_text_color(*_TDK); pdf.set_font("Helvetica","B",10)
    pdf.cell(190,8,f"  Eleves concernes : {len(eleves)}",fill=True,ln=True); pdf.ln(3)
    pdf.set_fill_color(*_PRI); pdf.set_text_color(*_WH); pdf.set_font("Helvetica","B",9)
    for w,l in [(10,"N"),(38,"Matricule"),(68,"Nom & Prenom"),(40,"Classe"),(34,"Reste")]:
        pdf.cell(w,8,l,fill=True,align="C")
    pdf.ln(); pdf.set_text_color(*_TDK)
    for i,e in enumerate(eleves,1):
        fill=(i%2==0); pdf.set_fill_color(*((232,240,254) if fill else (255,255,255)))
        pdf.set_font("Helvetica","",9)
        pdf.cell(10,7,str(i),fill=fill,align="C")
        pdf.cell(38,7,_safe(e.get("matricule","")),fill=fill)
        pdf.cell(68,7,_safe(f"{e.get('nom','')} {e.get('prenom','')}".strip()),fill=fill)
        pdf.cell(40,7,_safe(e.get("classe_reelle","")),fill=fill,align="C")
        pdf.set_text_color(*_ORG)
        pdf.cell(34,7,_fc(e.get("reste_total",0)),fill=fill,align="C",ln=True)
        pdf.set_text_color(*_TDK)
    total=sum(float(e.get("reste_total",0)) for e in eleves)
    pdf.set_fill_color(*_PRI); pdf.set_text_color(*_WH); pdf.set_font("Helvetica","B",10)
    pdf.cell(156,9,"  TOTAL IMPAYE",fill=True); pdf.cell(34,9,_fc(total),fill=True,align="C",ln=True)
    pdf.set_y(-25); pdf.set_font("Helvetica","I",8); pdf.set_text_color(*_TGR)
    pdf.line(10,pdf.get_y(),200,pdf.get_y()); pdf.ln(2)
    pdf.set_font("Helvetica","B",8); pdf.set_text_color(*_PRI)
    pdf.cell(190,5,"Developpe par Lankoande Enock  -  (c) 2024 Academix. Tous droits reserves.",align="C")
    pdf.output(path); return path

def open_pdf(path:str):
    try:
        if sys.platform=="win32": os.startfile(path)
        elif sys.platform=="darwin": subprocess.Popen(["open",path])
        else: subprocess.Popen(["xdg-open",path])
    except: pass