import customtkinter as ctk
import os
import queue
import threading
import time
import wave
from datetime import datetime
from tkinter import messagebox

from .theme import (
    ORANGE, ORANGE_HOVER, GREEN, GREEN_HOVER, RED, RED_HOVER,
    GRAY, GRAY_HOVER, TEXT_PRIMARY, TEXT_SECONDARY, BG_CARD, FONT,
)

try:
    import sounddevice as sd
except ImportError:
    sd = None


class RecorderFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.chunk = 1024
        self.sample_width = 2
        self.channels = 1
        self.rate = 44100

        self.is_recording = False
        self.stream = None
        self.frames = []
        self.audio_queue = queue.Queue()
        self.devices = []

        self.recording_start_time = None
        self.current_file_size = 0
        self.max_file_size = 20 * 1024 * 1024
        _home = os.path.expanduser("~")
        _default_save = os.path.join(_home, "OneDrive", "Documentos", "Gravacoes Som Audio Recorder Free")
        self.save_path = os.getenv("WATCH_DIRECTORY", _default_save)
        
        # Ensure path is valid for this user
        if "Users\\ferna" in self.save_path:
            self.save_path = _default_save
            
        os.makedirs(self.save_path, exist_ok=True)

        self.on_auto_transcribe = None

        self.setup_ui()
        self.populate_devices()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.configure(fg_color=BG_CARD, corner_radius=16)

        self.device_label = ctk.CTkLabel(
            self,
            text="Dispositivo de Entrada:",
            font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
            text_color=TEXT_SECONDARY,
        )
        self.device_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        self.device_combo = ctk.CTkComboBox(
            self,
            width=400,
            state="readonly",
            font=ctk.CTkFont(family=FONT, size=13),
            dropdown_font=ctk.CTkFont(family=FONT, size=13),
            fg_color="#1A1A1A",
            border_color="#3A3A3A",
            button_color=ORANGE,
            button_hover_color=ORANGE_HOVER,
        )
        self.device_combo.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        self.status_frame = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=12)
        self.status_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Parado",
            text_color=RED,
            font=ctk.CTkFont(family=FONT, size=22, weight="bold"),
        )
        self.status_label.pack(pady=(20, 5))

        self.time_label = ctk.CTkLabel(
            self.status_frame,
            text="00:00:00",
            font=ctk.CTkFont(family=FONT, size=32),
            text_color=TEXT_PRIMARY,
        )
        self.time_label.pack(pady=5)

        self.size_label = ctk.CTkLabel(
            self.status_frame,
            text="0.00 MB",
            font=ctk.CTkFont(family=FONT, size=12),
            text_color=TEXT_SECONDARY,
        )
        self.size_label.pack(pady=(0, 20))

        self.boost_var = ctk.BooleanVar(value=True)
        self.boost_checkbox = ctk.CTkCheckBox(
            self,
            text="Aumentar Volume (Boost 3x)",
            variable=self.boost_var,
            font=ctk.CTkFont(family=FONT, size=13),
            text_color=TEXT_PRIMARY,
            fg_color=ORANGE,
            hover_color=ORANGE_HOVER,
            checkmark_color=TEXT_PRIMARY,
            border_color="#3A3A3A",
        )
        self.boost_checkbox.grid(row=3, column=0, padx=20, pady=(10, 0))

        self.record_button = ctk.CTkButton(
            self,
            text="Iniciar Gravacao",
            command=self.toggle_recording,
            font=ctk.CTkFont(family=FONT, size=16, weight="bold"),
            height=52,
            corner_radius=12,
            fg_color=GREEN,
            hover_color=GREEN_HOVER,
            text_color=TEXT_PRIMARY,
        )
        self.record_button.grid(row=4, column=0, padx=20, pady=30, sticky="ew")

        self.file_label = ctk.CTkLabel(
            self,
            text="Ultimo arquivo: Nenhum",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family=FONT, size=12),
            wraplength=200,
        )
        self.file_label.grid(row=5, column=0, padx=20, pady=10)

    def populate_devices(self):
        """
        Preenche a lista de dispositivos de entrada e seleciona automaticamente
        o microfone USB (primeira opcao e padrao). Ordem da lista:
          1. Dispositivos USB (com "USB" no nome) — aparecem PRIMEIRO
          2. Demais dispositivos de entrada

        Selecao automatica pela cadeia de prioridade:
          P1. USB com "MIC"/"MICROFONE" no nome
          P2. Qualquer USB de entrada
          P3. Qualquer "MIC"/"MICROFONE"
          P4. Dispositivo padrao do sistema
          P5. Primeiro da lista
        """
        if not sd:
            self.disable_recording("Biblioteca sounddevice nao esta instalada.")
            return

        self.devices = []

        # Candidatos por nivel de prioridade
        usb_mic_candidate = None
        usb_candidate = None
        mic_candidate = None
        system_default_candidate = None

        usb_entries = []
        other_entries = []

        try:
            # Descobre o indice padrao do sistema
            raw_default = sd.default.device
            system_input_index = None
            if isinstance(raw_default, (list, tuple)) and len(raw_default) > 0:
                system_input_index = raw_default[0]
            elif isinstance(raw_default, int):
                system_input_index = raw_default

            # Coleta TODOS os dispositivos de todas as APIs de host para nao perder USB
            seen_names = set()
            for index, device_info in enumerate(sd.query_devices()):
                if int(device_info.get("max_input_channels", 0)) <= 0:
                    continue

                name = str(device_info.get("name", f"Dispositivo {index}"))

                # Evita duplicatas de nome (mesmo mic pode aparecer em multiplas APIs)
                if name in seen_names:
                    continue
                seen_names.add(name)

                normalized = name.upper()
                is_usb = "USB" in normalized

                entry = {
                    "index": index,
                    "name": name,
                    "label": name,
                    "channels": max(1, int(device_info.get("max_input_channels", 1))),
                }

                if is_usb:
                    usb_entries.append(entry)
                else:
                    other_entries.append(entry)

                is_mic = "MIC" in normalized or "MICROFONE" in normalized

                if is_usb and is_mic and usb_mic_candidate is None:
                    usb_mic_candidate = name
                elif is_usb and usb_candidate is None:
                    usb_candidate = name
                elif is_mic and mic_candidate is None:
                    mic_candidate = name

                if system_input_index is not None and index == system_input_index:
                    system_default_candidate = name

            # USB sempre primeiro na lista
            self.devices = usb_entries + other_entries
            device_names = [d["label"] for d in self.devices]

            if not self.devices:
                self.disable_recording("Nenhum dispositivo de entrada foi encontrado.")
                return

            # Selecao automatica pela cadeia de prioridade
            selected = (
                usb_mic_candidate
                or usb_candidate
                or mic_candidate
                or system_default_candidate
                or self.devices[0]["label"]
            )

            self.device_combo.configure(values=device_names, state="readonly")
            self.device_combo.set(selected)
            self.file_label.configure(text="Ultimo arquivo: Nenhum", text_color="gray")

        except Exception as error:
            self.disable_recording(f"Erro ao listar dispositivos: {error}")

    def disable_recording(self, reason):
        self.devices = []
        self.status_label.configure(text="Indisponivel", text_color=ORANGE)
        self.file_label.configure(text=reason, text_color=ORANGE)
        self.record_button.configure(state="disabled", text="Gravacao indisponivel", fg_color=GRAY)
        self.device_combo.configure(state="disabled", values=["Indisponivel"])
        self.device_combo.set("Indisponivel")

    def get_selected_device(self):
        selected_name = self.device_combo.get()
        for device in self.devices:
            if device["label"] == selected_name:
                return device
        return None

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self, auto_restart=False):
        device = self.get_selected_device()
        if device is None:
            messagebox.showerror("Erro", "Selecione um dispositivo de entrada valido.")
            return

        success = False
        last_error = None
        
        # Tenta re-encontrar o indice do dispositivo caso tenha sido desconectado/reconectado
        target_index = device["index"]
        try:
            live_devices = sd.query_devices()
            if target_index >= len(live_devices) or live_devices[target_index].get("name") != device["name"]:
                for i, live_dev in enumerate(live_devices):
                    if live_dev.get("name") == device["name"]:
                        target_index = i
                        break
        except Exception:
            pass

        try:
            device_info = sd.query_devices(target_index)
            # Lista de taxas de amostragem para testar (comecando pela padrao do dispositivo)
            default_rate = int(device_info.get("default_samplerate", 44100))
            rates_to_try = [default_rate, 44100, 48000, 16000, 8000]
            rates_to_try = list(dict.fromkeys(rates_to_try))  # Remove duplicatas preservando a ordem
            
            for rate in rates_to_try:
                try:
                    self.audio_queue = queue.Queue()
                    self.stream = sd.RawInputStream(
                        samplerate=rate,
                        blocksize=self.chunk,
                        device=target_index,
                        channels=min(self.channels, int(device_info.get("max_input_channels", 1))),
                        dtype="int16",
                        callback=self._audio_callback,
                    )
                    self.stream.start()
                    self.rate = rate  # Atualiza para salvar o arquivo com a taxa correta
                    success = True
                    break
                except Exception as e:
                    last_error = e

            if not success:
                self.populate_devices()
                messagebox.showerror("Erro", f"Erro ao abrir dispositivo.\nDetalhes: {last_error}\n\nA lista de dispositivos foi atualizada. Por favor, selecione novamente.")
                return

        except Exception as error:
            self.populate_devices()
            messagebox.showerror("Erro", f"Erro ao acessar dispositivo: {error}\n\nA lista de dispositivos foi atualizada.")
            return

        self.is_recording = True
        self.frames = []
        self.recording_start_time = time.time()
        self.current_file_size = 0

        if not auto_restart:
            self.record_button.configure(text="Parar Gravacao", fg_color=RED, hover_color=RED_HOVER)
            self.device_combo.configure(state="disabled")

        self.status_label.configure(text="Gravando...", text_color=GREEN)

        threading.Thread(target=self.record_loop, daemon=True).start()
        self.after(0, self.update_ui_loop)

    def _audio_callback(self, indata, frames, callback_time, status):
        if status:
            print(f"Audio callback status: {status}")
        self.audio_queue.put(bytes(indata))

    def stop_recording(self):
        self.is_recording = False
        self.record_button.configure(text="Iniciar Gravacao", fg_color=GREEN, hover_color=GREEN_HOVER)
        self.status_label.configure(text="Parado", text_color=RED)
        if self.devices:
            self.device_combo.configure(state="readonly")

    def show_no_audio_error(self):
        self.stop_recording()
        device_name = self.device_combo.get()
        messagebox.showerror(
            "Sem Audio Detectado",
            f"Nao foi possivel receber audio do dispositivo selecionado:\n'{device_name}'.\n\n"
            "Dicas:\n"
            "1. Se for um microfone USB, tente desconectar e conectar novamente.\n"
            "2. Verifique as configuracoes de Privacidade do Windows para o Microfone.\n"
            "3. Tente selecionar outro microfone na lista (ex: Realtek)."
        )

    def record_loop(self):
        split_triggered = False
        empty_queue_count = 0

        while self.is_recording:
            try:
                data = self.audio_queue.get(timeout=0.5)
                empty_queue_count = 0
            except queue.Empty:
                empty_queue_count += 1
                if self.current_file_size == 0 and empty_queue_count >= 4:
                    self.is_recording = False
                    self.after(0, self.show_no_audio_error)
                    break
                continue
            except Exception as error:
                print(f"Erro na fila de audio: {error}")
                self.is_recording = False
                break

            self.frames.append(data)
            self.current_file_size += len(data)

            if self.current_file_size >= self.max_file_size:
                self.is_recording = False
                split_triggered = True
                break

        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as error:
                print(f"Erro ao fechar stream: {error}")
            finally:
                self.stream = None

        if self.frames:
            saved_path = self.save_recording()

            if split_triggered and saved_path:
                if self.on_auto_transcribe:
                    self.after(0, lambda path=saved_path: self.on_auto_transcribe(path))
                self.after(200, lambda: self.start_recording(auto_restart=True))

    def save_recording(self):
        if not self.frames:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gravacao-fernando_{timestamp}.wav"
        filepath = os.path.join(self.save_path, filename)

        audio_data = b"".join(self.frames)

        if hasattr(self, 'boost_var') and self.boost_var.get():
            try:
                import numpy as np
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                audio_array = np.clip(audio_array * 3.0, -32768, 32767).astype(np.int16)
                audio_data = audio_array.tobytes()
            except Exception as e:
                print(f"Erro ao aplicar boost de volume: {e}")

        with wave.open(filepath, "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.sample_width)
            wav_file.setframerate(self.rate)
            wav_file.writeframes(audio_data)

        self.after(0, lambda: self.file_label.configure(text=f"Salvo em: {filename}", text_color=ORANGE))
        return filepath

    def update_ui_loop(self):
        if not self.is_recording or not self.recording_start_time:
            return

        elapsed = time.time() - self.recording_start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)

        size_mb = self.current_file_size / (1024 * 1024)
        self.time_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.size_label.configure(text=f"{size_mb:.2f} MB / 20.00 MB")

        self.after(500, self.update_ui_loop)

    def destroy(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        super().destroy()
