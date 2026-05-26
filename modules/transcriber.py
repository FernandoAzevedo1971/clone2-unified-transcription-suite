import customtkinter as ctk
import os
import threading
import time
import webbrowser
from tkinter import filedialog

from tkinterdnd2 import DND_FILES
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .services import AssemblyAIService, DeepgramService
from .theme import (
    ORANGE, ORANGE_HOVER, GRAY, GRAY_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, BG_CARD, FONT,
)


class AudioFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            self.handle_event(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.handle_event(event.dest_path)

    def handle_event(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext in [".mp3", ".wav", ".m4a", ".flac", ".ogg"]:
            time.sleep(2)
            self.callback(filepath)


class TranscriberFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.services = {
            "AssemblyAI": None,
            "Deepgram": None,
        }
        self.observer = None
        self.processing_files = set()  # Track files currently being processed

        # Configuration
        _home = os.path.expanduser("~")
        _default_watch = os.path.join(_home, "OneDrive", "Documentos", "Gravacoes Som Audio Recorder Free")
        self.watch_directory = os.getenv("WATCH_DIRECTORY", _default_watch)
        
        # Ensure path is valid for this user
        if "Users\\ferna" in self.watch_directory:
            self.watch_directory = _default_watch

        self.setup_ui()
        self.init_services()
        self.after(1000, self.start_monitor)

    def init_services(self):
        aai_key = os.getenv("ASSEMBLYAI_API_KEY")
        dg_key = os.getenv("DEEPGRAM_API_KEY")

        if aai_key:
            self.services["AssemblyAI"] = AssemblyAIService(aai_key)
        if dg_key:
            self.services["Deepgram"] = DeepgramService(dg_key)

        if self.services["AssemblyAI"]:
            self.service_combo.set("AssemblyAI")
        elif self.services["Deepgram"]:
            self.service_combo.set("Deepgram")

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.configure(fg_color=BG_CARD, corner_radius=16)

        _serif = ctk.CTkFont(family=FONT, size=13)
        _serif_bold = ctk.CTkFont(family=FONT, size=13, weight="bold")

        self.service_frame = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=10)
        self.service_frame.grid(row=0, column=0, padx=20, pady=(16, 6), sticky="ew")

        ctk.CTkLabel(
            self.service_frame,
            text="Servico:",
            font=_serif_bold,
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(14, 6), pady=10)

        self.service_combo = ctk.CTkComboBox(
            self.service_frame,
            values=["AssemblyAI", "Deepgram"],
            state="readonly",
            font=_serif,
            dropdown_font=_serif,
            fg_color="#252525",
            border_color="#3A3A3A",
            button_color=ORANGE,
            button_hover_color=ORANGE_HOVER,
            width=140,
        )
        self.service_combo.pack(side="left", padx=6, pady=10)
        self.service_combo.set("AssemblyAI")

        self.btn_check_balance = ctk.CTkButton(
            self.service_frame,
            text="Ver Saldo US$",
            width=110,
            font=_serif,
            fg_color=ORANGE,
            hover_color=ORANGE_HOVER,
            corner_radius=8,
            command=self.open_balance_dashboard,
        )
        self.btn_check_balance.pack(side="left", padx=10, pady=10)

        self.file_frame = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=10)
        self.file_frame.grid(row=1, column=0, padx=20, pady=6, sticky="ew")

        self.btn_select = ctk.CTkButton(
            self.file_frame,
            text="Selecionar Arquivo",
            width=150,
            font=_serif,
            fg_color=ORANGE,
            hover_color=ORANGE_HOVER,
            corner_radius=8,
            command=self.select_file,
        )
        self.btn_select.pack(side="left", padx=12, pady=10)

        self.lbl_status = ctk.CTkLabel(
            self.file_frame,
            text="Iniciando monitoramento...",
            text_color=ORANGE,
            font=_serif,
            anchor="w",
        )
        self.lbl_status.pack(side="left", padx=10, fill="x", expand=True)

        self.textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family=FONT, size=14),
            fg_color="#141414",
            text_color=TEXT_PRIMARY,
            corner_radius=12,
            border_width=1,
            border_color="#2A2A2A",
            scrollbar_button_color="#3A3A3A",
            scrollbar_button_hover_color=ORANGE,
        )
        self.textbox.grid(row=2, column=0, padx=20, pady=8, sticky="nsew")
        self.textbox._textbox.tag_configure("app_msg", foreground=ORANGE)
        self.textbox._textbox.tag_configure("transcript", foreground=TEXT_PRIMARY)

        # Drop zone visual hint
        self.drop_hint = ctk.CTkLabel(
            self,
            text="⬇  Arraste um arquivo de áudio aqui  (mp3 · wav · m4a · flac · ogg)",
            font=ctk.CTkFont(family=FONT, size=12),
            text_color="#4B5563",
            fg_color="#1A1A1A",
            corner_radius=8,
            height=32,
        )
        self.drop_hint.grid(row=3, column=0, padx=20, pady=(0, 4), sticky="ew")

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=4, column=0, padx=20, pady=(4, 16), sticky="ew")

        ctk.CTkButton(
            self.btn_frame,
            text="Copiar Texto",
            font=_serif,
            fg_color=ORANGE,
            hover_color=ORANGE_HOVER,
            corner_radius=8,
            command=self.copy_text,
        ).pack(side="right", padx=8, pady=8)

        ctk.CTkButton(
            self.btn_frame,
            text="Limpar",
            font=_serif,
            fg_color=GRAY,
            hover_color=GRAY_HOVER,
            corner_radius=8,
            command=self.clear_text,
        ).pack(side="left", padx=8, pady=8)

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.on_drop)

    def set_status(self, text, color):
        self.after(0, lambda: self.lbl_status.configure(text=text, text_color=color))

    def append_transcript(self, filepath, service_name, text):
        def _append():
            header = f"\n— {os.path.basename(filepath)} ({service_name}) —\n"
            self.textbox._textbox.insert("end", header, "app_msg")
            self.textbox._textbox.insert("end", text + "\n", "transcript")
            self.textbox.see("end")

        self.after(0, _append)

    def start_monitor(self):
        if not os.path.exists(self.watch_directory):
            try:
                os.makedirs(self.watch_directory, exist_ok=True)
            except Exception as error:
                self.set_status(f"Erro ao criar pasta: {error}", "red")
                return

        self.event_handler = AudioFileHandler(self.process_file_thread)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.watch_directory, recursive=False)
        self.observer.start()

        folder_name = os.path.basename(self.watch_directory)
        self.set_status(f"⬤  Monitorando: ...\\{folder_name}", ORANGE)

    def on_drop(self, event):
        filepath = event.data
        if filepath.startswith("{") and filepath.endswith("}"):
            filepath = filepath[1:-1]
        self.process_file_thread(filepath)

    def select_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.m4a *.ogg *.flac")])
        if filepath:
            self.process_file_thread(filepath)

    def process_file_thread(self, filepath):
        service_name = self.service_combo.get()
        if not self.services.get(service_name):
            self.set_status(f"ERRO: API Key para {service_name} ausente!", "red")
            return

        # Path normalization to avoid duplicates due to formatting
        abs_path = os.path.abspath(filepath)
        
        if abs_path in self.processing_files:
            print(f"Skipping duplicate processing for: {abs_path}")
            return

        self.processing_files.add(abs_path)
        filename = os.path.basename(abs_path)
        self.set_status(f"⟳  Processando {filename}...", ORANGE)
        threading.Thread(target=self.process_file, args=(abs_path, service_name), daemon=True).start()

    def process_file(self, filepath, service_name):
        try:
            service = self.services[service_name]
            text = service.transcribe(filepath)
            self.set_status("✓  Transcricao concluida!", "#22C55E")
            self.append_transcript(filepath, service_name, text)
        except Exception as error:
            self.set_status(f"Erro: {error}", "red")
        finally:
            # Always remove from processing set, even on error
            if filepath in self.processing_files:
                self.processing_files.remove(filepath)

    def copy_text(self):
        self.clipboard_clear()
        self.clipboard_append(self.textbox.get("0.0", "end"))

    def clear_text(self):
        self.textbox.delete("0.0", "end")

    def open_balance_dashboard(self):
        service = self.service_combo.get()
        if service == "AssemblyAI":
            webbrowser.open("https://www.assemblyai.com/app/usage")
        elif service == "Deepgram":
            webbrowser.open("https://console.deepgram.com/project/usage")

    def destroy(self):
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=1)
        super().destroy()
