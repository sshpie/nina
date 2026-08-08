# nina

Read text aloud using open source neural TTS.

Nina uses open source speech synthesis technology to deliver high-quality, natural-sounding voices on Linux — through a CLI, a desktop app, or a browser extension.

- **CLI** — pipe any text to `nina` and it plays through your speakers
- **Desktop GUI** — paste text, pick a voice, press Play
- **Browser extension** — one click reads any webpage aloud with a floating toolbar

No API key. No account required.

---

## Install

```bash
pip install edge-tts
sudo apt install mpv

git clone https://github.com/zellkernel/nina
cd nina
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

| Shortcut | Voice | Style |
|----------|-------|-------|
| `aria` | en-US-AriaNeural (default) | News, clear |
| `guy` | en-US-GuyNeural | News, authoritative |
| `jenny` | en-US-JennyNeural | Conversation |
| `andrew` | en-US-AndrewNeural | Warm, confident |
| `ava` | en-US-AvaNeural | Expressive |
| `brian` | en-US-BrianNeural | Casual |
| `emma` | en-US-EmmaNeural | Conversational |
| `libby` | en-GB-LibbyNeural | British |
| `ryan` | en-GB-RyanNeural | British male |
| `sonia` | en-GB-SoniaNeural | British female |
| `natasha` | en-AU-NatashaNeural | Australian |
| `william` | en-AU-WilliamNeural | Australian male |
| `connor` | en-IE-ConnorNeural | Irish male |
| `emily` | en-IE-EmilyNeural | Irish female |

Full voice IDs also work: `nina -v en-US-BrianMultilingualNeural "..."` — run `nina --list` to see all voices.

---

## Desktop GUI

```bash
python3 nina_gui.py
```

Pick a voice from the dropdown (47 English voices, filterable by region or name), set speed, paste text, and press **▶ Play**. The Clipboard button pulls whatever is in your clipboard directly into the text area.

---

## Browser extension

Load `extension/` as an unpacked extension in Chrome, Brave, or any Chromium browser.

- **Keyboard shortcut:** `Ctrl+Shift+U` toggles the read-aloud bar on any page
- **Popup:** click the Nina icon in the toolbar to set default voice and speed, then click **▶ Read This Page**

The floating bar shows:
- ▶ / ⏸ Play/Pause
- « / » Back/Forward
- Voice picker
- Speed selector (0.75× – 2×)
- Chunk progress counter

---

## Bookmarklet

For browsers without extension support, copy `bookmarklet.txt` and save it as a bookmark URL. Click it on any page to inject the read-aloud toolbar.

**Install:** Copy the contents of `bookmarklet.txt`, create a new bookmark in your browser, paste it as the URL.

**Use:** Click the bookmark on any article page. Click it again to close the bar.

---

## How it works

Nina uses `edge-tts`, an open source Python library that streams neural speech synthesis audio. The library sends text to a publicly accessible TTS endpoint and returns an audio stream — no API key, no account, no browser required. The browser extension uses the Web Speech API built into Chromium browsers for in-page reading.

