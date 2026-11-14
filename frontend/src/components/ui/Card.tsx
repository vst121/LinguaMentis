"use client";

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface CardProps {
  className?: string;
  bodyClassName?: string;
  title?: string;
  description?: string;
  footer?: ReactNode;
  children?: ReactNode;
}

export function Card({
  className,
  bodyClassName,
  title,
  description,
  footer,
  children,
}: CardProps) {
  return (
    <div className={cn("bg-white rounded-xl border border-gray-200 shadow-sm", className)}>
      {(title || description) && (
        <div className="shrink-0 px-4 pt-3 pb-0">
          {title && <h3 className="text-sm font-semibold text-gray-900 md:text-base">{title}</h3>}
          {description && <p className="mt-0.5 text-xs text-gray-500 md:text-sm">{description}</p>}
        </div>
      )}
      {children && <div className={cn("p-4", bodyClassName)}>{children}</div>}
      {footer && (
        <div className="shrink-0 px-4 py-2.5 border-t border-gray-100 bg-gray-50 rounded-b-xl">
          {footer}
        </div>
      )}
    </div>
  );
}
