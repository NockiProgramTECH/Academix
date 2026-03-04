import sqlite3 


def getEleveNotActif():
    conn =sqlite3.connect("db.sqlite3")
    cursor =conn.cursor()
    cursor.execute("SELECT nom, prenom FROM Inscriptions_eleve WHERE statut = 'EN_ATTENTE' ")
    r =cursor.fetchall()
    for i in r:
        print(i)
    


if __name__ == "__main__":
    getEleveNotActif()
