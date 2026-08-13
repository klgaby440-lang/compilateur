import customtkinter as ctk
import sqlite3
import os
import threading
import httpx
import uuid
import hashlib
import csv
from tkinter import filedialog
from typing import Callable, Dict, Any
import datetime

# Cryptage sécurisé
from cryptography.fernet import Fernet

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

fichier_donnees = "bd_prd4_sqlt3_v1.0.0.crypt"

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
    return f"SOKO-{h[:4]}-{h[4:8]}-{h[8:12]}"

# ==========================================
# GESTION DU CRYPTAGE / DÉCRYPTAGE
# ==========================================
class GestionnaireSecurite:
    """Gère le chiffrement symétrique Fernet des données sensibles de la BDD."""
    FICHIER_CLE = "secret.key"

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
            return token  # Retourne le texte brut si ce n'était pas crypté

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
                # Adaptation au format de réponse brut (Text/Streaming) du serveur FastAPI
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
    def __init__(self, master, on_activation_success: Callable, base_donnees: str = fichier_donnees):
        super().__init__(master)
        self.on_activation_success = on_activation_success
        self.base_donnees = base_donnees
        self.hw_id = obtenir_hardware_id()
        self.cle_attendue = generer_cle_activation_valide(self.hw_id)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.card = ctk.CTkFrame(self, corner_radius=15, fg_color="#1E1E1E")
        self.card.grid(row=0, column=0, padx=20, pady=20)

        ctk.CTkLabel(self.card, text="🔐 Activation de SokoMaster", font=("Arial", 22, "bold")).pack(pady=(30, 10), padx=30)
        ctk.CTkLabel(self.card, text="Veuillez entrer votre code de licence lié à cette machine.", font=("Arial", 12), text_color="gray").pack(pady=(0, 15), padx=30)

        self.entry_code = ctk.CTkEntry(self.card, placeholder_text="SOKO-XXXX-XXXX-XXXX", width=320, font=("Arial", 14), justify="center")
        self.entry_code.pack(pady=10)

        # Affichage de l'ID matériel en dessous du champ de saisie
        self.lbl_hwid = ctk.CTkLabel(self.card, text=f"🔑 Clé Matérielle (Hardware Key) :\n{self.cle_attendue}", font=("Arial", 12, "bold"), text_color="#2ECC71")
        self.lbl_hwid.pack(pady=10)

        self.lbl_msg = ctk.CTkLabel(self.card, text="", font=("Arial", 12))
        self.lbl_msg.pack(pady=5)

        self.btn_valider = ctk.CTkButton(self.card, text="Activer le logiciel 🚀", font=("Arial", 14, "bold"), command=self._verifier_code)
        self.btn_valider.pack(pady=(10, 30))

    def _verifier_code(self):
        code_saisi = self.entry_code.get().strip().upper()
        print(self.cle_attendue)

        if code_saisi == self.cle_attendue:
            try:
                conn = sqlite3.connect(self.base_donnees)
                cursor = conn.cursor()
                cursor.execute("UPDATE activation SET code = ?, is_activated = 1 WHERE id = 1", (code_saisi,))
                conn.commit()
                conn.close()

                self.lbl_msg.configure(text="✅ Activation matérielle réussie !", text_color="green")
                self.after(1000, self.on_activation_success)
            except sqlite3.Error as e:
                self.lbl_msg.configure(text=f"❌ Erreur BDD : {e}", text_color="red")
        else:
            self.lbl_msg.configure(text="❌ Code invalide pour cet ordinateur.", text_color="red")

