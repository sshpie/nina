#!/usr/bin/env python3
"""nina GUI — open source neural TTS desktop app."""

import asyncio
import json
import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
import edge_tts

# ── Colours ──────────────────────────────────────────────────────────────────
BG      = "#1c1c2e"
BG2     = "#2a2a40"
BG3     = "#363650"
FG      = "#ffffff"
FG2     = "#aab0cc"
ACCENT  = "#5a8aff"
RED     = "#ff6677"
GREEN   = "#44ee88"
FONT    = ("Inter", 11) if sys.platform != "darwin" else ("SF Pro Text", 11)
MONO    = ("JetBrains Mono", 10)

PROGRESS_FILE = Path.home() / ".config" / "nina" / "progress.json"
LIBRARY_DIR   = Path.home() / "VDT" / "books"


# ── Library window ────────────────────────────────────────────────────────────
class LibraryWindow(tk.Toplevel):
    """Scrollable panel listing all books in ~/chainsaw/books/."""

    def __init__(self, parent, progress: dict, on_open):
        super().__init__(parent)
        self.title("Nina — Library")
        self.geometry("540x520")
        self.minsize(400, 300)
        self.configure(bg=BG)
        self.resizable(True, True)
        self._on_open = on_open
        self._progress = progress
        self._all_books: list[tuple[str, str]] = []  # [(display_label, path)]

        self._build()
        self._populate()
        self.grab_set()   # modal

    def _build(self):
        # Search row
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(top, text="🔍", bg=BG, fg=FG2, font=("Inter", 11)).pack(side="left")
        self._q = tk.StringVar()
        self._q.trace_add("write", lambda *_: self._filter())
        tk.Entry(top, textvariable=self._q, bg=BG2, fg=FG, insertbackground=FG,
                 relief="flat", font=("Inter", 11), width=36).pack(side="left", padx=(6, 0), fill="x", expand=True)

        # Listbox + scrollbar
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        sb = tk.Scrollbar(frame, bg=BG3, troughcolor=BG, relief="flat")
        sb.pack(side="right", fill="y")
        self._lb = tk.Listbox(frame, bg=BG2, fg=FG, selectbackground=ACCENT,
                              selectforeground="#ffffff", relief="flat",
                              font=("Inter", 11), activestyle="none",
                              yscrollcommand=sb.set, borderwidth=0,
                              highlightthickness=0)
        self._lb.pack(side="left", fill="both", expand=True)
        sb.config(command=self._lb.yview)
        self._lb.bind("<Double-Button-1>", self._open_selected)
        self._lb.bind("<Return>", self._open_selected)

        # Bottom buttons
        bot = tk.Frame(self, bg=BG)
        bot.pack(fill="x", padx=12, pady=(0, 12))
        tk.Button(bot, text="▶ Open", command=self._open_selected,
                  bg=ACCENT, fg=FG, activebackground="#6a9aff", activeforeground=FG,
                  relief="flat", font=("Inter", 11), padx=14, pady=5,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(bot, text="Browse for file…", command=self._browse,
                  bg=BG3, fg=FG, activebackground=ACCENT, activeforeground=FG,
                  relief="flat", font=("Inter", 11), padx=10, pady=5,
                  cursor="hand2").pack(side="left")
        tk.Button(bot, text="Cancel", command=self.destroy,
                  bg=BG3, fg=FG2, activebackground=BG3, activeforeground=FG,
                  relief="flat", font=("Inter", 11), padx=10, pady=5,
                  cursor="hand2").pack(side="right")

    def _dir_to_title(self, name: str) -> str:
        """'gray-hat-hacking-the-ethical-hacker-s-handbook-6e' → readable title."""
        name = re.sub(r'^\d{10,13}-', '', name)   # strip ISBN prefix
        return name.replace('-', ' ').replace('_', ' ').title()

    def _populate(self):
        self._all_books = []
        if not LIBRARY_DIR.exists():
            self._lb.insert("end", f"  Library not found: {LIBRARY_DIR}")
            return

        for entry in sorted(LIBRARY_DIR.iterdir()):
            if not entry.is_dir() or entry.name.startswith('.'):
                continue
            # Determine if entry is a category dir (contains subdirs) or a book dir (contains .md)
            subdirs = [c for c in entry.iterdir() if c.is_dir()]
            md_files = [f for f in entry.iterdir() if f.suffix == '.md']
            if md_files:
                # Direct book (top-level book dir)
                label = f"Other / {self._dir_to_title(entry.name)}"
                saved = self._progress.get(str(entry))
                if saved:
                    label += f"  [ch {saved + 1}]"
                self._all_books.append((label, str(entry)))
            elif subdirs:
                # Category directory — list each book inside
                cat = entry.name.replace('-', ' ').replace('_', ' ').title()
                for book_dir in sorted(subdirs):
                    label = f"{cat} / {self._dir_to_title(book_dir.name)}"
                    saved = self._progress.get(str(book_dir))
                    if saved:
                        label += f"  [ch {saved + 1}]"
                    self._all_books.append((label, str(book_dir)))

        self._refresh_list(self._all_books)

    def _filter(self):
        q = self._q.get().lower()
        if not q:
            self._refresh_list(self._all_books)
        else:
            filtered = [(l, p) for l, p in self._all_books if q in l.lower()]
            self._refresh_list(filtered)

    def _refresh_list(self, items):
        self._lb.delete(0, "end")
        self._shown = items
        for label, _ in items:
            self._lb.insert("end", f"  {label}")
        if items:
            self._lb.selection_set(0)

    def _open_selected(self, _event=None):
        sel = self._lb.curselection()
        if not sel:
            return
        _, path = self._shown[sel[0]]
        self.destroy()
        self._on_open(path)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Open Book",
            filetypes=[("Books", "*.txt *.pdf *.epub"), ("All files", "*.*")],
            initialdir=str(LIBRARY_DIR) if LIBRARY_DIR.exists() else str(Path.home()),
        )
        if path:
            self.destroy()
            self._on_open(path)


