import { HatType } from "./hat";
import { GermanEvaluation, HatFeedback, ThinkingEvaluation } from "./evaluation";

export type LanguageLevel = "B2" | "C1";

export type MindQuestStatus =
  | "CREATED"
  | "TOPIC_SELECTED"
  | "IN_PROGRESS"
  | "HAT_ACTIVE"
  | "HAT_COMPLETED"
  | "ALL_HATS_COMPLETED"
  | "FINAL_EVALUATION"
  | "COMPLETED"
  | "ABANDONED";

export interface Turn {
  id: string;
  turn_number: number;
  hat: HatType;
  challenge_question: string;
  challenge_instruction: string;
  difficulty: number;
  user_response?: string | null;
  responded_at?: string | null;
  created_at: string;
}

export interface HatRound {
  id: string;
  hat: HatType;
  sequence_index: number;
  turns: Turn[];
  started_at: string;
  completed_at?: string | null;
}

export interface MindQuest {
  id: string;
  user_id: string;
  topic: string;
  target_level: LanguageLevel;
  status: MindQuestStatus;
  current_hat?: HatType | null;
  planned_hats: HatType[];
  completed_hats: HatType[];
  hat_rounds: HatRound[];
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
}

export interface CreateMindQuestRequest {
  topic: string;
  target_level?: LanguageLevel;
  planned_hats?: HatType[];
}

export interface StartMindQuestResponse {
  mindquest: MindQuest;
  active_hat: HatType;
  initial_turn: Turn;
  challenge_question: string;
  challenge_instruction: string;
  difficulty: number;
}

export interface SubmitResponseRequest {
  response: string;
}

export interface SubmitResponseResponse {
  turn: Turn;
  thinking_evaluation: ThinkingEvaluation;
  german_evaluation: GermanEvaluation;
  feedback: HatFeedback;
  next_challenge_question?: string | null;
  next_challenge_instruction?: string | null;
  round_should_complete: boolean;
}

export interface FinalReflection {
  score?: number;
  summary?: string;
  strengths?: string[];
  learner_weaknesses?: string[];
  [key: string]: unknown;
}

export interface AdvanceMindQuestResponse {
  mindquest: MindQuest;
  next_hat?: HatType | null;
  is_completed: boolean;
  initial_turn?: Turn | null;
  final_reflection?: FinalReflection | null;
}