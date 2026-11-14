import type { DimensionScore } from "./learning";

export interface Evidence {
  dimension: string;
  observation: string;
  impact: string;
}

export interface Correction {
  original: string;
  corrected: string;
  explanation: string;
  category: string;
}

export interface ThinkingEvaluation {
  id: string;
  score: number;
  score_anchor: string;
  hat_adherence: number;
  relevance: number;
  reasoning: number;
  depth: number;
  specificity: number;
  evidence: Evidence[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export interface GermanEvaluation {
  id: string;
  score: number;
  score_anchor: string;
  grammar: number;
  vocabulary: number;
  sentence_structure: number;
  naturalness: number;
  level_appropriateness: number;
  evidence: Evidence[];
  corrections: Correction[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export interface HatFeedback {
  thinking_feedback: string;
  german_feedback: string;
  encouragement?: string;
}

export interface ThinkingReflectionSection {
  overall_summary: string;
  strongest_thinking_modes?: string[];
  weakest_thinking_modes?: string[];
  key_reasoning_patterns?: string[];
  recommendations?: string[];
  progress_note?: string;
}

export interface GermanReflectionSection {
  overall_summary: string;
  grammar_strengths?: string[];
  vocabulary_notes?: string[];
  naturalness_notes?: string[];
  important_corrections?: Correction[];
  recommended_expressions?: string[];
  level_recommendations?: string[];
  progress_note?: string;
}

export interface FinalReflection {
  id: string;
  mindquest_id: string;
  topic?: string;
  target_level?: string;
  hats_completed?: number;
  hats_total?: number;
  thinking_overall?: number | null;
  german_overall?: number | null;
  thinking_dimensions?: DimensionScore[];
  german_dimensions?: DimensionScore[];
  strongest_thinking_dimension?: string | null;
  weakest_thinking_dimension?: string | null;
  strongest_german_dimension?: string | null;
  weakest_german_dimension?: string | null;
  thinking_summary: string;
  german_summary: string;
  thinking_section: ThinkingReflectionSection;
  german_section: GermanReflectionSection;
  closing_message: string;
  created_at?: string;
}
