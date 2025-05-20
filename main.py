import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd
import numpy as np
import wave
import threading
import whisper
from datetime import datetime
from pydub import AudioSegment


RECORDINGS_DIR = "recordings"
TRANSCRIPTS_FILE = os.path.join(RECORDINGS_DIR, "transcripts.json")
SAMPLE_RATE = 16000
CHANNELS = 1

class VoiceToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice-to-Text Transcriber")
        
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Set window size
        window_width = int(screen_width * 0.75)
        window_height = int(screen_height * 0.75)

        # Calculate position
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Set geometry
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.is_recording = False
        self.audio = []
        self.model_name = "base"
        self.model = None
        self.progress_dialog = None

        os.makedirs(RECORDINGS_DIR, exist_ok=True)
        self.transcripts = self.load_transcripts()

        self.playback_after_id = None
        self.is_playing = False

        self.setup_ui()
        self.load_model_async(self.model_name)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        controls = ttk.Frame(main_frame)
        controls.pack(pady=10, fill="x")

        ttk.Label(controls, text="Language:").pack(side="left", padx=5)
        self.lang_var = tk.StringVar(value="en")
        ttk.Combobox(controls, textvariable=self.lang_var, values=["en", "uk", "es", "de"], width=5).pack(side="left")

        ttk.Label(controls, text="Model:").pack(side="left", padx=(20,5))
        self.model_var = tk.StringVar(value=self.model_name)
        self.model_dropdown = ttk.Combobox(controls, textvariable=self.model_var, values=["base", "small"], width=7, state="readonly")
        self.model_dropdown.pack(side="left")
        self.model_dropdown.bind("<<ComboboxSelected>>", self.on_model_change)

        self.record_btn = ttk.Button(controls, text="Start Recording", command=self.toggle_recording)
        self.record_btn.pack(side="left", padx=15)

        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack(fill="x", pady=(0,10))

        self.transcription_box = tk.Text(main_frame, height=8, wrap=tk.WORD)
        self.transcription_box.pack(fill="both", expand=True, pady=10)

        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=(0, 10))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.stop_btn = ttk.Button(progress_frame, text="Stop Playback", command=self.stop_playback, state="disabled")
        self.stop_btn.pack(side="left")

        history_frame = ttk.LabelFrame(main_frame, text="Recording History")
        history_frame.pack(fill="both", expand=True)
        self.setup_history_table(history_frame)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Play Recording", command=self.play_selected_recording)
        self.menu.add_command(label="Remove Recording", command=self.remove_selected_recording)

        self.root.bind("<Button-1>", self.hide_menu_on_click_outside)

    def show_progress_dialog(self, message):
        self.progress_dialog = tk.Toplevel(self.root)
        self.progress_dialog.title("Please wait...")
        self.progress_dialog.geometry("680x100")
        self.progress_dialog.transient(self.root)
        self.progress_dialog.grab_set()
        self.progress_dialog.resizable(False, False)

        label = ttk.Label(self.progress_dialog, text=message)
        label.pack(pady=(20, 10))

        progress = ttk.Progressbar(self.progress_dialog, mode='indeterminate')
        progress.pack(padx=20, fill='x')
        progress.start()

    def close_progress_dialog(self):
        if self.progress_dialog and self.progress_dialog.winfo_exists():
            self.progress_dialog.grab_release()
            self.progress_dialog.destroy()
            self.progress_dialog = None

    def load_model_async(self, model_name):
        self.show_progress_dialog(f"Downloading/Loading AI Whisper model '{model_name}'...")

        def load():
            try:
                self.record_btn.config(state="disabled")
                self.model_dropdown.config(state="disabled")
                self.model = whisper.load_model(model_name)
                self.model_name = model_name
                self.status_var.set(f"Model '{model_name}' loaded.")
            except Exception as e:
                self.show_error(f"Failed to load model '{model_name}': {e}")
                self.status_var.set("Error loading model")
            finally:
                self.root.after(0, self.close_progress_dialog)
                self.root.after(0, lambda: self.record_btn.config(state="normal"))
                self.root.after(0, lambda: self.model_dropdown.config(state="readonly"))

        threading.Thread(target=load, daemon=True).start()

    def on_model_change(self, event):
        selected_model = self.model_var.get()
        if selected_model != self.model_name:
            self.load_model_async(selected_model)

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.audio = []
        self.is_recording = True
        self.record_btn.config(text="Stop Recording")
        threading.Thread(target=self.record, daemon=True).start()

    def record(self):
        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=self.audio_callback):
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            self.show_error(f"Recording error: {e}")

    def audio_callback(self, indata, frames, time, status):
        self.audio.append(indata.copy())

    def stop_recording(self):
        self.is_recording = False
        self.record_btn.config(text="Start Recording")
        audio_data = np.concatenate(self.audio)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.wav"
        filepath = os.path.join(RECORDINGS_DIR, filename)

        with wave.open(filepath, mode='wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

        threading.Thread(target=self.transcribe_audio, args=(filepath, filename), daemon=True).start()

    def transcribe_audio(self, filepath, filename):
        try:
            language = self.lang_var.get()
            self.status_var.set(f"Transcribing '{filename}' with model '{self.model_name}'...")
            result = self.model.transcribe(filepath, language=language)
            text = result['text']
            self.transcripts[filename] = {
                "text": text,
                "language": language,
                "model": self.model_name
            }
            self.save_transcripts()
            self.load_history()
            self.status_var.set(f"Transcription complete: '{filename}'")
        except Exception as e:
            self.show_error(f"Transcription error: {e}")
            self.status_var.set("Error during transcription")

    def setup_history_table(self, parent):
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)  # Set desired row height (e.g., 30 pixels)

        columns = ("file", "duration", "date", "summary", "language", "model")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())

        self.tree.column("file", width=190)
        self.tree.column("duration", width=70, anchor="center")
        self.tree.column("date", width=150)
        self.tree.column("summary", width=200)
        self.tree.column("language", width=50, anchor="center")
        self.tree.column("model", width=80, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)

        self.load_history()

    def get_audio_duration(self, filepath):
        try:
            audio = AudioSegment.from_file(filepath)
            return len(audio) / 1000.0
        except Exception as e:
            self.show_error(f"Duration error: {e}")
            return 0.0

    def load_history(self):
        self.tree.delete(*self.tree.get_children())
        for filename in sorted(os.listdir(RECORDINGS_DIR), reverse=True):
            if filename.endswith(".wav"):
                filepath = os.path.join(RECORDINGS_DIR, filename)
                stat = os.stat(filepath)
                duration = self.get_audio_duration(filepath)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                entry = self.transcripts.get(filename, {})
                text = entry.get("text", "") if isinstance(entry, dict) else entry
                lang = entry.get("language", "") if isinstance(entry, dict) else ""
                model = entry.get("model", "") if isinstance(entry, dict) else ""
                short_text = (text[:50] + "...") if len(text) > 50 else text
                self.tree.insert("", "end", values=(filename, f"{duration:.1f}s", mtime, short_text, lang, model))

    def on_tree_select(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            filename = self.tree.item(row_id, "values")[0]
            entry = self.transcripts.get(filename, {})
            full_text = entry.get("text", "No transcription available.") if isinstance(entry, dict) else entry
            self.transcription_box.delete("1.0", tk.END)
            self.transcription_box.insert("end", full_text)

    def on_double_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            filename = self.tree.item(row_id, "values")[0]
            filepath = os.path.join(RECORDINGS_DIR, filename)
            self.start_playback(filepath)

    def on_right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.menu.post(event.x_root, event.y_root)

    def hide_menu_on_click_outside(self, event):
        self.menu.unpost()

    def play_selected_recording(self):
        selected = self.tree.selection()
        if selected:
            filename = self.tree.item(selected[0], "values")[0]
            filepath = os.path.join(RECORDINGS_DIR, filename)
            self.start_playback(filepath)

    def remove_selected_recording(self):
        selected = self.tree.selection()
        if selected:
            filename = self.tree.item(selected[0], "values")[0]
            if messagebox.askyesno("Confirm Delete", f"Remove recording '{filename}'?"):
                try:
                    filepath = os.path.join(RECORDINGS_DIR, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    if filename in self.transcripts:
                        del self.transcripts[filename]
                        self.save_transcripts()
                    self.load_history()
                    self.transcription_box.delete("1.0", tk.END)
                except Exception as e:
                    self.show_error(f"Error removing recording: {e}")

    def start_playback(self, filepath):
        self.stop_playback()
        audio = AudioSegment.from_file(filepath)
        samples = np.array(audio.get_array_of_samples())

        # Handle stereo audio
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))

        # Normalize samples to float32 between -1 and 1
        dtype = samples.dtype
        if dtype == np.int16:
            samples = samples.astype(np.float32) / 32768
        elif dtype == np.int32:
            samples = samples.astype(np.float32) / 2147483648
        else:
            samples = samples.astype(np.float32)

        self.is_playing = True
        self.stop_btn.config(state="normal")

        sd.play(samples, samplerate=audio.frame_rate)

        duration = len(audio) / 1000.0
        start_time = datetime.now()

        def update_progress():
            if not self.is_playing:
                self.progress_var.set(0)
                self.stop_btn.config(state="disabled")
                self.playback_after_id = None
                return
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= duration:
                self.is_playing = False
                self.progress_var.set(0)
                self.stop_btn.config(state="disabled")
                self.playback_after_id = None
                return
            progress = min(elapsed / duration * 100, 100)
            self.progress_var.set(progress)
            self.playback_after_id = self.root.after(100, update_progress)

        update_progress()

    def stop_playback(self):
        if self.is_playing:
            sd.stop()
            self.is_playing = False
        self.progress_var.set(0)
        self.stop_btn.config(state="disabled")
        if self.playback_after_id:
            self.root.after_cancel(self.playback_after_id)
            self.playback_after_id = None


    def load_transcripts(self):
        if os.path.exists(TRANSCRIPTS_FILE):
            try:
                with open(TRANSCRIPTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_transcripts(self):
        try:
            with open(TRANSCRIPTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.transcripts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_error(f"Saving transcripts failed: {e}")

    def show_error(self, message):
        messagebox.showerror("Error", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceToTextApp(root)
    root.mainloop()
