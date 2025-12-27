"""Voice handler for WebSocket integration."""

import asyncio
import base64
from typing import Optional, AsyncGenerator

from config import get_logger
from .stt import get_stt, ModelSize
from .tts import get_tts, DEFAULT_VOICE

logger = get_logger(__name__)


class VoiceHandler:
    """
    Handles voice I/O for WebSocket connections.

    Flow:
    1. Receive audio from frontend (base64)
    2. Transcribe with local Whisper (FREE)
    3. Return text to orchestrator
    4. Synthesize response with Edge TTS (FREE)
    5. Stream audio back to frontend
    """

    def __init__(
        self,
        whisper_model: ModelSize = "medium",
        tts_voice: str = DEFAULT_VOICE,
    ):
        """
        Initialize voice handler.

        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large-v3)
            tts_voice: Edge TTS voice ID
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
        """Lazy-load TTS."""
        if self._tts is None:
            self._tts = get_tts(self.tts_voice)
        return self._tts

    async def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe audio to text using local Whisper.

        Runs in thread pool since Whisper is CPU-bound.

        Args:
            audio_data: Raw audio bytes

        Returns:
            Transcribed text
        """
        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None,
                self.stt.transcribe,
                audio_data,
            )
            logger.info(f"Transcribed: {text[:100]}...")
            return text

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise

    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to audio using Edge TTS.

        Args:
            text: Text to synthesize

        Returns:
            MP3 audio bytes
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
            MP3 audio chunks
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


# Singleton
_handler: Optional[VoiceHandler] = None


def get_voice_handler(
    whisper_model: ModelSize = "medium",
    tts_voice: str = DEFAULT_VOICE,
) -> VoiceHandler:
    """
    Get singleton voice handler.

    Args:
        whisper_model: Whisper model size
        tts_voice: Edge TTS voice ID

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