# ── Book loader ───────────────────────────────────────────────────────────────
class BookLoader:
    """Parse books into (title, text) chapter lists from TXT, PDF, or EPUB."""

    CHAINSAW_RE = re.compile(r'\n===== FILE \d+/\d+: (.+?) =====\n')
    CHAPTER_RE  = re.compile(
        r'\n(?=(?:Chapter|CHAPTER|Part|PART|Section|SECTION)\s+\d+)', re.M
    )
    SKIP_NAMES  = {'toc', 'cover', 'nav', 'ncx', 'opf', 'copyright',
                   'title', 'titlepage', 'colophon', 'halftitle',
                   'fm', 'fm2', 'ata', 'gla', 'ack', 'contents',
                   'dedication', 'about', 'copy', 'pre', 'int', 'p1', 'p2'}

    def load(self, path: str):
        p = Path(path)
        if p.is_dir():
            return self._load_book_dir(p)
        ext = p.suffix.lower()
        if ext == '.pdf':
            return self._load_pdf(path)
        if ext == '.epub':
            return self._load_epub(path)
        return self._load_txt(path)

    # ── Directory of .md files (VDT format) ──────────────────────────────────
    def _load_book_dir(self, dirpath: Path):
        md_files = sorted(dirpath.glob('*.md'))
        chapters = []
        for f in md_files:
            stem = re.sub(r'^\d+-', '', f.stem).lower()  # strip leading number
            if stem in self.SKIP_NAMES:
                continue
            text = f.read_text(encoding='utf-8', errors='replace').strip()
            if len(text) < 150:
                continue
            title = stem.replace('-', ' ').replace('_', ' ').title()
            chapters.append((title, text))
        if not chapters:
            # Fallback: include everything
            chapters = [(re.sub(r'^\d+-', '', f.stem).title(),
                         f.read_text(errors='replace').strip())
                        for f in md_files if f.stat().st_size > 50]
        return chapters

    # ── TXT ──────────────────────────────────────────────────────────────────
    def _load_txt(self, path):
        text = Path(path).read_text(encoding='utf-8', errors='replace')
        if '===== FILE' in text:
            return self._parse_chainsaw(text, Path(path).stem)
        parts = self.CHAPTER_RE.split(text)
        if len(parts) > 2:
            chapters = []
            for i, p in enumerate(parts):
                p = p.strip()
                if not p:
                    continue
                first = p.split('\n')[0].strip()
                title = first if first else f"Section {i + 1}"
                chapters.append((title, p))
            return chapters
        return self._chunk_plain(Path(path).stem, text)

    def _parse_chainsaw(self, text, stem):
        m = re.search(r'^TITLE:\s*(.+)$', text, re.M)
        book_title = m.group(1).strip() if m else stem
        parts = self.CHAINSAW_RE.split(text)
        # parts alternates: [preamble, filename, content, filename, content …]
        chapters = []
        for i in range(1, len(parts) - 1, 2):
            fname   = parts[i].strip()
            content = parts[i + 1].strip()
            if len(content) < 200:
                continue
            base = re.sub(r'\.(x?html?|xhtml)$', '', fname, flags=re.I).lower()
            if any(skip in base for skip in self.SKIP_NAMES):
                continue
            title = (fname.replace('.xhtml', '').replace('.html', '')
                         .replace('-', ' ').replace('_', ' ').title())
            chapters.append((title, content))
        return chapters or [(book_title, text.strip())]

    def _chunk_plain(self, stem, text, words=1500):
        word_list = text.split()
        chunks = []
        for i in range(0, len(word_list), words):
            part = ' '.join(word_list[i:i + words])
            n = i // words + 1
            chunks.append((f"{stem} — Part {n}", part))
        return chunks or [(stem, text.strip())]

    # ── PDF ──────────────────────────────────────────────────────────────────
    def _load_pdf(self, path):
        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            per_chunk, chunks = 8, []
            for i in range(0, len(reader.pages), per_chunk):
                batch = reader.pages[i:i + per_chunk]
                text  = '\n\n'.join(p.extract_text() or '' for p in batch)
                if text.strip():
                    end = min(i + per_chunk, len(reader.pages))
                    chunks.append((f"Pages {i + 1}–{end}", text))
            return chunks or [("Document", "Could not extract text.")]
        except Exception as e:
            return [("Error", f"PDF load failed: {e}")]

    # ── EPUB ─────────────────────────────────────────────────────────────────
    def _load_epub(self, path):
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            book     = epub.read_epub(path)
            chapters = []
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                soup  = BeautifulSoup(item.get_content(), 'html.parser')
                text  = soup.get_text('\n', strip=True)
                if len(text) < 200:
                    continue
                h     = soup.find(['h1', 'h2', 'h3'])
                title = h.get_text().strip() if h else item.get_name()
                chapters.append((title, text))
            return chapters
        except ImportError:
            return [("Error", "pip install ebooklib beautifulsoup4")]
        except Exception as e:
            return [("Error", f"EPUB load failed: {e}")]


