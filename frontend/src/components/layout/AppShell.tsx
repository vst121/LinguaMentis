"use client";

import Link from "next/link";
import { Brain, Compass, History, Sparkles } from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/", label: "Start", icon: Compass },
  { href: "/mindquests", label: "MindQuests", icon: Brain },
  { href: "/learning", label: "Lernprofil", icon: Sparkles },
  { href: "/history", label: "Verlauf", icon: History },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="flex min-h-dvh flex-col bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 shrink-0 border-b border-slate-200/80 bg-slate-50/90 backdrop-blur">
        <div className="mx-auto flex h-10 max-w-[1600px] items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-1.5 text-sm font-semibold tracking-tight">
            <span className="grid h-6 w-6 place-items-center rounded-md bg-slate-900 text-white">
              <Brain size={14} />
            </span>
            LinguaMentis
          </Link>
          <nav className="flex items-center gap-1">
            {navigation.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition",
                  pathname === href || (href !== "/" && pathname.startsWith(href))
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-200",
                )}
              >
                <Icon size={14} />
                <span className="hidden sm:block">{label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col px-4 py-2 sm:px-6">
        {children}
      </main>
    </div>
  );
}
