import { apiFetch } from "./client";
import {
  AdvanceMindQuestResponse,
  CreateMindQuestRequest,
  MindQuest,
  StartMindQuestResponse,
  SubmitResponseRequest,
  SubmitResponseResponse,
} from "@/types/mindquest";
import { FinalReflection } from "@/types/evaluation";

export async function createMindQuest(data: CreateMindQuestRequest): Promise<MindQuest> {
  return apiFetch<MindQuest>("/mindquests", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listMindQuests(limit = 50, offset = 0): Promise<MindQuest[]> {
  return apiFetch<MindQuest[]>(`/mindquests?limit=${limit}&offset=${offset}`);
}

export async function getMindQuest(id: string): Promise<MindQuest> {
  return apiFetch<MindQuest>(`/mindquests/${id}`);
}

export async function startMindQuest(id: string): Promise<StartMindQuestResponse> {
  return apiFetch<StartMindQuestResponse>(`/mindquests/${id}/start`, {
    method: "POST",
  });
}

export async function submitResponse(
  id: string,
  data: SubmitResponseRequest
): Promise<SubmitResponseResponse> {
  return apiFetch<SubmitResponseResponse>(`/mindquests/${id}/responses`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function advanceMindQuest(id: string): Promise<AdvanceMindQuestResponse> {
  return apiFetch<AdvanceMindQuestResponse>(`/mindquests/${id}/advance`, {
    method: "POST",
  });
}

export async function getFinalReflection(id: string): Promise<FinalReflection> {
  return apiFetch<FinalReflection>(`/mindquests/${id}/reflection`);
}
