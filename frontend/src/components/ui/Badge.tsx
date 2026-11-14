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
  default: "bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200",
  success: "bg-green-100 text-green-700 dark:bg-emerald-950/80 dark:text-emerald-300",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-950/80 dark:text-amber-300",
  danger: "bg-red-100 text-red-700 dark:bg-rose-950/80 dark:text-rose-300",
  info: "bg-blue-100 text-blue-700 dark:bg-blue-950/80 dark:text-blue-300",
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
