"""Voice module - FREE local speech-to-text and text-to-speech.

Components:
- WhisperSTT: Local speech-to-text using faster-whisper (FREE)
- EdgeTTS: Text-to-speech using Microsoft Edge (FREE)
- VoiceHandler: WebSocket integration for voice I/O
"""

from .stt import WhisperSTT, get_stt
from .tts import EdgeTTS, get_tts
from .handler import VoiceHandler, get_voice_handler

__all__ = [
    # STT
    "WhisperSTT",
    "get_stt",
    # TTS
    "EdgeTTS",
    "get_tts",
    # Handler
    "VoiceHandler",
    "get_voice_handler",
]
