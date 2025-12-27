import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useOnboardingStore, PermissionPreset } from "@/stores/onboardingStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// Step components
function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center text-center">
      <div className="mb-8">
        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center mb-6 mx-auto shadow-lg shadow-amber-500/20">
          <span className="text-4xl">👑</span>
        </div>
        <h1 className="text-3xl font-bold text-foreground mb-3">
          Welcome to Emperor
        </h1>
        <p className="text-muted-foreground max-w-md">
          Your intelligent AI assistant powered by Claude. Let's set up your
          experience in just a few steps.
        </p>
      </div>
      <Button
        onClick={onNext}
        className="bg-amber-500 hover:bg-amber-600 text-black font-semibold px-8"
      >
        Get Started
      </Button>
    </div>
  );
}

function NameStep({
  onNext,
  onPrev,
}: {
  onNext: () => void;
  onPrev: () => void;
}) {
  const { userConfig, setUserName } = useOnboardingStore();
  const [name, setName] = useState(userConfig.name);

  const handleContinue = () => {
    setUserName(name.trim());
    onNext();
  };

  return (
    <div className="flex flex-col items-center justify-center text-center">
      <h2 className="text-2xl font-bold text-foreground mb-2">
        What should I call you?
      </h2>
      <p className="text-muted-foreground mb-8 max-w-md">
        This helps personalize your experience.
      </p>

      <Input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Enter your name"
        className="max-w-xs text-center text-lg mb-8 bg-zinc-900 border-zinc-700"
        autoFocus
        onKeyDown={(e) => {
          if (e.key === "Enter" && name.trim()) {
            handleContinue();
          }
        }}
      />

      <div className="flex gap-3">
        <Button variant="ghost" onClick={onPrev}>
          Back
        </Button>
        <Button
          onClick={handleContinue}
          disabled={!name.trim()}
          className="bg-amber-500 hover:bg-amber-600 text-black font-semibold px-8"
        >
          Continue
        </Button>
      </div>
    </div>
  );
}

