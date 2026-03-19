"""
db_vie_scolaire.py  --  Academix · Module Vie Scolaire v1
=========================================================
Couche données pour :
  • Absences (JUSTIFIEE / NON_JUSTIFIEE) + justification
  • Configuration des pénalités (règle tranche horaire → retrait de points)
  • Emplois du temps (créneaux par classe, jour, heure, matière, prof)
  • Calcul de la pénalité d'absence sur la moyenne générale

Conventions (identiques à NotesDB) :
  • Méthodes d'écriture → rollback() sur exception
  • Méthodes de lecture  → [] ou None, jamais d'exception visible
  • Réutilise les tables existantes : Classes, Matiere, Inscriptions_eleve,
    Professeur, Scolarite_Affectation
"""
from __future__ import annotations
import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


D0 = Decimal("0")


def _to_dec(v) -> Decimal:
    if isinstance(v, Decimal):
        return v
    if v is None:
        return D0
    return Decimal(str(v))


class VieScolaireDB:
    """
    Instancié avec la connexion MySQL partagée (DbManager.connection).

    Usage depuis Acceuil / NotesView :
        from data.db_vie_scolaire import VieScolaireDB
        self.vs_db = VieScolaireDB(self.Database.connection)
    """

    ANNEE_DEFAUT = "2025-2026"

    def __init__(self, db_connection):
        self.db = db_connection
        self._create_tables()

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES INTERNES
    # ═══════════════════════════════════════════════════════════════════════════

    def _cur(self):
        self.db.ping(reconnect=True, attempts=3, delay=1)
        return self.db.cursor(dictionary=True)

    def _exec(self, sql: str, params: tuple = (), fetch: str = "all") -> Any:
        cur = self._cur()
        try:
            cur.execute(sql, params)
            if fetch == "all":
                result = cur.fetchall()
            elif fetch == "one":
                result = cur.fetchone()
            elif fetch == "lastrowid":
                self.db.commit()
                result = cur.lastrowid
            else:
                self.db.commit()
                result = None
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            cur.close()
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # INITIALISATION DES TABLES
    # ═══════════════════════════════════════════════════════════════════════════

    def _create_tables(self):
        """
        Crée les 3 tables du module Vie Scolaire si elles n'existent pas.

        Tables créées :
          • absences                — une ligne par tranche d'absence
          • configuration_discipline — règle de pénalité globale (1 seule ligne)
          • emploi_du_temps         — créneaux hebdomadaires par classe
        """
        statements = [
            # ── Absences ─────────────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS absences (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                eleve_id     VARCHAR(60) NOT NULL,
                date_absence DATE        NOT NULL,
                heure_debut  TIME        NOT NULL,
                heure_fin    TIME        NOT NULL,
                statut       ENUM('JUSTIFIEE','NON_JUSTIFIEE') DEFAULT 'NON_JUSTIFIEE',
                motif        VARCHAR(255),
                trimestre    INT         NOT NULL DEFAULT 1,
                annee_scolaire VARCHAR(20) NOT NULL,
                creneau_id   INT,
                saisie_par   VARCHAR(50) DEFAULT 'SECRETARIAT',
                date_saisie  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (eleve_id) REFERENCES Inscriptions_eleve(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

            # ── Configuration discipline (pénalité) ───────────────────────────
            # Une seule ligne de configuration ; upsert via id=1.
            # tranche_heures : nombre d'heures non justifiées déclenchant -1 palier
            # points_par_palier : retrait en points par palier (ex : 0.50)
            # plafond_points : plafond total de retrait (ex : 5.00)
            """CREATE TABLE IF NOT EXISTS configuration_discipline (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                tranche_heures   DECIMAL(5,2) NOT NULL DEFAULT 5.00,
                points_par_palier DECIMAL(4,2) NOT NULL DEFAULT 0.50,
                plafond_points   DECIMAL(4,2) NOT NULL DEFAULT 5.00,
                description      VARCHAR(255)
                    DEFAULT 'Toutes les 5h d\\'absence non justifiée = -0.5 pt sur moy. générale'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

            # ── Emploi du temps ───────────────────────────────────────────────
            """CREATE TABLE IF NOT EXISTS emploi_du_temps (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                classe_id     INT  NOT NULL,
                matiere_id    INT  NOT NULL,
                professeur_id INT,
                jour          ENUM('Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi')
                              NOT NULL,
                heure_debut   TIME NOT NULL,
                heure_fin     TIME NOT NULL,
                salle         VARCHAR(50),
                annee_scolaire VARCHAR(20) NOT NULL,
                FOREIGN KEY (classe_id)     REFERENCES Classes(id),
                FOREIGN KEY (matiere_id)    REFERENCES Matiere(id_matiere),
                FOREIGN KEY (professeur_id) REFERENCES Professeur(id_professeur)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        ]
        cur = self._cur()
        for sql in statements:
            try:
                cur.execute(sql)
            except Exception as e:
                print(f"[VieScolaireDB._create_tables] {e}")
        self.db.commit()
        cur.close()

        # Insère la configuration par défaut si la table est vide
        self._seed_config()

    def _seed_config(self):
        """Insère la ligne de configuration par défaut (si absente)."""
        try:
            row = self._exec(
                "SELECT id FROM configuration_discipline LIMIT 1",
                fetch="one"
            )
            if not row:
                self._exec(
                    "INSERT INTO configuration_discipline "
                    "(tranche_heures, points_par_palier, plafond_points) "
                    "VALUES (5.00, 0.50, 5.00)",
                    fetch="commit"
                )
        except Exception as e:
            print(f"[VieScolaireDB._seed_config] {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION DISCIPLINE
    # ═══════════════════════════════════════════════════════════════════════════

    def get_config_discipline(self) -> dict | None:
        """Retourne la règle de pénalité active."""
        return self._exec(
            "SELECT * FROM configuration_discipline LIMIT 1",
            fetch="one"
        )

    def update_config_discipline(self, tranche_heures: float,
                                  points_par_palier: float,
                                  plafond_points: float,
                                  description: str = "") -> None:
        """Met à jour (ou crée) la configuration discipline."""
        row = self.get_config_discipline()
        if row:
            self._exec(
                "UPDATE configuration_discipline "
                "SET tranche_heures=%s, points_par_palier=%s, "
                "    plafond_points=%s, description=%s "
                "WHERE id=%s",
                (tranche_heures, points_par_palier, plafond_points,
                 description, row["id"]),
                "commit"
            )
        else:
            self._exec(
                "INSERT INTO configuration_discipline "
                "(tranche_heures, points_par_palier, plafond_points, description) "
                "VALUES (%s, %s, %s, %s)",
                (tranche_heures, points_par_palier, plafond_points, description),
                "commit"
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # ABSENCES
    # ═══════════════════════════════════════════════════════════════════════════

    def add_absence(self, eleve_id: str, date_absence: str,
                    heure_debut: str, heure_fin: str,
                    trimestre: int, annee: str,
                    statut: str = "NON_JUSTIFIEE",
                    motif: str = "",
                    creneau_id: int | None = None,
                    saisie_par: str = "SECRETARIAT") -> int:
        """
        Ajoute une absence. Retourne l'id inséré.
        date_absence : 'YYYY-MM-DD'
        heure_debut / heure_fin : 'HH:MM'
        """
        return self._exec(
            "INSERT INTO absences "
            "(eleve_id, date_absence, heure_debut, heure_fin, "
            " statut, motif, trimestre, annee_scolaire, creneau_id, saisie_par) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (eleve_id, date_absence, heure_debut, heure_fin,
             statut, motif or None, trimestre, annee,
             creneau_id, saisie_par),
            "lastrowid"
        )

    def justifier_absence(self, absence_id: int, motif: str = "") -> None:
        """Marque une absence comme justifiée (annule la pénalité)."""
        self._exec(
            "UPDATE absences SET statut='JUSTIFIEE', motif=%s WHERE id=%s",
            (motif or None, absence_id),
            "commit"
        )

    def annuler_justification(self, absence_id: int) -> None:
        """Repasse une absence à NON_JUSTIFIEE."""
        self._exec(
            "UPDATE absences SET statut='NON_JUSTIFIEE' WHERE id=%s",
            (absence_id,),
            "commit"
        )

    def delete_absence(self, absence_id: int) -> None:
        """Supprime une absence."""
        self._exec(
            "DELETE FROM absences WHERE id=%s",
            (absence_id,),
            "commit"
        )

    def get_absences_eleve(self, eleve_id: str,
                           trimestre: int | None = None,
                           annee: str = ANNEE_DEFAUT) -> list[dict]:
        """Toutes les absences d'un élève, triées par date desc."""
        if trimestre:
            return self._exec(
                "SELECT * FROM absences "
                "WHERE eleve_id=%s AND trimestre=%s AND annee_scolaire=%s "
                "ORDER BY date_absence DESC, heure_debut",
                (eleve_id, trimestre, annee)
            )
        return self._exec(
            "SELECT * FROM absences WHERE eleve_id=%s AND annee_scolaire=%s "
            "ORDER BY date_absence DESC, heure_debut",
            (eleve_id, annee)
        )

    def get_absences_classe_date(self, classe_id: int,
                                  date_absence: str,
                                  annee: str = ANNEE_DEFAUT) -> list[dict]:
        """
        Absences d'une classe pour une date donnée.
        Jointure avec Inscriptions_eleve pour nom/prénom.
        """
        return self._exec(
            "SELECT a.*, ie.nom, ie.prenom, ie.matricule "
            "FROM absences a "
            "JOIN Inscriptions_eleve ie ON ie.id = a.eleve_id "
            "JOIN Scolarite_Affectation sa ON sa.eleve_id = a.eleve_id "
            "WHERE sa.classe_id=%s AND a.date_absence=%s "
            "  AND a.annee_scolaire=%s "
            "ORDER BY ie.nom, ie.prenom, a.heure_debut",
            (classe_id, date_absence, annee)
        )

    def get_nb_absences_classe(self, classe_id: int,
                                trimestre: int,
                                annee: str = ANNEE_DEFAUT) -> list[dict]:
        """
        Résumé des absences par élève pour une classe / trimestre.
        Retourne : eleve_id, nom, prenom, matricule,
                   total_heures, heures_nj, heures_j
        """
        return self._exec(
            "SELECT "
            "  ie.id AS eleve_id, ie.nom, ie.prenom, ie.matricule, "
            "  ROUND(SUM(TIME_TO_SEC(TIMEDIFF(a.heure_fin, a.heure_debut)))/3600, 2) "
            "      AS total_heures, "
            "  ROUND(SUM(CASE WHEN a.statut='NON_JUSTIFIEE' THEN "
            "      TIME_TO_SEC(TIMEDIFF(a.heure_fin, a.heure_debut)) ELSE 0 END)/3600, 2) "
            "      AS heures_nj, "
            "  ROUND(SUM(CASE WHEN a.statut='JUSTIFIEE' THEN "
            "      TIME_TO_SEC(TIMEDIFF(a.heure_fin, a.heure_debut)) ELSE 0 END)/3600, 2) "
            "      AS heures_j "
            "FROM absences a "
            "JOIN Inscriptions_eleve ie ON ie.id = a.eleve_id "
            "JOIN Scolarite_Affectation sa ON sa.eleve_id = a.eleve_id "
            "WHERE sa.classe_id=%s AND a.trimestre=%s AND a.annee_scolaire=%s "
            "GROUP BY ie.id, ie.nom, ie.prenom, ie.matricule "
            "ORDER BY heures_nj DESC",
            (classe_id, trimestre, annee)
        )

    def get_heures_nj(self, eleve_id: str,
                      trimestre: int,
                      annee: str = ANNEE_DEFAUT) -> Decimal:
        """
        Retourne le total d'heures d'absence NON JUSTIFIÉE d'un élève
        pour un trimestre donné (utilisé par calculer_penalite_absence).
        """
        row = self._exec(
            "SELECT ROUND("
            "  SUM(TIME_TO_SEC(TIMEDIFF(heure_fin, heure_debut)))/3600, 4"
            ") AS heures_nj "
            "FROM absences "
            "WHERE eleve_id=%s AND trimestre=%s AND annee_scolaire=%s "
            "  AND statut='NON_JUSTIFIEE'",
            (eleve_id, trimestre, annee),
            "one"
        )
        return _to_dec(row["heures_nj"]) if row and row["heures_nj"] else D0

    # ═══════════════════════════════════════════════════════════════════════════
    # CALCUL DE LA PÉNALITÉ D'ABSENCE
    # ═══════════════════════════════════════════════════════════════════════════

    def calculer_penalite_absence(self, eleve_id: str,
                                   trimestre: int,
                                   annee: str = ANNEE_DEFAUT) -> Decimal:
        """
        Calcule la pénalité à retrancher de la moyenne générale.

        Formule :
          paliers   = floor(heures_nj / tranche_heures)
          pénalité  = min(paliers × points_par_palier, plafond_points)

        Exemples avec config par défaut (5h → -0.5, plafond 5 pts) :
          9h NJ → 1 palier → -0.50
         11h NJ → 2 paliers → -1.00
         55h NJ → 11 paliers → plafonné à -5.00
        """
        cfg = self.get_config_discipline()
        if not cfg:
            return D0

        tranche   = _to_dec(cfg["tranche_heures"])
        pts_pal   = _to_dec(cfg["points_par_palier"])
        plafond   = _to_dec(cfg["plafond_points"])

        if tranche <= D0:
            return D0

        heures_nj = self.get_heures_nj(eleve_id, trimestre, annee)
        if heures_nj <= D0:
            return D0

        paliers   = int(heures_nj / tranche)
        penalite  = _to_dec(paliers) * pts_pal
        return min(penalite, plafond).quantize(Decimal("0.01"),
                                               rounding=ROUND_HALF_UP)

    def get_bulletin_avec_penalite(self, eleve_id: str,
                                    trimestre: int,
                                    notes_db,          # instance NotesDB
                                    annee: str = ANNEE_DEFAUT) -> dict:
        """
        Génère les données complètes du bulletin intégrant la pénalité.

        Retourne un dict :
          {
            "lignes"            : [...]  ← même format que NotesDB.get_bulletin_eleve
            "moyenne_pondérée"  : Decimal  ← vient du module Notes (non modifié)
            "pénalité"          : Decimal  ← vient du module Vie Scolaire
            "moyenne_conduite"  : Decimal  ← = moy_ponderée - pénalité (≥ 0)
            "heures_nj"         : Decimal  ← heures d'absence non justifiées
            "heures_j"          : Decimal  ← heures d'absence justifiées
            "config"            : dict     ← règle utilisée
          }

        Principe clé :
          On NE MODIFIE PAS les fonctions de calcul de NotesDB.
          On lit la moyenne pondérée telle quelle, puis on applique la pénalité
          pour obtenir la "Moyenne Définitive" affichée sur le bulletin.
        """
        lignes        = notes_db.get_bulletin_eleve(eleve_id, trimestre, annee)
        moy_ponderee  = notes_db.get_moyenne_generale(eleve_id, trimestre, annee)
        penalite      = self.calculer_penalite_absence(eleve_id, trimestre, annee)
        moy_definitive = max(D0, moy_ponderee - penalite).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Heures résumées pour affichage sur le bulletin
        heures_nj = self.get_heures_nj(eleve_id, trimestre, annee)
        row_j = self._exec(
            "SELECT ROUND("
            "  SUM(TIME_TO_SEC(TIMEDIFF(heure_fin, heure_debut)))/3600, 2"
            ") AS heures_j "
            "FROM absences "
            "WHERE eleve_id=%s AND trimestre=%s AND annee_scolaire=%s "
            "  AND statut='JUSTIFIEE'",
            (eleve_id, trimestre, annee),
            "one"
        )
        heures_j = _to_dec(row_j["heures_j"]) if row_j and row_j["heures_j"] else D0

        return {
            "lignes":           lignes,
            "moyenne_ponderee": moy_ponderee,
            "penalite":         penalite,
            "moyenne_definitive": moy_definitive,
            "heures_nj":        heures_nj,
            "heures_j":         heures_j,
            "config":           self.get_config_discipline(),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # EMPLOI DU TEMPS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_emploi_classe(self, classe_id: int,
                           annee: str = ANNEE_DEFAUT) -> list[dict]:
        """
        Retourne tous les créneaux de l'emploi du temps d'une classe.
        Joint avec Matiere et Professeur pour noms affichables.
        """
        return self._exec(
            "SELECT edt.id, edt.classe_id, edt.matiere_id, edt.professeur_id, "
            "       edt.jour, edt.heure_debut, edt.heure_fin, edt.salle, "
            "       m.nom_matiere, "
            "       CONCAT(COALESCE(p.nom,''), ' ', COALESCE(p.prenom,'')) AS prof_nom "
            "FROM emploi_du_temps edt "
            "JOIN Matiere m ON m.id_matiere = edt.matiere_id "
            "LEFT JOIN Professeur p ON p.id_professeur = edt.professeur_id "
            "WHERE edt.classe_id=%s AND edt.annee_scolaire=%s "
            "ORDER BY FIELD(edt.jour,'Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi'), "
            "         edt.heure_debut",
            (classe_id, annee)
        )

    def add_creneau(self, classe_id: int, matiere_id: int,
                    professeur_id: int | None,
                    jour: str, heure_debut: str, heure_fin: str,
                    salle: str = "",
                    annee: str = ANNEE_DEFAUT) -> int:
        """Ajoute un créneau à l'emploi du temps. Retourne l'id."""
        return self._exec(
            "INSERT INTO emploi_du_temps "
            "(classe_id, matiere_id, professeur_id, jour, heure_debut, heure_fin, "
            " salle, annee_scolaire) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (classe_id, matiere_id, professeur_id or None,
             jour, heure_debut, heure_fin, salle or None, annee),
            "lastrowid"
        )

    def update_creneau(self, creneau_id: int,
                        matiere_id: int, professeur_id: int | None,
                        jour: str, heure_debut: str, heure_fin: str,
                        salle: str = "") -> None:
        """Modifie un créneau existant."""
        self._exec(
            "UPDATE emploi_du_temps "
            "SET matiere_id=%s, professeur_id=%s, jour=%s, "
            "    heure_debut=%s, heure_fin=%s, salle=%s "
            "WHERE id=%s",
            (matiere_id, professeur_id or None, jour,
             heure_debut, heure_fin, salle or None, creneau_id),
            "commit"
        )

    def delete_creneau(self, creneau_id: int) -> None:
        """Supprime un créneau."""
        self._exec(
            "DELETE FROM emploi_du_temps WHERE id=%s",
            (creneau_id,),
            "commit"
        )

    def get_creneaux_par_jour(self, classe_id: int, jour: str,
                               annee: str = ANNEE_DEFAUT) -> list[dict]:
        """Créneaux d'un jour donné pour une classe (pour préfill des absences)."""
        return self._exec(
            "SELECT edt.id, edt.heure_debut, edt.heure_fin, "
            "       m.nom_matiere, "
            "       CONCAT(COALESCE(p.nom,''), ' ', COALESCE(p.prenom,'')) AS prof_nom "
            "FROM emploi_du_temps edt "
            "JOIN Matiere m ON m.id_matiere = edt.matiere_id "
            "LEFT JOIN Professeur p ON p.id_professeur = edt.professeur_id "
            "WHERE edt.classe_id=%s AND edt.jour=%s AND edt.annee_scolaire=%s "
            "ORDER BY edt.heure_debut",
            (classe_id, jour, annee)
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # POLLING — DÉTECTION DES NOUVELLES ABSENCES DEPUIS DJANGO (WEB)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_count_absences_since(self, since_dt: datetime.datetime,
                                  annee: str = ANNEE_DEFAUT) -> int:
        """
        Retourne le nombre d'absences ajoutées depuis `since_dt`.
        Utilisé par le polling de la secrétaire pour détecter les saisies web.
        """
        row = self._exec(
            "SELECT COUNT(*) AS c FROM absences "
            "WHERE date_saisie > %s AND annee_scolaire=%s",
            (since_dt, annee),
            "one"
        )
        return int(row["c"]) if row else 0

    def get_last_absence_ts(self, annee: str = ANNEE_DEFAUT) -> datetime.datetime | None:
        """Retourne le timestamp de la dernière absence enregistrée."""
        row = self._exec(
            "SELECT MAX(date_saisie) AS ts FROM absences WHERE annee_scolaire=%s",
            (annee,),
            "one"
        )
        return row["ts"] if row else None

    # ═══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_eleves_classe(self, classe_id: int) -> list[dict]:
        """Liste des élèves d'une classe (pour remplir la liste des absences)."""
        return self._exec(
            "SELECT ie.id, ie.matricule, ie.nom, ie.prenom "
            "FROM Inscriptions_eleve ie "
            "JOIN Scolarite_Affectation sa ON sa.eleve_id = ie.id "
            "WHERE sa.classe_id=%s "
            "ORDER BY ie.nom, ie.prenom",
            (classe_id,)
        )

    def get_classes(self) -> list[dict]:
        """Toutes les classes (id, nom_classe)."""
        return self._exec("SELECT id, nom_classe FROM Classes ORDER BY nom_classe")

    def get_matieres(self) -> list[dict]:
        """Toutes les matières (id_matiere, nom_matiere)."""
        return self._exec(
            "SELECT id_matiere, nom_matiere FROM Matiere ORDER BY nom_matiere"
        )

    def get_professeurs(self) -> list[dict]:
        """Tous les professeurs actifs."""
        return self._exec(
            "SELECT id_professeur, nom, prenom, specialite "
            "FROM Professeur ORDER BY nom, prenom"
        )