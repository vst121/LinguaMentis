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
    <div className={cn("bg-white rounded-xl border border-gray-200 shadow-sm", className)}>
      {(title || description || headerAction) && (
        <div className="shrink-0 px-5 pt-4 pb-0 flex items-start justify-between gap-3">
          <div>
            {title && <h3 className="text-base font-semibold text-gray-900">{title}</h3>}
            {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
          </div>
          {headerAction && <div className="shrink-0">{headerAction}</div>}
        </div>
      )}
      {children && <div className={cn("p-5", bodyClassName)}>{children}</div>}
      {footer && (
        <div className="shrink-0 px-5 py-3 border-t border-gray-100 bg-gray-50 rounded-b-xl">
          {footer}
        </div>
      )}
    </div>
  );
}
