# Voice System Implementation Guide

Complete guide to implementing **free, local** speech-to-text using faster-whisper and text-to-speech for Emperor.

**Total Cost: $0/month** (fully local)

---

## Architecture

```
Frontend                              Backend
┌─────────────────┐                  ┌─────────────────┐
│  Microphone     │──── WebSocket ──▶│  faster-whisper │
│  (Push-to-Talk) │     audio b64    │  (LOCAL STT)    │
└─────────────────┘                  └────────┬────────┘
                                              │ text
┌─────────────────┐                  ┌────────▼────────┐
│  Audio Player   │◀─── WebSocket ───│   Edge TTS      │
│                 │     audio b64    │   (FREE TTS)    │
└─────────────────┘                  └─────────────────┘
```

---

## Part 1: Backend Setup

### 1.1 Directory Structure

```
backend/voice/
├── __init__.py
├── stt.py           # faster-whisper transcription
├── tts.py           # Edge TTS synthesis
└── handler.py       # WebSocket integration
```

### 1.2 Install Dependencies

Add to `backend/requirements.txt`:

```txt
# Voice - STT (FREE, local)
faster-whisper>=1.0.0

# Voice - TTS (FREE, uses Microsoft Edge)
edge-tts>=6.1.0

# Audio processing
pydub>=0.25.0
soundfile>=0.12.0
numpy>=1.24.0
```

Install system dependency:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows - download from https://ffmpeg.org/download.html
```

### 1.3 Speech-to-Text (`stt.py`)

```python
"""Local Speech-to-Text using faster-whisper.

FREE - runs entirely on your machine.
No API calls, no costs, works offline.
"""

import tempfile
from typing import Optional, Literal
from pathlib import Path

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

        logger.info("Whisper model loaded")

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
        """Transcribe an audio file."""
        segments, info = self.model.transcribe(
            file_path,
            language=language,
            beam_size=5,
            vad_filter=True,  # Filter silence
            vad_parameters={"min_silence_duration_ms": 500},
        )

        text = " ".join(seg.text.strip() for seg in segments)

        logger.debug(f"Transcribed ({info.language}, {info.duration:.1f}s): {text[:50]}...")

        return text.strip()


# Singleton
_stt: Optional[WhisperSTT] = None


def get_stt(model_size: ModelSize = "small") -> WhisperSTT:
    """Get singleton STT instance. First call downloads model."""
    global _stt
    if _stt is None:
        _stt = WhisperSTT(model_size=model_size)
    return _stt
```

### 1.4 Text-to-Speech (`tts.py`)

```python
"""Text-to-Speech using Edge TTS.

FREE - uses Microsoft Edge's online TTS service.
Good quality, requires internet.
"""

import asyncio
from typing import AsyncGenerator

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
    """Free TTS using Microsoft Edge voices."""

    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice

    async def synthesize(self, text: str) -> bytes:
        """Convert text to MP3 audio bytes."""
        communicate = edge_tts.Communicate(text, self.voice)

        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])

        return b"".join(chunks)

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Stream audio chunks for low-latency playback."""
        communicate = edge_tts.Communicate(text, self.voice)

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]


# Singleton
_tts: Optional[EdgeTTS] = None


def get_tts(voice: str = DEFAULT_VOICE) -> EdgeTTS:
    """Get singleton TTS instance."""
    global _tts
    if _tts is None:
        _tts = EdgeTTS(voice=voice)
    return _tts
```

### 1.5 Voice Handler (`handler.py`)

```python
"""Voice handler for WebSocket integration."""

import asyncio
import base64
from typing import Optional, Callable, AsyncGenerator

from config import get_logger
from .stt import get_stt
from .tts import get_tts

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

    def __init__(self, whisper_model: str = "small", tts_voice: str = "en-US-AriaNeural"):
        self.whisper_model = whisper_model
        self.tts_voice = tts_voice
        self._stt = None
        self._tts = None

    @property
    def stt(self):
        """Lazy-load STT (downloads model on first use)."""
        if self._stt is None:
            logger.info("Loading Whisper model...")
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
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.stt.transcribe, audio_data)

    async def synthesize(self, text: str) -> bytes:
        """Convert text to audio using Edge TTS."""
        return await self.tts.synthesize(text)

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Stream synthesized audio chunks."""
        async for chunk in self.tts.synthesize_stream(text):
            yield chunk

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


