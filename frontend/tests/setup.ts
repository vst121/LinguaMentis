import "@testing-library/jest-dom/vitest";
import React from "react";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

export const mockPush = vi.fn();
export const mockPrefetch = vi.fn();
export const mockReplace = vi.fn();
export const mockRouter = {
  push: mockPush,
  prefetch: mockPrefetch,
  replace: mockReplace,
};
export const mockUsePathname = vi.fn(() => "/");
export const mockUseParams = vi.fn(() => ({ id: "mq-123" }));

vi.mock("next/navigation", () => ({
  useRouter: () => mockRouter,
  usePathname: () => mockUsePathname(),
  useParams: () => mockUseParams(),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => React.createElement("a", { href, ...rest }, children),
}));
