
import pathlib

from re import I
from tkinter import messagebox, ttk

from customtkinter import *


from utils.constant import * 

from data.db_manager import DbManager
from .documentView import DocView

INSCRIPTION_DIR =pathlib.Path(__file__).parent.parent.parent / "WEB" / "media" 


#creation de la classe eleveView qui sera une frame qui va contenir les info et etre charger dans acceuil

#lorsque on va l'appler on renseinger dans quel parent(master ,elle sera)

class EleveView(CTkFrame):
    def __init__(self,master,*args,**kwargs):
        super().__init__(master,*args,**kwargs)
        self.master =master
        self.Database =DbManager()
        self.configure(fg_color=BACKGROUND_LIGHT)

        self._refresh_job = None  # ← AJOUTER : référence au job after()


        #*VARIABLES
        self.id_var =StringVar()
        self.matricule_var =StringVar()
        self.nom_var =StringVar()
        self.prenom_var =StringVar()
        self.date_naissance_var =StringVar()
        self.addresse_var =StringVar()
        self.classe_var =StringVar()
        self.search_var =StringVar()
        self.imagePath =StringVar()
        self.typesearch_var =StringVar()

        #document de l'eleve (nom des fichiers récupérés en base)
        self.acteNaissance = None
        self.diplome = None
        self.last_bulletin = None
        # chemins vers les documents (utilisés par ShowEleveDocument)
        self.docActeNaissance = None
        self.docDiplome = None
        self.docBulletin = None

        #titre de la pages
        titreFrame =CTkFrame(self,fg_color='lightblue',border_width=0,height=50)
        titreFrame.pack(fill =X,side =TOP)
        titreLabel =CTkLabel(titreFrame,text ="Gestoin des Inscriptions",font =FONT_TITLE,text_color=PRIMARY_BLUE,fg_color="lightblue")
        titreLabel.pack(pady =20)

        # framepour afficher les infos dans des entry et e des bouttons d'actions(a gauche) et le tableau a droite

        infoFrame =CTkFrame(self,fg_color=BACKGROUND_LIGHT,width=500,border_width=1)
        infoFrame.pack(fill =Y,side =LEFT)
        infoFrame.pack_propagate(False)


        #titre de la frame info
        infoTitre= CTkLabel(infoFrame,text ="Information Eleve",font=FONT_TITLE,text_color=BACKGROUND_LIGHT,fg_color=PRIMARY_BLUE,bg_color=BACKGROUND_LIGHT)
        infoTitre.pack(fill =X,side =TOP)

        frameSearch =CTkFrame(infoFrame,fg_color=BACKGROUND_LIGHT,border_width=0,)
        frameSearch.pack(fill =X,side =TOP)

        #label et entry pour les info de l'eleve   
        self.combo =CTkComboBox(frameSearch,width=140,corner_radius=10,border_width=5,
    
                                button_hover_color=PRIMARY_BLUE,values=['matricule','nom','prenom'],
                                border_color=PRIMARY_BLUE,text_color=BACKGROUND_LIGHT)
        self.combo.pack(side= LEFT,anchor =N,pady =10,)

        self.searchEntry =CTkEntry(frameSearch,placeholder_text="Rechercher ",font=FONT_LABEL,fg_color=BACKGROUND_LIGHT,
                                   border_width=2,
                                   text_color=PRIMARY_BLUE,
                                   border_color=PRIMARY_BLUE,
                                   textvariable=self.search_var)
        
        self.searchEntry.pack(side =LEFT,anchor =N,expand =True,pady=10,padx =10)

        self.btnSerch =CTkButton(frameSearch,text ="Rechercher",font=FONT_LABEL,fg_color=PRIMARY_BLUE,
                                 hover_color=SECONDARY_BLUE,border_width=0,text_color=BACKGROUND_LIGHT
                                 ,command=self.Search)
        self.btnSerch.pack(side =LEFT,anchor =N,padx =20,pady =10)



        # =============================================
        # CONTENEUR PRINCIPAL POUR LES CHAMPS DEUX À DEUX
        # =============================================
        # Créer une frame principale qui contiendra les paires
        mainContentFrame = CTkFrame(infoFrame, fg_color=BACKGROUND_LIGHT)
        mainContentFrame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # =============================================
        # ROW 1: Matricule | Nom
        # =============================================
        row1 = CTkFrame(mainContentFrame, fg_color=BACKGROUND_LIGHT)
        row1.pack(fill=X, expand=True, pady=5)

        # Matricule à gauche
        matriculeFrame = CTkFrame(row1, fg_color=BACKGROUND_LIGHT)
        matriculeFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        matriculeLabel = CTkLabel(matriculeFrame, text="Matricule", font=FONT_LABEL, text_color=TEXT_DARK, fg_color=BACKGROUND_LIGHT)
        matriculeLabel.pack(anchor=W, pady=(0, 2))
        
        entrymatricule = CTkEntry(matriculeFrame,textvariable=self.matricule_var, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Matricule", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
        entrymatricule.pack(fill=X, anchor=W)

        # Nom à droite
        nomFrame = CTkFrame(row1, fg_color=BACKGROUND_LIGHT)
        nomFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))
        
        nomLabel = CTkLabel(nomFrame, text="Nom", font=FONT_LABEL, text_color=TEXT_DARK, fg_color=BACKGROUND_LIGHT)
        nomLabel.pack(anchor=W, pady=(0, 2))
        
        entryNom = CTkEntry(nomFrame,textvariable =self.nom_var, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Nom", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
        entryNom.pack(fill=X, anchor=W)

        # =============================================
        # ROW 2: Prenom | Date Naissance
        # =============================================
        row2 = CTkFrame(mainContentFrame, fg_color=BACKGROUND_LIGHT)
        row2.pack(fill=X, expand=True, pady=5)

        # Prenom à gauche
        prenomFrame = CTkFrame(row2, fg_color=BACKGROUND_LIGHT)
        prenomFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        prenomLabel = CTkLabel(prenomFrame, text="Prenom", font=FONT_LABEL, text_color=TEXT_DARK, fg_color=BACKGROUND_LIGHT)
        prenomLabel.pack(anchor=W, pady=(0, 2))
        
        entryprenom = CTkEntry(prenomFrame,textvariable=self.nom_var, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Prenom", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
        entryprenom.pack(fill=X, anchor=W)

        # Date Naissance à droite
        dateFrame = CTkFrame(row2, fg_color=BACKGROUND_LIGHT)
        dateFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))
        
        date_naissanceLabel = CTkLabel(dateFrame, text="Date Naissance", font=FONT_LABEL, text_color=TEXT_DARK, fg_color=BACKGROUND_LIGHT)
        date_naissanceLabel.pack(anchor=W, pady=(0, 2))
        
        entrydate_naissance = CTkEntry(dateFrame,textvariable=self.date_naissance_var, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Date de Naissance", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
        entrydate_naissance.pack(fill=X, anchor=W)

        # =============================================
        # ROW 3: Addresse | ImageFrame (en carré)
        # =============================================
        row3 = CTkFrame(mainContentFrame, fg_color=BACKGROUND_LIGHT)
        row3.pack(fill=X, expand=True, pady=5)

        # Addresse à gauche
        addresseFrame = CTkFrame(row3, fg_color=BACKGROUND_LIGHT)
        addresseFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        addresseLabel = CTkLabel(addresseFrame, text="Addresse", font=FONT_LABEL, text_color=TEXT_DARK, fg_color=BACKGROUND_LIGHT)
        addresseLabel.pack(anchor=W, pady=(0, 2))
        
        entryaddresse = CTkEntry(addresseFrame,textvariable=self.addresse_var, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Addresse", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
        entryaddresse.pack(fill=X, anchor=W)

       

        # =============================================
        # ROW 4: Classe
        # =============================================
        row4 = CTkFrame(mainContentFrame, fg_color=BACKGROUND_LIGHT)
        row4.pack(fill=X, expand=True, pady=5)

        # Classe à gauche
        classeFrame = CTkFrame(row4, fg_color=BACKGROUND_LIGHT)
        classeFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        classeLabel = CTkLabel(classeFrame, text="Classe", font=FONT_LABEL, text_color=TEXT_DARK, fg_color=BACKGROUND_LIGHT)
        classeLabel.pack(anchor=W, pady=(0, 2))
        
        entryClasse = CTkEntry(classeFrame,textvariable=self.classe_var, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Classe", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
        entryClasse.pack(fill=X, anchor=W)

        # Placeholder frame pour équilibre
        imageFrame = CTkFrame(row4, fg_color="blue",border_width=1)
        imageFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))
        imageFrame.pack_propagate(False)

        self.ImageEleve =CTkLabel(imageFrame,text ="Photo",fg_color="lightgray")
        self.ImageEleve.place(x =0,y=0,relwidth=1,relheight=1)



        # =============================================
        # BOUTONS D'ACTIONS (en bas)
        # =============================================
        buttonsFrame = CTkFrame(mainContentFrame, fg_color=BACKGROUND_LIGHT)
        buttonsFrame.pack(fill=X, expand=True, pady=10)

        self.addbutton = CTkButton(buttonsFrame, text="ACCEPTER", font=FONT_LABEL,
                    fg_color=SUCCESS_GREEN,
                    hover_color="#27AE60",
                    border_width=0,width=100,
                    command =self.Accepted)

        self.addbutton.pack(side=LEFT,
                padx=5, fill=X, 
                expand=True)

        self.updatebutton = CTkButton(buttonsFrame,
                     text="Modifier", font=FONT_LABEL, fg_color=WARNING_ORANGE, hover_color="#D35400", border_width=0,width=100)

        self.updatebutton.pack(side=LEFT, padx=5, 
                         fill=X, expand=True)

        self.deletebutton = CTkButton(buttonsFrame, text="Supprimer", font=FONT_LABEL, fg_color=DANGER_RED, hover_color="#C0392B", border_width=0,width=100)
        self.deletebutton.pack(side=LEFT, padx=5, fill=X, expand=True)

        self.showDocbutton = CTkButton(buttonsFrame, 
                                            text="Voir Documents", 
                                            font=FONT_LABEL, 
                                            fg_color=INFO_GRAY, 
                                            hover_color="#95A5A6",
                                              border_width=0,width=100,command =self.ShowEleveDocument)
        self.showDocbutton.pack(side=LEFT, padx=5,
         fill=X, 
        expand=True)







        #frame poru le tableau des eleve
        tableFrame =CTkFrame(self,fg_color=BACKGROUND_LIGHT,border_width=1)
        tableFrame.pack(fill =BOTH,side =LEFT,expand =True)

        tableTitre =CTkLabel(tableFrame,text ="Liste des Eleves",font=FONT_TITLE,text_color=BACKGROUND_LIGHT,fg_color=PRIMARY_BLUE,bg_color=BACKGROUND_LIGHT)
        tableTitre.pack(fill =X,side =TOP)
        #tableau treeview pour afficher les eleves


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


        self.TableListe =ttk.Treeview(tableFrame,columns=("id","Matricule","Nom","Prenom","Date Naissance","Addresse","Classe"),show="headings")
        self.TableListe.heading("id",text='')
        self.TableListe.heading("Matricule",text='Matricule')
        self.TableListe.heading("Nom",text='Nom')
        self.TableListe.heading("Prenom",text='Prenom')
        self.TableListe.heading("Date Naissance",text='Date Naissance')
        self.TableListe.heading("Addresse",text='Addresse')
        self.TableListe.heading("Classe",text='Classe')

        self.TableListe.column("id",width=0)
        self.TableListe.column("Matricule",width=80)
        self.TableListe.column("Nom",width=100)
        self.TableListe.column("Prenom",width=100)
        self.TableListe.column("Date Naissance",width=100)
        self.TableListe.column("Addresse",width=150)
        self.TableListe.column("Classe",width=80)


        #Scollbar pour le controle du tableau

        xcrollbar =ttk.Scrollbar(tableFrame,orient=HORIZONTAL,command=self.TableListe.xview)
        yscrollbar =ttk.Scrollbar(tableFrame,orient=VERTICAL,command=self.TableListe.yview)
        self.TableListe.configure(xscrollcommand=xcrollbar.set,yscrollcommand=yscrollbar.set)
        xcrollbar.pack(side=BOTTOM,fill=X)
        yscrollbar.pack(side=RIGHT,fill=Y)


        #appel de la fonction evenement pour afficher les elements
        self.TableListe.bind("<ButtonRelease-1>",self.getListeData)

        self.TableListe.pack(fill=BOTH,expand=True,pady=10,padx=10)
    

        #place de de notre frame 
        self.pack(fill =BOTH,expand =True)
    
    def GetEleves(self):
        if self.Database.connection:
            data =self.Database.refresh_pending_list()
            self.TableListe.delete(*self.TableListe.get_children())
          
            for row in data:

                self.TableListe.insert("",END,values  =row)

    
    def refresh(self):
        """Appelé depuis main.py à chaque fois qu'on affiche cette vue."""
        self.clear()           # vide les champs du formulaire
        self.GetEleves()
    
    
    #fonction d"evenement click sur une ligne du tableau qui va retourner les element dans les entry

    def getListeData(self,ev):
        selected =self.TableListe.focus()
        values =self.TableListe.item(selected,'values')
        
        # Vérifier si une ligne valide est sélectionnée
        if not values:
            return
        
        try:
            self.id_var.set(values[0])
            self.matricule_var.set(values[1])
            self.nom_var.set(values[2])
            self.prenom_var.set(values[3])
            self.date_naissance_var.set(values[4])
            self.addresse_var.set(values[5])
            self.classe_var.set(values[6])
            self.imagePath.set(values[7])
            self.showImage(self.imagePath.get())
        except IndexError:
            # Ignore les erreurs d'index si les données sont incomplètes
            pass



    
    

    def showImage(self,path):
        from PIL import Image,ImageTk
        img =Image.open(INSCRIPTION_DIR / path)
        # img =img.resize((200,200))
        img =CTkImage(img,size=(250,250))
        self.ImageEleve.configure(text ="",image =img)
        # self.ImageEleve.image =img
    
    def clear(self):
        self.id_var.set("")
        self.matricule_var.set("")
        self.nom_var.set("")
        self.prenom_var.set("")
        self.date_naissance_var.set("")
        self.classe_var.set("")
        self.addresse_var.set("")
        self.ImageEleve.configure(image="",text="Photo",fg_color="lightgray")
        self.imagePath.set("")
    

    def Accepted(self):
        """Fonction d'appelle pour accepter l'inscription
        """
        if self.Database.connection:
            self.Database.AcceptedInscription(self.matricule_var.get(),self.id_var.get())
            self.GetEleves()
            self.clear() 
    

    def Search(self):
        """Fonction qui va faire la recherche dans la base de donner
        """
        if self.Database.connection:
            data =self.Database.SearchEleveInscription(self.combo.get(),self.search_var.get())
            print(data)
            if data:
                self.TableListe.delete(*self.TableListe.get_children()) #j'efface la table liste 
                self.clear() #j'efface tous les entry
                for row in data:
                    self.TableListe.insert("",END,values =row)

           
    def GetEleveDocument(self):
        """Récupère les chemins des documents pour l'élève sélectionné.

        La méthode interroge la base de données et stocke les trois
        fichiers dans des attributs de l'instance. Elle renvoie également
        la liste retournée par la base afin que l'appelant puisse
        l'exploiter directement.

        Returns
            Une liste de trois éléments [acteNaissance, diplome, bulletin]
            ou ``None`` si aucun document n'a été trouvé. Dans ce dernier cas
            une boîte de dialogue est affichée.
        """
        if self.Database.connection:
            documents = self.Database.GetDocuments(self.id_var.get(),)
            if documents:
                print("Documents trouvés :", documents)  # Debug: afficher les documents récupérés
                # les index correspondent à l'ordre renvoyé par GetDocuments
                self.docActeNaissance = documents[0]
                self.docDiplome = documents[1]
                self.docBulletin = documents[2]
                print(self.docActeNaissance, self.docDiplome, self.docBulletin)
                return documents
            else:
                messagebox.showinfo("Documents", "Aucun document trouvé pour cet eleve")
        return None
    


    def _poll_database(self):
        """Requête silencieuse : rafraîchit le Treeview sans toucher
        aux champs du formulaire ni à la sélection en cours."""
        if not self.Database.connection:
            return
        try:
            nouvelles_datas = self.Database.refresh_pending_list()
            
            # Construit un set des IDs déjà affichés
            ids_affiches = {
                self.TableListe.item(i, "values")[0]
                for i in self.TableListe.get_children()
            }
            # Construit un set des IDs reçus de la BDD
            ids_bdd = {str(row[0]) for row in nouvelles_datas} if nouvelles_datas else set()

            # Rafraîchit seulement si les données ont changé
            if ids_affiches != ids_bdd:
                self.TableListe.delete(*self.TableListe.get_children())
                for row in nouvelles_datas:
                    self.TableListe.insert("", END, values=row)

        except Exception:
            pass  # Silencieux : on ne spamme pas de popups en arrière-plan

    def _start_auto_refresh(self):
        """Démarre le polling (appelé quand la vue devient visible)."""
        self._stop_auto_refresh()  # évite les doublons
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
    

    def ShowEleveDocument(self):
        """Fonction qui va se charger d'afficher les documents dans une fenetre separer
        La solution : PyMuPDF (fitz) + PIL (Pillow)
        Pour que cela fonctionne, vous aurez besoin de deux bibliothèques :

        PyMuPDF (fitz) : Pour lire le PDF et transformer les pages en images.

        Pillow (PIL) : Pour manipuler l'image et la rendre compatible avec Tkinter.

        """
        documents = self.GetEleveDocument()
        if not documents:
            print("pas de documents")

            # rien à afficher ou erreur déjà signalée
            return

        # création de notre top level pour afficher les documents
        docWindow = CTkToplevel(self, fg_color=BACKGROUND_LIGHT)
        docWindow.geometry("600x800+750+10")
        docWindow.title("Documents de l'eleve")
        docWindow.resizable(False,False) #ne doit pas etre redimentsionner



        #creation des composants 

        #tabs
        tabframe =CTkFrame(docWindow,fg_color=BACKGROUND_LIGHT)
        tabframe.pack(fill =X,side =TOP)
        tabframe.pack_propagate(False)

        self.Tabview=CTkTabview(docWindow,fg_color ="black",bg_color =PRIMARY_BLUE,text_color =BACKGROUND_LIGHT)
        self.Tabview.place(x =0,y=0,relwidth=1,relheight=0.9)
        self.Tabview.add("Acte de Naissance")
        self.Tabview.add("Diplome")
        self.Tabview.add("Dernier Bulletin")

      
        # utiliser les valeurs retournées plutôt que des attributs non initialisés
        acte_path, diplome_path, bulletin_path = documents
        if not acte_path:
            messagebox.showwarning("Documents", "Aucun acte de naissance disponible")
        else:
            actenaissance_img = DocView(documentpath=INSCRIPTION_DIR / acte_path)
            self.labelActe = CTkLabel(self.Tabview.tab("Acte de Naissance"), text="", image=actenaissance_img, width=596, height=842, fg_color="red")
            self.labelActe.pack(fill="both", pady=20, padx=10, expand=True)
        # affichage du diplome et du bulletin si présents
        if diplome_path:
            diplome_img = DocView(documentpath=INSCRIPTION_DIR / diplome_path)
            self.labelDiplome = CTkLabel(self.Tabview.tab("Diplome"), image=diplome_img, fg_color="green", font=FONT_H1)
            self.labelDiplome.pack(fill=BOTH, expand=True)
        else:
            messagebox.showwarning("Documents", "Aucun diplôme disponible")

        if bulletin_path:
            bulletin_img = DocView(documentpath=INSCRIPTION_DIR / bulletin_path)
            self.last_bulletin = CTkLabel(self.Tabview.tab("Dernier Bulletin"), image=bulletin_img, fg_color="gold", font=FONT_H1)
            self.last_bulletin.pack(fill=BOTH, expand=True)
        else:
            messagebox.showwarning("Documents", "Aucun bulletin disponible")

        docWindow.grab_set()  # empeche l'interaction avec la fenetre principale tant qu'elle reste ouverte
        docWindow.mainloop()



        
