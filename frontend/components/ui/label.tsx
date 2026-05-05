import * as React from "react";

import { cn } from "@/lib/utils";

export const Label = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => <label ref={ref} className={cn("mb-2 block text-sm font-medium text-slate-200", className)} {...props} />,
);
Label.displayName = "Label";

