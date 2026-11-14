"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import { ArrowRight, MessageSquareText, Send, Volume2 } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { ConversationView } from "@/components/conversation/ConversationView";
import { ScoreBar } from "@/components/evaluation/ProfileScoreCards";
import { HatIndicator } from "@/components/hats/HatIndicator";
import {
  SpeechModeToggle,
  SpeechRecordingBanner,
} from "@/components/speech/SpeechInputControls";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useConversationSession } from "@/hooks/useConversationSession";
import { useSpeechToText } from "@/hooks/useSpeechToText";
import {
  getMindQuest,
  startMindQuest,
  submitResponse,
  advanceMindQuest,
} from "@/services/api/mindquests";
import { HAT_METADATA, HatType } from "@/types/hat";
import { MindQuest, SubmitResponseResponse, Turn } from "@/types/mindquest";

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
    [error, setError] = useState(""),
    [experienceMode, setExperienceMode] = useState<"written" | "conversation">("written");
  useEffect(() => {
    getMindQuest(id)
      .then((q) => {
        if (q.status === "COMPLETED") {
          router.replace(`/mindquests/${id}/reflection`);
          return;
        }
        setQuest(q);
        const round = q.hat_rounds.find((r) => r.hat === q.current_hat);
        setTurn(round?.turns.at(-1) ?? null);
        if (q.planned_hats.length - q.completed_hats.length <= 1) {
          router.prefetch(`/mindquests/${id}/reflection`);
        }
      })
      .catch(() => setError("Diese MindQuest konnte nicht geladen werden."))
      .finally(() => setLoading(false));
  }, [id, router]);
  async function begin() {
    setBusy(true);
    setError("");
    try {
      const result = await startMindQuest(id);
      setQuest(result.mindquest);
      setTurn(result.initial_turn);
    } catch {
      setError("Starten war nicht möglich.");
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
    elapsedSeconds,
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
      <div className="flex flex-col gap-4 md:flex-1 md:min-h-0">
        <div className="shrink-0">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <Link
                href="/mindquests"
                className="text-sm text-blue-700 hover:underline"
              >
                ← Alle MindQuests
              </Link>
              <h1 className="mt-1 truncate text-2xl font-bold md:text-3xl">{quest.topic}</h1>
              <p className="mt-0.5 text-sm text-slate-600">
                Sprachniveau {quest.target_level} · {quest.completed_hats.length}/
                {quest.planned_hats.length} Perspektiven
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2.5">
              <div
                role="group"
                aria-label="MindQuest-Modus"
                className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-xs font-medium"
              >
                <button
                  type="button"
                  aria-pressed={experienceMode === "written"}
                  onClick={() => setExperienceMode("written")}
                  className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 transition cursor-pointer ${
                    experienceMode === "written"
                      ? "bg-white text-slate-900 shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <MessageSquareText size={14} />
                  Schriftlich
                </button>
                <button
                  type="button"
                  aria-pressed={experienceMode === "conversation"}
                  onClick={() => {
                    if (isRecording) void stopRecording();
                    setExperienceMode("conversation");
                  }}
                  className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 transition cursor-pointer ${
                    experienceMode === "conversation"
                      ? "bg-blue-600 text-white shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Volume2 size={14} />
                  Gesprächsmodus
                </button>
              </div>
              {currentHat && <HatIndicator hat={currentHat} detail />}
            </div>
          </div>
          <div className="mt-4 flex gap-1.5">
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
                  className={`h-2.5 flex-1 rounded-full transition-all ${stateClass}`}
                />
              );
            })}
          </div>
          {error && (
            <p className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
              {error}
            </p>
          )}
        </div>

        {quest.status === "COMPLETED" ? (
          <div className="md:flex md:flex-1 md:min-h-0 md:items-center md:justify-center">
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
          <div className="md:flex md:flex-1 md:min-h-0 md:items-center md:justify-center">
            <Card
              title="Bereit für deine erste Perspektive"
              description="Du bekommst eine fokussierte Frage und Feedback zu Denken und Sprache."
              className="w-full max-w-xl"
            >
              <div className="flex flex-wrap gap-3">
                <Button isLoading={busy} onClick={begin}>
                  MindQuest beginnen <ArrowRight className="ml-2" size={16} />
                </Button>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() => setExperienceMode("conversation")}
                >
                  <Volume2 className="mr-2" size={16} />
                  Mündliches Gespräch starten
                </Button>
              </div>
            </Card>
          </div>
        ) : (
          <div
            className={`grid gap-5 md:flex-1 md:min-h-0 ${
              feedback
                ? "md:grid-cols-[.95fr_1.05fr]"
                : "md:grid-cols-[.9fr_1.1fr]"
            }`}
          >
            {/* Left column: Challenge prompt (and Feedback summary when evaluated) */}
            <div className="flex flex-col gap-4 md:min-h-0 md:overflow-y-auto md:pr-1">
              <Card className={feedback ? "shrink-0" : "md:flex-1 md:flex md:flex-col"}>
                <p className="text-xs font-semibold text-blue-700 md:text-sm">
                  RUNDE {turn.turn_number} ·{" "}
                  {currentHat && <span>{currentHat}</span>}
                </p>
                <h2 className="mt-2.5 text-lg font-semibold leading-7 md:text-[clamp(1.05rem,1.4vw,1.35rem)] md:leading-relaxed">
                  {turn.challenge_question}
                </h2>
                <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-600">
                  {turn.challenge_instruction}
                </p>
              </Card>

              {feedback && (
                <Card
                  title="Dein Feedback"
                  description={feedback.feedback.encouragement}
                  className="flex flex-col md:flex-1 md:min-h-0"
                  bodyClassName="flex flex-1 flex-col justify-between gap-4"
                >
                  <div className="space-y-3">
                    <p className="rounded-lg bg-blue-50 p-3.5 text-sm leading-6 text-slate-700">
                      {feedback.feedback.thinking_feedback}
                    </p>
                    <p className="rounded-lg bg-emerald-50 p-3.5 text-sm leading-6 text-slate-700">
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

            {/* Right column: Response editor, pending state, or horizontal score + corrections panel */}
            <div className="flex flex-col md:min-h-0">
              {pendingResponse ? (
                <Card
                  title="Deine Antwort"
                  description="Denken und Deutsch werden gleichzeitig ausgewertet …"
                  className="md:flex md:h-full md:flex-col"
                  bodyClassName="flex flex-1 flex-col justify-between gap-4"
                >
                  <p className="rounded-lg bg-slate-50 p-4 text-sm leading-6 text-slate-700">
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
                  className="flex flex-col md:h-full md:min-h-0"
                  bodyClassName="flex flex-1 flex-col md:min-h-0"
                  headerAction={
                    <SpeechModeToggle
                      mode={inputMode}
                      isRecording={isRecording}
                      onStartSpeaking={() => void startRecording()}
                      onStopSpeaking={() => void stopRecording()}
                    />
                  }
                >
                  <form
                    onSubmit={handleResponseSubmit}
                    className="flex flex-1 flex-col md:min-h-0"
                  >
                    <SpeechRecordingBanner
                      isRecording={isRecording}
                      isTranscribing={isTranscribing}
                      elapsedSeconds={elapsedSeconds}
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
                      className={`min-h-44 w-full flex-1 resize-none rounded-lg border p-3 leading-7 outline-none md:min-h-0 ${
                        isRecording
                          ? "border-rose-400 bg-rose-50/20 ring-2 ring-rose-200 focus:ring-rose-400"
                          : "border-slate-300 focus:ring-2 focus:ring-blue-500"
                      }`}
                    />
                    <div className="mt-3 flex shrink-0 items-center justify-between text-xs text-slate-500">
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
                <div className="grid gap-4 md:flex-1 md:min-h-0 md:grid-cols-2 md:auto-rows-max md:overflow-y-auto md:pr-1">
                  <Card title="Denken" bodyClassName="pt-3">
                    <ScoreBar
                      label="Gesamt"
                      value={feedback.thinking_evaluation.score}
                      barClassName="bg-blue-600"
                    />
                    <div className="mt-4 space-y-2.5">
                      <ScoreBar
                        label="Perspektiven-Fokus"
                        value={feedback.thinking_evaluation.hat_adherence}
                        barClassName="bg-blue-600"
                      />
                      <ScoreBar
                        label="Argumentation"
                        value={feedback.thinking_evaluation.reasoning}
                        barClassName="bg-blue-600"
                      />
                      <ScoreBar
                        label="Tiefe"
                        value={feedback.thinking_evaluation.depth}
                        barClassName="bg-blue-600"
                      />
                      <ScoreBar
                        label="Spezifität"
                        value={feedback.thinking_evaluation.specificity}
                        barClassName="bg-blue-600"
                      />
                    </div>
                  </Card>
                  <Card title="Deutsch" bodyClassName="pt-3">
                    <ScoreBar
                      label="Gesamt"
                      value={feedback.german_evaluation.score}
                      barClassName="bg-emerald-600"
                    />
                    <div className="mt-4 space-y-2.5">
                      <ScoreBar
                        label="Grammatik"
                        value={feedback.german_evaluation.grammar}
                        barClassName="bg-emerald-600"
                      />
                      <ScoreBar
                        label="Wortschatz"
                        value={feedback.german_evaluation.vocabulary}
                        barClassName="bg-emerald-600"
                      />
                      <ScoreBar
                        label="Satzbau"
                        value={feedback.german_evaluation.sentence_structure}
                        barClassName="bg-emerald-600"
                      />
                      <ScoreBar
                        label="Natürlichkeit"
                        value={feedback.german_evaluation.naturalness}
                        barClassName="bg-emerald-600"
                      />
                    </div>
                  </Card>
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
