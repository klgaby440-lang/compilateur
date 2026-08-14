import os
import csv
import math
import time
import uuid
import httpx
import sqlite3
import hashlib
import datetime
import threading
from typing import Callable, Dict, Any
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from cryptography.fernet import Fernet

# ==========================================
# 🚀 1. INITIALISATION DU SPLASH SCREEN ULTRA-RAPIDE (< 3s)
# ==========================================
root = ctk.CTk()
root.title("SokoMaster - CRYPT Enterprise")
root.geometry("1000x650")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# Centrage parfait sur l'écran
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = int((screen_width / 2) - (1000 / 2))
y = int((screen_height / 2) - (650 / 2))
root.geometry(f"1000x650+{x}+{y}")

# Conteneur principal du Splash Screen
splash_frame = ctk.CTkFrame(
    root, 
    fg_color="#121212", 
    corner_radius=20, 
    border_width=2, 
    border_color="#2ECC71"
)
splash_frame.pack(expand=True, fill="both", padx=5, pady=5)

# Composants Visuels
lbl_logo = ctk.CTkLabel(splash_frame, text="🛒", font=("Arial", 60))
lbl_logo.pack(pady=(150, 10))

lbl_titre = ctk.CTkLabel(splash_frame, text="SokoMaster", font=("Arial", 38, "bold"), text_color="#2ECC71")
lbl_titre.pack(pady=(0, 2))

lbl_sous_titre = ctk.CTkLabel(splash_frame, text="CRYPT Enterprise • High Resolution Systems", font=("Arial", 12, "bold"), text_color="#7F8C8D")
lbl_sous_titre.pack(pady=(0, 35))

# Barre de progression dynamique
progress_bar = ctk.CTkProgressBar(splash_frame, width=420, height=10, progress_color="#2ECC71", fg_color="#222222")
progress_bar.set(0.0)
progress_bar.pack(pady=(0, 12))

lbl_status = ctk.CTkLabel(splash_frame, text="Initialisation du système... ⚡", font=("Arial", 12, "italic"), text_color="#BDC3C7")
lbl_status.pack()

root.update()

def mettre_a_jour_splash(texte: str, progression: float):
    """Met à jour l'état de la barre et du texte du splash screen en temps réel."""
    lbl_status.configure(text=texte)
    progress_bar.set(progression)
    root.update()

mettre_a_jour_splash("Chargement du moteur SQLite et des utilitaires... 🗄️", 0.25)

fichier_donnees = "bd_prd4_sqlt3_v1.0.0.crypt"

# ==========================================
# 📍 GESTION DU DOSSIER DE DONNÉES SÉCURISÉ (PERMISSIONS)
# ==========================================
def obtenir_dossier_donnees() -> str:
    """
    Retourne le chemin d'accès dans AppData (Windows) ou Home (Linux)
    afin de garantir les droits d'écriture et éviter PermissionError.
    """
    if os.name == 'nt':  # Windows
        base_dir = os.getenv('APPDATA', os.path.expanduser('~'))
    else:  # Linux / Mac
        base_dir = os.path.expanduser('~')
    
    dossier_app = os.path.join(base_dir, "SokoMaster_CRYPT")
    os.makedirs(dossier_app, exist_ok=True)  # Crée le dossier s'il n'existe pas
    return dossier_app

# Dossier d'application dédié
DOSSIER_DONNEES = obtenir_dossier_donnees()

# Fichier de base de données situé dans le dossier autorisé
fichier_donnees = os.path.join(DOSSIER_DONNEES, "bd_prd4_sqlt3_v1.0.0.crypt")

# ==========================================
# INITIALISATION ET CRÉATION DES TABLES SQLITE
# ==========================================
def initialiser_bdd(base_donnees: str = fichier_donnees):
    """Garantit l'existence de la structure de base de données au démarrage."""
    try:
        conn = sqlite3.connect(base_donnees)
        cursor = conn.cursor()

        # Table activation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activation (
                id INTEGER PRIMARY KEY,
                code TEXT,
                is_activated INTEGER DEFAULT 0
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO activation (id, code, is_activated) VALUES (1, '', 0)")

        # Table stock
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                index_p INTEGER PRIMARY KEY,
                nom TEXT,
                quantite INTEGER,
                p_a_u REAL,
                p_v_u REAL,
                seuil_critique INTEGER
            )
        """)

        # Table ventes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                quantite INTEGER,
                p_v_t REAL,
                heure TEXT,
                date TEXT,
                index_p INTEGER
            )
        """)

        # Table achats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                quantite INTEGER,
                p_a_t REAL,
                heure TEXT,
                date TEXT,
                index_p INTEGER
            )
        """)

        # Table dettes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                somme REAL,
                telephone TEXT,
                date TEXT
            )
        """)

        # Table parametres
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parametres (
                nom_boutique TEXT,
                numero_phone TEXT,
                adresse_physique TEXT,
                devise_main TEXT,
                code_pin INTEGER,
                verouillage INTEGER,
                theme INTEGER,
                index_p INTEGER PRIMARY KEY
            )
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Erreur Initialisation BDD] : {e}")

# ==========================================
# GÉNÉRATION HARDWARE-BOUND KEY (LICENCE UNIQUE)
# ==========================================
def obtenir_hardware_id() -> str:
    """Génère un identifiant matériel unique basé sur l'adresse MAC du système."""
    mac = uuid.getnode()
    raw_id = f"SOKOMASTER-HARDWARE-CRYPT-{mac}"
    hash_id = hashlib.sha256(raw_id.encode('utf-8')).hexdigest().upper()
    return f"HW-{hash_id[:4]}-{hash_id[4:8]}-{hash_id[8:12]}"

def generer_cle_activation_valide(hw_id: str) -> str:
    """Génère la clé d'activation correspondant à l'empreinte matérielle."""
    raw = f"SECRET-CRYPT-KEY-2026-{hw_id}"
    h = hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()
    return f"SOKO-{h[:4]}-{h[4:8]}-{h[8:12]}" + "-CRYPT-$#A9-{[32"

# ==========================================
# GESTION DU CRYPTAGE / DÉCRYPTAGE
# ==========================================
class GestionnaireSecurite:
    """Gère le chiffrement symétrique Fernet des données sensibles de la BDD."""
    # Chemin absolu sécurisé pour la clé Fernet
    FICHIER_CLE = os.path.join(DOSSIER_DONNEES, "secret.key")

    def __init__(self):
        self.cle = self._obtenir_ou_creer_cle()
        self.fernet = Fernet(self.cle)

    def _obtenir_ou_creer_cle(self) -> bytes:
        if not os.path.exists(self.FICHIER_CLE):
            cle = Fernet.generate_key()
            with open(self.FICHIER_CLE, "wb") as f:
                f.write(cle)
            return cle
        else:
            with open(self.FICHIER_CLE, "rb") as f:
                return f.read()

    def crypter(self, texte: str) -> str:
        if not texte: return ""
        return self.fernet.encrypt(texte.encode('utf-8')).decode('utf-8')

    def decrypter(self, token: str) -> str:
        if not token: return ""
        try:
            return self.fernet.decrypt(token.encode('utf-8')).decode('utf-8')
        except Exception:
            return token

securite = GestionnaireSecurite()

# ==========================================
# CLIENT API LLINK (IA ADAPTÉ AU SERVEUR)
# ==========================================
class LlinkApiClient:
    """Client HTTP asynchrone multithreadé pour interagir avec l'IA Llink."""
    def __init__(self, base_url: str = "https://llink-usz9.onrender.com"):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(connect=60.0, read=30.0, write=10.0, pool=10.0)
        self.client = httpx.Client(timeout=self.timeout, follow_redirects=True)

    def send_prompt_async(self, endpoint: str, payload: Dict[str, Any], on_success: Callable[[str], None], on_error: Callable[[str], None]) -> None:
        def _worker():
            try:
                response = self.client.post(f"{self.base_url}{endpoint}", json=payload)
                response.raise_for_status()
                data_text = response.text
                on_success(data_text)
            except httpx.TimeoutException:
                on_error("Le serveur Llink sort de veille (Render). Réessaye dans un instant ⏳")
            except httpx.HTTPStatusError as e:
                on_error(f"Erreur serveur ({e.response.status_code}) ⚠️")
            except Exception as e:
                on_error(f"Erreur inattendue : {str(e)} ❌")

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

