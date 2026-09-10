import { apiFetch } from "./client";
import { UserActivity, UserLearningProfile } from "@/types/learning";
import { MindQuest } from "@/types/mindquest";

const DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001";

export async function getLearningProfile(userId = DEFAULT_USER_ID): Promise<UserLearningProfile> {
  return apiFetch<UserLearningProfile>(`/users/${userId}/learning-profile`);
}

export async function getUserActivities(
  userId = DEFAULT_USER_ID,
  limit = 50,
  offset = 0
): Promise<UserActivity[]> {
  return apiFetch<UserActivity[]>(`/users/${userId}/activities?limit=${limit}&offset=${offset}`);
}

export async function getUserMindQuests(
  userId = DEFAULT_USER_ID,
  limit = 50,
  offset = 0
): Promise<MindQuest[]> {
  return apiFetch<MindQuest[]>(`/users/${userId}/mindquests?limit=${limit}&offset=${offset}`);
}
