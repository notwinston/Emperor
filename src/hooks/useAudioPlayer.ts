/**
 * Audio player hook for streaming TTS playback.
 *
 * Queues and plays audio chunks received from the backend,
 * providing seamless streaming audio playback.
 */

import { useState, useRef, useCallback } from "react";

interface AudioPlayerState {
  /** Whether audio is currently playing */
  isPlaying: boolean;
  /** Queue a base64 audio chunk for playback */
  playChunk: (base64Audio: string) => Promise<void>;
  /** Stop playback and clear queue */
  stop: () => void;
  /** Number of chunks waiting in queue */
  queueLength: number;
}

export function useAudioPlayer(): AudioPlayerState {
  const [isPlaying, setIsPlaying] = useState(false);
  const [queueLength, setQueueLength] = useState(0);

  const audioContextRef = useRef<AudioContext | null>(null);
  const queueRef = useRef<AudioBuffer[]>([]);
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);
  const isPlayingRef = useRef(false);

  const getContext = useCallback(() => {
    if (!audioContextRef.current || audioContextRef.current.state === "closed") {
      audioContextRef.current = new AudioContext();
    }
    // Resume if suspended (browser autoplay policy)
    if (audioContextRef.current.state === "suspended") {
      audioContextRef.current.resume();
    }
    return audioContextRef.current;
  }, []);

  const playNext = useCallback(() => {
    const ctx = audioContextRef.current;

    if (!ctx || queueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsPlaying(false);
      setQueueLength(0);
      return;
    }

    isPlayingRef.current = true;
    setIsPlaying(true);

    const buffer = queueRef.current.shift()!;
    setQueueLength(queueRef.current.length);

    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    source.onended = () => {
      sourceRef.current = null;
      playNext();
    };

    sourceRef.current = source;
    source.start();
  }, []);

  const playChunk = useCallback(
    async (base64Audio: string) => {
      try {
        const ctx = getContext();

        // Decode base64 to ArrayBuffer
        const binaryString = atob(base64Audio);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }

        // Decode audio data
        const audioBuffer = await ctx.decodeAudioData(bytes.buffer.slice(0));

        // Add to queue
        queueRef.current.push(audioBuffer);
        setQueueLength(queueRef.current.length);

        // Start playing if not already
        if (!isPlayingRef.current) {
          playNext();
        }
      } catch (error) {
        console.error("Failed to decode audio chunk:", error);
      }
    },
    [getContext, playNext]
  );

  const stop = useCallback(() => {
    // Stop current source
    if (sourceRef.current) {
      try {
        sourceRef.current.stop();
      } catch {
        // Ignore if already stopped
      }
      sourceRef.current = null;
    }

    // Clear queue
    queueRef.current = [];
    setQueueLength(0);

    isPlayingRef.current = false;
    setIsPlaying(false);
  }, []);

  return {
    isPlaying,
    playChunk,
    stop,
    queueLength,
  };
}
