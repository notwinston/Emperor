import { useState } from "react";
import { X, Cpu, Mic, Shield, Database, Wifi, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  useSettingsStore,
  TTS_VOICES,
  type ModelType,
  type PermissionLevel,
  type VoiceMode,
  type TTSVoiceId
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
