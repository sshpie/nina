#!/usr/bin/env python3
"""nina GUI — Microsoft neural TTS desktop app."""

import asyncio
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import edge_tts

# ── Colours ──────────────────────────────────────────────────────────────────
BG      = "#0f0f1e"
BG2     = "#1a1a30"
BG3     = "#22223a"
FG      = "#dde0ff"
FG2     = "#8890bb"
ACCENT  = "#4a7aff"
RED     = "#ff5555"
GREEN   = "#44ee88"
FONT    = ("Inter", 11) if sys.platform != "darwin" else ("SF Pro Text", 11)
MONO    = ("JetBrains Mono", 10)


# ── Async worker ─────────────────────────────────────────────────────────────
class TTSWorker:
    """Runs TTS in a background thread with its own asyncio loop."""

    def __init__(self, on_chunk, on_done, on_error):
        self._loop   = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._proc        = None
        self._cancel_flag = threading.Event()
        self.on_chunk     = on_chunk
        self.on_done      = on_done
        self.on_error     = on_error
        self._voices      = []

    # voices ------------------------------------------------------------------
    def load_voices(self, callback):
        async def _load():
            try:
                voices = await edge_tts.list_voices()
                self._voices = sorted(voices, key=lambda v: v["ShortName"])
                callback(self._voices)
            except Exception as e:
                callback(None)
        asyncio.run_coroutine_threadsafe(_load(), self._loop)

    # playback ----------------------------------------------------------------
    def play(self, text: str, voice_id: str, rate: str):
        self._cancel_flag.clear()

        async def _speak():
            chunks = text.strip().split("\n\n")
            total  = len(chunks)
            try:
                for idx, chunk in enumerate(chunks):
                    if self._cancel_flag.is_set():
                        break
                    chunk = chunk.strip()
                    if not chunk:
                        continue
                    self.on_chunk(idx + 1, total, chunk[:60] + ("…" if len(chunk) > 60 else ""))
                    communicate = edge_tts.Communicate(chunk, voice_id, rate=rate)
                    proc = subprocess.Popen(
                        ["mpv", "--no-video", "--really-quiet", "--audio-display=no", "-"],
                        stdin=subprocess.PIPE,
                    )
                    self._proc = proc
                    async for seg in communicate.stream():
                        if self._cancel_flag.is_set():
                            proc.terminate()
                            break
                        if seg["type"] == "audio":
                            try:
                                proc.stdin.write(seg["data"])
                            except BrokenPipeError:
                                break
                    proc.stdin.close()
                    proc.wait()
                    self._proc = None
                self.on_done()
            except Exception as e:
                self.on_error(str(e))

        asyncio.run_coroutine_threadsafe(_speak(), self._loop)

    def stop(self):
        self._cancel_flag.set()
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
            self._proc = None


