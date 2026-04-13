import { useState, useCallback } from "react";

export interface EmotionScore {
  name: string;
  score: number;
}

export interface HumeEmotions {
  prosody: EmotionScore[];
}

export function useHumeProsody() {
  const [emotions, setEmotions] = useState<HumeEmotions>({ prosody: [] });
  const [analyzing, setAnalyzing] = useState(false);

  const analyzeAudio = useCallback(async (audioBlob: Blob) => {
    if (!audioBlob || audioBlob.size === 0) return;
    setAnalyzing(true);
    try {
      const form = new FormData();
      const ext = audioBlob.type.includes("ogg") ? "ogg" : "webm";
      form.append("file", audioBlob, `answer.${ext}`);

      const res = await fetch("http://127.0.0.1:8000/api/v1/hume/analyze-prosody", {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        console.warn("[Hume] analyze-prosody failed:", await res.text());
        return;
      }

      const data = await res.json();
      const prosody: EmotionScore[] = (data.prosody || [])
        .sort((a: EmotionScore, b: EmotionScore) => b.score - a.score)
        .slice(0, 10);

      setEmotions({ prosody });
    } catch (e) {
      console.warn("[Hume] Error:", e);
    } finally {
      setAnalyzing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setEmotions({ prosody: [] });
  }, []);

  return { emotions, analyzing, analyzeAudio, reset };
}
