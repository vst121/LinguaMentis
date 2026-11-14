"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { PropositionHighlight, ResponseProposition } from "@/types/evaluation";

export interface HighlightSegment {
  text: string;
  highlight?: PropositionHighlight;
  number?: number;
}

const CATEGORY_STYLES: Record<
  string,
  { label: string; markClass: string; pillClass: string }
> = {
  vocabulary: {
    label: "Wortschatz",
    markClass: "bg-indigo-100 text-indigo-950 ring-1 ring-indigo-300/80",
    pillClass: "bg-indigo-100 text-indigo-800",
  },
  syntax: {
    label: "Satzbau",
    markClass: "bg-violet-100 text-violet-950 ring-1 ring-violet-300/80",
    pillClass: "bg-violet-100 text-violet-800",
  },
  idiom: {
    label: "Redemittel",
    markClass: "bg-emerald-100 text-emerald-950 ring-1 ring-emerald-300/80",
    pillClass: "bg-emerald-100 text-emerald-800",
  },
  precision: {
    label: "Präzision",
    markClass: "bg-amber-100 text-amber-950 ring-1 ring-amber-300/80",
    pillClass: "bg-amber-100 text-amber-800",
  },
  connector: {
    label: "Konnektor",
    markClass: "bg-sky-100 text-sky-950 ring-1 ring-sky-300/80",
    pillClass: "bg-sky-100 text-sky-800",
  },
};

const DEFAULT_STYLE = {
  label: "Stil",
  markClass: "bg-amber-100 text-amber-950 ring-1 ring-amber-300/80",
  pillClass: "bg-amber-100 text-amber-800",
};

export function getHighlightStyle(category: string) {
  return CATEGORY_STYLES[category] ?? DEFAULT_STYLE;
}

/**
 * Splits `text` into plain and highlighted segments using longest-first,
 * non-overlapping substring matching so inline highlights never corrupt text.
 */
export function buildHighlightedSegments(
  text: string,
  highlights: PropositionHighlight[],
): HighlightSegment[] {
  if (!text || highlights.length === 0) {
    return text ? [{ text }] : [];
  }

  interface CandidateMatch {
    start: number;
    end: number;
    highlight: PropositionHighlight;
    number: number;
  }

  const lowerText = text.toLowerCase();
  const candidates: CandidateMatch[] = [];

  highlights.forEach((h, idx) => {
    const phrase = h.upgraded_phrase.trim();
    if (!phrase) return;

    let start = text.indexOf(phrase);
    if (start === -1) {
      start = lowerText.indexOf(phrase.toLowerCase());
    }
    if (start !== -1) {
      candidates.push({
        start,
        end: start + phrase.length,
        highlight: h,
        number: idx + 1,
      });
    }
  });

  candidates.sort((a, b) => a.start - b.start || b.end - a.end);

  const selected: CandidateMatch[] = [];
  let cursor = 0;
  for (const match of candidates) {
    if (match.start >= cursor) {
      selected.push(match);
      cursor = match.end;
    }
  }

  const segments: HighlightSegment[] = [];
  let pos = 0;
  for (const match of selected) {
    if (match.start > pos) {
      segments.push({ text: text.slice(pos, match.start) });
    }
    segments.push({
      text: text.slice(match.start, match.end),
      highlight: match.highlight,
      number: match.number,
    });
    pos = match.end;
  }
  if (pos < text.length) {
    segments.push({ text: text.slice(pos) });
  }

  return segments;
}

export function ResponsePropositionCard({
  proposition,
  originalResponse,
}: {
  proposition: ResponseProposition;
  originalResponse?: string;
}) {
  const [activeNumber, setActiveNumber] = useState<number | null>(null);
  const segments = buildHighlightedSegments(
    proposition.improved_response,
    proposition.highlights,
  );

  return (
    <Card
      title="Sprach-Upgrade: Elaborierte Antwort"
      description="Deine eigene Idee auf höherem Niveau — markierte Stellen zeigen verfeinerte Wörter, Redemittel und Satzstrukturen."
      className="md:col-span-2"
    >
      <div className="space-y-4">
        {originalResponse && (
          <div className="rounded-lg bg-slate-50 px-3.5 py-2.5 text-xs leading-5 text-slate-600 dark:bg-slate-800/70 dark:text-slate-300">
            <span className="font-semibold text-slate-700 dark:text-slate-200">Deine Antwort: </span>
            {originalResponse}
          </div>
        )}

        <div
          className="rounded-lg border border-indigo-200/80 bg-indigo-50/40 p-3.5 text-sm leading-7 text-slate-900 dark:border-indigo-800/60 dark:bg-indigo-950/40 dark:text-slate-100"
          data-testid="proposition-improved-text"
        >
          {segments.map((seg, i) => {
            if (!seg.highlight || !seg.number) {
              return <span key={i}>{seg.text}</span>;
            }
            const style = getHighlightStyle(seg.highlight.category);
            const isActive = activeNumber === seg.number;
            return (
              <mark
                key={i}
                title={seg.highlight.explanation}
                onMouseEnter={() => setActiveNumber(seg.number!)}
                onMouseLeave={() => setActiveNumber(null)}
                onClick={() =>
                  setActiveNumber((prev) => (prev === seg.number ? null : seg.number!))
                }
                className={`cursor-pointer rounded px-1 py-0.5 font-medium transition ${style.markClass} ${
                  isActive ? "ring-2 ring-slate-900/40" : ""
                }`}
              >
                {seg.text}
                <sup className="ml-0.5 text-[10px] font-bold opacity-75">
                  {seg.number}
                </sup>
              </mark>
            );
          })}
        </div>

        {proposition.highlights.length > 0 && (
          <div className="grid gap-2.5 lg:grid-cols-2">
            {proposition.highlights.map((h, i) => {
              const num = i + 1;
              const style = getHighlightStyle(h.category);
              const isActive = activeNumber === num;
              return (
                <div
                  key={i}
                  onMouseEnter={() => setActiveNumber(num)}
                  onMouseLeave={() => setActiveNumber(null)}
                  className={`rounded-lg border p-2.5 text-sm transition ${
                    isActive
                      ? "border-indigo-400 bg-indigo-50/50 dark:border-indigo-500 dark:bg-indigo-950/50"
                      : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-900 text-[11px] font-bold text-white dark:bg-slate-200 dark:text-slate-900">
                      {num}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${style.pillClass}`}
                    >
                      {style.label}
                    </span>
                  </div>
                  <div className="mt-1.5 leading-5">
                    {h.original_phrase && (
                      <>
                        <s className="text-slate-500 dark:text-slate-400">{h.original_phrase}</s>
                        <span className="mx-1.5 text-slate-400">→</span>
                      </>
                    )}
                    <strong className="font-semibold text-slate-900 dark:text-slate-100">
                      {h.upgraded_phrase}
                    </strong>
                  </div>
                  <p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-400">
                    {h.explanation}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
}
