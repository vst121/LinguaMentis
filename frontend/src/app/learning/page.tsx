"use client";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { ProfileMetricsSection } from "@/components/evaluation/ProfileScoreCards";
import { Card } from "@/components/ui/Card";
import { getLearningProfile } from "@/services/api/learning";
import { UserLearningProfile } from "@/types/learning";

export default function LearningPage() {
  const [profile, setProfile] = useState<UserLearningProfile | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getLearningProfile()
      .then(setProfile)
      .catch(() => setError("Dein Lernprofil konnte nicht geladen werden."));
  }, []);
  return (
    <AppShell>
      <div className="flex flex-col gap-3">
        <div>
          <p className="text-xs font-semibold text-blue-700">LERNPROFIL</p>
          <h1 className="mt-0.5 text-xl font-bold md:text-2xl">
            Deine Entwicklung im Blick
          </h1>
          <p className="mt-0.5 text-xs text-slate-600 md:text-sm">
            Denken und Sprache sind zwei eigene Fähigkeiten — hier siehst du beide.
          </p>
        </div>
        {error ? (
          <p className="text-rose-700">{error}</p>
        ) : !profile ? (
          <div className="grid gap-4 md:grid-cols-3">
            {[0, 1, 2].map((idx) => (
              <Card key={idx} className="h-24 animate-pulse bg-slate-100/70" />
            ))}
          </div>
        ) : (
          <ProfileMetricsSection
            primaryCardLabel="Abgeschlossene MindQuests"
            primaryCardValue={profile.mindquests_completed}
            thinkingOverall={profile.thinking_overall}
            germanOverall={profile.german_overall}
            thinkingDimensions={profile.thinking_dimensions}
            germanDimensions={profile.german_dimensions}
            strongestThinking={profile.strongest_thinking_dimension}
            weakestThinking={profile.weakest_thinking_dimension}
            strongestGerman={profile.strongest_german_dimension}
            weakestGerman={profile.weakest_german_dimension}
          />
        )}
      </div>
    </AppShell>
  );
}
