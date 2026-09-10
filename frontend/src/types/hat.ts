export type HatType = "WHITE" | "RED" | "BLACK" | "YELLOW" | "GREEN" | "BLUE";

export interface HatMeta {
  type: HatType;
  nameGerman: string;
  nameEnglish: string;
  question: string;
  mode: string;
  badgeBg: string;
  badgeText: string;
  borderColor: string;
  bgColor: string;
  accentColor: string;
}

export const HAT_METADATA: Record<HatType, HatMeta> = {
  WHITE: {
    type: "WHITE",
    nameGerman: "Weißer Hut",
    nameEnglish: "White Hat",
    question: "Was wissen wir?",
    mode: "Fakten, Daten, Informationsbedarf & Evidenz",
    badgeBg: "bg-slate-100",
    badgeText: "text-slate-800",
    borderColor: "border-slate-300",
    bgColor: "bg-slate-50",
    accentColor: "text-slate-600",
  },
  RED: {
    type: "RED",
    nameGerman: "Roter Hut",
    nameEnglish: "Red Hat",
    question: "Was fühlen wir?",
    mode: "Emotionen, Gefühle, Intuition & Bauchgefühl",
    badgeBg: "bg-rose-100",
    badgeText: "text-rose-800",
    borderColor: "border-rose-300",
    bgColor: "bg-rose-50",
    accentColor: "text-rose-600",
  },
  BLACK: {
    type: "BLACK",
    nameGerman: "Schwarzer Hut",
    nameEnglish: "Black Hat",
    question: "Was könnte schiefgehen?",
    mode: "Kritisches Denken, Risiken & Schwachstellen",
    badgeBg: "bg-slate-900",
    badgeText: "text-white",
    borderColor: "border-slate-800",
    bgColor: "bg-slate-950",
    accentColor: "text-slate-400",
  },
  YELLOW: {
    type: "YELLOW",
    nameGerman: "Gelber Hut",
    nameEnglish: "Yellow Hat",
    question: "Was könnte klappen?",
    mode: "Chancen, Vorteile & positiver Wert",
    badgeBg: "bg-amber-100",
    badgeText: "text-amber-900",
    borderColor: "border-amber-300",
    bgColor: "bg-amber-50",
    accentColor: "text-amber-600",
  },
  GREEN: {
    type: "GREEN",
    nameGerman: "Grüner Hut",
    nameEnglish: "Green Hat",
    question: "Was ist noch möglich?",
    mode: "Kreativität, Alternativen & neue Ideen",
    badgeBg: "bg-emerald-100",
    badgeText: "text-emerald-800",
    borderColor: "border-emerald-300",
    bgColor: "bg-emerald-50",
    accentColor: "text-emerald-600",
  },
  BLUE: {
    type: "BLUE",
    nameGerman: "Blauer Hut",
    nameEnglish: "Blue Hat",
    question: "Wie steuern wir den Prozess?",
    mode: "Prozesssteuerung, Synthese & Reflexion",
    badgeBg: "bg-blue-100",
    badgeText: "text-blue-800",
    borderColor: "border-blue-300",
    bgColor: "bg-blue-50",
    accentColor: "text-blue-600",
  },
};
