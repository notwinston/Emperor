import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          // Base styles
          "flex h-9 w-full rounded-md px-3 py-1 text-sm shadow-sm",
          // Background and border
          "bg-black-secondary border border-black-elevated",
          // Text and placeholder colors
          "text-gold-light placeholder:text-gold-muted",
          // Transitions
          "transition-all duration-200 ease-out",
          // Focus states - premium gold ring
          "focus-visible:outline-none focus-visible:border-gold-primary focus-visible:ring-2 focus-visible:ring-gold-primary/20 focus-visible:shadow-[0_0_15px_rgba(212,175,55,0.15)]",
          // Hover state
          "hover:border-gold-dark/50",
          // File input styling
          "file:border-0 file:bg-gold-primary/10 file:text-gold-text file:text-sm file:font-medium file:mr-3 file:px-3 file:py-1 file:rounded",
          // Disabled state
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-black-primary disabled:border-black-tertiary",
          // Selection styling
          "selection:bg-gold-primary/30 selection:text-gold-light",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
