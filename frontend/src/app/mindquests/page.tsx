"use client";
import { useEffect, useState, type SubmitEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Plus, Trash2 } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  createMindQuest,
  deleteMindQuest,
  listMindQuests,
} from "@/services/api/mindquests";
import { MindQuest } from "@/types/mindquest";

export default function MindQuestsPage() {
  const router = useRouter();
  const [items, setItems] = useState<MindQuest[]>([]),
    [topic, setTopic] = useState(""),
    [level, setLevel] = useState<"B2" | "C1">("B2"),
    [loading, setLoading] = useState(true),
    [creating, setCreating] = useState(false),
    [deletingId, setDeletingId] = useState<string | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    listMindQuests()
      .then(setItems)
      .catch(() => setError("Deine MindQuests konnten nicht geladen werden."))
      .finally(() => setLoading(false));
  }, []);
  async function submit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    if (creating || !topic.trim()) return;
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
  function handleFormKeyDown(e: React.KeyboardEvent<HTMLFormElement>) {
    // Submit on Enter across all form inputs; do not submit when Shift+Enter is pressed
    if (e.key === "Enter" && !e.nativeEvent.isComposing) {
      if (e.shiftKey) {
        e.preventDefault();
        return;
      }
      e.preventDefault();
      e.currentTarget.requestSubmit();
    }
  }
  async function handleDelete(
    e: React.MouseEvent<HTMLButtonElement>,
    questId: string,
  ) {
    e.preventDefault();
    e.stopPropagation();
    if (deletingId === questId) return;
    setDeletingId(questId);
    setError("");
    try {
      await deleteMindQuest(questId);
      setItems((prev) => prev.filter((item) => item.id !== questId));
    } catch {
      setError("MindQuest konnte nicht gelöscht werden.");
    } finally {
      setDeletingId(null);
    }
  }
  return (
    <AppShell>
      <div className="flex flex-col gap-3">
        <h1 className="text-lg font-bold">Woran möchtest du heute denken?</h1>
        <div className="grid gap-4 md:grid-cols-[minmax(280px,.8fr)_1.2fr] md:items-start">
          <Card
            title="Neue MindQuest"
            description="Starte mit einem Thema, das dich wirklich interessiert."
          >
            <form
              onSubmit={submit}
              onKeyDown={handleFormKeyDown}
              className="flex flex-col gap-4"
            >
              <div className="space-y-4">
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
              </div>
              <Button type="submit" isLoading={creating} className="w-full">
                <Plus className="mr-2" size={16} />
                MindQuest erstellen
              </Button>
            </form>
          </Card>
          <div className="flex flex-col">
            <h2 className="mb-2.5 text-base font-semibold md:text-lg">Deine MindQuests</h2>
            {loading ? (
              <p className="text-slate-500">Wird geladen …</p>
            ) : items.length === 0 ? (
              <Card>
                <p className="text-slate-600">
                  Noch keine MindQuest. Dein erster Gedankengang wartet.
                </p>
              </Card>
            ) : (
              <div className="grid gap-3 md:grid-cols-1 lg:grid-cols-2">
                {items.map((q) => (
                  <Link href={`/mindquests/${q.id}`} key={q.id} className="block">
                    <Card className="h-full transition hover:border-blue-300 hover:shadow-md">
                      <div className="flex items-center justify-between gap-4">
                        <div className="min-w-0">
                          <div className="flex flex-wrap gap-2">
                            <Badge>{q.target_level}</Badge>
                            <Badge
                              variant={
                                q.status === "COMPLETED" ? "success" : "info"
                              }
                            >
                              {q.status.replaceAll("_", " ")}
                            </Badge>
                          </div>
                          <h3 className="mt-2.5 truncate font-semibold">{q.topic}</h3>
                          <p className="mt-1 text-sm text-slate-500">
                            {q.completed_hats.length} von {q.planned_hats.length}{" "}
                            Perspektiven abgeschlossen
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-1.5">
                          <button
                            type="button"
                            onClick={(e) => void handleDelete(e, q.id)}
                            disabled={deletingId === q.id}
                            aria-label={`MindQuest "${q.topic}" löschen`}
                            title="MindQuest löschen"
                            className="rounded-lg p-2 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"
                          >
                            <Trash2 size={16} />
                          </button>
                          <ArrowRight className="text-slate-400" />
                        </div>
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
