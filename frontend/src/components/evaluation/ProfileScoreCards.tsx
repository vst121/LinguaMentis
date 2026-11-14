"use client";

import { ReactNode } from "react";
import { Card } from "@/components/ui/Card";
import { ScoreRadarChart } from "@/components/evaluation/ScoreRadarChart";
import { DimensionScore } from "@/types/learning";

const DIMENSION_LABELS: Record<string, string> = {
  hat_adherence: "Perspektiven-Fokus",
  relevance: "Relevanz",
  reasoning: "Argumentation",
  depth: "Tiefe",
  specificity: "Spezifität",
  grammar: "Grammatik",
  vocabulary: "Wortschatz",
  sentence_structure: "Satzbau",
  naturalness: "Natürlichkeit",
  level_appropriateness: "Niveau-Passung",
};

export function formatDimensionName(name: string): string {
  return DIMENSION_LABELS[name] ?? name.replaceAll("_", " ");
}

interface ProfileMetricsSectionProps {
  primaryCardLabel: string;
  primaryCardValue: string | number;
  thinkingOverall: number | null | undefined;
  germanOverall: number | null | undefined;
  thinkingDimensions: DimensionScore[];
  germanDimensions: DimensionScore[];
  strongestThinking?: string | null;
  weakestThinking?: string | null;
  strongestGerman?: string | null;
  weakestGerman?: string | null;
  thinkingExtra?: ReactNode;
  germanExtra?: ReactNode;
}

export function ProfileMetricsSection({
  primaryCardLabel,
  primaryCardValue,
  thinkingOverall,
  germanOverall,
  thinkingDimensions,
  germanDimensions,
  strongestThinking,
  weakestThinking,
  strongestGerman,
  weakestGerman,
  thinkingExtra,
  germanExtra,
}: ProfileMetricsSectionProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs shadow-sm sm:text-sm dark:border-slate-600 dark:bg-slate-700/90">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500 dark:text-slate-300">{primaryCardLabel}:</span>
          <strong className="font-bold text-slate-900 dark:text-slate-50">{primaryCardValue}</strong>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500 dark:text-slate-300">Denken:</span>
          <strong className="font-bold text-blue-700 dark:text-blue-300">
            {thinkingOverall !== null && thinkingOverall !== undefined
              ? thinkingOverall
              : "—"}
          </strong>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500 dark:text-slate-300">Deutsch:</span>
          <strong className="font-bold text-emerald-700 dark:text-emerald-300">
            {germanOverall !== null && germanOverall !== undefined
              ? germanOverall
              : "—"}
          </strong>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 md:items-start">
        <Card
          title="Denkfähigkeiten"
          description={
            strongestThinking && weakestThinking
              ? `Stärke: ${formatDimensionName(strongestThinking)} · Fokus: ${formatDimensionName(weakestThinking)}`
              : "Deine Werte erscheinen nach der ersten Auswertung."
          }
          bodyClassName="space-y-3"
        >
          {thinkingDimensions.length > 0 && (
            <ScoreRadarChart
              accent="blue"
              ariaLabel="Radar-Diagramm Denkfähigkeiten"
              dimensions={thinkingDimensions.map((d) => ({
                key: d.name,
                label: formatDimensionName(d.name),
                score: d.score,
              }))}
            />
          )}
          {thinkingExtra}
        </Card>

        <Card
          title="Deutsch"
          description={
            strongestGerman && weakestGerman
              ? `Stärke: ${formatDimensionName(strongestGerman)} · Fokus: ${formatDimensionName(weakestGerman)}`
              : "Deine Werte erscheinen nach der ersten Auswertung."
          }
          bodyClassName="space-y-3"
        >
          {germanDimensions.length > 0 && (
            <ScoreRadarChart
              accent="emerald"
              ariaLabel="Radar-Diagramm Deutsch"
              dimensions={germanDimensions.map((d) => ({
                key: d.name,
                label: formatDimensionName(d.name),
                score: d.score,
              }))}
            />
          )}
          {germanExtra}
        </Card>
      </div>
    </div>
  );
}
