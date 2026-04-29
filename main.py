import threading
import customtkinter as ctk

from recorder import Recorder
from transcriber import Transcriber
from improver import Improver
from logger import log_session

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

IDLE = "idle"
LOADING = "loading"
RECORDING = "recording"
TRANSCRIBING = "transcribing"
IMPROVING = "improving"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Voice Prompt")
        self.geometry("640x520")
        self.resizable(False, False)

        self._transcriber = Transcriber()
        self._improver = Improver()
        self._recorder = Recorder()
        self._state = IDLE
        self._models_loaded = False

        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._status = ctk.CTkLabel(self, text="Ready", font=("Helvetica", 13))
        self._status.pack(pady=(16, 4))

        self._textbox = ctk.CTkTextbox(self, width=600, height=280, font=("Helvetica", 13))
        self._textbox.pack(pady=(4, 12))

        # Button row — contents swap based on state
        self._btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._btn_frame.pack(pady=(0, 8))

        self._record_btn = ctk.CTkButton(
            self._btn_frame, text="● Record", width=140, height=48,
            font=("Helvetica", 15, "bold"), command=self._on_record,
        )
        self._stop_btn = ctk.CTkButton(
            self._btn_frame, text="■ Stop", width=120, height=48,
            font=("Helvetica", 15, "bold"), fg_color="#2980b9",
            command=self._on_stop,
        )
        self._cancel_btn = ctk.CTkButton(
            self._btn_frame, text="Cancel", width=100, height=48,
            fg_color="#555", command=self._on_cancel,
        )
        self._improve_btn = ctk.CTkButton(
            self._btn_frame, text="Improve →", width=120, height=48,
            command=self._on_improve,
        )
        self._clear_btn = ctk.CTkButton(
            self._btn_frame, text="Clear", width=90, height=48,
            fg_color="#555", command=self._on_clear,
        )
        self._copy_btn = ctk.CTkButton(
            self._btn_frame, text="Copy", width=80, height=48,
            command=self._on_copy,
        )

        self._set_idle_buttons()

    def _set_idle_buttons(self):
        for w in self._btn_frame.winfo_children():
            w.pack_forget()
        self._record_btn.pack(side="left", padx=5)
        self._improve_btn.pack(side="left", padx=5)
        self._clear_btn.pack(side="left", padx=5)
        self._copy_btn.pack(side="left", padx=5)

    def _set_recording_buttons(self):
        for w in self._btn_frame.winfo_children():
            w.pack_forget()
        self._stop_btn.pack(side="left", padx=5)
        self._cancel_btn.pack(side="left", padx=5)
        self._clear_btn.pack(side="left", padx=5)

    # ── Actions ──────────────────────────────────────────────────────────────

    def _on_record(self):
        self._state = LOADING
        self._status.configure(text="Loading models..." if not self._models_loaded else "Recording...")
        self._set_recording_buttons()
        if not self._models_loaded:
            threading.Thread(target=self._load_models_then_record, daemon=True).start()
        else:
            self._begin_recording()

    def _load_models_then_record(self):
        self._transcriber.load()
        # Qwen loads in parallel — warm by the time user hits Improve
        threading.Thread(target=self._improver.load, daemon=True).start()
        self._models_loaded = True
        self.after(0, self._begin_recording)

    def _begin_recording(self):
        self._state = RECORDING
        self._status.configure(text="Recording...")
        self._recorder.start()

    def _on_stop(self):
        if self._state != RECORDING:
            return
        self._state = TRANSCRIBING
        audio = self._recorder.stop()
        self._status.configure(text="Transcribing...")
        for w in self._btn_frame.winfo_children():
            w.pack_forget()
        threading.Thread(target=self._do_transcribe, args=(audio,), daemon=True).start()

    def _on_cancel(self):
        self._recorder.stop()
        self._state = IDLE
        self._status.configure(text="Ready")
        self._set_idle_buttons()

    def _do_transcribe(self, audio):
        text = self._transcriber.transcribe(audio)
        self.after(0, lambda: self._on_transcribed(text))

    def _on_transcribed(self, text):
        if text:
            current = self._textbox.get("1.0", "end").strip()
            separator = "\n\n" if current else ""
            self._textbox.insert("end", separator + text)
        self._state = IDLE
        self._status.configure(text="Ready")
        self._set_idle_buttons()

    def _on_improve(self):
        raw = self._textbox.get("1.0", "end").strip()
        if not raw:
            return
        if not self._models_loaded:
            self._status.configure(text="Loading model...")
            threading.Thread(target=self._load_improver_then_improve, args=(raw,), daemon=True).start()
            return
        self._state = IMPROVING
        for w in self._btn_frame.winfo_children():
            w.pack_forget()
        self._status.configure(text="Improving...")
        threading.Thread(target=self._do_improve, args=(raw,), daemon=True).start()

    def _load_improver_then_improve(self, raw):
        self._transcriber.load()
        self._improver.load()
        self._models_loaded = True
        self.after(0, lambda: self._on_improve())

    def _do_improve(self, raw):
        result = self._improver.improve(raw)
        self.after(0, lambda: self._on_improved(result))

    def _on_improved(self, result):
        raw = self._textbox.get("1.0", "end").strip()
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", result)
        self._state = IDLE
        self._status.configure(text="Done — edit as needed")
        self._set_idle_buttons()
        threading.Thread(target=log_session, args=(raw, result), daemon=True).start()

    def _on_clear(self):
        self._textbox.delete("1.0", "end")
        if self._state == RECORDING:
            self._recorder.stop()
        self._state = IDLE
        self._status.configure(text="Ready")
        self._set_idle_buttons()

    def _on_copy(self):
        text = self._textbox.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self._copy_btn.configure(text="Copied ✓")
        self.after(1500, lambda: self._copy_btn.configure(text="Copy"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
