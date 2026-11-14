"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import { ArrowRight, Send } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { ScoreRadarChart } from "@/components/evaluation/ScoreRadarChart";
import { ResponsePropositionCard } from "@/components/evaluation/ResponsePropositionCard";
import { HatIndicator } from "@/components/hats/HatIndicator";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  getMindQuest,
  startMindQuest,
  submitResponse,
  advanceMindQuest,
} from "@/services/api/mindquests";
import { HAT_METADATA, HatType } from "@/types/hat";
import {
  MindQuest,
  StartMindQuestResponse,
  SubmitResponseResponse,
  Turn,
} from "@/types/mindquest";

const inFlightStarts = new Map<string, Promise<StartMindQuestResponse>>();

function startMindQuestOnce(questId: string): Promise<StartMindQuestResponse> {
  const existing = inFlightStarts.get(questId);
  if (existing) return existing;
  const promise = startMindQuest(questId).finally(() => {
    inFlightStarts.delete(questId);
  });
  inFlightStarts.set(questId, promise);
  return promise;
}

const HAT_PROGRESS_COLORS: Record<
  HatType,
  { completed: string; active: string; upcoming: string }
> = {
  WHITE: {
    completed: "bg-white border border-slate-400",
    active: "bg-white border border-slate-600 ring-2 ring-slate-400/70",
    upcoming: "bg-white/60 border border-slate-300",
  },
  YELLOW: {
    completed: "bg-amber-400",
    active: "bg-amber-400 ring-2 ring-amber-500/60",
    upcoming: "bg-amber-200/80",
  },
  GREEN: {
    completed: "bg-emerald-500",
    active: "bg-emerald-500 ring-2 ring-emerald-500/60",
    upcoming: "bg-emerald-200/80",
  },
  RED: {
    completed: "bg-rose-500",
    active: "bg-rose-500 ring-2 ring-rose-500/60",
    upcoming: "bg-rose-200/80",
  },
  BLACK: {
    completed: "bg-slate-900",
    active: "bg-slate-900 ring-2 ring-slate-700/60",
    upcoming: "bg-slate-400/75",
  },
  BLUE: {
    completed: "bg-blue-600",
    active: "bg-blue-600 ring-2 ring-blue-500/60",
    upcoming: "bg-blue-200/80",
  },
};

