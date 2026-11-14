"use client";
import Link from "next/link";
import { ArrowRight, Brain, Languages, Lightbulb } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function HomePage() {
  return (
    <AppShell>
      <div className="flex flex-col gap-6 md:flex-1 md:min-h-0 md:justify-between md:gap-5">
        <section className="grid gap-6 md:flex-1 md:min-h-0 md:grid-cols-[1.15fr_.85fr] md:items-center lg:gap-10">
          <div className="flex flex-col justify-center">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[.18em] text-blue-700 md:text-sm">
              Denken · Deutsch · Fortschritt
            </p>
            <h1 className="max-w-2xl text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl md:text-[clamp(1.75rem,3.1vw,3.25rem)] md:leading-[1.12]">
              Denk klarer. Drück dich auf Deutsch sicherer aus.
            </h1>
            <p className="mt-4 max-w-xl text-base leading-7 text-slate-600 md:text-[clamp(.95rem,1.25vw,1.15rem)] md:leading-relaxed">
              Erkunde ein Thema mit den sechs Denkrollen und erhalte separates
              Feedback zu deiner Argumentation und deinem Deutsch.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/mindquests">
                <Button size="lg">
                  MindQuest starten <ArrowRight className="ml-2" size={18} />
                </Button>
              </Link>
              <Link href="/learning">
                <Button size="lg" variant="outline">
                  Mein Lernprofil
                </Button>
              </Link>
            </div>
          </div>
          <Card
            className="overflow-hidden border-slate-200 shadow-lg shadow-slate-200/50"
            bodyClassName="p-0"
          >
            <div className="bg-slate-900 p-5 text-white md:p-6 lg:p-7">
              <p className="text-xs text-slate-300 md:text-sm">Dein Denkraum</p>
              <p className="mt-1.5 text-xl font-semibold md:text-2xl">
                Eine Idee. Sechs Perspektiven.
              </p>
              <div className="mt-5 grid grid-cols-2 gap-2.5 sm:grid-cols-3 md:mt-6 md:gap-3">
                {[
                  "Fakten",
                  "Gefühle",
                  "Risiken",
                  "Chancen",
                  "Ideen",
                  "Überblick",
                ].map((item, i) => (
                  <div key={item} className="rounded-xl bg-white/10 p-2.5 text-sm md:p-3">
                    <span
                      className="mb-1.5 block h-2 w-2 rounded-full md:mb-2"
                      style={{
                        background: [
                          "#cbd5e1",
                          "#fb7185",
                          "#64748b",
                          "#fbbf24",
                          "#4ade80",
                          "#60a5fa",
                        ][i],
                      }}
                    />
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </section>
        <section className="grid shrink-0 gap-4 md:grid-cols-3">
          {[
            [
              Brain,
              "Denken schärfen",
              "Sechs klare Denkmodi helfen dir, eine Frage wirklich auszuloten.",
            ],
            [
              Languages,
              "Deutsch verbessern",
              "Erhalte präzises Feedback zu Grammatik, Wortschatz und Natürlichkeit.",
            ],
            [
              Lightbulb,
              "Fortschritt sehen",
              "Behalte deine Stärken, Entwicklung und nächsten Schritte im Blick.",
            ],
          ].map(([Icon, title, text]) => (
            <Card key={String(title)} bodyClassName="p-4 md:p-5">
              <div className="flex items-center gap-3 md:block">
                <Icon className="shrink-0 text-blue-700" size={20} />
                <h2 className="font-semibold md:mt-3">{String(title)}</h2>
              </div>
              <p className="mt-1.5 text-sm leading-5 text-slate-600 md:mt-2 md:leading-6">
                {String(text)}
              </p>
            </Card>
          ))}
        </section>
      </div>
    </AppShell>
  );
}
