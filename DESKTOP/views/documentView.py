from tkinter import messagebox

import fitz  # PyMuPDF
from PIL import Image
from customtkinter import CTkImage
# from customtkinter import 

def DocView(documentpath):
    """Fonctiono qui va se charger de transformer le document pdf en image pixamp

    Args:
        documentpath (str | path): lien vers le document 

    Returns:
        Image: L'image pixamp retourner
    """
    if documentpath=="" or documentpath ==None:
        messagebox.showerror("Erreur","Lien vers le document introuvable")
    else:

        try:
            document =fitz.open(documentpath)  #ouvrir le document pdf
            page =document.load_page(0) #charger la premiere page du pdf
            pix =page.get_pixmap() #converir la page en pixmap
            #transformer le pixmap en image PIL
            img =Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
            imgctk =CTkImage(light_image=img,dark_image =img,size =(pix.width,pix.height))
            print(pix.width,pix.height)
            
            return imgctk

        except Exception as e:
            messagebox.showerror("Erreur","Erreur de chargement du document ")
            # return None