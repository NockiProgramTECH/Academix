"""
db_notes_manager.py  --  Academix · Module Notes v1
=====================================================
Couche données pour la gestion des évaluations, notes, moyennes et rangs.

Conventions :
  • Toutes les méthodes d'écriture font un rollback() sur exception.
  • Les méthodes de lecture retournent [] ou None (jamais d'exception visible).
  • La table source des élèves est `Inscriptions_eleve`.
  • On réutilise la table `Matiere` déjà présente (id_matiere / nom_matiere)
    plutôt que de créer une table `matieres` en doublon.
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


class NotesDB:
    """
    Instancié avec la connexion MySQL partagée (DbManager.connection).

    Usage depuis Acceuil :
        from data.db_notes_manager import NotesDB
        self.notes_db = NotesDB(self.Database.connection)
    """

    ANNEE_DEFAUT = "2025-2026"

    def __init__(self, db_connection):
        self.db = db_connection
        self._create_tables()

    # ═════════════════════════════════════════════════════════════════════════
    # UTILITAIRES INTERNES
    # ═════════════════════════════════════════════════════════════════════════

    def _cur(self):
        self.db.ping(reconnect=True, attempts=3, delay=1)
        return self.db.cursor(dictionary=True)

    def _exec(self, sql: str, params: tuple = (), fetch: str = "all") -> Any:
        cur = self._cur()
        cur.execute(sql, params)
        if fetch == "all":
            result = cur.fetchall()
        elif fetch == "one":
            result = cur.fetchone()
        elif fetch == "lastrowid":
            self.db.commit(); result = cur.lastrowid
        else:
            self.db.commit(); result = None
        cur.close()
        return result

    # ═════════════════════════════════════════════════════════════════════════
    # INITIALISATION DES TABLES
    # ═════════════════════════════════════════════════════════════════════════

    def _create_tables(self):
        """
        Crée les tables si elles n'existent pas, puis applique les migrations
        nécessaires sur les tables déjà existantes.

        Migration gérée ici :
          • evaluations.type  →  evaluations.type_eval
            (la première version du code utilisait le mot réservé SQL `type` ;
             MySQL l'accepte mais Python/connector le rejette en INSERT nommé.
             On renomme la colonne si elle existe encore sous son ancien nom.)
        """
        statements = [
            # Liaison Matière <-> Classe
            """CREATE TABLE IF NOT EXISTS classe_matiere (
                classe_id   INT NOT NULL,
                matiere_id  INT NOT NULL,
                PRIMARY KEY (classe_id, matiere_id),
                FOREIGN KEY (classe_id)  REFERENCES Classes(id),
                FOREIGN KEY (matiere_id) REFERENCES Matiere(id_matiere)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            # Évaluations — créée avec type_eval dès le départ
            """CREATE TABLE IF NOT EXISTS evaluations (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                titre          VARCHAR(100) NOT NULL,
                type_eval      ENUM('Interrogation','Devoir','Examen') DEFAULT 'Devoir',
                trimestre      INT NOT NULL,
                date_eval      DATE NOT NULL,
                matiere_id     INT NOT NULL,
                classe_id      INT NOT NULL,
                annee_scolaire VARCHAR(20) NOT NULL,
                verrouille     TINYINT(1) DEFAULT 0,
                FOREIGN KEY (matiere_id) REFERENCES Matiere(id_matiere),
                FOREIGN KEY (classe_id)  REFERENCES Classes(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            # Notes
            """CREATE TABLE IF NOT EXISTS notes (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                evaluation_id INT NOT NULL,
                eleve_id      VARCHAR(60) NOT NULL,
                note          DECIMAL(5,2) NOT NULL,
                appreciation  VARCHAR(255),
                saisi_par     VARCHAR(50) DEFAULT 'SECRETARIAT',
                date_saisie   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE,
                FOREIGN KEY (eleve_id)      REFERENCES Inscriptions_eleve(id),
                UNIQUE KEY uq_note (evaluation_id, eleve_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        ]
        cur = self._cur()
        for sql in statements:
            try:
                cur.execute(sql)
            except Exception as e:
                print(f"[NotesDB._create_tables] {e}")
        self.db.commit()

        # ── MIGRATION : renommer `type` → `type_eval` si besoin ──────────────
        # On interroge INFORMATION_SCHEMA pour savoir quelle colonne existe.
        # Si `type` existe  → ALTER TABLE CHANGE
        # Si `type_eval` existe déjà → rien à faire
        try:
            cur.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'evaluations'
                  AND COLUMN_NAME IN ('type', 'type_eval')
            """)
            cols = {row[0] if isinstance(row, tuple) else row["COLUMN_NAME"]
                    for row in cur.fetchall()}

            if "type" in cols and "type_eval" not in cols:
                print("[NotesDB] Migration : renommage evaluations.type → type_eval")
                cur.execute("""
                    ALTER TABLE evaluations
                    CHANGE `type` `type_eval`
                    ENUM('Interrogation','Devoir','Examen') DEFAULT 'Devoir'
                """)
                self.db.commit()
                print("[NotesDB] Migration terminée.")
            elif "type_eval" in cols:
                pass  # déjà à jour, rien à faire
            else:
                # Colonne absente des deux noms → ajouter type_eval
                print("[NotesDB] Migration : ajout colonne type_eval manquante")
                cur.execute("""
                    ALTER TABLE evaluations
                    ADD COLUMN `type_eval`
                    ENUM('Interrogation','Devoir','Examen') DEFAULT 'Devoir'
                    AFTER titre
                """)
                self.db.commit()
        except Exception as e:
            print(f"[NotesDB._create_tables migration] {e}")

        cur.close()

    # ═════════════════════════════════════════════════════════════════════════
    # MATIÈRES
    # ═════════════════════════════════════════════════════════════════════════

    def get_matieres(self) -> list[dict]:
        """Toutes les matières avec coefficient."""
        return self._exec(
            "SELECT id_matiere AS id, nom_matiere AS nom, coefficient "
            "FROM Matiere ORDER BY nom_matiere"
        )

    def get_matieres_classe(self, classe_id: int) -> list[dict]:
        """Matières assignées à une classe. Repli sur toutes les matières si vide."""
        rows = self._exec(
            "SELECT m.id_matiere AS id, m.nom_matiere AS nom, m.coefficient "
            "FROM Matiere m "
            "JOIN classe_matiere cm ON cm.matiere_id = m.id_matiere "
            "WHERE cm.classe_id = %s ORDER BY m.nom_matiere",
            (classe_id,)
        )
        return rows if rows else self.get_matieres()

    def assigner_matiere_classe(self, classe_id: int, matiere_id: int):
        self._exec(
            "INSERT IGNORE INTO classe_matiere (classe_id, matiere_id) VALUES (%s, %s)",
            (classe_id, matiere_id), "commit"
        )

    def retirer_matiere_classe(self, classe_id: int, matiere_id: int):
        self._exec(
            "DELETE FROM classe_matiere WHERE classe_id=%s AND matiere_id=%s",
            (classe_id, matiere_id), "commit"
        )

    # ═════════════════════════════════════════════════════════════════════════
    # CLASSES (lecture seule)
    # ═════════════════════════════════════════════════════════════════════════

    def get_classes(self) -> list[dict]:
        return self._exec("SELECT id, nom_classe FROM Classes ORDER BY nom_classe")

    def get_classe_id(self, nom_classe: str) -> int | None:
        r = self._exec(
            "SELECT id FROM Classes WHERE nom_classe=%s", (nom_classe,), "one"
        )
        return r["id"] if r else None

    # ═════════════════════════════════════════════════════════════════════════
    # ÉLÈVES (lecture seule)
    # ═════════════════════════════════════════════════════════════════════════

    def get_eleves_classe(self, classe_id: int) -> list[dict]:
        """Élèves ACCEPTED d'une classe, triés alphabétiquement."""
        return self._exec(
            "SELECT ie.id, ie.matricule, ie.nom, ie.prenom "
            "FROM Inscriptions_eleve ie "
            "JOIN Scolarite_Affectation sa ON sa.eleve_id = ie.id "
            "WHERE sa.classe_id = %s AND ie.statut = 'ACCEPTED' "
            "ORDER BY ie.nom, ie.prenom",
            (classe_id,)
        )

    # ═════════════════════════════════════════════════════════════════════════
    # ÉVALUATIONS
    # ═════════════════════════════════════════════════════════════════════════

    def get_evaluations(self, classe_id: int, matiere_id: int,
                        trimestre: int, annee: str = ANNEE_DEFAUT) -> list[dict]:
        return self._exec(
            "SELECT * FROM evaluations "
            "WHERE classe_id=%s AND matiere_id=%s AND trimestre=%s AND annee_scolaire=%s "
            "ORDER BY date_eval",
            (classe_id, matiere_id, trimestre, annee)
        )

    def get_evaluation(self, eval_id: int) -> dict | None:
        return self._exec("SELECT * FROM evaluations WHERE id=%s", (eval_id,), "one")

    def create_evaluation(self, titre: str, type_eval: str, trimestre: int,
                          date_eval: str, matiere_id: int, classe_id: int,
                          annee: str = ANNEE_DEFAUT) -> int:
        return self._exec(
            "INSERT INTO evaluations(titre, type_eval, trimestre, date_eval, "
            "matiere_id, classe_id, annee_scolaire) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (titre, type_eval, trimestre, date_eval, matiere_id, classe_id, annee),
            "lastrowid"
        )

    def delete_evaluation(self, eval_id: int):
        """Supprime seulement si non verrouillée (cascade sur notes)."""
        self._exec(
            "DELETE FROM evaluations WHERE id=%s AND verrouille=0",
            (eval_id,), "commit"
        )

    def verrouiller_evaluation(self, eval_id: int):
        """Secrétaire valide : verrouille pour bloquer les modifs du prof web."""
        self._exec(
            "UPDATE evaluations SET verrouille=1 WHERE id=%s",
            (eval_id,), "commit"
        )

    def get_statut_evaluation(self, eval_id: int) -> str:
        """
        Retourne l'état visuel de l'évaluation :
          'vide'        -> aucune note saisie           (icône grise)
          'prof'        -> notes saisies par le prof    (icône bleue)
          'secretariat' -> notes saisies par secrétaire
          'valide'      -> verrouillé par secrétaire    (icône verte)
        """
        ev = self.get_evaluation(eval_id)
        if not ev:
            return "vide"
        if ev.get("verrouille"):
            return "valide"
        r = self._exec(
            "SELECT COUNT(*) AS c, "
            "SUM(CASE WHEN saisi_par != 'SECRETARIAT' THEN 1 ELSE 0 END) AS prof "
            "FROM notes WHERE evaluation_id=%s",
            (eval_id,), "one"
        )
        if not r or r["c"] == 0:
            return "vide"
        if r["prof"] and r["prof"] > 0:
            return "prof"
        return "secretariat"

    # ═════════════════════════════════════════════════════════════════════════
    # NOTES
    # ═════════════════════════════════════════════════════════════════════════

    def get_notes_evaluation(self, eval_id: int) -> list[dict]:
        """Notes + infos élève pour une évaluation donnée."""
        return self._exec(
            "SELECT n.id, n.eleve_id, n.note, n.appreciation, n.saisi_par, "
            "       ie.nom, ie.prenom, ie.matricule "
            "FROM notes n "
            "JOIN Inscriptions_eleve ie ON ie.id = n.eleve_id "
            "WHERE n.evaluation_id = %s ORDER BY ie.nom, ie.prenom",
            (eval_id,)
        )

    def upsert_note(self, eval_id: int, eleve_id: str, note: float,
                    appreciation: str = "", saisi_par: str = "SECRETARIAT"):
        """INSERT ou UPDATE note. Bloque si verrouillé et auteur != SECRETARIAT."""
        ev = self.get_evaluation(eval_id)
        if ev and ev.get("verrouille") and saisi_par != "SECRETARIAT":
            raise PermissionError(
                f"L'évaluation '{ev['titre']}' est verrouillée par le secrétariat."
            )
        note_d = str(_to_dec(note))
        self._exec(
            "INSERT INTO notes(evaluation_id, eleve_id, note, appreciation, saisi_par) "
            "VALUES(%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE note=%s, appreciation=%s, saisi_par=%s, "
            "date_saisie=CURRENT_TIMESTAMP",
            (eval_id, eleve_id, note_d, appreciation, saisi_par,
             note_d, appreciation, saisi_par),
            "commit"
        )

    def supprimer_note(self, eval_id: int, eleve_id: str):
        self._exec(
            "DELETE FROM notes WHERE evaluation_id=%s AND eleve_id=%s",
            (eval_id, eleve_id), "commit"
        )

    # ═════════════════════════════════════════════════════════════════════════
    # MOYENNES
    # ═════════════════════════════════════════════════════════════════════════

    def get_bulletin_eleve(self, eleve_id: str, trimestre: int,
                           annee: str = ANNEE_DEFAUT) -> list[dict]:
        """
        Une ligne par matière avec : nom, coefficient, moyenne pondérée, points.
        Pondération : Examen×3, Devoir×2, Interrogation×1.
        """
        rows = self._exec(
            "SELECT m.id_matiere AS matiere_id, m.nom_matiere AS nom, "
            "       m.coefficient, "
            "       SUM(n.note * CASE e.type_eval "
            "           WHEN 'Examen' THEN 3 WHEN 'Devoir' THEN 2 ELSE 1 END) "
            "           AS total_pondere, "
            "       SUM(CASE e.type_eval "
            "           WHEN 'Examen' THEN 3 WHEN 'Devoir' THEN 2 ELSE 1 END) "
            "           AS total_poids "
            "FROM notes n "
            "JOIN evaluations e ON e.id = n.evaluation_id "
            "JOIN Matiere     m ON m.id_matiere = e.matiere_id "
            "WHERE n.eleve_id=%s AND e.trimestre=%s AND e.annee_scolaire=%s "
            "GROUP BY m.id_matiere, m.nom_matiere, m.coefficient "
            "ORDER BY m.nom_matiere",
            (eleve_id, trimestre, annee)
        )
        result = []
        for r in rows:
            moy = (_to_dec(r["total_pondere"]) / _to_dec(r["total_poids"])
                   ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) \
                  if r["total_poids"] else D0
            coeff = int(r["coefficient"] or 1)
            result.append({
                "matiere_id":  r["matiere_id"],
                "nom":         r["nom"],
                "coefficient": coeff,
                "moyenne":     moy,
                "points":      (moy * coeff).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            })
        return result

    def get_moyenne_generale(self, eleve_id: str, trimestre: int,
                             annee: str = ANNEE_DEFAUT) -> Decimal:
        """Moyenne générale = Σ(moy × coeff) / Σ(coeff)."""
        bul = self.get_bulletin_eleve(eleve_id, trimestre, annee)
        if not bul:
            return D0
        total_pts   = sum(r["points"]      for r in bul)
        total_coeff = sum(r["coefficient"] for r in bul)
        if not total_coeff:
            return D0
        return (_to_dec(total_pts) / _to_dec(total_coeff)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # ═════════════════════════════════════════════════════════════════════════
    # CLASSEMENT — RANK() côté MySQL
    # ═════════════════════════════════════════════════════════════════════════

    def get_classement_classe(self, classe_id: int, trimestre: int,
                              annee: str = ANNEE_DEFAUT) -> list[dict]:
        """
        Classement complet d'une classe sur un trimestre.
        MySQL calcule les rangs via RANK() OVER → zéro loop Python.
        Retourne : eleve_id, nom, prenom, matricule, moy_gen, rang
        """
        return self._exec(
            "SELECT "
            "  sub.eleve_id, sub.nom, sub.prenom, sub.matricule, "
            "  sub.moy_gen, "
            "  RANK() OVER (ORDER BY sub.moy_gen DESC) AS rang "
            "FROM ( "
            "  SELECT "
            "    ie.id AS eleve_id, ie.nom, ie.prenom, ie.matricule, "
            "    ROUND( "
            "      SUM(n.note "
            "          * CASE e.type_eval WHEN 'Examen' THEN 3 WHEN 'Devoir' THEN 2 ELSE 1 END "
            "          * m.coefficient) "
            "      / NULLIF(SUM( "
            "          CASE e.type_eval WHEN 'Examen' THEN 3 WHEN 'Devoir' THEN 2 ELSE 1 END "
            "          * m.coefficient), 0), 2) AS moy_gen "
            "  FROM notes n "
            "  JOIN evaluations e ON e.id = n.evaluation_id "
            "  JOIN Matiere     m ON m.id_matiere = e.matiere_id "
            "  JOIN Inscriptions_eleve ie ON ie.id = n.eleve_id "
            "  WHERE e.classe_id=%s AND e.trimestre=%s AND e.annee_scolaire=%s "
            "  GROUP BY ie.id, ie.nom, ie.prenom, ie.matricule "
            ") sub "
            "ORDER BY rang",
            (classe_id, trimestre, annee)
        )

    # ═════════════════════════════════════════════════════════════════════════
    # STATISTIQUES PAR MATIÈRE
    # ═════════════════════════════════════════════════════════════════════════

    def get_stats_matiere(self, classe_id: int, matiere_id: int,
                          trimestre: int, annee: str = ANNEE_DEFAUT) -> dict:
        """Min / Max / Moyenne de la classe pour une matière × trimestre."""
        r = self._exec(
            "SELECT ROUND(AVG(n.note),2) AS moyenne_classe, "
            "       MIN(n.note) AS note_min, MAX(n.note) AS note_max, "
            "       COUNT(DISTINCT n.eleve_id) AS nb_notes "
            "FROM notes n "
            "JOIN evaluations e ON e.id = n.evaluation_id "
            "WHERE e.classe_id=%s AND e.matiere_id=%s "
            "  AND e.trimestre=%s AND e.annee_scolaire=%s",
            (classe_id, matiere_id, trimestre, annee), "one"
        )
        return {
            "moyenne_classe": _to_dec(r["moyenne_classe"]) if r else D0,
            "note_min":       _to_dec(r["note_min"])       if r else D0,
            "note_max":       _to_dec(r["note_max"])       if r else D0,
            "nb_notes":       r["nb_notes"]                if r else 0,
        }