import customtkinter as ctk
import os
import sys
from dotenv import load_dotenv
from modules.recorder import RecorderFrame
from modules.transcriber import TranscriberFrame

# Load environment variables
load_dotenv(override=True)

from tkinterdnd2 import TkinterDnD

class UnifiedApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        # Window Setup
        self.title("Unified Transcription Suite")
        self.geometry("900x700")

        # Window Icon
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        # Theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # Grid Layout
        self.grid_columnconfigure(0, weight=1)  # 1/4
        self.grid_columnconfigure(1, weight=3)  # 3/4
        self.grid_rowconfigure(0, weight=1)

        # Recorder Frame (Left - 1/4)
        self.recorder_frame = RecorderFrame(self)
        self.recorder_frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        # Transcriber Frame (Right - 3/4)
        self.transcriber_frame = TranscriberFrame(self)
        self.transcriber_frame.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")

        # Connect auto-transcribe callback: when recorder hits 20 MB limit,
        # automatically send the saved file to the transcriber
        self.recorder_frame.on_auto_transcribe = self.transcriber_frame.process_file_thread

if __name__ == "__main__":
    app = UnifiedApp()
    app.mainloop()
