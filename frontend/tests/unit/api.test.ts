import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "@/services/api/client";
import {
  advanceMindQuest,
  createMindQuest,
  deleteMindQuest,
  getFinalReflection,
  getMindQuest,
  listMindQuests,
  startMindQuest,
  submitResponse,
} from "@/services/api/mindquests";
import {
  getLearningProfile,
  getUserActivities,
  getUserMindQuests,
} from "@/services/api/learning";

describe("API client and service functions", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("apiFetch normalizes leading slash, sets JSON content-type, and parses JSON", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "ok" }),
    });

    const data = await apiFetch<{ status: string }>("mindquests");
    expect(data).toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/mindquests",
      expect.objectContaining({
        headers: expect.objectContaining({ "Content-Type": "application/json" }),
      })
    );
  });

  it("apiFetch throws server error message when response is not ok and has JSON message", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: async () => ({ message: "Invalid state transition" }),
    });

    await expect(apiFetch("/mindquests/1/start")).rejects.toThrow("Invalid state transition");
  });

  it("apiFetch falls back to HTTP status text when error body is not JSON", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 502,
      statusText: "Bad Gateway",
      json: async () => {
        throw new Error("not json");
      },
    });

    await expect(apiFetch("/mindquests/1/responses")).rejects.toThrow(
      "HTTP error 502: Bad Gateway"
    );
  });

  it("calls all MindQuest and Learning endpoints with expected paths and methods", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    await createMindQuest({ topic: "KI in Schulen", target_level: "B2" });
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/mindquests",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ topic: "KI in Schulen", target_level: "B2" }),
      })
    );

    await listMindQuests(10, 5);
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/mindquests?limit=10&offset=5",
      expect.anything()
    );

    await getMindQuest("mq-1");
    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/mindquests/mq-1", expect.anything());

    await startMindQuest("mq-1");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/mindquests/mq-1/start",
      expect.objectContaining({ method: "POST" })
    );

    await submitResponse("mq-1", { response: "Meine Antwort" });
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/mindquests/mq-1/responses",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ response: "Meine Antwort" }),
      })
    );

    await advanceMindQuest("mq-1");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/mindquests/mq-1/advance",
      expect.objectContaining({ method: "POST" })
    );

    await getFinalReflection("mq-1");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/mindquests/mq-1/reflection",
      expect.anything()
    );

    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 204,
      json: async () => {
        throw new Error("should not parse 204 body");
      },
    });
    await deleteMindQuest("mq-1");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/mindquests/mq-1",
      expect.objectContaining({ method: "DELETE" })
    );

    await getLearningProfile("u-1");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/users/u-1/learning-profile",
      expect.anything()
    );

    await getUserActivities("u-1", 20, 0);
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/users/u-1/activities?limit=20&offset=0",
      expect.anything()
    );

    await getUserMindQuests("u-1", 15, 0);
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/users/u-1/mindquests?limit=15&offset=0",
      expect.anything()
    );
  });
});