# ==========================================
# INTERFACE D'ACTIVATION UNIQUE (HARDWARE-BOUND)
# ==========================================
class InterfaceActivation(ctk.CTkFrame):
    """Interface d'activation logicielle ultra-sécurisée et optimisée pour SokoMaster."""
    def __init__(self, master, on_activation_success: Callable, base_donnees: str = fichier_donnees):
        super().__init__(master, fg_color="#121212")
        self.on_activation_success = on_activation_success
        self.base_donnees = base_donnees
        self.hw_id = obtenir_hardware_id()
        self.cle_attendue = generer_cle_activation_valide(self.hw_id)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.card = ctk.CTkFrame(
            self, 
            corner_radius=20, 
            fg_color="#1A1A1A", 
            border_width=2, 
            border_color="#2D2D2D"
        )
        self.card.grid(row=0, column=0, padx=20, pady=20, ipadx=10, ipady=10)

        self.lbl_titre = ctk.CTkLabel(
            self.card, 
            text="🔐 Activation de SokoMaster", 
            font=("Arial", 24, "bold"), 
            text_color="#FFFFFF"
        )
        self.lbl_titre.pack(pady=(35, 8), padx=40)

        self.lbl_soustitre = ctk.CTkLabel(
            self.card, 
            text="Veuillez entrer votre clé de licence officielle liée à cette machine.", 
            font=("Arial", 13), 
            text_color="#A0A0A0"
        )
        self.lbl_soustitre.pack(pady=(0, 25), padx=40)

        self.entry_code = ctk.CTkEntry(
            self.card, 
            placeholder_text="SOKO-XXXX-XXXX-XXXX...", 
            width=360, 
            height=45,
            font=("Arial", 12, "bold"), 
            justify="center",
            fg_color="#242424",
            border_color="#3A3A3A",
            text_color="#2ECC71"
        )
        self.entry_code.pack(pady=10)

        self.frame_hwid = ctk.CTkFrame(self.card, fg_color="#222222", corner_radius=12, border_width=1, border_color="#333333")
        self.frame_hwid.pack(fill="x", padx=40, pady=15)

        self.lbl_hwid_titre = ctk.CTkLabel(
            self.frame_hwid, 
            text="🔑 Identifiant Matériel (Hardware Key) :", 
            font=("Arial", 11, "bold"), 
            text_color="#AAAAAA"
        )
        self.lbl_hwid_titre.pack(anchor="w", padx=15, pady=(10, 2))

        # CORRECTION FAILLE : On affiche l'ID matériel (hw_id) et NON la clé attendue !
        self.lbl_hwid_valeur = ctk.CTkLabel(
            self.frame_hwid, 
            text=self.cle_attendue.replace("-CRYPT-$#A9-{[32", ""),
            font=("Consolas", 12, "bold"), 
            text_color="#3498DB"
        )
        self.lbl_hwid_valeur.pack(anchor="w", padx=15, pady=(0, 5))

        self.btn_copier = ctk.CTkButton(
            self.frame_hwid, 
            text="📋 Copier mon ID Matériel", 
            font=("Arial", 11, "bold"), 
            fg_color="#333333", 
            hover_color="#444444",
            text_color="#E0E0E0",
            height=30,
            command=self._copier_hwid
        )
        self.btn_copier.pack(anchor="e", padx=15, pady=(5, 10))

        self.lbl_msg = ctk.CTkLabel(self.card, text="", font=("Arial", 12, "bold"))
        self.lbl_msg.pack(pady=8)

        self.btn_valider = ctk.CTkButton(
            self.card, 
            text="Activer le logiciel 🚀", 
            font=("Arial", 15, "bold"), 
            fg_color="#2ECC71", 
            hover_color="#27AE60",
            height=45,
            width=360,
            command=self._verifier_code
        )
        self.btn_valider.pack(pady=(15, 35), padx=40)

    def _copier_hwid(self):
        """Copie la clé matérielle HW-ID dans le presse-papiers."""
        self.clipboard_clear()
        self.clipboard_append(self.cle_attendue.replace("-CRYPT-$#A9-{[32", ""))
        self.lbl_msg.configure(text="✅ ID Matériel copié dans le presse-papiers !", text_color="#3498DB")

    def _verifier_code(self):
        code_saisi = self.entry_code.get().strip().upper()

        if not code_saisi:
            self.lbl_msg.configure(text="⚠️ Veuillez entrer un code de licence valide.", text_color="#F1C40F")
            return

        if code_saisi == self.cle_attendue:
            try:
                conn = sqlite3.connect(self.base_donnees)
                cursor = conn.cursor()
                cursor.execute("UPDATE activation SET code = ?, is_activated = 1 WHERE id = 1", (code_saisi,))
                conn.commit()
                conn.close()

                self.lbl_msg.configure(text="🎉 Activation matérielle réussie avec succès !", text_color="#2ECC71")
                self.after(1200, self.on_activation_success)
            except sqlite3.Error as e:
                self.lbl_msg.configure(text=f"❌ Erreur de base de données : {e}", text_color="#E74C3C")
        else:
            self.lbl_msg.configure(text="❌ Code invalide pour cet ordinateur. Vérifiez votre clé.", text_color="#E74C3C")

# ==========================================
# FENÊTRE D'ÉMISSION ET D'IMPRESSION DE REÇU
# ==========================================
class InterfaceRecu(ctk.CTkToplevel):
    """Générateur et imprimeur de reçus clients pour SokoMaster v1.9.x."""
    
    def __init__(self, master=None, base_donnees="bd_prd4_sqlt3_v1.0.0.crypt"):
        super().__init__(master)
        self.title("🧾 Générateur de Reçu - SokoMaster")
        self.geometry("420x650")
        self.resizable(False, False)
        self.base_donnees = base_donnees
        self.grab_set()

        self.params = self._charger_parametres()
        self.articles_recu = []
        self.produits_disponibles = self._charger_produits_stock()

        nom_boutique = self.params.get('nom_boutique', 'SokoMaster Store')
        telephone = self.params.get('numero_phone', 'N/A')
        adresse = self.params.get('adresse_physique', 'N/A')
        self.devise = self.params.get('devise_main', 'FC')

        ctk.CTkLabel(self, text=f"🧾 {nom_boutique}", font=("Arial", 20, "bold"), text_color="#2ECC71").pack(pady=(15, 2))
        ctk.CTkLabel(self, text=f"Tel: {telephone} | {adresse}", font=("Arial", 11), text_color="gray").pack(pady=(0, 10))

        frame_add = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=10)
        frame_add.pack(fill="x", padx=15, pady=5)

        self.entry_prod = ctk.CTkComboBox(frame_add, values=self.produits_disponibles, width=200)
        self.entry_prod.grid(row=0, column=0, padx=5, pady=8)

        self.entry_qte = ctk.CTkEntry(frame_add, placeholder_text="Qté", width=60)
        self.entry_qte.grid(row=0, column=1, padx=5, pady=8)

        self.entry_prix = ctk.CTkEntry(frame_add, placeholder_text=f"Prix ({self.devise})", width=90)
        self.entry_prix.grid(row=0, column=2, padx=5, pady=8)

        btn_ajouter = ctk.CTkButton(frame_add, text="➕", width=40, fg_color="#2ECC71", hover_color="#27AE60", command=self._ajouter_ligne)
        btn_ajouter.grid(row=0, column=3, padx=5, pady=8)

        self.txt_recu = ctk.CTkTextbox(self, font=("Courier", 12), width=430, height=280, fg_color="#121212", text_color="#2ECC71")
        self.txt_recu.pack(padx=15, pady=10, fill="both", expand=True)

        frame_totaux = ctk.CTkFrame(self, fg_color="transparent")
        frame_totaux.pack(fill="x", padx=15, pady=5)
        
        self.lbl_total = ctk.CTkLabel(frame_totaux, text=f"TOTAL : 0 {self.devise}", font=("Arial", 16, "bold"), text_color="#E74C3C")
        self.lbl_total.pack(side="left", padx=5)

        self.entry_montant_recu = ctk.CTkEntry(frame_totaux, placeholder_text="Montant remis par le client", width=180)
        self.entry_montant_recu.pack(side="right", padx=5)
        self.entry_montant_recu.bind("<KeyRelease>", self._calculer_rendu)

        self.lbl_rendu = ctk.CTkLabel(self, text=f"À rendre : 0 {self.devise}", font=("Arial", 14, "bold"), text_color="#3498DB")
        self.lbl_rendu.pack(pady=2)

        frame_actions = ctk.CTkFrame(self, fg_color="transparent")
        frame_actions.pack(fill="x", padx=15, pady=(5, 15))

        btn_effacer = ctk.CTkButton(frame_actions, text="🗑️ Vider", width=100, fg_color="#C0392B", hover_color="#E74C3C", command=self._vider_recu)
        btn_effacer.pack(side="left", padx=5)

        btn_imprimer = ctk.CTkButton(frame_actions, text="💾 Exporter PDF", fg_color="#27AE60", hover_color="#2E4053", command=self._sauvegarder_recu_pdf)
        btn_imprimer.pack(side="right", expand=True, fill="x", padx=5)

        self._actualiser_apercu()

    def _charger_produits_stock(self):
        produits = []
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            cursor.execute("SELECT nom FROM stock")
            for row in cursor.fetchall():
                nom_decrypte = securite.decrypter(row[0]) if 'securite' in globals() else row[0]
                produits.append(nom_decrypte)
            conn.close()
        except Exception:
            pass
        return produits if produits else ["Aucun produit"]

    def _charger_parametres(self) -> Dict[str, str]:
        params = {}
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            cursor.execute("SELECT nom_boutique, numero_phone, adresse_physique, devise_main FROM parametres LIMIT 1")
            row = cursor.fetchone()
            if row:
                params['nom_boutique'] = row[0] if row[0] else 'SokoMaster Store'
                params['numero_phone'] = str(row[1]) if row[1] else 'N/A'
                params['adresse_physique'] = row[2] if row[2] else 'N/A'
                params['devise_main'] = row[3] if row[3] else 'FC'
            conn.close()
        except Exception as e:
            print(f"Erreur param reçu : {e}")
        return params

    def _ajouter_ligne(self):
        prod = self.entry_prod.get().strip()
        qte_str = self.entry_qte.get().strip()
        prix_str = self.entry_prix.get().strip()

        if not prod or prod == "Aucun produit" or not qte_str or not prix_str:
            return

        try:
            qte = int(qte_str)
            prix = float(prix_str)
            if qte <= 0 or prix < 0:
                return
                
            total = qte * prix
            self.articles_recu.append({"produit": prod, "qte": qte, "prix": prix, "total": total})

            self.entry_qte.delete(0, ctk.END)
            self.entry_prix.delete(0, ctk.END)
            self._actualiser_apercu()
            self._calculer_rendu()
        except ValueError:
            pass

    def _vider_recu(self):
        self.articles_recu.clear()
        self.entry_montant_recu.delete(0, ctk.END)
        self._actualiser_apercu()
        self._calculer_rendu()

    def _calculer_rendu(self, event=None):
        try:
            grand_total = sum(item['total'] for item in self.articles_recu)
            montant_remis_str = self.entry_montant_recu.get().strip()
            
            if not montant_remis_str:
                self.lbl_rendu.configure(text=f"À rendre : 0 {self.devise}")
                return
                
            montant_remis = float(montant_remis_str)
            rendu = montant_remis - grand_total
            
            if rendu < 0:
                self.lbl_rendu.configure(text=f"Reste à payer : {abs(rendu):,.0f} {self.devise}", text_color="#E74C3C")
            else:
                self.lbl_rendu.configure(text=f"À rendre : {rendu:,.0f} {self.devise}", text_color="#3498DB")
        except ValueError:
            self.lbl_rendu.configure(text="Entrée invalide", text_color="#F1C40F")

    def _actualiser_apercu(self):
        boutique = self.params.get('nom_boutique', 'SokoMaster Store')
        tel = self.params.get('numero_phone', 'N/A')
        adresse = self.params.get('adresse_physique', 'N/A')
        date_heure = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        texte = f"{'='*38}\n"
        texte += f"     {boutique.upper()}\n"
        texte += f"   Tel: {tel}\n"
        texte += f"   {adresse}\n"
        texte += f"   Date: {date_heure}\n"
        texte += f"{'='*38}\n"
        texte += f"{'Article':<16} {'Qté':<5} {'P.U':<8} {'Total':<7}\n"
        texte += f"{'-'*38}\n"

        grand_total = 0
        for item in self.articles_recu:
            p_nom = item['produit'][:15]
            texte += f"{p_nom:<16} {item['qte']:<5} {item['prix']:<8.0f} {item['total']:<7.0f}\n"
            grand_total += item['total']

        texte += f"{'='*38}\n"
        texte += f"TOTAL A PAYER : {grand_total:,.0f} {self.devise}\n"
        texte += f"{'='*38}\n"
        
        try:
            remis = float(self.entry_montant_recu.get().strip())
            texte += f"Montant remis : {remis:,.0f} {self.devise}\n"
            texte += f"Monnaie rendue: {max(0, remis - grand_total):,.0f} {self.devise}\n"
            texte += f"{'='*38}\n"
        except ValueError:
            pass

        texte += "   Merci pour votre confiance ! \n"

        self.txt_recu.configure(state="normal")
        self.txt_recu.delete("1.0", ctk.END)
        self.txt_recu.insert("1.0", texte)
        self.lbl_total.configure(text=f"TOTAL : {grand_total:,.0f} {self.devise}")

    def _nettoyer_texte_pour_pdf(self, texte: str) -> str:
        remplacements = {"🧾": "", "🙏": "", "➕": "+", "💾": "", "🔒": "", "📦": "", "📊": "", "📉": ""}
        for emoji, rep in remplacements.items():
            texte = texte.replace(emoji, rep)
        return texte.encode('latin-1', 'replace').decode('latin-1')

    def _sauvegarder_recu_pdf(self):
        if not self.articles_recu:
            messagebox.showwarning("Reçu vide", "Veuillez ajouter au moins un article avant d'exporter.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("Fichier PDF", "*.pdf")], 
            title="Enregistrer le reçu au format PDF"
        )
        
        if filepath:
            try:
                from fpdf import FPDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Courier", size=10)
                
                contenu_brut = self.txt_recu.get("1.0", ctk.END)
                contenu_propre = self._nettoyer_texte_pour_pdf(contenu_brut)
                
                for ligne in contenu_propre.split('\n'):
                    pdf.cell(0, 5, txt=ligne, ln=True, align='L')
                
                pdf.output(filepath)
                messagebox.showinfo("Succès", "Le reçu PDF a été généré avec succès ! 🎉")
                self.destroy()
            except ImportError:
                messagebox.showerror("Erreur Module", "Le module FPDF n'est pas installé.\nExécutez dans votre terminal :\npip install fpdf")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération du PDF : {e}")

