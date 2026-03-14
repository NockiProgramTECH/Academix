"""
db_compta_manager.py  --  Academix Comptabilite v2
Decimal partout, transactions avec rollback, annulation, remises, cloture.
"""
from __future__ import annotations
import datetime, random, string
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


D0 = Decimal("0")
D2 = Decimal("0.01")


def to_dec(v) -> Decimal:
    """Convertit n'importe quelle valeur numerique en Decimal."""
    if isinstance(v, Decimal): return v
    if v is None: return D0
    return Decimal(str(v))


class ComptaDB:

    def __init__(self, db_connection):
        self.db = db_connection

    def _cur(self):
        self.db.ping(reconnect=True, attempts=3, delay=1)
        return self.db.cursor(dictionary=True)

    def _exec(self, sql: str, params: tuple = (), fetch: str = "all") -> Any:
        cur = self._cur()
        cur.execute(sql, params)
        if fetch == "all":    result = cur.fetchall()
        elif fetch == "one":  result = cur.fetchone()
        elif fetch == "lastrowid":
            self.db.commit(); result = cur.lastrowid
        else:
            self.db.commit(); result = None
        cur.close()
        return result

    @staticmethod
    def gen_recu() -> str:
        n = datetime.datetime.now()
        return f"REC{n.strftime('%Y%m%d%H%M%S')}{''.join(random.choices(string.digits,k=4))}"

    # ── Type de frais ─────────────────────────────────────────────────────────

    def get_types_frais(self) -> list[dict]:
        return self._exec("SELECT * FROM type_frais WHERE actif=1 ORDER BY nom")

    def get_type_frais(self, tf_id: int) -> dict | None:
        return self._exec("SELECT * FROM type_frais WHERE id=%s",(tf_id,),"one")

    def create_type_frais(self, nom: str, montant: float, desc: str="") -> int:
        return self._exec(
            "INSERT INTO type_frais(nom,montant_total,description) VALUES(%s,%s,%s)",
            (nom, str(to_dec(montant)), desc), "lastrowid")

    def update_type_frais(self, tf_id:int, nom:str, montant:float, desc:str=""):
        self._exec(
            "UPDATE type_frais SET nom=%s,montant_total=%s,description=%s WHERE id=%s",
            (nom, str(to_dec(montant)), desc, tf_id), "commit")

    def delete_type_frais(self, tf_id:int):
        self._exec("UPDATE type_frais SET actif=0 WHERE id=%s",(tf_id,),"commit")

    # ── Tranches ──────────────────────────────────────────────────────────────

    def get_tranches(self, tf_id:int) -> list[dict]:
        return self._exec(
            "SELECT * FROM configuration_tranches WHERE type_frais_id=%s ORDER BY ordre",
            (tf_id,))

    def create_tranche(self, tf_id:int, nom:str, montant:float, ordre:int) -> int:
        return self._exec(
            "INSERT INTO configuration_tranches(type_frais_id,nom_tranche,montant,ordre)"
            " VALUES(%s,%s,%s,%s)",
            (tf_id, nom, str(to_dec(montant)), ordre), "lastrowid")

    def delete_tranches(self, tf_id:int):
        self._exec("DELETE FROM configuration_tranches WHERE type_frais_id=%s",
                   (tf_id,),"commit")

    def replace_tranches(self, tf_id:int, tranches:list[dict]):
        self.delete_tranches(tf_id)
        for i,t in enumerate(tranches,1):
            self.create_tranche(tf_id, t["nom"], float(t["montant"]), i)

    # ── Remises ───────────────────────────────────────────────────────────────

    def get_remise(self, eleve_id:str, tf_id:int, annee:str) -> Decimal:
        r = self._exec(
            "SELECT montant_remise FROM remises_eleve "
            "WHERE eleve_id=%s AND type_frais_id=%s AND annee_scolaire=%s",
            (eleve_id, tf_id, annee), "one")
        return to_dec(r["montant_remise"]) if r else D0

    def get_remises_eleve(self, eleve_id:str, annee:str) -> list[dict]:
        return self._exec(
            "SELECT r.*,tf.nom AS type_nom FROM remises_eleve r "
            "JOIN type_frais tf ON tf.id=r.type_frais_id "
            "WHERE r.eleve_id=%s AND r.annee_scolaire=%s",
            (eleve_id, annee))

    def upsert_remise(self, eleve_id:str, tf_id:int, montant:float,
                      motif:str, annee:str):
        self._exec(
            "INSERT INTO remises_eleve(eleve_id,type_frais_id,montant_remise,motif,annee_scolaire)"
            " VALUES(%s,%s,%s,%s,%s)"
            " ON DUPLICATE KEY UPDATE montant_remise=%s, motif=%s",
            (eleve_id, tf_id, str(to_dec(montant)), motif, annee,
             str(to_dec(montant)), motif), "commit")

    def delete_remise(self, eleve_id:str, tf_id:int, annee:str):
        self._exec(
            "DELETE FROM remises_eleve WHERE eleve_id=%s AND type_frais_id=%s AND annee_scolaire=%s",
            (eleve_id, tf_id, annee), "commit")

    # ── Classes / Eleves ──────────────────────────────────────────────────────

    def get_classes(self) -> list[dict]:
        return self._exec("SELECT * FROM classes ORDER BY nom_classe")

    def get_eleves(self, classe_reelle:str) -> list[dict]:
        return self._exec(
            "SELECT id,matricule,nom,prenom,classe_reelle FROM inscriptions_eleve "
            "WHERE classe_reelle=%s AND statut='ACCEPTED' ORDER BY nom,prenom",
            (classe_reelle,))

    def get_eleve(self, eleve_id:str) -> dict | None:
        return self._exec("SELECT * FROM inscriptions_eleve WHERE id=%s",
                          (eleve_id,),"one")

    def search_eleves(self, terme:str) -> list[dict]:
        t = f"%{terme}%"
        return self._exec(
            "SELECT id,matricule,nom,prenom,classe_reelle FROM inscriptions_eleve "
            "WHERE statut='ACCEPTED' AND (nom LIKE %s OR prenom LIKE %s OR matricule LIKE %s) "
            "ORDER BY nom,prenom LIMIT 30",
            (t,t,t))

    # ── Paiements ─────────────────────────────────────────────────────────────

    def enregistrer_paiement(self, eleve_id:str, tf_id:int,
                              tranche_id, montant:float,
                              notes:str="", annee:str="2025-2026") -> dict:
        """Transaction complete : rollback si echec."""
        recu = self.gen_recu()
        try:
            cur = self._cur()
            cur.execute(
                "INSERT INTO paiements(eleve_id,type_frais_id,tranche_id,montant,"
                "recu_num,notes,annee_scolaire) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (eleve_id, tf_id, tranche_id, str(to_dec(montant)),
                 recu, notes, annee))
            self.db.commit()
            pid = cur.lastrowid
            cur.close()
            return {"id": pid, "recu_num": recu}
        except Exception:
            self.db.rollback()
            raise

    def annuler_paiement(self, pmt_id:int, motif:str):
        """Annulation logique -- la ligne est conservee pour l'audit."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._exec(
            "UPDATE paiements SET annule=1,annule_motif=%s,annule_at=%s WHERE id=%s",
            (motif, now, pmt_id), "commit")

    def get_paiement_by_id(self, pmt_id:int) -> dict | None:
        return self._exec("SELECT * FROM paiements WHERE id=%s",(pmt_id,),"one")

    def get_paiements_eleve(self, eleve_id:str, annee:str="2025-2026") -> list[dict]:
        return self._exec(
            "SELECT p.*,tf.nom AS type_nom,ct.nom_tranche "
            "FROM paiements p "
            "JOIN type_frais tf ON tf.id=p.type_frais_id "
            "LEFT JOIN configuration_tranches ct ON ct.id=p.tranche_id "
            "WHERE p.eleve_id=%s AND p.annee_scolaire=%s AND p.annule=0 "
            "ORDER BY p.date_paiement",
            (eleve_id, annee))

    def get_total_par_type(self, eleve_id:str, annee:str="2025-2026") -> list[dict]:
        """Retourne montant_total (remise deduite) et total_paye en Decimal."""
        rows = self._exec(
            "SELECT tf.id,tf.nom,tf.montant_total,"
            " COALESCE(SUM(CASE WHEN p.annule=0 THEN p.montant ELSE 0 END),0) AS total_paye "
            "FROM type_frais tf "
            "LEFT JOIN paiements p ON p.type_frais_id=tf.id AND p.eleve_id=%s AND p.annee_scolaire=%s "
            "WHERE tf.actif=1 GROUP BY tf.id,tf.nom,tf.montant_total",
            (eleve_id, annee))
        result = []
        for r in rows:
            remise   = self.get_remise(eleve_id, r["id"], annee)
            mt_net   = max(to_dec(r["montant_total"]) - remise, D0)
            total_p  = to_dec(r["total_paye"])
            result.append({
                "id":           r["id"],
                "nom":          r["nom"],
                "montant_total": mt_net,
                "montant_brut": to_dec(r["montant_total"]),
                "remise":       remise,
                "total_paye":   total_p,
                "reste":        max(mt_net - total_p, D0),
            })
        return result

    def get_statut_eleve(self, eleve_id:str, annee:str="2025-2026") -> str:
        for r in self.get_total_par_type(eleve_id, annee):
            if r["reste"] > D0:
                return "Impaye"
        return "A jour"

    def get_insolvables(self, classe_reelle:str, annee:str="2025-2026") -> list[dict]:
        result = []
        for e in self.get_eleves(classe_reelle):
            rows  = self.get_total_par_type(e["id"], annee)
            reste = sum((r["reste"] for r in rows), D0)
            if reste > D0:
                e["reste_total"] = reste
                result.append(e)
        return result

    def get_paiement_by_recu(self, recu_num:str) -> dict | None:
        return self._exec(
            "SELECT p.*,tf.nom AS type_nom,ct.nom_tranche,"
            " e.nom AS eleve_nom,e.prenom AS eleve_prenom,e.matricule,e.classe_reelle "
            "FROM paiements p "
            "JOIN type_frais tf ON tf.id=p.type_frais_id "
            "LEFT JOIN configuration_tranches ct ON ct.id=p.tranche_id "
            "JOIN inscriptions_eleve e ON e.id=p.eleve_id "
            "WHERE p.recu_num=%s",
            (recu_num,), "one")

    def rechercher_recu(self, terme:str) -> list[dict]:
        t = f"%{terme}%"
        return self._exec(
            "SELECT p.*,tf.nom AS type_nom,"
            " e.nom AS eleve_nom,e.prenom AS eleve_prenom,e.classe_reelle "
            "FROM paiements p "
            "JOIN type_frais tf ON tf.id=p.type_frais_id "
            "JOIN inscriptions_eleve e ON e.id=p.eleve_id "
            "WHERE p.recu_num LIKE %s OR e.nom LIKE %s OR e.prenom LIKE %s "
            "ORDER BY p.date_paiement DESC LIMIT 30",
            (t,t,t))

    def get_paiements_recents(self, limite:int=20, annee:str="2025-2026") -> list[dict]:
        return self._exec(
            "SELECT p.id,p.recu_num,p.montant,p.date_paiement,p.annule,"
            " e.nom AS eleve_nom,e.prenom AS eleve_prenom,e.classe_reelle,"
            " tf.nom AS type_nom "
            "FROM paiements p "
            "JOIN inscriptions_eleve e ON e.id=p.eleve_id "
            "JOIN type_frais tf ON tf.id=p.type_frais_id "
            "WHERE p.annee_scolaire=%s "
            "ORDER BY p.date_paiement DESC LIMIT %s",
            (annee, limite))

    # ── Depot & Cloture ───────────────────────────────────────────────────────

    def jour_est_cloture(self, date_j:str) -> bool:
        r = self._exec("SELECT id FROM clotures_caisse WHERE date_cloture=%s",
                       (date_j,), "one")
        return r is not None

    def cloturer_caisse(self, date_j:str, notes:str="") -> dict:
        if self.jour_est_cloture(date_j):
            raise ValueError(f"Caisse du {date_j} deja cloturee.")
        r_row = self._exec(
            "SELECT COALESCE(SUM(montant),0) AS t FROM paiements "
            "WHERE DATE(date_paiement)=%s AND annule=0", (date_j,), "one")
        d_row = self._exec(
            "SELECT COALESCE(SUM(montant),0) AS t FROM depenses "
            "WHERE date_depense=%s", (date_j,), "one")
        rec = to_dec(r_row["t"])
        dep = to_dec(d_row["t"])
        sol = rec - dep
        self._exec(
            "INSERT INTO clotures_caisse(date_cloture,total_recettes,total_depenses,solde,notes)"
            " VALUES(%s,%s,%s,%s,%s)",
            (date_j, str(rec), str(dep), str(sol), notes), "commit")
        return {"recettes": rec, "depenses": dep, "solde": sol}

    def get_clotures(self, limite:int=30) -> list[dict]:
        return self._exec(
            "SELECT * FROM clotures_caisse ORDER BY date_cloture DESC LIMIT %s",
            (limite,))

    # ── Depenses ──────────────────────────────────────────────────────────────

    def create_depense(self, motif:str, montant:float, categorie:str,
                       date_d:str, notes:str="") -> int:
        return self._exec(
            "INSERT INTO depenses(motif,montant,categorie,date_depense,notes)"
            " VALUES(%s,%s,%s,%s,%s)",
            (motif, str(to_dec(montant)), categorie, date_d, notes), "lastrowid")

    def get_depenses(self, debut:str=None, fin:str=None) -> list[dict]:
        if debut and fin:
            return self._exec(
                "SELECT * FROM depenses WHERE date_depense BETWEEN %s AND %s "
                "ORDER BY date_depense DESC", (debut, fin))
        return self._exec("SELECT * FROM depenses ORDER BY date_depense DESC")

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def get_stats(self, annee:str="2025-2026") -> dict:
        total_rec = to_dec(self._exec(
            "SELECT COALESCE(SUM(montant),0) AS t FROM paiements "
            "WHERE annee_scolaire=%s AND annule=0", (annee,), "one")["t"])
        today = datetime.date.today().isoformat()
        rec_j = to_dec(self._exec(
            "SELECT COALESCE(SUM(montant),0) AS t FROM paiements "
            "WHERE DATE(date_paiement)=%s AND annee_scolaire=%s AND annule=0",
            (today, annee), "one")["t"])
        total_dep = to_dec(self._exec(
            "SELECT COALESCE(SUM(montant),0) AS t FROM depenses", (), "one")["t"])
        nb_imp = 0
        classes = self.get_classes()
        for cl in classes:
            for e in self.get_eleves(cl["nom_classe"]):
                if self.get_statut_eleve(e["id"], annee) == "Impaye":
                    nb_imp += 1
        nb = self._exec(
            "SELECT COUNT(*) AS c FROM inscriptions_eleve WHERE statut='ACCEPTED'",
            (), "one")["c"]
        return {
            "recettes":      total_rec,
            "recettes_jour": rec_j,
            "depenses":      total_dep,
            "solde":         total_rec - total_dep,
            "nb_eleves":     nb,
            "nb_impayes":    nb_imp,
        }

    def get_recettes_par_type(self, annee:str="2025-2026") -> list[dict]:
        rows = self._exec(
            "SELECT tf.nom,COALESCE(SUM(p.montant),0) AS total "
            "FROM type_frais tf "
            "LEFT JOIN paiements p ON p.type_frais_id=tf.id AND p.annee_scolaire=%s AND p.annule=0 "
            "WHERE tf.actif=1 GROUP BY tf.id,tf.nom ORDER BY total DESC", (annee,))
        return [{**r, "total": to_dec(r["total"])} for r in rows]

    # ── Timestamps pour polling ───────────────────────────────────────────────

    def get_timestamps(self) -> dict:
        ts = {}
        for tbl in ("paiements","depenses","type_frais","configuration_tranches","remises_eleve"):
            try:
                r = self._exec(f"SELECT MAX(created_at) AS t FROM {tbl}", (), "one")
                ts[tbl] = str(r["t"]) if r and r["t"] else None
            except Exception:
                ts[tbl] = None
        return ts