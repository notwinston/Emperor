"""Local Text-to-Speech using Kokoro-82M.

FREE - runs entirely on your machine.
No API calls, no costs, works offline.
"""

import io
import asyncio
from typing import Optional, Literal, AsyncGenerator

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from config import get_logger

logger = get_logger(__name__)

# Language codes for Kokoro
LanguageCode = Literal["a", "b", "e", "f", "h", "i", "j", "p", "z"]

# Voice naming convention: {lang}{gender}_{name}
# First char: language (a=American, b=British, j=Japanese, etc.)
# Second char: gender (f=female, m=male)

KOKORO_VOICES = {
    # American English - Female
    "af_heart": {"name": "Heart", "gender": "female", "lang": "American English"},
    "af_alloy": {"name": "Alloy", "gender": "female", "lang": "American English"},
    "af_aoede": {"name": "Aoede", "gender": "female", "lang": "American English"},
    "af_bella": {"name": "Bella", "gender": "female", "lang": "American English"},
    "af_jessica": {"name": "Jessica", "gender": "female", "lang": "American English"},
    "af_kore": {"name": "Kore", "gender": "female", "lang": "American English"},
    "af_nicole": {"name": "Nicole", "gender": "female", "lang": "American English"},
    "af_nova": {"name": "Nova", "gender": "female", "lang": "American English"},
    "af_river": {"name": "River", "gender": "female", "lang": "American English"},
    "af_sarah": {"name": "Sarah", "gender": "female", "lang": "American English"},
    "af_sky": {"name": "Sky", "gender": "female", "lang": "American English"},
    # American English - Male
    "am_adam": {"name": "Adam", "gender": "male", "lang": "American English"},
    "am_echo": {"name": "Echo", "gender": "male", "lang": "American English"},
    "am_eric": {"name": "Eric", "gender": "male", "lang": "American English"},
    "am_fenrir": {"name": "Fenrir", "gender": "male", "lang": "American English"},
    "am_liam": {"name": "Liam", "gender": "male", "lang": "American English"},
    "am_michael": {"name": "Michael", "gender": "male", "lang": "American English"},
    "am_onyx": {"name": "Onyx", "gender": "male", "lang": "American English"},
    "am_puck": {"name": "Puck", "gender": "male", "lang": "American English"},
    "am_santa": {"name": "Santa", "gender": "male", "lang": "American English"},
    # British English - Female
    "bf_alice": {"name": "Alice", "gender": "female", "lang": "British English"},
    "bf_emma": {"name": "Emma", "gender": "female", "lang": "British English"},
    "bf_isabella": {"name": "Isabella", "gender": "female", "lang": "British English"},
    "bf_lily": {"name": "Lily", "gender": "female", "lang": "British English"},
    # British English - Male
    "bm_daniel": {"name": "Daniel", "gender": "male", "lang": "British English"},
    "bm_fable": {"name": "Fable", "gender": "male", "lang": "British English"},
    "bm_george": {"name": "George", "gender": "male", "lang": "British English"},
    "bm_lewis": {"name": "Lewis", "gender": "male", "lang": "British English"},
    # Japanese
    "jf_alpha": {"name": "Alpha", "gender": "female", "lang": "Japanese"},
    "jf_gongitsune": {"name": "Gongitsune", "gender": "female", "lang": "Japanese"},
    "jf_nezumi": {"name": "Nezumi", "gender": "female", "lang": "Japanese"},
    "jf_tebukuro": {"name": "Tebukuro", "gender": "female", "lang": "Japanese"},
    "jm_kumo": {"name": "Kumo", "gender": "male", "lang": "Japanese"},
    # Mandarin Chinese
    "zf_xiaobei": {"name": "Xiaobei", "gender": "female", "lang": "Mandarin Chinese"},
    "zf_xiaoni": {"name": "Xiaoni", "gender": "female", "lang": "Mandarin Chinese"},
    "zf_xiaoxiao": {"name": "Xiaoxiao", "gender": "female", "lang": "Mandarin Chinese"},
    "zf_xiaoyi": {"name": "Xiaoyi", "gender": "female", "lang": "Mandarin Chinese"},
    "zm_yunjian": {"name": "Yunjian", "gender": "male", "lang": "Mandarin Chinese"},
    "zm_yunxi": {"name": "Yunxi", "gender": "male", "lang": "Mandarin Chinese"},
    "zm_yunxia": {"name": "Yunxia", "gender": "male", "lang": "Mandarin Chinese"},
    "zm_yunyang": {"name": "Yunyang", "gender": "male", "lang": "Mandarin Chinese"},
    # Spanish
    "ef_dora": {"name": "Dora", "gender": "female", "lang": "Spanish"},
    "em_alex": {"name": "Alex", "gender": "male", "lang": "Spanish"},
    "em_santa": {"name": "Santa", "gender": "male", "lang": "Spanish"},
    # French
    "ff_siwis": {"name": "Siwis", "gender": "female", "lang": "French"},
    # Hindi
    "hf_alpha": {"name": "Alpha", "gender": "female", "lang": "Hindi"},
    "hf_beta": {"name": "Beta", "gender": "female", "lang": "Hindi"},
    "hm_omega": {"name": "Omega", "gender": "male", "lang": "Hindi"},
    "hm_psi": {"name": "Psi", "gender": "male", "lang": "Hindi"},
    # Italian
    "if_sara": {"name": "Sara", "gender": "female", "lang": "Italian"},
    "im_nicola": {"name": "Nicola", "gender": "male", "lang": "Italian"},
    # Brazilian Portuguese
    "pf_dora": {"name": "Dora", "gender": "female", "lang": "Brazilian Portuguese"},
    "pm_alex": {"name": "Alex", "gender": "male", "lang": "Brazilian Portuguese"},
    "pm_santa": {"name": "Santa", "gender": "male", "lang": "Brazilian Portuguese"},
}

