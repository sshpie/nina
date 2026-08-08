"""Neural TTS engine — thin wrapper so callers stay backend-agnostic."""
import edge_tts as _engine

Communicate  = _engine.Communicate
list_voices  = _engine.list_voices
