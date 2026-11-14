"use client";

import { Brain, Check, Loader2, Mic, Pause, Play, RotateCcw, SkipForward, Volume2 } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { HAT_METADATA, HatType } from "@/types/hat";

export type ConversationPhase =
  | "initializing"
  | "agent_speaking"
  | "listening"
  | "thinking"
  | "paused"
  | "completed";

export interface ConversationMessage {
  id: string;
  role: "agent" | "user";
  text: string;
  hat?: HatType | null;
  thinkingScore?: number;
  germanScore?: number;
  averageScore?: number;
}

const STATUS_LABELS: Record<ConversationPhase, string> = {
  initializing: "Gespräch wird gestartet …",
  agent_speaking: "Conversation Agent spricht …",
  listening: "Mikrofon hört zu — sprich auf Deutsch …",
  thinking: "Agent denkt nach & bereitet Antwort vor …",
  paused: "Mikrofon pausiert",
  completed: "Gespräch abgeschlossen — Reflexion öffnet …",
};

export interface ConversationViewProps {
  activeHat?: HatType | null;
  isArgue?: boolean;
  phase: ConversationPhase;
  messages: ConversationMessage[];
  liveTranscript: string;
  audioLevels: number[];
  silenceProgress: number;
  error: string;
  onFinishSpeaking: () => void;
  onSkipAgentSpeech: () => void;
  onReplayAgentSpeech: () => void;
  onPauseListening: () => void;
  onResumeListening: () => void;
}
export function ConversationView(props: ConversationViewProps) {
  const {
    activeHat,
    isArgue = false,
    phase,
    messages,
    liveTranscript,
    audioLevels,
    silenceProgress,
    error,
    onFinishSpeaking,
    onSkipAgentSpeech,
    onReplayAgentSpeech,
    onPauseListening,
    onResumeListening,
  } = props;
  const hatMeta = activeHat ? HAT_METADATA[activeHat] : null;
  const latestAgentMsg = [...messages].reverse().find((m) => m.role === "agent");
  const orbColor =
    phase === "listening"
      ? "bg-indigo-600 text-white shadow-lg ring-8 ring-indigo-100 dark:ring-indigo-400/30"
      : phase === "agent_speaking"
        ? "bg-blue-600 text-white shadow-lg ring-8 ring-blue-100 dark:ring-blue-400/30"
        : phase === "thinking"
          ? "bg-amber-500 text-white shadow-lg ring-8 ring-amber-100 dark:ring-amber-400/30"
          : "bg-slate-700 text-white ring-4 ring-slate-200 dark:ring-slate-600";

  return (
    <div
      data-testid="conversation-view"
      className="grid gap-4 md:grid-cols-[1.05fr_.95fr] md:items-start"
    >
      <Card
        bodyClassName="flex flex-col items-center justify-between gap-5 p-6 text-center"
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-blue-700 dark:text-indigo-300">
            {isArgue
              ? "Mündlicher Argue Mode · Perspective Challenger"
              : "Mündlicher Gesprächsmodus · Conversation Agent"}
          </p>
          {hatMeta && (
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Perspektive: <strong>{hatMeta.nameGerman}</strong> ({hatMeta.question})
            </p>
          )}
        </div>

        <div className="flex flex-col items-center gap-4">
          <div
            data-testid="conversation-orb"
            className={`relative grid h-24 w-24 place-items-center rounded-full transition-all ${orbColor}`}
          >
            {(phase === "listening" || phase === "agent_speaking") && (
              <span className="absolute inset-0 animate-ping rounded-full bg-current opacity-20" />
            )}
            {phase === "listening" ? (
              <Mic size={34} />
            ) : phase === "agent_speaking" ? (
              <Volume2 size={34} />
            ) : phase === "thinking" ? (
              <Loader2 size={34} className="animate-spin" />
            ) : (
              <Brain size={34} />
            )}
          </div>

          <p role="status" aria-live="polite" data-testid="conversation-status" className="font-semibold">
            {STATUS_LABELS[phase]}
          </p>

          {phase === "listening" && (
            <div className="flex flex-col items-center gap-2">
              <div data-testid="conversation-audio-bars" className="flex h-5 items-end gap-1">
                {audioLevels.map((lvl, idx) => (
                  <span
                    key={idx}
                    className="w-1.5 rounded-full bg-indigo-500 transition-all duration-150 dark:bg-indigo-300"
                    style={{ height: `${Math.max(4, Math.round(lvl * 20))}px` }}
                  />
                ))}
              </div>
              {silenceProgress > 0 && (
                <div className="w-44">
                  <p className="text-[11px] text-slate-500 dark:text-slate-300">
                    Sprechpause — sendet gleich …
                  </p>
                  <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-600">
                    <div className="h-full bg-indigo-500 dark:bg-indigo-300" style={{ width: `${silenceProgress}%` }} />
                  </div>
                </div>
              )}
            </div>
          )}

          {phase === "agent_speaking" && latestAgentMsg && (
            <p className="max-w-md rounded-xl bg-blue-50 px-4 py-3 text-sm text-slate-800 dark:bg-slate-800/80 dark:text-slate-100">
              „{latestAgentMsg.text}“
            </p>
          )}
          {phase === "listening" && liveTranscript && (
            <p
              data-testid="live-spoken-transcript"
              className="max-w-md rounded-xl border border-indigo-200 bg-indigo-50/70 px-4 py-3 text-sm dark:border-indigo-400/50 dark:bg-indigo-900/40 dark:text-slate-100"
            >
              „{liveTranscript}“
            </p>
          )}
          {error && (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-900/50 dark:text-amber-200">
              {error}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-center gap-2">
          {phase === "agent_speaking" && (
            <Button variant="outline" size="sm" onClick={onSkipAgentSpeech}>
              <SkipForward size={15} className="mr-1.5" /> Direkt antworten
            </Button>
          )}
          {phase === "listening" && (
            <>
              <Button onClick={onFinishSpeaking}>
                <Check size={16} className="mr-1.5" /> Fertig gesprochen
              </Button>
              <Button variant="outline" onClick={onPauseListening}>
                <Pause size={15} className="mr-1.5" /> Pausieren
              </Button>
              {latestAgentMsg && (
                <Button variant="ghost" size="sm" onClick={onReplayAgentSpeech}>
                  <RotateCcw size={14} className="mr-1.5" /> Wiederholen
                </Button>
              )}
            </>
          )}
          {phase === "paused" && (
            <Button onClick={onResumeListening}>
              <Play size={15} className="mr-1.5" /> Weiter sprechen
            </Button>
          )}
        </div>
      </Card>

      <Card
        title="Gesprächsverlauf"
        description="Deine mündliche Debatte durch die Denkhüte"
        bodyClassName="space-y-3"
      >
        {messages.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-300">
            Der Conversation Agent bereitet die Frage vor …
          </p>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`rounded-xl p-3.5 text-sm leading-6 ${
                msg.role === "agent"
                  ? "border border-blue-100 bg-blue-50/60 dark:border-indigo-400/40 dark:bg-indigo-900/35"
                  : "border border-slate-200 bg-slate-50 dark:border-slate-500 dark:bg-slate-800/80"
              }`}
            >
              <div className="mb-1 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-300">
                <span className="font-semibold text-slate-700 dark:text-slate-100">
                  {msg.role === "agent"
                    ? isArgue
                      ? "Perspective Challenger"
                      : "Conversation Agent"
                    : "Du (gesprochen)"}
                </span>
                <div className="flex items-center gap-1.5">
                  {msg.hat && <Badge>{HAT_METADATA[msg.hat].nameGerman}</Badge>}
                  {typeof msg.thinkingScore === "number" && (
                    <Badge variant="info">Denken {msg.thinkingScore}</Badge>
                  )}
                  {typeof msg.germanScore === "number" && (
                    <Badge variant="success">Deutsch {msg.germanScore}</Badge>
                  )}
                  {typeof msg.averageScore === "number" && (
                    <Badge variant={msg.averageScore > 80 ? "success" : "warning"}>
                      Ø {msg.averageScore} %
                    </Badge>
                  )}
                </div>
              </div>
              <p>{msg.text}</p>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