function PermissionStep({
  onNext,
  onPrev,
}: {
  onNext: () => void;
  onPrev: () => void;
}) {
  const { userConfig, setPermissionPreset } = useOnboardingStore();

  const presets: {
    id: PermissionPreset;
    name: string;
    description: string;
    icon: string;
  }[] = [
    {
      id: "strict",
      name: "Strict",
      description: "Approve most operations. Best for sensitive work.",
      icon: "🔒",
    },
    {
      id: "moderate",
      name: "Moderate",
      description: "Approve sensitive operations only. Recommended.",
      icon: "⚖️",
    },
    {
      id: "relaxed",
      name: "Relaxed",
      description: "Minimal approvals. For trusted environments.",
      icon: "🚀",
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center text-center">
      <h2 className="text-2xl font-bold text-foreground mb-2">
        Permission Level
      </h2>
      <p className="text-muted-foreground mb-8 max-w-md">
        Choose how much oversight you want over AI actions.
      </p>

      <div className="flex flex-col gap-3 w-full max-w-md mb-8">
        {presets.map((preset) => (
          <button
            key={preset.id}
            onClick={() => setPermissionPreset(preset.id)}
            className={cn(
              "flex items-center gap-4 p-4 rounded-lg border transition-all text-left",
              userConfig.permissionPreset === preset.id
                ? "border-amber-500 bg-amber-500/10"
                : "border-zinc-700 bg-zinc-900 hover:border-zinc-600"
            )}
          >
            <span className="text-2xl">{preset.icon}</span>
            <div>
              <div className="font-semibold text-foreground">{preset.name}</div>
              <div className="text-sm text-muted-foreground">
                {preset.description}
              </div>
            </div>
            {userConfig.permissionPreset === preset.id && (
              <div className="ml-auto text-amber-500">✓</div>
            )}
          </button>
        ))}
      </div>

      <div className="flex gap-3">
        <Button variant="ghost" onClick={onPrev}>
          Back
        </Button>
        <Button
          onClick={onNext}
          className="bg-amber-500 hover:bg-amber-600 text-black font-semibold px-8"
        >
          Continue
        </Button>
      </div>
    </div>
  );
}

function PreferencesStep({
  onNext,
  onPrev,
}: {
  onNext: () => void;
  onPrev: () => void;
}) {
  const { userConfig, setPreference } = useOnboardingStore();

  const toggles = [
    {
      key: "voiceEnabled" as const,
      label: "Voice Input",
      description: "Enable microphone for voice commands",
      icon: "🎤",
    },
    {
      key: "soundEffects" as const,
      label: "Sound Effects",
      description: "Play sounds for notifications and actions",
      icon: "🔊",
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center text-center">
      <h2 className="text-2xl font-bold text-foreground mb-2">Preferences</h2>
      <p className="text-muted-foreground mb-8 max-w-md">
        Customize your experience. You can change these later in settings.
      </p>

      <div className="flex flex-col gap-3 w-full max-w-md mb-8">
        {toggles.map((toggle) => (
          <button
            key={toggle.key}
            onClick={() =>
              setPreference(toggle.key, !userConfig.preferences[toggle.key])
            }
            className={cn(
              "flex items-center gap-4 p-4 rounded-lg border transition-all text-left",
              userConfig.preferences[toggle.key]
                ? "border-amber-500 bg-amber-500/10"
                : "border-zinc-700 bg-zinc-900"
            )}
          >
            <span className="text-2xl">{toggle.icon}</span>
            <div className="flex-1">
              <div className="font-semibold text-foreground">{toggle.label}</div>
              <div className="text-sm text-muted-foreground">
                {toggle.description}
              </div>
            </div>
            <div
              className={cn(
                "w-12 h-6 rounded-full transition-colors relative",
                userConfig.preferences[toggle.key]
                  ? "bg-amber-500"
                  : "bg-zinc-700"
              )}
            >
              <div
                className={cn(
                  "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                  userConfig.preferences[toggle.key]
                    ? "translate-x-7"
                    : "translate-x-1"
                )}
              />
            </div>
          </button>
        ))}
      </div>

      <div className="flex gap-3">
        <Button variant="ghost" onClick={onPrev}>
          Back
        </Button>
        <Button
          onClick={onNext}
          className="bg-amber-500 hover:bg-amber-600 text-black font-semibold px-8"
        >
          Continue
        </Button>
      </div>
    </div>
  );
}

function CompleteStep({ onComplete }: { onComplete: () => void }) {
  const { userConfig } = useOnboardingStore();

  return (
    <div className="flex flex-col items-center justify-center text-center">
      <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center mb-6">
        <span className="text-4xl">✨</span>
      </div>
      <h2 className="text-2xl font-bold text-foreground mb-2">You're all set!</h2>
      <p className="text-muted-foreground mb-8 max-w-md">
        {userConfig.name
          ? `Welcome, ${userConfig.name}! `
          : "Welcome! "}
        Emperor is ready to assist you.
      </p>

      <div className="bg-zinc-900 rounded-lg p-4 mb-8 max-w-md w-full text-left">
        <h3 className="font-semibold text-foreground mb-3">Quick Tips:</h3>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li className="flex items-center gap-2">
            <span className="text-amber-500">•</span>
            Press <kbd className="px-1.5 py-0.5 bg-zinc-800 rounded text-xs">Cmd+Enter</kbd> to send messages
          </li>
          <li className="flex items-center gap-2">
            <span className="text-amber-500">•</span>
            Hold <kbd className="px-1.5 py-0.5 bg-zinc-800 rounded text-xs">Space</kbd> for push-to-talk
          </li>
          <li className="flex items-center gap-2">
            <span className="text-amber-500">•</span>
            Press <kbd className="px-1.5 py-0.5 bg-zinc-800 rounded text-xs">Cmd+K</kbd> for quick commands
          </li>
        </ul>
      </div>

      <Button
        onClick={onComplete}
        className="bg-amber-500 hover:bg-amber-600 text-black font-semibold px-8"
      >
        Start Using Emperor
      </Button>
    </div>
  );
}

// Step indicator
function StepIndicator({
  steps,
  currentStep,
}: {
  steps: number;
  currentStep: number;
}) {
  return (
    <div className="flex gap-2 justify-center mb-8">
      {Array.from({ length: steps }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "w-2 h-2 rounded-full transition-colors",
            i === currentStep ? "bg-amber-500" : "bg-zinc-700"
          )}
        />
      ))}
    </div>
  );
}

// Main onboarding component
export function Onboarding() {
  const { currentStep, nextStep, prevStep, completeOnboarding } =
    useOnboardingStore();

  const steps = [
    <WelcomeStep key="welcome" onNext={nextStep} />,
    <NameStep key="name" onNext={nextStep} onPrev={prevStep} />,
    <PermissionStep key="permission" onNext={nextStep} onPrev={prevStep} />,
    <PreferencesStep key="preferences" onNext={nextStep} onPrev={prevStep} />,
    <CompleteStep key="complete" onComplete={completeOnboarding} />,
  ];

  return (
    <div className="fixed inset-0 bg-background flex items-center justify-center z-50">
      <div className="w-full max-w-lg px-6">
        <StepIndicator steps={steps.length} currentStep={currentStep} />

        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {steps[currentStep]}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
