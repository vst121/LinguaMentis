import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { HatIndicator } from "@/components/hats/HatIndicator";
import {
  ResponsePropositionCard,
  buildHighlightedSegments,
} from "@/components/evaluation/ResponsePropositionCard";
import { ScoreRadarChart } from "@/components/evaluation/ScoreRadarChart";
import { AppShell } from "@/components/layout/AppShell";
import { HAT_METADATA, HatType } from "@/types/hat";
import { mockUsePathname } from "../setup";

describe("UI and layout components", () => {
  it("renders Button variants, sizes, and loading spinner state", () => {
    const { rerender } = render(
      <Button variant="outline" size="lg">
        Klicken
      </Button>
    );
    const btn = screen.getByRole("button", { name: "Klicken" });
    expect(btn).not.toBeDisabled();
    expect(btn.className).toContain("border-slate-300");

    rerender(<Button isLoading>Speichern</Button>);
    const loadingBtn = screen.getByRole("button", { name: "Speichern" });
    expect(loadingBtn).toBeDisabled();
    expect(loadingBtn.querySelector("svg.animate-spin")).not.toBeNull();
  });

  it("renders Badge variants with custom classes", () => {
    render(
      <Badge variant="success" className="extra-badge">
        COMPLETED
      </Badge>
    );
    const badge = screen.getByText("COMPLETED");
    expect(badge.className).toContain("bg-green-100");
    expect(badge.className).toContain("extra-badge");
  });

  it("renders Card with title, description, children, and footer", () => {
    render(
      <Card title="Kartentitel" description="Untertitel" footer={<span>Fußzeile</span>}>
        <p>Inhalt</p>
      </Card>
    );
    expect(screen.getByText("Kartentitel")).toBeInTheDocument();
    expect(screen.getByText("Untertitel")).toBeInTheDocument();
    expect(screen.getByText("Inhalt")).toBeInTheDocument();
    expect(screen.getByText("Fußzeile")).toBeInTheDocument();
  });

  it("renders HatIndicator for all 6 hats and supports detail mode", () => {
    const hats: HatType[] = ["WHITE", "RED", "BLACK", "YELLOW", "GREEN", "BLUE"];
    for (const hat of hats) {
      const { unmount } = render(<HatIndicator hat={hat} detail />);
      expect(screen.getByText(HAT_METADATA[hat].nameGerman)).toBeInTheDocument();
      expect(screen.getByText(`· ${HAT_METADATA[hat].question}`)).toBeInTheDocument();
      unmount();
    }
  });

  it("renders AppShell navigation and highlights active route", () => {
    mockUsePathname.mockReturnValue("/mindquests/abc");
    render(
      <AppShell>
        <div>Seiteninhalt</div>
      </AppShell>
    );
    expect(screen.getByText("LinguaMentis")).toBeInTheDocument();
    expect(screen.getByText("Seiteninhalt")).toBeInTheDocument();

    const mindquestsLink = screen.getByText("MindQuests").closest("a");
    const startLink = screen.getByText("Start").closest("a");
    expect(mindquestsLink?.className).toContain("bg-slate-900");
    expect(startLink?.className).not.toContain("bg-slate-900");
  });

  it("splits improved response into highlighted and plain segments without overlap", () => {
    const segments = buildHighlightedSegments(
      "Ein wesentlicher Nachteil liegt darin, dass Kosten rasch eskalieren.",
      [
        {
          upgraded_phrase: "Ein wesentlicher Nachteil liegt darin",
          original_phrase: "Ein Nachteil ist",
          explanation: "Gehobene Nominalstruktur.",
          category: "syntax",
        },
        {
          upgraded_phrase: "rasch eskalieren",
          original_phrase: "schnell steigen",
          explanation: "Ausdrucksstärkeres Verb.",
          category: "vocabulary",
        },
      ],
    );
    expect(segments.map((s) => s.text).join("")).toBe(
      "Ein wesentlicher Nachteil liegt darin, dass Kosten rasch eskalieren.",
    );
    expect(segments.filter((s) => Boolean(s.highlight))).toHaveLength(2);
  });

  it("renders ResponsePropositionCard with inline highlights and upgrade explanations", () => {
    const { container } = render(
      <ResponsePropositionCard
        originalResponse="Ein Nachteil ist, dass Kosten schnell steigen."
        proposition={{
          id: "prop-1",
          improved_response:
            "Ein wesentlicher Nachteil liegt darin, dass die Kosten rasch eskalieren.",
          highlights: [
            {
              upgraded_phrase: "Ein wesentlicher Nachteil liegt darin",
              original_phrase: "Ein Nachteil ist",
              explanation: "Gehobene Einleitung für ein Gegenargument.",
              category: "syntax",
            },
            {
              upgraded_phrase: "rasch eskalieren",
              original_phrase: "schnell steigen",
              explanation: "Präzisere C1-Verbverbindung.",
              category: "vocabulary",
            },
          ],
        }}
      />,
    );
    expect(screen.getByText("Sprach-Upgrade: Elaborierte Antwort")).toBeInTheDocument();
    expect(container.querySelectorAll("mark")).toHaveLength(2);
    expect(screen.getByText("Satzbau")).toBeInTheDocument();
    expect(screen.getByText("Wortschatz")).toBeInTheDocument();
    expect(screen.getByText("Gehobene Einleitung für ein Gegenargument.")).toBeInTheDocument();
  });

  it("renders ScoreRadarChart SVG polygon and all dimension labels/scores", () => {
    const { container } = render(
      <ScoreRadarChart
        accent="blue"
        ariaLabel="Radar-Diagramm Test"
        dimensions={[
          { key: "hat_adherence", label: "Perspektiven-Fokus", score: 90 },
          { key: "relevance", label: "Relevanz", score: 85 },
          { key: "reasoning", label: "Argumentation", score: 88 },
          { key: "depth", label: "Tiefe", score: 80 },
          { key: "specificity", label: "Spezifität", score: 84 },
        ]}
      />,
    );
    expect(screen.getByRole("img", { name: "Radar-Diagramm Test" })).toBeInTheDocument();
    expect(container.querySelectorAll("circle")).toHaveLength(5);
    expect(screen.getByText("Perspektiven-Fokus")).toBeInTheDocument();
    expect(screen.getByText("Relevanz")).toBeInTheDocument();
    expect(screen.getByText("90")).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument();
    expect(screen.queryByText("90 / 100")).not.toBeInTheDocument();
  });
});
