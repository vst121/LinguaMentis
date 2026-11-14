"use client";

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface CardProps {
  className?: string;
  bodyClassName?: string;
  title?: string;
  description?: string;
  headerAction?: ReactNode;
  footer?: ReactNode;
  children?: ReactNode;
}

export function Card({
  className,
  bodyClassName,
  title,
  description,
  headerAction,
  footer,
  children,
}: CardProps) {
  return (
<<<<<<< HEAD
    <div className={cn("bg-white rounded-xl border border-gray-200 shadow-sm", className)}>
      {(title || description || headerAction) && (
        <div className="shrink-0 px-5 pt-4 pb-0 flex items-start justify-between gap-3">
          <div>
            {title && <h3 className="text-base font-semibold text-gray-900">{title}</h3>}
            {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
          </div>
          {headerAction && <div className="shrink-0">{headerAction}</div>}
=======
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900",
        className,
      )}
    >
      {(title || description) && (
        <div className="shrink-0 px-4 pt-3 pb-0">
          {title && (
            <h3 className="text-sm font-semibold text-gray-900 md:text-base dark:text-slate-100">
              {title}
            </h3>
          )}
          {description && (
            <p className="mt-0.5 text-xs text-gray-500 md:text-sm dark:text-slate-400">
              {description}
            </p>
          )}
>>>>>>> feature_propositions
        </div>
      )}
      {children && <div className={cn("p-4", bodyClassName)}>{children}</div>}
      {footer && (
        <div className="shrink-0 rounded-b-xl border-t border-gray-100 bg-gray-50 px-4 py-2.5 dark:border-slate-800 dark:bg-slate-900/80">
          {footer}
        </div>
      )}
    </div>
  );
}