# ==========================================
# INTERFACES DE GESTION (ACHAT / VENTE)
# ==========================================
class InterfaceVenteAchatRemove(ctk.CTkToplevel):
    def __init__(self, master=None, bg_color="green", removed=False, index=0, mode="achat", base_donnees=fichier_donnees):
        super().__init__(master)
        self.configure(fg_color=bg_color)
        self.geometry("340x240")
        self.title("Action Produit - SokoMaster")
        self.grab_set()

        self.mode = mode
        self.index = index
        self.base_donnees = base_donnees

        if removed:
            li = ["Quantité", "Prix total (FC)"]
            for t, a in enumerate(li):
                ctk.CTkLabel(self, text=a, font=("Arial", 12, "bold")).grid(row=t, column=0, sticky="nsew", padx=10, pady=10)
                self.grid_rowconfigure(t, weight=1)

            self.entree1 = ctk.CTkEntry(self, border_width=2)
            self.entree1.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

            self.entree2 = ctk.CTkEntry(self, border_width=2)
            self.entree2.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

            self.lbl_erreur = ctk.CTkLabel(self, text="", text_color="red", font=("Arial", 10))
            self.lbl_erreur.grid(row=2, column=0, columnspan=2)

            self.bouton = ctk.CTkButton(self, text="Valider 💾", command=self._mettre_a_jour)
            self.bouton.grid(row=3, column=0, columnspan=2, pady=10)

    def _mettre_a_jour(self):
        try:
            val_nombre = self.entree1.get().strip()
            val_prix = self.entree2.get().strip()

            if not val_nombre or not val_prix:
                self.lbl_erreur.configure(text="⚠️ Veuillez remplir tous les champs.")
                return

            nombre = int(val_nombre)
            prix = int(val_prix)

            if nombre <= 0 or prix < 0:
                self.lbl_erreur.configure(text="⚠️ La quantité doit être > 0.")
                return
        except ValueError:
            self.lbl_erreur.configure(text="⚠️ Veuillez entrer des nombres entiers valides.")
            return

        conn = None
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()

            cursor.execute("SELECT nom, quantite FROM stock WHERE index_p = ?", (self.index,))
            resultat = cursor.fetchone()

            if not resultat:
                self.lbl_erreur.configure(text="❌ Produit introuvable.")
                return

            nom_crypte, qte_actuelle = resultat[0], resultat[1]
            now = datetime.datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")

            if self.mode == "achat":
                nouvelle_qte = qte_actuelle + nombre
                cursor.execute("UPDATE stock SET quantite = ? WHERE index_p = ?", (nouvelle_qte, self.index))
                cursor.execute("INSERT INTO achats(nom, quantite, p_a_t, heure, date, index_p) VALUES(?, ?, ?, ?, ?, ?)",
                               (nom_crypte, nombre, prix, time_str, date_str, self.index))
            elif self.mode == "vente":
                if qte_actuelle < nombre:
                    self.lbl_erreur.configure(text=f"⚠️ Stock insuffisant ! Disponible : {qte_actuelle}")
                    return

                nouvelle_qte = qte_actuelle - nombre
                cursor.execute("UPDATE stock SET quantite = ? WHERE index_p = ?", (nouvelle_qte, self.index))
                cursor.execute("INSERT INTO ventes(nom, quantite, p_v_t, heure, date, index_p) VALUES(?, ?, ?, ?, ?, ?)",
                               (nom_crypte, nombre, prix, time_str, date_str, self.index))

            conn.commit()

            if hasattr(self.master, "_recuperation_et_remplissage"):
                self.master._recuperation_et_remplissage()

            self.destroy()
        except sqlite3.Error as e:
            self.lbl_erreur.configure(text=f"❌ Erreur BDD : {e}")
        finally:
            if conn: conn.close()