def get_voice_handler() -> VoiceHandler:
    """Get singleton voice handler."""
    global _handler
    if _handler is None:
        _handler = VoiceHandler()
    return _handler
```

### 1.6 Module Init (`__init__.py`)

```python
"""Voice module - FREE local speech-to-text and text-to-speech."""

from .stt import WhisperSTT, get_stt
from .tts import EdgeTTS, get_tts
from .handler import VoiceHandler, get_voice_handler

__all__ = [
    "WhisperSTT",
    "get_stt",
    "EdgeTTS",
    "get_tts",
    "VoiceHandler",
    "get_voice_handler",
]
```

---

## Part 2: WebSocket Integration

Add voice message handling to `api/main.py`:

```python
from voice import get_voice_handler

# In route_message() function, add:

elif msg_type == "voice.audio":
    # Receive audio from frontend
    audio_b64 = data.get("audio", "")

    handler = get_voice_handler()
    audio_bytes = handler.decode_audio(audio_b64)

    # Transcribe with local Whisper (FREE)
    text = await handler.transcribe(audio_bytes)

    # Send transcription back
    await manager.send_message(websocket, {
        "type": "voice.transcription",
        "text": text,
    })

    # Process as regular message
    if text.strip():
        await process_user_message(websocket, text, msg_id)

elif msg_type == "voice.tts":
    # Frontend requesting TTS for a message
    text = data.get("text", "")

    handler = get_voice_handler()

    # Stream audio chunks
    async for chunk in handler.synthesize_stream(text):
        await manager.send_message(websocket, {
            "type": "voice.audio_chunk",
            "audio": handler.encode_audio(chunk),
            "format": "mp3",
        })

    await manager.send_message(websocket, {
        "type": "voice.audio_complete",
    })
```

---

## Part 3: Frontend Hooks

### 3.1 Audio Recorder (`useAudioRecorder.ts`)

```typescript
import { useState, useRef, useCallback } from "react";

interface AudioRecorderOptions {
  onAudioData?: (audioBlob: Blob) => void;
  onError?: (error: Error) => void;
}

export function useAudioRecorder(options: AudioRecorderOptions = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const animationRef = useRef<number>(0);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      streamRef.current = stream;

      // Audio level visualization
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const updateLevel = () => {
        const data = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(data);
        const avg = data.reduce((a, b) => a + b) / data.length;
        setAudioLevel(avg / 255);
        animationRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();

      // MediaRecorder
      const recorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        options.onAudioData?.(blob);

        stream.getTracks().forEach((t) => t.stop());
        cancelAnimationFrame(animationRef.current);
        setAudioLevel(0);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
    } catch (err) {
      options.onError?.(err as Error);
    }
  }, [options]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  return { isRecording, audioLevel, startRecording, stopRecording };
}
```

### 3.2 Audio Player (`useAudioPlayer.ts`)

```typescript
import { useState, useRef, useCallback } from "react";

export function useAudioPlayer() {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const queueRef = useRef<AudioBuffer[]>([]);
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);

  const getContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext();
    }
    return audioContextRef.current;
  }, []);

  const playChunk = useCallback(
    async (base64Audio: string) => {
      const ctx = getContext();

      // Decode base64 to ArrayBuffer
      const binary = atob(base64Audio);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }

      const buffer = await ctx.decodeAudioData(bytes.buffer);
      queueRef.current.push(buffer);

      if (!isPlaying) playNext();
    },
    [getContext, isPlaying]
  );

  const playNext = useCallback(() => {
    const ctx = audioContextRef.current;
    if (!ctx || queueRef.current.length === 0) {
      setIsPlaying(false);
      return;
    }

    setIsPlaying(true);
    const buffer = queueRef.current.shift()!;
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);
    source.onended = playNext;
    sourceRef.current = source;
    source.start();
  }, []);

  const stop = useCallback(() => {
    sourceRef.current?.stop();
    queueRef.current = [];
    setIsPlaying(false);
  }, []);

  return { isPlaying, playChunk, stop };
}
```

### 3.3 Update WebSocket Hook

Add to `useWebSocket.ts`:

```typescript
import { useAudioPlayer } from "./useAudioPlayer";

// Inside hook:
const audioPlayer = useAudioPlayer();

