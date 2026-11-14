import React, { act } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MindQuestPage from "@/app/mindquests/[id]/page";
import * as mqApi from "@/services/api/mindquests";
import * as convApi from "@/services/api/conversation";
import { MindQuest } from "@/types/mindquest";

vi.mock("@/services/api/mindquests");
vi.mock("@/services/api/conversation");

const baseQuest: MindQuest = {
  id: "mq-123",
  user_id: "u-1",
  topic: "Homeoffice als Grundrecht",
  target_level: "B2",
  status: "TOPIC_SELECTED",
  current_hat: null,
  planned_hats: ["WHITE", "YELLOW"],
  completed_hats: [],
  hat_rounds: [],
  created_at: "2026-11-14T10:00:00Z",
  updated_at: "2026-11-14T10:00:00Z",
};

describe("Spoken Conversation Mode (ConversationAgent UI)", () => {
  it("switches to Gesprächsmodus, speaks opening, listens to German speech, and plays spoken agent reply", async () => {
    let recInstance: {
      onresult: ((ev: unknown) => void) | null;
      onend: (() => void) | null;
      start: ReturnType<typeof vi.fn>;
      stop: () => void;
    } | null = null;

    class MockSpeechRecognition {
      lang = "de-DE";
      continuous = true;
      interimResults = true;
      onresult: ((ev: unknown) => void) | null = null;
      onerror: ((ev: unknown) => void) | null = null;
      onend: (() => void) | null = null;
      start = vi.fn();
      stop() {
        if (this.onend) this.onend();
      }
      constructor() {
        // eslint-disable-next-line @typescript-eslint/no-this-alias
        recInstance = this;
      }
    }

    (window as unknown as Record<string, unknown>).SpeechRecognition =
      MockSpeechRecognition;

    const turn1 = {
      id: "t-1",
      turn_number: 1,
      hat: "WHITE" as const,
      challenge_question: "Welche Daten gibt es zur Produktivität im Homeoffice?",
      challenge_instruction: "Fakten nennen.",
      difficulty: 2,
      created_at: "2026-11-14T10:01:00Z",
    };

    vi.mocked(mqApi.getMindQuest).mockResolvedValueOnce(baseQuest);
    vi.mocked(convApi.openConversation).mockResolvedValueOnce({
      mindquest: { ...baseQuest, status: "HAT_ACTIVE", current_hat: "WHITE" },
      active_hat: "WHITE",
      active_turn: turn1,
      spoken_text: "Willkommen! Welche Daten gibt es zur Produktivität im Homeoffice?",
      audio_base64: "",
      audio_mime_type: "audio/wav",
      is_completed: false,
    });

    vi.mocked(convApi.submitConversationTurn).mockResolvedValueOnce({
      mindquest: {
        ...baseQuest,
        status: "HAT_ACTIVE",
        current_hat: "YELLOW",
        completed_hats: ["WHITE"],
      },
      user_transcript: "Studien zeigen eine konstante Produktivität.",
      spoken_reply: "Sehr guter Punkt! Schauen wir nun mit dem Gelben Hut auf die Chancen.",
      audio_base64: "",
      audio_mime_type: "audio/wav",
      thinking_evaluation: {
        id: "te-1",
        score: 84,
        score_anchor: "Strong",
        hat_adherence: 85,
        relevance: 85,
        reasoning: 84,
        depth: 80,
        specificity: 84,
        evidence: [],
        strengths: [],
        weaknesses: [],
        recommendations: [],
      },
      german_evaluation: {
        id: "ge-1",
        score: 88,
        score_anchor: "Strong",
        grammar: 90,
        vocabulary: 86,
        sentence_structure: 88,
        naturalness: 88,
        level_appropriateness: 88,
        evidence: [],
        corrections: [],
        strengths: [],
        weaknesses: [],
        recommendations: [],
      },
      active_hat: "YELLOW",
      transitioned_hat: "YELLOW",
      is_completed: false,
    });

    render(<MindQuestPage />);
    const startConvBtn = await screen.findByRole("button", {
      name: /Mündliches Gespräch starten/i,
    });
    fireEvent.click(startConvBtn);

    expect(await screen.findByTestId("conversation-view")).toBeInTheDocument();
    expect(
      await screen.findByText(/Mikrofon hört zu — sprich auf Deutsch/i)
    ).toBeInTheDocument();

    act(() => {
      recInstance!.onresult!({
        resultIndex: 0,
        results: {
          length: 1,
          0: {
            isFinal: true,
            0: { transcript: "Studien zeigen eine konstante Produktivität." },
          },
        },
      });
    });

    expect(
      await screen.findByTestId("live-spoken-transcript")
    ).toHaveTextContent("Studien zeigen eine konstante Produktivität.");

    fireEvent.click(screen.getByRole("button", { name: /Fertig gesprochen/i }));

    expect(
      await screen.findByText(
        "Sehr guter Punkt! Schauen wir nun mit dem Gelben Hut auf die Chancen."
      )
    ).toBeInTheDocument();
    expect(screen.getByText("Denken 84")).toBeInTheDocument();
    expect(screen.getByText("Deutsch 88")).toBeInTheDocument();

    delete (window as unknown as Record<string, unknown>).SpeechRecognition;
  });
});