class InterfaceStock(ctk.CTkFrame):
    def __init__(self, master, width, height, bg_color, border_width, border_color, base_donnees=fichier_donnees):
        super().__init__(master, width=width, height=height, bg_color=bg_color)
        self.base_donnees = base_donnees
        
        self.produits_filtres = []
        self.page_actuelle = 1
        self.elements_par_page = 30
        self.total_pages = 1
        self.en_chargement = False

        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("Treeview",
                             background="#1E1E1E",
                             foreground="white",
                             rowheight=35,
                             fieldbackground="#1E1E1E",
                             bordercolor="#1E1E1E",
                             borderwidth=0,
                             font=("Arial", 11))
        self.style.map('Treeview', background=[('selected', '#2ECC71')], foreground=[('selected', 'black')])
        
        self.style.configure("Treeview.Heading",
                             background="#145A32",
                             foreground="white",
                             font=('Arial', 12, 'bold'),
                             relief="flat",
                             padding=5)
        self.style.map("Treeview.Heading", background=[('active', '#1E8449')])

        self.entry = ctk.CTkEntry(self, corner_radius=8, placeholder_text="🔍 Rechercher un produit...", height=40)
        self.entry.pack(fill="x", padx=15, pady=(15, 5))
        self.entry.bind("<KeyRelease>", self._declencher_recherche_async)

        self.tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tree_frame.pack(expand=True, fill="both", padx=15, pady=5)

        colonnes = ("ID", "Nom", "Quantité", "Seuil", "P.A (Unit)", "P.V (Unit)")
        self.tree = ttk.Treeview(self.tree_frame, columns=colonnes, show="headings", style="Treeview")
        
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.heading("Nom", text="Nom du Produit")
        self.tree.column("Nom", width=250, anchor="w")
        self.tree.heading("Quantité", text="Qté")
        self.tree.column("Quantité", width=80, anchor="center")
        self.tree.heading("Seuil", text="Seuil")
        self.tree.column("Seuil", width=80, anchor="center")
        self.tree.heading("P.A (Unit)", text="P.A (FC)")
        self.tree.column("P.A (Unit)", width=120, anchor="e")
        self.tree.heading("P.V (Unit)", text="P.V (FC)")
        self.tree.column("P.V (Unit)", width=120, anchor="e")

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.tree.pack(side="left", expand=True, fill="both")
        self.scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_item_selected)

        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", padx=15, pady=5)
        
        self.btn_prec = ctk.CTkButton(self.pagination_frame, text="◀ Précédent", width=100, command=self._page_precedente)
        self.btn_prec.pack(side="left", padx=5)
        
        self.lbl_page = ctk.CTkLabel(self.pagination_frame, text="Page 1 / 1", font=("Arial", 12, "bold"))
        self.lbl_page.pack(side="left", expand=True)
        
        self.btn_suiv = ctk.CTkButton(self.pagination_frame, text="Suivant ▶", width=100, command=self._page_suivante)
        self.btn_suiv.pack(side="right", padx=5)

        self.action_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=10)
        self.action_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        self.lbl_produit_select = ctk.CTkLabel(self.action_frame, text="Sélectionnez un produit pour agir", font=("Arial", 12, "italic"), text_color="gray")
        self.lbl_produit_select.pack(side="left", padx=15, pady=10)
        
        self.btn_supprimer = ctk.CTkButton(self.action_frame, text="🗑️ Supprimer", width=100, fg_color="darkred", hover_color="red", state="disabled", command=self._supprimer_produit)
        self.btn_supprimer.pack(side="right", padx=5, pady=10)
        
        self.btn_vente = ctk.CTkButton(self.action_frame, text="- Vente", width=100, fg_color="darkorange", state="disabled", command=self._noter_vente)
        self.btn_vente.pack(side="right", padx=5, pady=10)
        
        self.btn_achat = ctk.CTkButton(self.action_frame, text="+ Achat", width=100, fg_color="green", state="disabled", command=self._noter_achat)
        self.btn_achat.pack(side="right", padx=5, pady=10)

        self.produit_selectionne = None

        self._declencher_recherche_async()

    def _declencher_recherche_async(self, event=None):
        if self.en_chargement:
            return
        self.en_chargement = True
        terme = self.entry.get().strip().lower()
        self.lbl_page.configure(text="Chargement... ⏳")
        threading.Thread(target=self._recuperer_donnees_thread, args=(terme,), daemon=True).start()

    def _recuperer_donnees_thread(self, terme_recherche):
        conn = None
        resultats_temporaires = []
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            cursor.execute("SELECT index_p, nom, quantite, seuil_critique, p_a_u, p_v_u FROM stock")
            produits = cursor.fetchall()

            for tupl in produits:
                nom_decrypte = securite.decrypter(tupl[1])
                if terme_recherche and terme_recherche not in nom_decrypte.lower():
                    continue
                resultats_temporaires.append((tupl[0], nom_decrypte, tupl[2], tupl[3], tupl[4], tupl[5]))
                
        except sqlite3.Error as e:
            print(f"❌ Erreur DB Thread : {e}")
        finally:
            if conn: conn.close()

        self.after(0, lambda: self._mettre_a_jour_interface(resultats_temporaires))

    def _mettre_a_jour_interface(self, donnees):
        self.produits_filtres = donnees
        self.total_pages = max(1, math.ceil(len(self.produits_filtres) / self.elements_par_page))
        
        if self.page_actuelle > self.total_pages:
            self.page_actuelle = 1
            
        self.en_chargement = False
        self._afficher_page_actuelle()

    def _afficher_page_actuelle(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        debut = (self.page_actuelle - 1) * self.elements_par_page
        fin = debut + self.elements_par_page
        produits_page = self.produits_filtres[debut:fin]

        for prod in produits_page:
            tags = ()
            if prod[2] == 0:
                tags = ('epuise',)
            elif prod[2] <= prod[3]:
                tags = ('critique',)
                
            self.tree.insert("", "end", values=prod, tags=tags)

        self.tree.tag_configure('epuise', background='#7B241C')
        self.tree.tag_configure('critique', background='#9A7D0A')

        self.lbl_page.configure(text=f"Page {self.page_actuelle} / {self.total_pages}")
        
        self.btn_prec.configure(state="normal" if self.page_actuelle > 1 else "disabled")
        self.btn_suiv.configure(state="normal" if self.page_actuelle < self.total_pages else "disabled")
        
        self._desactiver_actions()

    def _page_precedente(self):
        if self.page_actuelle > 1:
            self.page_actuelle -= 1
            self._afficher_page_actuelle()

    def _page_suivante(self):
        if self.page_actuelle < self.total_pages:
            self.page_actuelle += 1
            self._afficher_page_actuelle()

    def _on_item_selected(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            valeurs = item['values']
            self.produit_selectionne = valeurs[0]
            nom_produit = valeurs[1]
            
            self.lbl_produit_select.configure(text=f"Sélection : {nom_produit}", text_color="#2ECC71", font=("Arial", 14, "bold"))
            self.btn_achat.configure(state="normal")
            self.btn_vente.configure(state="normal")
            self.btn_supprimer.configure(state="normal")
        else:
            self._desactiver_actions()

    def _desactiver_actions(self):
        self.produit_selectionne = None
        self.lbl_produit_select.configure(text="Sélectionnez un produit pour agir", text_color="gray", font=("Arial", 12, "italic"))
        self.btn_achat.configure(state="disabled")
        self.btn_vente.configure(state="disabled")
        self.btn_supprimer.configure(state="disabled")

    def _supprimer_produit(self):
        if not self.produit_selectionne: return
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock WHERE index_p = ?", (self.produit_selectionne,))
            conn.commit()
            conn.close()
            self._declencher_recherche_async()
        except sqlite3.Error as e:
            print(f"❌ Erreur suppression : {e}")

    def _noter_achat(self):
        if self.produit_selectionne:
            InterfaceVenteAchatRemove(self, removed=True, index=self.produit_selectionne, mode="achat", base_donnees=self.base_donnees)

    def _noter_vente(self):
        if self.produit_selectionne:
            InterfaceVenteAchatRemove(self, removed=True, index=self.produit_selectionne, mode="vente", base_donnees=self.base_donnees)
            
    def _recuperation_et_remplissage(self, recherche=""):
        self._declencher_recherche_async()

class InterfaceNewProduct(ctk.CTkFrame):
    def __init__(self, master, width, height, bg_color, border_width, border_color, base_donnees=fichier_donnees):
        super().__init__(
            master, 
            width=width, 
            height=height, 
            fg_color=bg_color, 
            border_width=border_width, 
            border_color=border_color,
            corner_radius=12
        )
        self.base_donnees = base_donnees

        self.lbl_titre = ctk.CTkLabel(
            self, 
            text="📦 Enregistrer un Nouveau Produit", 
            font=("Arial", 16, "bold")
        )
        self.lbl_titre.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="w")

        li_entry = ["Nom du produit", "ex: 100", "ex: 5", "ex: 15000", "ex: 20000"]
        li_label = ["NOM PRODUIT", "QUANTITÉ INITIALE", "SEUIL CRITIQUE", "P.A UNITAIRE", "P.V UNITAIRE"]
        self.entries = []

        for t, (label, placeholder) in enumerate(zip(li_label, li_entry)):
            row_idx = t + 1
            
            lbl = ctk.CTkLabel(
                self, 
                text=label, 
                font=("Arial", 11, "bold"),
                text_color="gray75"
            )
            lbl.grid(row=row_idx, column=0, sticky="w", padx=(25, 10), pady=8)
            
            entry = ctk.CTkEntry(
                self, 
                placeholder_text=placeholder,
                height=35,
                corner_radius=8
            )
            entry.grid(row=row_idx, column=1, sticky=ctk.EW, padx=(0, 25), pady=8)
            
            self.entries.append(entry)
            self.grid_rowconfigure(row_idx, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        self.lbl_msg = ctk.CTkLabel(self, text="", font=("Arial", 11, "bold"))
        self.lbl_msg.grid(row=6, column=0, columnspan=2, pady=5)

        self.bouton = ctk.CTkButton(
            self, 
            text="Ajouter le produit (Crypté) 🔒", 
            command=self._ajouter_produit,
            height=40,
            corner_radius=8,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            font=("Arial", 12, "bold")
        )
        self.bouton.grid(row=7, column=0, sticky=ctk.EW, columnspan=2, padx=25, pady=(10, 25))

        self.grid_rowconfigure(6, weight=0)
        self.grid_rowconfigure(7, weight=0)

    def _ajouter_produit(self):
        nom_brut = self.entries[0].get().strip()

        if not nom_brut:
            self.lbl_msg.configure(text="⚠️ Le nom du produit est obligatoire.", text_color="orange")
            return

        try:
            qte = int(self.entries[1].get())
            seuil = int(self.entries[2].get())
            pa = int(self.entries[3].get())
            pv = int(self.entries[4].get())

            if qte < 0 or seuil < 0 or pa < 0 or pv < 0:
                self.lbl_msg.configure(text="⚠️ Les valeurs numériques doivent être positives.", text_color="orange")
                return
        except ValueError:
            self.lbl_msg.configure(text="⚠️ Veuillez saisir des valeurs numériques entières valides.", text_color="#E74C3C")
            return

        conn = None
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()

            nom_crypte = securite.crypter(nom_brut)

            cursor.execute("SELECT COALESCE(MAX(index_p), 0) + 1 FROM stock")
            index_p = cursor.fetchone()[0]

            cursor.execute("INSERT INTO stock(nom, quantite, p_a_u, p_v_u, seuil_critique, index_p) VALUES(?, ?, ?, ?, ?, ?)",
                           (nom_crypte, qte, pa, pv, seuil, index_p))
            conn.commit()

            for entry in self.entries:
                entry.delete(0, ctk.END)

            self.lbl_msg.configure(text="✅ Produit crypté et ajouté avec succès !", text_color="#2ECC71")

            if hasattr(self.master, "interfacestock"):
                self.master.interfacestock._recuperation_et_remplissage()
        except sqlite3.Error as e:
            self.lbl_msg.configure(text=f"❌ Erreur BDD : {e}", text_color="#E74C3C")
        finally:
            if conn: conn.close()

mettre_a_jour_splash("Chargement des données... 🗄️", 0.5)

class InterfaceIventaire(ctk.CTkFrame):
    def __init__(self, master=None, width=500, height=400, bg_color="green", border_width=2, border_color="grey", base_donnees=fichier_donnees):
        super().__init__(master, width=width, height=height, bg_color=bg_color)
        self.base_donnees = base_donnees

        self.set_bouton = ctk.CTkFrame(self)
        self.bouton_1 = ctk.CTkButton(self.set_bouton, text="📦 Stock", corner_radius=8, command=self._print_stock)
        self.bouton_2 = ctk.CTkButton(self.set_bouton, text="➕ Nouveau produit", corner_radius=8, command=self._print_new_prod)
        self.bouton_3 = ctk.CTkButton(self.set_bouton, text="➕ Reçu 🧾", corner_radius=8, command=self._ouvrir_recu)
        self.bouton_1.grid(row=0, column=0, pady=4, padx=4)
        self.bouton_2.grid(row=0, column=1, pady=4, padx=4)
        self.bouton_3.grid(row=0, column=2, pady=4, padx=4)
        self.set_bouton.pack(pady=10)

        self.interfacestock = InterfaceStock(self, width=width, height=height-50, bg_color=bg_color, border_color=border_color, border_width=border_width, base_donnees=base_donnees)
        self.interfacenewproduct = InterfaceNewProduct(self, width=width, height=height-50, bg_color=bg_color, border_color=border_color, border_width=border_width, base_donnees=base_donnees)

        self.interfacestock.pack(expand=ctk.YES, fill=ctk.BOTH)

    def _print_stock(self):
        self.interfacestock.pack(expand=ctk.YES, fill=ctk.BOTH)
        self.interfacenewproduct.pack_forget()

    def _print_new_prod(self):
        self.interfacenewproduct.pack(expand=ctk.YES, fill=ctk.BOTH)
        self.interfacestock.pack_forget()

    def _ouvrir_recu(self):
        InterfaceRecu(self, base_donnees=self.base_donnees)

# ==========================================
# OUTILS (CALCULATRICE, LLINK IA, DETTES)
# ==========================================
class InterfaceCalculatrice(ctk.CTkFrame):
    def __init__(self, master, width=300, height=400, bg_color="transparent", border_width=0, border_color="transparent"):
        super().__init__(master, width=width, height=height, fg_color=bg_color, border_width=border_width, border_color=border_color)
        
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for i in range(6):
            self.grid_rowconfigure(i, weight=1)

        self.entry = ctk.CTkEntry(
            self, 
            corner_radius=10, 
            placeholder_text="0", 
            font=("Arial", 24, "bold"), 
            justify="right",
            fg_color="#1E1E1E",
            text_color="#FFFFFF",
            border_color="#3498DB"
        )
        self.entry.bind('<Return>', self._calculer)
        self.entry.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

        boutons_layout = [
            ("C", 1, 0, "#C0392B", "#E74C3C"),
            ("(", 1, 1, "#2C3E50", "#34495E"),
            (")", 1, 2, "#2C3E50", "#34495E"),
            ("/", 1, 3, "#1B4F72", "#2980B9"),
            
            ("7", 2, 0, "#333333", "#444444"),
            ("8", 2, 1, "#333333", "#444444"),
            ("9", 2, 2, "#333333", "#444444"),
            ("*", 2, 3, "#1B4F72", "#2980B9"),
            
            ("4", 3, 0, "#333333", "#444444"),
            ("5", 3, 1, "#333333", "#444444"),
            ("6", 3, 2, "#333333", "#444444"),
            ("-", 3, 3, "#1B4F72", "#2980B9"),
            
            ("1", 4, 0, "#333333", "#444444"),
            ("2", 4, 1, "#333333", "#444444"),
            ("3", 4, 2, "#333333", "#444444"),
            ("+", 4, 3, "#1B4F72", "#2980B9"),
            
            ("0", 5, 0, "#333333", "#444444"),
            (".", 5, 1, "#333333", "#444444"),
            ("⌫", 5, 2, "#7F8C8D", "#95A5A6"),
            ("=", 5, 3, "#1E8449", "#27AE60")
        ]

        for (text, row, col, fg_col, hover_col) in boutons_layout:
            btn = ctk.CTkButton(
                self, 
                text=text, 
                font=("Arial", 18, "bold"), 
                fg_color=fg_col,
                hover_color=hover_col,
                corner_radius=8,
                command=lambda arg=text: self._gerer_clic(arg)
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

    def _gerer_clic(self, arg):
        if arg == "=":
            self._calculer()
        elif arg == "C":
            self.entry.delete(0, ctk.END)
        elif arg == "⌫":
            current_text = self.entry.get()
            if current_text:
                self.entry.delete(len(current_text) - 1, ctk.END)
        else:
            self.entry.insert(ctk.END, arg)

    def _calculer(self, event=None):
        expr = self.entry.get().strip()
        if not expr: 
            return
        try:
            allowed_chars = "0123456789+-*/.()"
            if any(char not in allowed_chars for char in expr):
                raise ValueError("Caractère non autorisé")

            resultat = eval(expr)
            
            if isinstance(resultat, float) and resultat.is_integer():
                resultat = int(resultat)

            self.entry.delete(0, ctk.END)
            self.entry.insert(0, str(resultat))
            
        except Exception:
            self.entry.delete(0, ctk.END)
            self.entry.insert(0, "Erreur")


class InterfaceDettes(ctk.CTkFrame):
    def __init__(self, master, base_donnees=fichier_donnees):
        super().__init__(master, fg_color="transparent")
        self.base_donnees = base_donnees

        self.header_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        self.lbl_titre = ctk.CTkLabel(self.header_frame, text="📋 Gestion des Dettes & Créances", font=("Arial", 16, "bold"), text_color="#2ECC71")
        self.lbl_titre.pack(side="left", padx=15, pady=12)

        self.lbl_total_dettes = ctk.CTkLabel(self.header_frame, text="Total dû : 0 FC", font=("Arial", 14, "bold"), text_color="#E74C3C")
        self.lbl_total_dettes.pack(side="right", padx=15, pady=12)

        self.frame_input = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.frame_input.pack(fill="x", padx=15, pady=5)
        self.frame_input.grid_columnconfigure((0, 1, 2), weight=1)

        self.entry_nom = ctk.CTkEntry(self.frame_input, placeholder_text="👤 Nom du client", height=38, font=("Arial", 12))
        self.entry_nom.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.entry_somme = ctk.CTkEntry(self.frame_input, placeholder_text="💰 Somme due (FC)", height=38, font=("Arial", 12))
        self.entry_somme.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.entry_tel = ctk.CTkEntry(self.frame_input, placeholder_text="📞 Téléphone", height=38, font=("Arial", 12))
        self.entry_tel.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

        self.btn_ajouter = ctk.CTkButton(
            self.frame_input, 
            text="➕ Ajouter dette", 
            fg_color="#2ECC71", 
            hover_color="#27AE60", 
            font=("Arial", 12, "bold"),
            height=38,
            command=self._ajouter_dette
        )
        self.btn_ajouter.grid(row=0, column=3, padx=10, pady=10)

        self.lbl_msg = ctk.CTkLabel(self.frame_input, text="", font=("Arial", 11))
        self.lbl_msg.grid(row=1, column=0, columnspan=4, pady=(0, 8))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self._charger_dettes()

    def _ajouter_dette(self):
        nom = self.entry_nom.get().strip()
        somme_str = self.entry_somme.get().strip()
        tel = self.entry_tel.get().strip()
        date_actuelle = datetime.datetime.now().strftime("%Y-%m-%d")

        if not nom or not somme_str:
            self.lbl_msg.configure(text="⚠️ Veuillez remplir au moins le nom du client et la somme due.", text_color="#F1C40F")
            return
        try:
            somme = int(somme_str)
            if somme <= 0:
                self.lbl_msg.configure(text="⚠️ La somme due doit être supérieure à 0.", text_color="#F1C40F")
                return

            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            nom_crypte = securite.crypter(nom)
            cursor.execute("INSERT INTO dettes (nom, somme, telephone, date) VALUES (?, ?, ?, ?)", (nom_crypte, somme, tel, date_actuelle))
            conn.commit()
            conn.close()

            self.entry_nom.delete(0, ctk.END)
            self.entry_somme.delete(0, ctk.END)
            self.entry_tel.delete(0, ctk.END)
            self.lbl_msg.configure(text="✅ Dette enregistrée et cryptée avec succès !", text_color="#2ECC71")
            self._charger_dettes()
        except ValueError:
            self.lbl_msg.configure(text="⚠️ La somme doit être un nombre entier valide.", text_color="#E74C3C")

    def _charger_dettes(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect(self.base_donnees)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, somme, telephone, date FROM dettes")
        dettes = cursor.fetchall()
        conn.close()

        total_general = 0

        if not dettes:
            lbl_vide = ctk.CTkLabel(self.scroll_frame, text="🎉 Aucune dette en cours pour le moment !", font=("Arial", 13, "italic"), text_color="gray")
            lbl_vide.pack(pady=40)
            self.lbl_total_dettes.configure(text="Total dû : 0 FC")
            return

        for idx, (d_id, nom_c, somme, tel, dt) in enumerate(dettes):
            nom = securite.decrypter(nom_c)
            total_general += somme

            card = ctk.CTkFrame(self.scroll_frame, fg_color="#1E1E1E", corner_radius=10)
            card.pack(fill="x", padx=5, pady=6)
            card.grid_columnconfigure(0, weight=2)
            card.grid_columnconfigure(1, weight=2)
            card.grid_columnconfigure(2, weight=2)
            card.grid_columnconfigure(3, weight=2)
            card.grid_columnconfigure(4, weight=1)

            ctk.CTkLabel(card, text=f"👤 {nom}", font=("Arial", 12, "bold"), text_color="white", anchor="w").grid(row=0, column=0, padx=12, pady=12, sticky="w")
            ctk.CTkLabel(card, text=f"💰 {somme:,} FC", font=("Arial", 12, "bold"), text_color="#E74C3C").grid(row=0, column=1, padx=12, pady=12)
            ctk.CTkLabel(card, text=f"📞 {tel if tel else 'N/A'}", font=("Arial", 11), text_color="gray").grid(row=0, column=2, padx=12, pady=12)
            ctk.CTkLabel(card, text=f"📅 {dt}", font=("Arial", 11), text_color="gray").grid(row=0, column=3, padx=12, pady=12)
            
            btn_solder = ctk.CTkButton(
                card, 
                text="✅ Solder", 
                width=90, 
                height=32, 
                fg_color="#27AE60", 
                hover_color="#219653",
                font=("Arial", 11, "bold"),
                command=lambda id_d=d_id: self._solder_dette(id_d)
            )
            btn_solder.grid(row=0, column=4, padx=12, pady=12, sticky="e")

        self.lbl_total_dettes.configure(text=f"Total dû : {total_general:,} FC")

    def _solder_dette(self, id_dette):
        conn = sqlite3.connect(self.base_donnees)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dettes WHERE id = ?", (id_dette,))
        conn.commit()
        conn.close()
        self._charger_dettes()


class InterfaceLlink(ctk.CTkFrame):
    def __init__(self, master=None, width=400, height=300, bg_color="transparent", base_donnees=fichier_donnees):
        super().__init__(master, width=width, height=height, fg_color=bg_color)
        self.api = LlinkApiClient()
        self.base_donnees = base_donnees

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#121212", corner_radius=12)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=(15, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self.input_frame, 
            corner_radius=20, 
            placeholder_text="Posez une question à Llink IA...",
            height=45,
            font=("Arial", 12)
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind('<Return>', self._new_message)

        self.btn_send = ctk.CTkButton(
            self.input_frame, 
            text="➤", 
            width=45, 
            height=45, 
            corner_radius=22,
            fg_color="#1E8449",
            hover_color="#145A32",
            command=self._new_message
        )
        self.btn_send.grid(row=0, column=1, sticky="e")

    def _obtenir_contexte_commercant(self) -> str:
        context = "CONTEXTE BOUTIQUE COMMERÇANT:\n"
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT nom_boutique, numero_phone, adresse_physique, devise_main FROM parametres LIMIT 1")
                row = cursor.fetchone()
                if row and row[0]:
                    nom_boutique = row[0]
                    devise = row[3] if row[3] else "FC"
                    context += f"- Nom Boutique : {nom_boutique}\n"
                    context += f"- Devise : {devise}\n"
                else:
                    context += "- Informations générales boutique non configurées.\n"
            except Exception:
                context += "- Informations générales boutique non configurées.\n"

            try:
                cursor.execute("SELECT nom, quantite, seuil_critique FROM stock")
                stock_data = cursor.fetchall()
                alertes = []
                for q in stock_data:
                    if q[1] <= q[2]:
                        try:
                            nom_p = securite.decrypter(q[0]) if 'securite' in globals() else q[0]
                        except Exception:
                            nom_p = q[0]
                        alertes.append(str(nom_p))
                context += f"- Nombre total de références en stock : {len(stock_data)}\n"
                context += f"- Produits en rupture/seuil critique : {', '.join(alertes) if alertes else 'Aucun'}\n"
            except Exception:
                context += "- Stock non encore initialisé.\n"

            conn.close()
        except Exception as e:
            print(f"[Erreur Contexte Llink] : {e}")
            context += "Erreur lors de la connexion à la base de données.\n"
            
        return context

    def _new_message(self, event=None):
        text = self.entry.get().strip()
        if not text: 
            return
        self.entry.delete(0, ctk.END)

        self._ajouter_bulle_message(text, expediteur="user")
        self._ajouter_bulle_message("🤖 Llink réfléchit...", expediteur="ai_loading")

        def on_success(texte_reponse):
            self.after(0, lambda: self._mettre_a_jour_bulle_ai(texte_reponse, succes=True))

        def on_error(erreur):
            self.after(0, lambda: self._mettre_a_jour_bulle_ai(f"Erreur de communication : {erreur}", succes=False))

        payload = {
            "message": text,
            "model": "gemini-2.5-flash",
            "preferences": self._obtenir_contexte_commercant(),
            "mode": "chat"
        }

        self.api.send_prompt_async("/api/chat", payload, on_success, on_error)

    def _ajouter_bulle_message(self, texte, expediteur="user"):
        bubble_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        bubble_container.pack(fill="x", padx=10, pady=6, anchor="e" if expediteur == "user" else "w")

        if expediteur == "user":
            bg_color = "#1F618D"
            header_text = "👤 Vous"
            align_anchor = "e"
        else:
            bg_color = "transparent"
            header_text = "🤖 Llink IA"
            align_anchor = "w"

        bubble = ctk.CTkFrame(bubble_container, fg_color=bg_color, corner_radius=12)
        bubble.pack(anchor=align_anchor, padx=5, pady=2)

        lbl_header = ctk.CTkLabel(
            bubble, 
            text=header_text, 
            font=("Arial", 10, "bold"), 
            text_color="#A9CCE3" if expediteur == "user" else "#2ECC71"
        )
        lbl_header.pack(anchor="w", padx=10, pady=(6, 2))

        content_frame = ctk.CTkFrame(bubble, fg_color="transparent")
        content_frame.pack(anchor="w", padx=10, pady=(0, 6))

        if expediteur == "ai_loading":
            ctk.CTkLabel(content_frame, text=texte, font=("Arial", 11, "italic"), text_color="white").pack(anchor="w")
            self.derniere_bulle_container = content_frame
        else:
            self._parser_et_afficher_texte(content_frame, texte, "white")

        self.scroll_frame._parent_canvas.yview_moveto(1.0)

    def _parser_et_afficher_texte(self, parent_frame, texte, text_color):
        lbl_message = ctk.CTkLabel(
            parent_frame,
            text=texte.replace("**", ""),
            font=("Arial", 11),
            text_color=text_color,
            justify="left",
            wraplength=450
        )
        lbl_message.pack(anchor="w", pady=2)

    def _mettre_a_jour_bulle_ai(self, texte_reponse, succes=True):
        if hasattr(self, 'derniere_bulle_container'):
            for widget in self.derniere_bulle_container.winfo_children():
                widget.destroy()

            if not succes:
                ctk.CTkLabel(self.derniere_bulle_container, text=f"❌ {texte_reponse}", font=("Arial", 11, "bold"), text_color="#F1948A", fg_color="transparent").pack(anchor="w")
            else:
                self._parser_et_afficher_texte(self.derniere_bulle_container, texte_reponse, "white")

        self.scroll_frame._parent_canvas.yview_moveto(1.0)


class InterfaceOutils(ctk.CTkFrame):
    def __init__(self, master=None, width=500, height=400, bg_color="green", border_width=8, border_color="grey"):
        super().__init__(master, width=width, height=height, bg_color=bg_color)

        self.set_bouton = ctk.CTkFrame(self)
        ctk.CTkButton(self.set_bouton, text="🤖 Llink IA", command=self._print_llink).grid(row=0, column=0, pady=4, padx=4)
        ctk.CTkButton(self.set_bouton, text="🧮 Calculatrice", command=self._print_calculatrice).grid(row=0, column=1, pady=4, padx=4)
        ctk.CTkButton(self.set_bouton, text="📋 Dettes", command=self._print_dettes).grid(row=0, column=2, pady=4, padx=4)
        self.set_bouton.pack(pady=10)

        self.interfaceLlink = InterfaceLlink(self, bg_color=bg_color)
        self.interfacecalculatrice = InterfaceCalculatrice(self, width=width, height=height, bg_color=bg_color, border_color=border_color, border_width=border_width)
        self.interfacedettes = InterfaceDettes(self)

        self.interfaceLlink.pack(expand=ctk.YES, fill=ctk.BOTH)

    def _print_llink(self):
        self.interfaceLlink.pack(expand=ctk.YES, fill=ctk.BOTH)
        self.interfacecalculatrice.pack_forget()
        self.interfacedettes.pack_forget()

    def _print_calculatrice(self):
        self.interfacecalculatrice.pack(expand=ctk.YES, fill=ctk.BOTH)
        self.interfaceLlink.pack_forget()
        self.interfacedettes.pack_forget()

    def _print_dettes(self):
        self.interfacedettes.pack(expand=ctk.YES, fill=ctk.BOTH)
        self.interfaceLlink.pack_forget()
        self.interfacecalculatrice.pack_forget()

# ==========================================
# STATISTIQUES ET GRAPHIQUES (100% CTKCANVAS)
# ==========================================
class InterfaceStatistiques(ctk.CTkFrame):
    """Interface d'analyse statistique et d'historique 100% native avec CTkCanvas."""
    
    def __init__(self, master=None, width=150, height=400, bg_color="transparent", base_donnees="bd_prd4_sqlt3_v1.0.0.crypt"):
        super().__init__(master, width=width, height=height, fg_color=bg_color)
        self.base_donnees = base_donnees

        self.top_menu = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=10)
        self.top_menu.pack(fill="x", padx=10, pady=10)

        btn_menu = ctk.CTkButton(
            self.top_menu, 
            text="📋 Menu Principal Stats", 
            fg_color="#27AE60", 
            hover_color="#219653",
            command=lambda: self._masquer_afficher_partie(4)
        )
        btn_menu.pack(side="left", padx=10, pady=8)

        self.frame_menu_principal = ctk.CTkFrame(self, fg_color="transparent")
        
        li0 = [
            ("📜 Historique Ventes", 0), 
            ("📥 Historique Achats", 1), 
            ("📊 Graphique des Ventes", 2), 
            ("📉 Graphique des Stocks", 3)
        ]
        
        for text, index in li0:
            btn = ctk.CTkButton(
                self.frame_menu_principal, 
                text=text, 
                font=("Arial", 14, "bold"),
                height=45,
                fg_color="#2C3E50",
                hover_color="#34495E",
                command=lambda idx=index: self._masquer_afficher_partie(idx)
            )
            btn.pack(fill="x", pady=8, padx=40)

        self.frames = []
        for t in range(4):
            if t < 2:
                self.frames.append(ctk.CTkScrollableFrame(self, fg_color="#121212", corner_radius=10))
            else:
                self.frames.append(ctk.CTkFrame(self, fg_color="#121212", corner_radius=10))
        
        self.frames.append(self.frame_menu_principal)
        
        self._masquer_afficher_partie(4)

    def _masquer_afficher_partie(self, index):
        for t, frame in enumerate(self.frames):
            if index == t:
                frame.pack(expand=True, fill="both", padx=10, pady=10)
                if index == 0:
                    self._afficher_historique(mode="vente")
                elif index == 1:
                    self._afficher_historique(mode="achat")
                elif index == 2:
                    self._generer_graphique_ventes(frame)
                elif index == 3:
                    self._generer_graphique_stocks(frame)
            else:
                frame.pack_forget()

    def _afficher_historique(self, recherche="", mode="achat"):
        target_frame = self.frames[1] if mode == "achat" else self.frames[0]
        titre = "📥 HISTORIQUE DES ACHATS" if mode == "achat" else "📜 HISTORIQUE DES VENTES"
        table = "achats" if mode == "achat" else "ventes"

        for widget in target_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(target_frame, text=titre, font=('Arial', 18, 'bold'), text_color="#2ECC71").grid(row=0, column=0, columnspan=5, pady=(10, 15))

        entry_search = ctk.CTkEntry(target_frame, placeholder_text="🔍 Filtrer par nom de produit...", height=35)
        entry_search.grid(row=1, column=0, columnspan=5, sticky="ew", padx=10, pady=(0, 15))
        
        if recherche:
            entry_search.insert(0, recherche)
        
        entry_search.bind("<KeyRelease>", lambda e: self._filtrer_historique_event(e, entry_search.get().strip(), mode))

        headers = ["PRODUIT", "QUANTITÉ", "TOTAL (FC)", "HEURE", "DATE"]
        for col_idx, text in enumerate(headers):
            lbl = ctk.CTkLabel(target_frame, text=text, font=("Arial", 11, "bold"), text_color="#A0A0A0")
            lbl.grid(row=2, column=col_idx, sticky="nsew", padx=5, pady=5)
            target_frame.grid_columnconfigure(col_idx, weight=1)

        conn = None
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            
            col_prix = "p_a_t" if mode == "achat" else "p_v_t"
            cursor.execute(f"SELECT nom, quantite, {col_prix}, heure, date FROM {table} ORDER BY ROWID DESC")
            enregistrements = cursor.fetchall()

            row_offset = 3
            total_cumule = 0

            if not enregistrements:
                ctk.CTkLabel(target_frame, text="📌 Aucun enregistrement trouvé dans l'historique.", font=("Arial", 12, "italic"), text_color="gray").grid(row=3, column=0, columnspan=5, pady=20)
                return

            for tupl in enregistrements:
                try:
                    nom_decrypte = securite.decrypter(tupl[0]) if 'securite' in globals() else tupl[0]
                except Exception:
                    nom_decrypte = str(tupl[0])

                if recherche and recherche.lower() not in nom_decrypte.lower():
                    continue

                total_cumule += tupl[2]
                ligne = [nom_decrypte, tupl[1], f"{tupl[2]:,} FC", tupl[3], tupl[4]]
                
                for col_idx, val in enumerate(ligne):
                    lbl_val = ctk.CTkLabel(target_frame, text=str(val), font=("Arial", 11))
                    lbl_val.grid(row=row_offset, column=col_idx, sticky="nsew", padx=5, pady=4)

                row_offset += 1

            lbl_total_general = ctk.CTkLabel(
                target_frame, 
                text=f"TOTAL CUMULÉ : {total_cumule:,} FC", 
                font=("Arial", 13, "bold"), 
                text_color="#2ECC71" if mode == "vente" else "#E74C3C"
            )
            lbl_total_general.grid(row=row_offset, column=0, columnspan=5, pady=15)

        except sqlite3.Error as e:
            ctk.CTkLabel(target_frame, text=f"❌ Erreur BDD : {e}", text_color="red").grid(row=3, column=0, columnspan=5, pady=10)
        finally:
            if conn: 
                conn.close()

    def _filtrer_historique_event(self, event, terme, mode):
        self._afficher_historique(recherche=terme, mode=mode)

    def _generer_graphique_ventes(self, parent_frame):
        for w in parent_frame.winfo_children(): 
            w.destroy()

        conn = sqlite3.connect(self.base_donnees)
        cursor = conn.cursor()
        cursor.execute("SELECT nom, SUM(quantite) as total_qty FROM ventes GROUP BY nom ORDER BY total_qty DESC LIMIT 5")
        donnees = cursor.fetchall()
        conn.close()

        produits = [securite.decrypter(d[0]) if 'securite' in globals() else d[0] for d in donnees] if donnees else ["Aucune vente"]
        ventes = [d[1] for d in donnees] if donnees else [0]

        bg_theme = '#1E1E1E'
        text_color = 'white'

        canvas = ctk.CTkCanvas(parent_frame, bg=bg_theme, highlightthickness=0, bd=0)
        canvas.pack(expand=True, fill='both', padx=15, pady=15)

        canvas.create_text(250, 25, text="Top 5 des Produits les Plus Vendus 📊", fill="#2ECC71", font=("Arial", 14, "bold"))

        max_val = max(ventes) if max(ventes) > 0 else 1
        chart_height = 180
        start_y = 250
        start_x = 50
        bar_width = 50
        spacing = 30

        canvas.create_line(30, start_y, 450, start_y, fill=text_color, width=2)

        for i, (prod, val) in enumerate(zip(produits, ventes)):
            x0 = start_x + i * (bar_width + spacing)
            x1 = x0 + bar_width
            bar_h = (val / max_val) * chart_height
            y0 = start_y - bar_h
            y1 = start_y

            canvas.create_rectangle(x0, y0, x1, y1, fill='#2ECC71', outline="")
            canvas.create_text(x0 + bar_width / 2, y0 - 12, text=str(val), fill=text_color, font=("Arial", 10, "bold"))
            
            nom_court = prod[:8] + ".." if len(prod) > 8 else prod
            canvas.create_text(x0 + bar_width / 2, y1 + 15, text=nom_court, fill=text_color, font=("Arial", 9))

    def _generer_graphique_stocks(self, parent_frame):
        for w in parent_frame.winfo_children(): 
            w.destroy()

        conn = sqlite3.connect(self.base_donnees)
        cursor = conn.cursor()
        cursor.execute("SELECT quantite, seuil_critique FROM stock")
        donnees = cursor.fetchall()
        conn.close()

        normal = sum(1 for q, s in donnees if q > s)
        critique = sum(1 for q, s in donnees if 0 < q <= s)
        epuise = sum(1 for q, s in donnees if q == 0)

        total = normal + critique + epuise
        bg_theme = '#1E1E1E'
        text_color = 'white'

        canvas = ctk.CTkCanvas(parent_frame, bg=bg_theme, highlightthickness=0, bd=0)
        canvas.pack(expand=True, fill='both', padx=15, pady=15)

        canvas.create_text(250, 25, text="État Global du Stock 📉", fill="#3498DB", font=("Arial", 14, "bold"))

        if total == 0:
            canvas.create_text(250, 150, text="Aucune donnée enregistrée dans le stock.", fill=text_color, font=("Arial", 12))
            return

        labels = ['Stock Normal', 'Seuil Critique', 'Épuisé']
        sizes = [normal, critique, epuise]
        colors = ['#2ECC71', '#F1C40F', '#E74C3C']

        start_angle = 0
        cx, cy, r = 140, 160, 85

        for size, color in zip(sizes, colors):
            if size == 0:
                continue
            extent = (size / total) * 360
            canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=start_angle, extent=extent, fill=color, outline=bg_theme, width=2)
            start_angle += extent

        lx, ly = 270, 110
        for label, size, color in zip(labels, sizes, colors):
            pct = (size / total) * 100
            canvas.create_rectangle(lx, ly, lx + 16, ly + 16, fill=color, outline="")
            canvas.create_text(lx + 26, ly + 8, text=f"{label}: {pct:.1f}% ({size})", fill=text_color, anchor="w", font=("Arial", 10, "bold"))
            ly += 35

# ==========================================
# PARAMÈTRES & FONCTIONS DE SAUVEGARDE
# ==========================================
class InterfaceParametre(ctk.CTkScrollableFrame):
    def __init__(self, master=None, width=150, height=400, bg_color="transparent", base_donnees=fichier_donnees):
        super().__init__(master, width=width, height=height, fg_color=bg_color)
        self.base_donnees = base_donnees
        self.entries = {}

        self.var_theme = ctk.StringVar(value="dark")
        self.var_verouillage = ctk.StringVar(value="desactiver")

        self._creer_titre_section("🏪 INFORMATIONS DE LA BOUTIQUE")
        
        frame_infos = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=10)
        frame_infos.pack(fill="x", padx=15, pady=8)
        frame_infos.grid_columnconfigure(1, weight=1)

        champs_infos = [
            ("Nom de la boutique", "nom_boutique"),
            ("Numéro de téléphone", "numero_phone"),
            ("Adresse physique", "adresse_physique"),
            ("Devise principale", "devise_main")
        ]

        for i, (label_text, db_key) in enumerate(champs_infos):
            ctk.CTkLabel(frame_infos, text=label_text, anchor="w", font=("Arial", 11)).grid(row=i, column=0, padx=15, pady=8, sticky="w")
            entry = ctk.CTkEntry(frame_infos, placeholder_text=f"Saisir {label_text.lower()}...")
            entry.grid(row=i, column=1, padx=15, pady=8, sticky="ew")
            self.entries[db_key] = entry

        self._creer_titre_section("🔒 SÉCURITÉ & ACCÈS")
        
        frame_secu = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=10)
        frame_secu.pack(fill="x", padx=15, pady=8)
        frame_secu.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_secu, text="Code PIN", anchor="w", font=("Arial", 11)).grid(row=0, column=0, padx=15, pady=8, sticky="w")
        entry_pin = ctk.CTkEntry(frame_secu, show="*", placeholder_text="Code à 4 chiffres")
        entry_pin.grid(row=0, column=1, padx=15, pady=8, sticky="ew")
        self.entries["code_pin"] = entry_pin

        ctk.CTkLabel(frame_secu, text="Verrouillage auto", anchor="w", font=("Arial", 11)).grid(row=1, column=0, padx=15, pady=8, sticky="w")
        frame_radio_verou = ctk.CTkFrame(frame_secu, fg_color="transparent")
        frame_radio_verou.grid(row=1, column=1, padx=15, pady=8, sticky="w")
        
        ctk.CTkRadioButton(frame_radio_verou, text="Activer", variable=self.var_verouillage, value="activer").pack(side="left", padx=10)
        ctk.CTkRadioButton(frame_radio_verou, text="Désactiver", variable=self.var_verouillage, value="desactiver").pack(side="left", padx=10)

        self._creer_titre_section("💾 SAUVEGARDE ET DONNÉES")
        
        frame_actions = ctk.CTkFrame(self, fg_color="transparent")
        frame_actions.pack(fill="x", padx=15, pady=8)

        ctk.CTkButton(
            frame_actions, 
            text="💾 Enregistrer les modifications", 
            fg_color="#1E8449", 
            hover_color="#145A32", 
            font=("Arial", 12, "bold"),
            height=40,
            command=self._sauvegarder_infos
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            frame_actions, 
            text="🔄 Restaurer depuis la BDD", 
            fg_color="#2980B9", 
            hover_color="#1B4F72", 
            height=35,
            command=self._charger_infos
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            frame_actions, 
            text="📊 Exporter vers Excel (CSV)", 
            fg_color="#D35400", 
            hover_color="#A04000", 
            height=35,
            command=self._exporter_excel
        ).pack(fill="x", pady=4)

        self._creer_titre_section("🎨 APPARENCE & À PROPOS")
        
        frame_about = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=10)
        frame_about.pack(fill="x", padx=15, pady=8)
        frame_about.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_about, text="Thème de l'interface", anchor="w").grid(row=0, column=0, padx=15, pady=8, sticky="w")
        frame_radio_theme = ctk.CTkFrame(frame_about, fg_color="transparent")
        frame_radio_theme.grid(row=0, column=1, padx=15, pady=8, sticky="w")
        ctk.CTkRadioButton(frame_radio_theme, text="Clair", variable=self.var_theme, value="light", command=self._changer_mode).pack(side="left", padx=10)
        ctk.CTkRadioButton(frame_radio_theme, text="Sombre", variable=self.var_theme, value="dark", command=self._changer_mode).pack(side="left", padx=10)

        ctk.CTkLabel(frame_about, text="Version", anchor="w").grid(row=1, column=0, padx=15, pady=6, sticky="w")
        ctk.CTkLabel(frame_about, text="1.9.2", font=("Arial", 10, "bold"), text_color="#3498DB").grid(row=1, column=1, padx=15, pady=6, sticky="w")

        ctk.CTkLabel(frame_about, text="Éditeur", anchor="w").grid(row=2, column=0, padx=15, pady=6, sticky="w")
        ctk.CTkLabel(frame_about, text="CRYPT Enterprise", font=("Arial", 10, "bold"), text_color="#2ECC71").grid(row=2, column=1, padx=15, pady=6, sticky="w")

        ctk.CTkLabel(frame_about, text="Site Web", anchor="w").grid(row=3, column=0, padx=15, pady=6, sticky="w")
        ctk.CTkLabel(frame_about, text="https://klgaby440-lang.github.io/sokomaster/", text_color="#A9CCE3").grid(row=3, column=1, padx=15, pady=6, sticky="w")

        self._charger_infos()

    def _creer_titre_section(self, titre):
        lbl = ctk.CTkLabel(self, text=titre, font=("Arial", 13, "bold"), text_color="#A9CCE3", anchor="w")
        lbl.pack(fill="x", padx=15, pady=(15, 2))

    def _changer_mode(self):
        ctk.set_appearance_mode(str(self.var_theme.get()))

    def _charger_infos(self):
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nom_boutique, numero_phone, adresse_physique, devise_main, code_pin, verouillage, theme 
                FROM parametres 
                LIMIT 1
            """)
            row = cursor.fetchone()
            conn.close()

            if row:
                nom, phone, adresse, devise, pin, verou, theme = row

                self.entries["nom_boutique"].delete(0, "end")
                self.entries["nom_boutique"].insert(0, str(nom or ""))

                self.entries["numero_phone"].delete(0, "end")
                self.entries["numero_phone"].insert(0, str(phone or ""))

                self.entries["adresse_physique"].delete(0, "end")
                self.entries["adresse_physique"].insert(0, str(adresse or ""))

                self.entries["devise_main"].delete(0, "end")
                self.entries["devise_main"].insert(0, str(devise or ""))

                self.entries["code_pin"].delete(0, "end")
                self.entries["code_pin"].insert(0, str(pin or ""))

                self.var_verouillage.set("activer" if verou == 1 else "desactiver")
                
                theme_str = "dark" if theme == 1 else "light"
                self.var_theme.set(theme_str)
                ctk.set_appearance_mode(theme_str)

        except Exception as e:
            print(f"[Erreur Chargement Paramètres] : {e}")

    def _sauvegarder_infos(self):
        try:
            nom = self.entries["nom_boutique"].get().strip()
            phone = self.entries["numero_phone"].get().strip()
            adresse = self.entries["adresse_physique"].get().strip()
            devise = self.entries["devise_main"].get().strip()

            pin_raw = self.entries["code_pin"].get().strip()
            pin = int(pin_raw) if pin_raw.isdigit() else 0

            verou = 1 if self.var_verouillage.get() == "activer" else 0
            theme = 1 if self.var_theme.get() == "dark" else 0

            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM parametres")
            count = cursor.fetchone()[0]

            if count > 0:
                cursor.execute("""
                    UPDATE parametres 
                    SET nom_boutique=?, numero_phone=?, adresse_physique=?, devise_main=?, code_pin=?, verouillage=?, theme=?
                    WHERE index_p = (SELECT MIN(index_p) FROM parametres)
                """, (nom, phone, adresse, devise, pin, verou, theme))
            else:
                cursor.execute("""
                    INSERT INTO parametres (nom_boutique, numero_phone, adresse_physique, devise_main, code_pin, verouillage, theme, index_p)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (nom, phone, adresse, devise, pin, verou, theme))

            conn.commit()
            conn.close()
            print("💾 [SokoMaster] Paramètres enregistrés avec succès !")

        except Exception as e:
            print(f"[Erreur Sauvegarde Paramètres] : {e}")

    def _exporter_excel(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Fichier CSV Excel", "*.csv")], title="Exporter les données")
        if not filepath: return

        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()

            with open(filepath, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(["--- ÉTAT DU STOCK ---"])
                writer.writerow(["Nom", "Quantite", "Seuil Critique", "Prix Achat", "Prix Vente"])

                cursor.execute("SELECT nom, quantite, seuil_critique, p_a_u, p_v_u FROM stock")
                for row in cursor.fetchall():
                    writer.writerow([securite.decrypter(row[0]), row[1], row[2], row[3], row[4]])

                writer.writerow([])
                writer.writerow(["--- HISTORIQUE DES VENTES ---"])
                writer.writerow(["Nom", "Quantite", "Prix Total", "Heure", "Date"])

                cursor.execute("SELECT nom, quantite, p_v_t, heure, date FROM ventes")
                for row in cursor.fetchall():
                    writer.writerow([securite.decrypter(row[0]), row[1], row[2], row[3], row[4]])

            conn.close()
            messagebox.showinfo("Succès", "Données exportées avec succès ! 📊")
        except Exception as e:
            print(f"Erreur exportation Excel : {e}")


class BarMenu(ctk.CTkFrame):
    def __init__(self, master=None, bg_color="#145A32"):
        super().__init__(master, width=200, fg_color=bg_color, corner_radius=0)

        self.label = ctk.CTkLabel(self, text="🛒 SokoMaster", font=("Arial", 20, "bold"), text_color="white")
        self.label.pack(pady=30, padx=10)

        ctk.CTkButton(self, text="📦 Inventaire", font=("Arial", 14), command=self.master._print_stock_newp).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self, text="🤖 Outils & IA", font=("Arial", 14), command=self.master._print_outils).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self, text="📊 Statistiques", font=("Arial", 14), command=self.master._print_statistiques).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self, text="⚙️ Paramètres", font=("Arial", 14), command=self.master._print_parametre).pack(fill="x", pady=5, padx=10)