// Add to message handler:
case "voice.transcription":
  // User's speech was transcribed
  console.log("Transcribed:", data.text);
  break;

case "voice.audio_chunk":
  // Play TTS audio
  audioPlayer.playChunk(data.audio);
  break;

case "voice.audio_complete":
  console.log("TTS finished");
  break;

// Add sendAudio function:
const sendAudio = useCallback(async (blob: Blob) => {
  const buffer = await blob.arrayBuffer();
  const base64 = btoa(String.fromCharCode(...new Uint8Array(buffer)));

  send({
    type: "voice.audio",
    audio: base64,
    format: "webm",
  });
}, [send]);

// Return:
return { ...existing, sendAudio, audioPlayer };
```

### 3.4 Update MicrophoneButton

```typescript
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useWebSocket } from "@/hooks/useWebSocket";
import { toast } from "@/stores/toastStore";
import { cn } from "@/lib/utils";
import { Mic } from "lucide-react";

export function MicrophoneButton({ disabled }: { disabled?: boolean }) {
  const { sendAudio } = useWebSocket();

  const { isRecording, audioLevel, startRecording, stopRecording } =
    useAudioRecorder({
      onAudioData: (blob) => {
        sendAudio(blob);
        toast.info("Processing", "Transcribing...");
      },
      onError: (err) => {
        toast.error("Mic Error", err.message);
      },
    });

  return (
    <button
      onMouseDown={startRecording}
      onMouseUp={stopRecording}
      onMouseLeave={stopRecording}
      onTouchStart={startRecording}
      onTouchEnd={stopRecording}
      disabled={disabled}
      className={cn(
        "relative w-16 h-16 rounded-full",
        "bg-gradient-to-br from-[var(--gold-primary)] to-[var(--gold-dark)]",
        "flex items-center justify-center text-black",
        "transition-all duration-200",
        isRecording && "scale-110 shadow-[0_0_30px_rgba(212,175,55,0.5)]",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      {/* Level indicator */}
      {isRecording && (
        <div
          className="absolute inset-0 rounded-full bg-[var(--gold-primary)]/30"
          style={{ transform: `scale(${1 + audioLevel * 0.5})` }}
        />
      )}
      <Mic className={cn("w-6 h-6", isRecording && "animate-pulse")} />
    </button>
  );
}
```

---

## Part 4: Testing

### Test STT

```python
# test_stt.py
from voice import get_stt

print("Loading model (first run downloads ~466MB)...")
stt = get_stt("small")

text = stt.transcribe_file("test.wav")
print(f"Transcription: {text}")
```

### Test TTS

```python
# test_tts.py
import asyncio
from voice import get_tts

async def main():
    tts = get_tts()
    audio = await tts.synthesize("Hello, I am Emperor.")

    with open("output.mp3", "wb") as f:
        f.write(audio)
    print("Saved output.mp3")

asyncio.run(main())
```

---

## Model Sizes

| Model | Download | RAM | Speed | Quality |
|-------|----------|-----|-------|---------|
| tiny | 75 MB | ~1 GB | Fastest | Basic |
| base | 142 MB | ~1 GB | Very Fast | Good |
| **small** | 466 MB | ~2 GB | Fast | **Very Good** |
| medium | 1.5 GB | ~5 GB | Moderate | Excellent |
| large-v3 | 3 GB | ~10 GB | Slow | Best |

**Recommended: `small`** - best balance of speed and accuracy.

---

## Cost Summary

| Component | Provider | Cost |
|-----------|----------|------|
| Speech-to-Text | faster-whisper (local) | **FREE** |
| Text-to-Speech | Edge TTS (Microsoft) | **FREE** |
| **Total** | | **$0/month** |

---

## Checklist

### Backend
- [ ] Create `backend/voice/` directory
- [ ] Add `stt.py`, `tts.py`, `handler.py`, `__init__.py`
- [ ] Add dependencies to `requirements.txt`
- [ ] Install ffmpeg
- [ ] Add WebSocket handlers to `api/main.py`

### Frontendß
- [ ] Create `useAudioRecorder.ts`
- [ ] Create `useAudioPlayer.ts`
- [ ] Update `useWebSocket.ts`
- [ ] Update `MicrophoneButton.tsx`

### Test
- [ ] Test transcription with audio file
- [ ] Test TTS output
- [ ] Test full voice loop in app
