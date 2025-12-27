# Settings Panel Implementation Guide

## Step 12.4: Settings Panel

Create a comprehensive settings panel for Emperor AI Assistant with model selection, voice settings, permissions, memory management, and connection settings.

---

## Overview

The Settings Panel provides user configuration for:
- **Model Selection**: Choose between Claude Sonnet and Opus
- **Voice Settings**: Enable/disable voice, select TTS voice, auto-send vs input field
- **Permission Defaults**: Strict, moderate, or relaxed approval modes
- **Memory Management**: Clear memory, export conversation history
- **Connection Settings**: Server URL, reconnection behavior

---

## Part 1: Settings Store

### 1.1 Create Settings Store (`src/stores/settingsStore.ts`)

```typescript
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
  ttsVoice: "af_heart" as TTSVoiceId,  // Kokoro default voice
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
```

---

## Part 2: Settings Panel Component

### 2.1 Create Settings Panel (`src/components/SettingsPanel.tsx`)

```typescript
import { useState } from "react";
import { X, Cpu, Mic, Shield, Database, Wifi, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  useSettingsStore,
  TTS_VOICES,
  ModelType,
  PermissionLevel,
  VoiceMode,
  TTSVoiceId
} from "@/stores/settingsStore";
import { useConversationStore } from "@/stores/conversationStore";
import { cn } from "@/lib/utils";

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

type SettingsTab = "model" | "voice" | "permissions" | "memory" | "connection";

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>("model");

  const settings = useSettingsStore();
  const { clearMessages } = useConversationStore();

  if (!isOpen) return null;

  const tabs: { id: SettingsTab; label: string; icon: React.ReactNode }[] = [
    { id: "model", label: "Model", icon: <Cpu className="h-4 w-4" /> },
    { id: "voice", label: "Voice", icon: <Mic className="h-4 w-4" /> },
    { id: "permissions", label: "Permissions", icon: <Shield className="h-4 w-4" /> },
    { id: "memory", label: "Memory", icon: <Database className="h-4 w-4" /> },
    { id: "connection", label: "Connection", icon: <Wifi className="h-4 w-4" /> },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative z-10 w-full max-w-2xl max-h-[80vh] overflow-hidden rounded-2xl bg-[var(--black-secondary)] border border-[var(--gold-primary)]/20 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--gold-primary)]/10">
          <h2 className="text-xl font-semibold text-[var(--gold-light)]">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[var(--black-tertiary)] text-[var(--gold-dark)] hover:text-[var(--gold-primary)] transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex h-[60vh]">
          {/* Sidebar Tabs */}
          <div className="w-48 border-r border-[var(--gold-primary)]/10 p-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors",
                  activeTab === tab.id
                    ? "bg-[var(--gold-primary)]/10 text-[var(--gold-primary)]"
                    : "text-[var(--gold-dark)] hover:bg-[var(--black-tertiary)] hover:text-[var(--gold-light)]"
                )}
              >
                {tab.icon}
                <span className="text-sm font-medium">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === "model" && <ModelSettings />}
            {activeTab === "voice" && <VoiceSettings />}
            {activeTab === "permissions" && <PermissionSettings />}
            {activeTab === "memory" && <MemorySettings />}
            {activeTab === "connection" && <ConnectionSettings />}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--gold-primary)]/10">
          <button
            onClick={settings.resetToDefaults}
            className="flex items-center gap-2 px-4 py-2 text-sm text-[var(--gold-dark)] hover:text-[var(--gold-primary)] transition-colors"
          >
            <RotateCcw className="h-4 w-4" />
            Reset to Defaults
          </button>
          <Button onClick={onClose}>Done</Button>
        </div>
      </div>
    </div>
  );
}

// ============================================
// Model Settings Section
// ============================================

function ModelSettings() {
  const { model, setModel } = useSettingsStore();

  const models: { id: ModelType; name: string; description: string }[] = [
    {
      id: "sonnet",
      name: "Claude Sonnet",
      description: "Fast and efficient. Best for most tasks.",
    },
    {
      id: "opus",
      name: "Claude Opus",
      description: "Most capable. Best for complex reasoning.",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-[var(--gold-light)] mb-1">AI Model</h3>
        <p className="text-sm text-[var(--gold-dark)]">
          Choose which Claude model powers Emperor
        </p>
      </div>

      <div className="space-y-3">
        {models.map((m) => (
          <button
            key={m.id}
            onClick={() => setModel(m.id)}
            className={cn(
              "w-full p-4 rounded-xl border text-left transition-all",
              model === m.id
                ? "border-[var(--gold-primary)] bg-[var(--gold-primary)]/10"
                : "border-[var(--gold-primary)]/20 hover:border-[var(--gold-primary)]/40"
            )}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-[var(--gold-light)]">{m.name}</div>
                <div className="text-sm text-[var(--gold-dark)]">{m.description}</div>
              </div>
              <div
                className={cn(
                  "h-5 w-5 rounded-full border-2 flex items-center justify-center",
                  model === m.id
                    ? "border-[var(--gold-primary)]"
                    : "border-[var(--gold-dark)]"
                )}
              >
                {model === m.id && (
                  <div className="h-2.5 w-2.5 rounded-full bg-[var(--gold-primary)]" />
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// ============================================
// Voice Settings Section
// ============================================

function VoiceSettings() {
  const {
    voiceEnabled,
    setVoiceEnabled,
    ttsVoice,
    setTTSVoice,
    voiceMode,
    setVoiceMode,
    ttsEnabled,
    setTTSEnabled,
  } = useSettingsStore();

  // Auto-read setting is in conversationStore (enabled by default)
  const { autoReadResponses, setAutoReadResponses } = useConversationStore();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-[var(--gold-light)] mb-1">Voice Settings</h3>
        <p className="text-sm text-[var(--gold-dark)]">
          Configure voice input and text-to-speech
        </p>
      </div>

      {/* Voice Input Toggle */}
      <SettingRow
        label="Voice Input"
        description="Enable microphone for voice commands"
      >
        <Switch
          checked={voiceEnabled}
          onCheckedChange={setVoiceEnabled}
        />
      </SettingRow>

      {/* Voice Mode */}
      {voiceEnabled && (
        <div className="space-y-3">
          <label className="text-sm font-medium text-[var(--gold-light)]">
            After transcription
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setVoiceMode("input_field")}
              className={cn(
                "p-3 rounded-lg border text-center transition-all",
                voiceMode === "input_field"
                  ? "border-[var(--gold-primary)] bg-[var(--gold-primary)]/10"
                  : "border-[var(--gold-primary)]/20 hover:border-[var(--gold-primary)]/40"
              )}
            >
              <div className="text-sm font-medium text-[var(--gold-light)]">Add to Input</div>
              <div className="text-xs text-[var(--gold-dark)]">Edit before sending</div>
            </button>
            <button
              onClick={() => setVoiceMode("auto_send")}
              className={cn(
                "p-3 rounded-lg border text-center transition-all",
                voiceMode === "auto_send"
                  ? "border-[var(--gold-primary)] bg-[var(--gold-primary)]/10"
                  : "border-[var(--gold-primary)]/20 hover:border-[var(--gold-primary)]/40"
              )}
            >
              <div className="text-sm font-medium text-[var(--gold-light)]">Auto Send</div>
              <div className="text-xs text-[var(--gold-dark)]">Send immediately</div>
            </button>
          </div>
        </div>
      )}

      <div className="h-px bg-[var(--gold-primary)]/10" />

      {/* Auto-Read Responses Toggle */}
      <SettingRow
        label="Auto-Read Responses"
        description="Automatically read assistant responses aloud"
      >
        <Switch
          checked={autoReadResponses}
          onCheckedChange={setAutoReadResponses}
        />
      </SettingRow>

      {/* TTS Enabled Toggle */}
      <SettingRow
        label="Text-to-Speech"
        description="Enable TTS functionality"
      >
        <Switch
          checked={ttsEnabled}
          onCheckedChange={setTTSEnabled}
        />
      </SettingRow>

      {/* TTS Voice Selection - Kokoro 82M */}
      {ttsEnabled && (
        <div className="space-y-3">
          <label className="text-sm font-medium text-[var(--gold-light)]">
            Voice (Kokoro 82M - Local)
          </label>
          <select
            value={ttsVoice}
            onChange={(e) => setTTSVoice(e.target.value as TTSVoiceId)}
            className="w-full px-4 py-2 rounded-lg bg-[var(--black-tertiary)] border border-[var(--gold-primary)]/20 text-[var(--gold-light)] focus:border-[var(--gold-primary)]/50 focus:outline-none"
          >
            <optgroup label="American English">
              {TTS_VOICES.filter(v => v.lang === "American English").map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.name} ({voice.gender})
                </option>
              ))}
            </optgroup>
            <optgroup label="British English">
              {TTS_VOICES.filter(v => v.lang === "British English").map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.name} ({voice.gender})
                </option>
              ))}
            </optgroup>
          </select>
          <p className="text-xs text-[var(--gold-dark)]">
            Powered by Kokoro 82M - runs locally, no API costs
          </p>
        </div>
      )}
    </div>
  );
}

// ============================================
// Permission Settings Section
// ============================================

function PermissionSettings() {
  const { permissionLevel, setPermissionLevel } = useSettingsStore();

  const levels: { id: PermissionLevel; name: string; description: string }[] = [
    {
      id: "strict",
      name: "Strict",
      description: "Require approval for all file and system operations",
    },
    {
      id: "moderate",
      name: "Moderate",
      description: "Approve read operations automatically, ask for writes",
    },
    {
      id: "relaxed",
      name: "Relaxed",
      description: "Auto-approve most operations, ask only for high-risk",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-[var(--gold-light)] mb-1">Permission Level</h3>
        <p className="text-sm text-[var(--gold-dark)]">
          Control when Emperor asks for approval
        </p>
      </div>

      <div className="space-y-3">
        {levels.map((level) => (
          <button
            key={level.id}
            onClick={() => setPermissionLevel(level.id)}
            className={cn(
              "w-full p-4 rounded-xl border text-left transition-all",
              permissionLevel === level.id
                ? "border-[var(--gold-primary)] bg-[var(--gold-primary)]/10"
                : "border-[var(--gold-primary)]/20 hover:border-[var(--gold-primary)]/40"
            )}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-[var(--gold-light)]">{level.name}</div>
                <div className="text-sm text-[var(--gold-dark)]">{level.description}</div>
              </div>
              <div
                className={cn(
                  "h-5 w-5 rounded-full border-2 flex items-center justify-center",
                  permissionLevel === level.id
                    ? "border-[var(--gold-primary)]"
                    : "border-[var(--gold-dark)]"
                )}
              >
                {permissionLevel === level.id && (
                  <div className="h-2.5 w-2.5 rounded-full bg-[var(--gold-primary)]" />
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="p-4 rounded-lg bg-[var(--gold-primary)]/5 border border-[var(--gold-primary)]/10">
        <p className="text-xs text-[var(--gold-dark)]">
          <strong className="text-[var(--gold-light)]">Note:</strong> Even in relaxed mode,
          destructive operations like deleting files or running system commands
          will always require your approval.
        </p>
      </div>
    </div>
  );
}

// ============================================
// Memory Settings Section
// ============================================

function MemorySettings() {
  const { clearMessages, messages } = useConversationStore();
  const [isClearing, setIsClearing] = useState(false);

  const handleClearMemory = async () => {
    if (!confirm("Clear all conversation history? This cannot be undone.")) return;

    setIsClearing(true);
    // TODO: Also clear backend memory via API
    clearMessages();
    setIsClearing(false);
  };

  const handleExportHistory = () => {
    const data = JSON.stringify(messages, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `emperor-history-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-[var(--gold-light)] mb-1">Memory Management</h3>
        <p className="text-sm text-[var(--gold-dark)]">
          Manage conversation history and stored memories
        </p>
      </div>

      <div className="space-y-4">
        <div className="p-4 rounded-xl border border-[var(--gold-primary)]/20">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-[var(--gold-light)]">Conversation History</div>
              <div className="text-sm text-[var(--gold-dark)]">
                {messages.length} messages in current session
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={handleExportHistory}>
              Export
            </Button>
          </div>
        </div>

        <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-red-400">Clear All Data</div>
              <div className="text-sm text-red-400/70">
                Delete conversation history and memories
              </div>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleClearMemory}
              disabled={isClearing}
            >
              {isClearing ? "Clearing..." : "Clear"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================
// Connection Settings Section
// ============================================

function ConnectionSettings() {
  const {
    serverUrl,
    setServerUrl,
    autoReconnect,
    setAutoReconnect,
    maxReconnectAttempts,
    setMaxReconnectAttempts,
  } = useSettingsStore();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-[var(--gold-light)] mb-1">Connection</h3>
        <p className="text-sm text-[var(--gold-dark)]">
          Configure server connection settings
        </p>
      </div>

      {/* Server URL */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-[var(--gold-light)]">
          Server URL
        </label>
        <input
          type="text"
          value={serverUrl}
          onChange={(e) => setServerUrl(e.target.value)}
          className="w-full px-4 py-2 rounded-lg bg-[var(--black-tertiary)] border border-[var(--gold-primary)]/20 text-[var(--gold-light)] focus:border-[var(--gold-primary)]/50 focus:outline-none"
          placeholder="ws://127.0.0.1:8765/ws"
        />
        <p className="text-xs text-[var(--gold-dark)]">
          WebSocket URL for the backend server
        </p>
      </div>

      <div className="h-px bg-[var(--gold-primary)]/10" />

      {/* Auto Reconnect */}
      <SettingRow
        label="Auto Reconnect"
        description="Automatically reconnect when connection is lost"
      >
        <Switch
          checked={autoReconnect}
          onCheckedChange={setAutoReconnect}
        />
      </SettingRow>

      {/* Max Reconnect Attempts */}
      {autoReconnect && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-[var(--gold-light)]">
            Max Reconnect Attempts
          </label>
          <input
            type="number"
            value={maxReconnectAttempts}
            onChange={(e) => setMaxReconnectAttempts(Number(e.target.value))}
            min={1}
            max={20}
            className="w-24 px-4 py-2 rounded-lg bg-[var(--black-tertiary)] border border-[var(--gold-primary)]/20 text-[var(--gold-light)] focus:border-[var(--gold-primary)]/50 focus:outline-none"
          />
        </div>
      )}
    </div>
  );
}

