from posixpath import expanduser

from customtkinter import *
from utils.constant import *
from data.db_manager import DbManager
from tkinter import Menu, messagebox, ttk



class Repartitions(CTkFrame):
    def __init__(self,master,*args,**kwargs):
        super().__init__(master,*args,**kwargs)
        self.master =master
        self.Database =DbManager()
        self.configure(fg_color=BACKGROUND_LIGHT)



        ##########################################################
        self.menu_tree = Menu(self, tearoff=0)

        self.menu_tree.add_command(label="Voir détails", command="")
        self.menu_tree.add_command(label="Modifier", command="")
        self.menu_tree.add_command(label="Supprimer", command="")



        #frame1 pour voir tous la liste des elevs accpeter 
        #frame 2 bouton pour lancer la repartition et la synchronisation
        #frame 3:combox et treeview pour afficher la liste des eleves par classe selection par le combobox et button afficher la classe 


        #les variables
        self.niveau_var =StringVar()
        self.search_var =StringVar()
        self.typesearch_var =StringVar()
        self.nnbrClasse =IntVar()

        self.id_var =StringVar()
        self.matricule_var =StringVar()
        self.nom_var =StringVar()
        self.prenom_var =StringVar()
        self.date_naissance_var =StringVar()
        self.addresse_var =StringVar()
        self.classe_var =StringVar()
        self.classrel_var =StringVar()
    

        #partager les frame en 3  deux frame a gauche et un frame a droite et un autre en bas pour la liste des elevs par classe
        
        # --- 1. CONTENEUR DU HAUT (50% de la hauteur) ---
        frameHaut = CTkFrame(self, fg_color="transparent")
        frameHaut.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=(10, 5))

        # Configuration pour que les deux frames aient la même largeur
        frameHaut.grid_columnconfigure(0, weight=1, uniform="groupe1")
        frameHaut.grid_columnconfigure(1, weight=1, uniform="groupe1")
        frameHaut.grid_rowconfigure(0, weight=1)

        # Frame de gauche (dans frameHaut)
        frameAction = CTkFrame(
            frameHaut, 
            fg_color=BACKGROUND_LIGHT,
            border_width=1,
            border_color=PRIMARY_BLUE
        )
        frameAction.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        # Titre de la frame gauche
        lbl_atitre = CTkLabel(
            frameAction, 
            text="Affectation",
            font=FONT_TITLE,
            text_color=BACKGROUND_LIGHT,
            fg_color=PRIMARY_BLUE,
            anchor=CENTER,
            height=30
        )
        lbl_atitre.pack(fill=X, side=TOP)

        # Conteneur pour les éléments de la frame gauche avec padding
        content_frame = CTkFrame(frameAction, fg_color="transparent")
        content_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Première ligne : Niveau scolaire + bouton + entry
        ligne1 = CTkFrame(content_frame, fg_color="transparent")
        ligne1.pack(fill=X, pady=(5, 10))

        class_label = CTkLabel(
            ligne1,
            text="Niveau scolaire",
            font=FONT_TITLE,
            text_color=PRIMARY_BLUE
        )
        class_label.pack(side=LEFT, padx=(0, 10))

        self.class_combobox = CTkComboBox(
            ligne1,
            values=["6eme", "5eme", "4eme", "3eme"],
            variable=self.niveau_var,
            fg_color=FRAME_WHITE,
            text_color=PRIMARY_BLUE,
            font=FONT_NORMAL,
            width=120
        )
        self.class_combobox.pack(side=LEFT, padx=(0, 10))

        self.btn_affectation_multiple = CTkButton(
            ligne1,
            text="Affectation Multiple",
            font=FONT_NORMAL,
            fg_color=SECONDARY_BLUE,
            text_color=BACKGROUND_LIGHT,
            hover_color=PRIMARY_BLUE,
            command=self.executer_repartition_et_synchronisation,
            height=35
        )
        self.btn_affectation_multiple.pack(side=LEFT, padx=(0, 10))

        self.nbrClasse = CTkEntry(
            ligne1,
            placeholder_text="Nbr Cls",
            font=FONT_NORMAL,
            text_color=PRIMARY_BLUE,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE,
            width=80,
            textvariable=self.nnbrClasse
        )
        self.nbrClasse.pack(side=LEFT)

        # Ligne de séparation
        separator = CTkFrame(content_frame, height=2, fg_color=PRIMARY_BLUE, corner_radius=0)
        separator.pack(fill=X, pady=10)

        # Grille pour les champs de saisie
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill=BOTH, expand=True)

        # Configurer les colonnes de la grille
        form_frame.grid_columnconfigure(0, weight=1, uniform="col")
        form_frame.grid_columnconfigure(1, weight=2, uniform="col")
        form_frame.grid_columnconfigure(2, weight=1, uniform="col")
        form_frame.grid_columnconfigure(3, weight=2, uniform="col")

        # Ligne 2 : Matricule et Nom
        lbl_matricule = CTkLabel(
            form_frame,
            text="Matricule:",
            font=FONT_TITLE,
            text_color=PRIMARY_BLUE
        )
        lbl_matricule.grid(row=0, column=0, padx=5, pady=5, sticky=W)

        self.matricule_entry = CTkEntry(
            form_frame,
            placeholder_text="Matricule",
            font=FONT_NORMAL,
            text_color=PRIMARY_BLUE,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE,
            textvariable=self.matricule_var
        )
        self.matricule_entry.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        lbl_nom = CTkLabel(
            form_frame,
            text="Nom:",
            font=FONT_TITLE,
            text_color=PRIMARY_BLUE
        )
        lbl_nom.grid(row=0, column=2, padx=5, pady=5, sticky=W)

        self.nom_entry = CTkEntry(
            form_frame,
            placeholder_text="Nom de l'élève",
            font=FONT_NORMAL,
            text_color=PRIMARY_BLUE,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE,
            textvariable=self.nom_var
        )
        self.nom_entry.grid(row=0, column=3, padx=5, pady=5, sticky=EW)

        # Ligne 3 : Prénom et Date Naissance
        lbl_prenom = CTkLabel(
            form_frame,
            text="Prénom:",
            font=FONT_TITLE,
            text_color=PRIMARY_BLUE
        )
        lbl_prenom.grid(row=1, column=0, padx=5, pady=5, sticky=W)

        self.prenom_entry = CTkEntry(
            form_frame,
            placeholder_text="Prénom de l'élève",
            font=FONT_NORMAL,
            text_color=PRIMARY_BLUE,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE,
            textvariable=self.prenom_var
        )
        self.prenom_entry.grid(row=1, column=1, padx=5, pady=5, sticky=EW)

        lbl_date_naissance = CTkLabel(
            form_frame,
            text="Date Naiss:",
            font=FONT_TITLE,
            text_color=PRIMARY_BLUE
        )
        lbl_date_naissance.grid(row=1, column=2, padx=5, pady=5, sticky=W)

        self.date_naissance_entry = CTkEntry(
            form_frame,
            placeholder_text="JJ/MM/AAAA",
            font=FONT_NORMAL,
            text_color=PRIMARY_BLUE,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE,
            textvariable=self.date_naissance_var
        )
        self.date_naissance_entry.grid(row=1, column=3, padx=5, pady=5, sticky=EW)

        # Ligne 4 : Adresse et Classe
        lbl_addresse = CTkLabel(
            form_frame,
            text="Adresse:",
            font=FONT_TITLE,
            text_color=PRIMARY_BLUE
        )
        lbl_addresse.grid(row=2, column=0, padx=5, pady=5, sticky=W)

        self.addresse_entry = CTkEntry(
            form_frame,
            placeholder_text="Adresse",
            font=FONT_NORMAL,
            text_color=PRIMARY_BLUE,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE,
            textvariable=self.addresse_var
        )
        self.addresse_entry.grid(row=2, column=1, padx=5, pady=5, sticky=EW)

        lbl_classe = CTkLabel(
            form_frame,
            text="Classe:",
            font=FONT_TITLE,
            text_color=PRIMARY_BLUE
        )
        lbl_classe.grid(row=2, column=2, padx=5, pady=5, sticky=W)

        self.classe_entry = CTkEntry(
            form_frame,
            placeholder_text="Classe",
            font=FONT_NORMAL,
            text_color=PRIMARY_BLUE,
            fg_color=FRAME_WHITE,
            border_color=PRIMARY_BLUE,
            textvariable=self.classe_var
            
        )
        self.classe_entry.grid(row=2, column=3, padx=5, pady=5, sticky=EW)

        # Ligne des boutons
        buttons_frame = CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill=X, pady=(20, 5))

        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        self.btn_affecter_unique = CTkButton(
            buttons_frame,
            text="Affectation Unique",
            font=FONT_NORMAL,
            fg_color=PRIMARY_BLUE,
            text_color=BACKGROUND_LIGHT,
            hover_color=SECONDARY_BLUE,
            command=self.affectation_unique,
            height=40,
            corner_radius=8
        )
        self.btn_affecter_unique.grid(row=0, column=0, padx=5, pady=5, sticky=EW)

        self.btn_reinitialiser = CTkButton(
            buttons_frame,
            text="Réinitialiser",
            font=FONT_NORMAL,
            fg_color=INFO_GRAY,
            text_color=BACKGROUND_LIGHT,
            hover_color="red",
            command=self.reinitialiser_champs,
            height=40,
            corner_radius=8
        )
        self.btn_reinitialiser.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        # Frame de droite (dans frameHaut)
        frameListeAccepted = CTkFrame(
            frameHaut, 
            fg_color=BACKGROUND_LIGHT,
            border_width=1,
            border_color=PRIMARY_BLUE
        )
        frameListeAccepted.grid(row=0, column=1, sticky="nsew", padx=(2, 0))

        lbl_titre = CTkLabel(
            frameListeAccepted,
            text="Liste des Élèves Acceptés",
            font=FONT_TITLE,
            text_color=BACKGROUND_LIGHT,
            fg_color=PRIMARY_BLUE,
            anchor=CENTER,
            height=30
        )
        lbl_titre.pack(fill=X, side=TOP)

        #liste par treeview
        
        #creation de style pour le treeview
        
        # Définir un style ttk 
        style = ttk.Style() 
        style.theme_use("default") 
        # Couleur des headings 
        style.configure("Treeview.Heading", background=PRIMARY_BLUE, foreground=BACKGROUND_LIGHT, font=("Arial", 12, "bold"))
        # Couleur des lignes du tableau
        style.configure("Treeview", background="white", foreground="black", fieldbackground="lightgrey", font=("Arial", 11))
        # Couleur quand une ligne est sélectionnée 
        style.map("Treeview", background=[("selected", "skyblue")], foreground=[("selected", "black")])

        # Conteneur pour le treeview avec padding
        tree_container = CTkFrame(frameListeAccepted, fg_color="transparent")
        tree_container.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.TableListe = ttk.Treeview(
            tree_container,
            columns=("id", "Matricule", "Nom", "Prenom", "Date Naissance", "Addresse", "Classe"),
            show="headings"
        )
        self.TableListe.heading("id", text='')
        self.TableListe.heading("Matricule", text='Matricule')
        self.TableListe.heading("Nom", text='Nom')
        self.TableListe.heading("Prenom", text='Prénom')
        self.TableListe.heading("Date Naissance", text='Date Naissance')
        self.TableListe.heading("Addresse", text='Adresse')
        self.TableListe.heading("Classe", text='Classe')

        self.TableListe.column("id", width=0, stretch=False)
        self.TableListe.column("Matricule", width=80, minwidth=80)
        self.TableListe.column("Nom", width=100, minwidth=80)
        self.TableListe.column("Prenom", width=100, minwidth=80)
        self.TableListe.column("Date Naissance", width=100, minwidth=80)
        self.TableListe.column("Addresse", width=150, minwidth=100)
        self.TableListe.column("Classe", width=80, minwidth=60)

        #Scrollbar pour le contrôle du tableau
        xscrollbar = ttk.Scrollbar(tree_container, orient=HORIZONTAL, command=self.TableListe.xview)
        yscrollbar = ttk.Scrollbar(tree_container, orient=VERTICAL, command=self.TableListe.yview)
        self.TableListe.configure(xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set)
        self.TableListe.bind("<ButtonRelease-1>",self.getDonnerAccepted)

        # Placement du treeview et des scrollbars
        self.TableListe.grid(row=0, column=0, sticky="nsew")
        xscrollbar.grid(row=1, column=0, sticky="ew")
        yscrollbar.grid(row=0, column=1, sticky="ns")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # --- 2. CONTENEUR DU BAS (50% de la hauteur) ---
        frame3 = CTkFrame(
            self, 
            fg_color=BACKGROUND_LIGHT,
            border_width=1,
            border_color=PRIMARY_BLUE
        )
        frame3.pack(side=BOTTOM, fill=BOTH, expand=True, padx=5, pady=(5, 10))

        lbl_ctitre = CTkLabel(
            frame3,
            text="Liste Par Classe Réelle",
            font=FONT_TITLE,
            text_color=BACKGROUND_LIGHT,
            fg_color=PRIMARY_BLUE,
            anchor=CENTER,
            height=30
        )
        lbl_ctitre.pack(fill=X, side=TOP)

        self.classReelCombox =CTkComboBox(frame3,values =["Selected"],fg_color =BACKGROUND_LIGHT,
                                          text_color=PRIMARY_BLUE,font =FONT_NORMAL,
                                          command =self.afficherClasse)
        self.classReelCombox.pack(fill =X,side =LEFT,anchor =N)
    
        # self.classReelCombox.bind("<ButtonRelease-1>",self.afficherClasse)
             #afficher la liste des classe reele
        self.classReelCombox.configure(values=self.Database.getClasseReel())
        

        # Conteneur pour le treeview du bas
        tree_container2 = CTkFrame(frame3, fg_color="transparent")
        tree_container2.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Style pour le deuxième treeview (optionnel, si vous voulez différencier)
        style2 = ttk.Style()
        style2.theme_use("default")
        style2.configure("Treeview.Heading", background=PRIMARY_BLUE, foreground=BACKGROUND_LIGHT, font=("Arial", 12, "bold"))
        style2.configure("Treeview", background="white", foreground="black", fieldbackground="lightgrey", font=("Arial", 11))
        style2.map("Treeview", background=[("selected", "skyblue")], foreground=[("selected", "black")])

        self.TableListeClasse = ttk.Treeview(
            tree_container2,
            columns=("id", "Matricule", "Nom", "Prenom", "Date Naissance", "Addresse", "Classe Reel"),
            show="headings"
        )
        self.TableListeClasse.heading("id", text='')
        self.TableListeClasse.heading("Matricule", text='Matricule')
        self.TableListeClasse.heading("Nom", text='Nom')
        self.TableListeClasse.heading("Prenom", text='Prénom')
        self.TableListeClasse.heading("Date Naissance", text='Date Naissance')
        self.TableListeClasse.heading("Addresse", text='Adresse')
        self.TableListeClasse.heading("Classe Reel", text='Classe Réelle')

        self.TableListeClasse.column("id", width=0, stretch=False)
        self.TableListeClasse.column("Matricule", width=80, minwidth=80)
        self.TableListeClasse.column("Nom", width=100, minwidth=80)
        self.TableListeClasse.column("Prenom", width=100, minwidth=80)
        self.TableListeClasse.column("Date Naissance", width=100, minwidth=80)
        self.TableListeClasse.column("Addresse", width=150, minwidth=100)
        self.TableListeClasse.column("Classe Reel", width=100, minwidth=80)

        #Scrollbar pour le contrôle du tableau
        xscrollbarc = ttk.Scrollbar(tree_container2, orient=HORIZONTAL, command=self.TableListeClasse.xview)
        yscrollbarc = ttk.Scrollbar(tree_container2, orient=VERTICAL, command=self.TableListeClasse.yview)
        self.TableListeClasse.configure(xscrollcommand=xscrollbarc.set, yscrollcommand=yscrollbarc.set)

        self.TableListeClasse.bind("<Button-3>", self.afficher_menu)


        # Placement du treeview et des scrollbars
        self.TableListeClasse.grid(row=0, column=0, sticky="nsew")
        xscrollbarc.grid(row=1, column=0, sticky="ew")
        yscrollbarc.grid(row=0, column=1, sticky="ns")

        tree_container2.grid_rowconfigure(0, weight=1)
        tree_container2.grid_columnconfigure(0, weight=1)

        self.getAccepted()

    
    def getAccepted(self):
        try:
            if self.Database.connection:
                data=self.Database.GetEleveAccepted()
                if data:
                    for row in data:
                        self.TableListe.delete(*self.TableListe.get_children())
                        self.TableListe.insert("",END,values=row)
                        print(row)
                else:
                    self.TableListe.insert("",END,values=[])
                    
        except Exception as e:
            messagebox.showerror("Erreur",f"Erreur de connection {e}")
    
    def executer_repartition_et_synchronisation(self):
        """Algorithme combiné : Répartit A->Z et crée les liens officiels"""
        # try:
        niveau = self.niveau_var.get().upper()
        nb = int(self.nnbrClasse.get())
        lettres = ["A", "B", "C", "D", "E", "F"][:nb]
        annee = "2025-2026"
            
        cursor = self.Database.connection.cursor()

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
                # Calcul de la classe (Round-robin)
            lettre = lettres[count % nb]
            nom_classe = f"{niveau} {lettre}"

                # 2. On s'assure que la classe existe dans 'Classes'
            cursor.execute("INSERT  INTO Classes (nom_classe) VALUES (%s) ", (nom_classe,))
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

        self.Database.connection.commit()
        self.getAccepted()
        messagebox.showinfo("Succès", f"Répartition terminée : {count} élèves affectés officiellement.")

    # except Exception as e:
    #     print(e)
    #     messagebox.showerror("Erreur", f"Détails : {e}")

    
    def getDonnerAccepted(self,ev):
        selected =self.TableListe.focus()
        try:
            values =self.TableListe.item(selected,'values')

            self.id_var.set(values[0])
            self.matricule_var.set(values[1])
            self.nom_var.set(values[2])
            self.prenom_var.set(values[3])
            self.date_naissance_var.set(str(values[4]))
            self.addresse_var.set(values[5])
            self.classe_var.set(values[6])
        except IndexError:
            pass
    
    def afficherClasse(self,value):
        """Fonction qui va afficher les eleves 

        Args:
           
        """

        try:
            if self.Database.connection:
                 #recuperer la liste des classe reel pour le combox

                classe_reel =self.classReelCombox.get()
                print(f"Classe réelle sélectionnée e : {classe_reel}")  # Debug: afficher la classe réelle sélectionnée
                data=self.Database.GetEleveByClasse(classe_reel)
                if data:
                    for row in data:
                        self.TableListeClasse.delete(*self.TableListeClasse.get_children())
                        self.TableListeClasse.insert("",END,values=row)
                        print(row)
                else:
                    self.TableListeClasse.insert("",END,values=[])
                    
        except Exception as e:
            messagebox.showerror("Erreur",f"Erreur de connection {e}")


    

    def afficher_menu(self, event):

        item = self.TableListeClasse.identify_row(event.y)

        if item:
            self.TableListeClasse.selection_set(item)

            self.selected_item = self.TableListeClasse.item(item, "values")

            self.menu_tree.tk_popup(event.x_root, event.y_root)

    def voir_details(self):

        print("Détails :", self.selected_item)


    def modifier_eleve(self):

        print("Modifier :", self.selected_item)


    def supprimer_eleve(self):

        print("Supprimer :", self.selected_item)

    # ===================== METHODES POUR LES BOUTONS =====================

   
    
    def affectation_unique(self):
        """Methode pour l'affectation unique d'un eleve a une classe"""
        matricule = self.matricule_entry.get()
        nom = self.nom_entry.get()
        prenom = self.prenom_entry.get()
        date_naissance = self.date_naissance_entry.get()
        addresse = self.addresse_entry.get()
        classe = self.classe_entry.get()
        
        print(f"Affectation Unique - Matricule: {matricule}, Nom: {nom}, Prenom: {prenom}")
        print(f"Date Naissance: {date_naissance}, Addresse: {addresse}, Classe: {classe}")
        # Implementer la logique d'affectation unique ici
    
    def reinitialiser_champs(self):
        """Reinitialise tous les champs d'entree"""
        self.matricule_entry.delete(0, END)
        self.nom_entry.delete(0, END)
        self.prenom_entry.delete(0, END)
        self.date_naissance_entry.delete(0, END)
        self.addresse_entry.delete(0, END)
        self.classe_entry.delete(0, END)
        self.nbrClasse.delete(0, END)
        self.class_combobox.set("")