import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Mic, MicOff, Video, VideoOff, Clock, AlertCircle,
  Loader2, CheckCircle, XCircle, AlertTriangle,
  Eye, Focus, ScanFace, Volume2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { startInterview, getQuestion, submitAnswer, getReport, textToSpeech, speechToText } from "@/lib/api";
import { useMediaPipe } from "@/hooks/useMediaPipe";
import { useHumeProsody } from "@/hooks/useHumeStream";

interface AnswerRecord {
  question: string;
  answer: string;
  score: number;
  feedback: string;
}

type Stage = "loading" | "speaking" | "recording" | "transcribing" | "evaluating" | "feedback";

function getSupportedMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];
  for (const type of candidates) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return "";
}

const LiveInterview = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const domain = location.state?.domain || "Software Engineering";
  const skills: string[] = location.state?.skills || [];

  const INTERVIEW_DURATION = 5 * 60;
  const [timeLeft, setTimeLeft] = useState(INTERVIEW_DURATION);
  const [isCameraOn, setIsCameraOn] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [questionNumber, setQuestionNumber] = useState(1);
  const [questionLayer, setQuestionLayer] = useState("basic");
  const [attempts, setAttempts] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [stage, setStage] = useState<Stage>("loading");
  const [feedback, setFeedback] = useState<{ score: number; feedback: string } | null>(null);
  const [allAnswers, setAllAnswers] = useState<AnswerRecord[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportReady, setReportReady] = useState(false);
  const cachedReport = useRef<object | null>(null);

  const initialized = useRef(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const webcamStreamRef = useRef<MediaStream | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const mimeTypeRef = useRef<string>("");
  const faceMetrics = useMediaPipe(videoRef);
  const hume = useHumeProsody();

  // Coaching hint overlay
  const [coachingHint, setCoachingHint] = useState<string | null>(null);
  const hintTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const speakHint = (text: string) => {
    try {
      if (!window.speechSynthesis) return;
      window.speechSynthesis.cancel(); // stop any ongoing speech
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.volume = 0.85;
      utterance.rate = 1.05;
      utterance.pitch = 1.1;
      window.speechSynthesis.speak(utterance);
    } catch { /* speechSynthesis not available — silently skip */ }
  };

  useEffect(() => {
    // Suppress hints only while TTS is speaking — show during all other stages
    if (stage === "speaking" || faceMetrics.status !== "ready") { setCoachingHint(null); return; }
    let hint: string | null = null;
    if (!faceMetrics.faceDetected) hint = "Position your face in the camera";
    else if (!faceMetrics.eyeContact) hint = "Look at the camera";
    else if (faceMetrics.headPose === "turned") hint = "Face the camera directly";
    else if (faceMetrics.headPose === "tilted") hint = "Keep your head straight";
    else if (faceMetrics.lookingAway) hint = "Stay focused on the camera";
    if (hint) {
      setCoachingHint((prev) => {
        if (prev === hint) return prev;
        if (hintTimerRef.current) clearTimeout(hintTimerRef.current);
        hintTimerRef.current = setTimeout(() => setCoachingHint(null), 3000);
        // Speak only when hint changes to a new message
        speakHint(hint as string);
        return hint;
      });
    } else {
      if (hintTimerRef.current) clearTimeout(hintTimerRef.current);
      setCoachingHint(null);
    }
  }, [stage, faceMetrics]);

  useEffect(() => () => {
    if (hintTimerRef.current) clearTimeout(hintTimerRef.current);
    window.speechSynthesis?.cancel();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) { clearInterval(interval); if (sessionId) navigate("/feedback", { state: { sessionId, domain } }); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [sessionId]);

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      .then((stream) => { webcamStreamRef.current = stream; if (videoRef.current) videoRef.current.srcObject = stream; })
      .catch(() => console.warn("Camera access denied"));
    return () => {
      webcamStreamRef.current?.getTracks().forEach((t) => t.stop());
      audioStreamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const toggleCamera = () => {
    const stream = webcamStreamRef.current;
    if (!stream) return;
    stream.getVideoTracks().forEach((t) => { t.enabled = !t.enabled; });
    setIsCameraOn((prev) => !prev);
  };

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    const init = async () => {
      try {
        const session = await startInterview(domain, skills);
        setSessionId(session.session_id);
        const q = await getQuestion(session.session_id);
        setQuestion(q.question); setQuestionNumber(q.question_number); setQuestionLayer(q.layer || "basic");
        await speakQuestion(q.question);
      } catch { setError("Failed to start interview. Make sure the backend is running."); setStage("feedback"); }
    };
    init();
  }, []);

  const speakQuestion = async (text: string) => {
    setStage("speaking");
    let objectUrl: string | null = null;
    try {
      const blob = await textToSpeech(text);
      objectUrl = URL.createObjectURL(blob);
      const audio = new Audio(objectUrl);
      await new Promise<void>((resolve) => { audio.onended = () => resolve(); audio.onerror = () => resolve(); audio.play().catch(() => resolve()); });
    } catch { } finally { if (objectUrl) URL.revokeObjectURL(objectUrl); }
    setStage("recording");
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      audioStreamRef.current = stream;
      const mimeType = getSupportedMimeType();
      mimeTypeRef.current = mimeType;
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      audioChunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      recorder.start(100);
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch { setError("Microphone access denied."); }
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") return;
    setIsRecording(false); setStage("transcribing");
    recorder.onstop = async () => {
      const mimeType = mimeTypeRef.current || "audio/webm";
      const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
      audioStreamRef.current?.getTracks().forEach((t) => t.stop());
      audioStreamRef.current = null;
      hume.analyzeAudio(audioBlob);
      try {
        const sttResult = await speechToText(audioBlob);
        if (!sttResult.transcript.trim()) { setError("No speech detected. Please try again."); setStage("recording"); return; }
        setTranscript(sttResult.transcript);
        await handleSubmit(sttResult.transcript);
      } catch { setError("Failed to transcribe audio. Please try again."); setStage("recording"); }
    };
    recorder.stop();
  };

  const handleSubmit = async (answerText: string) => {
    if (!sessionId || !answerText.trim()) return;
    setStage("evaluating");
    try {
      const result = await submitAnswer(sessionId, answerText);
      setFeedback({ score: result.score, feedback: result.feedback });
      setAllAnswers((prev) => [...prev, { question, answer: answerText, score: result.score, feedback: result.feedback }]);
      setAttempts((p) => p + 1); setStage("feedback");
      if (result.interview_complete) {
        setIsComplete(true);
        getReport(sessionId).then((r) => { cachedReport.current = r; setReportReady(true); }).catch(() => {});
      }
    } catch { setError("Failed to evaluate answer."); setStage("recording"); }
  };

  const handleNext = async () => {
    if (!sessionId) return;
    setFeedback(null); setTranscript(""); setAttempts(0); setError(null); setStage("loading");
    try {
      const q = await getQuestion(sessionId);
      setQuestion(q.question); setQuestionNumber(q.question_number); setQuestionLayer(q.layer || "basic");
      await speakQuestion(q.question);
    } catch { setError("Failed to load next question."); setStage("recording"); }
  };

  const handleRetry = async () => { setFeedback(null); setTranscript(""); setError(null); await speakQuestion(question); };

  const avgScore = allAnswers.length ? Math.round((allAnswers.reduce((s, a) => s + a.score, 0) / allAnswers.length) * 10) / 10 : 0;
  const getLevel = (s: number) => s >= 8.5 ? "Expert" : s >= 7 ? "Advanced" : s >= 5 ? "Intermediate" : "Beginner";
  const scoreColor = (s: number) => s >= 7 ? "text-green-600" : s >= 4 ? "text-yellow-600" : "text-red-600";
  const scoreBg = (s: number) => s >= 7 ? "bg-green-500/10 border-green-500/20" : s >= 4 ? "bg-yellow-500/10 border-yellow-500/20" : "bg-red-500/10 border-red-500/20";
  const ScoreIcon = ({ score }: { score: number }) => score >= 7 ? <CheckCircle className="w-4 h-4 text-green-600" /> : score >= 4 ? <AlertTriangle className="w-4 h-4 text-yellow-600" /> : <XCircle className="w-4 h-4 text-red-600" />;
  const formatTime = (s: number) => `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;
  const layerColor = (layer: string) => layer === "advanced" ? "bg-red-500/10 text-red-600 border-red-500/20" : layer === "intermediate" ? "bg-yellow-500/10 text-yellow-600 border-yellow-500/20" : "bg-green-500/10 text-green-600 border-green-500/20";

  // ── SUMMARY SCREEN ──────────────────────────────────────
  if (isComplete) {
    return (
      <div className="min-h-screen bg-background px-6 py-8 overflow-y-auto">
        <div className="max-w-[680px] mx-auto">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-semibold text-foreground mb-1">Interview Complete</h1>
            <p className="text-sm text-muted-foreground">Domain: {domain}</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-6 mb-4 text-center">
            <p className="text-5xl font-bold text-primary mb-1">{avgScore}<span className="text-2xl text-muted-foreground">/10</span></p>
            <span className="inline-block px-4 py-1 rounded-full bg-primary/10 text-primary font-medium text-sm">{getLevel(avgScore)}</span>
          </div>
          <div className="space-y-2 mb-6">
            {allAnswers.map((a, i) => (
              <div key={i} className={`bg-card border rounded-xl p-4 ${scoreBg(a.score)}`}>
                <div className="flex items-start justify-between gap-3 mb-1">
                  <p className="text-sm font-medium text-foreground">Q{i + 1}: {a.question}</p>
                  <div className="flex items-center gap-1 flex-shrink-0"><ScoreIcon score={a.score} /><span className={`text-sm font-semibold ${scoreColor(a.score)}`}>{a.score}/10</span></div>
                </div>
                <p className="text-xs text-muted-foreground italic mb-1">"{a.answer}"</p>
                <p className="text-xs text-muted-foreground">{a.feedback}</p>
              </div>
            ))}
          </div>
          <div className="flex gap-3 justify-center">
            <Button variant="outline" onClick={() => navigate("/")}>New Interview</Button>
            <Button onClick={() => navigate("/feedback", { state: { sessionId, domain, cachedReport: cachedReport.current } })}>
              {reportReady ? "View Full Report" : "Generate Report"}
              {!reportReady && <Loader2 className="w-4 h-4 ml-2 animate-spin" />}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ── INTERVIEW SCREEN — fixed viewport, no scroll ─────────
  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">

      {/* Top bar */}
      <header className="flex-shrink-0 flex items-center justify-between px-5 py-2.5 border-b border-border bg-card">
        <div>
          <h1 className="text-sm font-semibold text-foreground">Live Interview</h1>
          <p className="text-xs text-muted-foreground">{domain}</p>
        </div>
        <div className="flex items-center gap-3">
          {error && (
            <span className="text-xs text-destructive bg-destructive/10 border border-destructive/20 px-3 py-1 rounded-full">{error}</span>
          )}
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" size="sm" className="h-8 px-4 text-xs">End Interview</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>End Interview Session?</AlertDialogTitle>
                <AlertDialogDescription>Are you sure you want to end the interview?</AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Continue</AlertDialogCancel>
                <AlertDialogAction onClick={() => navigate("/feedback", { state: { sessionId, domain } })}>End & View Feedback</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </header>

      {/* Main content — fills remaining height */}
      <div className="flex-1 flex overflow-hidden">

        {/* Left — camera + controls */}
        <div className="flex flex-col flex-1 min-w-0 p-4 gap-3">

          {/* Camera — fills available space */}
          <div className="relative flex-1 bg-[hsl(var(--camera-bg))] rounded-xl overflow-hidden min-h-0">
            {/* Top overlay: timer + camera toggle */}
            <div className="absolute inset-x-0 top-0 p-3 bg-gradient-to-b from-black/60 to-transparent z-10 flex items-center justify-between">
              <div className={`flex items-center gap-1.5 bg-black/50 backdrop-blur-sm rounded-lg px-2.5 py-1.5 ${timeLeft < 60 ? "border border-red-500/60" : ""}`}>
                <Clock className={`w-3.5 h-3.5 ${timeLeft < 60 ? "text-red-400" : "text-white/80"}`} />
                <span className={`font-mono text-sm font-semibold ${timeLeft < 60 ? "text-red-400" : "text-white"}`}>{formatTime(timeLeft)}</span>
              </div>
              <div className="flex items-center gap-2">
                {/* Q badge */}
                <span className="text-xs font-medium text-white/80 bg-black/40 px-2 py-1 rounded-lg">Q{questionNumber}</span>
                <button onClick={toggleCamera} className={`p-1.5 rounded-lg transition-colors ${isCameraOn ? "bg-white/20 text-white hover:bg-white/30" : "bg-red-500/80 text-white"}`}>
                  {isCameraOn ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Video */}
            <video ref={videoRef} autoPlay playsInline muted className={`w-full h-full object-cover ${isCameraOn ? "block" : "hidden"}`} />
            {!isCameraOn && (
              <div className="w-full h-full flex items-center justify-center bg-muted/10">
                <VideoOff className="w-12 h-12 text-white/20" />
              </div>
            )}

            {/* Coaching hint */}
            {coachingHint && (
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 pointer-events-none">
                <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-black/70 backdrop-blur-sm border border-white/10 shadow-lg">
                  <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse flex-shrink-0" />
                  <span className="text-xs font-medium text-white whitespace-nowrap">{coachingHint}</span>
                </div>
              </div>
            )}
          </div>

          {/* Controls panel */}
          <div className="flex-shrink-0 bg-card border border-border rounded-xl px-5 py-3">
            {stage === "loading" && (
              <div className="flex items-center justify-center gap-2 py-1">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">Starting interview...</span>
              </div>
            )}
            {stage === "speaking" && (
              <div className="flex items-center justify-center gap-2 py-1">
                <Volume2 className="w-4 h-4 text-primary animate-pulse" />
                <span className="text-sm text-foreground">Speaking question...</span>
              </div>
            )}
            {stage === "recording" && !isRecording && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">Ready to record your answer</p>
                <Button onClick={startRecording} size="sm" className="gap-2 px-5">
                  <Mic className="w-4 h-4" /> Start Recording
                </Button>
              </div>
            )}
            {stage === "recording" && isRecording && (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-sm text-red-600 font-medium">Recording in progress...</span>
                </div>
                <Button onClick={stopRecording} variant="destructive" size="sm" className="gap-2 px-5">
                  <MicOff className="w-4 h-4" /> Stop Recording
                </Button>
              </div>
            )}
            {stage === "transcribing" && (
              <div className="flex items-center justify-center gap-2 py-1">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">Transcribing your answer...</span>
              </div>
            )}
            {stage === "evaluating" && (
              <div className="flex items-center justify-center gap-2 py-1">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">Evaluating your answer...</span>
                {transcript && <span className="text-xs text-muted-foreground italic ml-1 truncate max-w-[200px]">"{transcript}"</span>}
              </div>
            )}
            {stage === "feedback" && feedback && (
              <div className="flex items-center gap-4">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${scoreBg(feedback.score)}`}>
                  <ScoreIcon score={feedback.score} />
                  <span className={`text-sm font-semibold ${scoreColor(feedback.score)}`}>{feedback.score}/10</span>
                </div>
                <p className="text-xs text-muted-foreground flex-1 line-clamp-2">{feedback.feedback}</p>
                <div className="flex gap-2 flex-shrink-0">
                  {feedback.score >= 5 ? (
                    <Button onClick={handleNext} size="sm" className="px-4">Next</Button>
                  ) : attempts < 2 ? (
                    <>
                      <Button onClick={handleRetry} variant="outline" size="sm">Retry</Button>
                      <Button onClick={handleNext} variant="ghost" size="sm">Skip</Button>
                    </>
                  ) : (
                    <Button onClick={handleNext} size="sm" className="px-4">Next</Button>
                  )}
                </div>
              </div>
            )}
            {stage === "feedback" && !feedback && !error && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">Something went wrong.</p>
                <Button onClick={handleRetry} variant="outline" size="sm">Retry</Button>
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar — fixed width, scrollable */}
        <div className="w-72 flex-shrink-0 border-l border-border flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-3 space-y-3">

            {/* Question card */}
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="text-xs font-bold text-primary">{questionNumber}</span>
                  </div>
                  <span className="text-xs font-medium text-muted-foreground">Question {questionNumber}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${layerColor(questionLayer)}`}>{questionLayer}</span>
              </div>
              {stage === "loading" ? (
                <div className="flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" /><span className="text-xs text-muted-foreground">Loading...</span></div>
              ) : (
                <p className="text-sm font-medium text-foreground leading-relaxed">{question}</p>
              )}
            </div>

            {/* Progress */}
            {allAnswers.length > 0 && (
              <div className="bg-card border border-border rounded-xl p-4">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Progress</h3>
                <div className="space-y-1.5">
                  {allAnswers.map((a, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground truncate max-w-[150px]">Q{i + 1}: {a.question.slice(0, 28)}…</span>
                      <span className={`font-semibold flex-shrink-0 ml-2 ${scoreColor(a.score)}`}>{a.score}/10</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Face Analysis */}
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-semibold text-foreground">Face Analysis</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex items-center gap-1 ${faceMetrics.status === "ready" ? "bg-green-500/15 text-green-600" : "bg-muted text-muted-foreground"}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${faceMetrics.status === "ready" ? "bg-green-500 animate-pulse" : "bg-muted-foreground"}`} />
                  {faceMetrics.status === "ready" ? "Live" : faceMetrics.status === "error" ? "Error" : "Loading"}
                </span>
              </div>
              {faceMetrics.status === "loading" && <div className="flex items-center gap-2 text-muted-foreground"><Loader2 className="w-3.5 h-3.5 animate-spin" /><span className="text-xs">Loading model...</span></div>}
              {faceMetrics.status === "error" && <p className="text-xs text-red-500">Failed to load face model.</p>}
              {faceMetrics.status === "ready" && (
                !faceMetrics.faceDetected ? (
                  <p className="text-xs text-muted-foreground text-center py-2">No face detected</p>
                ) : (
                  <div className="space-y-1.5">
                    {[
                      { icon: Eye, label: "Eye Contact", value: faceMetrics.eyeContact ? "Good" : "Off", ok: faceMetrics.eyeContact },
                      { icon: Focus, label: "Focus", value: faceMetrics.lookingAway ? "Away" : "Focused", ok: !faceMetrics.lookingAway },
                      { icon: ScanFace, label: "Head Pose", value: faceMetrics.headPose, ok: faceMetrics.headPose === "center" },
                    ].map(({ icon: Icon, label, value, ok }) => (
                      <div key={label} className="flex items-center justify-between p-1.5 rounded-lg bg-muted/30">
                        <div className="flex items-center gap-1.5"><Icon className="w-3 h-3 text-muted-foreground" /><span className="text-xs text-foreground">{label}</span></div>
                        <span className={`text-xs font-medium px-1.5 py-0.5 rounded-full capitalize ${ok ? "bg-green-500/15 text-green-600" : "bg-yellow-500/15 text-yellow-600"}`}>{value}</span>
                      </div>
                    ))}
                    <div className="p-1.5 rounded-lg bg-muted/30">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-foreground">Smile</span>
                        <span className="text-xs text-muted-foreground">{Math.round(faceMetrics.smileScore * 100)}%</span>
                      </div>
                      <div className="w-full h-1 bg-muted rounded-full overflow-hidden">
                        <div className={`h-full rounded-full transition-all duration-300 ${faceMetrics.smileScore > 0.4 ? "bg-green-500" : faceMetrics.smileScore > 0.2 ? "bg-yellow-500" : "bg-muted-foreground/40"}`} style={{ width: `${faceMetrics.smileScore * 100}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center justify-between p-1.5 rounded-lg bg-muted/30">
                      <span className="text-xs text-foreground">Mouth</span>
                      <span className={`text-xs font-medium px-1.5 py-0.5 rounded-full ${faceMetrics.mouthOpen ? "bg-yellow-500/15 text-yellow-600" : "bg-muted text-muted-foreground"}`}>{faceMetrics.mouthOpen ? "Open" : "Closed"}</span>
                    </div>
                    <div className="flex items-center justify-between p-1.5 rounded-lg bg-muted/30">
                      <span className="text-xs text-foreground">Eyebrow</span>
                      <span className={`text-xs font-medium px-1.5 py-0.5 rounded-full ${faceMetrics.eyebrowRaise ? "bg-blue-500/15 text-blue-500" : "bg-muted text-muted-foreground"}`}>{faceMetrics.eyebrowRaise ? "Raised" : "Neutral"}</span>
                    </div>
                  </div>
                )
              )}
            </div>

            {/* Speech Prosody */}
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-semibold text-foreground">Speech Prosody</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex items-center gap-1 ${hume.analyzing ? "bg-blue-500/15 text-blue-600" : "bg-muted text-muted-foreground"}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${hume.analyzing ? "bg-blue-500 animate-pulse" : "bg-muted-foreground"}`} />
                  {hume.analyzing ? "Analyzing..." : "Ready"}
                </span>
              </div>
              {(() => {
                const list = hume.emotions.prosody;
                if (list.length === 0) return <p className="text-xs text-muted-foreground text-center py-2">{hume.analyzing ? "Analyzing speech..." : "Results appear after recording"}</p>;
                return (
                  <div className="space-y-1.5">
                    {list.slice(0, 5).map((e, i) => (
                      <div key={e.name} className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground w-3">{i + 1}</span>
                        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-primary/60 rounded-full" style={{ width: `${e.score * 100}%` }} />
                        </div>
                        <span className="text-xs text-foreground capitalize w-20 truncate">{e.name}</span>
                        <span className="text-xs text-muted-foreground w-8 text-right">{(e.score * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>

            {/* Instructions — compact */}
            <div className="bg-card border border-border rounded-xl p-4">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Instructions</h3>
              <div className="space-y-1.5 text-xs text-muted-foreground">
                <div className="flex items-center gap-2"><Volume2 className="w-3 h-3 text-primary flex-shrink-0" />Listen to the question</div>
                <div className="flex items-center gap-2"><Mic className="w-3 h-3 text-primary flex-shrink-0" />Click Start Recording to answer</div>
                <div className="flex items-center gap-2"><MicOff className="w-3 h-3 text-primary flex-shrink-0" />Click Stop when done speaking</div>
                <div className="flex items-center gap-2"><AlertCircle className="w-3 h-3 text-primary flex-shrink-0" />Speak clearly and in detail</div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveInterview;