# ── Async TTS worker ──────────────────────────────────────────────────────────
class TTSWorker:
    """Runs TTS in a background thread with its own asyncio loop."""

    def __init__(self, on_chunk, on_done, on_error):
        self._loop        = asyncio.new_event_loop()
        self._thread      = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._proc        = None
        self._cancel_flag = threading.Event()
        self.on_chunk     = on_chunk
        self.on_done      = on_done
        self.on_error     = on_error
        self._voices      = []

    def load_voices(self, callback):
        async def _load():
            try:
                voices = await edge_tts.list_voices()
                self._voices = sorted(voices, key=lambda v: v["ShortName"])
                callback(self._voices)
            except Exception:
                callback(None)
        asyncio.run_coroutine_threadsafe(_load(), self._loop)

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
                            proc.kill()   # SIGKILL — immediate, no buffer drain
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
                self._proc.kill()   # SIGKILL — cut audio immediately
            except Exception:
                pass
            self._proc = None


# ── Main window ───────────────────────────────────────────────────────────────
class NinaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nina")
        self.geometry("760x580")
        self.minsize(500, 420)
        self.configure(bg=BG)
        self._configure_style()

        self._playing   = False
        self._voices    = []
        self._voice_map = {}

        # ── book state
        self._book_chapters: list  = []   # [(title, text), …]
        self._chapter_idx: int     = 0
        self._book_path: str | None = None
        self._progress: dict       = self._load_progress()

        self._loader = BookLoader()
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
            selectforeground="#ffffff", insertcolor=FG, font=FONT)
        style.configure("TCombobox",
            background=BG3, foreground=FG, fieldbackground=BG2,
            arrowcolor=FG, selectforeground=FG, selectbackground=BG2)
        style.map("TCombobox",
            fieldbackground=[("readonly", BG2), ("disabled", BG)],
            foreground=[("readonly", FG), ("disabled", FG2)],
            selectforeground=[("readonly", FG)],
            selectbackground=[("readonly", BG2)])
        style.configure("TLabel",  background=BG,  foreground=FG)
        style.configure("TFrame",  background=BG)
        style.configure("Status.TLabel",  background=BG, foreground=FG2, font=(*FONT[:1], 10))
        style.configure("Book.TLabel",    background=BG2, foreground=FG,  font=(*FONT[:1], 10))
        style.configure("TScrollbar", background=BG3, troughcolor=BG, arrowcolor=FG2)

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Title row
        title_row = ttk.Frame(self)
        title_row.pack(fill="x", padx=16, pady=(14, 4))
        lbl = ttk.Label(title_row, text="NINA", font=("Inter", 13, "bold"))
        lbl["foreground"] = ACCENT
        lbl.pack(side="left")
        self._status_lbl = ttk.Label(title_row, text="Loading voices…", style="Status.TLabel")
        self._status_lbl.pack(side="right")

        # Controls row (voice / speed)
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

        # Filter row
        search_row = ttk.Frame(self)
        search_row.pack(fill="x", padx=16, pady=(4, 2))
        ttk.Label(search_row, text="Filter voices:", foreground=FG2).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._filter_voices)
        tk.Entry(search_row, textvariable=self._search_var,
                 bg=BG2, fg=FG, insertbackground=FG,
                 relief="flat", font=FONT, width=32).pack(side="left", padx=(6, 0))

        # ── Book bar (hidden until a book is loaded) ──────────────────────────
        self._book_bar = tk.Frame(self, bg=BG2)
        # Not packed yet — shown by _show_book_bar()

        # ── Row 1: title + chapter picker ─────────────────────────────────────
        bar_top = tk.Frame(self._book_bar, bg=BG2)
        bar_top.pack(fill="x", padx=10, pady=(6, 2))

        self._book_title_lbl = tk.Label(bar_top, text="", bg=BG2, fg=ACCENT,
                                         font=(*FONT[:1], 10, "bold"), anchor="w")
        self._book_title_lbl.pack(side="left")

        nav_frame = tk.Frame(bar_top, bg=BG2)
        nav_frame.pack(side="right")

        self._prev_ch_btn = tk.Button(nav_frame, text="◀", command=self._prev_chapter,
                                       bg=BG3, fg=FG, activebackground=ACCENT,
                                       activeforeground=FG, relief="flat",
                                       font=FONT, padx=6, pady=2, cursor="hand2")
        self._prev_ch_btn.pack(side="left", padx=(0, 3))

        self._chapter_var = tk.StringVar()
        self._chapter_box = ttk.Combobox(nav_frame, textvariable=self._chapter_var,
                                          state="readonly", width=26)
        self._chapter_box.pack(side="left", padx=(0, 3))
        self._chapter_box.bind("<<ComboboxSelected>>", self._on_chapter_selected)

        self._next_ch_btn = tk.Button(nav_frame, text="▶", command=self._next_chapter,
                                       bg=BG3, fg=FG, activebackground=ACCENT,
                                       activeforeground=FG, relief="flat",
                                       font=FONT, padx=6, pady=2, cursor="hand2")
        self._next_ch_btn.pack(side="left")

        # ── Row 2: scrubber (bookmark drag bar) ───────────────────────────────
        bar_bot = tk.Frame(self._book_bar, bg=BG2)
        bar_bot.pack(fill="x", padx=10, pady=(0, 6))

        self._scrubber_var = tk.IntVar(value=0)
        self._scrubber = tk.Scale(
            bar_bot, variable=self._scrubber_var, orient="horizontal",
            from_=0, to=1, showvalue=False,
            bg=BG2, fg=FG2, troughcolor=BG3, activebackground=ACCENT,
            highlightthickness=0, bd=0, sliderlength=14, width=6,
            cursor="hand2",
        )
        self._scrubber.pack(side="left", fill="x", expand=True, padx=(0, 8))
        # Load chapter on release so dragging doesn't thrash the text area
        self._scrubber.bind("<ButtonRelease-1>", self._on_scrub)

        self._scrub_lbl = tk.Label(bar_bot, text="", bg=BG2, fg=FG2,
                                    font=(*FONT[:1], 9), anchor="w", width=28)
        self._scrub_lbl.pack(side="left")

        # ── Button row ────────────────────────────────────────────────────────
        self._btn_row = ttk.Frame(self)
        self._btn_row.pack(fill="x", padx=16, pady=(6, 6))

        self._play_btn  = self._mk_btn(self._btn_row, "▶  Play",      self._toggle_play,       ACCENT)
        self._stop_btn  = self._mk_btn(self._btn_row, "■  Stop",      self._stop,              BG3)
        self._clip_btn  = self._mk_btn(self._btn_row, "📋 Clipboard", self._paste_clipboard,   BG3)
        self._clear_btn = self._mk_btn(self._btn_row, "✕ Clear",      self._clear_text,        BG3)
        self._open_btn  = self._mk_btn(self._btn_row, "📚 Open Book", self._open_book,         BG3)

        self._chunk_lbl = ttk.Label(self._btn_row, text="", style="Status.TLabel")
        self._chunk_lbl.pack(side="right")

        # ── Text area ─────────────────────────────────────────────────────────
        self._text_frame = ttk.Frame(self)
        self._text_frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        self._text = tk.Text(
            self._text_frame, bg=BG2, fg=FG, insertbackground=FG,
            selectbackground=ACCENT, relief="flat", font=FONT,
            padx=10, pady=8, wrap="word", undo=True,
        )
        self._text.pack(side="left", fill="both", expand=True)
        self._text.insert("1.0", "Paste or type text here, or click 📚 Open Book.")
        self._text.bind("<FocusIn>", self._clear_placeholder)

        scrollbar = tk.Scrollbar(self._text_frame, command=self._text.yview,
                                  bg=BG3, troughcolor=BG, relief="flat")
        scrollbar.pack(side="right", fill="y")
        self._text.config(yscrollcommand=scrollbar.set)

    def _mk_btn(self, parent, label, cmd, bg):
        b = tk.Button(parent, text=label, command=cmd,
                      bg=bg, fg=FG, activebackground=ACCENT, activeforeground="white",
                      relief="flat", font=FONT, padx=10, pady=4, cursor="hand2")
        b.pack(side="left", padx=(0, 6))
        return b

    # ── Book bar show/hide ────────────────────────────────────────────────────
    def _show_book_bar(self):
        self._book_bar.pack(fill="x", padx=0, pady=0, before=self._btn_row)

    def _hide_book_bar(self):
        self._book_bar.pack_forget()

    # ── Open book ─────────────────────────────────────────────────────────────
    def _open_book(self):
        LibraryWindow(self, self._progress, self._open_book_path)

    def _open_book_path(self, path: str):
        if not path:
            return

        self._status(f"Loading {Path(path).name}…")
        self.update_idletasks()

        chapters = self._loader.load(path)
        if not chapters:
            messagebox.showerror("Nina", "Could not extract any text from this file.")
            return

        self._book_path     = path
        self._book_chapters = chapters
        # Restore saved position or start at 0
        saved = self._progress.get(path, 0)
        self._chapter_idx   = min(saved, len(chapters) - 1)

        # Populate chapter combobox and scrubber range
        titles = [f"{i+1}. {t}" for i, (t, _) in enumerate(chapters)]
        self._chapter_box["values"] = titles
        self._chapter_var.set(titles[self._chapter_idx])
        self._scrubber.config(to=max(1, len(chapters) - 1))

        short = Path(path).stem[:50]
        self._book_title_lbl.config(text=f"📖  {short}")
        self._show_book_bar()

        self._load_chapter(self._chapter_idx)
        self._status(f"{Path(path).name}  •  {len(chapters)} chapters")

    def _load_chapter(self, idx):
        title, text = self._book_chapters[idx]
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", text)
        self._text.see("1.0")

        total = len(self._book_chapters)

        titles = self._chapter_box["values"]
        if titles:
            self._chapter_var.set(titles[idx])

        # Sync scrubber without triggering its callback
        self._scrubber.config(command="")
        self._scrubber_var.set(idx)
        self._scrubber.config(command=lambda v: None)

        self._scrub_lbl.config(text=f"{idx+1}/{total}  {title[:26]}")
        self._chunk_lbl.config(text=f"ch {idx+1}/{total}")
        self._prev_ch_btn.config(state="normal" if idx > 0 else "disabled")
        self._next_ch_btn.config(state="normal" if idx < total - 1 else "disabled")

    def _on_scrub(self, _event=None):
        idx = self._scrubber_var.get()
        if idx == self._chapter_idx:
            return
        self._stop()
        self._chapter_idx = idx
        self._load_chapter(idx)
        self._save_progress()

    def _on_chapter_selected(self, _event=None):
        idx = self._chapter_box.current()
        if idx < 0:
            return
        self._stop()
        self._chapter_idx = idx
        self._load_chapter(idx)
        self._save_progress()

    def _prev_chapter(self):
        if self._chapter_idx > 0:
            self._stop()
            self._chapter_idx -= 1
            self._load_chapter(self._chapter_idx)
            self._save_progress()

    def _next_chapter(self):
        if self._chapter_idx < len(self._book_chapters) - 1:
            self._stop()
            self._chapter_idx += 1
            self._load_chapter(self._chapter_idx)
            self._save_progress()

    # ── Progress persistence ──────────────────────────────────────────────────
    def _load_progress(self):
        try:
            if PROGRESS_FILE.exists():
                return json.loads(PROGRESS_FILE.read_text())
        except Exception:
            pass
        return {}

    def _save_progress(self):
        if not self._book_path:
            return
        self._progress[self._book_path] = self._chapter_idx
        try:
            PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
            PROGRESS_FILE.write_text(json.dumps(self._progress, indent=2))
        except Exception:
            pass

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
        en_voices = [v for v in voices if v.get("Locale", "").startswith("en-")]
        entries = []
        for v in en_voices:
            name  = v["ShortName"]
            parts = name.split("-")
            label = f"{parts[2].replace('Neural','').replace('Multilingual',' (ML)')} · {v['Locale']}"
            entries.append(label)
            self._voice_map[label] = name

        def _update():
            self._voice_box["values"] = entries
            aria = next((e for e in entries if "Aria" in e and "en-US" in e), entries[0] if entries else "")
            self._voice_var.set(aria)
            self._status(f"Ready  •  {len(entries)} English voices")
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
            self._status("Paused")
            return

        text = self._text.get("1.0", "end").strip()
        if not text or text == "Paste or type text here, or click 📚 Open Book.":
            messagebox.showwarning("Nina", "Paste text or open a book first.")
            return

        voice_label = self._voice_var.get()
        voice_id    = self._voice_map.get(voice_label)
        if not voice_id:
            messagebox.showerror("Nina", f"Voice not found: {voice_label}")
            return

        self._playing = True
        self._play_btn.config(text="⏸  Pause", bg=BG3)
        self._status("Playing…")
        self._worker.play(text, voice_id, self._rate_var.get())

    def _stop(self):
        self._worker.stop()
        self._playing = False
        self._play_btn.config(text="▶  Play", bg=ACCENT)
        self._chunk_lbl.config(
            text=f"ch {self._chapter_idx+1}/{len(self._book_chapters)}"
                 if self._book_chapters else ""
        )
        self._status("Ready")

    # ── Worker callbacks ──────────────────────────────────────────────────────
    def _on_chunk(self, idx, total, preview):
        self.after(0, lambda: (
            self._chunk_lbl.config(text=f"{idx}/{total}"),
            self._status(f"Reading: {preview}"),
        ))

    def _on_done(self):
        def _done():
            # Auto-advance to next chapter when in book mode
            if self._book_chapters and self._chapter_idx < len(self._book_chapters) - 1:
                self._chapter_idx += 1
                self._load_chapter(self._chapter_idx)
                self._save_progress()
                # Continue playing the next chapter
                _, text = self._book_chapters[self._chapter_idx]
                voice_id = self._voice_map.get(self._voice_var.get())
                if voice_id:
                    self._status(f"Chapter {self._chapter_idx + 1}…")
                    self._worker.play(text, voice_id, self._rate_var.get())
                    return
            # No more chapters or not in book mode
            self._playing = False
            self._play_btn.config(text="▶  Play", bg=ACCENT)
            self._chunk_lbl.config(text="")
            self._status("Done" if not self._book_chapters else "Book complete")
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
        placeholder = "Paste or type text here, or click 📚 Open Book."
        if self._text.get("1.0", "end").strip() == placeholder:
            self._text.delete("1.0", "end")

    def _paste_clipboard(self):
        # Clear book mode if pasting free text
        try:
            text = self.clipboard_get()
            self._stop()
            self._text.delete("1.0", "end")
            self._text.insert("1.0", text)
        except tk.TclError:
            messagebox.showinfo("Nina", "Clipboard is empty.")

    def _clear_text(self):
        self._stop()
        self._book_chapters = []
        self._book_path     = None
        self._hide_book_bar()
        self._text.delete("1.0", "end")
        self._text.insert("1.0", "Paste or type text here, or click 📚 Open Book.")
        self._chunk_lbl.config(text="")


def main():
    app = NinaApp()
    app.mainloop()


if __name__ == "__main__":
    main()
