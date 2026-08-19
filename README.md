# nina

Read text aloud using open source neural TTS.

Nina delivers high-quality, natural-sounding voices on Linux through a CLI, a desktop GUI, and a browser extension. Load a book, paste text, or read any webpage — no API key, no account required.

- **CLI** — pipe any text to `nina` and it plays through your speakers
- **Desktop GUI** — paste text or load a book, pick a voice, press Play
- **Browser extension** — one click reads any webpage aloud with a floating toolbar

---

## Install

```bash
sudo apt install mpv

git clone https://github.com/sshpie/nina
cd nina
pip install -r requirements.txt
chmod +x nina.py
ln -s "$PWD/nina.py" ~/.local/bin/nina
```

---

## CLI usage

```bash
# Read text directly
nina "The quick brown fox jumps over the lazy dog"

# Pipe from stdin
cat article.txt | nina

# Different voice
nina -v guy "Hello from Guy"
nina -v libby "Hello from Libby"

# Adjust speed
nina -r "+25%" "Faster reading"
nina -r "-15%" "Slower and clearer"

# Save to MP3
nina -o output.mp3 "Save this as audio"

# List all voices
nina --list
```

### Voice shortcuts

| Shortcut | Locale | Style |
|----------|--------|-------|
| `aria` | en-US | News, clear |
| `guy` | en-US | News, authoritative |
| `jenny` | en-US | Conversation |
| `alex` | en-US | Warm, confident |
| `ava` | en-US | Expressive |
| `brian` | en-US | Casual |
| `emma` | en-US | Conversational |
| `libby` | en-GB | British female |
| `ryan` | en-GB | British male |
| `sonia` | en-GB | British female |
| `natasha` | en-AU | Australian female |
| `william` | en-AU | Australian male |
| `connor` | en-IE | Irish male |
| `helen` | en-IE | Irish female (default) |

Full voice IDs also work: `nina -v en-US-BrianMultilingualNeural "..."` — run `nina --list` to see all 47 English voices.

---

## Desktop GUI

```bash
python3 nina_gui.py
```

Pick a voice from the dropdown, set speed, then:

- **Paste text** and press **▶ Play**
- **Clipboard** button pulls whatever is in your clipboard directly into the text area
- **Open Book** loads a TXT, PDF, EPUB, or a directory of Markdown files

### Book reader

The GUI includes a full book reader with chapter navigation:

- Supports TXT, PDF, EPUB, and directory-based books (Markdown files)
- Chapter picker dropdown and ◀ ▶ buttons to navigate
- **Vertical bookmark bar** — stacked tab markers on the right edge of the text area; click any tab to jump to that chapter; current chapter highlighted in blue
- Auto-advances to the next chapter when TTS finishes
- Saves your reading position per book between sessions
- Stop button cuts audio immediately

Point **Open Book** at any of these formats or point it at a folder of numbered Markdown chapter files.

---

## Browser extension

Load `extension/` as an unpacked extension in Chrome, Brave, or any Chromium browser.

- **Keyboard shortcut:** `Ctrl+Shift+U` toggles the read-aloud bar on any page
- **Popup:** click the Nina icon in the toolbar to set default voice and speed, then click **▶ Read This Page**

The floating bar shows:
- ▶ / ⏸ Play/Pause
- « / » Back/Forward
- Voice picker (English voices from the browser's speech synthesis engine)
- Speed selector (0.75× – 2×)
- Chunk progress counter

### O'Reilly Learning support

The extension automatically detects O'Reilly Learning pages and waits for the JavaScript-rendered content to load before extracting text. If you see "NINA - Loading content..." for more than a few seconds, the page may not have loaded yet — wait for the chapter content to appear in the browser, then try activating Nina again.

---

## Bookmarklet

For browsers without extension support, copy `bookmarklet.txt` and save it as a bookmark URL. Click it on any page to inject the read-aloud toolbar.

**Install:** Copy the contents of `bookmarklet.txt`, create a new bookmark in your browser, paste it as the URL.

**Use:** Click the bookmark on any article page. Click it again to close the bar.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| see `requirements.txt` | Neural speech synthesis + book format support |
| `mpv` | Audio playback |
| `pypdf` | PDF text extraction |
| `ebooklib` | EPUB parsing |
| `beautifulsoup4` | HTML stripping inside EPUB files |

All dependencies (including book format support) are in `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## How it works

The CLI and GUI convert text to speech using a neural synthesis library and pipe the audio stream directly to `mpv` — no API key, no account, no browser required.

The browser extension and bookmarklet use the Web Speech API built into Chromium browsers for in-page reading.
