const BASE_URL = "http://127.0.0.1:8000/api/v1";

export async function analyzeCV(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/cv/analyze`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Failed to analyze document.");
  }
  return res.json();
}

export type InterviewExperiencePayload = {
  yearsExperience?: string;
  totalExperienceMonths?: number;
  jobs?: Array<Record<string, unknown>>;
};

export async function startInterview(
  domain: string,
  skills: string[],
  prioritySkills: string[] = [],
  experience?: InterviewExperiencePayload,
) {
  const body: Record<string, unknown> = {
    domain,
    skills,
    priority_skills: prioritySkills,
  };
  if (experience?.yearsExperience?.trim()) {
    body.years_experience = experience.yearsExperience.trim();
  }
  if (experience?.totalExperienceMonths != null && Number.isFinite(experience.totalExperienceMonths)) {
    body.total_experience_months = Math.max(0, Math.round(experience.totalExperienceMonths));
  }
  if (experience?.jobs?.length) {
    body.jobs = experience.jobs;
  }
  const res = await fetch(`${BASE_URL}/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getQuestion(session_id: string) {
  const res = await fetch(`${BASE_URL}/interview/question?session_id=${session_id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitAnswer(session_id: string, answer: string) {
  const res = await fetch(`${BASE_URL}/interview/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, answer }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitAnswerWithCoaching(
  session_id: string,
  answer: string,
  coaching_metrics?: Record<string, unknown>,
) {
  const res = await fetch(`${BASE_URL}/interview/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, answer, coaching_metrics }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getReport(session_id: string) {
  const res = await fetch(`${BASE_URL}/interview/report?session_id=${session_id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function textToSpeech(text: string): Promise<Blob> {
  const res = await fetch(`${BASE_URL}/speech/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.blob();
}

export async function speechToText(audioBlob: Blob): Promise<{ transcript: string }> {
  const form = new FormData();
  const ext = audioBlob.type.includes("ogg") ? "ogg" : "webm";
  form.append("file", audioBlob, `answer.${ext}`);
  const res = await fetch(`${BASE_URL}/speech/stt`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

