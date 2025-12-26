import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-all duration-200 ease-out focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        // Primary: Gold gradient with dark text
        default:
          "bg-gradient-to-br from-gold-primary via-gold-accent to-gold-dark text-black-primary shadow-md hover:shadow-lg hover:shadow-gold-primary/25 hover:from-gold-accent hover:via-gold-primary hover:to-gold-dark active:scale-[0.98]",
        // Destructive: Red with gold accent
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90 hover:shadow-md",
        // Outline: Gold border with transparent background
        outline:
          "border border-gold-primary bg-transparent text-gold-primary shadow-sm hover:bg-gold-primary/10 hover:shadow-gold-primary/20 hover:shadow-md",
        // Secondary: Dark background with gold text
        secondary:
          "bg-black-tertiary text-gold-text border border-black-elevated shadow-sm hover:bg-black-elevated hover:border-gold-dark hover:shadow-gold-primary/10",
        // Ghost: Subtle gold hover effect
        ghost:
          "text-gold-text hover:bg-gold-primary/10 hover:text-gold-light",
        // Link: Gold underline
        link:
          "text-gold-primary underline-offset-4 hover:underline hover:text-gold-accent",
        // Premium: Gold with intense glow effect
        premium:
          "bg-gradient-to-br from-gold-primary via-gold-accent to-gold-dark text-black-primary shadow-lg shadow-gold-primary/30 hover:shadow-xl hover:shadow-gold-primary/40 hover:from-gold-accent hover:via-gold-light hover:to-gold-primary active:scale-[0.98]",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
