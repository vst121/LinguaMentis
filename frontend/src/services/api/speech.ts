import { apiFetch } from "./client";

export interface SpeechTranscribeRequest {
  audio_base64: string;
  mime_type?: string;
}

export interface SpeechTranscribeResponse {
  text: string;
}

export async function transcribeAudio(
  data: SpeechTranscribeRequest
): Promise<SpeechTranscribeResponse> {
  return apiFetch<SpeechTranscribeResponse>("/speech/transcribe", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
