"use client";
import { useEffect, useState, type SubmitEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Plus } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createMindQuest, listMindQuests } from "@/services/api/mindquests";
import { MindQuest } from "@/types/mindquest";

export default function MindQuestsPage() {
  const router = useRouter();
  const [items, setItems] = useState<MindQuest[]>([]),
    [topic, setTopic] = useState(""),
    [level, setLevel] = useState<"B2" | "C1">("B2"),
    [loading, setLoading] = useState(true),
    [creating, setCreating] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    listMindQuests()
      .then(setItems)
      .catch(() => setError("Deine MindQuests konnten nicht geladen werden."))
      .finally(() => setLoading(false));
  }, []);
  async function submit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!topic.trim()) return;
    setCreating(true);
    setError("");
    try {
      const quest = await createMindQuest({
        topic: topic.trim(),
        target_level: level,
      });
      router.push(`/mindquests/${quest.id}`);
    } catch {
      setError(
        "MindQuest konnte nicht erstellt werden. Bitte versuche es erneut.",
      );
    } finally {
      setCreating(false);
    }
  }
  return (
    <AppShell>
      <div className="mb-8">
        <p className="text-sm font-semibold text-blue-700">MINQUESTS</p>
        <h1 className="mt-1 text-3xl font-bold">
          Woran möchtest du heute denken?
        </h1>
        <p className="mt-2 text-slate-600">
          Wähle ein relevantes Thema und nimm es Perspektive für Perspektive
          unter die Lupe.
        </p>
      </div>
      <div className="grid gap-7 lg:grid-cols-[.85fr_1.15fr]">
        <Card
          title="Neue MindQuest"
          description="Starte mit einem Thema, das dich wirklich interessiert."
        >
          <form onSubmit={submit} className="space-y-4">
            <label className="block text-sm font-medium">
              Thema
              <input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="z. B. Soll KI Hausaufgaben bewerten?"
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none ring-blue-500 focus:ring-2"
              />
            </label>
            <label className="block text-sm font-medium">
              Sprachniveau
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value as "B2" | "C1")}
                className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
              >
                <option>B2</option>
                <option>C1</option>
              </select>
            </label>
            {error && <p className="text-sm text-rose-700">{error}</p>}
            <Button type="submit" isLoading={creating} className="w-full">
              <Plus className="mr-2" size={16} />
              MindQuest erstellen
            </Button>
          </form>
        </Card>
        <div>
          <h2 className="mb-3 text-lg font-semibold">Deine MindQuests</h2>
          {loading ? (
            <p className="text-slate-500">Wird geladen …</p>
          ) : items.length === 0 ? (
            <Card>
              <p className="text-slate-600">
                Noch keine MindQuest. Dein erster Gedankengang wartet.
              </p>
            </Card>
          ) : (
            <div className="space-y-3">
              {items.map((q) => (
                <Link href={`/mindquests/${q.id}`} key={q.id}>
                  <Card className="transition hover:border-blue-300 hover:shadow-md">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="flex gap-2">
                          <Badge>{q.target_level}</Badge>
                          <Badge
                            variant={
                              q.status === "COMPLETED" ? "success" : "info"
                            }
                          >
                            {q.status.replaceAll("_", " ")}
                          </Badge>
                        </div>
                        <h3 className="mt-3 font-semibold">{q.topic}</h3>
                        <p className="mt-1 text-sm text-slate-500">
                          {q.completed_hats.length} von {q.planned_hats.length}{" "}
                          Perspektiven abgeschlossen
                        </p>
                      </div>
                      <ArrowRight className="text-slate-400" />
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
