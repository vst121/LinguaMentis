"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ConversationMessage,
  ConversationPhase,
} from "@/components/conversation/ConversationView";
import { openConversation, submitConversationTurn } from "@/services/api/conversation";
import { synthesizeSpeech } from "@/services/api/speech";
import { MindQuest, Turn } from "@/types/mindquest";

const SILENCE_AUTO_SEND_MS = 2000;

interface SpeechEventLike {
  resultIndex: number;
  results: {
    length: number;
    [i: number]: { isFinal: boolean; 0: { transcript: string } };
  };
}

interface SpeechRecognitionLike {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((ev: SpeechEventLike) => void) | null;
  onerror: ((ev: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

function getSpeechCtor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as Record<string, unknown>;
  return (w.SpeechRecognition || w.webkitSpeechRecognition || null) as
    | (new () => SpeechRecognitionLike)
    | null;
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onloadend = () => {
      const s = String(r.result || "");
      resolve(s.includes(",") ? s.split(",")[1] : s);
    };
    r.onerror = () => reject(new Error("Audio read failed"));
    r.readAsDataURL(blob);
  });
}

export function useConversationSession({
  mindquestId,
  enabled,
  onQuestUpdated,
  onCompleted,
  onHatSelectionNeeded,
}: {
  mindquestId: string;
  enabled: boolean;
  onQuestUpdated: (quest: MindQuest, activeTurn: Turn | null) => void;
  onCompleted: () => void;
  onHatSelectionNeeded?: (quest: MindQuest) => void;
}) {
  const [phase, setPhase] = useState<ConversationPhase>("initializing");
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [audioLevels, setAudioLevels] = useState<number[]>([0.25, 0.5, 0.75, 0.5, 0.3]);
  const [silenceProgress, setSilenceProgress] = useState(0);
  const [error, setError] = useState("");
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const lastAudioRef = useRef<{ base64: string; mime: string; text: string } | null>(null);
  const recRef = useRef<SpeechRecognitionLike | null>(null);
  const mediaRecRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const finalTxtRef = useRef("");
  const interimTxtRef = useRef("");
  const hasSpokenAudioRef = useRef(false);
  const lastSpeechAtRef = useRef<number>(0);
  const silenceTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const levelTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const submittingRef = useRef(false);

  const stopAllMedia = useCallback(() => {
    if (silenceTimerRef.current) clearInterval(silenceTimerRef.current);
    if (levelTimerRef.current) clearInterval(levelTimerRef.current);
    silenceTimerRef.current = null;
    levelTimerRef.current = null;

    if (audioElRef.current) {
      audioElRef.current.onended = null;
      audioElRef.current.onerror = null;
      audioElRef.current.pause();
      audioElRef.current = null;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      try {
        window.speechSynthesis.cancel();
      } catch {}
    }
    if (recRef.current) {
      try {
        recRef.current.onresult = null;
        recRef.current.onerror = null;
        recRef.current.onend = null;
        recRef.current.stop();
      } catch {}
      recRef.current = null;
    }
    if (audioCtxRef.current) {
      try {
        void audioCtxRef.current.close();
      } catch {}
      audioCtxRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }, []);

  const beginListeningRef = useRef<() => Promise<void>>(async () => {});
  const finishSpeakingRef = useRef<() => Promise<void>>(async () => {});

  const playAgentSpeech = useCallback(
    (
      audioBase64: string,
      mimeType: string,
      fallbackText: string,
      isDone: boolean,
      hatCompletedQuest?: MindQuest | null,
    ) => {
      stopAllMedia();
      lastAudioRef.current = { base64: audioBase64, mime: mimeType, text: fallbackText };
      setPhase("agent_speaking");

      const afterSpeech = () => {
        if (isDone) {
          setPhase("completed");
          onCompleted();
        } else if (hatCompletedQuest && onHatSelectionNeeded) {
          setPhase("paused");
          onHatSelectionNeeded(hatCompletedQuest);
        } else {
          void beginListeningRef.current();
        }
      };

      if (audioBase64 && typeof Audio !== "undefined") {
        try {
          const audio = new Audio(`data:${mimeType || "audio/wav"};base64,${audioBase64}`);
          audioElRef.current = audio;
          audio.onended = afterSpeech;
          audio.onerror = afterSpeech;
          const p = audio.play();
          if (p && typeof p.catch === "function") {
            p.catch(() => afterSpeech());
          }
          return;
        } catch {}
      }

      if (typeof window !== "undefined" && "speechSynthesis" in window && fallbackText) {
        try {
          const u = new SpeechSynthesisUtterance(fallbackText);
          u.lang = "de-DE";
          u.onend = afterSpeech;
          u.onerror = afterSpeech;
          window.speechSynthesis.speak(u);
          return;
        } catch {}
      }

      afterSpeech();
    },
    [onCompleted, onHatSelectionNeeded, stopAllMedia]
  );

  const finishSpeaking = useCallback(async () => {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setError("");
    setSilenceProgress(0);

    const activeRec = recRef.current;
    if (activeRec) {
      await new Promise<void>((resolve) => {
        const to = setTimeout(resolve, 200);
        activeRec.onend = () => {
          clearTimeout(to);
          resolve();
        };
        try {
          activeRec.stop();
        } catch {
          clearTimeout(to);
          resolve();
        }
      });
    }

    const recorder = mediaRecRef.current;
    mediaRecRef.current = null;
    let blob: Blob | null = null;
    if (recorder && recorder.state !== "inactive") {
      blob = await new Promise<Blob | null>((resolve) => {
        recorder.onstop = () => {
          const mime = recorder.mimeType || "audio/webm";
          resolve(chunksRef.current.length ? new Blob(chunksRef.current, { type: mime }) : null);
        };
        try {
          recorder.stop();
        } catch {
          resolve(null);
        }
      });
    }

    stopAllMedia();

    const combinedText = `${finalTxtRef.current} ${interimTxtRef.current}`.trim();
    let audioB64: string | null = null;
    if (!combinedText && blob && blob.size > 0) {
      try {
        audioB64 = await blobToBase64(blob);
      } catch {}
    }

    if (!combinedText && !audioB64) {
      submittingRef.current = false;
      setError("Es wurde noch keine Sprache erkannt. Sprich einfach los!");
      void beginListeningRef.current();
      return;
    }

    setPhase("thinking");
    setLiveTranscript("");

    try {
      const res = await submitConversationTurn(mindquestId, {
        transcript: combinedText || null,
        audio_base64: audioB64,
        mime_type: blob?.type || "audio/webm",
        include_audio: false,
      });
      const needsNextHatSelection =
        res.mindquest.mode === "ARGUE" &&
        res.mindquest.status === "HAT_COMPLETED" &&
        !res.is_completed;
      if (!needsNextHatSelection) {
        onQuestUpdated(res.mindquest, res.active_turn ?? null);
      }
      setMessages((prev) => [
        ...prev,
        {
          id: `u-${Date.now()}`,
          role: "user",
          text: res.user_transcript,
          thinkingScore: res.thinking_evaluation.score,
          germanScore: res.german_evaluation.score,
          averageScore: res.average_score,
        },
        {
          id: `a-${Date.now() + 1}`,
          role: "agent",
          text: res.spoken_reply,
          hat: res.active_hat,
        },
      ]);

      let finalAudioB64 = res.audio_base64;
      let finalAudioMime = res.audio_mime_type;
      if (!finalAudioB64 && res.spoken_reply) {
        try {
          const tts = await synthesizeSpeech(res.spoken_reply);
          finalAudioB64 = tts.audio_base64;
          finalAudioMime = tts.mime_type;
        } catch {}
      }
      submittingRef.current = false;
      playAgentSpeech(
        finalAudioB64,
        finalAudioMime,
        res.spoken_reply,
        res.is_completed,
        needsNextHatSelection ? res.mindquest : null,
      );
    } catch {
      submittingRef.current = false;
      setError("Deine gesprochene Antwort konnte nicht verarbeitet werden.");
      setPhase("paused");
    }
  }, [mindquestId, onQuestUpdated, playAgentSpeech, stopAllMedia]);

  const beginListening = useCallback(async () => {
    stopAllMedia();
    setSilenceProgress(0);
    setError("");
    setLiveTranscript("");
    finalTxtRef.current = "";
    interimTxtRef.current = "";
    chunksRef.current = [];
    hasSpokenAudioRef.current = false;
    lastSpeechAtRef.current = 0;

    const SpeechCtor = getSpeechCtor();

    if (typeof navigator !== "undefined" && navigator.mediaDevices?.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        if (typeof MediaRecorder !== "undefined") {
          const mime =
            typeof MediaRecorder.isTypeSupported === "function" &&
            MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
              ? "audio/webm;codecs=opus"
              : undefined;
          const rec = new MediaRecorder(
            stream,
            mime ? { mimeType: mime, audioBitsPerSecond: 24000 } : { audioBitsPerSecond: 24000 }
          );
          rec.ondataavailable = (ev) => {
            if (ev.data?.size > 0) chunksRef.current.push(ev.data);
          };
          rec.start(250);
          mediaRecRef.current = rec;
        }

        if (typeof AudioContext !== "undefined") {
          try {
            const ctx = new AudioContext();
            audioCtxRef.current = ctx;
            const src = ctx.createMediaStreamSource(stream);
            const analyser = ctx.createAnalyser();
            analyser.fftSize = 256;
            src.connect(analyser);
            const buf = new Uint8Array(analyser.frequencyBinCount);
            levelTimerRef.current = setInterval(() => {
              analyser.getByteTimeDomainData(buf);
              let sumSq = 0;
              for (let i = 0; i < buf.length; i += 1) {
                const v = (buf[i] - 128) / 128;
                sumSq += v * v;
              }
              const rms = Math.sqrt(sumSq / buf.length);
              if (rms > 0.035) {
                hasSpokenAudioRef.current = true;
                lastSpeechAtRef.current = Date.now();
              }
              setAudioLevels([0.7, 1.0, 1.3, 1.0, 0.8].map((f) => Math.min(1, Math.max(0.2, rms * 6 * f))));
            }, 120);
          } catch {}
        }
      } catch {
        if (!SpeechCtor) {
          setError("Mikrofonzugriff wurde verweigert.");
          setPhase("paused");
          return;
        }
      }
    } else if (!SpeechCtor) {
      setError("Spracherkennung wird in diesem Browser nicht unterstützt.");
      setPhase("paused");
      return;
    }

    if (SpeechCtor) {
      try {
        const rec = new SpeechCtor();
        rec.lang = "de-DE";
        rec.continuous = true;
        rec.interimResults = true;
        rec.onresult = (ev) => {
          let f = "";
          let inter = "";
          for (let i = ev.resultIndex; i < ev.results.length; i += 1) {
            const r = ev.results[i];
            const t = r[0]?.transcript || "";
            if (r.isFinal) f += `${t} `;
            else inter += t;
          }
          if (f.trim()) finalTxtRef.current = `${finalTxtRef.current} ${f.trim()}`.trim();
          interimTxtRef.current = inter.trim();
          const full = `${finalTxtRef.current} ${interimTxtRef.current}`.trim();
          if (full) {
            hasSpokenAudioRef.current = true;
            lastSpeechAtRef.current = Date.now();
          }
          setLiveTranscript(full);
        };
        rec.start();
        recRef.current = rec;
      } catch {}
    }

    setPhase("listening");

    silenceTimerRef.current = setInterval(() => {
      if (!hasSpokenAudioRef.current || lastSpeechAtRef.current === 0) {
        setSilenceProgress(0);
        return;
      }
      const elapsed = Date.now() - lastSpeechAtRef.current;
      const pct = Math.min(100, Math.round((elapsed / SILENCE_AUTO_SEND_MS) * 100));
      setSilenceProgress(pct);
      if (elapsed >= SILENCE_AUTO_SEND_MS) {
        void finishSpeakingRef.current();
      }
    }, 150);
  }, [stopAllMedia]);

  useEffect(() => {
    finishSpeakingRef.current = finishSpeaking;
    beginListeningRef.current = beginListening;
  }, [finishSpeaking, beginListening]);

  const skipAgentSpeech = useCallback(() => {
    void beginListening();
  }, [beginListening]);

  const replayAgentSpeech = useCallback(() => {
    const last = lastAudioRef.current;
    if (last) playAgentSpeech(last.base64, last.mime, last.text, false);
  }, [playAgentSpeech]);

  const pauseListening = useCallback(() => {
    stopAllMedia();
    setSilenceProgress(0);
    setPhase("paused");
  }, [stopAllMedia]);

  useEffect(() => {
    if (!enabled) {
      stopAllMedia();
      return;
    }
    let cancelled = false;
    void (async () => {
      await Promise.resolve();
      if (cancelled) return;
      setPhase("initializing");
      setError("");
      try {
        const res = await openConversation(mindquestId);
        if (cancelled) return;
        onQuestUpdated(res.mindquest, res.active_turn ?? null);
        setMessages((prev) =>
          prev.length > 0
            ? prev
            : [{ id: "a-init", role: "agent", text: res.spoken_text, hat: res.active_hat }]
        );
        playAgentSpeech(res.audio_base64, res.audio_mime_type, res.spoken_text, res.is_completed);
      } catch {
        if (!cancelled) {
          setError("Gesprächsmodus konnte nicht gestartet werden.");
          setPhase("paused");
        }
      }
    })();

    return () => {
      cancelled = true;
      stopAllMedia();
    };
  }, [enabled, mindquestId, onQuestUpdated, playAgentSpeech, stopAllMedia]);

  return {
    phase,
    messages,
    liveTranscript,
    audioLevels,
    silenceProgress,
    error,
    finishSpeaking,
    skipAgentSpeech,
    replayAgentSpeech,
    pauseListening,
    resumeListening: beginListening,
  };
}
