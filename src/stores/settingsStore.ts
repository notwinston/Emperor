import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ModelType = "sonnet" | "opus";
export type PermissionLevel = "strict" | "moderate" | "relaxed";
export type VoiceMode = "auto_send" | "input_field";

// Available TTS voices (Kokoro 82M - Local & Free)
export const TTS_VOICES = [
  // American English - Female
  { id: "af_heart", name: "Heart (US)", gender: "female", lang: "American English" },
  { id: "af_bella", name: "Bella (US)", gender: "female", lang: "American English" },
  { id: "af_jessica", name: "Jessica (US)", gender: "female", lang: "American English" },
  { id: "af_nicole", name: "Nicole (US)", gender: "female", lang: "American English" },
  { id: "af_nova", name: "Nova (US)", gender: "female", lang: "American English" },
  { id: "af_sarah", name: "Sarah (US)", gender: "female", lang: "American English" },
  { id: "af_sky", name: "Sky (US)", gender: "female", lang: "American English" },
  // American English - Male
  { id: "am_adam", name: "Adam (US)", gender: "male", lang: "American English" },
  { id: "am_eric", name: "Eric (US)", gender: "male", lang: "American English" },
  { id: "am_liam", name: "Liam (US)", gender: "male", lang: "American English" },
  { id: "am_michael", name: "Michael (US)", gender: "male", lang: "American English" },
  // British English - Female
  { id: "bf_alice", name: "Alice (UK)", gender: "female", lang: "British English" },
  { id: "bf_emma", name: "Emma (UK)", gender: "female", lang: "British English" },
  { id: "bf_lily", name: "Lily (UK)", gender: "female", lang: "British English" },
  // British English - Male
  { id: "bm_daniel", name: "Daniel (UK)", gender: "male", lang: "British English" },
  { id: "bm_george", name: "George (UK)", gender: "male", lang: "British English" },
] as const;

export type TTSVoiceId = (typeof TTS_VOICES)[number]["id"];

interface SettingsState {
  // Model settings
  model: ModelType;
  setModel: (model: ModelType) => void;

  // Voice settings
  voiceEnabled: boolean;
  setVoiceEnabled: (enabled: boolean) => void;
  ttsVoice: TTSVoiceId;
  setTTSVoice: (voice: TTSVoiceId) => void;
  voiceMode: VoiceMode;
  setVoiceMode: (mode: VoiceMode) => void;
  ttsEnabled: boolean;
  setTTSEnabled: (enabled: boolean) => void;

  // Permission settings
  permissionLevel: PermissionLevel;
  setPermissionLevel: (level: PermissionLevel) => void;

  // Connection settings
  serverUrl: string;
  setServerUrl: (url: string) => void;
  autoReconnect: boolean;
  setAutoReconnect: (enabled: boolean) => void;
  maxReconnectAttempts: number;
  setMaxReconnectAttempts: (attempts: number) => void;

  // Actions
  resetToDefaults: () => void;
}

const DEFAULT_SETTINGS = {
  model: "sonnet" as ModelType,
  voiceEnabled: true,
  ttsVoice: "af_heart" as TTSVoiceId,
  voiceMode: "input_field" as VoiceMode,
  ttsEnabled: false,
  permissionLevel: "moderate" as PermissionLevel,
  serverUrl: "ws://127.0.0.1:8765/ws",
  autoReconnect: true,
  maxReconnectAttempts: 5,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...DEFAULT_SETTINGS,

      setModel: (model) => set({ model }),
      setVoiceEnabled: (voiceEnabled) => set({ voiceEnabled }),
      setTTSVoice: (ttsVoice) => set({ ttsVoice }),
      setVoiceMode: (voiceMode) => set({ voiceMode }),
      setTTSEnabled: (ttsEnabled) => set({ ttsEnabled }),
      setPermissionLevel: (permissionLevel) => set({ permissionLevel }),
      setServerUrl: (serverUrl) => set({ serverUrl }),
      setAutoReconnect: (autoReconnect) => set({ autoReconnect }),
      setMaxReconnectAttempts: (maxReconnectAttempts) =>
        set({ maxReconnectAttempts }),

      resetToDefaults: () => set(DEFAULT_SETTINGS),
    }),
    {
      name: "emperor-settings",
    }
  )
);
