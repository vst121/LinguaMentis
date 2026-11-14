import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MindQuestPage from "@/app/mindquests/[id]/page";
import MindQuestsPage from "@/app/mindquests/page";
import HistoryPage from "@/app/history/page";
import * as mqApi from "@/services/api/mindquests";
import * as learningApi from "@/services/api/learning";
import { MindQuest, SubmitResponseResponse } from "@/types/mindquest";
import { mockPrefetch } from "../setup";

vi.mock("@/services/api/mindquests");
vi.mock("@/services/api/learning");

const activeTurn = {
  id: "turn-1",
  turn_number: 1,
  hat: "BLACK" as const,
  challenge_question: "Welche Risiken entstehen durch KI-Überwachung?",
  challenge_instruction: "Bleib strikt beim Schwarzen Hut.",
  difficulty: 3,
  created_at: "2026-11-14T10:01:00Z",
};

const activeQuest: MindQuest = {
  id: "mq-123",
  user_id: "u-1",
  topic: "KI im öffentlichen Raum",
  target_level: "B2",
  status: "HAT_ACTIVE",
  current_hat: "BLACK",
  planned_hats: ["BLACK"],
  completed_hats: [],
  hat_rounds: [
    {
      id: "round-1",
      hat: "BLACK",
      sequence_index: 0,
      turns: [activeTurn],
      started_at: "2026-11-14T10:01:00Z",
    },
  ],
  created_at: "2026-11-14T10:00:00Z",
  updated_at: "2026-11-14T10:00:00Z",
};

const makeEval = (done: boolean, nextQ?: string) => ({
  turn: { ...activeTurn, user_response: "Antwort." },
  thinking_evaluation: {
    id: "te-1",
    score: done ? 82 : 60,
    score_anchor: "Good",
    hat_adherence: 75,
    relevance: 75,
    reasoning: 75,
    depth: 75,
    specificity: 75,
    evidence: [],
    strengths: [],
    weaknesses: [],
    recommendations: [],
  },
  german_evaluation: {
    id: "ge-1",
    score: 82,
    score_anchor: "Strong",
    grammar: 85,
    vocabulary: 80,
    sentence_structure: 80,
    naturalness: 80,
    level_appropriateness: 85,
    evidence: [],
    corrections: [],
    strengths: [],
    weaknesses: [],
    recommendations: [],
  },
  feedback: {
    thinking_feedback: "Guter Punkt.",
    german_feedback: "Sprachlich klar.",
    encouragement: "Weiter!",
  },
  next_challenge_question: nextQ,
  next_challenge_instruction: nextQ ? "Nenne ein Beispiel." : undefined,
  round_should_complete: done,
});

describe("Frontend Speed & Responsiveness Tests", () => {
  it("transitions to follow-up intra-hat challenge in < 35ms with ZERO extra HTTP calls", async () => {
    vi.mocked(mqApi.getMindQuest).mockResolvedValueOnce(activeQuest);
    vi.mocked(mqApi.submitResponse).mockResolvedValueOnce(
      makeEval(false, "Welches Grundrecht ist konkret gefährdet?")
    );

    render(<MindQuestPage />);
    await waitFor(() => {
      expect(mockPrefetch).toHaveBeenCalledWith("/mindquests/mq-123/reflection");
    });

    const textarea = await screen.findByPlaceholderText(/Schreibe deine Antwort hier/i);
    fireEvent.change(textarea, { target: { value: "Kurze Antwort." } });
    fireEvent.click(screen.getByRole("button", { name: /Antwort auswerten/i }));

    const nextBtn = await screen.findByRole("button", {
      name: /Nächste Herausforderung/i,
    });
    vi.mocked(mqApi.getMindQuest).mockClear();
    vi.mocked(mqApi.advanceMindQuest).mockClear();

    const t0 = performance.now();
    fireEvent.click(nextBtn);
    expect(screen.getByText("Welches Grundrecht ist konkret gefährdet?")).toBeInTheDocument();
    expect(performance.now() - t0).toBeLessThan(35);
    expect(mqApi.getMindQuest).not.toHaveBeenCalled();
    expect(mqApi.advanceMindQuest).not.toHaveBeenCalled();
  });

  it("renders optimistic pending state immediately (< 35ms) while slow AI request is in flight", async () => {
    vi.mocked(mqApi.getMindQuest).mockResolvedValueOnce(activeQuest);
    let resolveSubmit!: (value: SubmitResponseResponse) => void;
    vi.mocked(mqApi.submitResponse).mockImplementationOnce(
      () =>
        new Promise<SubmitResponseResponse>((r) => {
          resolveSubmit = r;
        })
    );

    render(<MindQuestPage />);
    const textarea = await screen.findByPlaceholderText(/Schreibe deine Antwort hier/i);
    fireEvent.change(textarea, { target: { value: "Sofort sichtbare Antwort." } });

    const t0 = performance.now();
    fireEvent.click(screen.getByRole("button", { name: /Antwort auswerten/i }));

    expect(screen.getByText("Sofort sichtbare Antwort.")).toBeInTheDocument();
    expect(screen.getByText(/Auswertung läuft/i)).toBeInTheDocument();
    expect(performance.now() - t0).toBeLessThan(35);

    resolveSubmit(makeEval(true));
    await screen.findByText("Dein Feedback");
  });

  it("fetches HistoryPage concurrently via Promise.all and renders 50 items under 180ms", async () => {
    const fiftyQuests: MindQuest[] = Array.from({ length: 50 }, (_, i) => ({
      ...activeQuest,
      id: `mq-${i}`,
      topic: `Debattenthema Nummer ${i + 1}`,
      status: "COMPLETED",
      completed_hats: ["BLACK"],
    }));

    vi.mocked(mqApi.listMindQuests).mockResolvedValueOnce(fiftyQuests);

    const tRender0 = performance.now();
    const { unmount } = render(<MindQuestsPage />);
    expect(await screen.findByText("Debattenthema Nummer 50")).toBeInTheDocument();
    expect(performance.now() - tRender0).toBeLessThan(180);
    unmount();

    const delay = 90;
    vi.mocked(learningApi.getUserMindQuests).mockImplementationOnce(
      () => new Promise((r) => setTimeout(() => r(fiftyQuests.slice(0, 10)), delay))
    );
    vi.mocked(learningApi.getUserActivities).mockImplementationOnce(
      () => new Promise((r) => setTimeout(() => r([]), delay))
    );

    const tHist0 = performance.now();
    render(<HistoryPage />);
    expect(await screen.findByText("Debattenthema Nummer 1")).toBeInTheDocument();
    expect(performance.now() - tHist0).toBeLessThan(delay * 1.85);
  });
});
