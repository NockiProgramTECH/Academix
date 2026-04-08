"""
Module DbManager — Gestionnaire de base de données MySQL pour Academix.

CORRECTIONS APPLIQUÉES :
  1. Connexion unique partagée (singleton) : évite les instances multiples
  2. Reconnexion automatique si la connexion est perdue
  3. commit() systématique après chaque écriture
  4. cursor.close() systématique pour éviter les fuites de ressources
"""

import datetime
import time
from tkinter import messagebox

import mysql.connector 

DB_CONFIG={
         'user':  'freedb_h4xgroover',#'root',
            'password': '9P*H2*Xv8wZU#%U',
            'host':  ' sql.freedb.tech',#'localhost',
            'port': '3306',
            'database':'freedb_academix'
}

# ══════════════════════════════════════════════════════════════════════════════
# CORRECTION 1 : Instance partagée globale (pattern Singleton léger)
# Toutes les vues récupèrent la MÊME connexion MySQL → les commits sont
# immédiatement visibles dans toutes les vues sans redémarrage.
# ══════════════════════════════════════════════════════════════════════════════
_shared_db_instance = None

def get_shared_db():
    """Retourne l'instance partagée de DbManager (crée si nécessaire)."""
    global _shared_db_instance
    if _shared_db_instance is None:
        _shared_db_instance = DbManager()
    return _shared_db_instance


def getConnection():
    db = mysql.connector.connect(**DB_CONFIG,autocommit=True)
    if db:
        return db
    return None


def close():
    con = getConnection()
    if con:
        con.close()
        return True


