import { create } from "zustand";
import { persist } from "zustand/middleware";

export type PermissionPreset = "strict" | "moderate" | "relaxed";

interface UserConfig {
  name: string;
  permissionPreset: PermissionPreset;
  preferences: {
    theme: "dark" | "light" | "system";
    voiceEnabled: boolean;
    soundEffects: boolean;
  };
}

interface OnboardingState {
  // Whether onboarding has been completed
  isComplete: boolean;

  // Current step in onboarding (0-indexed)
  currentStep: number;

  // User configuration
  userConfig: UserConfig;

  // Actions
  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  setUserName: (name: string) => void;
  setPermissionPreset: (preset: PermissionPreset) => void;
  setPreference: <K extends keyof UserConfig["preferences"]>(
    key: K,
    value: UserConfig["preferences"][K]
  ) => void;
  completeOnboarding: () => void;
  resetOnboarding: () => void;
}

const defaultUserConfig: UserConfig = {
  name: "",
  permissionPreset: "moderate",
  preferences: {
    theme: "dark",
    voiceEnabled: true,
    soundEffects: true,
  },
};

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      isComplete: false,
      currentStep: 0,
      userConfig: defaultUserConfig,

      setStep: (step) => set({ currentStep: step }),

      nextStep: () =>
        set((state) => ({ currentStep: state.currentStep + 1 })),

      prevStep: () =>
        set((state) => ({
          currentStep: Math.max(0, state.currentStep - 1),
        })),

      setUserName: (name) =>
        set((state) => ({
          userConfig: { ...state.userConfig, name },
        })),

      setPermissionPreset: (preset) =>
        set((state) => ({
          userConfig: { ...state.userConfig, permissionPreset: preset },
        })),

      setPreference: (key, value) =>
        set((state) => ({
          userConfig: {
            ...state.userConfig,
            preferences: {
              ...state.userConfig.preferences,
              [key]: value,
            },
          },
        })),

      completeOnboarding: () => set({ isComplete: true }),

      resetOnboarding: () =>
        set({
          isComplete: false,
          currentStep: 0,
          userConfig: defaultUserConfig,
        }),
    }),
    {
      name: "emperor-onboarding",
    }
  )
);
