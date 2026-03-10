"""
Module pour la gestion des répartitions d'élèves dans l'application desktop de gestion scolaire.

Ce module contient la classe Repartitions qui fournit une interface graphique
pour affecter les élèves acceptés à des classes réelles, effectuer des répartitions
automatiques et gérer les listes d'élèves par classe.
"""

from posixpath import expanduser

from customtkinter import *
from utils.constant import *
from data.db_manager import DbManager
from tkinter import Menu, messagebox, ttk



class Repartitions(CTkFrame):
    """
    Classe principale pour l'interface de répartition des élèves.

    Cette classe hérite de CTkFrame et fournit une interface utilisateur pour :
    - Afficher la liste des élèves acceptés
    - Effectuer des affectations individuelles ou multiples
    - Répartir automatiquement les élèves dans des classes
    - Afficher les élèves par classe réelle

    Attributes:
        master: Le widget parent (fenêtre principale)
        Database: Instance du gestionnaire de base de données
        menu_tree: Menu contextuel pour les actions sur les élèves
        niveau_var: Variable pour le niveau scolaire sélectionné
        search_var: Variable pour la recherche
        typesearch_var: Variable pour le type de recherche
        nnbrClasse: Nombre de classes à créer
        id_var, matricule_var, etc.: Variables pour les champs de formulaire
        TableListe: Treeview pour la liste des élèves acceptés
        TableListeClasse: Treeview pour les élèves par classe
        classReelCombox: Combobox pour sélectionner la classe réelle
    """

    def __init__(self,master,*args,**kwargs):
        """
        Initialise l'interface de répartition.

        Args:
            master: Le widget parent
            *args: Arguments supplémentaires pour CTkFrame
            **kwargs: Arguments nommés supplémentaires pour CTkFrame
        """
        super().__init__(master,*args,**kwargs)
        self.master =master
        self.Database =DbManager()
        self.configure(fg_color=BACKGROUND_LIGHT)

        self._refresh_job = None  # ← AJOUTER 
    



        ##########################################################
        self.menu_treeC = Menu(self, tearoff=0)

        self.menu_treeC.add_command(label="Voir détails", command="")
        self.menu_treeC.add_command(label="Modifier", command="")
        self.menu_treeC.add_command(label="Supprimer", command=self.supprimer_eleve)

        self.menu_treeL = Menu(self, tearoff=0)
         
        # Création du menu (il est caché par défaut)
        # self.context_menu = Menu(self, tearoff=0, bg="#2b2b2b", fg="white", font=("Arial", 10))

        # On le remplira dynamiquement selon l'élève
      # Si tu préfères vraiment le clic gauche, utilise <Button-1>, 
        # mais attention cela peut gêner la sélection simple.

        # self.menu_treeL.add_command(label="Voir détails", command="")
        # self.menu_treeL.add_command(label="Modifier", command="")
        # self.menu_treeL.add_command(label="Supprimer", command="")



        # Structure des frames :
        # - Frame gauche (haut) : Formulaire d'affectation et boutons
        # - Frame droite (haut) : Liste des élèves acceptés
        # - Frame bas : Liste des élèves par classe réelle


        # Initialisation des variables Tkinter pour les champs de formulaire
        self.niveau_var = StringVar()  # Niveau scolaire sélectionné (6eme, 5eme, etc.)
        self.search_var = StringVar()  # Terme de recherche
        self.typesearch_var = StringVar()  # Type de recherche
        self.nnbrClasse = IntVar()  # Nombre de classes à créer lors de la répartition

        # Variables pour stocker les informations de l'élève sélectionné
        self.id_var = StringVar()  # ID unique de l'élève
        self.matricule_var = StringVar()  # Matricule de l'élève
        self.nom_var = StringVar()  # Nom de l'élève
        self.prenom_var = StringVar()  # Prénom de l'élève
        self.date_naissance_var = StringVar()  # Date de naissance
        self.addresse_var = StringVar()  # Adresse de l'élève
        self.classe_var = StringVar()  # Classe actuelle
        self.classrel_var = StringVar()  # Classe réelle affectée
    

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
            command=self.repartitionGlobal,
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
        self.TableListe.bind("<Button-3>", self.afficher_menu_contextuel) # Clic droit (Windows/Linux)
     
    

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

        self.TableListeClasse.bind("<Button-3>", self.afficher_menuC)


        # Placement du treeview et des scrollbars
        self.TableListeClasse.grid(row=0, column=0, sticky="nsew")
        xscrollbarc.grid(row=1, column=0, sticky="ew")
        yscrollbarc.grid(row=0, column=1, sticky="ns")

        tree_container2.grid_rowconfigure(0, weight=1)
        tree_container2.grid_columnconfigure(0, weight=1)
    
    def getAccepted(self):
        """
        Récupère et affiche la liste des élèves acceptés dans le Treeview.

        Cette méthode interroge la base de données pour obtenir tous les élèves
        ayant le statut 'ACCEPTED' et les affiche dans le tableau TableListe.
        En cas d'erreur de connexion, affiche un message d'erreur.

        Raises:
            Exception: En cas d'erreur de connexion à la base de données
        """
        try:
            print("Maintine")
            # Vérifie si la connexion à la base de données est établie
            if self.Database.connection:
                print("connecter")
                # Appelle la méthode du gestionnaire de BD pour récupérer les élèves acceptés
                data=self.Database.GetEleveAccepted()
                print(data)
                if data:
                    print(data)
                    # Vide le tableau avant d'insérer les nouvelles données
                    for row in data:
                        self.TableListe.delete(*self.TableListe.get_children())
                        # Insère chaque élève dans le Treeview
                        self.TableListe.insert("",END,values=row)
                        print('ELEVE ACCEPTER TROUVER:',row)
                else:
                    # Si aucune donnée, insère une ligne vide
                    self.TableListe.insert("",END,values=[])
                    
        except Exception as e:
            # Affiche un message d'erreur en cas de problème
            messagebox.showerror("Erreur",f"Erreur de connection {e}")
    



    def repartitionGlobal(self):
        """
        Effectuer la repartition global sur la liste des touts les eleves en fonction de la classe souhaiter 

        """
        niveau = self.niveau_var.get().upper()
        nb = int(self.nnbrClasse.get())
        try:
            if self.Database.connection:
                self.Database.affectation_global(niveau=niveau,nb =nb)
                messagebox.showinfo("Succès", f"Répartition globale effectuée pour le niveau {niveau} avec {nb} classes créées.")
                self.getAccepted()  # Rafraîchir la liste des élèves acceptés
                self.reinitialiser_champs()  # Réinitialiser les champs du formulaire
                self.classReelCombox.configure(values=self.Database.getClasseReel())  # Rafraîchir la liste des classes réelles dans le combobox

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la répartition globale : {e}")

    
    def getDonnerAccepted(self,ev):
        """
        Récupère les données de l'élève sélectionné dans le Treeview des acceptés.

        Cette méthode est appelée lors d'un clic sur une ligne du tableau des élèves
        acceptés. Elle remplit automatiquement les champs du formulaire avec les
        informations de l'élève sélectionné.

        Args:
            ev: Événement du clic (non utilisé dans cette implémentation)

        Note:
            En cas d'IndexError (ligne vide sélectionnée), l'exception est ignorée.
        """
        selected =self.TableListe.focus()
        try:
            # Récupère les valeurs de la ligne sélectionnée
            values =self.TableListe.item(selected,'values')

            # Remplit les variables des champs avec les données de l'élève
            self.id_var.set(values[0])
            self.matricule_var.set(values[1])
            self.nom_var.set(values[2])
            self.prenom_var.set(values[3])
            self.date_naissance_var.set(str(values[4]))
            self.addresse_var.set(values[5])
            self.classe_var.set(values[6])
        except IndexError:
            # Ignore si aucune ligne valide n'est sélectionnée
            pass
    
    def afficherClasse(self,value):
        """
        Affiche les élèves d'une classe réelle sélectionnée dans le Treeview.

        Cette méthode est appelée lorsque l'utilisateur sélectionne une classe
        dans le combobox. Elle récupère tous les élèves de cette classe et les
        affiche dans le tableau des classes réelles.

        Args:
            value: La valeur sélectionnée dans le combobox (nom de la classe)

        Raises:
            Exception: En cas d'erreur de connexion à la base de données
        """

        try:
            # Vérifie la connexion à la base de données
            if self.Database.connection:
                 #recuperer la liste des classe reel pour le combox

                classe_reel =self.classReelCombox.get()
                print(f"Classe réelle sélectionnée e : {classe_reel}")  # Debug: afficher la classe réelle sélectionnée
                # Appelle la méthode pour récupérer les élèves de la classe sélectionnée
                data=self.Database.GetEleveByClasse(classe_reel)
                if data:
                    # Vide le tableau et insère les nouvelles données
                    for row in data:
                        self.TableListeClasse.delete(*self.TableListeClasse.get_children())
                        self.TableListeClasse.insert("",END,values=row)
                        print(row)
                else:
                    # Si aucune donnée, insère une ligne vide
                    self.TableListeClasse.insert("",END,values=[])
                    
        except Exception as e:
            # Affiche un message d'erreur en cas de problème
            messagebox.showerror("Erreur",f"Erreur de connection {e}")


    

    def afficher_menuC(self, event):
        """
        Affiche le menu contextuel pour les actions sur les élèves des classes réelles.

        Cette méthode est appelée lors d'un clic droit sur une ligne du tableau
        des classes réelles. Elle sélectionne la ligne et affiche le menu contextuel.

        Args:
            event: L'événement du clic droit contenant les coordonnées
        """
        # Identifie la ligne sous la souris
        item = self.TableListeClasse.identify_row(event.y)

        if item:
            # Sélectionne la ligne identifiée
            self.TableListeClasse.selection_set(item)

            # Récupère les valeurs de la ligne sélectionnée
            self.selected_item = self.TableListeClasse.item(item, "values")

            # Affiche le menu contextuel à la position du clic
            self.menu_treeC.tk_popup(event.x_root, event.y_root)


    def voir_details(self):
        """
        Affiche les détails de l'élève sélectionné.

        Cette méthode est appelée depuis le menu contextuel pour voir
        les informations détaillées de l'élève sélectionné.

        Note:
            Actuellement, cette méthode affiche seulement un message de debug.
            Elle devrait être implémentée pour ouvrir une fenêtre de détails.
        """
        print("Détails :", self.selected_item)


    def modifier_eleve(self):
        """
        Ouvre une interface pour modifier les informations de l'élève sélectionné.

        Cette méthode est appelée depuis le menu contextuel pour permettre
        la modification des données de l'élève.

        Note:
            Actuellement, cette méthode affiche seulement un message de debug.
            Elle devrait être implémentée pour ouvrir une fenêtre d'édition.
        """
        print("Modifier :", self.selected_item)


    def supprimer_eleve(self):
        """
        Supprime l'élève sélectionné après confirmation.

        Cette méthode est appelée depuis le menu contextuel pour supprimer
        un élève de la base de données.

        Note:
            Actuellement, cette méthode affiche seulement un message de debug.
            Elle devrait être implémentée avec une confirmation et la logique de suppression.
        """
        print("Supprimer :", self.selected_item)
    


    def afficher_menu_contextuel(self, event):
        # Trouver la ligne sous la souris
        item_id = self.TableListe.identify_row(event.y)
        if item_id:
            self.TableListe.selection_set(item_id) # Sélectionne la ligne
            self.selected_item = self.TableListe.item(item_id, 'values') # Récupère les données
            
            # On vide le menu précédent
            self.menu_treeL.delete(0, END)
            
            # On ajoute des options dynamiques basées sur le niveau souhaité
            niveau = self.selected_item[6] #  le niveau est en 7ème colonne
            
            for lettre in ["A", "B", "C", "D"]:
                nom_classe = f"{niveau} {lettre}"
                self.menu_treeL.add_command(
                    label=f"Affecter en {nom_classe}", 
                    command=lambda c=nom_classe: self.Database.affectation_individuel(c, self.selected_item,self.getAccepted))
                #si sa reussi on doit rafraichir la table des élèves acceptés et la table des classes réelles
            
            # Afficher le menu là où se trouve la souris
            self.menu_treeL.post(event.x_root, event.y_root)
    
    # ===================== METHODES POUR LES BOUTONS =====================
    
    def reinitialiser_champs(self):
        """
        Réinitialise tous les champs d'entrée du formulaire.

        Cette méthode vide tous les champs de saisie et les listes déroulantes
        pour permettre une nouvelle saisie.
        """
        self.matricule_entry.delete(0, END)
        self.nom_entry.delete(0, END)
        self.prenom_entry.delete(0, END)
        self.date_naissance_entry.delete(0, END)
        self.addresse_entry.delete(0, END)
        self.classe_entry.delete(0, END)
        self.nbrClasse.delete(0, END)
        self.class_combobox.set("")

    def refresh(self):
        """Appelé depuis main.py à chaque fois qu'on affiche cette vue."""
        self.reinitialiser_champs()   # vide le formulaire
        self.getAccepted()            # recharge les élèves acceptés non affectés

        # Rafraîchit aussi le combobox des classes réelles
        classes = self.Database.getClasseReel()
        self.classReelCombox.configure(values=classes)

        # Vide le tableau des classes réelles (sera rempli au choix du combobox)
        self.TableListeClasse.delete(*self.TableListeClasse.get_children())
        self._start_auto_refresh() 
    



     # ─── NOUVELLES MÉTHODES À AJOUTER ────────────────────────────

    def _poll_database(self):
        """Requête silencieuse : vérifie les deux tableaux sans
        perturber la sélection ou les champs du formulaire."""
        if not self.Database.connection:
            return
        try:
            # 1. Vérifie le tableau des élèves acceptés non affectés
            nouvelles_datas = self.Database.GetEleveAccepted()
            ids_affiches = {
                self.TableListe.item(i, "values")[0]
                for i in self.TableListe.get_children()
            }
            ids_bdd = {str(row[0]) for row in nouvelles_datas} if nouvelles_datas else set()

            if ids_affiches != ids_bdd:
                self.TableListe.delete(*self.TableListe.get_children())
                if nouvelles_datas:
                    for row in nouvelles_datas:
                        self.TableListe.insert("", END, values=row)

            # 2. Vérifie si de nouvelles classes réelles sont apparues
            classes_actuelles = set(self.classReelCombox.cget("values"))
            classes_bdd = set(self.Database.getClasseReel())
            if classes_actuelles != classes_bdd:
                self.classReelCombox.configure(values=list(classes_bdd))

        except Exception:
            pass  # Silencieux

    def _start_auto_refresh(self):
        """Démarre le polling (appelé quand la vue devient visible)."""
        self._stop_auto_refresh()
        self._auto_refresh()

    def _auto_refresh(self):
        """Boucle : interroge la BDD puis se replanifie dans 10 s."""
        self._poll_database()
        self._refresh_job = self.after(10000, self._auto_refresh)

    def _stop_auto_refresh(self):
        """Stoppe le polling (appelé quand la vue est cachée)."""
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None