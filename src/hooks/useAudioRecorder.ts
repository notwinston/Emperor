/**
 * Audio recorder hook for capturing microphone input.
 *
 * Uses MediaRecorder API to capture audio and provides
 * real-time audio level visualization.
 */

import { useState, useRef, useCallback } from "react";

interface AudioRecorderOptions {
  /** Called when recording stops with the audio blob */
  onAudioData?: (audioBlob: Blob) => void;
  /** Called on recording error */
  onError?: (error: Error) => void;
  /** Called when recording starts */
  onStart?: () => void;
  /** Called when recording stops */
  onStop?: () => void;
}

interface AudioRecorderState {
  /** Whether currently recording */
  isRecording: boolean;
  /** Audio level 0-1 for visualization */
  audioLevel: number;
  /** Start recording */
  startRecording: () => Promise<void>;
  /** Stop recording */
  stopRecording: () => void;
  /** Whether microphone permission was denied */
  permissionDenied: boolean;
}

export function useAudioRecorder(
  options: AudioRecorderOptions = {}
): AudioRecorderState {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [permissionDenied, setPermissionDenied] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number>(0);

  // Use refs for callbacks to avoid stale closures
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const cleanup = useCallback(() => {
    // Stop animation frame
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = 0;
    }

    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    setAudioLevel(0);
  }, []);

  const startRecording = useCallback(async () => {
    try {
      // Check if mediaDevices is available (requires secure context)
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error(
          "Microphone access not available. This may be because the app is not running in a secure context (HTTPS or localhost)."
        );
      }

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;
      setPermissionDenied(false);

      // Set up audio level visualization
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Update audio level for visualization
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!analyserRef.current) return;

        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(Math.min(average / 128, 1)); // Normalize to 0-1

        animationRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();

      // Set up MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        optionsRef.current.onAudioData?.(blob);
        optionsRef.current.onStop?.();
        cleanup();
      };

      recorder.onerror = () => {
        const error = new Error("MediaRecorder error");
        optionsRef.current.onError?.(error);
        cleanup();
        setIsRecording(false);
      };

      // Start recording
      recorder.start();
      setIsRecording(true);
      optionsRef.current.onStart?.();
      console.log("[useAudioRecorder] Recording started");
    } catch (err) {
      const error = err as Error;
      console.error("[useAudioRecorder] Error starting recording:", error);

      // Check if permission denied
      if (
        error.name === "NotAllowedError" ||
        error.name === "PermissionDeniedError"
      ) {
        setPermissionDenied(true);
      }

      optionsRef.current.onError?.(error);
      cleanup();
      setIsRecording(false);
    }
  }, [cleanup]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
      setIsRecording(false);
    }
  }, [isRecording]);

  return {
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    permissionDenied,
  };
}
