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
      <div className="flex flex-col gap-2.5">
        <h1 className="text-lg font-bold">Deine Entwicklung im Blick</h1>
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
