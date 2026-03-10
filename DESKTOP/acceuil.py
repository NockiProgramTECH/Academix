

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
        self.after(500,self.showNotifications())



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
    # Toutes les vues sont créées UNE SEULE FOIS au démarrage
    # puis cachées. On les affiche/cache sans les recréer.
    # Les données sont rechargées via refresh() à chaque affichage.

        self.views = {}
        self.current_view = None  # Aucune vue active au départ

        # Création de toutes les vues (cachées par défaut)
        self._create_eleve_view()
        self._create_repartitions_view()

        # Afficher la vue par défaut au lancement
        self.show_view("eleve")


    def _create_eleve_view(self):
        """Crée la vue EleveView et la stocke dans self.views.
        Elle est cachée immédiatement après création.
        Les données seront chargées lors du premier show_view("eleve").
        """
        from views.eleves import EleveView
        eleve_view = EleveView(self.mainFrame)
        eleve_view.pack_forget()  # Cachée par défaut
        self.views["eleve"] = eleve_view


    def _create_repartitions_view(self):
        """Crée la vue Repartitions et la stocke dans self.views.
        Elle est cachée immédiatement après création.
        Les données seront chargées lors du premier show_view("repartitions").
        """
        from views.repartitions import Repartitions
        repartitions_view = Repartitions(self.mainFrame)
        repartitions_view.pack_forget()  # Cachée par défaut
        self.views["repartitions"] = repartitions_view

    def show_view(self, view_name: str):
        """Affiche une vue et recharge ses données via refresh().

        Workflow :
            1. Vérifie que la vue demandée existe
            2. Stoppe le polling de la vue quittée
            3. Cache la vue actuellement affichée
            4. Affiche la nouvelle vue
            5. Appelle refresh() qui démarre le polling de la nouvelle vue

        Args:
            view_name (str): Clé de la vue à afficher ("eleve", "repartitions", ...)
        """
        # Sécurité : la clé doit exister dans le dictionnaire
        if view_name not in self.views:
            print(f"[WARN] Vue introuvable : '{view_name}'")
            return

        # Cache la vue courante + stoppe son polling
        if self.current_view and self.current_view in self.views:
            vue_quittee = self.views[self.current_view]

            # Stoppe le polling AVANT de cacher la vue
            if hasattr(vue_quittee, "_stop_auto_refresh"):
                vue_quittee._stop_auto_refresh()

            vue_quittee.pack_forget()

        # Affiche la nouvelle vue
        self.views[view_name].pack(fill=BOTH, expand=True)
        self.current_view = view_name

        # refresh() recharge les données ET démarre le polling de la nouvelle vue
        if hasattr(self.views[view_name], "refresh"):
            self.views[view_name].refresh()
        else:
            print(f"[WARN] La vue '{view_name}' n'a pas de méthode refresh()")

    def show_eleve_view(self):
        """Raccourci pour afficher la vue inscriptions depuis la sidebar."""
        self.show_view("eleve")


    def show_repartitions_view(self):
        """Raccourci pour afficher la vue répartitions depuis la sidebar."""
        self.show_view("repartitions")


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
