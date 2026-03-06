from ast import Return
from email import message
from tkinter import messagebox

import mysql.connector 

import sqlite3

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

    def AcceptedInscription(self,matricule:str):
        """Foncction qui sera apeler pour accepter l'inscription d'un eleve
        Args:
            matricule (str): Le numero matricule donner lors de l'inscription
        
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE Inscriptions_eleve SET statut ='ACCEPTE' WHERE matricule = ?",(matricule,))
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
            