# ==========================================
# FENÊTRE D'ÉMISSION ET D'IMPRESSION DE REÇU
# ==========================================
class InterfaceRecu(ctk.CTkToplevel):
    def __init__(self, master=None, base_donnees=fichier_donnees):
        super().__init__(master)
        self.title("🧾 Générateur de Reçu - SokoMaster")
        self.geometry("450x600")
        self.base_donnees = base_donnees
        self.grab_set()

        self.params = self._charger_parametres()
        self.articles_recu = []

        ctk.CTkLabel(self, text=f"🧾 {self.params.get('nom_boutique', 'SokoMaster Store')}", font=("Arial", 18, "bold")).pack(pady=(15, 2))
        ctk.CTkLabel(self, text=f"Tel: {self.params.get('telephone', 'N/A')} | {self.params.get('adresse', 'N/A')}", font=("Arial", 10), text_color="gray").pack(pady=(0, 10))

        # Zone d'ajout d'article sur le reçu
        frame_add = ctk.CTkFrame(self)
        frame_add.pack(fill="x", padx=15, pady=5)

        self.entry_prod = ctk.CTkEntry(frame_add, placeholder_text="Article", width=140)
        self.entry_prod.grid(row=0, column=0, padx=5, pady=5)

        self.entry_qte = ctk.CTkEntry(frame_add, placeholder_text="Qté", width=60)
        self.entry_qte.grid(row=0, column=1, padx=5, pady=5)

        self.entry_prix = ctk.CTkEntry(frame_add, placeholder_text=f"Prix ({self.params.get('devise', 'FC')})", width=90)
        self.entry_prix.grid(row=0, column=2, padx=5, pady=5)

        btn_ajouter = ctk.CTkButton(frame_add, text="➕", width=40, command=self._ajouter_ligne)
        btn_ajouter.grid(row=0, column=3, padx=5, pady=5)

        # Aperçu du reçu
        self.txt_recu = ctk.CTkTextbox(self, font=("Courier", 12), width=400, height=320)
        self.txt_recu.pack(padx=15, pady=10, fill="both", expand=True)

        self.lbl_total = ctk.CTkLabel(self, text=f"TOTAL : 0 {self.params.get('devise', 'FC')}", font=("Arial", 14, "bold"), text_color="#2ECC71")
        self.lbl_total.pack(pady=5)

        btn_imprimer = ctk.CTkButton(self, text="💾 Sauvegarder / Imprimer Reçu", command=self._sauvegarder_recu)
        btn_imprimer.pack(pady=(0, 15))

        self._actualiser_apercu()

    def _charger_parametres(self) -> Dict[str, str]:
        params = {}
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            cursor.execute("SELECT cle, valeur FROM parametres")
            for k, v in cursor.fetchall():
                params[k] = v
            conn.close()
        except Exception:
            pass
        return params

    def _ajouter_ligne(self):
        prod = self.entry_prod.get().strip()
        qte_str = self.entry_qte.get().strip()
        prix_str = self.entry_prix.get().strip()

        if not prod or not qte_str or not prix_str:
            return

        try:
            qte = int(qte_str)
            prix = float(prix_str)
            total = qte * prix
            self.articles_recu.append({"produit": prod, "qte": qte, "prix": prix, "total": total})

            self.entry_prod.delete(0, ctk.END)
            self.entry_qte.delete(0, ctk.END)
            self.entry_prix.delete(0, ctk.END)

            self._actualiser_apercu()
        except ValueError:
            pass

    def _actualiser_apercu(self):
        devise = self.params.get('devise', 'FC')
        boutique = self.params.get('nom_boutique', 'SokoMaster Store')
        tel = self.params.get('telephone', 'N/A')
        adresse = self.params.get('adresse', 'N/A')
        date_heure = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        texte = f"{'='*36}\n"
        texte += f"     {boutique.upper()}\n"
        texte += f"   Tel: {tel}\n"
        texte += f"   {adresse}\n"
        texte += f"   Date: {date_heure}\n"
        texte += f"{'='*36}\n"
        texte += f"{'Article':<16} {'Qté':<5} {'P.U':<7} {'Total':<6}\n"
        texte += f"{'-'*36}\n"

        grand_total = 0
        for item in self.articles_recu:
            p_nom = item['produit'][:15]
            texte += f"{p_nom:<16} {item['qte']:<5} {item['prix']:<7.0f} {item['total']:<6.0f}\n"
            grand_total += item['total']

        texte += f"{'='*36}\n"
        texte += f"TOTAL A PAYER : {grand_total:.0f} {devise}\n"
        texte += f"{'='*36}\n"
        texte += "   Merci pour votre confiance ! 🙏\n"

        self.txt_recu.delete("1.0", ctk.END)
        self.txt_recu.insert("1.0", texte)
        self.lbl_total.configure(text=f"TOTAL : {grand_total:.0f} {devise}")

    def _sauvegarder_recu(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Fichier texte", "*.txt")], title="Enregistrer le reçu")
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.txt_recu.get("1.0", ctk.END))
            self.destroy()

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

        self.entry = ctk.CTkEntry(self, corner_radius=8, placeholder_text="🔍 Rechercher un produit...")
        self.entry.grid(row=0, column=0, columnspan=8, sticky="ew", padx=10, pady=10)
        self.entry.bind("<KeyRelease>", self._rechercher)

        li = ["Nom", "Quantité", "Seuil critique", "P.A (Unit)", "P.V (Unit)", "Actions"]
        for t, a in enumerate(li):
            ctk.CTkLabel(self, text=a, font=("Arial", 12, "bold")).grid(row=1, column=t, sticky=ctk.EW)
            self.grid_columnconfigure(t, weight=1)

        self.frame = ctk.CTkScrollableFrame(self)
        self.frame.grid(row=2, column=0, columnspan=8, sticky="nsew", padx=5, pady=5)
        self.grid_rowconfigure(2, weight=1)
        self._recuperation_et_remplissage()

    def _rechercher(self, event=None):
        terme = self.entry.get().strip()
        self._recuperation_et_remplissage(recherche=terme)

    def _recuperation_et_remplissage(self, recherche=""):
        for widget in self.frame.winfo_children():
            widget.destroy()

        conn = None
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            
            # Si on ne recherche rien, on limite aux 50 premiers produits pour ne pas freezer l'interface
            if not recherche:
                cursor.execute("SELECT nom, quantite, seuil_critique, p_a_u, p_v_u, index_p FROM stock LIMIT 50")
            else:
                cursor.execute("SELECT nom, quantite, seuil_critique, p_a_u, p_v_u, index_p FROM stock")
                
            produits = cursor.fetchall()
            
            row_index = 0
            for tupl in produits:
                nom_decrypte = securite.decrypter(tupl[0])

                if recherche and recherche.lower() not in nom_decrypte.lower():
                    continue
                # ... (le reste de ta fonction pour dessiner les widgets reste identique)

                self.frame.grid_rowconfigure(row_index, weight=1)
                index_p = tupl[5]

                valeurs_affichees = [nom_decrypte, tupl[1], tupl[2], tupl[3], tupl[4]]
                for b, val in enumerate(valeurs_affichees):
                    ctk.CTkLabel(self.frame, text=str(val)).grid(row=row_index, column=b, sticky="nsew", padx=2)
                    self.frame.grid_columnconfigure(b, weight=1)

                ctk.CTkButton(self.frame, text="+ Achat", width=55, fg_color="green", command=lambda idx=index_p: self._noter_achat(idx)).grid(row=row_index, column=5, sticky="ns", padx=2)
                ctk.CTkButton(self.frame, text="- Vente", width=55, fg_color="darkorange", command=lambda idx=index_p: self._noter_vente(idx)).grid(row=row_index, column=6, sticky="ns", padx=2)

                action_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
                action_frame.grid(row=row_index, column=7, sticky="nsew")
                ctk.CTkButton(action_frame, text="🗑️", width=30, fg_color="darkred", hover_color="red", command=lambda idx=index_p: self._supprimer_produit(idx)).pack(side="left", padx=2)

                row_index += 1
        except sqlite3.Error as e:
            print(f"❌ Erreur chargement stock : {e}")
        finally:
            if conn: conn.close()

    def _supprimer_produit(self, index):
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock WHERE index_p = ?", (index,))
            conn.commit()
            conn.close()
            self._recuperation_et_remplissage()
        except sqlite3.Error as e:
            print(f"❌ Erreur suppression : {e}")

    def _noter_achat(self, index):
        InterfaceVenteAchatRemove(self, removed=True, index=index, mode="achat", base_donnees=self.base_donnees)

    def _noter_vente(self, index):
        InterfaceVenteAchatRemove(self, removed=True, index=index, mode="vente", base_donnees=self.base_donnees)


