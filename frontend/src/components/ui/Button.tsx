import { forwardRef } from "react";
import { cn } from "@/utils/cn";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "outline" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "default",
      size = "md",
      isLoading,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
          {
            "bg-primary text-primary-foreground hover:bg-primary/90":
              variant === "default",
            "bg-secondary text-secondary-foreground hover:bg-secondary/80":
              variant === "secondary",
            "border border-input bg-background hover:bg-accent":
              variant === "outline",
            "hover:bg-accent hover:text-accent-foreground": variant === "ghost",
            "bg-destructive text-white hover:bg-destructive/90":
              variant === "destructive",
            "h-8 px-3 text-xs": size === "sm",
            "h-9 px-4 text-sm": size === "md",
            "h-10 px-6 text-sm": size === "lg",
          },
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <span className="mr-2 h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
            Loading...
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);
Button.displayName = "Button";
