import customtkinter as ctk
import webbrowser
import os
import threading
import time
import requests
import subprocess
from fpdf import FPDF
from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")

class SherlockApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sherlock by Lupo")
        self.geometry("900x980")
        
        # --- CONFIGURACIÓN DE RUTAS PROFESIONAL ---
        # Detecta la ubicación del script (src/)
        self.SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
        # Sube un nivel para encontrar Logs y Assets
        self.BASE_DIR = os.path.dirname(self.SCRIPT_PATH)
        self.LOG_DIR = os.path.join(self.BASE_DIR, "Logs_Sherlock")
        self.ICON_FILE = os.path.join(self.BASE_DIR, "assets", "sherlock.png")
        
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)

        self.stop_event = threading.Event()
        self.results_count = 0
        self.valid_results = []

        # Carga del logo para la UI
        try:
            self.pil_img = Image.open(self.ICON_FILE)
            self.tk_icon = ImageTk.PhotoImage(self.pil_img)
            self.iconphoto(True, self.tk_icon) 
        except Exception:
            self.pil_img = None

        self.setup_ui()

    def setup_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(pady=10)
        if self.pil_img:
            logo_img = ctk.CTkImage(light_image=self.pil_img, dark_image=self.pil_img, size=(100, 100))
            ctk.CTkLabel(self.header, image=logo_img, text="").pack()
        ctk.CTkLabel(self.header, text="SHERLOCK BY LUPO", font=("Courier New", 36, "bold"), text_color="#00FF00").pack()

        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(pady=10)
        self.entry = ctk.CTkEntry(self.search_frame, placeholder_text="Nombre de usuario...", width=400, height=40)
        self.entry.pack(side="left", padx=10)
        
        self.filter = ctk.CTkOptionMenu(self.search_frame, values=["Redes Sociales (Rápido)", "Búsqueda Profunda (Completo)"])
        self.filter.set("Búsqueda Profunda (Completo)")
        self.filter.pack(side="left")

        self.btns = ctk.CTkFrame(self, fg_color="transparent")
        self.btns.pack(pady=10)
        self.run_btn = ctk.CTkButton(self.btns, text="RUN INVESTIGATION", command=self.start_thread, fg_color="#1f6aa5", width=200, height=40)
        self.run_btn.grid(row=0, column=0, padx=10)
        self.abort_btn = ctk.CTkButton(self.btns, text="ABORT", command=self.stop_search, fg_color="#a03232", width=200, height=40, state="disabled")
        self.abort_btn.grid(row=0, column=1, padx=10)

        self.bar = ctk.CTkProgressBar(self, width=750, progress_color="#00FF00")
        self.bar.set(0)
        self.bar.pack(pady=5)

        self.console = ctk.CTkTextbox(self, width=800, height=350, font=("Courier New", 13), fg_color="#000000", text_color="#00FF00", border_color="#333333", border_width=1)
        self.console.pack(pady=10)
        
        self.console.tag_config("link", foreground="#3498db", underline=True)
        self.console.tag_config("found", foreground="#00FF00")
        self.console.tag_config("not_found", foreground="#a03232")
        
        self.console.bind("<Motion>", self.update_cursor)
        self.console.bind("<Button-1>", self.on_console_click)
        self.console.configure(state="disabled")

        self.tools = ctk.CTkFrame(self, fg_color="#1a1a1a", height=45)
        self.tools.pack(fill="x", padx=50, pady=5)
        ctk.CTkButton(self.tools, text="🗑️ Limpiar", width=80, fg_color="transparent", command=self.clear).pack(side="left", padx=10)
        ctk.CTkButton(self.tools, text="📋 Copiar Todo", width=100, fg_color="transparent", command=self.copy).pack(side="left", padx=10)
        self.findings = ctk.CTkLabel(self.tools, text="Findings: 0", font=("Courier New", 14, "bold"), text_color="#00FF00")
        self.findings.pack(side="right", padx=20)

        self.rep_btn = ctk.CTkButton(self, text="GENERATE AUDIT REPORT (PDF/TXT)", command=self.save_audit, fg_color="#27ae60", width=350, height=45)
        self.rep_btn.pack(pady=10)

        self.status = ctk.CTkLabel(self, text="[SYSTEM ONLINE]", font=("Courier New", 12), text_color="gray")
        self.status.pack(side="bottom", pady=10)

    def update_cursor(self, event):
        click_pos = self.console.index(f"@{event.x},{event.y}")
        if "link" in self.console.tag_names(click_pos):
            self.console.configure(cursor="hand2")
        else:
            self.console.configure(cursor="xterm")

    def on_console_click(self, event):
        click_pos = self.console.index(f"@{event.x},{event.y}")
        if "link" in self.console.tag_names(click_pos):
            start, end = self.console.tag_prevrange("link", f"{click_pos} + 1c")
            url = self.console.get(start, end).strip()
            webbrowser.open(url)

    def add_res(self, name, url, status_code):
        self.console.configure(state="normal")
        if status_code == 200:
            self.console.insert("end", f"[✔] {name}: ", "found")
            self.console.insert("end", url, "link")
            self.valid_results.append((name, url))
            self.results_count += 1
        else:
            self.console.insert("end", f"[✘] {name}: Not Found\n", "not_found")
        
        if status_code == 200: self.console.insert("end", "\n")
        self.console.see("end")
        self.console.configure(state="disabled")
        self.findings.configure(text=f"Findings: {self.results_count}")

    def check_url(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code in [200, 403]:
                return 200
            return response.status_code
        except Exception:
            return 404

    def start_thread(self):
        user = self.entry.get().replace("@", "")
        if not user: return
        self.clear()
        self.stop_event.clear()
        self.run_btn.configure(state="disabled")
        self.abort_btn.configure(state="normal")
        self.status.configure(text="[SCANNING & VALIDATING...]", text_color="#3498db")
        threading.Thread(target=self.scan, args=(user,), daemon=True).start()

    def scan(self, user):
        sites = [
            ("Instagram", "https://instagram.com/"), ("Facebook", "https://facebook.com/"), 
            ("TikTok", "https://www.tiktok.com/@"), ("Twitter/X", "https://twitter.com/"),
            ("GitHub", "https://github.com/"), ("Reddit", "https://reddit.com/user/"), 
            ("Twitch", "https://twitch.tv/")
        ]
        
        if self.filter.get() == "Búsqueda Profunda (Completo)":
            deep_sites = [
                ("LinkedIn", "https://www.linkedin.com/in/"), ("Pinterest", "https://pinterest.com/"),
                ("SoundCloud", "https://soundcloud.com/"), ("Spotify", "https://open.spotify.com/user/"),
                ("Steam", "https://steamcommunity.com/id/"), ("Vimeo", "https://vimeo.com/"),
                ("DailyMotion", "https://www.dailymotion.com/"), ("Medium", "https://medium.com/@")
            ]
            sites.extend(deep_sites)

        for i, (name, base) in enumerate(sites):
            if self.stop_event.is_set(): break
            url = f"{base}{user}"
            code = self.check_url(url)
            self.after(0, self.add_res, name, url, code)
            self.after(0, self.bar.set, (i + 1) / len(sites))
        
        self.after(0, self.finish)

    def save_audit(self):
        user = self.entry.get() or "audit"
        if not self.valid_results: return
        timestamp = int(time.time())
        
        txt_path = os.path.join(self.LOG_DIR, f"Lupo_Audit_{user}_{timestamp}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"SHERLOCK OSINT REPORT - TARGET: {user}\n\n")
            for name, url in self.valid_results:
                f.write(f"{name}: {url}\n")

        pdf_path = os.path.join(self.LOG_DIR, f"Lupo_Report_{user}_{timestamp}.pdf")
        try:
            pdf = FPDF()
            pdf.add_page()
            
            if os.path.exists(self.ICON_FILE):
                pdf.image(self.ICON_FILE, x=10, y=8, w=30)
            
            pdf.set_font("Arial", 'B', 18)
            pdf.set_text_color(31, 106, 165)
            pdf.cell(200, 15, txt="SHERLOCK OSINT AUDIT REPORT", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(200, 10, txt=f"Investigador: Lupo SysAdmin", ln=True)
            pdf.cell(200, 10, txt=f"Objetivo: {user}", ln=True)
            pdf.cell(200, 10, txt=f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Cuentas Encontradas:", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.set_text_color(0, 128, 0)
            
            for name, url in self.valid_results:
                pdf.cell(200, 8, txt=f"  [FOUND] {name}: {url}", ln=True)
            
            pdf.output(pdf_path)
            self.status.configure(text=f"[REPORTS GENERATED]", text_color="#00FF00")
            subprocess.run(['xdg-open', self.LOG_DIR], check=True)
                
        except Exception as e:
            self.status.configure(text=f"Error PDF: {e}", text_color="red")

    def finish(self):
        self.run_btn.configure(state="normal")
        self.abort_btn.configure(state="disabled")
        self.status.configure(text="[COMPLETE]", text_color="#00FF00")

    def stop_search(self): self.stop_event.set()

    def clear(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        self.results_count = 0
        self.valid_results = []
        self.findings.configure(text="Findings: 0")
        self.bar.set(0)

    def copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.console.get("1.0", "end-1c"))

if __name__ == "__main__":
    app = SherlockApp()
    app.mainloop()
