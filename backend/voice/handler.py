"""Voice handler for WebSocket integration."""

import asyncio
import base64
from typing import Optional, AsyncGenerator

from config import get_logger
from .stt import get_stt, ModelSize
from .tts import get_tts, DEFAULT_VOICE, KOKORO_VOICES, get_available_voices

logger = get_logger(__name__)


class VoiceHandler:
    """
    Handles voice I/O for WebSocket connections.

    Flow:
    1. Receive audio from frontend (base64)
    2. Transcribe with local Whisper (FREE)
    3. Return text to orchestrator
    4. Synthesize response with Kokoro TTS (FREE, local)
    5. Stream audio back to frontend
    """

    def __init__(
        self,
        whisper_model: ModelSize = "base",
        tts_voice: str = DEFAULT_VOICE,
    ):
        """
        Initialize voice handler.

        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large-v3)
            tts_voice: Kokoro voice ID (e.g., af_heart, am_adam)
        """
        self.whisper_model = whisper_model
        self.tts_voice = tts_voice
        self._stt = None
        self._tts = None

    @property
    def stt(self):
        """Lazy-load STT (downloads model on first use)."""
        if self._stt is None:
            logger.info("Loading Whisper model (first use)...")
            self._stt = get_stt(self.whisper_model)
        return self._stt

    @property
    def tts(self):
        """Lazy-load TTS (downloads Kokoro model on first use)."""
        if self._tts is None:
            logger.info("Loading Kokoro TTS model (first use)...")
            self._tts = get_tts(self.tts_voice)
        return self._tts

    def set_tts_voice(self, voice: str) -> bool:
        """
        Change the TTS voice.

        Args:
            voice: Kokoro voice ID (e.g., af_heart, am_adam)

        Returns:
            True if voice was changed successfully
        """
        if voice not in KOKORO_VOICES:
            logger.warning(f"Unknown voice '{voice}'")
            return False

        self.tts_voice = voice
        if self._tts:
            self._tts.set_voice(voice)
        logger.info(f"TTS voice changed to '{voice}'")
        return True

    async def transcribe(self, audio_data: bytes, input_format: str = "webm") -> str:
        """
        Transcribe audio to text using local Whisper.

        Runs in thread pool since Whisper is CPU-bound.

        Args:
            audio_data: Raw audio bytes
            input_format: Audio format (webm, wav, mp3)

        Returns:
            Transcribed text
        """
        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None,
                lambda: self.stt.transcribe(audio_data, input_format=input_format),
            )
            logger.info(f"Transcribed: {text[:100]}...")
            return text

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise

    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to audio using Kokoro TTS.

        Args:
            text: Text to synthesize

        Returns:
            WAV audio bytes (24kHz)
        """
        try:
            audio = await self.tts.synthesize(text)
            logger.info(f"Synthesized {len(text)} chars -> {len(audio)} bytes")
            return audio

        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesized audio chunks.

        Args:
            text: Text to synthesize

        Yields:
            WAV audio chunks
        """
        try:
            async for chunk in self.tts.synthesize_stream(text):
                yield chunk

        except Exception as e:
            logger.error(f"TTS stream error: {e}")
            raise

    @staticmethod
    def encode_audio(audio_data: bytes) -> str:
        """Encode audio bytes to base64 for WebSocket."""
        return base64.b64encode(audio_data).decode("utf-8")

    @staticmethod
    def decode_audio(audio_b64: str) -> bytes:
        """Decode base64 audio from WebSocket."""
        return base64.b64decode(audio_b64)

    @staticmethod
    def get_available_voices() -> dict:
        """Get all available Kokoro TTS voices."""
        return get_available_voices()


# Singleton
_handler: Optional[VoiceHandler] = None


def get_voice_handler(
    whisper_model: ModelSize = "base",
    tts_voice: str = DEFAULT_VOICE,
) -> VoiceHandler:
    """
    Get singleton voice handler.

    Args:
        whisper_model: Whisper model size
        tts_voice: Kokoro voice ID

    Returns:
        VoiceHandler instance
    """
    global _handler
    if _handler is None:
        _handler = VoiceHandler(
            whisper_model=whisper_model,
            tts_voice=tts_voice,
        )
    return _handler


def reset_voice_handler() -> None:
    """Reset the singleton."""
    global _handler
    _handler = None
