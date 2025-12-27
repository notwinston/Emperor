"""Local Speech-to-Text using faster-whisper.

FREE - runs entirely on your machine.
No API calls, no costs, works offline.
"""

import tempfile
from typing import Optional, Literal

from faster_whisper import WhisperModel

from config import get_logger

logger = get_logger(__name__)

ModelSize = Literal["tiny", "base", "small", "medium", "large-v3"]

# Model specs:
# tiny   - 75MB,  fastest, good for simple speech
# base   - 142MB, very fast, good accuracy
# small  - 466MB, fast, very good accuracy (recommended)
# medium - 1.5GB, moderate, excellent accuracy
# large  - 3GB,   slow, best accuracy


class WhisperSTT:
    """
    Local Whisper speech-to-text.

    First run downloads the model to ~/.cache/huggingface/
    """

    def __init__(
        self,
        model_size: ModelSize = "small",
        device: str = "auto",
        compute_type: str = "auto",
    ):
        """
        Initialize local Whisper model.

        Args:
            model_size: Model to use (tiny, base, small, medium, large-v3)
            device: "cuda", "cpu", or "auto"
            compute_type: "float16", "int8", or "auto"
        """
        self.model_size = model_size

        # Auto-detect device
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        # Auto-select compute type for performance
        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"

        logger.info(f"Loading Whisper '{model_size}' on {device}...")

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

        self.device = device
        self.compute_type = compute_type

        logger.info("Whisper model loaded successfully")

    def transcribe(self, audio_data: bytes, language: Optional[str] = None) -> str:
        """
        Transcribe audio bytes to text.

        Args:
            audio_data: Audio bytes (WAV, WebM, MP3, etc.)
            language: Optional language code (auto-detects if None)

        Returns:
            Transcribed text
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
            f.write(audio_data)
            f.flush()
            return self.transcribe_file(f.name, language)

    def transcribe_file(self, file_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe an audio file.

        Args:
            file_path: Path to audio file
            language: Optional language code

        Returns:
            Transcribed text
        """
        segments, info = self.model.transcribe(
            file_path,
            language=language,
            beam_size=5,
            vad_filter=True,  # Filter silence
            vad_parameters={"min_silence_duration_ms": 500},
        )

        text = " ".join(seg.text.strip() for seg in segments)

        logger.debug(
            f"Transcribed ({info.language}, {info.duration:.1f}s): {text[:50]}..."
        )

        return text.strip()


# Singleton
_stt: Optional[WhisperSTT] = None


def get_stt(model_size: ModelSize = "small") -> WhisperSTT:
    """
    Get singleton STT instance.

    First call downloads model (~466MB for 'small').
    """
    global _stt
    if _stt is None:
        _stt = WhisperSTT(model_size=model_size)
    return _stt


def reset_stt() -> None:
    """Reset the singleton to free memory."""
    global _stt
    _stt = None
