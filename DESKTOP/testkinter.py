import sqlite3
from tkinter import *
from tkinter import ttk, messagebox

class Acceuil(Tk):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.geometry("600x600")
        self.title("Système de Gestion Scolaire - Répartition & Synchronisation")
        self.connection = sqlite3.connect(r"C:\Users\h4xgroover\Desktop\GESTION ECOLE\WEB\db.sqlite3")
        
        # Initialisation des tables système (le placard et les étiquettes)
        self.setup_system_tables()

        # --- Interface (Ton code existant) ---
        Label(self, text="Gestion des Inscriptions", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.com = ttk.Combobox(self, font=("Arial", 10), state="readonly")
        self.com.pack(pady=5)
        self.refresh_pending_list()

        Button(self, text='1. Valider le dossier', bg="#27ae60", fg="white", command=self.valider_eleve).pack(pady=5)

        # --- Zone de Répartition & Synchronisation ---
        Frame(self, height=2, bd=1, relief=SUNKEN).pack(fill=X, padx=10, pady=20)
        
        Label(self, text="Répartition & Affectation Officielle", font=("Arial", 12, "bold")).pack()
        
        Label(self, text="Niveau (ex: 6EME):").pack()
        self.entry_niveau = Entry(self)
        self.entry_niveau.insert(0, "6EME")
        self.entry_niveau.pack()

        Label(self, text="Nombre de divisions (A, B, C...):").pack()
        self.entry_nb_classes = Entry(self)
        self.entry_nb_classes.insert(0, "3")
        self.entry_nb_classes.pack()

        # LE BOUTON MAGIQUE
        Button(self, text='Lancer la Répartition et l\'Affectation', 
               bg="#2980b9", fg="white", font=("Arial", 10, "bold"),
               command=self.executer_repartition_et_synchronisation).pack(pady=20)

    def setup_system_tables(self):
        """Prépare les tables de gestion si elles n'existent pas"""
        cursor = self.connection.cursor()
        # Table des étiquettes de classes
        cursor.execute("CREATE TABLE IF NOT EXISTS Classes (id INTEGER PRIMARY KEY AUTOINCREMENT, nom_classe TEXT UNIQUE)")
        # Table des liens officiels (Affectations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Scolarite_Affectation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id TEXT,
                classe_id INTEGER,
                annee_scolaire TEXT,
                FOREIGN KEY(eleve_id) REFERENCES Inscriptions_eleve(id),
                FOREIGN KEY(classe_id) REFERENCES Classes(id)
            )
        """)
        self.connection.commit()

    def refresh_pending_list(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, nom FROM Inscriptions_eleve WHERE statut ='EN_ATTENTE'")
        rows = cursor.fetchall()
        self.com['values'] = [f"{r[0]} - {r[1]}" for r in rows]
        if not rows: self.com.set("Aucun dossier en attente")

    def valider_eleve(self):
        try:
            val = self.com.get().split(" - ")[0]
            cursor = self.connection.cursor()
            cursor.execute("UPDATE Inscriptions_eleve SET statut ='ACCEPTED' WHERE id =?", (val,))
            self.connection.commit()
            messagebox.showinfo("Succès", "Dossier Validé !")
            self.refresh_pending_list()
            self.com.set("")
        except: messagebox.showerror("Erreur", "Sélectionnez un élève")

    def executer_repartition_et_synchronisation(self):
        """Algorithme combiné : Répartit A->Z et crée les liens officiels"""
        try:
            niveau = self.entry_niveau.get().upper()
            nb = int(self.entry_nb_classes.get())
            lettres = ["A", "B", "C", "D", "E", "F"][:nb]
            annee = "2025-2026"
            
            cursor = self.connection.cursor()

            # 1. Sélection des élèves validés non encore affectés officiellement
            cursor.execute("""
                SELECT id, nom, prenom FROM Inscriptions_eleve 
                WHERE statut = 'ACCEPTED' 
                AND classe = ?
                AND id NOT IN (SELECT eleve_id FROM Scolarite_Affectation)
                ORDER BY nom ASC, prenom ASC
            """, (niveau,))
            
            eleves = cursor.fetchall()
            if not eleves:
                messagebox.showinfo("Info", "Tous les élèves sont déjà affectés !")
                return

            count = 0
            for id_eleve, nom, prenom in eleves:
                # Calcul de la classe (Round-robin)
                lettre = lettres[count % nb]
                nom_classe = f"{niveau} {lettre}"

                # 2. On s'assure que la classe existe dans 'Classes'
                cursor.execute("INSERT OR IGNORE INTO Classes (nom_classe) VALUES (?)", (nom_classe,))
                cursor.execute("SELECT id FROM Classes WHERE nom_classe = ?", (nom_classe,))
                id_classe = cursor.fetchone()[0]

                # 3. On crée l'affectation officielle
                cursor.execute("""
                    INSERT INTO Scolarite_Affectation (eleve_id, classe_id, annee_scolaire)
                    VALUES (?, ?, ?)
                """, (id_eleve, id_classe, annee))
                
                # 4. On met à jour le champ informatif dans la table inscription
                cursor.execute("UPDATE Inscriptions_eleve SET classe_reelle = ? WHERE id = ?", (nom_classe, id_eleve))
                
                count += 1

            self.connection.commit()
            messagebox.showinfo("Succès", f"Répartition terminée : {count} élèves affectés officiellement.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Détails : {e}")

if __name__ == "__main__":
    app = Acceuil()
    app.mainloop()