# ── Main window ──────────────────────────────────────────────────────────────
class NinaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nina")
        self.geometry("720x540")
        self.minsize(500, 400)
        self.configure(bg=BG)
        self._configure_style()

        self._playing  = False
        self._voices   = []
        self._voice_map = {}  # display name -> voice ID

        self._worker = TTSWorker(
            on_chunk=self._on_chunk,
            on_done=self._on_done,
            on_error=self._on_error,
        )

        self._build_ui()
        self._load_voices()

    # ── Style ─────────────────────────────────────────────────────────────────
    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".",
            background=BG, foreground=FG,
            fieldbackground=BG2, selectbackground=ACCENT,
            font=FONT)
        style.configure("TCombobox",
            background=BG3, foreground=FG,
            fieldbackground=BG2, arrowcolor=FG2)
        style.map("TCombobox",
            fieldbackground=[("readonly", BG2)],
            foreground=[("readonly", FG)])
        style.configure("TLabel",  background=BG,  foreground=FG)
        style.configure("TFrame",  background=BG)
        style.configure("Status.TLabel", background=BG, foreground=FG2, font=(*FONT[:1], 10))

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Title bar row
        title_row = ttk.Frame(self)
        title_row.pack(fill="x", padx=16, pady=(14, 4))

        title_lbl = ttk.Label(title_row, text="NINA", font=("Inter", 13, "bold"))
        title_lbl["foreground"] = ACCENT
        title_lbl.pack(side="left")

        self._status_lbl = ttk.Label(title_row, text="Loading voices…", style="Status.TLabel")
        self._status_lbl.pack(side="right")

        # ── Controls row
        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=16, pady=4)

        ttk.Label(ctrl, text="Voice", foreground=FG2).pack(side="left")
        self._voice_var = tk.StringVar(value="Loading…")
        self._voice_box = ttk.Combobox(ctrl, textvariable=self._voice_var,
                                       state="readonly", width=38)
        self._voice_box.pack(side="left", padx=(6, 16))

        ttk.Label(ctrl, text="Speed", foreground=FG2).pack(side="left")
        self._rate_var = tk.StringVar(value="+0%")
        rate_box = ttk.Combobox(ctrl, textvariable=self._rate_var, state="readonly", width=8,
                                values=["-25%", "-15%", "+0%", "+15%", "+25%", "+50%", "+75%"])
        rate_box.pack(side="left", padx=(6, 0))

        # ── Search row
        search_row = ttk.Frame(self)
        search_row.pack(fill="x", padx=16, pady=(4, 2))
        ttk.Label(search_row, text="Filter voices:", foreground=FG2).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._filter_voices)
        search_entry = tk.Entry(search_row, textvariable=self._search_var,
                                bg=BG2, fg=FG, insertbackground=FG,
                                relief="flat", font=FONT, width=32)
        search_entry.pack(side="left", padx=(6, 0))

        # ── Text area
        text_frame = ttk.Frame(self)
        text_frame.pack(fill="both", expand=True, padx=16, pady=6)

        self._text = tk.Text(
            text_frame, bg=BG2, fg=FG, insertbackground=FG,
            selectbackground=ACCENT, relief="flat", font=FONT,
            padx=10, pady=8, wrap="word", undo=True,
        )
        self._text.pack(fill="both", expand=True)
        self._text.insert("1.0", "Paste or type text here…")
        self._text.bind("<FocusIn>", self._clear_placeholder)

        scrollbar = tk.Scrollbar(text_frame, command=self._text.yview,
                                 bg=BG3, troughcolor=BG, relief="flat")
        scrollbar.pack(side="right", fill="y")
        self._text.config(yscrollcommand=scrollbar.set)

        # ── Button row
        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", padx=16, pady=(4, 12))

        self._play_btn  = self._mk_btn(btn_row, "▶  Play",  self._toggle_play, ACCENT)
        self._stop_btn  = self._mk_btn(btn_row, "■  Stop",  self._stop,        BG3)
        self._clip_btn  = self._mk_btn(btn_row, "📋 Clipboard", self._paste_clipboard, BG3)
        self._clear_btn = self._mk_btn(btn_row, "✕ Clear",  self._clear_text,  BG3)

        self._chunk_lbl = ttk.Label(btn_row, text="", style="Status.TLabel")
        self._chunk_lbl.pack(side="right")

    def _mk_btn(self, parent, label, cmd, bg):
        b = tk.Button(parent, text=label, command=cmd,
                      bg=bg, fg=FG, activebackground=ACCENT, activeforeground="white",
                      relief="flat", font=FONT, padx=10, pady=4, cursor="hand2")
        b.pack(side="left", padx=(0, 6))
        return b

    # ── Voice loading ─────────────────────────────────────────────────────────
    def _load_voices(self):
        def callback(voices):
            if not voices:
                self.after(0, lambda: self._status("Failed to load voices — check connection"))
                return
            self._voices = voices
            self._rebuild_voice_list(voices)

        self._worker.load_voices(callback)

    def _rebuild_voice_list(self, voices):
        entries = []
        for v in voices:
            name  = v["ShortName"]          # en-US-AriaNeural
            parts = name.split("-")
            label = f"{parts[2].replace('Neural','').replace('Multilingual',' (ML)')} · {v['Locale']}"
            entries.append(label)
            self._voice_map[label] = name

        def _update():
            self._voice_box["values"] = entries
            # Default to Aria
            aria = next((e for e in entries if "Aria" in e and "en-US" in e), entries[0])
            self._voice_var.set(aria)
            self._status(f"Ready  •  {len(voices)} voices loaded")

        self.after(0, _update)

    def _filter_voices(self, *_):
        q = self._search_var.get().lower()
        filtered = [k for k in self._voice_map if q in k.lower()]
        self._voice_box["values"] = filtered
        if filtered and self._voice_var.get() not in filtered:
            self._voice_var.set(filtered[0])

    # ── Playback ──────────────────────────────────────────────────────────────
    def _toggle_play(self):
        if self._playing:
            self._worker.stop()
            self._playing = False
            self._play_btn.config(text="▶  Play", bg=ACCENT)
            self._status("Stopped")
            return

        text = self._text.get("1.0", "end").strip()
        if not text or text == "Paste or type text here…":
            messagebox.showwarning("Nina", "Paste or type some text first.")
            return

        voice_label = self._voice_var.get()
        voice_id    = self._voice_map.get(voice_label)
        if not voice_id:
            messagebox.showerror("Nina", f"Voice not found: {voice_label}")
            return

        rate = self._rate_var.get()
        self._playing = True
        self._play_btn.config(text="⏸  Pause", bg=BG3)
        self._status("Playing…")
        self._worker.play(text, voice_id, rate)

    def _stop(self):
        self._worker.stop()
        self._playing = False
        self._play_btn.config(text="▶  Play", bg=ACCENT)
        self._chunk_lbl.config(text="")
        self._status("Ready")

    # ── Callbacks from worker (cross-thread → schedule on main loop) ──────────
    def _on_chunk(self, idx, total, preview):
        self.after(0, lambda: (
            self._chunk_lbl.config(text=f"{idx}/{total}"),
            self._status(f"Reading: {preview}"),
        ))

    def _on_done(self):
        def _done():
            self._playing = False
            self._play_btn.config(text="▶  Play", bg=ACCENT)
            self._chunk_lbl.config(text="")
            self._status("Done")
        self.after(0, _done)

    def _on_error(self, msg):
        def _err():
            self._playing = False
            self._play_btn.config(text="▶  Play", bg=ACCENT)
            self._status(f"Error: {msg}")
        self.after(0, _err)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _status(self, msg):
        self._status_lbl.config(text=msg)

    def _clear_placeholder(self, _event):
        if self._text.get("1.0", "end").strip() == "Paste or type text here…":
            self._text.delete("1.0", "end")

    def _paste_clipboard(self):
        try:
            text = self.clipboard_get()
            self._text.delete("1.0", "end")
            self._text.insert("1.0", text)
        except tk.TclError:
            messagebox.showinfo("Nina", "Clipboard is empty.")

    def _clear_text(self):
        self._stop()
        self._text.delete("1.0", "end")
        self._text.insert("1.0", "Paste or type text here…")


def main():
    app = NinaApp()
    app.mainloop()


if __name__ == "__main__":
    main()
