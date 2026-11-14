import { describe, expect, it } from "vitest";
import { cn } from "@/lib/utils";

describe("cn utility", () => {
  it("combines multiple class names and conditional values", () => {
    expect(cn("px-4", false && "hidden", "py-2", undefined)).toBe("px-4 py-2");
  });

  it("merges conflicting Tailwind utility classes deterministically", () => {
    expect(cn("bg-slate-100 text-sm", "bg-slate-900")).toBe("text-sm bg-slate-900");
    expect(cn("px-2 py-1", "px-4")).toBe("py-1 px-4");
  });
});
