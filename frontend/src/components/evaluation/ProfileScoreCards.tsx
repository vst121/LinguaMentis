"use client";

import { ReactNode } from "react";
import { Card } from "@/components/ui/Card";
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

export function ScoreBar({
  label,
  value,
  barClassName = "bg-blue-600",
}: {
  label: string;
  value: number;
  barClassName?: string;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span>
        <strong>{value} / 100</strong>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${barClassName}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
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
    <div className="flex flex-col gap-5 md:flex-1 md:min-h-0">
      <div className="grid shrink-0 gap-4 md:grid-cols-3">
        <Card bodyClassName="p-4 md:p-5">
          <p className="text-sm text-slate-500">{primaryCardLabel}</p>
          <p className="mt-1.5 text-2xl font-bold md:text-3xl">
            {primaryCardValue}
          </p>
        </Card>
        <Card bodyClassName="p-4 md:p-5">
          <p className="text-sm text-slate-500">Denken</p>
          <p className="mt-1.5 text-2xl font-bold md:text-3xl">
            {thinkingOverall !== null && thinkingOverall !== undefined ? (
              <>
                {thinkingOverall}{" "}
                <span className="text-base font-medium text-slate-400">/ 100</span>
              </>
            ) : (
              "—"
            )}
          </p>
        </Card>
        <Card bodyClassName="p-4 md:p-5">
          <p className="text-sm text-slate-500">Deutsch</p>
          <p className="mt-1.5 text-2xl font-bold md:text-3xl">
            {germanOverall !== null && germanOverall !== undefined ? (
              <>
                {germanOverall}{" "}
                <span className="text-base font-medium text-slate-400">/ 100</span>
              </>
            ) : (
              "—"
            )}
          </p>
        </Card>
      </div>

      <div className="grid gap-5 md:flex-1 md:min-h-0 md:grid-cols-2">
        <Card
          title="Denkfähigkeiten"
          description={
            strongestThinking && weakestThinking
              ? `Stärke: ${formatDimensionName(strongestThinking)} · Fokus: ${formatDimensionName(weakestThinking)}`
              : "Deine Werte erscheinen nach der ersten Auswertung."
          }
          className="flex flex-col md:h-full md:min-h-0"
          bodyClassName="flex-1 space-y-4 md:overflow-y-auto"
        >
          {thinkingDimensions.length > 0 && (
            <div className="space-y-3.5">
              {thinkingDimensions.map((d) => (
                <ScoreBar
                  key={d.name}
                  label={formatDimensionName(d.name)}
                  value={d.score}
                  barClassName="bg-blue-600"
                />
              ))}
            </div>
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
          className="flex flex-col md:h-full md:min-h-0"
          bodyClassName="flex-1 space-y-4 md:overflow-y-auto"
        >
          {germanDimensions.length > 0 && (
            <div className="space-y-3.5">
              {germanDimensions.map((d) => (
                <ScoreBar
                  key={d.name}
                  label={formatDimensionName(d.name)}
                  value={d.score}
                  barClassName="bg-emerald-600"
                />
              ))}
            </div>
          )}
          {germanExtra}
        </Card>
      </div>
    </div>
  );
}