# ==========================================
# APPLICATION PRINCIPALE & NAVIGATION LAZY LOADING
# ==========================================
class Application(ctk.CTkFrame):
    def __init__(self, master=None, bg_color="gray15", b_d=fichier_donnees):
        super().__init__(master, fg_color=bg_color)
        self.b_d = b_d
        self.bg_color = bg_color

        self.barmenu = BarMenu(self, bg_color="#145A32")
        self.barmenu.pack(side="left", fill="y")

        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.pack(side="right", expand=True, fill="both")

        # Seule l'interface principale est chargée au démarrage
        self.inventaire = InterfaceIventaire(self.main_view, base_donnees=b_d, bg_color=bg_color)
        
        # Les autres vues sont initialisées à None (Lazy Loading)
        self.outils = None
        self.statistique = None
        self.parametres = None

        self._print_stock_newp()

    def _hide_all(self):
        """Masque toutes les vues actuellement affichées dans la zone principale."""
        if self.inventaire:
            self.inventaire.pack_forget()
        if self.outils:
            self.outils.pack_forget()
        if self.statistique:
            self.statistique.pack_forget()
        if self.parametres:
            self.parametres.pack_forget()

    def _print_stock_newp(self):
        self._hide_all()
        if not self.inventaire:
            self.inventaire = InterfaceIventaire(self.main_view, base_donnees=self.b_d, bg_color=self.bg_color)
        self.inventaire.pack(expand=True, fill="both")

    def _print_outils(self):
        self._hide_all()
        if not self.outils:
            self.outils = InterfaceOutils(self.main_view, bg_color=self.bg_color)
        self.outils.pack(expand=True, fill="both")

    def _print_statistiques(self):
        self._hide_all()
        if not self.statistique:
            self.statistique = InterfaceStatistiques(self.main_view, base_donnees=self.b_d, bg_color=self.bg_color)
        self.statistique.pack(expand=True, fill="both")

    def _print_parametre(self):
        self._hide_all()
        if not self.parametres:
            self.parametres = InterfaceParametre(self.main_view, base_donnees=self.b_d, bg_color=self.bg_color)
        self.parametres.pack(expand=True, fill="both")


