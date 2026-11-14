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
    expect(screen.getAllByText("Answering Mode").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/1 von 2 Perspektiven abgeschlossen/i)).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Soll KI Hausaufgaben bewerten/i);
    fireEvent.change(input, { target: { value: "Grundeinkommen" } });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "C1" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(mqApi.createMindQuest).toHaveBeenCalledWith({
        topic: "Grundeinkommen",
        target_level: "C1",
        mode: "ANSWERING",
      });
      expect(mockPush).toHaveBeenCalledWith("/mindquests/mq-new");
    });
  });

  it("MindQuestsPage toggles dark theme and creates an Argue Mode MindQuest", async () => {
    vi.mocked(mqApi.listMindQuests).mockResolvedValueOnce([]);
    vi.mocked(mqApi.createMindQuest).mockResolvedValueOnce({
      id: "mq-argue-1",
      user_id: "u-1",
      topic: "Tempolimit",
      target_level: "B2",
      mode: "ARGUE",
      status: "TOPIC_SELECTED",
      planned_hats: ["WHITE", "YELLOW", "GREEN", "RED", "BLACK"],
      completed_hats: [],
      hat_rounds: [],
      created_at: "2026-11-14T10:00:00Z",
      updated_at: "2026-11-14T10:00:00Z",
    });

    render(<MindQuestsPage />);
    expect(await screen.findByText(/Noch keine MindQuest/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: /Argue Mode/i }));
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    const input = screen.getByPlaceholderText(/Soll KI Hausaufgaben bewerten/i);
    fireEvent.change(input, { target: { value: "Tempolimit" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(mqApi.createMindQuest).toHaveBeenCalledWith({
        topic: "Tempolimit",
        target_level: "B2",
        mode: "ARGUE",
      });
      expect(mockPush).toHaveBeenCalledWith("/mindquests/mq-argue-1");
    });
  });

  it("MindQuestsPage blocks submission and reminds the user when topic is empty", async () => {
    vi.mocked(mqApi.listMindQuests).mockResolvedValueOnce([]);
    const createSpy = vi.mocked(mqApi.createMindQuest);
    createSpy.mockClear();

    render(<MindQuestsPage />);
    expect(await screen.findByText(/Noch keine MindQuest/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /MindQuest erstellen/i }));
    expect(
      await screen.findByText("Bitte gib zuerst ein Thema für deine MindQuest ein."),
    ).toBeInTheDocument();
    expect(createSpy).not.toHaveBeenCalled();
  });

  it("MindQuestsPage deletes an individual MindQuest from the list without navigating", async () => {
    vi.mocked(mqApi.listMindQuests).mockResolvedValueOnce([
      {
        id: "mq-del-1",
        user_id: "u-1",
        topic: "Alte Quest 1",
        target_level: "B2",
        status: "TOPIC_SELECTED",
        planned_hats: ["WHITE"],
        completed_hats: [],
        hat_rounds: [],
        created_at: "2026-11-14T10:00:00Z",
        updated_at: "2026-11-14T10:00:00Z",
      },
      {
        id: "mq-keep-2",
        user_id: "u-1",
        topic: "Aktuelle Quest 2",
        target_level: "C1",
        status: "COMPLETED",
        planned_hats: ["WHITE"],
        completed_hats: ["WHITE"],
        hat_rounds: [],
        created_at: "2026-11-14T10:05:00Z",
        updated_at: "2026-11-14T10:05:00Z",
      },
    ]);
    vi.mocked(mqApi.deleteMindQuest).mockResolvedValueOnce(undefined);

    render(<MindQuestsPage />);
    expect(await screen.findByText("Alte Quest 1")).toBeInTheDocument();
    expect(screen.getByText("Aktuelle Quest 2")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: 'MindQuest "Alte Quest 1" löschen' }),
    );

    await waitFor(() => {
      expect(mqApi.deleteMindQuest).toHaveBeenCalledWith("mq-del-1");
      expect(screen.queryByText("Alte Quest 1")).not.toBeInTheDocument();
    });
    expect(screen.getByText("Aktuelle Quest 2")).toBeInTheDocument();
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
    expect(
      screen.getByRole("img", { name: "Radar-Diagramm Denkfähigkeiten" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Radar-Diagramm Deutsch" }),
    ).toBeInTheDocument();
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

  it("handles keyboard Enter vs Shift+Enter on MindQuestsPage and renders empty & error states across pages", async () => {
    vi.mocked(mqApi.listMindQuests).mockResolvedValueOnce([]);
    render(<MindQuestsPage />);
    expect(
      await screen.findByText(/Noch keine MindQuest\. Dein erster Gedankengang wartet\./i)
    ).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Soll KI Hausaufgaben bewerten/i);
    fireEvent.change(input, { target: { value: "Thema per Enter" } });

    // Shift+Enter must NOT submit
    fireEvent.keyDown(input.closest("form")!, { key: "Enter", shiftKey: true });
    expect(mqApi.createMindQuest).not.toHaveBeenCalled();

    // Error states across ReflectionPage, LearningPage, HistoryPage
    vi.mocked(mqApi.getFinalReflection).mockRejectedValueOnce(new Error("404"));
    render(<ReflectionPage />);
    expect(
      await screen.findByText("Die Reflexion ist noch nicht verfügbar.")
    ).toBeInTheDocument();

    vi.mocked(learningApi.getLearningProfile).mockResolvedValueOnce({
      user_id: "u-1",
      mindquests_completed: 0,
      thinking_overall: null,
      german_overall: null,
      thinking_dimensions: [],
      german_dimensions: [],
      strongest_thinking_dimension: null,
      weakest_thinking_dimension: null,
      strongest_german_dimension: null,
      weakest_german_dimension: null,
    });
    render(<LearningPage />);
    expect(
      (await screen.findAllByText("Deine Werte erscheinen nach der ersten Auswertung.")).length
    ).toBe(2);
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(2);

    vi.mocked(learningApi.getUserMindQuests).mockRejectedValueOnce(new Error("fail"));
    vi.mocked(learningApi.getUserActivities).mockRejectedValueOnce(new Error("fail"));
    render(<HistoryPage />);
    expect(
      await screen.findByText("Dein Verlauf konnte nicht geladen werden.")
    ).toBeInTheDocument();
  });
});
