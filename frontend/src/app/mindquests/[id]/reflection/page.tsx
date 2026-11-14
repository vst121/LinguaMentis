"use client";
import Link from "next/link"; import { useEffect,useState } from "react"; import { useParams } from "next/navigation"; import { AppShell } from "@/components/layout/AppShell"; import { Card } from "@/components/ui/Card"; import { Button } from "@/components/ui/Button"; import { getFinalReflection } from "@/services/api/mindquests"; import { FinalReflection } from "@/types/evaluation";
export default function ReflectionPage(){const {id}=useParams<{id:string}>();const [r,setR]=useState<FinalReflection|null>(null);const [error,setError]=useState("");useEffect(()=>{getFinalReflection(id).then(setR).catch(()=>setError("Die Reflexion ist noch nicht verfügbar."))},[id]); if(error)return <AppShell><p className="text-rose-700">{error}</p></AppShell>;if(!r)return <AppShell><p className="text-slate-500">Reflexion wird geladen …</p></AppShell>;return (
  <AppShell>
    <div className="flex flex-col gap-5 md:flex-1 md:min-h-0">
      <div className="flex shrink-0 flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold text-blue-700 md:text-sm">ABSCHLUSS</p>
          <h1 className="mt-1 text-2xl font-bold md:text-3xl">
            Deine MindQuest-Reflexion
          </h1>
          <p className="mt-2 max-w-3xl text-base text-slate-600 md:text-lg">
            {r.closing_message}
          </p>
        </div>
        <Link href="/mindquests" className="shrink-0">
          <Button>Neue MindQuest starten</Button>
        </Link>
      </div>
      <div className="grid gap-5 md:flex-1 md:min-h-0 md:grid-cols-2">
        <Card
          title="Dein Denken"
          className="flex flex-col md:h-full md:min-h-0"
          bodyClassName="flex-1 md:overflow-y-auto"
        >
          <p className="leading-7 text-slate-700">{r.thinking_summary}</p>
          <h3 className="mt-5 font-semibold">Nächster Schritt</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-600">
            {r.thinking_section.recommendations?.map((x) => (
              <li key={x}>• {x}</li>
            ))}
          </ul>
        </Card>
        <Card
          title="Dein Deutsch"
          className="flex flex-col md:h-full md:min-h-0"
          bodyClassName="flex-1 md:overflow-y-auto"
        >
          <p className="leading-7 text-slate-700">{r.german_summary}</p>
          <h3 className="mt-5 font-semibold">Nächster Schritt</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-600">
            {r.german_section.level_recommendations?.map((x) => (
              <li key={x}>• {x}</li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  </AppShell>
);}
