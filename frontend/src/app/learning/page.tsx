"use client";
import { useEffect,useState } from "react"; import { AppShell } from "@/components/layout/AppShell"; import { Card } from "@/components/ui/Card"; import { getLearningProfile } from "@/services/api/learning"; import { UserLearningProfile } from "@/types/learning";
function Dimension({name,score}:{name:string;score:number}){return <div className="mb-4"><div className="mb-1 flex justify-between text-sm"><span>{name}</span><strong>{score}</strong></div><div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-blue-600" style={{width:`${score}%`}}/></div></div>}
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
      <div className="flex flex-col gap-5 md:flex-1 md:min-h-0">
        <div className="shrink-0">
          <p className="text-xs font-semibold text-blue-700 md:text-sm">LERNPROFIL</p>
          <h1 className="mt-1 text-2xl font-bold md:text-3xl">
            Deine Entwicklung im Blick
          </h1>
          <p className="mt-1 text-sm text-slate-600 md:text-base">
            Denken und Sprache sind zwei eigene Fähigkeiten — hier siehst du beide.
          </p>
        </div>
        {error ? (
          <p className="text-rose-700">{error}</p>
        ) : !profile ? (
          <p className="text-slate-500">Lernprofil wird geladen …</p>
        ) : (
          <div className="flex flex-col gap-5 md:flex-1 md:min-h-0">
            <div className="grid shrink-0 gap-4 md:grid-cols-3">
              <Card bodyClassName="p-4 md:p-5">
                <p className="text-sm text-slate-500">Abgeschlossene MindQuests</p>
                <p className="mt-1.5 text-2xl font-bold md:text-3xl">
                  {profile.mindquests_completed}
                </p>
              </Card>
              <Card bodyClassName="p-4 md:p-5">
                <p className="text-sm text-slate-500">Denken</p>
                <p className="mt-1.5 text-2xl font-bold md:text-3xl">
                  {profile.thinking_overall ?? "—"}
                </p>
              </Card>
              <Card bodyClassName="p-4 md:p-5">
                <p className="text-sm text-slate-500">Deutsch</p>
                <p className="mt-1.5 text-2xl font-bold md:text-3xl">
                  {profile.german_overall ?? "—"}
                </p>
              </Card>
            </div>
            <div className="grid gap-5 md:flex-1 md:min-h-0 md:grid-cols-2">
              <Card
                title="Denkfähigkeiten"
                description={
                  profile.strongest_thinking_dimension
                    ? `Stärke: ${profile.strongest_thinking_dimension} · Fokus: ${profile.weakest_thinking_dimension}`
                    : "Deine Werte erscheinen nach der ersten Auswertung."
                }
                className="flex flex-col md:h-full md:min-h-0"
                bodyClassName="flex-1 md:overflow-y-auto"
              >
                {profile.thinking_dimensions.map((d) => (
                  <Dimension key={d.name} {...d} />
                ))}
              </Card>
              <Card
                title="Deutsch"
                description={
                  profile.strongest_german_dimension
                    ? `Stärke: ${profile.strongest_german_dimension} · Fokus: ${profile.weakest_german_dimension}`
                    : "Deine Werte erscheinen nach der ersten Auswertung."
                }
                className="flex flex-col md:h-full md:min-h-0"
                bodyClassName="flex-1 md:overflow-y-auto"
              >
                {profile.german_dimensions.map((d) => (
                  <Dimension key={d.name} {...d} />
                ))}
              </Card>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
