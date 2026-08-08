#!/usr/bin/env python3
"""nina — read text aloud using Microsoft Edge neural voices."""

import asyncio
import subprocess
import sys
import argparse
import edge_tts

VOICES = {
    "aria":      "en-US-AriaNeural",
    "guy":       "en-US-GuyNeural",
    "jenny":     "en-US-JennyNeural",
    "libby":     "en-GB-LibbyNeural",
    "ryan":      "en-GB-RyanNeural",
    "sonia":     "en-GB-SoniaNeural",
    "natasha":   "en-AU-NatashaNeural",
    "william":   "en-AU-WilliamNeural",
    "andrew":    "en-US-AndrewNeural",
    "ava":       "en-US-AvaNeural",
    "brian":     "en-US-BrianNeural",
    "emma":      "en-US-EmmaNeural",
}


async def stream_audio(text: str, voice_id: str, rate: str) -> None:
    """Stream TTS audio directly to mpv."""
    communicate = edge_tts.Communicate(text, voice_id, rate=rate)
    proc = subprocess.Popen(
        ["mpv", "--no-video", "--really-quiet", "--audio-display=no", "-"],
        stdin=subprocess.PIPE,
    )
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                proc.stdin.write(chunk["data"])
        proc.stdin.close()
        proc.wait()
    except (BrokenPipeError, KeyboardInterrupt):
        proc.terminate()


async def save_audio(text: str, voice_id: str, rate: str, path: str) -> None:
    communicate = edge_tts.Communicate(text, voice_id, rate=rate)
    await communicate.save(path)


async def resolve_voice(name: str) -> str:
    """Resolve a shortcut or prefix to a full voice ID."""
    if name in VOICES:
        return VOICES[name]
    if "Neural" in name:
        return name
    # Prefix match against full list
    all_voices = await edge_tts.list_voices()
    match = next(
        (v["ShortName"] for v in all_voices
         if v["ShortName"].lower().startswith(name.lower())),
        None,
    )
    if match:
        return match
    print(f"nina: unknown voice '{name}'. Run 'nina --list' to see options.", file=sys.stderr)
    sys.exit(1)


async def main() -> None:
    p = argparse.ArgumentParser(
        prog="nina",
        description="nina — Microsoft neural TTS for Linux via Edge voices",
    )
    p.add_argument("text", nargs="*", help="Text to read (omit to read from stdin)")
    p.add_argument(
        "-v", "--voice", default="aria", metavar="NAME",
        help=f"Voice shortcut or full ID. Shortcuts: {', '.join(VOICES)}. Default: aria",
    )
    p.add_argument(
        "-r", "--rate", default="+0%", metavar="RATE",
        help="Speed: +20%% faster, -10%% slower. Default: +0%%",
    )
    p.add_argument("-o", "--output", metavar="FILE", help="Save to MP3 instead of playing")
    p.add_argument("-l", "--list", action="store_true", help="List all available voices")
    args = p.parse_args()

    if args.list:
        voices = await edge_tts.list_voices()
        for v in sorted(voices, key=lambda x: x["Locale"]):
            print(f"{v['ShortName']:<48} {v['Gender']:<8} {v['Locale']}")
        return

    voice_id = await resolve_voice(args.voice)

    if args.text:
        text = " ".join(args.text)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        p.print_help()
        sys.exit(0)

    if not text.strip():
        print("nina: no text provided.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        await save_audio(text, voice_id, args.rate, args.output)
        print(f"nina: saved to {args.output}")
    else:
        await stream_audio(text, voice_id, args.rate)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
