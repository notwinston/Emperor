"""Text-to-Speech using Edge TTS.

FREE - uses Microsoft Edge's online TTS service.
Good quality, requires internet.
"""

from typing import Optional, AsyncGenerator

import edge_tts

from config import get_logger

logger = get_logger(__name__)

# Popular voices:
# en-US-AriaNeural    - Female, American (recommended)
# en-US-GuyNeural     - Male, American
# en-US-JennyNeural   - Female, American
# en-GB-SoniaNeural   - Female, British
# en-AU-NatashaNeural - Female, Australian

DEFAULT_VOICE = "en-US-AriaNeural"


class EdgeTTS:
    """
    Free TTS using Microsoft Edge voices.

    No API key required, uses Microsoft's public TTS service.
    """

    def __init__(self, voice: str = DEFAULT_VOICE):
        """
        Initialize Edge TTS.

        Args:
            voice: Voice ID to use (e.g., "en-US-AriaNeural")
        """
        self.voice = voice
        logger.info(f"Edge TTS initialized with voice: {voice}")

    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to MP3 audio bytes.

        Args:
            text: Text to synthesize

        Returns:
            MP3 audio bytes
        """
        if not text.strip():
            return b""

        communicate = edge_tts.Communicate(text, self.voice)

        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])

        audio_data = b"".join(chunks)
        logger.debug(f"Synthesized {len(text)} chars -> {len(audio_data)} bytes")

        return audio_data

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Stream audio chunks for low-latency playback.

        Args:
            text: Text to synthesize

        Yields:
            MP3 audio chunks
        """
        if not text.strip():
            return

        communicate = edge_tts.Communicate(text, self.voice)

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    @staticmethod
    async def list_voices(language: str = "en") -> list[dict]:
        """
        List available voices for a language.

        Args:
            language: Language code prefix (e.g., "en", "es", "fr")

        Returns:
            List of voice info dicts
        """
        voices = await edge_tts.list_voices()
        return [v for v in voices if v["Locale"].startswith(language)]


# Singleton
_tts: Optional[EdgeTTS] = None


def get_tts(voice: str = DEFAULT_VOICE) -> EdgeTTS:
    """Get singleton TTS instance."""
    global _tts
    if _tts is None:
        _tts = EdgeTTS(voice=voice)
    return _tts


def reset_tts() -> None:
    """Reset the singleton."""
    global _tts
    _tts = None
