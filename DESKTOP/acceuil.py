

from customtkinter import *

#importation des constant pour le style 

from utils.constant import *

from PIL import Image,ImageTk
import pathlib


#recupron le chemin des images poru les charger 
IMAGE_DIR =pathlib.Path(__file__).parent / "images"
print(IMAGE_DIR)

class Acceuil(CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}-1+0")
        self.title("Academix")
        self._set_appearance_mode("light")
       

        self.images ={}


        #PARTIE HEADER LA FENETRE
        header =CTkFrame(self, fg_color=PRIMARY_BLUE,height =75,border_width=0,bg_color=PRIMARY_BLUE)
        header.pack(fill =X,side =TOP)
        header.pack_propagate(False)

        #icone de Academix
        self.images['logo'] =CTkImage(Image.open(IMAGE_DIR / "logo.png"),size=(75,75))
        logoLabel =CTkLabel(header,image =self.images['logo'],text="")
        logoLabel.pack(side =LEFT,padx =20)

        #ICON DE NOTIFICATIONS
        self.images['notification_icon'] =CTkImage(Image.open(IMAGE_DIR / "notification.png"),size=(50,50))
        self.notificationLabel =CTkLabel(header,image =self.images['notification_icon'],text="0",fg_color=PRIMARY_BLUE,text_color="red")
        self.notificationLabel.pack(side =RIGHT,padx =20)



        # Fonction utilitaire pour créer une ligne label + entry def add_row(parent, label_text): row = tk.Frame(parent) row.pack(fill="x", pady=5) lbl = tk.Label(row, text=label_text, width=15, anchor="w") lbl.pack(side="left") entry = tk.Entry(row) entry.pack(side="left", fill="x", expand=True) return entry # Création des lignes matricule_entry = add_row(main_frame, "Matricule") nom_entry = add_row(main_frame, "Nom") prenom_entry = add_row(main_frame, "Prénom") date_entry = add_row(main_frame, "Date naissance")


            
        

        sidebar =CTkFrame(self,fg_color=SIDEBAR_BG,width=SIDEBAR_WIDTH,border_width=0)
        sidebar.pack(fill =Y,side =LEFT)
        sidebar.pack_propagate(False)

        sidebar_title =CTkLabel(sidebar,text ="Tableau de bord",font=FONT_TITLE,fg_color=SIDEBAR_BG,text_color=SIDEBAR_TEXT)
        sidebar_title.pack(pady =20)

        #mainframe est la frame ou on va afficher les differentes page de l'application
        self.mainFrame =CTkFrame(self,fg_color=BACKGROUND_LIGHT,bg_color=BACKGROUND_LIGHT)
        self.mainFrame.pack(fill =BOTH,side =LEFT,expand =True)



        self.images['eleve'] =CTkImage(Image.open(IMAGE_DIR / "eleve.png"),size=(ICON_SIZE,ICON_SIZE))


        #btn_config 
        BTN ={
            1:{
                'text':"Gestion Des Eleves",
                'command':lambda:self.show_eleve_view(),
                'image':self.images['eleve']
            },
            2:{
                "text":"Gestion COURS",
                "command":lambda:print("Gestion cours") ,
                "image":''
            }
        }
       

        for key,value in BTN.items():
           btn =CTkButton(sidebar,text=value['text'],font=FONT_TITLE,
                          fg_color=SIDEBAR_BG,text_color=SIDEBAR_TEXT,
                          command=value['command'],
                          hover_color=SIDEBAR_HOVER,border_width=5,
                          image=value['image'],compound=LEFT)
           btn.pack(fill=X,pady=5,padx=10,)

        

    def show_eleve_view(self):
        from views.eleves import EleveView
        #clear mainframe
        for widget in self.mainFrame.winfo_children():
            widget.destroy()
        eleve_view =EleveView(self.mainFrame)
        eleve_view.pack(fill=BOTH,expand=True)



if __name__ =="__main__":
    app =Acceuil()
    app.mainloop()
