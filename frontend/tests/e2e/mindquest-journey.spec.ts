import { expect, test } from "@playwright/test";

test.describe("LinguaMentis E2E MindQuest Journey", () => {
  test("completes a full MindQuest from landing page through evaluation, reflection, learning profile, and history", async ({
    page,
  }) => {
    // 1. Open Home page
    await page.goto("/");
    await expect(
      page.getByRole("heading", {
        name: /Denk klarer\. Drück dich auf Deutsch sicherer aus\./i,
      })
    ).toBeVisible();

    // 2. Navigate to MindQuests page
    await page.getByRole("link", { name: /MindQuest starten/i }).click();
    await expect(page).toHaveURL(/\/mindquests$/);
    await expect(
      page.getByRole("heading", { name: /Woran möchtest du heute denken\?/i })
    ).toBeVisible();

    // 3. Create a new MindQuest
    const topic = "KI-Bewertung von Hausaufgaben an Schulen";
    await page
      .getByPlaceholder(/Soll KI Hausaufgaben bewerten/i)
      .fill(topic);
    await page.getByRole("button", { name: /MindQuest erstellen/i }).click();

    // 4. Verify redirect to active MindQuest detail page and immediate first question (no begin button)
    await expect(page).toHaveURL(/\/mindquests\/[0-9a-f-]+$/);
    await expect(page.getByRole("heading", { name: topic })).toBeVisible();

    // 5. Complete all 6 mandatory hats (WHITE -> YELLOW -> GREEN -> RED -> BLACK -> BLUE)
    for (let hatIdx = 0; hatIdx < 6; hatIdx++) {
      await expect(
        page.getByText("Welche Risiken siehst du bei diesem Vorhaben?")
      ).toBeVisible();
      const textarea = page.getByPlaceholder(/Schreibe deine Antwort hier/i);
      await textarea.fill(
        "Ein erhebliches Risiko besteht darin, dass kreative Lösungswege von Algorithmen falsch bewertet werden."
      );
      await page.getByRole("button", { name: /Antwort auswerten/i }).click();

      // Verify independent Thinking and German evaluations + elaborated proposition appear
      await expect(page.getByText("Dein Feedback")).toBeVisible();
      await expect(page.getByText("Denken", { exact: true })).toBeVisible();
      await expect(page.getByText("Deutsch", { exact: true })).toBeVisible();
      await expect(page.getByText("Sprach-Upgrade: Elaborierte Antwort")).toBeVisible();
      await expect(page.getByText("Verbesserungen")).toBeVisible();

      if (hatIdx < 5) {
        await page
          .getByRole("button", { name: /Nächste Perspektive/i })
          .click();
      } else {
        await page
          .getByRole("button", { name: /Abschlussreflexion ansehen/i })
          .click();
      }
    }

    // 7. Verify Final Reflection page
    await expect(page).toHaveURL(/\/mindquests\/[0-9a-f-]+\/reflection$/);
    await expect(
      page.getByRole("heading", { name: /Deine MindQuest-Reflexion/i })
    ).toBeVisible();
    await expect(page.getByText("Ausgezeichnete Leistung!")).toBeVisible();

    // 8. Check Learning Profile page (/learning)
    await page.getByRole("link", { name: /Lernprofil/i }).click();
    await expect(page).toHaveURL(/\/learning$/);
    await expect(
      page.getByRole("heading", { name: /Deine Entwicklung im Blick/i })
    ).toBeVisible();
    await expect(page.getByText("Perspektiven-Fokus", { exact: true })).toBeVisible();
    await expect(page.getByText("Grammatik", { exact: true })).toBeVisible();

    // 9. Check Learning History page (/history)
    await page.getByRole("link", { name: /Verlauf/i }).click();
    await expect(page).toHaveURL(/\/history$/);
    await expect(page.getByText(topic).first()).toBeVisible();
  });

  test("prevents empty topic creation and navigates across main header links", async ({
    page,
  }) => {
    await page.goto("/mindquests");
    await page.getByRole("button", { name: /MindQuest erstellen/i }).click();
    // Should remain on /mindquests and show reminder when topic is empty
    await expect(page).toHaveURL(/\/mindquests$/);
    await expect(
      page.getByText("Bitte gib zuerst ein Thema für deine MindQuest ein."),
    ).toBeVisible();

    await page.getByRole("link", { name: /Start/i }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test("handles 404 MindQuest and missing reflection gracefully without crashing", async ({
    page,
  }) => {
    await page.goto("/mindquests/00000000-0000-0000-0000-999999999999");
    await expect(
      page.getByText("Diese MindQuest konnte nicht geladen werden.")
    ).toBeVisible();

    await page.goto(
      "/mindquests/00000000-0000-0000-0000-999999999999/reflection"
    );
    await expect(
      page.getByText("Die Reflexion ist noch nicht verfügbar.")
    ).toBeVisible();
  });

  test("meets E2E speed budgets for navigation, optimistic UI, and MindQuest transitions", async ({
    page,
  }) => {
    const tHome = Date.now();
    await page.goto("/");
    await expect(page.getByRole("link", { name: /MindQuest starten/i })).toBeVisible();
    expect(Date.now() - tHome).toBeLessThan(2000);

    // Client-side route transition speed budget (< 800ms)
    const tNav = Date.now();
    await page.getByRole("link", { name: /MindQuest starten/i }).click();
    await expect(
      page.getByRole("heading", { name: /Woran möchtest du heute denken\?/i })
    ).toBeVisible();
    expect(Date.now() - tNav).toBeLessThan(800);

    // Create MindQuest via Enter key and measure start & evaluation latency
    const input = page.getByPlaceholder(/Soll KI Hausaufgaben bewerten/i);
    await input.fill("Geschwindigkeitstest Debatte");
    await input.press("Enter");
    await expect(page).toHaveURL(/\/mindquests\/[0-9a-f-]+$/);

    const tStart = Date.now();
    await page.getByRole("button", { name: /MindQuest beginnen/i }).click();
    await expect(
      page.getByText("Welche Risiken siehst du bei diesem Vorhaben?")
    ).toBeVisible();
    expect(Date.now() - tStart).toBeLessThan(800);

    const textarea = page.getByPlaceholder(/Schreibe deine Antwort hier/i);
    await textarea.fill("Schnelle Antwort per Enter-Taste.");
    const tEval = Date.now();
    await textarea.press("Enter");
    await expect(page.getByText("Dein Feedback")).toBeVisible();
    expect(Date.now() - tEval).toBeLessThan(800);
  });

  test("toggles between Eintippen and Einsprechen with visual microphone indicator in browser", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      class BrowserMockSpeechRecognition {
        lang = "de-DE";
        continuous = true;
        interimResults = true;
        onresult: ((ev: unknown) => void) | null = null;
        onerror: ((ev: unknown) => void) | null = null;
        onend: (() => void) | null = null;
        start() {
          setTimeout(() => {
            if (this.onresult) {
              this.onresult({
                resultIndex: 0,
                results: {
                  length: 1,
                  0: {
                    isFinal: true,
                    0: {
                      transcript:
                        "Eingesprochene Antwort über das Browser-Mikrofon.",
                    },
                  },
                },
              });
            }
          }, 50);
        }
        stop() {}
      }
      (window as unknown as Record<string, unknown>).SpeechRecognition =
        BrowserMockSpeechRecognition;
      (window as unknown as Record<string, unknown>).webkitSpeechRecognition =
        BrowserMockSpeechRecognition;
    });

    await page.goto("/mindquests");
    await page
      .getByPlaceholder(/Soll KI Hausaufgaben bewerten/i)
      .fill("Spracheingabe Test Thema");
    await page.getByRole("button", { name: /MindQuest erstellen/i }).click();
    await expect(page).toHaveURL(/\/mindquests\/[0-9a-f-]+$/);

    await page.getByRole("button", { name: /MindQuest beginnen/i }).click();

    // Click "Einsprechen" button
    const speakBtn = page.getByRole("button", { name: /Einsprechen/i });
    await speakBtn.click();

    // Verify visual recording banner & level bars appear
    await expect(page.getByTestId("recording-indicator")).toBeVisible();
    await expect(page.getByText(/Mikrofon nimmt auf/i)).toBeVisible();
    await expect(page.getByTestId("audio-level-bars")).toBeVisible();

    // Wait for spoken transcript to populate textarea
    const textarea = page.getByPlaceholder(/Sprich jetzt ins Mikrofon/i);
    await expect(textarea).toHaveValue(
      "Eingesprochene Antwort über das Browser-Mikrofon."
    );

    // Switch back to "Eintippen" and verify recording indicator closes
    await page.getByRole("button", { name: /Eintippen/i }).click();
    await expect(page.getByTestId("recording-indicator")).toBeHidden();
  });

  test("conducts a spoken conversation with Conversation Agent across Thinking Hats", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      class ConversationMockSpeechRecognition {
        lang = "de-DE";
        continuous = true;
        interimResults = true;
        onresult: ((ev: unknown) => void) | null = null;
        onerror: ((ev: unknown) => void) | null = null;
        onend: (() => void) | null = null;
        start() {
          setTimeout(() => {
            if (this.onresult) {
              this.onresult({
                resultIndex: 0,
                results: {
                  length: 1,
                  0: {
                    isFinal: true,
                    0: {
                      transcript:
                        "Belegbare Studien zeigen klare Produktivitätsvorteile.",
                    },
                  },
                },
              });
            }
          }, 80);
        }
        stop() {
          if (this.onend) this.onend();
        }
      }
      const w = window as unknown as Record<string, unknown>;
      w.SpeechRecognition = ConversationMockSpeechRecognition;
      w.webkitSpeechRecognition = ConversationMockSpeechRecognition;
    });

    await page.goto("/mindquests");
    await page
      .getByPlaceholder(/Soll KI Hausaufgaben bewerten/i)
      .fill("Mündliches Debatten-Gespräch");
    await page.getByRole("button", { name: /MindQuest erstellen/i }).click();
    await expect(page).toHaveURL(/\/mindquests\/[0-9a-f-]+$/);

    // Start directly in spoken conversation mode
    await page
      .getByRole("button", { name: /Mündliches Gespräch starten/i })
      .click();
    await expect(page.getByTestId("conversation-view")).toBeVisible();

    // If browser is playing opening WAV, skip or wait until listening starts
    const skipBtn = page.getByRole("button", { name: /Direkt antworten/i });
    if (await skipBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await skipBtn.click();
    }

    await expect(page.getByTestId("live-spoken-transcript")).toContainText(
      "Belegbare Studien zeigen klare Produktivitätsvorteile."
    );
    await page.getByRole("button", { name: /Fertig gesprochen/i }).click();

    // Verify Conversation Agent replies and scores appear in conversation log
    await expect(
      page.getByText(/Das ist ein spannender Gedanke/i)
    ).toBeVisible();
  });
});