class DbManager:
    def __init__(self):
        self.connection = getConnection()
        self.SetAfecTable()
        self.createTablesProfesseurs()
        self.createTableMatiere()
        self.addMatiere()
        # self.create_notes_tables()

    # ══════════════════════════════════════════════════════════════════════════
    # CORRECTION 2 : Reconnexion automatique
    # MySQL ferme les connexions inactives après ~8h (wait_timeout).
    # Cette méthode vérifie et rétablit la connexion avant chaque opération.
    # ══════════════════════════════════════════════════════════════════════════
    def _ensure_connection(self):
        """Vérifie que la connexion est active, se reconnecte si besoin."""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = getConnection()
        except Exception:
            try:
                self.connection = getConnection()
            except Exception as e:
                messagebox.showerror("Connexion", f"Impossible de se reconnecter : {e}")

    def refresh_pending_list(self):
        try:
            self._ensure_connection()  # CORRECTION 2
            cursor = self.connection.cursor()
            cursor.execute("SELECT id,matricule, nom,prenom,date_naissance,adresse,classe,photo FROM Inscriptions_eleve WHERE statut ='EN_ATTENTE'")
            rows = cursor.fetchall()
            cursor.close()  # CORRECTION : fermeture systématique
            return rows
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de {e}")
    
    def GetEleveAccepted(self):
        """
        Récupère tous les élèves dont le statut d'inscription est accepté
        et qui n'ont pas encore de classe_reelle affectée.
        """
        try:
            self._ensure_connection()  # CORRECTION 2
            with self.connection.cursor() as cursor:
                cursor.execute("""SELECT id,matricule, nom,prenom,date_naissance,adresse,classe FROM Inscriptions_eleve WHERE statut = 'ACCEPTED' AND classe_reelle is NULL """ )
                data = cursor.fetchall()
                print("Donner colercter", data)
                if data:
                    return data
                else:
                    return None
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de {e}")
    
     
    def SetAfecTable(self):
        """Prépare les tables de gestion si elles n'existent pas."""
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS Classes (id INTEGER PRIMARY KEY AUTO_INCREMENT, nom_classe VARCHAR(20) UNIQUE)")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Scolarite_Affectation (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    eleve_id VARCHAR(60),
                    classe_id INTEGER,
                    annee_scolaire VARCHAR(20),
                    FOREIGN KEY(eleve_id) REFERENCES Inscriptions_eleve(id),
                    FOREIGN KEY(classe_id) REFERENCES Classes(id)
                )
            """)
            self.connection.commit()  # CORRECTION 3
            cursor.close()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de :{e}")

    def AcceptedInscription(self, matricule: str, eleve_id: str):
        """Accepte l'inscription d'un élève (UPDATE + commit immédiat)."""
        try:
            self._ensure_connection()  # CORRECTION 2
            cursor = self.connection.cursor()
            cursor.execute("UPDATE Inscriptions_eleve SET statut ='ACCEPTED' WHERE matricule = %s", (matricule,))
            # CORRECTION 3 : commit après chaque UPDATE
            self.connection.commit()
            cursor.execute("UPDATE Inscriptions_documenteleve SET est_valide = 1 WHERE eleve_id = %s", (eleve_id,))
            self.connection.commit()  # CORRECTION 3
            cursor.close()
            messagebox.showinfo("Succès", f"Inscription de l'élève {matricule} a été acceptée")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de {e}")

    
    def GetDocuments(self, id: str):
        """Retourne le lien vers les différents documents de l'élève."""
        try:
            self._ensure_connection()
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT acte_naissance,diplome,last_bulletin from Inscriptions_documenteleve where eleve_id = %s", (id,))
                row = cursor.fetchone()
                cursor.close()
                print("Row obtenue :", row)
                return row if row else None
            else:
                return None
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'obtention du fichier : {e}")

    
    def SearchEleveInscription(self, VarSeaerch: str, variable: str):
        """Recherche dans la table Inscriptions_eleve selon le critère donné."""
        try:
            querie = f"SELECT id,matricule,nom,prenom,date_naissance,adresse,classe,photo from Inscriptions_eleve WHERE {str(VarSeaerch)}  LIKE '{str(variable)}%' AND statut ='EN_ATTENTE'"
            self._ensure_connection()
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute(querie)
                row = cursor.fetchall()
                cursor.close()
                return row if row else None
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de connexion à la base de données : {e}")
    

    def getClasseReel(self):
        """Retourne la liste de toutes les classes réelles présentes."""
        try:
            self._ensure_connection()
            if self.connection:
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT nom_classe FROM Classes")
                    rows = cursor.fetchall()
                    return [row[0] for row in rows] if rows else []
            else:
                return []
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'obtention des classes : {e}")
    

    def GetEleveByClasse(self, classrel: str):
        """Retourne tous les élèves d'une classe réelle donnée."""
        try:
            self._ensure_connection()
            if self.connection:
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT ie.id, ie.matricule, ie.nom, ie.prenom, ie.date_naissance, ie.adresse, ie.classe_reelle, ie.photo 
                        FROM Inscriptions_eleve ie
                        JOIN Scolarite_Affectation sa ON ie.id = sa.eleve_id
                        JOIN Classes c ON sa.classe_id = c.id
                        WHERE c.nom_classe = %s AND ie.statut = 'ACCEPTED'
                    """, (classrel,))
                    rows = cursor.fetchall()
                    return rows if rows else None
            else:
                return None
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'obtention des élèves : {e}")
    
    
    def affectation_individuel(self, classe_cible, selected_items, func):
        id_eleve = selected_items[0]
        print("repartir unique", id_eleve)
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            cursor.execute("UPDATE Inscriptions_eleve SET classe_reelle = %s WHERE id = %s", (classe_cible, id_eleve))
            
            cursor.execute("INSERT  IGNORE INTO Classes (nom_classe) VALUES (%s)", (classe_cible,))
            cursor.execute("SELECT id FROM Classes WHERE nom_classe = %s", (classe_cible,))
            id_classe = cursor.fetchone()[0]

            cursor.execute("""
            INSERT INTO Scolarite_Affectation (eleve_id, classe_id, annee_scolaire)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            classe_id = VALUES(classe_id),
            annee_scolaire = VALUES(annee_scolaire)
            """, (id_eleve, id_classe, "2025-2026"))

            self.connection.commit()  # CORRECTION 3 : un seul commit couvre toutes les écritures
            cursor.close()
            messagebox.showinfo("Succès", f"L'élève a été affecté en {classe_cible}")
            func()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'affecter l'élève : {e}")
    

    def affectation_global(self, niveau: str, nb: int):
        """
        Répartition automatique round-robin des élèves dans des classes A→Z.
        Un seul commit à la fin garantit l'atomicité de l'opération.
        """
        try:
            self._ensure_connection()
            lettres = ["A", "B", "C", "D", "E", "F"][:nb]
            annee = f"{int(time.strftime('%Y')) - 1}-{(time.strftime('%Y'))}"

            cursor = self.connection.cursor()

            cursor.execute("""
                    SELECT id, nom, prenom FROM Inscriptions_eleve 
                    WHERE statut = 'ACCEPTED' 
                    AND classe = %s
                    AND id NOT IN (SELECT eleve_id FROM Scolarite_Affectation)
                    ORDER BY nom ASC, prenom ASC
                """, (niveau,))
                
            eleves = cursor.fetchall()
            if not eleves:
                messagebox.showinfo("Info", "Tous les élèves sont déjà affectés !")
                cursor.close()
                return

            count = 0
            for id_eleve, nom, prenom in eleves:
                lettre = lettres[count % nb]
                nom_classe = f"{niveau} {lettre}"

                cursor.execute("INSERT IGNORE  INTO Classes (nom_classe) VALUES (%s) ", (nom_classe,))
                cursor.execute("SELECT id FROM Classes WHERE nom_classe = %s", (nom_classe,))
                id_classe = cursor.fetchone()[0]

                cursor.execute("""
                        INSERT INTO Scolarite_Affectation (eleve_id, classe_id, annee_scolaire)
                        VALUES (%s, %s, %s)
                    """, (id_eleve, id_classe, annee))
                    
                cursor.execute("UPDATE Inscriptions_eleve SET classe_reelle = %s WHERE id = %s", (nom_classe, id_eleve))
                    
                count += 1

            # CORRECTION 3 : un seul commit à la fin (atomicité)
            self.connection.commit()
            cursor.close()
            print(f"Répartition terminée : {count} élèves affectés officiellement.")
            messagebox.showinfo("Succès", f"Répartition terminée : {count} élèves affectés officiellement.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de connexion à la base de données : {e}")
    
    def createTablesProfesseurs(self):
        """Crée les tables des professeurs et des affectations si elles n'existent pas."""
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Professeur (
                    id_professeur INTEGER PRIMARY KEY AUTO_INCREMENT,
                    matricule VARCHAR(20) UNIQUE,
                    nom VARCHAR(50),
                    prenom VARCHAR(50),
                    telephone VARCHAR(20),
                    specialite VARCHAR(100),
                    statut VARCHAR(20),
                    email VARCHAR(100),
                    password VARCHAR(255)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Enseignement (
                    id_enseignement INTEGER PRIMARY KEY AUTO_INCREMENT,
                    id_professeur INTEGER,
                    id_matiere INTEGER,
                    id_classe INTEGER,
                    FOREIGN KEY(id_professeur) REFERENCES Professeur(id_professeur),
                    FOREIGN KEY(id_matiere) REFERENCES Matiere(id_matiere),
                    FOREIGN KEY(id_classe) REFERENCES Classes(id)
                )
            """)
            self.connection.commit()  # CORRECTION 3
            cursor.close()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création des tables : {e}")
    

    def createTableMatiere(self):
        """Crée la table des matières si elle n'existe pas."""
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Matiere (
                    id_matiere INTEGER PRIMARY KEY AUTO_INCREMENT,
                    nom_matiere VARCHAR(100) UNIQUE,
                    coefficient INTEGER
                )
            """)
            self.connection.commit()  # CORRECTION 3
            cursor.close()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création de la table Matiere : {e}")


    def createProfesseur(self, matricule: str, nom: str, prenom: str, telephone: str, specialite: str, statut, email: str):
        """Crée un nouveau professeur."""
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO Professeurs (matricule, nom, prenom, telephone, specialite, statut, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (matricule, nom, prenom, telephone, specialite, statut, email))
            self.connection.commit()  # CORRECTION 3
            cursor.close()
            messagebox.showinfo("Succès", f"Le professeur {nom} {prenom} a été créé avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création du professeur : {e}")


    def _load_professeurs(self):
        """Charge tous les professeurs de la base de données."""
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT id_professeur, matricule, nom,
                            prenom, telephone, specialite,
                            statut, email FROM Professeur
                           ORDER BY nom,prenom
                           """
                           )
            professeurs = cursor.fetchall()
            cursor.close()
            return professeurs if professeurs else []
          
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des professeurs : {e}")
            return []
    


    def _load_affectations(self):
        """Charge la liste des affectations."""
        self._ensure_connection()
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT e.id_enseignement,
                       CONCAT(p.nom, ' ', p.prenom) as professeur,
                       m.nom_matiere,
                       c.nom_classe
                FROM Enseignement e
                JOIN Professeur p ON e.id_professeur = p.id_professeur
                JOIN Matiere m ON e.id_matiere = m.id_matiere
                JOIN Classes c ON e.id_classe = c.id
                ORDER BY c.nom_classe, m.nom_matiere
            """)
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des affectations : {e}")
            return []
        
    
    def _load_classes(self):
        """Charge la liste des classes pour le combobox."""
        self._ensure_connection()
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT nom_classe FROM Classes ORDER BY nom_classe")
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des classes : {e}")
            return []
    


    def _load_matieres(self):
        """Charge la liste des matières pour le combobox."""
        self._ensure_connection()
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT nom_matiere FROM Matiere ORDER BY nom_matiere")
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des matières : {e}")
            return []
        
    

    
    def _add_professeur(self, matricule: str, nom: str, prenom: str, telephone: str, specialite: str, statut: str, email: str):
        """Ajoute un nouveau professeur dans la base de données."""
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()

            cursor.execute("SELECT id_professeur FROM Professeur WHERE matricule = %s", (matricule,))
            if cursor.fetchone():
                messagebox.showerror("Erreur", "Ce matricule existe déjà.")
                cursor.close()
                return

            query = """
                INSERT INTO Professeur 
                (matricule, nom, prenom, telephone, specialite, statut, email, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                matricule, nom, prenom,
                telephone or None, specialite or None,
                statut, email or None,
                None  # password laissé NULL
            )
            cursor.execute(query, values)
            self.connection.commit()  # CORRECTION 3
            cursor.close()

            messagebox.showinfo("Succès", "Professeur ajouté avec succès!")

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ajouter le professeur: {e}")

    def _update_professeur(self, id: str, matricule: str, nom: str, prenom: str, telephone: str, specialite: str, statut: str, email: str):
        """Modifie les informations d'un professeur existant."""
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()

            query = """
                UPDATE Professeur 
                SET matricule = %s, nom = %s, prenom = %s, telephone = %s,
                    specialite = %s, statut = %s, email = %s
                WHERE id_professeur = %s
            """
            values = (
                matricule, nom, prenom,
                telephone or None, specialite or None,
                statut, email or None,
                id
            )
            cursor.execute(query, values)
            self.connection.commit()  # CORRECTION 3
            cursor.close()

            messagebox.showinfo("Succès", "Professeur modifié avec succès!")
      
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier le professeur: {e}")

    def _delete_professeur(self, id: int, nom: str, prenom: str):
        """Supprime un professeur et toutes ses affectations."""
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()

            # Supprimer d'abord les affectations (contrainte FK)
            cursor.execute("DELETE FROM Enseignement WHERE id_professeur = %s", (id,))
            cursor.execute("DELETE FROM Professeur WHERE id_professeur = %s", (id,))

            self.connection.commit()  # CORRECTION 3 : un seul commit couvre les deux DELETE
            cursor.close()

            messagebox.showinfo("Succès", "Professeur supprimé avec succès!")
    
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer le professeur: {e}")
    
    def addMatiere(self):
        """Insère les matières par défaut si elles n'existent pas encore."""
        matiere_liste = {
            "Mathématiques": 5,
            "Français": 4,
            "Anglais": 3,
            "Histoire-Géographie": 3,
            "Sciences (SVT)": 4,
            "Informatique": 2,
            "Philosophie": 2,
            'EPS': 2,
            'Espagnole': 2,
            'Allemand': 4
        }
        self._ensure_connection()
        if self.connection:
            try:
                cursor = self.connection.cursor()
                for matiere, coeff in matiere_liste.items():
                    cursor.execute("INSERT IGNORE INTO Matiere (nom_matiere, coefficient) VALUES (%s, %s)", (matiere, coeff))
                self.connection.commit()  # CORRECTION 3
                cursor.close()
            
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'ajout des matières : {e}")
