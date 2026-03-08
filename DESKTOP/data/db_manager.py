from ast import Return
from email import message
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
    db =sqlite3.connect(r"WEB\db.sqlite3")
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

    def AcceptedInscription(self,matricule:str,id:str):
        """Foncction qui sera apeler pour accepter l'inscription d'un eleve
        Args:
            matricule (str): Le numero matricule donner lors de l'inscription
            id (str): l'identifiant
        
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE Inscriptions_eleve SET statut ='ACCEPTE' WHERE matricule = ?",(matricule,))
            self.connection.commit()
            #valider aussi les documents
            cursor.execute("UPDATE Inscriptions_documenteleve SET est_valide = TRUE WHERE id = ?",{id})
            messagebox.showinfo("Succès",f"Inscription de l'eleve {matricule} a été accepté")
        except Exception as e:
            messagebox.showerror("Errreur",f"Erreur de {e}")

    
    def GetDocuments(self,id:str):
        """Fonction qui retourne le lien vers les differents documents

        Args:
            matricule (str): matricule a l'inscription 
            id (str): l'identifiant unique 
        """
        try:
            if self.connection:
                cursor =self.connection.cursor()
                cursor.execute("SELECT acte_naissance,diplome,last_bulletin from Inscriptions_documenteleve where eleve_id =?",(id,))
                row =cursor.fetchone()
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
    
