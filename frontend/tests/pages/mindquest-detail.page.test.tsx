import React from "react";
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

    // 1. Wait for TOPIC_SELECTED view and click "MindQuest beginnen"
    const startBtn = await screen.findByRole("button", { name: /MindQuest beginnen/i });
    fireEvent.click(startBtn);

    // 2. Active challenge appears
    expect(
      await screen.findByText("Welche Risiken birgt ein sofortiges Plastikverbot?")
    ).toBeInTheDocument();

    // 3. Enter response and submit
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
});
