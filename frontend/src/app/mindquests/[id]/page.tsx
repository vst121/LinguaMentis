"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  CircleDashed,
  Flame,
  Loader2,
  Lock,
  MessageSquareText,
  RotateCcw,
  Send,
  Volume2,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { ConversationView } from "@/components/conversation/ConversationView";
import { ScoreRadarChart } from "@/components/evaluation/ScoreRadarChart";
import { ResponsePropositionCard } from "@/components/evaluation/ResponsePropositionCard";
import { HatIndicator } from "@/components/hats/HatIndicator";
import {
  SpeechModeToggle,
  SpeechRecordingBanner,
} from "@/components/speech/SpeechInputControls";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useConversationSession } from "@/hooks/useConversationSession";
import { useSpeechToText } from "@/hooks/useSpeechToText";
import {
  getMindQuest,
  selectHat,
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

const ARGUE_HATS: HatType[] = ["WHITE", "YELLOW", "GREEN", "RED", "BLACK"];

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
    [elapsedSeconds, setElapsedSeconds] = useState(0),
    [error, setError] = useState(""),
    [experienceMode, setExperienceMode] = useState<"written" | "conversation">("written");
  useEffect(() => {
    if (!pendingResponse && !busy) {
      return;
    }
    const startedAt = Date.now();
    const timer = window.setInterval(() => {
      setElapsedSeconds(Math.max(1, Math.floor((Date.now() - startedAt) / 1000)));
    }, 1000);
    return () => {
      window.clearInterval(timer);
    };
  }, [pendingResponse, busy]);
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

        const isActiveHat = q.status === "HAT_ACTIVE";
        const round = isActiveHat
          ? q.hat_rounds.find((r) => r.hat === q.current_hat)
          : undefined;
        const existingTurn = round?.turns.at(-1) ?? null;

        if (q.mode === "ARGUE") {
          // Argue Mode waits for manual hat selection whenever no hat is active
          setQuest(q);
          setTurn(existingTurn);
          if (q.planned_hats.length - q.completed_hats.length <= 1) {
            router.prefetch(`/mindquests/${id}/reflection`);
          }
          return;
        }

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
  async function chooseHat(hat: HatType) {
    if (busy) return;
    setElapsedSeconds(0);
    setBusy(true);
    setError("");
    try {
      const result = await selectHat(id, hat);
      setQuest(result.mindquest);
      setTurn(result.initial_turn);
      setFeedback(null);
      setDraft("");
    } catch {
      setError("Hut konnte nicht ausgewählt werden.");
    } finally {
      setBusy(false);
    }
  }
  const appendTranscript = useCallback((spokenText: string) => {
    setDraft((prev) => {
      const trimmed = prev.trim();
      return trimmed ? `${trimmed} ${spokenText}` : spokenText;
    });
  }, []);

  const {
    mode: inputMode,
    isRecording,
    isTranscribing,
    interimText,
    elapsedSeconds: speechElapsedSeconds,
    audioLevels,
    speechError,
    startRecording,
    stopRecording,
  } = useSpeechToText(appendTranscript);

  const handleConversationQuestUpdate = useCallback(
    (updated: MindQuest, activeTurn: Turn | null) => {
      setQuest(updated);
      setTurn(activeTurn);
      setFeedback(null);
    },
    []
  );

  const handleConversationCompleted = useCallback(() => {
    router.replace(`/mindquests/${id}/reflection`);
  }, [id, router]);

  const conversation = useConversationSession({
    mindquestId: id,
    enabled: experienceMode === "conversation" && quest?.status !== "COMPLETED",
    onQuestUpdated: handleConversationQuestUpdate,
    onCompleted: handleConversationCompleted,
  });

  async function send() {
    if (isRecording) {
      await stopRecording();
    }
    if (busy || isTranscribing || !draft.trim()) return;
    const submitted = draft.trim();
    setElapsedSeconds(0);
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
    // Intra-hat follow-up (e.g. Devil's Advocate rejection in Argue Mode)
    if (feedback && !feedback.round_should_complete) {
      const previousAnswer = feedback.turn.user_response ?? "";
      if (feedback.next_challenge_question && turn) {
        setTurn({
          ...turn,
          turn_number: turn.turn_number + 1,
          challenge_question: feedback.next_challenge_question,
          challenge_instruction: feedback.next_challenge_instruction ?? "",
          user_response: null,
          responded_at: null,
        });
        if (quest?.mode === "ARGUE" && previousAnswer) {
          setDraft(previousAnswer);
        }
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
        if (refreshed.mode === "ARGUE" && previousAnswer) {
          setDraft(previousAnswer);
        }
        setFeedback(null);
      } catch {
        setError("Nächster Schritt nicht möglich.");
      } finally {
        setBusy(false);
      }
      return;
    }

    setElapsedSeconds(0);
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
  const isArgue = quest?.mode === "ARGUE";
  if (loading)
    return (
      <AppShell dark={isArgue}>
        <div className="flex items-center justify-center py-10">
          <Card className="w-full max-w-md">
            <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
              <Loader2 className="h-5 w-5 animate-spin text-blue-600 dark:text-indigo-400" />
              <div>
                <p className="font-semibold text-slate-900 dark:text-slate-100">
                  MindQuest wird geladen …
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Die erste Perspektive wird vorbereitet.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </AppShell>
    );
  if (!quest)
    return (
      <AppShell dark={isArgue}>
        <p className="text-amber-700 dark:text-amber-300">{error || "MindQuest nicht gefunden."}</p>
      </AppShell>
    );
  const currentHat =
    quest.status === "HAT_ACTIVE"
      ? quest.current_hat || quest.planned_hats[0]
      : isArgue
        ? null
        : quest.current_hat || quest.planned_hats[0];
  const remainingHats = quest.planned_hats.filter(
    (h) => !quest.completed_hats.includes(h),
  );
  const isLastHat = remainingHats.length <= 1;

  const topActionButton = feedback ? (
    feedback.round_should_complete ? (
      <Button
        onClick={nextStep}
        isLoading={busy}
        size="md"
        className="shrink-0 bg-emerald-600 text-white shadow-md ring-2 ring-emerald-400/60 hover:bg-emerald-500"
      >
        {isLastHat ? "Abschlussreflexion ansehen" : "Nächste Perspektive"}
        <ArrowRight className="ml-2" size={16} />
      </Button>
    ) : (
      <Button
        onClick={nextStep}
        isLoading={busy}
        size="md"
        className="shrink-0 bg-amber-600 text-white shadow-md ring-2 ring-amber-400/60 hover:bg-amber-500"
      >
        <RotateCcw className="mr-2" size={15} />
        {isArgue ? "Antwort überarbeiten" : "Nächste Herausforderung"}
      </Button>
    )
  ) : null;

  return (
    <AppShell dark={isArgue}>
      <div className="flex flex-col gap-3">
        <div className="sticky top-10 z-10 -mx-4 border-b border-slate-200/70 bg-slate-50/95 px-4 py-2 backdrop-blur sm:-mx-6 sm:px-6 dark:border-slate-800/80 dark:bg-slate-950/95">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex min-w-0 items-center gap-2">
              <Link
                href="/mindquests"
                className="shrink-0 text-xs font-medium text-blue-700 hover:underline dark:text-blue-400"
                title="Alle MindQuests"
              >
                ← Zurück
              </Link>
              <span className="text-slate-300 dark:text-slate-700">|</span>
              <h1 className="truncate text-sm font-bold sm:text-base">
                {quest.topic}
              </h1>
              {isArgue && <Badge variant="default">Argue Mode</Badge>}
              <span className="shrink-0 rounded bg-slate-200/70 px-1.5 py-0.5 text-[11px] font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                {quest.target_level} · {quest.completed_hats.length}/
                {quest.planned_hats.length}
              </span>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {!isArgue && (
                <div
                  role="group"
                  aria-label="MindQuest-Modus"
                  className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-xs font-medium"
                >
                  <button
                    type="button"
                    aria-pressed={experienceMode === "written"}
                    onClick={() => setExperienceMode("written")}
                    className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 transition cursor-pointer ${
                      experienceMode === "written"
                        ? "bg-white text-slate-900 shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    <MessageSquareText size={13} />
                    Schriftlich
                  </button>
                  <button
                    type="button"
                    aria-pressed={experienceMode === "conversation"}
                    onClick={() => {
                      if (isRecording) void stopRecording();
                      setExperienceMode("conversation");
                    }}
                    className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 transition cursor-pointer ${
                      experienceMode === "conversation"
                        ? "bg-blue-600 text-white shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    <Volume2 size={13} />
                    Gesprächsmodus
                  </button>
                </div>
              )}
              {!isArgue && currentHat && <HatIndicator hat={currentHat} />}
              {topActionButton}
            </div>
          </div>

          {isArgue ? (
            <div
              className="mt-2 flex flex-wrap items-center gap-1.5"
              aria-label="Hut-Fortschritt"
            >
              {ARGUE_HATS.map((h) => {
                const meta = HAT_METADATA[h];
                const isDone = quest.completed_hats.includes(h);
                const isCurrent = h === currentHat;
                return (
                  <div
                    key={h}
                    title={`${meta.nameGerman} — ${
                      isDone ? "Erledigt" : isCurrent ? "Aktuell" : "Offen"
                    }`}
                    aria-label={`${meta.nameGerman}: ${
                      isDone ? "erledigt" : isCurrent ? "aktuell" : "offen"
                    }`}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold transition ${
                      isCurrent
                        ? "border-indigo-400 bg-indigo-900/90 text-white ring-2 ring-indigo-400/70 shadow-sm"
                        : isDone
                          ? "border-emerald-500/50 bg-emerald-950/60 text-emerald-300"
                          : "border-slate-700 bg-slate-900/70 text-slate-400"
                    }`}
                  >
                    <span
                      className={`h-2 w-2 rounded-full ${HAT_PROGRESS_COLORS[h].completed}`}
                    />
                    <span>{meta.nameGerman.replace(" Hut", "")}</span>
                    {isDone ? (
                      <CheckCircle2 size={13} className="text-emerald-400" />
                    ) : isCurrent ? (
                      <Flame size={13} className="text-indigo-300" />
                    ) : (
                      <CircleDashed size={13} className="text-slate-500" />
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
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
          )}

          {busy && !pendingResponse && (
            <div className="mt-2 flex items-center gap-2 rounded-lg border border-indigo-400/40 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-200">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>
                {isLastHat && feedback?.round_should_complete
                  ? "Abschlussreflexion wird erstellt …"
                  : "Nächster Schritt wird geladen …"}
                {elapsedSeconds > 0 ? ` (${elapsedSeconds}s)` : ""}
              </span>
            </div>
          )}

          {error && (
            <p className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-800 sm:text-sm dark:bg-amber-950/50 dark:text-amber-200">
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
        ) : experienceMode === "conversation" ? (
          <ConversationView
            activeHat={currentHat}
            phase={conversation.phase}
            messages={conversation.messages}
            liveTranscript={conversation.liveTranscript}
            audioLevels={conversation.audioLevels}
            silenceProgress={conversation.silenceProgress}
            error={conversation.error}
            onFinishSpeaking={() => void conversation.finishSpeaking()}
            onSkipAgentSpeech={conversation.skipAgentSpeech}
            onReplayAgentSpeech={conversation.replayAgentSpeech}
            onPauseListening={conversation.pauseListening}
            onResumeListening={() => void conversation.resumeListening()}
          />
        ) : !turn ? (
          isArgue ? (
            <Card
              title="Perspektive wählen (Argue Mode)"
              description="Wähle einen der 5 Hüte. Einmal gewählt, bleibt der Hut gesperrt, bis dein Gesamtschnitt über 80 % liegt."
            >
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {ARGUE_HATS.map((hat) => {
                  const meta = HAT_METADATA[hat];
                  const isCompleted = quest.completed_hats.includes(hat);
                  return (
                    <button
                      key={hat}
                      type="button"
                      disabled={isCompleted || busy}
                      onClick={() => void chooseHat(hat)}
                      className={`flex flex-col justify-between rounded-xl border p-3.5 text-left transition ${
                        isCompleted
                          ? "cursor-not-allowed border-slate-800 bg-slate-900/50 opacity-50"
                          : "border-slate-700 bg-slate-950/70 hover:border-indigo-400 hover:bg-slate-800/80"
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2">
                          <span className="inline-flex items-center gap-2 text-sm font-semibold text-slate-100">
                            <span
                              className={`h-2.5 w-2.5 rounded-full ${
                                HAT_PROGRESS_COLORS[hat].completed
                              }`}
                            />
                            {meta.nameGerman}
                          </span>
                          {isCompleted ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                              <CheckCircle2 size={13} />
                              Erledigt
                            </span>
                          ) : (
                            <Flame size={14} className="text-indigo-400" />
                          )}
                        </div>
                        <p className="mt-1.5 text-xs text-slate-400">
                          {meta.question}
                        </p>
                      </div>
                      <span className="mt-3 text-[11px] font-medium text-indigo-400">
                        {isCompleted
                          ? "Bereits gemeistert"
                          : "Hut wählen & argumentieren →"}
                      </span>
                    </button>
                  );
                })}
              </div>
            </Card>
          ) : (
            <div className="flex items-center justify-center py-8">
              <Card className="w-full max-w-md">
                <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                  <span>Erste Perspektive wird vorbereitet …</span>
                </div>
              </Card>
            </div>
          )
        ) : isArgue ? (
          <div className="grid gap-4 md:grid-cols-[.9fr_1.1fr] md:items-start">
            {/* LEFT COLUMN (Argue Mode): Learner starts and gives reasoning */}
            <div className="flex flex-col gap-3">
              <Card>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-indigo-400">
                    VERSUCH {turn.turn_number} · {currentHat && <span>{currentHat}</span>}
                  </p>
                  <span className="inline-flex items-center gap-1 text-[11px] text-slate-400">
                    <Lock size={11} />
                    Gesperrt bis &gt; 80 %
                  </span>
                </div>
                {turn.turn_number === 1 && (
                  <>
                    <h2 className="mt-1.5 text-base font-semibold leading-6 text-slate-100">
                      {turn.challenge_question}
                    </h2>
                    <p className="mt-2 rounded-lg bg-slate-800/80 p-2.5 text-xs leading-5 text-slate-300">
                      {turn.challenge_instruction}
                    </p>
                  </>
                )}
              </Card>

              {pendingResponse ? (
                <Card
                  title="Deine Argumentation"
                  description="Wird an Devil's Advocate & Auswertung gesendet …"
                >
                  <p className="rounded-lg bg-slate-800/70 p-3 text-sm leading-6 text-slate-200">
                    {pendingResponse}
                  </p>
                </Card>
              ) : feedback ? (
                <Card
                  title="Deine Argumentation"
                  description={
                    feedback.round_should_complete
                      ? "Überzeugend begründet!"
                      : "Klicke oben rechts auf „Antwort überarbeiten“, um deinen Entwurf zu schärfen."
                  }
                >
                  <p className="rounded-lg bg-slate-800/70 p-3 text-sm leading-6 text-slate-200">
                    {feedback.turn.user_response}
                  </p>
                </Card>
              ) : (
                <Card
                  title="Deine Argumentation"
                  description={`Formuliere deine Begründung zu „${quest.topic}“ — Ziel: > 80 % Durchschnitt.`}
                >
                  <form onSubmit={handleResponseSubmit} className="flex flex-col">
                    <textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={handleResponseKeyDown}
                      placeholder="Schreibe deine Antwort hier …"
                      className="min-h-60 w-full resize-y rounded-lg border border-slate-700 bg-slate-950 p-3 leading-7 text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                      <span>
                        {draft.trim().split(/\s+/).filter(Boolean).length} Wörter
                      </span>
                      <Button type="submit" disabled={!draft.trim()} isLoading={busy}>
                        <Send className="mr-2" size={16} />
                        Antwort auswerten
                      </Button>
                    </div>
                  </form>
                </Card>
              )}
            </div>

            {/* RIGHT COLUMN (Argue Mode): Devil's Advocate responds here */}
            <div className="flex flex-col gap-3">
              {pendingResponse ? (
                <Card
                  title="Devil's Advocate prüft dein Argument …"
                  description="Denken, Deutsch, Sprach-Upgrade und Gegenargument werden parallel erstellt."
                >
                  <div className="flex items-center gap-3 rounded-lg border border-indigo-500/30 bg-indigo-950/30 p-4 text-sm text-indigo-200">
                    <Loader2 className="h-5 w-5 shrink-0 animate-spin text-indigo-400" />
                    <div>
                      <p className="font-medium">
                        Auswertung &amp; Devil&apos;s Advocate laufen ({elapsedSeconds}s) …
                      </p>
                      <p className="mt-0.5 text-xs text-slate-400">
                        Alle Bewertungsdimensionen werden gleichzeitig berechnet.
                      </p>
                    </div>
                  </div>
                </Card>
              ) : !feedback ? (
                turn.turn_number > 1 ? (
                  <Card
                    title="Devil's Advocate — Gegenargument"
                    description="Widerlege diese Einwände in deiner Überarbeitung links."
                  >
                    <div className="rounded-lg border border-amber-500/40 bg-amber-950/35 p-3.5 text-sm text-amber-50">
                      <p className="leading-6">{turn.challenge_question}</p>
                      {turn.challenge_instruction && (
                        <p className="mt-2 text-xs text-amber-200/80">
                          {turn.challenge_instruction}
                        </p>
                      )}
                    </div>
                  </Card>
                ) : (
                  <Card
                    title="Devil's Advocate"
                    description="Bereit für deine Argumentation"
                  >
                    <p className="text-sm leading-6 text-slate-300">
                      Gib links dein erstes Argument ein. Der Devil&apos;s Advocate
                      wird deine Logik und dein Deutsch kritisch prüfen, bis dein
                      Gesamtschnitt über <strong className="text-white">80 %</strong>{" "}
                      liegt.
                    </p>
                  </Card>
                )
              ) : (
                <>
                  <Card
                    title={
                      feedback.round_should_complete
                        ? `Akzeptiert (${feedback.average_score ?? "—"} % > 80 %)`
                        : `Abgelehnt (${feedback.average_score ?? "—"} % · > 80 % nötig)`
                    }
                    description={feedback.feedback.encouragement}
                    bodyClassName="flex flex-col gap-3"
                  >
                    {!feedback.round_should_complete && feedback.next_challenge_question && (
                      <div className="rounded-lg border border-amber-500/40 bg-amber-950/35 p-3 text-sm text-amber-50">
                        <p className="text-xs font-bold uppercase tracking-wide text-amber-300">
                          Devil&apos;s Advocate — Gegenargument
                        </p>
                        <p className="mt-1 leading-6">{feedback.next_challenge_question}</p>
                        {feedback.next_challenge_instruction && (
                          <p className="mt-1.5 text-xs text-amber-200/80">
                            {feedback.next_challenge_instruction}
                          </p>
                        )}
                      </div>
                    )}
                    <div className="space-y-2.5">
                      <p className="rounded-lg bg-blue-950/40 p-3 text-sm leading-6 text-blue-100">
                        {feedback.feedback.thinking_feedback}
                      </p>
                      <p className="rounded-lg bg-emerald-950/40 p-3 text-sm leading-6 text-emerald-100">
                        {feedback.feedback.german_feedback}
                      </p>
                    </div>
                  </Card>

                  <div className="grid gap-3 md:grid-cols-2 md:auto-rows-max">
                    <Card title="Denken" bodyClassName="pt-3">
                      <div className="mb-2 flex items-baseline justify-between">
                        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
                          Gesamt
                        </span>
                        <strong className="text-lg font-bold text-blue-400">
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
                        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
                          Gesamt
                        </span>
                        <strong className="text-lg font-bold text-emerald-400">
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
                              <s className="text-slate-400">{c.original}</s>
                              <p className="font-medium">{c.corrected}</p>
                              <p className="mt-1 text-slate-400">{c.explanation}</p>
                            </div>
                          ))}
                        </div>
                      </Card>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-[.9fr_1.1fr] md:items-start">
            {/* Left column (Answering Mode): Challenge prompt and Feedback summary */}
            <div className="flex flex-col gap-3">
              <Card>
                <p className="text-xs font-semibold text-blue-700">
                  RUNDE {turn.turn_number} · {currentHat && <span>{currentHat}</span>}
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
                </Card>
              )}
            </div>

            {/* Right column (Answering Mode): Editor, loading state, or evaluation */}
            <div className="flex flex-col">
              {pendingResponse ? (
                <Card
                  title="Deine Antwort"
                  description="Denken, Deutsch und Sprach-Upgrade werden parallel erstellt …"
                  bodyClassName="flex flex-col gap-3"
                >
                  <p className="rounded-lg bg-slate-50 p-3.5 text-sm leading-6 text-slate-700">
                    {pendingResponse}
                  </p>
                  <div className="flex items-center gap-2.5 rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
                    <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                    <span>Auswertung läuft ({elapsedSeconds}s) …</span>
                  </div>
                </Card>
              ) : !feedback ? (
                <Card
                  title="Deine Antwort"
                  description="Formuliere deine Gedanken auf Deutsch. Qualität ist wichtiger als Länge."
                  headerAction={
                    <SpeechModeToggle
                      mode={inputMode}
                      isRecording={isRecording}
                      onStartSpeaking={() => void startRecording()}
                      onStopSpeaking={() => void stopRecording()}
                    />
                  }
                >
                  <form onSubmit={handleResponseSubmit} className="flex flex-col">
                    <SpeechRecordingBanner
                      isRecording={isRecording}
                      isTranscribing={isTranscribing}
                      elapsedSeconds={speechElapsedSeconds}
                      audioLevels={audioLevels}
                      interimText={interimText}
                      speechError={speechError}
                      onStopSpeaking={() => void stopRecording()}
                    />
                    <textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={handleResponseKeyDown}
                      placeholder={
                        isRecording
                          ? "Sprich jetzt ins Mikrofon — dein Text erscheint hier …"
                          : "Schreibe deine Antwort hier …"
                      }
                      className={`min-h-56 w-full resize-y rounded-lg border bg-white p-3 leading-7 text-slate-900 outline-none ${
                        isRecording
                          ? "border-amber-400 bg-amber-50/20 ring-2 ring-amber-200 focus:ring-amber-400"
                          : "border-slate-300 focus:ring-2 focus:ring-blue-500"
                      }`}
                    />
                    <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                      <span>
                        {draft.trim().split(/\s+/).filter(Boolean).length} Wörter
                      </span>
                      <Button
                        type="submit"
                        disabled={!draft.trim() || isTranscribing}
                        isLoading={busy || isTranscribing}
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
                      <span className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        Gesamt
                      </span>
                      <strong className="text-lg font-bold text-emerald-700 dark:text-emerald-400">
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
                            <s className="text-slate-500 dark:text-slate-400">{c.original}</s>
                            <p className="font-medium">{c.corrected}</p>
                            <p className="mt-1 text-slate-600 dark:text-slate-400">{c.explanation}</p>
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
