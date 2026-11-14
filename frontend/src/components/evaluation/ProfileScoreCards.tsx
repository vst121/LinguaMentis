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
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 md:grid-cols-3">
        <Card bodyClassName="p-3 md:p-3.5">
          <p className="text-xs text-slate-500">{primaryCardLabel}</p>
          <p className="mt-1 text-xl font-bold md:text-2xl">
            {primaryCardValue}
          </p>
        </Card>
        <Card bodyClassName="p-3 md:p-3.5">
          <p className="text-xs text-slate-500">Denken</p>
          <p className="mt-1 text-xl font-bold md:text-2xl">
            {thinkingOverall !== null && thinkingOverall !== undefined ? (
              <>
                {thinkingOverall}{" "}
                <span className="text-sm font-medium text-slate-400">/ 100</span>
              </>
            ) : (
              "—"
            )}
          </p>
        </Card>
        <Card bodyClassName="p-3 md:p-3.5">
          <p className="text-xs text-slate-500">Deutsch</p>
          <p className="mt-1 text-xl font-bold md:text-2xl">
            {germanOverall !== null && germanOverall !== undefined ? (
              <>
                {germanOverall}{" "}
                <span className="text-sm font-medium text-slate-400">/ 100</span>
              </>
            ) : (
              "—"
            )}
          </p>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 md:items-start">
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
