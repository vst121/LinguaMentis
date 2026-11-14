import { apiFetch } from "./client";
import { GermanEvaluation, ThinkingEvaluation } from "@/types/evaluation";
import { HatType } from "@/types/hat";
import { MindQuest, Turn } from "@/types/mindquest";

export interface ConversationOpeningResponse {
  mindquest: MindQuest;
  active_hat?: HatType | null;
  active_turn?: Turn | null;
  spoken_text: string;
  audio_base64: string;
  audio_mime_type: string;
  is_completed: boolean;
}

export interface ConversationTurnRequest {
  transcript?: string | null;
  audio_base64?: string | null;
  mime_type?: string;
  include_audio?: boolean;
}

export interface ConversationTurnResponse {
  mindquest: MindQuest;
  user_transcript: string;
  spoken_reply: string;
  audio_base64: string;
  audio_mime_type: string;
  thinking_evaluation: ThinkingEvaluation;
  german_evaluation: GermanEvaluation;
  active_hat?: HatType | null;
  active_turn?: Turn | null;
  transitioned_hat?: HatType | null;
  is_completed: boolean;
  average_score?: number;
  round_should_complete?: boolean;
}

export async function openConversation(
  mindquestId: string
): Promise<ConversationOpeningResponse> {
  return apiFetch<ConversationOpeningResponse>(
    `/mindquests/${mindquestId}/conversation/opening`,
    { method: "POST" }
  );
}

export async function submitConversationTurn(
  mindquestId: string,
  data: ConversationTurnRequest
): Promise<ConversationTurnResponse> {
  return apiFetch<ConversationTurnResponse>(
    `/mindquests/${mindquestId}/conversation/turn`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}
