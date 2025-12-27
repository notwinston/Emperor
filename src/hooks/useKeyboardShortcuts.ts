import { useEffect, useCallback, useRef } from "react";

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  meta?: boolean; // Cmd on Mac
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description?: string;
  enabled?: boolean;
}

interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[];
  enabled?: boolean;
}

/**
 * Hook for handling keyboard shortcuts globally
 *
 * @example
 * useKeyboardShortcuts({
 *   shortcuts: [
 *     { key: "k", meta: true, action: () => openCommandPalette() },
 *     { key: "Enter", meta: true, action: () => sendMessage() },
 *   ]
 * });
 */
export function useKeyboardShortcuts({
  shortcuts,
  enabled = true,
}: UseKeyboardShortcutsOptions) {
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Don't trigger shortcuts when typing in inputs (unless explicitly handled)
      const target = event.target as HTMLElement;
      const isInput =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      for (const shortcut of shortcutsRef.current) {
        if (shortcut.enabled === false) continue;

        // Check key match (case-insensitive for letters)
        const keyMatch =
          event.key.toLowerCase() === shortcut.key.toLowerCase() ||
          event.code === shortcut.key;

        if (!keyMatch) continue;

        // Check modifiers
        const ctrlMatch = shortcut.ctrl ? event.ctrlKey : !event.ctrlKey;
        const metaMatch = shortcut.meta ? event.metaKey : !event.metaKey;
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatch = shortcut.alt ? event.altKey : !event.altKey;

        // For shortcuts with modifiers, allow them in inputs
        // For shortcuts without modifiers, block them in inputs
        const hasModifier =
          shortcut.ctrl || shortcut.meta || shortcut.shift || shortcut.alt;
        if (isInput && !hasModifier) continue;

        if (ctrlMatch && metaMatch && shiftMatch && altMatch) {
          event.preventDefault();
          shortcut.action();
          return;
        }
      }
    },
    [enabled]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}

/**
 * Hook for push-to-talk functionality
 */
export function usePushToTalk(onStart: () => void, onStop: () => void) {
  const isHolding = useRef(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Space bar for push-to-talk (only when not in input)
      if (event.code === "Space" && !isHolding.current) {
        const target = event.target as HTMLElement;
        const isInput =
          target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable;

        if (!isInput) {
          event.preventDefault();
          isHolding.current = true;
          onStart();
        }
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.code === "Space" && isHolding.current) {
        event.preventDefault();
        isHolding.current = false;
        onStop();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [onStart, onStop]);
}

/**
 * Format a shortcut for display
 */
export function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];

  if (shortcut.ctrl) parts.push("Ctrl");
  if (shortcut.meta) parts.push("⌘");
  if (shortcut.shift) parts.push("⇧");
  if (shortcut.alt) parts.push("⌥");

  // Format special keys
  const keyDisplay: Record<string, string> = {
    Enter: "↵",
    Escape: "Esc",
    ArrowUp: "↑",
    ArrowDown: "↓",
    ArrowLeft: "←",
    ArrowRight: "→",
    Backspace: "⌫",
    Delete: "Del",
    Space: "Space",
  };

  parts.push(keyDisplay[shortcut.key] || shortcut.key.toUpperCase());

  return parts.join(" ");
}

/**
 * Common app shortcuts
 */
export const APP_SHORTCUTS = {
  SEND_MESSAGE: { key: "Enter", meta: true },
  NEW_CONVERSATION: { key: "n", meta: true },
  OPEN_SETTINGS: { key: ",", meta: true },
  COMMAND_PALETTE: { key: "k", meta: true },
  TOGGLE_MICROPHONE: { key: "m", meta: true },
  STOP_SPEAKING: { key: ".", meta: true },
  CANCEL_OPERATION: { key: "Backspace", meta: true },
  COPY_LAST_RESPONSE: { key: "c", meta: true, shift: true },
} as const;
