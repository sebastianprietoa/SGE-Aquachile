import * as React from "react";

import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: "default" | "success" | "warning" | "destructive" | "secondary" }) {
  const styles: Record<NonNullable<typeof variant>, string> = {
    default: "bg-cyan-400/15 text-cyan-200 border-cyan-400/20",
    success: "bg-emerald-400/15 text-emerald-200 border-emerald-400/20",
    warning: "bg-amber-400/15 text-amber-200 border-amber-400/20",
    destructive: "bg-rose-400/15 text-rose-200 border-rose-400/20",
    secondary: "bg-white/10 text-slate-200 border-white/10",
  };

  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium", styles[variant], className)} {...props} />;
}

