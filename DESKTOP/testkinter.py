import tkinter as tk # Nécessaire pour le composant Menu

class AppScolaire(ctk.CTk):
    def __init__(self):
        # ... ton code existant ...
        
        # Création du menu (il est caché par défaut)
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", font=("Arial", 10))
        # On le remplira dynamiquement selon l'élève
        
    def setup_treeview(self):
        # ... configuration de ton treeview ...
        self.tree.bind("<Button-3>", self.afficher_menu_contextuel) # Clic droit (Windows/Linux)
        # Si tu préfères vraiment le clic gauche, utilise <Button-1>, 
        # mais attention cela peut gêner la sélection simple.

    def afficher_menu_contextuel(self, event):
        # Trouver la ligne sous la souris
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id) # Sélectionne la ligne
            self.selected_item = self.tree.item(item_id, 'values') # Récupère les données
            
            # On vide le menu précédent
            self.context_menu.delete(0, tk.END)
            
            # On ajoute des options dynamiques basées sur le niveau souhaité
            niveau = self.selected_item[2] # Supposons que le niveau est en 3ème colonne
            
            for lettre in ["A", "B", "C", "D"]:
                nom_classe = f"{niveau} {lettre}"
                self.context_menu.add_command(
                    label=f"Affecter en {nom_classe}", 
                    command=lambda c=nom_classe: self.affecter_individuel(c)
                )
            
            # Afficher le menu là où se trouve la souris
            self.context_menu.post(event.x_root, event.y_root)

    def affecter_individuel(self, classe_cible):
        id_eleve = self.selected_item[0] # L'ID de l'élève
        try:
            cursor = self.connection.cursor()
            
            # 1. Mise à jour de la classe réelle
            cursor.execute("UPDATE Inscriptions_eleve SET classe_reelle = ? WHERE id = ?", (classe_cible, id_eleve))
            
            # 2. Création de l'affectation officielle (comme dans l'algorithme groupé)
            cursor.execute("INSERT OR IGNORE INTO Classes (nom_classe) VALUES (?)", (classe_cible,))
            cursor.execute("SELECT id FROM Classes WHERE nom_classe = ?", (classe_cible,))
            id_classe = cursor.fetchone()[0]

            cursor.execute("""
                INSERT OR REPLACE INTO Scolarite_Affectation (eleve_id, classe_id, annee_scolaire)
                VALUES (?, ?, ?)
            """, (id_eleve, id_classe, "2025-2026"))

            self.connection.commit()
            messagebox.showinfo("Succès", f"L'élève a été affecté en {classe_cible}")
            self.refresh_treeview() # Pour mettre à jour l'affichage
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'affecter l'élève : {e}")