class InterfaceNewProduct(ctk.CTkFrame):
    def __init__(self, master, width, height, bg_color, border_width, border_color, base_donnees=fichier_donnees):
        super().__init__(master, width=width, height=height, bg_color=bg_color)
        self.base_donnees = base_donnees

        li_entry = ["Nom du produit", "ex: 100", "ex: 5", "ex: 15000", "ex: 20000"]
        li_label = ["NOM PRODUIT", "QUANTITÉ INITIALE", "SEUIL CRITIQUE", "P.A UNITAIRE", "P.V UNITAIRE"]
        self.entries = []

        for t, (label, placeholder) in enumerate(zip(li_label, li_entry)):
            ctk.CTkLabel(self, text=label, font=("Arial", 12, "bold")).grid(row=t, column=0, sticky=ctk.EW, padx=20, pady=10)
            entry = ctk.CTkEntry(self, placeholder_text=placeholder)
            entry.grid(row=t, column=1, sticky=ctk.EW, padx=20, pady=10)
            self.entries.append(entry)
            self.grid_rowconfigure(t, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        self.lbl_msg = ctk.CTkLabel(self, text="", font=("Arial", 11))
        self.lbl_msg.grid(row=5, column=0, columnspan=2)

        self.bouton = ctk.CTkButton(self, text="Ajouter le produit (Crypté) 🔒", command=self._ajouter_produit)
        self.bouton.grid(row=6, column=0, sticky=ctk.NSEW, columnspan=2, padx=20, pady=20)

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
            self.lbl_msg.configure(text="⚠️ Veuillez saisir des valeurs numériques entières valides.", text_color="red")
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

            self.lbl_msg.configure(text="✅ Produit crypté et ajouté avec succès !", text_color="green")

            if hasattr(self.master, "interfacestock"):
                self.master.interfacestock._recuperation_et_remplissage()
        except sqlite3.Error as e:
            self.lbl_msg.configure(text=f"❌ Erreur BDD : {e}", text_color="red")
        finally:
            if conn: conn.close()


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
        """Ouvre l'interface de génération et d'impression de reçus."""
        InterfaceRecu(self, base_donnees=self.base_donnees)

# ==========================================
# OUTILS (CALCULATRICE, LLINK IA, DETTES)
# ==========================================
class InterfaceCalculatrice(ctk.CTkFrame):
    def __init__(self, master, width, height, bg_color, border_width, border_color):
        super().__init__(master, width=width, height=height, bg_color=bg_color)
        self.entry = ctk.CTkEntry(self, corner_radius=8, placeholder_text="0", font=("Arial", 20), justify="right")
        self.entry.bind('<Return>', self._calculer)
        self.entry.grid(row=0, column=0, columnspan=4, sticky=ctk.NSEW, padx=10, pady=10)

        li = ["7", "8", "9", "/", "4", "5", "6", "*", "1", "2", "3", "-", "C", "0", "=", "+"]
        c = 0
        for a in range(1, 5):
            for b in range(4):
                btn = ctk.CTkButton(self, text=li[c], font=("Arial", 18, "bold"), command=lambda arg=li[c]: self._inser_car(arg))
                btn.grid(row=a, column=b, sticky=ctk.NSEW, padx=5, pady=5)
                c += 1
                self.grid_columnconfigure(b, weight=1)
            self.grid_rowconfigure(a, weight=1)

    def _inser_car(self, arg):
        if arg == "=":
            self._calculer()
        elif arg == "C":
            self.entry.delete(0, ctk.END)
        else:
            self.entry.insert(ctk.END, arg)

    def _calculer(self, event=None):
        expr = self.entry.get().strip()
        if not expr: return
        try:
            allowed_chars = "0123456789+-*/.()"
            if any(char not in allowed_chars for char in expr):
                raise ValueError("Invalide")

            calc = str(eval(expr))
            self.entry.delete(0, ctk.END)
            self.entry.insert(0, calc)
        except Exception:
            self.entry.delete(0, ctk.END)
            self.entry.insert(0, "Erreur")


class InterfaceDettes(ctk.CTkFrame):
    """Interface de gestion des créances et dettes des clients."""
    def __init__(self, master, base_donnees=fichier_donnees):
        super().__init__(master)
        self.base_donnees = base_donnees

        # Zone de saisie
        frame_input = ctk.CTkFrame(self)
        frame_input.pack(fill="x", padx=10, pady=10)

        self.entry_nom = ctk.CTkEntry(frame_input, placeholder_text="Nom Client", width=150)
        self.entry_nom.grid(row=0, column=0, padx=5, pady=5)

        self.entry_somme = ctk.CTkEntry(frame_input, placeholder_text="Somme due", width=100)
        self.entry_somme.grid(row=0, column=1, padx=5, pady=5)

        self.entry_tel = ctk.CTkEntry(frame_input, placeholder_text="Téléphone", width=120)
        self.entry_tel.grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkButton(frame_input, text="➕ Ajouter dette", command=self._ajouter_dette).grid(row=0, column=3, padx=5, pady=5)

        # Liste des dettes
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self._charger_dettes()

    def _ajouter_dette(self):
        nom = self.entry_nom.get().strip()
        somme_str = self.entry_somme.get().strip()
        tel = self.entry_tel.get().strip()
        date_actuelle = datetime.datetime.now().strftime("%Y-%m-%d")

        if not nom or not somme_str: return
        try:
            somme = int(somme_str)
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            nom_crypte = securite.crypter(nom)
            cursor.execute("INSERT INTO dettes (nom, somme, telephone, date) VALUES (?, ?, ?, ?)", (nom_crypte, somme, tel, date_actuelle))
            conn.commit()
            conn.close()

            self.entry_nom.delete(0, ctk.END)
            self.entry_somme.delete(0, ctk.END)
            self.entry_tel.delete(0, ctk.END)
            self._charger_dettes()
        except ValueError:
            pass

    def _charger_dettes(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()

        conn = sqlite3.connect(self.base_donnees)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, somme, telephone, date FROM dettes")
        dettes = cursor.fetchall()
        conn.close()

        for idx, (d_id, nom_c, somme, tel, dt) in enumerate(dettes):
            nom = securite.decrypter(nom_c)
            ctk.CTkLabel(self.scroll_frame, text=f"👤 {nom}").grid(row=idx, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.scroll_frame, text=f"💰 {somme} FC").grid(row=idx, column=1, padx=10, pady=5)
            ctk.CTkLabel(self.scroll_frame, text=f"📞 {tel}").grid(row=idx, column=2, padx=10, pady=5)
            ctk.CTkLabel(self.scroll_frame, text=f"📅 {dt}").grid(row=idx, column=3, padx=10, pady=5)
            ctk.CTkButton(self.scroll_frame, text="✅ Solder", width=60, fg_color="green", command=lambda id_d=d_id: self._solder_dette(id_d)).grid(row=idx, column=4, padx=5, pady=5)

    def _solder_dette(self, id_dette):
        conn = sqlite3.connect(self.base_donnees)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dettes WHERE id = ?", (id_dette,))
        conn.commit()
        conn.close()
        self._charger_dettes()


class InterfaceLlink(ctk.CTkFrame):
    def __init__(self, master=None, width=400, height=300, bg_color="green", base_donnees=fichier_donnees):
        super().__init__(master, width=width, height=height, bg_color=bg_color)
        self.api = LlinkApiClient()
        self.base_donnees = base_donnees

        self.frame = ctk.CTkScrollableFrame(self)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.entry = ctk.CTkEntry(self, corner_radius=8, placeholder_text="Posez une question à Llink IA...")
        self.entry.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.entry.bind('<Return>', self._new_message)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _obtenir_contexte_commercant(self) -> str:
        """Construit un contexte détaillé sur l'état de la boutique pour informer Llink."""
        context = "CONTEXTE BOUTIQUE COMMERÇANT:\n"
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()

            # Informations générales
            cursor.execute("SELECT cle, valeur FROM parametres")
            params = dict(cursor.fetchall())
            context += f"- Nom Boutique : {params.get('nom_boutique', 'Inconnu')}\n"
            context += f"- Devise : {params.get('devise', 'FC')}\n"

            # Analyse des stocks
            cursor.execute("SELECT nom, quantite, seuil_critique FROM stock")
            stock_data = cursor.fetchall()
            alertes = [securite.decrypter(q[0]) for q in stock_data if q[1] <= q[2]]
            context += f"- Nombre total de références en stock : {len(stock_data)}\n"
            context += f"- Produits en rupture/seuil critique : {', '.join(alertes) if alertes else 'Aucun'}\n"

            conn.close()
        except Exception as e:
            context += "Erreur lors de la récupération des données boutique.\n"
        return context

    def _new_message(self, event=None):
        text = self.entry.get().strip()
        if not text: return
        self.entry.delete(0, ctk.END)

        # Message Utilisateur
        ctk.CTkLabel(self.frame, text=f"Vous : {text}", fg_color="#1F618D", corner_radius=8, justify="right", wraplength=300).pack(anchor="e", pady=5, padx=10)

        # Bulle de réponse IA
        lbl_ia = ctk.CTkLabel(self.frame, text="🤖 Llink réfléchit...", fg_color="#1E8449", corner_radius=8, justify="left", wraplength=300)
        lbl_ia.pack(anchor="w", pady=5, padx=10)

        def on_success(texte_reponse):
            self.after(0, lambda: lbl_ia.configure(text=f"🤖 Llink : {texte_reponse}"))

        def on_error(erreur):
            self.after(0, lambda: lbl_ia.configure(text=f"❌ Llink : {erreur}", fg_color="#922B21"))

        # Transmission du payload conforme à la structure attendue par FastAPI
        payload = {
            "message": text,
            "model": "gemini-2.5-flash",
            "preferences": self._obtenir_contexte_commercant(),
            "mode": "chat"
        }

        self.api.send_prompt_async("/api/chat", payload, on_success, on_error)


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
    def __init__(self, master=None, width=150, height=400, bg_color="green", base_donnees=fichier_donnees):
        super().__init__(master, width=width, height=height, bg_color=bg_color)
        self.base_donnees = base_donnees

        ctk.CTkButton(self, text="📋 Menu Statistiques", command=lambda: self._masquer_afficher_partie(4)).pack(fill=ctk.X, pady=5, padx=10)

        self.frame1 = ctk.CTkFrame(self)
        self.frame1.pack(expand=ctk.YES, fill=ctk.BOTH, padx=10, pady=10)

        li0 = ["📜 Historique Ventes", "📥 Historique Achats", "📊 Graphique des Ventes", "📉 Graphique des Stocks"]
        for t, a in enumerate(li0):
            ctk.CTkButton(self.frame1, text=a, command=lambda arg=t: self._masquer_afficher_partie(arg)).pack(fill=ctk.X, pady=10)

        self.frames = []
        for t in range(4):
            if t < 2:
                self.frames.append(ctk.CTkScrollableFrame(self))
            else:
                self.frames.append(ctk.CTkFrame(self))
        self.frames.append(self.frame1)

    def _masquer_afficher_partie(self, index):
        for t, frame in enumerate(self.frames):
            if index == t:
                frame.pack(expand=ctk.YES, fill=ctk.BOTH)
                if index == 2: self._generer_graphique_ventes(frame)
                elif index == 3: self._generer_graphique_stocks(frame)
            else:
                frame.pack_forget()

    def _afficher_historique(self, recherche="", mode="achat"):
        target_frame = self.frames[1] if mode == "achat" else self.frames[0]
        titre = "HISTORIQUE ACHATS" if mode == "achat" else "HISTORIQUE VENTES"
        table = "achats" if mode == "achat" else "ventes"

        for widget in target_frame.winfo_children():
            widget.destroy()

        conn = None
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            cursor.execute(f"SELECT nom, quantite, p_{'a' if mode=='achat' else 'v'}_t, heure, date FROM {table}")
            enregistrements = cursor.fetchall()

            ctk.CTkLabel(target_frame, text=titre, font=('Arial', 20, 'bold')).grid(row=0, column=0, sticky="nsew", padx=2, columnspan=5, pady=8)
            li = ["PRODUIT", "QUANTITÉ", "TOTAL (FC)", "HEURE", "DATE"]

            for t, a in enumerate(li):
                ctk.CTkLabel(target_frame, text=a, font=("Arial", 11, "bold")).grid(row=1, column=t, sticky="nsew", padx=2)
                target_frame.grid_columnconfigure(t, weight=1)

            for t, tupl in enumerate(enregistrements):
                target_frame.grid_rowconfigure(t+2, weight=1)
                nom_decrypte = securite.decrypter(tupl[0])

                if recherche and recherche.lower() not in nom_decrypte.lower():
                    continue

                ligne = [nom_decrypte, tupl[1], tupl[2], tupl[3], tupl[4]]
                for b, val in enumerate(ligne):
                    ctk.CTkLabel(target_frame, text=str(val)).grid(row=t+2, column=b, sticky="nsew", padx=2)
        except sqlite3.Error as e:
            print(f"❌ Erreur historique {mode} : {e}")
        finally:
            if conn: conn.close()

    def _generer_graphique_ventes(self, parent_frame):
        """Dessine un histogramme des 5 meilleurs produits vendus à l'aide d'un CTkCanvas natif."""
        for w in parent_frame.winfo_children(): 
            w.destroy()

        conn = sqlite3.connect(self.base_donnees)
        cursor = conn.cursor()
        cursor.execute("SELECT nom, SUM(quantite) FROM ventes GROUP BY nom LIMIT 5")
        donnees = cursor.fetchall()
        conn.close()

        produits = [securite.decrypter(d[0]) for d in donnees] if donnees else ["Aucune vente"]
        ventes = [d[1] for d in donnees] if donnees else [0]

        bg_theme = '#2b2b2b' if ctk.get_appearance_mode() == "Dark" else '#F2F2F2'
        text_color = 'white' if ctk.get_appearance_mode() == "Dark" else 'black'

        canvas = ctk.CTkCanvas(parent_frame, bg=bg_theme, highlightthickness=0, bd=0)
        canvas.pack(expand=True, fill='both', padx=10, pady=10)

        # Titre du graphique
        canvas.create_text(250, 25, text="Top 5 des Produits Vendus 📊", fill=text_color, font=("Arial", 14, "bold"))

        max_val = max(ventes) if max(ventes) > 0 else 1
        chart_height = 180
        start_y = 260
        start_x = 50
        bar_width = 50
        spacing = 30

        # Ligne de base (Axe X)
        canvas.create_line(30, start_y, 450, start_y, fill=text_color, width=2)

        for i, (prod, val) in enumerate(zip(produits, ventes)):
            x0 = start_x + i * (bar_width + spacing)
            x1 = x0 + bar_width
            bar_h = (val / max_val) * chart_height
            y0 = start_y - bar_h
            y1 = start_y

            # Dessin de la barre (Rectangle)
            canvas.create_rectangle(x0, y0, x1, y1, fill='#2ECC71', outline="")
            
            # Affichage de la valeur vendue au-dessus de la barre
            canvas.create_text(x0 + bar_width / 2, y0 - 12, text=str(val), fill=text_color, font=("Arial", 10, "bold"))
            
            # Libellé du produit sous la barre
            nom_court = prod[:7] + ".." if len(prod) > 7 else prod
            canvas.create_text(x0 + bar_width / 2, y1 + 15, text=nom_court, fill=text_color, font=("Arial", 9))

    def _generer_graphique_stocks(self, parent_frame):
        """Dessine un diagramme circulaire (Camembert) de l'état du stock à l'aide d'un CTkCanvas natif."""
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
        bg_theme = '#2b2b2b' if ctk.get_appearance_mode() == "Dark" else '#F2F2F2'
        text_color = 'white' if ctk.get_appearance_mode() == "Dark" else 'black'

        canvas = ctk.CTkCanvas(parent_frame, bg=bg_theme, highlightthickness=0, bd=0)
        canvas.pack(expand=True, fill='both', padx=10, pady=10)

        # Titre du graphique
        canvas.create_text(250, 25, text="État Global du Stock 📉", fill=text_color, font=("Arial", 14, "bold"))

        if total == 0:
            canvas.create_text(250, 160, text="Aucune donnée disponible dans le stock", fill=text_color, font=("Arial", 12))
            return

        labels = ['Stock Normal', 'Seuil Critique', 'Épuisé']
        sizes = [normal, critique, epuise]
        colors = ['#2ECC71', '#F1C40F', '#E74C3C']

        # Paramètres du Camembert
        start_angle = 0
        cx, cy, r = 140, 160, 85

        for size, color in zip(sizes, colors):
            if size == 0:
                continue
            extent = (size / total) * 360
            canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=start_angle, extent=extent, fill=color, outline=bg_theme, width=2)
            start_angle += extent

        # Dessin de la Légende à droite
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
    def __init__(self, master=None, width=150, height=400, bg_color="green", base_donnees=fichier_donnees):
        super().__init__(master, width=width, height=height, fg_color=bg_color)
        self.base_donnees = base_donnees

        li = ["INFORMATIONS", "Nom de la boutique", "Numéro de téléphone", "Adresse physique", "Devise", 
              "SÉCURITÉ", "Code PIN", "Vérouillage", "SAUVEGARDE ET RESTAURATION"]

        self.var_theme = ctk.StringVar(value="dark")
        self.var_verouillage = ctk.StringVar(value="desactiver")

        self.entries = {}

        self.frame_but_theme = ctk.CTkFrame(self)
        self.frame_but_verou = ctk.CTkFrame(self)
        ctk.CTkRadioButton(self.frame_but_theme, text="Clair", variable=self.var_theme, value="light", command=self._changer_mode).grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        ctk.CTkRadioButton(self.frame_but_theme, text="Sombre", variable=self.var_theme, value="dark", command=self._changer_mode).grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

        ctk.CTkRadioButton(self.frame_but_verou, text="on", variable=self.var_verouillage, value="activer").grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        ctk.CTkRadioButton(self.frame_but_verou, text="off", variable=self.var_verouillage, value="desactiver").grid(row=0, column=1, sticky="nsew", padx=20, pady=10)

        cle_mapping = {
            "Nom de la boutique": "nom_boutique",
            "Numéro de téléphone": "telephone",
            "Adresse physique": "adresse",
            "Devise": "devise",
            "Code PIN": "code_pin"
        }

        for t, a in enumerate(li):
            if a in ["INFORMATIONS", "SÉCURITÉ", "SAUVEGARDE ET RESTAURATION"]:
                ctk.CTkLabel(self, text=a, font=("Arial", 16, "bold"), text_color="white").grid(row=t, column=0, sticky="nsew", columnspan=2, pady=10)
            else:
                ctk.CTkLabel(self, text=a, width=150, anchor="w", text_color="white").grid(row=t, column=0, sticky="nsew", padx=20, pady=10)
                if a != "Vérouillage":
                    entry = ctk.CTkEntry(self)
                    entry.grid(row=t, column=1, sticky="nsew", padx=20, pady=10)
                    if a in cle_mapping:
                        self.entries[cle_mapping[a]] = entry
            self.grid_rowconfigure(t, weight=1)

        self.frame_but_theme.grid(row=13, column=1)
        self.frame_but_verou.grid(row=7, column=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        # Boutons d'actions des paramètres
        ctk.CTkButton(self, text="💾 Sauvegarder les informations", text_color="white", corner_radius=5, command=self._sauvegarder_infos).grid(row=9, column=0, pady=10, padx=20, columnspan=2, sticky="nsew")
        ctk.CTkButton(self, text="🔄 Restaurer", text_color="white", corner_radius=5, command=self._charger_infos).grid(row=10, column=0, pady=10, padx=20, columnspan=2, sticky="nsew")
        ctk.CTkButton(self, text="📊 Exporter vers Excel (CSV)", text_color="white", corner_radius=5, command=self._exporter_excel).grid(row=11, column=0, pady=10, padx=20, columnspan=2, sticky="nsew")

        ctk.CTkLabel(self, text="APPARENCE ET À PROPOS", bg_color=bg_color, text_color="white").grid(row=12, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        ctk.CTkLabel(self, text="VERSION", bg_color=bg_color, text_color="white").grid(row=14, column=0, sticky="nsew", padx=20, pady=10)
        ctk.CTkLabel(self, text="THEME", bg_color=bg_color, text_color="white").grid(row=13, column=0, sticky="nsew", padx=20, pady=10)
        ctk.CTkLabel(self, text="1.4.2", bg_color=bg_color, text_color="white").grid(row=14, column=1, sticky="nsew", padx=20, pady=10)
        ctk.CTkLabel(self, text="from CRYPT", bg_color=bg_color, text_color="white").grid(row=16, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        ctk.CTkLabel(self, text="Site Web", bg_color=bg_color, text_color="white").grid(row=15, column=0, sticky="nsew", padx=20, pady=10)
        ctk.CTkLabel(self, text="https://klgaby440-lang.github.io/sokomaster/", bg_color=bg_color, text_color="white").grid(row=15, column=1, sticky="nsew", pady=10, padx=20)

        self._charger_infos()

    def _changer_mode(self):
        ctk.set_appearance_mode(str(self.var_theme.get()))

    def _sauvegarder_infos(self):
        """Enregistre les informations du commerçant en base de données pour les reçus."""
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            for cle, entry in self.entries.items():
                valeur = entry.get().strip()
                cursor.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES (?, ?)", (cle, valeur))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Erreur sauvegarde paramètres : {e}")

    def _charger_infos(self):
        """Recharge les informations du commerçant sauvegardées."""
        try:
            conn = sqlite3.connect(self.base_donnees)
            cursor = conn.cursor()
            cursor.execute("SELECT cle, valeur FROM parametres")
            data = dict(cursor.fetchall())
            conn.close()

            for cle, entry in self.entries.items():
                if cle in data:
                    entry.delete(0, ctk.END)
                    entry.insert(0, data[cle])
        except Exception:
            pass

    def _exporter_excel(self):
        """Exporte l'état des stocks et des ventes dans un fichier CSV compatible Excel."""
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
        except Exception as e:
            print(f"Erreur exportation Excel : {e}")


class BarMenu(ctk.CTkFrame):
    def __init__(self, master=None, bg_color="green"):
        super().__init__(master, width=200, fg_color=bg_color, corner_radius=0)

        self.label = ctk.CTkLabel(self, text="🛒 SokoMaster", font=("Arial", 20, "bold"), text_color="white")
        self.label.pack(pady=30, padx=10)

        ctk.CTkButton(self, text="📦 Inventaire", font=("Arial", 14), command=self.master._print_stock_newp).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self, text="🤖 Outils & IA", font=("Arial", 14), command=self.master._print_outils).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self, text="📊 Statistiques", font=("Arial", 14), command=self.master._print_statistiques).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self, text="⚙️ Paramètres", font=("Arial", 14), command=self.master._print_parametre).pack(fill="x", pady=5, padx=10)


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
        for widget in self.main_view.winfo_children():
            widget.pack_forget()

    def _print_stock_newp(self):
        self._hide_all()
        self.inventaire.pack(expand=True, fill="both")

    def _print_outils(self):
        self._hide_all()
        if self.outils is None:
            # Instanciation uniquement lors du premier clic
            self.outils = InterfaceOutils(self.main_view, bg_color=self.bg_color)
        self.outils.pack(expand=True, fill="both")

    def _print_statistiques(self):
        self._hide_all()
        if self.statistique is None:
            self.statistique = InterfaceStatistiques(self.main_view, bg_color=self.bg_color, base_donnees=self.b_d)
            self.statistique._afficher_historique()
            self.statistique._afficher_historique(mode="vente")
        self.statistique.pack(expand=True, fill="both")

    def _print_parametre(self):
        self._hide_all()
        if self.parametres is None:
            self.parametres = InterfaceParametre(self.main_view, bg_color=self.bg_color, base_donnees=self.b_d)
        self.parametres.pack(expand=True, fill="both")