// ============================================
// Utility Components
// ============================================

function SettingRow({
  label,
  description,
  children,
}: {
  label: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <div className="font-medium text-[var(--gold-light)]">{label}</div>
        <div className="text-sm text-[var(--gold-dark)]">{description}</div>
      </div>
      {children}
    </div>
  );
}
```

---

## Part 3: UI Components

### 3.1 Create Switch Component (`src/components/ui/switch.tsx`)

```typescript
import * as React from "react";
import * as SwitchPrimitives from "@radix-ui/react-switch";
import { cn } from "@/lib/utils";

const Switch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitives.Root
    className={cn(
      "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--gold-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--black-primary)]",
      "disabled:cursor-not-allowed disabled:opacity-50",
      "data-[state=checked]:bg-[var(--gold-primary)] data-[state=unchecked]:bg-[var(--black-tertiary)]",
      className
    )}
    {...props}
    ref={ref}
  >
    <SwitchPrimitives.Thumb
      className={cn(
        "pointer-events-none block h-5 w-5 rounded-full shadow-lg ring-0 transition-transform",
        "bg-white data-[state=checked]:bg-[var(--black-primary)]",
        "data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0"
      )}
    />
  </SwitchPrimitives.Root>
));
Switch.displayName = SwitchPrimitives.Root.displayName;

