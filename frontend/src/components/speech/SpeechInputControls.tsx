"use client";

import { Keyboard, Mic, Square } from "lucide-react";
import { InputMode } from "@/hooks/useSpeechToText";

export function SpeechModeToggle({
  mode,
  isRecording,
  onStartSpeaking,
  onStopSpeaking,
}: {
  mode: InputMode;
  isRecording: boolean;
  onStartSpeaking: () => void;
  onStopSpeaking: () => void;
}) {
  return (
    <div
      role="group"
      aria-label="Eingabemodus"
      className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-xs font-medium"
    >
      <button
        type="button"
        aria-pressed={mode === "typing"}
        onClick={() => {
          if (isRecording) onStopSpeaking();
        }}
        className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 transition cursor-pointer ${
          mode === "typing"
            ? "bg-white text-slate-900 shadow-xs"
            : "text-slate-600 hover:text-slate-900"
        }`}
      >
        <Keyboard size={14} />
        Eintippen
      </button>
      <button
        type="button"
        aria-pressed={mode === "speaking"}
        onClick={() => {
          if (!isRecording) onStartSpeaking();
          else onStopSpeaking();
        }}
        className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 transition cursor-pointer ${
          mode === "speaking"
            ? "bg-rose-600 text-white shadow-xs"
            : "text-slate-600 hover:text-slate-900"
        }`}
      >
        <Mic size={14} />
        Einsprechen
      </button>
    </div>
  );
}

export function SpeechRecordingBanner({
  isRecording,
  isTranscribing,
  elapsedSeconds,
  audioLevels,
  interimText,
  speechError,
  onStopSpeaking,
}: {
  isRecording: boolean;
  isTranscribing: boolean;
  elapsedSeconds: number;
  audioLevels: number[];
  interimText: string;
  speechError: string;
  onStopSpeaking: () => void;
}) {
  return (
    <>
      {(isRecording || isTranscribing) && (
        <div
          role="status"
          aria-live="polite"
          data-testid="recording-indicator"
          className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-xs text-rose-900"
        >
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-rose-600" />
            </span>
            <span className="font-semibold">
              {isTranscribing ? "Sprache wird transkribiert …" : "Mikrofon nimmt auf …"}
            </span>
            <span className="font-mono text-rose-700">
              {String(Math.floor(elapsedSeconds / 60)).padStart(2, "0")}:
              {String(elapsedSeconds % 60).padStart(2, "0")}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div
              data-testid="audio-level-bars"
              aria-hidden="true"
              className="flex h-4 items-end gap-0.5"
            >
              {audioLevels.map((lvl, idx) => (
                <span
                  key={idx}
                  className="w-1 rounded-full bg-rose-500 transition-all duration-150"
                  style={{ height: `${Math.round(lvl * 16)}px` }}
                />
              ))}
            </div>
            {isRecording && (
              <button
                type="button"
                onClick={onStopSpeaking}
                className="inline-flex items-center gap-1 rounded-md bg-rose-600 px-2.5 py-1 font-medium text-white hover:bg-rose-700 cursor-pointer"
              >
                <Square size={11} />
                Aufnahme stoppen
              </button>
            )}
          </div>
        </div>
      )}
      {interimText && (
        <p className="mb-2 rounded-md bg-slate-100 px-3 py-1.5 text-xs italic text-slate-600">
          Live: „{interimText}“
        </p>
      )}
      {speechError && (
        <p className="mb-2 rounded-md bg-rose-50 px-3 py-1.5 text-xs text-rose-700">
          {speechError}
        </p>
      )}
    </>
  );
}
