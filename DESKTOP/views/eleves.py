




from encodings.punycode import T
from tkinter import ttk

from customtkinter import * 

from utils.constant import * 

#creation de la classe eleveView qui sera une frame qui va contenir les info et etre charger dans acceuil

#lorsque on va l'appler on renseinger dans quel parent(master ,elle sera)

class EleveView(CTkFrame):
    def __init__(self,master,*args,**kwargs):
        super().__init__(master,*args,**kwargs)
        self.master =master
        # self.connection =connection
        self.configure(fg_color=BACKGROUND_LIGHT)

        #titre de la pages
        titreFrame =CTkFrame(self,fg_color='lightblue',border_width=0,height=50)
        titreFrame.pack(fill =X,side =TOP)
        titreLabel =CTkLabel(titreFrame,text ="Gestoin des ELEVES",font =FONT_TITLE,text_color=PRIMARY_BLUE,fg_color="lightblue")
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
        self.searchEntry =CTkEntry(frameSearch,placeholder_text="Rechercher par matricule",font=FONT_LABEL,fg_color=BACKGROUND_LIGHT,border_width=2,text_color=PRIMARY_BLUE,border_color=PRIMARY_BLUE)
        self.searchEntry.pack(side =LEFT,anchor =N,expand =True,pady =10)
        self.btnSerch =CTkButton(frameSearch,text ="Rechercher",font=FONT_LABEL,fg_color=PRIMARY_BLUE,hover_color=SECONDARY_BLUE,border_width=0)
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
        
        entrymatricule = CTkEntry(matriculeFrame, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Matricule", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
        entrymatricule.pack(fill=X, anchor=W)

        # Nom à droite
        nomFrame = CTkFrame(row1, fg_color=BACKGROUND_LIGHT)
        nomFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))
        
        nomLabel = CTkLabel(nomFrame, text="Nom", font=FONT_LABEL, text_color=TEXT_DARK, fg_color=BACKGROUND_LIGHT)
        nomLabel.pack(anchor=W, pady=(0, 2))
        
        entryNom = CTkEntry(nomFrame, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Nom", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
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
        
        entryprenom = CTkEntry(prenomFrame, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Prenom", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
        entryprenom.pack(fill=X, anchor=W)

        # Date Naissance à droite
        dateFrame = CTkFrame(row2, fg_color=BACKGROUND_LIGHT)
        dateFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))
        
        date_naissanceLabel = CTkLabel(dateFrame, text="Date Naissance", font=FONT_LABEL, text_color=TEXT_DARK, fg_color=BACKGROUND_LIGHT)
        date_naissanceLabel.pack(anchor=W, pady=(0, 2))
        
        entrydate_naissance = CTkEntry(dateFrame, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Date de Naissance", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
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
        
        entryaddresse = CTkEntry(addresseFrame, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Addresse", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
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
        
        entryClasse = CTkEntry(classeFrame, font=("times new roman",15,"bold"), fg_color=BACKGROUND_LIGHT, border_width=2, placeholder_text="Classe", text_color=PRIMARY_BLUE, border_color=PRIMARY_BLUE)
        entryClasse.pack(fill=X, anchor=W)

        # Placeholder frame pour équilibre
        imageFrame = CTkFrame(row4, fg_color="blue",border_width=1)
        imageFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))



        # =============================================
        # BOUTONS D'ACTIONS (en bas)
        # =============================================
        buttonsFrame = CTkFrame(mainContentFrame, fg_color=BACKGROUND_LIGHT)
        buttonsFrame.pack(fill=X, expand=True, pady=10)

        self.addbutton = CTkButton(buttonsFrame, text="Ajouter", font=FONT_LABEL, fg_color=SUCCESS_GREEN, hover_color="#27AE60", border_width=0,width=100)
        self.addbutton.pack(side=LEFT, padx=5, fill=X, expand=True)

        self.updatebutton = CTkButton(buttonsFrame, text="Modifier", font=FONT_LABEL, fg_color=WARNING_ORANGE, hover_color="#D35400", border_width=0,width=100)
        self.updatebutton.pack(side=LEFT, padx=5, fill=X, expand=True)

        self.deletebutton = CTkButton(buttonsFrame, text="Supprimer", font=FONT_LABEL, fg_color=DANGER_RED, hover_color="#C0392B", border_width=0,width=100)
        self.deletebutton.pack(side=LEFT, padx=5, fill=X, expand=True)

        self.renitialiserbutton = CTkButton(buttonsFrame, text="Renitialiser", font=FONT_LABEL, fg_color=INFO_GRAY, hover_color="#95A5A6", border_width=0,width=100)
        self.renitialiserbutton.pack(side=LEFT, padx=5, fill=X, expand=True)







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


        self.TableListe =ttk.Treeview(tableFrame,columns=("Matricule","Nom","Prenom","Date Naissance","Addresse","Classe"),show="headings")
        self.TableListe.heading("Matricule",text='Matricule')
        self.TableListe.heading("Nom",text='Nom')
        self.TableListe.heading("Prenom",text='Prenom')
        self.TableListe.heading("Date Naissance",text='Date Naissance')
        self.TableListe.heading("Addresse",text='Addresse')
        self.TableListe.heading("Classe",text='Classe')

        self.TableListe.column("Matricule",width=80)
        self.TableListe.column("Nom",width=100)
        self.TableListe.column("Prenom",width=100)
        self.TableListe.column("Date Naissance",width=100)
        self.TableListe.column("Addresse",width=150)
        self.TableListe.column("Classe",width=80)

        xcrollbar =ttk.Scrollbar(tableFrame,orient=HORIZONTAL,command=self.TableListe.xview)
        yscrollbar =ttk.Scrollbar(tableFrame,orient=VERTICAL,command=self.TableListe.yview)
        self.TableListe.configure(xscrollcommand=xcrollbar.set,yscrollcommand=yscrollbar.set)
        xcrollbar.pack(side=BOTTOM,fill=X)
        yscrollbar.pack(side=RIGHT,fill=Y)

        self.TableListe.pack(fill=BOTH,expand=True,pady=10,padx=10)
        for i in range(150):
            self.TableListe.insert("",END,values=i)


        #place de de notre frame 
        self.pack(fill =BOTH,expand =True)