export default function MindQuestPage() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const [quest, setQuest] = useState<MindQuest | null>(null),
    [turn, setTurn] = useState<Turn | null>(null),
    [draft, setDraft] = useState(""),
    [pendingResponse, setPendingResponse] = useState<string | null>(null),
    [feedback, setFeedback] = useState<SubmitResponseResponse | null>(null),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;

    async function loadQuest() {
      try {
        const q = await getMindQuest(id);
        if (cancelled) return;

        if (q.status === "COMPLETED") {
          router.replace(`/mindquests/${id}/reflection`);
          return;
        }

        const round = q.hat_rounds.find((r) => r.hat === q.current_hat);
        const existingTurn = round?.turns.at(-1) ?? null;

        if (!existingTurn) {
          const started = await startMindQuestOnce(id);
          if (cancelled) return;
          setQuest(started.mindquest);
          setTurn(started.initial_turn);
          if (
            started.mindquest.planned_hats.length -
              started.mindquest.completed_hats.length <=
            1
          ) {
            router.prefetch(`/mindquests/${id}/reflection`);
          }
          return;
        }

        setQuest(q);
        setTurn(existingTurn);
        if (q.planned_hats.length - q.completed_hats.length <= 1) {
          router.prefetch(`/mindquests/${id}/reflection`);
        }
      } catch {
        if (!cancelled) {
          setError("Diese MindQuest konnte nicht geladen werden.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadQuest();
    return () => {
      cancelled = true;
    };
  }, [id, router]);
  async function send() {
    if (busy || !draft.trim()) return;
    const submitted = draft.trim();
    setBusy(true);
    setError("");
    setPendingResponse(submitted);
    setDraft("");
    try {
      const res = await submitResponse(id, { response: submitted });
      setFeedback(res);
      setPendingResponse(null);
      if (
        res.round_should_complete &&
        quest &&
        quest.planned_hats.length - quest.completed_hats.length <= 1
      ) {
        router.prefetch(`/mindquests/${id}/reflection`);
      }
    } catch {
      setDraft(submitted);
      setPendingResponse(null);
      setError("Deine Antwort konnte nicht gesendet werden.");
    } finally {
      setBusy(false);
    }
  }
  function handleResponseSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void send();
  }
  function handleResponseKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Submit on Enter; allow newline only when Shift+Enter is pressed
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      void send();
    }
  }
  async function nextStep() {
    setError("");
    // Instant local transition when the backend already returned the next intra-hat challenge
    if (feedback && !feedback.round_should_complete) {
      if (feedback.next_challenge_question && turn) {
        setTurn({
          ...turn,
          turn_number: turn.turn_number + 1,
          challenge_question: feedback.next_challenge_question,
          challenge_instruction: feedback.next_challenge_instruction ?? "",
          user_response: null,
          responded_at: null,
        });
        setFeedback(null);
        return;
      }
      setBusy(true);
      try {
        const refreshed = await getMindQuest(id);
        setQuest(refreshed);
        const activeRound = refreshed.hat_rounds.find(
          (r) => r.hat === refreshed.current_hat,
        );
        setTurn(activeRound?.turns.at(-1) ?? null);
        setFeedback(null);
      } catch {
        setError("Nächster Schritt nicht möglich.");
      } finally {
        setBusy(false);
      }
      return;
    }

    setBusy(true);
    try {
      const result = await advanceMindQuest(id);
      if (result.is_completed) {
        if (result.final_reflection) {
          try {
            sessionStorage.setItem(
              `linguamentis:reflection:${id}`,
              JSON.stringify(result.final_reflection),
            );
          } catch {
            // Ignore storage errors and let reflection page fetch directly
          }
        }
        // Navigate straight to the final reflection without flashing an intermediate completion screen
        router.replace(`/mindquests/${id}/reflection`);
        return;
      }
      setQuest(result.mindquest);
      setFeedback(null);
      setTurn(result.initial_turn ?? null);
      setBusy(false);
    } catch {
      setError("Nächster Schritt nicht möglich.");
      setBusy(false);
    }
  }
  if (loading)
    return (
      <AppShell>
        <p className="text-slate-500">MindQuest wird geladen …</p>
      </AppShell>
    );
  if (!quest)
    return (
      <AppShell>
        <p className="text-rose-700">{error || "MindQuest nicht gefunden."}</p>
      </AppShell>
    );
  const currentHat = quest.current_hat || quest.planned_hats[0];
  const remainingHats = quest.planned_hats.filter(
    (h) => !quest.completed_hats.includes(h),
  );
  const isLastHat = remainingHats.length <= 1;
  return (
    <AppShell>
      <div className="flex flex-col gap-2.5">
        <div>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex min-w-0 items-center gap-2">
              <Link
                href="/mindquests"
                className="shrink-0 text-xs font-medium text-blue-700 hover:underline"
                title="Alle MindQuests"
              >
                ← Zurück
              </Link>
              <span className="text-slate-300">|</span>
              <h1 className="truncate text-sm font-bold sm:text-base">
                {quest.topic}
              </h1>
              <span className="shrink-0 rounded bg-slate-200/70 px-1.5 py-0.5 text-[11px] font-medium text-slate-700">
                {quest.target_level} · {quest.completed_hats.length}/
                {quest.planned_hats.length}
              </span>
            </div>
            {currentHat && <HatIndicator hat={currentHat} />}
          </div>
          <div className="mt-1.5 flex gap-1">
            {quest.planned_hats.map((h) => {
              const colors = HAT_PROGRESS_COLORS[h];
              const stateClass = quest.completed_hats.includes(h)
                ? colors.completed
                : h === currentHat
                  ? colors.active
                  : colors.upcoming;
              return (
                <div
                  key={h}
                  title={HAT_METADATA[h]?.nameGerman ?? h}
                  className={`h-1 flex-1 rounded-full transition-all ${stateClass}`}
                />
              );
            })}
          </div>
          {error && (
            <p className="mt-2 rounded-lg bg-rose-50 p-2 text-xs text-rose-700 sm:text-sm">
              {error}
            </p>
          )}
        </div>

        {quest.status === "COMPLETED" ? (
          <div className="flex items-center justify-center py-8">
            <Card
              title="MindQuest abgeschlossen"
              description="Alle geplanten Perspektiven wurden beendet."
              className="w-full max-w-xl"
            >
              <Link href={`/mindquests/${id}/reflection`}>
                <Button>
                  Abschlussreflexion ansehen <ArrowRight className="ml-2" size={16} />
                </Button>
              </Link>
            </Card>
          </div>
        ) : !turn ? (
          <p className="text-slate-500">Erste Perspektive wird vorbereitet …</p>
        ) : (
          <div
            className={`grid gap-4 md:items-start ${
              feedback
                ? "md:grid-cols-[.9fr_1.1fr]"
                : "md:grid-cols-[.9fr_1.1fr]"
            }`}
          >
            {/* Left column: Challenge prompt (and Feedback summary when evaluated) */}
            <div className="flex flex-col gap-3">
              <Card>
                <p className="text-xs font-semibold text-blue-700">
                  RUNDE {turn.turn_number} ·{" "}
                  {currentHat && <span>{currentHat}</span>}
                </p>
                <h2 className="mt-1.5 text-base font-semibold leading-6 md:text-lg md:leading-7">
                  {turn.challenge_question}
                </h2>
                <p className="mt-2.5 rounded-lg bg-slate-50 p-2.5 text-xs leading-5 text-slate-600 md:text-sm md:leading-6">
                  {turn.challenge_instruction}
                </p>
              </Card>

              {feedback && (
                <Card
                  title="Dein Feedback"
                  description={feedback.feedback.encouragement}
                  bodyClassName="flex flex-col gap-3"
                >
                  <div className="space-y-2.5">
                    <p className="rounded-lg bg-blue-50 p-3 text-sm leading-6 text-slate-700">
                      {feedback.feedback.thinking_feedback}
                    </p>
                    <p className="rounded-lg bg-emerald-50 p-3 text-sm leading-6 text-slate-700">
                      {feedback.feedback.german_feedback}
                    </p>
                  </div>
                  <div>
                    <Button onClick={nextStep} isLoading={busy}>
                      {feedback.round_should_complete
                        ? isLastHat
                          ? "Abschlussreflexion ansehen"
                          : "Nächste Perspektive"
                        : "Nächste Herausforderung"}
                      <ArrowRight className="ml-2" size={16} />
                    </Button>
                  </div>
                </Card>
              )}
            </div>

            {/* Right column: Response editor, pending state, or radar charts + proposition + corrections */}
            <div className="flex flex-col">
              {pendingResponse ? (
                <Card
                  title="Deine Antwort"
                  description="Denken und Deutsch werden gleichzeitig ausgewertet …"
                  bodyClassName="flex flex-col gap-3"
                >
                  <p className="rounded-lg bg-slate-50 p-3.5 text-sm leading-6 text-slate-700">
                    {pendingResponse}
                  </p>
                  <div className="flex items-center gap-2 text-sm text-blue-700">
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-blue-600" />
                    Auswertung läuft …
                  </div>
                </Card>
              ) : !feedback ? (
                <Card
                  title="Deine Antwort"
                  description="Formuliere deine Gedanken auf Deutsch. Qualität ist wichtiger als Länge."
                >
                  <form
                    onSubmit={handleResponseSubmit}
                    className="flex flex-col"
                  >
                    <textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={handleResponseKeyDown}
                      placeholder="Schreibe deine Antwort hier …"
                      className="min-h-56 w-full resize-y rounded-lg border border-slate-300 p-3 leading-7 outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                      <span>
                        {draft.trim().split(/\s+/).filter(Boolean).length} Wörter
                      </span>
                      <Button
                        type="submit"
                        disabled={!draft.trim()}
                        isLoading={busy}
                      >
                        <Send className="mr-2" size={16} />
                        Antwort auswerten
                      </Button>
                    </div>
                  </form>
                </Card>
              ) : (
                <div className="grid gap-3 md:grid-cols-2 md:auto-rows-max">
                  <Card title="Denken" bodyClassName="pt-3">
                    <div className="mb-2 flex items-baseline justify-between">
                      <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
                        Gesamt
                      </span>
                      <strong className="text-lg font-bold text-blue-700">
                        {feedback.thinking_evaluation.score} / 100
                      </strong>
                    </div>
                    <ScoreRadarChart
                      accent="blue"
                      ariaLabel="Radar-Diagramm Denken"
                      dimensions={[
                        {
                          key: "hat_adherence",
                          label: "Perspektiven-Fokus",
                          score: feedback.thinking_evaluation.hat_adherence,
                        },
                        {
                          key: "relevance",
                          label: "Relevanz",
                          score: feedback.thinking_evaluation.relevance,
                        },
                        {
                          key: "reasoning",
                          label: "Argumentation",
                          score: feedback.thinking_evaluation.reasoning,
                        },
                        {
                          key: "depth",
                          label: "Tiefe",
                          score: feedback.thinking_evaluation.depth,
                        },
                        {
                          key: "specificity",
                          label: "Spezifität",
                          score: feedback.thinking_evaluation.specificity,
                        },
                      ]}
                    />
                  </Card>
                  <Card title="Deutsch" bodyClassName="pt-3">
                    <div className="mb-2 flex items-baseline justify-between">
                      <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
                        Gesamt
                      </span>
                      <strong className="text-lg font-bold text-emerald-700">
                        {feedback.german_evaluation.score} / 100
                      </strong>
                    </div>
                    <ScoreRadarChart
                      accent="emerald"
                      ariaLabel="Radar-Diagramm Deutsch"
                      dimensions={[
                        {
                          key: "grammar",
                          label: "Grammatik",
                          score: feedback.german_evaluation.grammar,
                        },
                        {
                          key: "vocabulary",
                          label: "Wortschatz",
                          score: feedback.german_evaluation.vocabulary,
                        },
                        {
                          key: "sentence_structure",
                          label: "Satzbau",
                          score: feedback.german_evaluation.sentence_structure,
                        },
                        {
                          key: "naturalness",
                          label: "Natürlichkeit",
                          score: feedback.german_evaluation.naturalness,
                        },
                        {
                          key: "level_appropriateness",
                          label: "Niveau-Passung",
                          score: feedback.german_evaluation.level_appropriateness,
                        },
                      ]}
                    />
                  </Card>
                  {feedback.proposition && (
                    <ResponsePropositionCard
                      proposition={feedback.proposition}
                      originalResponse={feedback.turn.user_response ?? undefined}
                    />
                  )}
                  {feedback.german_evaluation.corrections.length > 0 && (
                    <Card title="Verbesserungen" className="md:col-span-2">
                      <div className="grid gap-3 lg:grid-cols-2">
                        {feedback.german_evaluation.corrections.map((c, i) => (
                          <div
                            key={i}
                            className="border-l-2 border-blue-400 pl-3 text-sm"
                          >
                            <s className="text-slate-500">{c.original}</s>
                            <p className="font-medium">{c.corrected}</p>
                            <p className="mt-1 text-slate-600">{c.explanation}</p>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
