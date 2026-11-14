"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { ProfileMetricsSection } from "@/components/evaluation/ProfileScoreCards";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { getFinalReflection } from "@/services/api/mindquests";
import { FinalReflection } from "@/types/evaluation";

export default function ReflectionPage() {
  const { id } = useParams<{ id: string }>();
  const [r, setR] = useState<FinalReflection | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const cacheKey = `linguamentis:reflection:${id}`;

    const load = async () => {
      try {
        const cached = sessionStorage.getItem(cacheKey);
        if (cached) {
          const parsed = await Promise.resolve(
            JSON.parse(cached) as FinalReflection,
          );
          sessionStorage.removeItem(cacheKey);
          if (active) setR(parsed);
          return;
        }
      } catch {
        // Ignore storage errors and fetch from API
      }

      try {
        const data = await getFinalReflection(id);
        if (active) setR(data);
      } catch {
        if (active) setError("Die Reflexion ist noch nicht verfügbar.");
      }
    };

    void load();
    return () => {
      active = false;
    };
  }, [id]);

  if (error) {
    return (
      <AppShell>
        <p className="text-rose-700">{error}</p>
      </AppShell>
    );
  }

  if (!r) {
    return (
      <AppShell>
        <div className="flex flex-col gap-5 md:flex-1 md:min-h-0">
          <div className="h-16 w-2/3 animate-pulse rounded-xl bg-slate-200/70" />
          <div className="grid gap-4 md:grid-cols-3">
            {[0, 1, 2].map((idx) => (
              <Card key={idx} className="h-24 animate-pulse bg-slate-100/70" />
            ))}
          </div>
        </div>
      </AppShell>
    );
  }

  const hatsLabel =
    r.hats_completed !== undefined && r.hats_total !== undefined
      ? `${r.hats_completed} / ${r.hats_total}`
      : "Abgeschlossen";

  return (
    <AppShell>
      <div className="flex flex-col gap-5 md:flex-1 md:min-h-0">
        <div className="flex shrink-0 flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div className="min-w-0">
            <p className="text-xs font-semibold text-blue-700 md:text-sm">
              ABSCHLUSS{r.topic ? ` · ${r.topic}` : ""}
              {r.target_level ? ` (${r.target_level})` : ""}
            </p>
            <h1 className="mt-1 text-2xl font-bold md:text-3xl">
              Deine MindQuest-Reflexion
            </h1>
            <p className="mt-1.5 max-w-3xl text-sm text-slate-600 md:text-base">
              {r.closing_message}
            </p>
          </div>
          <Link href="/mindquests" className="shrink-0">
            <Button>Neue MindQuest starten</Button>
          </Link>
        </div>

        <ProfileMetricsSection
          primaryCardLabel="Abgeschlossene Perspektiven"
          primaryCardValue={hatsLabel}
          thinkingOverall={r.thinking_overall}
          germanOverall={r.german_overall}
          thinkingDimensions={r.thinking_dimensions ?? []}
          germanDimensions={r.german_dimensions ?? []}
          strongestThinking={r.strongest_thinking_dimension}
          weakestThinking={r.weakest_thinking_dimension}
          strongestGerman={r.strongest_german_dimension}
          weakestGerman={r.weakest_german_dimension}
          thinkingExtra={
            <div className="border-t border-slate-100 pt-4">
              <p className="rounded-lg bg-blue-50/70 p-3.5 text-sm leading-6 text-slate-700">
                {r.thinking_summary}
              </p>
              {(r.thinking_section.recommendations?.length ?? 0) > 0 && (
                <>
                  <h4 className="mt-4 text-sm font-semibold text-slate-900">
                    Nächster Schritt
                  </h4>
                  <ul className="mt-1.5 space-y-1.5 text-sm text-slate-600">
                    {r.thinking_section.recommendations?.map((x) => (
                      <li key={x}>• {x}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          }
          germanExtra={
            <div className="border-t border-slate-100 pt-4">
              <p className="rounded-lg bg-emerald-50/70 p-3.5 text-sm leading-6 text-slate-700">
                {r.german_summary}
              </p>
              {(r.german_section.important_corrections?.length ?? 0) > 0 && (
                <div className="mt-4 space-y-2">
                  <h4 className="text-sm font-semibold text-slate-900">
                    Wichtige Korrekturen
                  </h4>
                  {r.german_section.important_corrections?.map((c, idx) => (
                    <div
                      key={idx}
                      className="border-l-2 border-emerald-500 pl-3 text-xs leading-5"
                    >
                      <s className="text-slate-500">{c.original}</s>{" "}
                      <span className="font-medium text-slate-900">
                        → {c.corrected}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {(r.german_section.level_recommendations?.length ?? 0) > 0 && (
                <>
                  <h4 className="mt-4 text-sm font-semibold text-slate-900">
                    Nächster Schritt
                  </h4>
                  <ul className="mt-1.5 space-y-1.5 text-sm text-slate-600">
                    {r.german_section.level_recommendations?.map((x) => (
                      <li key={x}>• {x}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          }
        />
      </div>
    </AppShell>
  );
}
