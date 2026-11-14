import React, { act } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MindQuestPage from "@/app/mindquests/[id]/page";
import * as mqApi from "@/services/api/mindquests";
import { MindQuest } from "@/types/mindquest";
import { mockReplace } from "../setup";

vi.mock("@/services/api/mindquests");

const baseQuest: MindQuest = {
  id: "mq-123",
  user_id: "u-1",
  topic: "Plastikverbot in Supermärkten",
  target_level: "B2",
  status: "TOPIC_SELECTED",
  current_hat: null,
  planned_hats: ["BLACK"],
  completed_hats: [],
  hat_rounds: [],
  created_at: "2026-11-14T10:00:00Z",
  updated_at: "2026-11-14T10:00:00Z",
};

describe("MindQuestPage interactive flow", () => {
  it("starts a MindQuest, submits a German response, renders independent Thinking & German evaluations, and advances to reflection", async () => {
    vi.mocked(mqApi.getMindQuest).mockResolvedValueOnce(baseQuest);

    const activeTurn = {
      id: "turn-1",
      turn_number: 1,
      hat: "BLACK" as const,
      challenge_question: "Welche Risiken birgt ein sofortiges Plastikverbot?",
      challenge_instruction: "Fokussiere dich auf negative Folgen.",
      difficulty: 3,
      created_at: "2026-11-14T10:01:00Z",
    };

    vi.mocked(mqApi.startMindQuest).mockResolvedValueOnce({
      mindquest: {
        ...baseQuest,
        status: "HAT_ACTIVE",
        current_hat: "BLACK",
        hat_rounds: [
          {
            id: "round-1",
            hat: "BLACK",
            sequence_index: 0,
            turns: [activeTurn],
            started_at: "2026-11-14T10:01:00Z",
          },
        ],
      },
      active_hat: "BLACK",
      initial_turn: activeTurn,
      challenge_question: activeTurn.challenge_question,
      challenge_instruction: activeTurn.challenge_instruction,
      difficulty: 3,
    });

    vi.mocked(mqApi.submitResponse).mockResolvedValueOnce({
      turn: {
        ...activeTurn,
        user_response: "Haltbarkeit von Lebensmitteln könnte sinken.",
        responded_at: "2026-11-14T10:02:00Z",
      },
      thinking_evaluation: {
        id: "te-1",
        score: 86,
        score_anchor: "Strong",
        hat_adherence: 90,
        relevance: 85,
        reasoning: 88,
        depth: 80,
        specificity: 84,
        evidence: [],
        strengths: ["Klares Risiko"],
        weaknesses: [],
        recommendations: [],
      },
      german_evaluation: {
        id: "ge-1",
        score: 78,
        score_anchor: "Good",
        grammar: 80,
        vocabulary: 78,
        sentence_structure: 80,
        naturalness: 75,
        level_appropriateness: 78,
        evidence: [],
        corrections: [
          {
            original: "Haltbarkeit von Lebensmitteln",
            corrected: "Die Haltbarkeit von Lebensmitteln",
            explanation: "Bestimmter Artikel am Satzanfang.",
            category: "grammar",
          },
        ],
        strengths: [],
        weaknesses: [],
        recommendations: [],
      },
      feedback: {
        thinking_feedback: "Sehr gute Risikoanalyse zur Lieferkette.",
        german_feedback: "Achte auf Artikel am Satzanfang.",
        encouragement: "Weiter so!",
      },
      proposition: {
        id: "prop-1",
        improved_response:
          "Ein gravierendes Risiko besteht darin, dass die Haltbarkeit von Lebensmitteln erheblich sinkt.",
        highlights: [
          {
            upgraded_phrase: "Ein gravierendes Risiko besteht darin",
            original_phrase: "",
            explanation: "Stilistisch gehobene Argumentationseinleitung.",
            category: "syntax",
          },
          {
            upgraded_phrase: "erheblich sinkt",
            original_phrase: "könnte sinken",
            explanation: "Präziseres Adverb zur Verstärkung der Aussage.",
            category: "vocabulary",
          },
        ],
      },
      round_should_complete: true,
    });

    vi.mocked(mqApi.advanceMindQuest).mockResolvedValueOnce({
      mindquest: { ...baseQuest, status: "COMPLETED", completed_hats: ["BLACK"] },
      is_completed: true,
      final_reflection: {
        id: "refl-1",
        mindquest_id: "mq-123",
        thinking_summary: "Starke Risikoanalyse.",
        german_summary: "Klare Ausdrucksweise auf B2-Niveau.",
        thinking_section: { overall_summary: "Gut", recommendations: [] },
        german_section: { overall_summary: "Gut", level_recommendations: [] },
        closing_message: "Weiter so!",
      },
    });

    render(<MindQuestPage />);

    // 1. Auto-starts immediately without an intermediate "Bereit für deine erste Perspektive" step
    expect(
      await screen.findByText("Welche Risiken birgt ein sofortiges Plastikverbot?")
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Bereit für deine erste Perspektive")
    ).not.toBeInTheDocument();

    // 2. Enter response and submit
    const textarea = screen.getByPlaceholderText(/Schreibe deine Antwort hier/i);
    fireEvent.change(textarea, {
      target: { value: "Haltbarkeit von Lebensmitteln könnte sinken." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Antwort auswerten/i }));

    // 4. Verify Thinking & German evaluations and corrections appear
    expect(
      await screen.findByText("Sehr gute Risikoanalyse zur Lieferkette.")
    ).toBeInTheDocument();
    expect(screen.getByText("Achte auf Artikel am Satzanfang.")).toBeInTheDocument();
    expect(screen.getByText("Die Haltbarkeit von Lebensmitteln")).toBeInTheDocument();
    expect(screen.getByText("86 / 100")).toBeInTheDocument();
    expect(screen.getAllByText("78 / 100").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByRole("img", { name: "Radar-Diagramm Denken" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Radar-Diagramm Deutsch" })
    ).toBeInTheDocument();
    expect(screen.getByText("Relevanz")).toBeInTheDocument();
    expect(screen.getByText("Niveau-Passung")).toBeInTheDocument();
    expect(
      screen.getByText("Sprach-Upgrade: Elaborierte Antwort")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Stilistisch gehobene Argumentationseinleitung.")
    ).toBeInTheDocument();

    // 5. Click "Abschlussreflexion ansehen" to advance to reflection
    fireEvent.click(
      screen.getByRole("button", { name: /Abschlussreflexion ansehen|Nächste Perspektive/i })
    );
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/mindquests/mq-123/reflection");
    });
  });

  it("restores draft and displays error message when submitting a response fails", async () => {
    const activeTurn = {
      id: "turn-1",
      turn_number: 1,
      hat: "BLACK" as const,
      challenge_question: "Welche Risiken siehst du?",
      challenge_instruction: "Bleib beim Schwarzen Hut.",
      difficulty: 3,
      created_at: "2026-11-14T10:01:00Z",
    };

    vi.mocked(mqApi.getMindQuest).mockResolvedValueOnce({
      ...baseQuest,
      status: "HAT_ACTIVE",
      current_hat: "BLACK",
      hat_rounds: [
        {
          id: "round-1",
          hat: "BLACK",
          sequence_index: 0,
          turns: [activeTurn],
          started_at: "2026-11-14T10:01:00Z",
        },
      ],
    });
    vi.mocked(mqApi.submitResponse).mockRejectedValueOnce(new Error("Network error"));

    render(<MindQuestPage />);

    const textarea = await screen.findByPlaceholderText(/Schreibe deine Antwort hier/i);
    fireEvent.change(textarea, { target: { value: "Entwurf bleibt erhalten" } });
    fireEvent.click(screen.getByRole("button", { name: /Antwort auswerten/i }));

    expect(
      await screen.findByText("Deine Antwort konnte nicht gesendet werden.")
    ).toBeInTheDocument();
    expect(textarea).toHaveValue("Entwurf bleibt erhalten");
  });

  it("redirects immediately to reflection when opening an already COMPLETED MindQuest and counts words accurately", async () => {
    vi.mocked(mqApi.getMindQuest).mockResolvedValueOnce({
      ...baseQuest,
      status: "COMPLETED",
    });

    const { unmount } = render(<MindQuestPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/mindquests/mq-123/reflection");
    });
    unmount();

    // Multi-hat word count and Shift+Enter check
    const activeTurn = {
      id: "turn-1",
      turn_number: 1,
      hat: "BLACK" as const,
      challenge_question: "Welche Risiken?",
      challenge_instruction: "Nur Risiken.",
      difficulty: 2,
      created_at: "2026-11-14T10:01:00Z",
    };
    vi.mocked(mqApi.getMindQuest).mockResolvedValueOnce({
      ...baseQuest,
      status: "HAT_ACTIVE",
      current_hat: "BLACK",
      planned_hats: ["BLACK", "YELLOW"],
      hat_rounds: [
        {
          id: "round-1",
          hat: "BLACK",
          sequence_index: 0,
          turns: [activeTurn],
          started_at: "2026-11-14T10:01:00Z",
        },
      ],
    });

    render(<MindQuestPage />);
    const textarea = await screen.findByPlaceholderText(/Schreibe deine Antwort hier/i);
    expect(screen.getByText("0 Wörter")).toBeInTheDocument();

    fireEvent.change(textarea, {
      target: { value: "Vier   klare   deutsche   Wörter" },
    });
    expect(screen.getByText("4 Wörter")).toBeInTheDocument();

    // Shift+Enter does not trigger submitResponse
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });
    expect(mqApi.submitResponse).not.toHaveBeenCalled();
  });

  it("switches between Eintippen and Einsprechen on click, shows visual recording indicator, and inserts spoken German text", async () => {
    let recognitionInstance: {
      onresult: ((ev: unknown) => void) | null;
      start: ReturnType<typeof vi.fn>;
      stop: ReturnType<typeof vi.fn>;
    } | null = null;

    class MockSpeechRecognition {
      lang = "";
      continuous = false;
      interimResults = false;
      onresult: ((ev: unknown) => void) | null = null;
      onerror: ((ev: unknown) => void) | null = null;
      onend: (() => void) | null = null;
      start = vi.fn();
      stop = vi.fn();
      constructor() {
        // eslint-disable-next-line @typescript-eslint/no-this-alias
        recognitionInstance = this;
      }
    }

    (window as unknown as Record<string, unknown>).webkitSpeechRecognition =
      MockSpeechRecognition;

    const activeTurn = {
      id: "turn-1",
      turn_number: 1,
      hat: "WHITE" as const,
      challenge_question: "Welche Fakten kennen wir?",
      challenge_instruction: "Nur belegbare Daten.",
      difficulty: 2,
      created_at: "2026-11-14T10:01:00Z",
    };

    vi.mocked(mqApi.getMindQuest).mockResolvedValueOnce({
      ...baseQuest,
      status: "HAT_ACTIVE",
      current_hat: "WHITE",
      hat_rounds: [
        {
          id: "round-1",
          hat: "WHITE",
          sequence_index: 0,
          turns: [activeTurn],
          started_at: "2026-11-14T10:01:00Z",
        },
      ],
    });

    render(<MindQuestPage />);
    const speakBtn = await screen.findByRole("button", { name: /Einsprechen/i });
    const typeBtn = screen.getByRole("button", { name: /Eintippen/i });
    expect(typeBtn).toHaveAttribute("aria-pressed", "true");
    expect(speakBtn).toHaveAttribute("aria-pressed", "false");

    // 1. Click "Einsprechen" -> switches to speaking mode and shows visual recording indicator
    fireEvent.click(speakBtn);
    expect(await screen.findByTestId("recording-indicator")).toBeInTheDocument();
    expect(screen.getByText(/Mikrofon nimmt auf/i)).toBeInTheDocument();
    expect(screen.getByTestId("audio-level-bars")).toBeInTheDocument();
    expect(speakBtn).toHaveAttribute("aria-pressed", "true");

    // 2. Simulate spoken German result from SpeechRecognition
    act(() => {
      recognitionInstance!.onresult!({
        resultIndex: 0,
        results: {
          length: 1,
          0: {
            isFinal: true,
            0: { transcript: "Die Statistik zeigt einen Anstieg um zehn Prozent." },
          },
        },
      });
    });

    const textarea = screen.getByPlaceholderText(/Sprich jetzt ins Mikrofon/i);
    await waitFor(() => {
      expect(textarea).toHaveValue("Die Statistik zeigt einen Anstieg um zehn Prozent.");
    });

    // 3. Click "Eintippen" -> stops recording, indicator disappears, text remains editable
    fireEvent.click(typeBtn);
    await waitFor(() => {
      expect(screen.queryByTestId("recording-indicator")).not.toBeInTheDocument();
    });
    expect(typeBtn).toHaveAttribute("aria-pressed", "true");
    expect(textarea).toHaveValue("Die Statistik zeigt einen Anstieg um zehn Prozent.");

    delete (window as unknown as Record<string, unknown>).webkitSpeechRecognition;
  });

  it("Argue Mode switches to dark theme, allows hat switching via top-left pills preserving state, shows solved hats read-only, and finishes on last hat", async () => {
    const argueQuest: MindQuest = {
      id: "mq-argue",
      user_id: "u-1",
      topic: "Tempolimit auf Autobahnen",
      target_level: "C1",
      mode: "ARGUE",
      status: "TOPIC_SELECTED",
      current_hat: null,
      planned_hats: ["WHITE", "YELLOW", "GREEN", "RED", "BLACK"],
      completed_hats: [],
      hat_rounds: [],
      created_at: "2026-11-14T10:00:00Z",
      updated_at: "2026-11-14T10:00:00Z",
    };

    const blackTurn = {
      id: "t-argue-1",
      turn_number: 1,
      hat: "BLACK" as const,
      challenge_question: "Welche Risiken hat ein generelles Tempolimit?",
      challenge_instruction: "Bleibe beim Schwarzen Hut.",
      difficulty: 4,
      created_at: "2026-11-14T10:01:00Z",
    };

    const whiteTurn = {
      id: "t-argue-w1",
      turn_number: 1,
      hat: "WHITE" as const,
      challenge_question: "Welche Fakten gibt es zum Tempolimit?",
      challenge_instruction: "Nur gesicherte Fakten.",
      difficulty: 4,
      created_at: "2026-11-14T10:02:00Z",
    };

    vi.mocked(mqApi.getMindQuest).mockResolvedValueOnce(argueQuest);
    // 1. Select BLACK initially
    vi.mocked(mqApi.selectHat).mockResolvedValueOnce({
      mindquest: {
        ...argueQuest,
        status: "HAT_ACTIVE",
        current_hat: "BLACK",
        hat_rounds: [
          {
            id: "r-argue-1",
            hat: "BLACK",
            sequence_index: 0,
            turns: [blackTurn],
            started_at: "2026-11-14T10:01:00Z",
          },
        ],
      },
      active_hat: "BLACK",
      initial_turn: blackTurn,
      challenge_question: blackTurn.challenge_question,
      challenge_instruction: blackTurn.challenge_instruction,
      difficulty: 4,
      is_read_only: false,
    });
    // 2. Switch mid-debate to WHITE via top-left pill
    vi.mocked(mqApi.selectHat).mockResolvedValueOnce({
      mindquest: {
        ...argueQuest,
        status: "HAT_ACTIVE",
        current_hat: "WHITE",
        hat_rounds: [
          {
            id: "r-argue-1",
            hat: "BLACK",
            sequence_index: 0,
            turns: [{ ...blackTurn, user_response: "Es gibt Staus." }],
            started_at: "2026-11-14T10:01:00Z",
          },
          {
            id: "r-argue-w",
            hat: "WHITE",
            sequence_index: 1,
            turns: [whiteTurn],
            started_at: "2026-11-14T10:02:00Z",
          },
        ],
      },
      active_hat: "WHITE",
      initial_turn: whiteTurn,
      challenge_question: whiteTurn.challenge_question,
      challenge_instruction: whiteTurn.challenge_instruction,
      difficulty: 4,
      is_read_only: false,
    });
    // 3. Switch back to BLACK -> preserves Turn 2 counter-argument & previous answer
    const blackTurn2 = {
      ...blackTurn,
      turn_number: 2,
      challenge_question: "Das überzeugt noch nicht: Welche konkreten volkswirtschaftlichen Folgen entstehen?",
      challenge_instruction: "Belege deine Kritik mit einem konkreten Mechanismus.",
    };
    vi.mocked(mqApi.selectHat).mockResolvedValueOnce({
      mindquest: {
        ...argueQuest,
        status: "HAT_ACTIVE",
        current_hat: "BLACK",
      },
      active_hat: "BLACK",
      initial_turn: blackTurn2,
      challenge_question: blackTurn2.challenge_question,
      challenge_instruction: blackTurn2.challenge_instruction,
      difficulty: 4,
      is_read_only: false,
      last_evaluation: {
        turn: { ...blackTurn, user_response: "Es gibt Staus." },
        average_score: 65,
      },
    });
    // 4. Inspect completed BLACK hat later -> read-only view with scores
    vi.mocked(mqApi.selectHat).mockResolvedValueOnce({
      mindquest: {
        ...argueQuest,
        status: "HAT_COMPLETED",
        current_hat: "BLACK",
        completed_hats: ["BLACK"],
      },
      active_hat: "BLACK",
      initial_turn: blackTurn2,
      challenge_question: blackTurn2.challenge_question,
      challenge_instruction: blackTurn2.challenge_instruction,
      difficulty: 4,
      is_read_only: true,
      last_evaluation: {
        turn: {
          ...blackTurn2,
          user_response: "Ein zentrales Risiko liegt in höheren Transportkosten durch längere Fahrzeiten.",
        },
        thinking_evaluation: {
          id: "te-a2",
          score: 88,
          score_anchor: "Strong",
          hat_adherence: 90,
          relevance: 88,
          reasoning: 88,
          depth: 85,
          specificity: 89,
          evidence: [],
          strengths: ["Starkes Risikoargument."],
          weaknesses: [],
          recommendations: [],
        },
        german_evaluation: {
          id: "ge-a2",
          score: 86,
          score_anchor: "Strong",
          grammar: 86,
          vocabulary: 86,
          sentence_structure: 86,
          naturalness: 86,
          level_appropriateness: 86,
          evidence: [],
          corrections: [],
          strengths: ["Überzeugendes C1-Deutsch."],
          weaknesses: [],
          recommendations: [],
        },
        average_score: 87,
      },
    });

    // First attempt fails <= 80% -> Perspective Challenger rejection
    vi.mocked(mqApi.submitResponse).mockResolvedValueOnce({
      turn: { ...blackTurn, user_response: "Es gibt Staus." },
      thinking_evaluation: {
        id: "te-a1",
        score: 60,
        score_anchor: "Adequate",
        hat_adherence: 65,
        relevance: 60,
        reasoning: 55,
        depth: 55,
        specificity: 65,
        evidence: [],
        strengths: [],
        weaknesses: [],
        recommendations: [],
      },
      german_evaluation: {
        id: "ge-a1",
        score: 70,
        score_anchor: "Good",
        grammar: 70,
        vocabulary: 70,
        sentence_structure: 70,
        naturalness: 70,
        level_appropriateness: 70,
        evidence: [],
        corrections: [],
        strengths: [],
        weaknesses: [],
        recommendations: [],
      },
      feedback: {
        thinking_feedback: "Zu allgemein.",
        german_feedback: "Zu knapp formuliert.",
        encouragement: "Schärfe dein Argument.",
      },
      average_score: 65,
      next_challenge_question: blackTurn2.challenge_question,
      next_challenge_instruction: blackTurn2.challenge_instruction,
      round_should_complete: false,
    });

    // Second attempt succeeds > 80%
    vi.mocked(mqApi.submitResponse).mockResolvedValueOnce({
      turn: {
        ...blackTurn2,
        user_response: "Ein zentrales Risiko liegt in höheren Transportkosten durch längere Fahrzeiten.",
      },
      thinking_evaluation: {
        id: "te-a2",
        score: 88,
        score_anchor: "Strong",
        hat_adherence: 90,
        relevance: 88,
        reasoning: 88,
        depth: 85,
        specificity: 89,
        evidence: [],
        strengths: [],
        weaknesses: [],
        recommendations: [],
      },
      german_evaluation: {
        id: "ge-a2",
        score: 86,
        score_anchor: "Strong",
        grammar: 86,
        vocabulary: 86,
        sentence_structure: 86,
        naturalness: 86,
        level_appropriateness: 86,
        evidence: [],
        corrections: [],
        strengths: [],
        weaknesses: [],
        recommendations: [],
      },
      feedback: {
        thinking_feedback: "Starkes Risikoargument.",
        german_feedback: "Überzeugendes C1-Deutsch.",
        encouragement: "Geschafft!",
      },
      average_score: 87,
      round_should_complete: true,
    });

    render(<MindQuestPage />);

    // 1. Dark theme active and 5 hats visible (Blauer Hut must NOT be present)
    expect(
      await screen.findByText(/Perspektive wählen \(Argue Mode\)/i)
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(document.documentElement.classList.contains("dark")).toBe(true);
    });
    expect(screen.getByText("Weißer Hut")).toBeInTheDocument();
    expect(screen.getByText("Gelber Hut")).toBeInTheDocument();
    expect(screen.getByText("Grüner Hut")).toBeInTheDocument();
    expect(screen.getByText("Roter Hut")).toBeInTheDocument();
    expect(screen.getByText("Schwarzer Hut")).toBeInTheDocument();
    expect(screen.queryByText("Blauer Hut")).not.toBeInTheDocument();

    // 2. Select Schwarzer Hut -> shows SpeechModeToggle & top-left active pill
    fireEvent.click(screen.getByTestId("hat-card-BLACK"));
    expect(
      await screen.findByText("Welche Risiken hat ein generelles Tempolimit?")
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Einsprechen/i })).toBeInTheDocument();
    expect(screen.getByTestId("hat-pill-BLACK")).toHaveAttribute(
      "aria-label",
      "Schwarzer Hut: aktuell"
    );

    // 3. Submit weak answer -> rejected (<= 80% for C1)
    fireEvent.change(screen.getByPlaceholderText(/Schreibe deine Antwort hier/i), {
      target: { value: "Es gibt Staus." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Antwort auswerten/i }));

    expect(
      await screen.findByText(/Abgelehnt \(65 % · Ziel > 80 %\)/i)
    ).toBeInTheDocument();

    // 4. Switch to WHITE via top-left pill mid-debate, then switch back to BLACK -> preserves Turn 2!
    fireEvent.click(screen.getByTestId("hat-pill-WHITE"));
    expect(
      await screen.findByText("Welche Fakten gibt es zum Tempolimit?")
    ).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("hat-pill-BLACK"));
    expect(
      await screen.findByText(blackTurn2.challenge_question)
    ).toBeInTheDocument();
    const textarea = screen.getByPlaceholderText(/Schreibe deine Antwort hier/i);
    expect(textarea).toHaveValue("Es gibt Staus.");

    // 5. Submit stronger response -> accepted (> 80%)
    fireEvent.change(textarea, {
      target: {
        value:
          "Ein zentrales Risiko liegt in höheren Transportkosten durch längere Fahrzeiten.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: /Antwort auswerten/i }));

    expect(
      await screen.findByText(/Akzeptiert \(87 % · Ziel > 80 %\)/i)
    ).toBeInTheDocument();

    // 6. Click "Nächste Perspektive" -> selector shows BLACK completed, still clickable to view score read-only
    fireEvent.click(screen.getByRole("button", { name: /Nächste Perspektive/i }));
    const blackCard = await screen.findByTestId("hat-card-BLACK");
    expect(blackCard).not.toBeDisabled();
    expect(screen.getByText(/Erledigt · Punktzahl ansehen/i)).toBeInTheDocument();

    fireEvent.click(blackCard);
    expect(
      (await screen.findAllByText(/Abgeschlossen · Nur Ansicht/i)).length
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("88 / 100")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/Schreibe deine Antwort hier/i)).not.toBeInTheDocument();
  });
});
