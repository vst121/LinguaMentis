"use client";

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface CardProps {
  className?: string;
  title?: string;
  description?: string;
  footer?: ReactNode;
  children?: ReactNode;
}

export function Card({ className, title, description, footer, children }: CardProps) {
  return (
    <div className={cn("bg-white rounded-xl border border-gray-200 shadow-sm", className)}>
      {(title || description) && (
        <div className="px-5 pt-4 pb-0">
          {title && <h3 className="text-base font-semibold text-gray-900">{title}</h3>}
          {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
        </div>
      )}
      {children && <div className="p-5">{children}</div>}
      {footer && <div className="px-5 py-3 border-t border-gray-100 bg-gray-50 rounded-b-xl">{footer}</div>}
    </div>
  );
}
