"""
db_vie_scolaire.py  --  Academix · Module Vie Scolaire v2
=========================================================
CORRECTIONS v2 :
  • calculer_penalite_absence() : pénalité en POINTS (pas en pts de moyenne)
  • get_bulletin_avec_penalite() : formule correcte par trimestre :
        total_points  = Σ(moy_matiere × coeff)   ← toutes matières
        points_nets   = total_points − penalite_points
        moy_trim      = points_nets / Σ(coeff)
"""
from __future__ import annotations
import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

D0 = Decimal("0")


def _to_dec(v) -> Decimal:
    if isinstance(v, Decimal): return v
    if v is None: return D0
    return Decimal(str(v))


class VieScolaireDB:
    ANNEE_DEFAUT = "2025-2026"

    def __init__(self, db_connection):
        self.db = db_connection
        self._create_tables()

    # ── utilitaires ──────────────────────────────────────────────────────────

    def _cur(self):
        self.db.ping(reconnect=True, attempts=3, delay=1)
        return self.db.cursor(dictionary=True)

    def _exec(self, sql: str, params: tuple = (), fetch: str = "all") -> Any:
        cur = self._cur()
        try:
            cur.execute(sql, params)
            if fetch == "all":    result = cur.fetchall()
            elif fetch == "one":  result = cur.fetchone()
            elif fetch == "lastrowid": self.db.commit(); result = cur.lastrowid
            else:                 self.db.commit(); result = None
        except Exception as e:
            self.db.rollback(); raise e
        finally:
            cur.close()
        return result

    # ── création des tables ──────────────────────────────────────────────────

    def _create_tables(self):
        stmts = [
            """CREATE TABLE IF NOT EXISTS absences (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                eleve_id       VARCHAR(60) NOT NULL,
                date_absence   DATE        NOT NULL,
                heure_debut    TIME        NOT NULL,
                heure_fin      TIME        NOT NULL,
                statut         ENUM('JUSTIFIEE','NON_JUSTIFIEE') DEFAULT 'NON_JUSTIFIEE',
                motif          VARCHAR(255),
                trimestre      INT NOT NULL DEFAULT 1,
                annee_scolaire VARCHAR(20) NOT NULL,
                creneau_id     INT,
                saisie_par     VARCHAR(50) DEFAULT 'SECRETARIAT',
                date_saisie    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (eleve_id) REFERENCES Inscriptions_eleve(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

            # points_par_palier = pts retirés du TOTAL DES POINTS (pas de la moyenne)
            """CREATE TABLE IF NOT EXISTS configuration_discipline (
                id                INT AUTO_INCREMENT PRIMARY KEY,
                tranche_heures    DECIMAL(5,2) NOT NULL DEFAULT 5.00,
                points_par_palier DECIMAL(6,2) NOT NULL DEFAULT 2.00,
                plafond_points    DECIMAL(6,2) NOT NULL DEFAULT 20.00,
                description       VARCHAR(255)
                    DEFAULT 'Toutes les 5h NJ = -2 pts sur le total des points trimestriels'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

            """CREATE TABLE IF NOT EXISTS emploi_du_temps (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                classe_id      INT NOT NULL,
                matiere_id     INT NOT NULL,
                professeur_id  INT,
                jour           ENUM('Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi') NOT NULL,
                heure_debut    TIME NOT NULL,
                heure_fin      TIME NOT NULL,
                salle          VARCHAR(50),
                annee_scolaire VARCHAR(20) NOT NULL,
                FOREIGN KEY (classe_id)     REFERENCES Classes(id),
                FOREIGN KEY (matiere_id)    REFERENCES Matiere(id_matiere),
                FOREIGN KEY (professeur_id) REFERENCES Professeur(id_professeur)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        ]
        cur = self._cur()
        for s in stmts:
            try: cur.execute(s)
            except Exception as e: print(f"[VieScolaireDB] {e}")
        self.db.commit()
        cur.close()
        self._seed_config()

    def _seed_config(self):
        try:
            r = self._exec("SELECT id FROM configuration_discipline LIMIT 1", fetch="one")
            if not r:
                self._exec(
                    "INSERT INTO configuration_discipline (tranche_heures,points_par_palier,plafond_points) "
                    "VALUES (5.00,2.00,20.00)", fetch="commit")
        except Exception as e:
            print(f"[VieScolaireDB._seed_config] {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION DISCIPLINE
    # ═══════════════════════════════════════════════════════════════════════════

    def get_config_discipline(self) -> dict | None:
        return self._exec("SELECT * FROM configuration_discipline LIMIT 1", fetch="one")

    def update_config_discipline(self, tranche_heures: float, points_par_palier: float,
                                  plafond_points: float, description: str = "") -> None:
        row = self.get_config_discipline()
        if row:
            self._exec(
                "UPDATE configuration_discipline "
                "SET tranche_heures=%s, points_par_palier=%s, plafond_points=%s, description=%s "
                "WHERE id=%s",
                (tranche_heures, points_par_palier, plafond_points, description, row["id"]), "commit")
        else:
            self._exec(
                "INSERT INTO configuration_discipline (tranche_heures,points_par_palier,plafond_points,description) "
                "VALUES (%s,%s,%s,%s)",
                (tranche_heures, points_par_palier, plafond_points, description), "commit")

    # ═══════════════════════════════════════════════════════════════════════════
    # ABSENCES
    # ═══════════════════════════════════════════════════════════════════════════

    def add_absence(self, eleve_id: str, date_absence: str, heure_debut: str, heure_fin: str,
                    trimestre: int, annee: str, statut: str = "NON_JUSTIFIEE",
                    motif: str = "", creneau_id: int | None = None,
                    saisie_par: str = "SECRETARIAT") -> int:
        return self._exec(
            "INSERT INTO absences (eleve_id,date_absence,heure_debut,heure_fin,"
            "statut,motif,trimestre,annee_scolaire,creneau_id,saisie_par) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (eleve_id, date_absence, heure_debut, heure_fin,
             statut, motif or None, trimestre, annee, creneau_id, saisie_par),
            "lastrowid")

    def justifier_absence(self, absence_id: int, motif: str = "") -> None:
        self._exec("UPDATE absences SET statut='JUSTIFIEE', motif=%s WHERE id=%s",
                   (motif or None, absence_id), "commit")

    def annuler_justification(self, absence_id: int) -> None:
        self._exec("UPDATE absences SET statut='NON_JUSTIFIEE' WHERE id=%s",
                   (absence_id,), "commit")

    def delete_absence(self, absence_id: int) -> None:
        self._exec("DELETE FROM absences WHERE id=%s", (absence_id,), "commit")

    def get_absences_classe_date(self, classe_id: int, date_absence: str,
                                  annee: str = ANNEE_DEFAUT) -> list[dict]:
        return self._exec(
            "SELECT a.*, ie.nom, ie.prenom, ie.matricule "
            "FROM absences a "
            "JOIN Inscriptions_eleve ie ON ie.id = a.eleve_id "
            "JOIN Scolarite_Affectation sa ON sa.eleve_id = a.eleve_id "
            "WHERE sa.classe_id=%s AND a.date_absence=%s AND a.annee_scolaire=%s "
            "ORDER BY ie.nom, ie.prenom, a.heure_debut",
            (classe_id, date_absence, annee))

    def get_nb_absences_classe(self, classe_id: int, trimestre: int,
                                annee: str = ANNEE_DEFAUT) -> list[dict]:
        return self._exec(
            "SELECT ie.id AS eleve_id, ie.nom, ie.prenom, ie.matricule, "
            "  ROUND(SUM(TIME_TO_SEC(TIMEDIFF(a.heure_fin,a.heure_debut)))/3600,2) AS total_heures, "
            "  ROUND(SUM(CASE WHEN a.statut='NON_JUSTIFIEE' THEN "
            "    TIME_TO_SEC(TIMEDIFF(a.heure_fin,a.heure_debut)) ELSE 0 END)/3600,2) AS heures_nj, "
            "  ROUND(SUM(CASE WHEN a.statut='JUSTIFIEE' THEN "
            "    TIME_TO_SEC(TIMEDIFF(a.heure_fin,a.heure_debut)) ELSE 0 END)/3600,2) AS heures_j "
            "FROM absences a "
            "JOIN Inscriptions_eleve ie ON ie.id = a.eleve_id "
            "JOIN Scolarite_Affectation sa ON sa.eleve_id = a.eleve_id "
            "WHERE sa.classe_id=%s AND a.trimestre=%s AND a.annee_scolaire=%s "
            "GROUP BY ie.id, ie.nom, ie.prenom, ie.matricule ORDER BY heures_nj DESC",
            (classe_id, trimestre, annee))

    def get_heures_nj(self, eleve_id: str, trimestre: int, annee: str = ANNEE_DEFAUT) -> Decimal:
        row = self._exec(
            "SELECT ROUND(SUM(TIME_TO_SEC(TIMEDIFF(heure_fin,heure_debut)))/3600,4) AS h "
            "FROM absences WHERE eleve_id=%s AND trimestre=%s AND annee_scolaire=%s AND statut='NON_JUSTIFIEE'",
            (eleve_id, trimestre, annee), "one")
        return _to_dec(row["h"]) if row and row["h"] else D0

    def get_heures_j(self, eleve_id: str, trimestre: int, annee: str = ANNEE_DEFAUT) -> Decimal:
        row = self._exec(
            "SELECT ROUND(SUM(TIME_TO_SEC(TIMEDIFF(heure_fin,heure_debut)))/3600,2) AS h "
            "FROM absences WHERE eleve_id=%s AND trimestre=%s AND annee_scolaire=%s AND statut='JUSTIFIEE'",
            (eleve_id, trimestre, annee), "one")
        return _to_dec(row["h"]) if row and row["h"] else D0

    # ═══════════════════════════════════════════════════════════════════════════
    # PÉNALITÉ  ← CORRIGÉ v2 : retourne des POINTS (à soustraire du total)
    # ═══════════════════════════════════════════════════════════════════════════

    def calculer_penalite_absence(self, eleve_id: str, trimestre: int,
                                   annee: str = ANNEE_DEFAUT) -> Decimal:
        """
        Retourne les POINTS à retrancher du total Σ(moy×coeff) trimestriel.

        Config par défaut : 5h NJ → −2 pts, plafond 20 pts
          8h  → 1 palier → −2 pts
          11h → 2 paliers → −4 pts
          55h → 11 paliers → plafonné −20 pts
        """
        cfg = self.get_config_discipline()
        if not cfg: return D0
        tranche = _to_dec(cfg["tranche_heures"])
        pts_pal = _to_dec(cfg["points_par_palier"])
        plafond = _to_dec(cfg["plafond_points"])
        if tranche <= D0: return D0
        heures_nj = self.get_heures_nj(eleve_id, trimestre, annee)
        if heures_nj <= D0: return D0
        paliers  = int(heures_nj / tranche)
        penalite = _to_dec(paliers) * pts_pal
        return min(penalite, plafond).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # ═══════════════════════════════════════════════════════════════════════════
    # BULLETIN CORRIGÉ v2
    # ═══════════════════════════════════════════════════════════════════════════

    def get_bulletin_avec_penalite(self, eleve_id: str, trimestre: int,
                                    notes_db, annee: str = ANNEE_DEFAUT) -> dict:
        """
        Formule trimestrielle corrigée :

          lignes          = détail par matière (NotesDB, inchangé)
          total_pts_brut  = Σ(moy_matiere × coeff)    ← somme des POINTS de toutes les matières
          total_coeff     = Σ coeff
          penalite_pts    = calculer_penalite_absence()  ← en POINTS
          total_pts_nets  = max(0, total_pts_brut − penalite_pts)
          moy_brute       = total_pts_brut / total_coeff   (pour info)
          moy_definitive  = total_pts_nets  / total_coeff  ← MOYENNE TRIMESTRIELLE FINALE
        """
        lignes = notes_db.get_bulletin_eleve(eleve_id, trimestre, annee)

        total_pts_brut = D0
        total_coeff    = D0
        for r in lignes:
            moy   = _to_dec(r["moyenne"])
            coeff = _to_dec(r["coefficient"])
            total_pts_brut += moy * coeff
            total_coeff    += coeff

        total_pts_brut = total_pts_brut.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        moy_brute = D0
        if total_coeff > D0:
            moy_brute = (total_pts_brut / total_coeff).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)

        penalite_pts   = self.calculer_penalite_absence(eleve_id, trimestre, annee)
        total_pts_nets = max(D0, total_pts_brut - penalite_pts).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)

        moy_definitive = D0
        if total_coeff > D0:
            moy_definitive = (total_pts_nets / total_coeff).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "lignes":            lignes,
            "total_pts_brut":    total_pts_brut,    # ex : 87.50 pts
            "total_coeff":       total_coeff,        # ex : 31
            "penalite_pts":      penalite_pts,       # ex : 4.00 pts
            "total_pts_nets":    total_pts_nets,     # ex : 83.50 pts
            "moy_brute":         moy_brute,          # ex : 14.27 / 20
            "moy_definitive":    moy_definitive,     # ex : 13.95 / 20
            "heures_nj":         self.get_heures_nj(eleve_id, trimestre, annee),
            "heures_j":          self.get_heures_j(eleve_id, trimestre, annee),
            "config":            self.get_config_discipline(),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # EMPLOI DU TEMPS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_emploi_classe(self, classe_id: int, annee: str = ANNEE_DEFAUT) -> list[dict]:
        return self._exec(
            "SELECT edt.id, edt.classe_id, edt.matiere_id, edt.professeur_id, "
            "       edt.jour, edt.heure_debut, edt.heure_fin, edt.salle, m.nom_matiere, "
            "       TRIM(CONCAT(COALESCE(p.nom,''),' ',COALESCE(p.prenom,''))) AS prof_nom "
            "FROM emploi_du_temps edt "
            "JOIN Matiere m ON m.id_matiere = edt.matiere_id "
            "LEFT JOIN Professeur p ON p.id_professeur = edt.professeur_id "
            "WHERE edt.classe_id=%s AND edt.annee_scolaire=%s "
            "ORDER BY FIELD(edt.jour,'Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi'), edt.heure_debut",
            (classe_id, annee))

    def add_creneau(self, classe_id: int, matiere_id: int, professeur_id: int | None,
                    jour: str, heure_debut: str, heure_fin: str, salle: str = "",
                    annee: str = ANNEE_DEFAUT) -> int:
        return self._exec(
            "INSERT INTO emploi_du_temps (classe_id,matiere_id,professeur_id,jour,heure_debut,heure_fin,salle,annee_scolaire) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (classe_id, matiere_id, professeur_id or None, jour, heure_debut, heure_fin, salle or None, annee),
            "lastrowid")

    def update_creneau(self, creneau_id: int, matiere_id: int, professeur_id: int | None,
                        jour: str, heure_debut: str, heure_fin: str, salle: str = "") -> None:
        self._exec(
            "UPDATE emploi_du_temps SET matiere_id=%s, professeur_id=%s, jour=%s, "
            "heure_debut=%s, heure_fin=%s, salle=%s WHERE id=%s",
            (matiere_id, professeur_id or None, jour, heure_debut, heure_fin, salle or None, creneau_id),
            "commit")

    def delete_creneau(self, creneau_id: int) -> None:
        self._exec("DELETE FROM emploi_du_temps WHERE id=%s", (creneau_id,), "commit")

    def get_creneaux_par_jour(self, classe_id: int, jour: str,
                               annee: str = ANNEE_DEFAUT) -> list[dict]:
        return self._exec(
            "SELECT edt.id, edt.heure_debut, edt.heure_fin, m.nom_matiere, "
            "       TRIM(CONCAT(COALESCE(p.nom,''),' ',COALESCE(p.prenom,''))) AS prof_nom "
            "FROM emploi_du_temps edt "
            "JOIN Matiere m ON m.id_matiere = edt.matiere_id "
            "LEFT JOIN Professeur p ON p.id_professeur = edt.professeur_id "
            "WHERE edt.classe_id=%s AND edt.jour=%s AND edt.annee_scolaire=%s ORDER BY edt.heure_debut",
            (classe_id, jour, annee))

    # ═══════════════════════════════════════════════════════════════════════════
    # POLLING
    # ═══════════════════════════════════════════════════════════════════════════

    def get_last_absence_ts(self, annee: str = ANNEE_DEFAUT) -> datetime.datetime | None:
        row = self._exec(
            "SELECT MAX(date_saisie) AS ts FROM absences WHERE annee_scolaire=%s",
            (annee,), "one")
        return row["ts"] if row else None

    # ═══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_eleves_classe(self, classe_id: int) -> list[dict]:
        return self._exec(
            "SELECT ie.id, ie.matricule, ie.nom, ie.prenom "
            "FROM Inscriptions_eleve ie "
            "JOIN Scolarite_Affectation sa ON sa.eleve_id = ie.id "
            "WHERE sa.classe_id=%s ORDER BY ie.nom, ie.prenom", (classe_id,))

    def get_classes(self) -> list[dict]:
        return self._exec("SELECT id, nom_classe FROM Classes ORDER BY nom_classe")

    def get_matieres(self) -> list[dict]:
        return self._exec("SELECT id_matiere, nom_matiere FROM Matiere ORDER BY nom_matiere")

    def get_professeurs(self) -> list[dict]:
        return self._exec(
            "SELECT id_professeur, nom, prenom, specialite FROM Professeur ORDER BY nom, prenom")