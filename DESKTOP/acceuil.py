

from tkinter import messagebox

from customtkinter import *

#importation des constant pour le style 

from utils.constant import *

from PIL import Image,ImageTk
import pathlib

from data.db_manager import DbManager
#recupron le chemin des images poru les charger 
IMAGE_DIR =pathlib.Path(__file__).parent / "images"

print(IMAGE_DIR)


class Acceuil(CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}-1+0")
        self.title("Academix")
        self._set_appearance_mode("light")
        self.Database =DbManager()


        self.images ={}


        #PARTIE HEADER LA FENETRE
        header =CTkFrame(self, fg_color=PRIMARY_BLUE,height =75,border_width=0,bg_color=PRIMARY_BLUE)
        header.pack(fill =X,side =TOP)
        header.pack_propagate(False)

        #icone de Academix
        self.images['logo'] =CTkImage(Image.open(IMAGE_DIR / "logo.png"),size=(50,50  ))
        logoLabel =CTkLabel(header,image =self.images['logo'],text="")
        logoLabel.pack(side =LEFT,padx =20)
        

        #ICON DE NOTIFICATIONS
        self.images['notification_icon'] =CTkImage(Image.open(IMAGE_DIR / "notification.png"),size=(50,50))
        self.notificationLabel =CTkButton(header,image =self.images['notification_icon'],text="0",font=("goudy old style",30,"bold"),fg_color=PRIMARY_BLUE,text_color="red")
        self.notificationLabel.pack(side =RIGHT,padx =20)
        self.showNotifications()



        # Fonction utilitaire pour créer une ligne label + entry def add_row(parent, label_text): row = tk.Frame(parent) row.pack(fill="x", pady=5) lbl = tk.Label(row, text=label_text, width=15, anchor="w") lbl.pack(side="left") entry = tk.Entry(row) entry.pack(side="left", fill="x", expand=True) return entry # Création des lignes matricule_entry = add_row(main_frame, "Matricule") nom_entry = add_row(main_frame, "Nom") prenom_entry = add_row(main_frame, "Prénom") date_entry = add_row(main_frame, "Date naissance")

        

        sidebar =CTkFrame(self,fg_color=SIDEBAR_BG,width=SIDEBAR_WIDTH,border_width=0)
        sidebar.pack(fill =Y,side =LEFT)
        sidebar.pack_propagate(False)

        sidebar_title =CTkLabel(sidebar,text ="Tableau de bord",font=FONT_TITLE,fg_color=SIDEBAR_BG,text_color=SIDEBAR_TEXT)
        sidebar_title.pack(pady =20)

        #mainframe est la frame ou on va afficher les differentes page de l'application
        self.mainFrame =CTkFrame(self,fg_color=BACKGROUND_LIGHT,bg_color=BACKGROUND_LIGHT)
        self.mainFrame.pack(fill =BOTH,side =LEFT,expand =True)


        #btn_config 
        BTN ={
            1:{
                'text':"Gestion Des Eleves",
                'command':lambda:self.show_view("eleve"),
                'image':''
            },
            2:{
                "text":"Affectation Par Classe",
                "command":lambda:self.show_view("repartitions"),
                "image":''
            }
        }

    
        for key,value in BTN.items():
           btn =CTkButton(sidebar,text=value['text'],font=FONT_TITLE,fg_color=SIDEBAR_BG,text_color=SIDEBAR_TEXT,command=value['command'],hover_color=SIDEBAR_HOVER,border_width=5)
           btn.pack(fill=X,pady=5,padx=10,)


        # =====================================================
        # PRE-CREATION DES VUES (Optimisation performance)
        # =====================================================
        # Toutes les vues sont créées au démarrage mais cachées
        # Elles seront affichées au clic sur les boutons
        self.views = {}
        
        # Pré-créer la vue eleves (la plus utilisée)
        self._create_eleve_view()
        
        # Pré-créer placeholder pour les autres vues (à compléter)
        self.views["repartitions"] = self._create_repartitions_view()
        
        # Afficher la vue d'accueil par défaut (eleve)
        self.current_view = "eleve"
        # Afficher la vue EleveView au démarrage
        self.views["eleve"].pack(fill=BOTH, expand=True)

    def _create_eleve_view(self):
        """Pré-créer la vue eleves"""
        from views.eleves import EleveView
        eleve_view = EleveView(self.mainFrame)
        eleve_view.pack(fill=BOTH, expand=True)
        # Cacher initialement
        eleve_view.pack_forget()
        self.views["eleve"] = eleve_view

    def _create_repartitions_view(self):
        from views.repartitions import Repartitions
        repartitions_view = Repartitions(self.mainFrame)
        repartitions_view.pack(fill=BOTH, expand=True)
        # Cacher initialement
        repartitions_view.pack_forget()
        self.views["repartitions"] = repartitions_view
        return repartitions_view


    def show_view(self, view_name):
        """Afficher une vue spécifique en cachant les autres"""
        # Vérifier si la vue existe
        if view_name not in self.views:
            return
        
        # Cacher la vue actuelle
        if self.current_view and self.current_view in self.views:
            self.views[self.current_view].pack_forget()
        
        # Afficher la nouvelle vue
        self.views[view_name].pack(fill=BOTH, expand=True)
        self.current_view = view_name
        
        # Rafraîchir les données si c'est la vue eleves
        if view_name == "eleve" and hasattr(self.views["eleve"], "refresh"):
            self.views["eleve"].refresh()

    def show_eleve_view(self):
        """Méthode de compatibilité - redirige vers show_view"""
        self.show_view("eleve")

    def showNotifications(self):
        """fonction pour afficher le nombre de notifications
        """
        try:
            if self.Database.connection:
                data =self.Database.refresh_pending_list()
                if len(data) > 0:
                    self.notificationLabel.configure(text =f"{len(data)}")
                else:
                    pass
    
        except Exception as e :
            messagebox.showerror("Erreur",f"Erreur de :{e}")

if __name__ =="__main__":
    app =Acceuil()
    app.mainloop()
