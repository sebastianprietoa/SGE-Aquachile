import * as React from "react";

import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "ghost" | "destructive";
  size?: "default" | "sm" | "lg";
  asChild?: boolean;
}

const variantStyles: Record<NonNullable<ButtonProps["variant"]>, string> = {
  default: "bg-cyan-400 text-slate-950 hover:bg-cyan-300",
  secondary: "bg-white/10 text-white hover:bg-white/15 border border-white/10",
  ghost: "bg-transparent text-white hover:bg-white/8",
  destructive: "bg-rose-500 text-white hover:bg-rose-400",
};

const sizeStyles: Record<NonNullable<ButtonProps["size"]>, string> = {
  default: "h-10 px-4 py-2",
  sm: "h-8 px-3 text-sm",
  lg: "h-11 px-5 text-base",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, children, ...props }, ref) => {
    const styles = cn(
      "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 disabled:pointer-events-none disabled:opacity-50",
      variantStyles[variant],
      sizeStyles[size],
      className,
    );

    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<{ className?: string }>;
      return React.cloneElement(child, {
        className: cn(styles, child.props.className),
      });
    }

    return (
      <button
        ref={ref}
        className={styles}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";
