import customtkinter as ctk
import fitz  # PyMuPDF
from PIL import Image, ImageTk

class PDFViewer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lecteur PDF Minimaliste")
        self.geometry("600x800")

        # 1. Ouvrir le document PDF
        self.pdf_doc = fitz.open(r"C:\Users\h4xgroover\Desktop\GESTION ECOLE\WEB\media\inscriptions\2nd\1b4eb5d8-4905-4b73-a171-89d15b3cfa88\Exercice_sur_le_bilan_.pdf")
        
        # 2. Charger la première page (index 0)
        page = self.pdf_doc.load_page(0)
        
        # 3. Convertir la page en "pixmap" (image)
        pix = page.get_pixmap()
        
        # 4. Transformer le pixmap en Image PIL
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 5. Convertir pour CustomTkinter
        self.photo = ctk.CTkImage(light_image=img, dark_image=img, size=(pix.width, pix.height))

        # 6. Afficher dans un Label
        self.label = ctk.CTkLabel(self, image=self.photo, text="")
        self.label.pack(pady=20, padx=20, fill="both", expand=True)

if __name__ == "__main__":
    app = PDFViewer()
    app.mainloop()