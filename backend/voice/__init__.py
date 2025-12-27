"""Voice module - FREE local speech-to-text and text-to-speech.

Components:
- WhisperSTT: Local speech-to-text using faster-whisper (FREE)
- KokoroTTS: Local text-to-speech using Kokoro 82M (FREE)
- VoiceHandler: WebSocket integration for voice I/O
"""

from .stt import WhisperSTT, get_stt
from .tts import KokoroTTS, get_tts, get_available_voices, KOKORO_VOICES, DEFAULT_VOICE
from .handler import VoiceHandler, get_voice_handler

__all__ = [
    # STT
    "WhisperSTT",
    "get_stt",
    # TTS
    "KokoroTTS",
    "get_tts",
    "get_available_voices",
    "KOKORO_VOICES",
    "DEFAULT_VOICE",
    # Handler
    "VoiceHandler",
    "get_voice_handler",
]
