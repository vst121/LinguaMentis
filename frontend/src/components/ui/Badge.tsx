"use client";

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "info";

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  default: "bg-gray-100 text-gray-700 dark:bg-slate-600 dark:text-slate-100",
  success: "bg-green-100 text-green-700 dark:bg-emerald-900/60 dark:text-emerald-200",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-200",
  danger: "bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200",
  info: "bg-blue-100 text-blue-700 dark:bg-indigo-900/60 dark:text-indigo-200",
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        VARIANT_CLASSES[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
