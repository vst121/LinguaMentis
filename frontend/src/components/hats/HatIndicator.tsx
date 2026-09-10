import { HAT_METADATA, HatType } from "@/types/hat";
import { cn } from "@/lib/utils";

export function HatIndicator({ hat, detail = false }: { hat: HatType; detail?: boolean }) {
 const meta = HAT_METADATA[hat];
 return <div className={cn("inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-semibold", meta.badgeBg, meta.badgeText, meta.borderColor)}><span className={cn("h-2.5 w-2.5 rounded-full", hat === "BLACK" ? "bg-white" : meta.accentColor.replace("text-", "bg-"))}/>{meta.nameGerman}{detail && <span className="font-normal opacity-75">· {meta.question}</span>}</div>;
}