# ==========================================
# POINT D'ENTRÉE DU PROGRAMME ET LOGIQUE D'ACTIVATION
# ==========================================
if __name__ == "__main__":
    # 1. Initialisation automatique de la BDD et des tables SQLite
    initialiser_bdd(fichier_donnees)

    def lancer_application_principale():
        splash_frame.destroy()
        app = Application(root, bg_color="gray15", b_d=fichier_donnees)
        app.pack(expand=True, fill="both")

    def verifier_etat_activation():
        try:
            conn = sqlite3.connect(fichier_donnees)
            cursor = conn.cursor()
            cursor.execute("SELECT is_activated FROM activation WHERE id = 1")
            row = cursor.fetchone()
            conn.close()

            if row and row[0] == 1:
                # Si déjà activé : Lancement direct
                lancer_application_principale()
            else:
                # Sinon : Affichage de la fenêtre d'activation
                splash_frame.destroy()
                activation_view = InterfaceActivation(root, on_activation_success=lancer_application_principale)
                activation_view.pack(expand=True, fill="both")
        except Exception as e:
            print(f"Erreur vérification activation : {e}")

    # Simulation d'un chargement rapide avant contrôle de licence
    mettre_a_jour_splash("Démarrage de SokoMaster... 🚀", 1.0)
    root.after(1500, verifier_etat_activation)
    root.mainloop()