export { Switch };
```

### 3.2 Install Radix Switch

```bash
pnpm add @radix-ui/react-switch
```

---

## Part 4: Integration

### 4.1 Add Settings Button to Sidebar

Update `src/components/Sidebar.tsx`:

```typescript
// Add to imports
import { Settings } from "lucide-react";
import { useState } from "react";
import { SettingsPanel } from "./SettingsPanel";

// Inside Sidebar component
const [settingsOpen, setSettingsOpen] = useState(false);

// Add settings button to nav items
<button
  onClick={() => setSettingsOpen(true)}
  className={cn(
    "flex items-center gap-3 w-full px-3 py-2 rounded-lg transition-colors",
    "text-[var(--gold-dark)] hover:bg-[var(--black-tertiary)] hover:text-[var(--gold-light)]"
  )}
>
  <Settings className="h-5 w-5" />
  {!collapsed && <span>Settings</span>}
</button>

// Add SettingsPanel at end of component
<SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
```

### 4.2 Use Settings in WebSocket Hook

Update `src/hooks/useWebSocket.ts` to use settings:

```typescript
import { useSettingsStore } from "@/stores/settingsStore";

export function useWebSocket(voiceCallbacks?: VoiceCallbacks) {
  const { serverUrl, autoReconnect, maxReconnectAttempts } = useSettingsStore();

  // Use serverUrl instead of hardcoded WS_URL
  // Use maxReconnectAttempts instead of MAX_RECONNECT_ATTEMPTS
  // Use autoReconnect to control reconnection behavior
}
```

### 4.3 Use Voice Mode Setting

Update voice transcription handler in `useWebSocket.ts`:

```typescript
import { useSettingsStore } from "@/stores/settingsStore";

