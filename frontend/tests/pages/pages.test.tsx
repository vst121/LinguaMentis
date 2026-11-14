import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import HomePage from "@/app/page";
import MindQuestsPage from "@/app/mindquests/page";
import ReflectionPage from "@/app/mindquests/[id]/reflection/page";
import LearningPage from "@/app/learning/page";
import HistoryPage from "@/app/history/page";
import * as mqApi from "@/services/api/mindquests";
import * as learningApi from "@/services/api/learning";
import { mockPush } from "../setup";

vi.mock("@/services/api/mindquests");
vi.mock("@/services/api/learning");

describe("Frontend pages (Home, MindQuests list, Reflection, Learning, History)", () => {
  it("renders HomePage hero and CTA links", () => {
    render(<HomePage />);
    expect(
      screen.getByText(/Denk klarer\. Drück dich auf Deutsch sicherer aus\./i)
    ).toBeInTheDocument();
    expect(screen.getByText(/MindQuest starten/i)).toBeInTheDocument();
  });

  it("MindQuestsPage loads list, creates a new MindQuest, and navigates to detail page", async () => {
    vi.mocked(mqApi.listMindQuests).mockResolvedValueOnce([
      {
        id: "mq-1",
        user_id: "u-1",
        topic: "KI in der Schule",
        target_level: "B2",
        status: "TOPIC_SELECTED",
        planned_hats: ["BLACK", "WHITE"],
        completed_hats: ["BLACK"],
        hat_rounds: [],
        created_at: "2026-11-14T10:00:00Z",
        updated_at: "2026-11-14T10:00:00Z",
      },
    ]);
    vi.mocked(mqApi.createMindQuest).mockResolvedValueOnce({
      id: "mq-new",
      user_id: "u-1",
      topic: "Grundeinkommen",
      target_level: "C1",
      status: "TOPIC_SELECTED",
      planned_hats: ["BLACK"],
      completed_hats: [],
      hat_rounds: [],
      created_at: "2026-11-14T10:00:00Z",
      updated_at: "2026-11-14T10:00:00Z",
    });

    render(<MindQuestsPage />);
    expect(await screen.findByText("KI in der Schule")).toBeInTheDocument();
    expect(screen.getByText(/1 von 2 Perspektiven abgeschlossen/i)).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Soll KI Hausaufgaben bewerten/i);
    fireEvent.change(input, { target: { value: "Grundeinkommen" } });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "C1" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(mqApi.createMindQuest).toHaveBeenCalledWith({
        topic: "Grundeinkommen",
        target_level: "C1",
      });
      expect(mockPush).toHaveBeenCalledWith("/mindquests/mq-new");
    });
  });

  it("ReflectionPage renders thinking and german summaries or error on failure", async () => {
    vi.mocked(mqApi.getFinalReflection).mockResolvedValueOnce({
      id: "r-1",
      mindquest_id: "mq-123",
      thinking_summary: "Starke Risikoanalyse im Schwarzen Hut.",
      german_summary: "Solider B2-Satzbau mit klarer Struktur.",
      thinking_section: {
        overall_summary: "Starke Risikoanalyse",
        recommendations: ["Mehr Gegenbeispiele einbauen"],
      },
      german_section: {
        overall_summary: "Solider B2-Satzbau",
        level_recommendations: ["Konjunktiv II üben"],
      },
      closing_message: "Großartige Debatte!",
    });

    render(<ReflectionPage />);
    expect(await screen.findByText("Großartige Debatte!")).toBeInTheDocument();
    expect(screen.getByText("Starke Risikoanalyse im Schwarzen Hut.")).toBeInTheDocument();
    expect(screen.getByText("Solider B2-Satzbau mit klarer Struktur.")).toBeInTheDocument();
    expect(screen.getByText(/Mehr Gegenbeispiele einbauen/i)).toBeInTheDocument();
    expect(screen.getByText(/Konjunktiv II üben/i)).toBeInTheDocument();
  });

  it("LearningPage displays overall scores and dimension breakdowns", async () => {
    vi.mocked(learningApi.getLearningProfile).mockResolvedValueOnce({
      user_id: "u-1",
      mindquests_completed: 3,
      thinking_overall: 82.5,
      german_overall: 79.0,
      thinking_dimensions: [{ name: "reasoning", score: 85 }],
      german_dimensions: [{ name: "grammar", score: 80 }],
      strongest_thinking_dimension: "reasoning",
      weakest_thinking_dimension: "depth",
      strongest_german_dimension: "grammar",
      weakest_german_dimension: "naturalness",
    });

    render(<LearningPage />);
    expect(await screen.findByText("82.5")).toBeInTheDocument();
    expect(screen.getByText("79")).toBeInTheDocument();
    expect(screen.getByText("Argumentation")).toBeInTheDocument();
    expect(screen.getByText("Grammatik")).toBeInTheDocument();
  });

  it("HistoryPage renders completed MindQuests and activity timeline", async () => {
    vi.mocked(learningApi.getUserMindQuests).mockResolvedValueOnce([
      {
        id: "mq-1",
        user_id: "u-1",
        topic: "Homeoffice-Pflicht",
        target_level: "B2",
        status: "COMPLETED",
        planned_hats: ["BLACK"],
        completed_hats: ["BLACK"],
        hat_rounds: [],
        created_at: "2026-11-14T10:00:00Z",
        updated_at: "2026-11-14T10:00:00Z",
      },
    ]);
    vi.mocked(learningApi.getUserActivities).mockResolvedValueOnce([
      {
        id: "act-1",
        user_id: "u-1",
        activity_type: "MindQuestCompleted",
        mindquest_id: "mq-1",
        payload: {},
        created_at: "2026-11-14T10:05:00Z",
      },
    ]);

    render(<HistoryPage />);
    expect(await screen.findByText("Homeoffice-Pflicht")).toBeInTheDocument();
    expect(screen.getByText("Mind Quest Completed")).toBeInTheDocument();
  });
});
