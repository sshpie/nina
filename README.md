# nina

Read text aloud using Microsoft Edge's neural voices — on Linux.

Microsoft's natural TTS voices (Aria, Guy, Libby, Ryan, etc.) are wired into Edge's Web Speech API on Linux but the Read Aloud UI button isn't exposed. Nina gives you two ways to use them:

- **CLI** — pipe any text to `nina` and it plays through your speakers
- **Bookmarklet** — click once on any webpage and a Read Aloud bar appears

No API key. No Azure account. Same voices as Edge Read Aloud on Windows.

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

Full voice IDs also work: `nina -v en-US-BrianMultilingualNeural "..."` — run `nina --list` to see all ~400 voices.

---

## Bookmarklet

For browser use (Edge, Chrome, Firefox), the bookmarklet injects a Read Aloud toolbar into any webpage using the same Microsoft neural voices via the Web Speech API.

**Install:** Copy the contents of `bookmarklet.txt`, create a new bookmark in your browser, paste it as the URL.

**Use:** Click the bookmark on any article page. The bar appears at the top with:
- ▶ / ⏸ Play/Pause
- « / » Back/Forward
- Voice picker (all Microsoft neural voices)
- Speed selector (0.75× – 2×)
- Chunk progress counter

Click the bookmark again to close it.

---

## How it works

Edge on Linux exposes Microsoft's neural voices through the Web Speech API (`speechSynthesis.getVoices()`). These are the same cloud-hosted voices as Edge Read Aloud on Windows — streamed from Microsoft's servers. Nina accesses the same voice API directly via `edge-tts`, bypassing the browser entirely for CLI use.

Requires an internet connection. Voices are not cached locally.

---

## Dependencies

- [`edge-tts`](https://github.com/rany2/edge-tts) — Microsoft TTS API client
- `mpv` — audio playback for CLI streaming