DEFAULT_VOICE = "af_heart"
DEFAULT_LANG = "a"


class KokoroTTS:
    """
    Local Kokoro text-to-speech.

    First run downloads the model from Hugging Face (~80MB).
    """

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        lang_code: LanguageCode = DEFAULT_LANG,
    ):
        """
        Initialize Kokoro TTS.

        Args:
            voice: Voice ID (e.g., af_heart, am_adam)
            lang_code: Language code ('a' for American, 'b' for British, etc.)
        """
        self.voice = voice
        self.lang_code = lang_code
        self._pipeline: Optional[KPipeline] = None

        logger.info(f"Kokoro TTS initialized with voice '{voice}'")

    @property
    def pipeline(self) -> KPipeline:
        """Lazy-load the pipeline (downloads model on first use)."""
        if self._pipeline is None:
            logger.info(f"Loading Kokoro pipeline (lang={self.lang_code})...")
            self._pipeline = KPipeline(lang_code=self.lang_code)
            logger.info("Kokoro pipeline loaded successfully")
        return self._pipeline

    def set_voice(self, voice: str) -> bool:
        """
        Change the current voice.

        Args:
            voice: New voice ID

        Returns:
            True if voice was changed successfully
        """
        if voice not in KOKORO_VOICES:
            logger.warning(f"Unknown voice '{voice}', keeping current")
            return False

        old_lang = self.lang_code
        self.voice = voice
        # Update language code based on voice prefix (first char)
        self.lang_code = voice[0]

        # Reset pipeline if language changed
        if self.lang_code != old_lang:
            self._pipeline = None
            logger.info(f"Language changed to '{self.lang_code}', pipeline will reload")

        logger.info(f"Voice changed to '{voice}'")
        return True

    def synthesize_sync(self, text: str) -> bytes:
        """
        Synchronously synthesize text to audio.

        Args:
            text: Text to synthesize

        Returns:
            WAV audio bytes (24kHz, mono)
        """
        if not text.strip():
            return b""

        try:
            # Generate audio segments
            generator = self.pipeline(text, voice=self.voice)

            # Collect all audio segments
            audio_segments = []
            for gs, ps, audio in generator:
                audio_segments.append(audio)

            if not audio_segments:
                return b""

            # Concatenate segments
            full_audio = np.concatenate(audio_segments)

            # Convert to WAV bytes
            buffer = io.BytesIO()
            sf.write(buffer, full_audio, 24000, format="WAV")
            buffer.seek(0)

            wav_bytes = buffer.getvalue()
            logger.debug(f"Synthesized {len(text)} chars -> {len(wav_bytes)} bytes")
            return wav_bytes

        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise

    async def synthesize(self, text: str) -> bytes:
        """
        Asynchronously synthesize text to audio.

        Runs synthesis in thread pool since Kokoro is CPU-bound.

        Args:
            text: Text to synthesize

        Returns:
            WAV audio bytes (24kHz, mono)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.synthesize_sync, text)

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesized audio chunks as they're generated.

        Uses a queue to yield audio chunks as soon as they're ready,
        reducing latency for the first audio chunk.

        Args:
            text: Text to synthesize

        Yields:
            WAV audio chunks
        """
        if not text.strip():
            return

        import queue
        import threading

        audio_queue: queue.Queue = queue.Queue()
        error_holder: list = []

        def generate_in_thread():
            """Generate audio segments and put them in queue."""
            try:
                for gs, ps, audio in self.pipeline(text, voice=self.voice):
                    # Convert to WAV bytes immediately
                    buffer = io.BytesIO()
                    sf.write(buffer, audio, 24000, format="WAV")
                    buffer.seek(0)
                    audio_queue.put(buffer.getvalue())
            except Exception as e:
                error_holder.append(e)
            finally:
                audio_queue.put(None)  # Signal completion

        # Start generation in background thread
        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()

        # Yield chunks as they become available
        while True:
            try:
                # Non-blocking check with small sleep to not block event loop
                chunk = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: audio_queue.get(timeout=0.1)
                )

                if chunk is None:  # Generation complete
                    break

                yield chunk

            except queue.Empty:
                # Check if thread is still running
                if not thread.is_alive() and audio_queue.empty():
                    break
                await asyncio.sleep(0.01)

        # Check for errors
        if error_holder:
            logger.error(f"TTS stream error: {error_holder[0]}")
            raise error_holder[0]


# Singleton instance
_tts: Optional[KokoroTTS] = None


def get_tts(voice: str = DEFAULT_VOICE) -> KokoroTTS:
    """
    Get singleton TTS instance.

    First call downloads model (~80MB).
    """
    global _tts
    if _tts is None:
        _tts = KokoroTTS(voice=voice)
    return _tts


def reset_tts() -> None:
    """Reset the singleton to free memory."""
    global _tts
    _tts = None


def get_available_voices() -> dict:
    """Get all available Kokoro voices."""
    return KOKORO_VOICES
