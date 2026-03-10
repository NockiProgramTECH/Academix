from ast import Return
from email import message
import time
from tkinter import messagebox

import mysql.connector 

import sqlite3

DB_CONFIG={
        'host':"localhost",
        'user':'root',
        "port":3306,
        'database':'Academix',
        'password':'root'
}
#pour sqlite3
def getConnection():
    db =mysql.connector.connect(**DB_CONFIG)
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
        self.connection =getConnection()
        self.SetAfecTable()
        self.createTablesProfesseurs()
        self.createTableMatiere()
        self.addMatiere()

        #fonction pour rafraichir si il ya de dossier en attente
    def refresh_pending_list(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id,matricule, nom,prenom,date_naissance,adresse,classe,photo FROM Inscriptions_eleve WHERE statut ='EN_ATTENTE'")
            rows = cursor.fetchall()
            # self.com['values'] = [f"{r[0]} - {r[1]}" for r in rows]
            # if not rows: self.com.set("Aucun dossier en attente")
            return rows
        except Exception as e:
            messagebox.showerror("Errreur",f"Erreur de {e}")
    
    def GetEleveAccepted(self):
        """
        Function pour recuperer tous les eleves dont le statut d'inscription est accepter
        Returns:
                List:returne une liste de tuple de tous les donner vrai
                None:si il ya rien
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""SELECT id,matricule, nom,prenom,date_naissance,adresse,classe FROM Inscriptions_eleve WHERE statut = 'ACCEPTED' AND classe_reelle is NULL """ )
                data =cursor.fetchall()
                print("Donner colercter",data)
                if data:
                    
                    return data
                else:
                    return None
        
        except Exception as e:
            messagebox.showerror("Erreur",f"Erreur de {e}")
    
     
    def SetAfecTable(self):
        """Methode pour l'affectation multiple - a implementer selon la logique metier"""
        # Implementer la logique d'affectation multiple ici
        """Prépare les tables de gestion si elles n'existent pas"""
        try:
            cursor = self.connection.cursor()
            # Table des étiquettes de classes
            cursor.execute("CREATE TABLE IF NOT EXISTS Classes (id INTEGER PRIMARY KEY AUTO_INCREMENT, nom_classe VARCHAR(20) UNIQUE)")
            # Table des liens officiels (Affectations)
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
            self.connection.commit()
        except Exception as e:
                messagebox.showerror("Erreur",f"Erreur de :{e}")

    def AcceptedInscription(self,matricule:str,eleve_id:str):
        """Foncction qui sera apeler pour accepter l'inscription d'un eleve
        Args:
            matricule (str): Le numero matricule donner lors de l'inscription
            eleve_id (str): L'identifiant unique de l'élève
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE Inscriptions_eleve SET statut ='ACCEPTED' WHERE matricule = %s",(matricule,))
            self.connection.commit()
            #valider aussi les documents
            cursor.execute("UPDATE Inscriptions_documenteleve SET est_valide = 1 WHERE eleve_id = %s",(eleve_id,))
            self.connection.commit()
            messagebox.showinfo("Succès",f"Inscription de l'eleve {matricule} a été accepté")
        except Exception as e:
            messagebox.showerror("Errreur",f"Erreur de {e}")

    
    def GetDocuments(self,id:str):
        """Fonction qui retourne le lien vers les differents documents

        Args:
            matricule (str): matricule a l'inscription 
            id (str): l'identifiant unique 
        """
        if self.connection:
            print("Connexion à la base de données réussie.")
            print(f"ID recherché : {id}")  # Debug: afficher l'ID recherché
        else:
            print("Échec de la connexion à la base de données.")
        try:
            if self.connection:
                cursor =self.connection.cursor()
                cursor.execute("SELECT acte_naissance,diplome,last_bulletin from Inscriptions_documenteleve where eleve_id = %s",(id,))
                row =cursor.fetchone()
                print("Row obtenue :", row)  # Debug: afficher la ligne obtenue
                return row if row else  None
            else:
                 return None
        except Exception as e :
              messagebox.showerror("Erreur",f"Erreur lors de l'obtention du fichier : {e}")

    
    def SearchEleveInscription(self,VarSeaerch:str,variable:str):
        """Fonction qui va faire la recherche dans la plage entry

        Args:
            Varsearch (str): valeur  type a rechercher dans la table           
            variable (str): valeur entrer dans pour la recherche
        
        Return:
            retourne liste de valeur quelle a trouver ou rien 
        """
        try:
            querie =f"SELECT id,matricule,nom,prenom,date_naissance,adresse,classe,photo from Inscriptions_eleve WHERE {str(VarSeaerch)}  LIKE '{str(variable)}%' AND statut ='EN_ATTENTE'"
            print(querie)
            if self.connection:
                    cursor =self.connection.cursor()
                    cursor.execute(querie )
                    row =cursor.fetchall()
                    return row if row else None
        
        except Exception as e:
            messagebox.showerror("Erreur",f"Erreur de connection a la base de donner: {e}")
    

    def getClasseReel(self):
        """Fonction pour selectionner le nom de tous les classe relles present

        Returns:
            List: retourne une liste de classe reel ou rien

        """

        try:
            if self.connection:
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT nom_classe FROM Classes")
                    rows = cursor.fetchall()
                    print("Classes réelles obtenues :", rows)  # Debug: afficher les classes réelles obtenues
                    return [row[0] for row in rows] if rows else []
            else:
                 return []
        except Exception as e :
              messagebox.showerror("Erreur",f"Erreur lors de l'obtention du fichier : {e}")
    

    def GetEleveByClasse(self,classrel:str):
        """Fonction pour selectionner tous les eleves d'une classe reel

        Args:
            classrel (str): le nom de la classe reel

        Returns:
            List: retourne une liste de tuple de tous les eleves d'une classe reel ou rien
        """
        try:
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
        except Exception as e :
              messagebox.showerror("Erreur",f"Erreur lors de l'obtention du fichier : {e}")
    
    
    def affectation_individuel(self, classe_cible,selected_items,func):
        id_eleve = selected_items[0] # L'ID de l'élève
        print("repartir unique",id_eleve)
        try:
            cursor = self.connection.cursor()
            
            # 1. Mise à jour de la classe réelle
            cursor.execute("UPDATE Inscriptions_eleve SET classe_reelle = %s WHERE id = %s", (classe_cible, id_eleve))
            
            # 2. Création de l'affectation officielle (comme dans l'algorithme groupé)
            cursor.execute("INSERT  IGNORE INTO Classes (nom_classe) VALUES (%s)", (classe_cible,))
            cursor.execute("SELECT id FROM Classes WHERE nom_classe = %s", (classe_cible,))
            id_classe = cursor.fetchone()[0]

            cursor.execute("""
            INSERT INTO Scolarite_Affectation (eleve_id, classe_id, annee_scolaire)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            classe_id = VALUES(classe_id),
            annee_scolaire = VALUES(annee_scolaire)
            """, (id_eleve, id_classe, "2025-2026"))  # corriger l'année apres exemple(anne passer - ann d'aujouduit)

            self.connection.commit()
            messagebox.showinfo("Succès", f"L'élève a été affecté en {classe_cible}")
            # self.refresh_treeview() # Pour mettre à jour l'affichage
            print('apple')
            func()
            print("fini")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'affecter l'élève : {e}")
    


    
    def affectation_global(self,niveau:str,nb:int):
        """
        Exécute la répartition automatique des élèves et synchronise avec la base de données.

        Cette méthode répartit les élèves acceptés non encore affectés dans des classes
        de A à Z selon le nombre de classes spécifié. Elle crée les classes si elles
        n'existent pas, affecte les élèves et met à jour les informations.

        Le processus suit un algorithme round-robin pour distribuer équitablement
        les élèves dans les classes.

        Raises:
            ValueError: Si le nombre de classes n'est pas un entier valide
        """
        """Algorithme combiné : Répartit A->Z et crée les liens officiels"""
        try:
           
            # Génère les lettres de classe selon le nombre spécifié (A, B, C, etc.)
            lettres = ["A", "B", "C", "D", "E", "F"][:nb]
            annee = f"{int(time.strftime('%Y') ) -1 }-{(time.strftime('%Y'))}"  # Exemple : "2024-2025"

            cursor = self.connection.cursor()

                # 1. Sélection des élèves validés non encore affectés officiellement
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
                return

            count = 0
            for id_eleve, nom, prenom in eleves:
                    # Calcul de la classe (Round-robin) - distribution équilibrée
                lettre = lettres[count % nb]
                nom_classe = f"{niveau} {lettre}"

                    # 2. On s'assure que la classe existe dans 'Classes'
                cursor.execute("INSERT IGNORE  INTO Classes (nom_classe) VALUES (%s) ", (nom_classe,))
                cursor.execute("SELECT id FROM Classes WHERE nom_classe = %s", (nom_classe,))
                id_classe = cursor.fetchone()[0]

                    # 3. On crée l'affectation officielle
                cursor.execute("""
                        INSERT INTO Scolarite_Affectation (eleve_id, classe_id, annee_scolaire)
                        VALUES (%s, %s, %s)
                    """, (id_eleve, id_classe, annee))
                    
                    # 4. On met à jour le champ informatif dans la table inscription
                cursor.execute("UPDATE Inscriptions_eleve SET classe_reelle = %s WHERE id = %s", (nom_classe, id_eleve))
                    
                count += 1

            self.connection.commit()
            print(f"Répartition terminée : {count} élèves affectés officiellement.")
            # func() #appelle de la fonction
            messagebox.showinfo("Succès", f"Répartition terminée : {count} élèves affectés officiellement.")
        except Exception as e:
            messagebox.showerror("Erreur",f"Erreur de connection a la base de donner: {e}")
    
        #creation des Tables pour les professeurs et les affectations

    def createTablesProfesseurs(self):
        """Fonction pour creer les tables des professeurs et des affectations"""
        try:
            cursor = self.connection.cursor()
            # Table des professeurs
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
            # Table des enseignements (affectations)
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
            self.connection.commit()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création des tables : {e}")
    

    #Creation de table matiere
    def createTableMatiere(self):
        """Fonction pour creer la table des matieres"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Matiere (
                    id_matiere INTEGER PRIMARY KEY AUTO_INCREMENT,
                    nom_matiere VARCHAR(100) UNIQUE,
                    coefficient INTEGER
                )
            """)
            self.connection.commit()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création de la table Matiere : {e}")


    def createProfesseur(self,matricule:str,nom:str,prenom:str,telephone:str,specialite:str,statut,email:str):
        """Fonction pour creer un professeur

        Args:
            matricule (str): le matricule du professeur
            nom (str): le nom du professeur
            prenom (str): le prenom du professeur
            telephone (str): le numero de telephone du professeur
            specialite (str): la specialite du professeur
            statut: le statut du professeur (ex: "ACTIF", "INACTIF")
            email (str): l'adresse email du professeur
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO Professeurs (matricule, nom, prenom, telephone, specialite, statut, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (matricule, nom, prenom, telephone, specialite, statut, email))
            self.connection.commit()
            messagebox.showinfo("Succès", f"Le professeur {nom} {prenom} a été créé avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création du professeur : {e}")


    def _load_professeurs(self):
        """Fonction pour charger tous les professeurs de la base de données"""
        try:
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
        if not self.connection:
            return

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
        if not self.connection:
            return

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
        if not self.connection:
            return

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT nom_matiere FROM Matiere ORDER BY nom_matiere")
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des matières : {e}")
            return []
        
    

    
    def _add_professeur(self,matricule:str,nom:str,prenom:str,telephone:str,specialite:str,statut:str,email:str):

        """
        Ajoute un nouveau professeur dans la base de données.
        L'email et le password sont optionnels (peuvent être NULL).
        Args:
            matricule (str): Le matricule unique du professeur (obligatoire)
            nom (str): Le nom du professeur (obligatoire)
            prenom (str): Le prénom du professeur (obligatoire)
            telephone (str): Le numéro de téléphone du professeur (optionnel)
            specialite (str): La spécialité du professeur (optionnel)
            statut (str): Le statut du professeur, ex: "ACTIF" ou "INACTIF" (obligatoire)
            email (str): L'adresse email du professeur (optionnel)

        """

        try:
            cursor = self.connection.cursor()

            # Vérifier si le matricule existe déjà
            cursor.execute("SELECT id_professeur FROM Professeur WHERE matricule = %s",
                          (matricule,))
            if cursor.fetchone():
                messagebox.showerror("Erreur", "Ce matricule existe déjà.")
                cursor.close()
                return

            # Insertion du nouveau professeur
            query = """
                INSERT INTO Professeur 
                (matricule, nom, prenom, telephone, specialite, statut, email, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                matricule,
                nom,
                prenom,
                telephone or None,
                specialite or None,
                statut,
                email or None,
                None  # password laissé NULL
            )
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()

            messagebox.showinfo("Succès", "Professeur ajouté avec succès!")

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ajouter le professeur: {e}")

    def _update_professeur(self,id:str,matricule:str,nom:str,prenom:str,telephone:str,specialite:str,statut:str,email:str):
        """
        Modifie les informations d'un professeur existant.
        """

        try:
            cursor = self.connection.cursor()

            query = """
                UPDATE Professeur 
                SET matricule = %s, nom = %s, prenom = %s, telephone = %s,
                    specialite = %s, statut = %s, email = %s
                WHERE id_professeur = %s
            """
            values = (
                matricule,
                nom,
                prenom,
                telephone or None,
                specialite or None,
                statut,
                email or None,
                id
            )

            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()

            messagebox.showinfo("Succès", "Professeur modifié avec succès!")
      

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier le professeur: {e}")

    def _delete_professeur(self,id:int,nom:str,prenom:str):
        """
        Supprime un professeur après confirmation.
        """

        try:
            cursor = self.connection.cursor()

            # Supprimer d'abord les affectations (contrainte FK)
            cursor.execute("DELETE FROM Enseignement WHERE id_professeur = %s", (id,))

            # Supprimer le professeur
            cursor.execute("DELETE FROM Professeur WHERE id_professeur = %s", (id,))

            self.connection.commit()
            cursor.close()

            messagebox.showinfo("Succès", "Professeur supprimé avec succès!")
    

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer le professeur: {e}")
    
    def addMatiere(self):
        #liste des matieres et coefficients
        matiere_liste ={
            "Mathématiques": 5,
            "Français": 4,
            "Anglais": 3,
            "Histoire-Géographie": 3,
            "Sciences (SVT)": 4,
            "Informatique": 2,
            "Philosophie": 2,
            'EPS':2,
            'Espagnole':2,
            'Allemand':4
            }
        if self.connection:
            try:
                cursor =self.connection.cursor()
                for matiere, coeff in matiere_liste.items():
                    cursor.execute("INSERT IGNORE INTO Matiere (nom_matiere, coefficient) VALUES (%s, %s)", (matiere, coeff))
                self.connection.commit()
            
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'ajout des matières : {e}")    
    

    

if __name__ == "__main__":  
    db_manager = DbManager()
    # Exemple d'utilisation
    # db_manager.createProfesseur("MAT123", "Doe", "John", "1234567890", "Mathématiques", "ACTIF", "