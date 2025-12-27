# Kokoro 82M TTS Implementation Guide

## Overview

[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) is a lightweight, open-weight text-to-speech model that runs entirely locally. With only 82 million parameters (~80MB), it delivers quality comparable to larger models while being fast and completely free.

**Key Benefits:**
- **FREE** - No API costs, runs locally
- **Fast** - Small model size enables quick inference
- **Offline** - Works without internet after initial setup
- **Apache 2.0** - Unrestricted commercial use

---

## Part 1: Installation

### 1.1 System Dependencies

**macOS:**
```bash
brew install espeak-ng
```

**Linux/Ubuntu:**
```bash
apt-get install -y espeak-ng
```

**Windows:**
Download the espeak-ng `.msi` installer from [espeak-ng releases](https://github.com/espeak-ng/espeak-ng/releases).

### 1.2 Python Dependencies

Add to `backend/requirements.txt`:

```txt
kokoro>=0.9.4
soundfile
```

Install:
```bash
pip install kokoro>=0.9.4 soundfile
```

### 1.3 Optional: Language-Specific Dependencies

For Japanese:
```bash
pip install misaki[ja]
```

For Mandarin Chinese:
```bash
pip install misaki[zh]
```

---

## Part 2: Backend Implementation

### 2.1 Create Kokoro TTS Module (`backend/voice/tts.py`)

Replace the existing Edge TTS implementation with Kokoro:

```python
"""Local Text-to-Speech using Kokoro-82M.

FREE - runs entirely on your machine.
No API calls, no costs, works offline.
"""

import io
import asyncio
from typing import Optional, Literal, AsyncGenerator
import soundfile as sf

from kokoro import KPipeline

from config import get_logger

logger = get_logger(__name__)

# Language codes for Kokoro
LanguageCode = Literal["a", "b", "e", "f", "h", "i", "j", "p", "z"]

# Voice naming convention: {lang}{gender}_{name}
# Examples: af_heart (American Female), am_adam (American Male)

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

    def set_voice(self, voice: str) -> None:
        """Change the current voice."""
        if voice in KOKORO_VOICES:
            self.voice = voice
            # Update language code based on voice prefix
            self.lang_code = voice[0]  # First char is lang code
            # Reset pipeline to use new language
            self._pipeline = None
            logger.info(f"Voice changed to '{voice}'")
        else:
            logger.warning(f"Unknown voice '{voice}', keeping current")

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
            import numpy as np
            full_audio = np.concatenate(audio_segments)

            # Convert to WAV bytes
            buffer = io.BytesIO()
            sf.write(buffer, full_audio, 24000, format="WAV")
            buffer.seek(0)

            logger.debug(f"Synthesized {len(text)} chars -> {len(buffer.getvalue())} bytes")
            return buffer.getvalue()

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
        Stream synthesized audio chunks.

        Args:
            text: Text to synthesize

        Yields:
            WAV audio chunks
        """
        if not text.strip():
            return

        try:
            loop = asyncio.get_event_loop()

            # Run generation in thread pool
            def generate():
                return list(self.pipeline(text, voice=self.voice))

            segments = await loop.run_in_executor(None, generate)

            for gs, ps, audio in segments:
                # Convert each segment to WAV
                buffer = io.BytesIO()
                sf.write(buffer, audio, 24000, format="WAV")
                buffer.seek(0)
                yield buffer.getvalue()

        except Exception as e:
            logger.error(f"TTS stream error: {e}")
            raise


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
```

### 2.2 Update Voice Handler (`backend/voice/handler.py`)

```python
"""Voice handler for WebSocket integration."""

import asyncio
import base64
from typing import Optional, AsyncGenerator

from config import get_logger
from .stt import get_stt, ModelSize
from .tts import get_tts, DEFAULT_VOICE, KOKORO_VOICES

logger = get_logger(__name__)


class VoiceHandler:
    """
    Handles voice I/O for WebSocket connections.

    Flow:
    1. Receive audio from frontend (base64)
    2. Transcribe with local Whisper (FREE)
    3. Return text to orchestrator
    4. Synthesize response with Kokoro (FREE)
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
        """Lazy-load TTS (downloads model on first use)."""
        if self._tts is None:
            logger.info("Loading Kokoro TTS model (first use)...")
            self._tts = get_tts(self.tts_voice)
        return self._tts

    def set_tts_voice(self, voice: str) -> bool:
        """
        Change the TTS voice.

        Args:
            voice: Kokoro voice ID

        Returns:
            True if voice was changed successfully
        """
        if voice in KOKORO_VOICES:
            self.tts_voice = voice
            if self._tts:
                self._tts.set_voice(voice)
            return True
        return False

    async def transcribe(self, audio_data: bytes, input_format: str = "webm") -> str:
        """
        Transcribe audio to text using local Whisper.

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
        """Get all available TTS voices."""
        return KOKORO_VOICES


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
```

---

## Part 3: Frontend Integration

### 3.1 Update Audio Player Hook

Since Kokoro outputs WAV (not MP3), update `src/hooks/useAudioPlayer.ts` to handle WAV:

```typescript
// WAV is natively supported by browsers, no changes needed
// The AudioContext can decode WAV directly
```

### 3.2 Voice Settings Store Update

See the updated `settingsStore.ts` in SETTINGS_IMPLEMENTATION.md for Kokoro voice options.

---

## Part 4: API Endpoints

### 4.1 Add Voice List Endpoint

```python
# backend/api/main.py

from voice import get_voice_handler
from voice.tts import get_available_voices

@app.get("/api/voices")
async def list_voices():
    """Get available TTS voices."""
    voices = get_available_voices()
    return {
        "voices": [
            {
                "id": voice_id,
                "name": info["name"],
                "gender": info["gender"],
                "language": info["lang"],
            }
            for voice_id, info in voices.items()
        ]
    }

@app.post("/api/voice/set")
async def set_voice(voice_id: str):
    """Set the TTS voice."""
    handler = get_voice_handler()
    if handler.set_tts_voice(voice_id):
        return {"status": "ok", "voice": voice_id}
    return {"status": "error", "message": f"Unknown voice: {voice_id}"}
```

---

## Part 5: Preloading (Optional)

### 5.1 Preload Kokoro at Startup

Add to `backend/api/main.py` lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload models at startup."""
    logger.info("Preloading Whisper STT model (base)...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: get_stt("base"))

    logger.info("Preloading Kokoro TTS model...")
    await loop.run_in_executor(None, lambda: get_tts())

    logger.info("All models loaded, server ready")
    yield
```

---

## Available Voices Reference

### American English (lang_code: 'a')

| Voice ID | Name | Gender |
|----------|------|--------|
| af_heart | Heart | Female |
| af_alloy | Alloy | Female |
| af_aoede | Aoede | Female |
| af_bella | Bella | Female |
| af_jessica | Jessica | Female |
| af_kore | Kore | Female |
| af_nicole | Nicole | Female |
| af_nova | Nova | Female |
| af_river | River | Female |
| af_sarah | Sarah | Female |
| af_sky | Sky | Female |
| am_adam | Adam | Male |
| am_echo | Echo | Male |
| am_eric | Eric | Male |
| am_fenrir | Fenrir | Male |
| am_liam | Liam | Male |
| am_michael | Michael | Male |
| am_onyx | Onyx | Male |
| am_puck | Puck | Male |
| am_santa | Santa | Male |

### British English (lang_code: 'b')

| Voice ID | Name | Gender |
|----------|------|--------|
| bf_alice | Alice | Female |
| bf_emma | Emma | Female |
| bf_isabella | Isabella | Female |
| bf_lily | Lily | Female |
| bm_daniel | Daniel | Male |
| bm_fable | Fable | Male |
| bm_george | George | Male |
| bm_lewis | Lewis | Male |

### Other Languages

| Voice ID | Name | Gender | Language |
|----------|------|--------|----------|
| jf_alpha | Alpha | Female | Japanese |
| jf_gongitsune | Gongitsune | Female | Japanese |
| jf_nezumi | Nezumi | Female | Japanese |
| jf_tebukuro | Tebukuro | Female | Japanese |
| jm_kumo | Kumo | Male | Japanese |
| zf_xiaobei | Xiaobei | Female | Mandarin |
| zf_xiaoni | Xiaoni | Female | Mandarin |
| zf_xiaoxiao | Xiaoxiao | Female | Mandarin |
| zf_xiaoyi | Xiaoyi | Female | Mandarin |
| zm_yunjian | Yunjian | Male | Mandarin |
| zm_yunxi | Yunxi | Male | Mandarin |
| zm_yunxia | Yunxia | Male | Mandarin |
| zm_yunyang | Yunyang | Male | Mandarin |
| ef_dora | Dora | Female | Spanish |
| em_alex | Alex | Male | Spanish |
| em_santa | Santa | Male | Spanish |
| ff_siwis | Siwis | Female | French |
| hf_alpha | Alpha | Female | Hindi |
| hf_beta | Beta | Female | Hindi |
| hm_omega | Omega | Male | Hindi |
| hm_psi | Psi | Male | Hindi |
| if_sara | Sara | Female | Italian |
| im_nicola | Nicola | Male | Italian |
| pf_dora | Dora | Female | Portuguese |
| pm_alex | Alex | Male | Portuguese |
| pm_santa | Santa | Male | Portuguese |

---

## Troubleshooting

### espeak-ng not found
```
Error: espeak-ng not found
```
Solution: Install espeak-ng for your platform (see Installation section).

### Apple Silicon GPU Acceleration
```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 python your-script.py
```

### Model Download Issues
First run downloads from Hugging Face. If blocked, set:
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

---

## Resources

- [Kokoro GitHub](https://github.com/hexgrad/kokoro)
- [Kokoro-82M on Hugging Face](https://huggingface.co/hexgrad/Kokoro-82M)
- [Demo Space](https://huggingface.co/spaces/hexgrad/Kokoro-TTS)
