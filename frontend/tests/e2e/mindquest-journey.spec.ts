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

    // 4. Verify redirect to active MindQuest detail page and start the quest
    await expect(page).toHaveURL(/\/mindquests\/[0-9a-f-]+$/);
    await expect(page.getByRole("heading", { name: topic })).toBeVisible();
    await page.getByRole("button", { name: /MindQuest beginnen/i }).click();

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

      // Verify independent Thinking and German evaluations + corrections appear
      await expect(page.getByText("Dein Feedback")).toBeVisible();
      await expect(page.getByText("Denken", { exact: true })).toBeVisible();
      await expect(page.getByText("Deutsch", { exact: true })).toBeVisible();
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
    // Should remain on /mindquests when topic is empty
    await expect(page).toHaveURL(/\/mindquests$/);

    await page.getByRole("link", { name: /Start/i }).click();
    await expect(page).toHaveURL(/\/$/);
  });
});
