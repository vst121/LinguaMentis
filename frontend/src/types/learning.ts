export interface DimensionScore {
  name: string;
  score: number;
}

export interface UserLearningProfile {
  user_id: string;
  mindquests_completed: number;
  thinking_overall: number | null;
  german_overall: number | null;
  thinking_dimensions: DimensionScore[];
  german_dimensions: DimensionScore[];
  strongest_thinking_dimension: string | null;
  weakest_thinking_dimension: string | null;
  strongest_german_dimension: string | null;
  weakest_german_dimension: string | null;
}

export interface UserActivity {
  id: string;
  user_id: string;
  activity_type: string;
  mindquest_id?: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}