// In handleMessage for voice.transcription:
const { voiceMode } = useSettingsStore.getState();

if (payload.text.trim()) {
  if (voiceMode === "auto_send") {
    // Add as message and process
    addMessage({ ... });
  } else {
    // Put in input field
    voiceCallbacksRef.current?.onSetInputText?.(payload.text);
  }
}
```

### 4.4 Send Voice Mode to Backend

Update `sendAudio` in `useWebSocket.ts`:

```typescript
const sendAudio = useCallback(async (audioBlob: Blob) => {
  const { voiceMode } = useSettingsStore.getState();

  // ... existing code ...

  const event: WSEvent = {
    event_id: generateId(),
    event_type: "voice.audio",
    source: "frontend",
    timestamp: new Date().toISOString(),
    payload: {
      audio: base64Audio,
      format,
      auto_send: voiceMode === "auto_send",  // Add this
    },
  };

  // ... rest of code ...
}, []);
```

---

## Part 5: Backend Settings API (Optional)

### 5.1 Add Settings Endpoint

```python
# backend/api/main.py

from voice import get_voice_handler
from voice.tts import get_available_voices, DEFAULT_VOICE

@app.post("/api/settings")
async def update_settings(settings: dict):
    """Update backend settings (model, voice, etc.)"""
    # Update model selection
    if "model" in settings:
        # Store model preference
        pass

    # Update TTS voice (Kokoro 82M)
    if "tts_voice" in settings:
        handler = get_voice_handler()
        if handler.set_tts_voice(settings["tts_voice"]):
            return {"status": "ok", "voice": settings["tts_voice"]}
        return {"status": "error", "message": "Unknown voice"}

    return {"status": "ok"}