# ==========================================
# DEMARRAGE ET INITIALISATION BDD
# ==========================================
def initialiser_base_donnees(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS stock (nom TEXT, quantite INTEGER, p_a_u INTEGER, p_v_u INTEGER, seuil_critique INTEGER, index_p INTEGER PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS achats (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, quantite INTEGER, p_a_t INTEGER, heure TEXT, date TEXT, index_p INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, quantite INTEGER, p_v_t INTEGER, heure TEXT, date TEXT, index_p INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS activation (id INTEGER PRIMARY KEY, code TEXT, is_activated INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS dettes (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, somme INTEGER, telephone TEXT, date TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS parametres (cle TEXT PRIMARY KEY, valeur TEXT)")

    cursor.execute("SELECT COUNT(*) FROM activation")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO activation (id, code, is_activated) VALUES (1, '', 0)")

    conn.commit()
    conn.close()

def verifier_activation(db_path) -> bool:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT is_activated FROM activation WHERE id = 1")
    res = cursor.fetchone()
    conn.close()
    return res and res[0] == 1

if __name__ == "__main__":
    # Avant toute initialisation lourde, on crée la fenêtre
    root = ctk.CTk()
    root.geometry("1000x650")
    root.title("SokoMaster - CRYPT Enterprise")

    # On affiche un écran de chargement basique immédiatement
    splash_frame = ctk.CTkFrame(root)
    splash_frame.pack(expand=True, fill="both")
    ctk.CTkLabel(splash_frame, text="SokoMaster", font=("Arial", 36, "bold"), text_color="#2ECC71").pack(pady=(200, 20))
    ctk.CTkLabel(splash_frame, text="Chargement des modules cryptographiques et de la base de données... ⏳", font=("Arial", 14)).pack()

    # On force la mise à jour de l'écran pour que l'utilisateur voie le message
    root.update()

    def initialisation_lourde():
        initialiser_base_donnees(fichier_donnees)
        splash_frame.destroy() # On supprime l'écran de chargement

        def lancer_application_principale():
            for widget in root.winfo_children():
                widget.destroy()
            app = Application(root, b_d=fichier_donnees)
            app.pack(expand=ctk.YES, fill=ctk.BOTH)

        if verifier_activation(fichier_donnees):
            lancer_application_principale()
        else:
            interface_act = InterfaceActivation(root, on_activation_success=lancer_application_principale, base_donnees=fichier_donnees)
            interface_act.pack(expand=True, fill="both")

    # On lance l'initialisation après 100ms pour laisser l'interface s'afficher proprement
    root.after(100, initialisation_lourde)
    
    root.mainloop()
