"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { transcribeAudio } from "@/services/api/speech";

export type InputMode = "typing" | "speaking";

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

export function useSpeechToText(onAppend: (text: string) => void) {
  const [mode, setMode] = useState<InputMode>("typing");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [interimText, setInterimText] = useState("");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [audioLevels, setAudioLevels] = useState<number[]>([0.3, 0.55, 0.8, 0.5, 0.35]);
  const [speechError, setSpeechError] = useState("");

  const recRef = useRef<SpeechRecognitionLike | null>(null);
  const mediaRecRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const webSpeechOkRef = useRef(false);
  const interimRef = useRef("");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const levelRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onAppendRef = useRef(onAppend);

  useEffect(() => {
    onAppendRef.current = onAppend;
  }, [onAppend]);

  const cleanup = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (levelRef.current) clearInterval(levelRef.current);
    timerRef.current = null;
    levelRef.current = null;
    if (recRef.current) {
      try {
        recRef.current.onresult = null;
        recRef.current.onerror = null;
        recRef.current.onend = null;
        recRef.current.stop();
      } catch {}
      recRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }, []);

  const stopRecording = useCallback(async () => {
    setIsRecording(false);
    setMode("typing");

    // 1. Gracefully stop SpeechRecognition and wait briefly for its final onresult/onend
    const activeRec = recRef.current;
    if (activeRec) {
      await new Promise<void>((resolve) => {
        const timeout = setTimeout(resolve, 220);
        activeRec.onend = () => {
          clearTimeout(timeout);
          resolve();
        };
        try {
          activeRec.stop();
        } catch {
          clearTimeout(timeout);
          resolve();
        }
      });
    }

    // 2. If interim speech was captured but not marked isFinal before stop, commit it now
    if (interimRef.current.trim()) {
      webSpeechOkRef.current = true;
      onAppendRef.current(interimRef.current.trim());
      interimRef.current = "";
    }
    setInterimText("");

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

    cleanup();

    if (!webSpeechOkRef.current && blob && blob.size > 0) {
      setIsTranscribing(true);
      try {
        const base64 = await blobToBase64(blob);
        if (base64) {
          const res = await transcribeAudio({
            audio_base64: base64,
            mime_type: blob.type || "audio/webm",
          });
          if (res.text.trim()) onAppendRef.current(res.text.trim());
        }
      } catch {
        setSpeechError("Sprachaufnahme konnte nicht transkribiert werden.");
      } finally {
        setIsTranscribing(false);
      }
    }
  }, [cleanup]);

  const startRecording = useCallback(async () => {
    setSpeechError("");
    setInterimText("");
    interimRef.current = "";
    setElapsedSeconds(0);
    webSpeechOkRef.current = false;
    chunksRef.current = [];

    const SpeechCtor = getSpeechCtor();
    let hasStream = false;

    if (typeof navigator !== "undefined" && navigator.mediaDevices?.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;
        hasStream = true;
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
      } catch {
        if (!SpeechCtor) {
          setSpeechError("Mikrofonzugriff wurde verweigert.");
          return;
        }
      }
    } else if (!SpeechCtor) {
      setSpeechError("Spracheingabe wird nicht unterstützt.");
      return;
    }

    if (SpeechCtor) {
      try {
        const rec = new SpeechCtor();
        rec.lang = "de-DE";
        rec.continuous = true;
        rec.interimResults = true;
        rec.onresult = (ev) => {
          let finalTxt = "";
          let interimTxt = "";
          for (let i = ev.resultIndex; i < ev.results.length; i += 1) {
            const r = ev.results[i];
            const t = r[0]?.transcript || "";
            if (r.isFinal) finalTxt += t;
            else interimTxt += t;
          }
          if (finalTxt.trim()) {
            webSpeechOkRef.current = true;
            interimRef.current = "";
            onAppendRef.current(finalTxt.trim());
          } else {
            interimRef.current = interimTxt.trim();
          }
          setInterimText(interimTxt.trim());
        };
        rec.onerror = (ev) => {
          if (ev.error === "not-allowed" && !hasStream) {
            setSpeechError("Mikrofonfreigabe blockiert.");
            void stopRecording();
          }
        };
        rec.start();
        recRef.current = rec;
      } catch {}
    }

    setMode("speaking");
    setIsRecording(true);
    timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
    levelRef.current = setInterval(() => {
      setAudioLevels((prev) =>
        prev.map((_, i) => Number((0.25 + ((Date.now() / 160 + i * 0.9) % 0.7)).toFixed(2)))
      );
    }, 180);
  }, [stopRecording]);

  useEffect(() => () => cleanup(), [cleanup]);

  return {
    mode,
    isRecording,
    isTranscribing,
    interimText,
    elapsedSeconds,
    audioLevels,
    speechError,
    startRecording,
    stopRecording,
  };
}