@app.get("/api/settings")
async def get_settings():
    """Get current backend settings"""
    handler = get_voice_handler()
    return {
        "model": "sonnet",
        "tts_voice": handler.tts_voice,  # Kokoro voice ID (e.g., af_heart)
    }

@app.get("/api/voices")
async def list_voices():
    """Get all available Kokoro TTS voices"""
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
```

---

## Part 6: Keyboard Shortcuts

Add settings shortcut in `App.tsx`:

```typescript
useKeyboardShortcuts({
  shortcuts: [
    {
      ...APP_SHORTCUTS.OPEN_SETTINGS,
      action: () => setSettingsOpen(true),
      description: "Open settings",
    },
    // ... other shortcuts
  ],
});
```

---

## Checklist

### Frontend
- [ ] Create `src/stores/settingsStore.ts`
- [ ] Create `src/components/SettingsPanel.tsx`
- [ ] Create `src/components/ui/switch.tsx`
- [ ] Install `@radix-ui/react-switch`
- [ ] Add settings button to Sidebar
- [ ] Update WebSocket hook to use settings
- [ ] Add keyboard shortcut (Cmd+,)

### Backend (Optional)
- [ ] Add settings endpoints
- [ ] Use model setting for Claude API calls
- [ ] Use TTS voice setting

### Testing
- [ ] Model selection persists
- [ ] Voice mode switches correctly
- [ ] Permission level affects approvals
- [ ] Export conversation works
- [ ] Clear memory works
- [ ] Connection settings reconnect correctly

---

## Settings Summary

| Setting | Location | Default |
|---------|----------|---------|
| Model | Model tab | Sonnet |
| Voice Input | Voice tab | Enabled |
| Voice Mode | Voice tab | Input Field |
| **Auto-Read Responses** | Voice tab | **Enabled** |
| TTS | Voice tab | Disabled |
| TTS Voice | Voice tab | Heart (US) - Kokoro af_heart |
| Permission Level | Permissions tab | Moderate |
| Server URL | Connection tab | ws://127.0.0.1:8765/ws |
| Auto Reconnect | Connection tab | Enabled |
| Max Attempts | Connection tab | 5 |

> **Note:** Auto-Read Responses is stored in `conversationStore` and is enabled by default.
> When enabled, all assistant responses are automatically read aloud using Kokoro TTS.

---

## TTS Implementation Note

This settings panel uses **Kokoro 82M** for text-to-speech, a local and free TTS model. See `docs/TTS_IMPLEMENTATION.md` for full implementation details including:
- Backend Kokoro TTS module
- Voice handler updates
- API endpoints for voice management
- Full list of 54 available voices
