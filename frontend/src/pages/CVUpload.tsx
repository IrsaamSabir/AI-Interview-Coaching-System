import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  FileText,
  CheckCircle,
  Loader2,
  X,
  Plus,
  ArrowRight,
  Mic,
  BarChart2,
  Brain,
  ShieldCheck,
  Briefcase,
  Clock,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { analyzeCV } from "@/lib/api";

function formatTotalExperienceMonths(totalMonths: unknown): string | null {
  const n = typeof totalMonths === "number" ? totalMonths : Number(totalMonths);
  if (!Number.isFinite(n) || n < 0) return null;
  if (n === 0) return "0 months";
  const y = Math.floor(n / 12);
  const m = n % 12;
  if (y === 0) return `${m} month${m === 1 ? "" : "s"}`;
  if (m === 0) return `${y} year${y === 1 ? "" : "s"}`;
  return `${y} year${y === 1 ? "" : "s"} ${m} month${m === 1 ? "" : "s"}`;
}

function buildExperienceLabel(result: {
  years_experience?: unknown;
  total_experience_months?: unknown;
}): string | null {
  const text =
    result.years_experience !== undefined && result.years_experience !== null
      ? String(result.years_experience).trim()
      : "";
  const fromMonths = formatTotalExperienceMonths(result.total_experience_months);
  if (text) return text;
  if (fromMonths) return fromMonths;
  return null;
}

function normalizeSkill(value: string): string {
  return value.trim().toLowerCase();
}

type InterviewExperienceFromCv = {
  yearsExperience?: string;
  totalExperienceMonths?: number;
  jobs?: Array<Record<string, unknown>>;
};

function buildInterviewExperienceFromCv(result: Record<string, unknown>): InterviewExperienceFromCv {
  const years =
    typeof result.years_experience === "string" && result.years_experience.trim()
      ? result.years_experience.trim()
      : undefined;
  let months: number | undefined;
  if (typeof result.total_experience_months === "number" && Number.isFinite(result.total_experience_months)) {
    months = Math.max(0, Math.round(result.total_experience_months));
  } else if (result.total_experience_months != null && result.total_experience_months !== "") {
    const n = Number(result.total_experience_months);
    if (Number.isFinite(n)) months = Math.max(0, Math.round(n));
  }
  const jobs = Array.isArray(result.jobs) ? (result.jobs as Array<Record<string, unknown>>) : undefined;
  return { yearsExperience: years, totalExperienceMonths: months, jobs };
}

const CVUpload = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [detectedDomain, setDetectedDomain] = useState<string | null>(null);
  const [detectedSkills, setDetectedSkills] = useState<string[]>([]);
  const [prioritySkills, setPrioritySkills] = useState<string[]>([]);
  const [manualSkillInput, setManualSkillInput] = useState("");
  const [experienceLabel, setExperienceLabel] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [howItWorksOpen, setHowItWorksOpen] = useState(true);
  const [interviewExperience, setInterviewExperience] = useState<InterviewExperienceFromCv | null>(null);

  const processFile = useCallback(async (selectedFile: File) => {
    setFile(selectedFile);
    setIsLoading(true);
    setError(null);
    setDetectedDomain(null);
    setDetectedSkills([]);
    setPrioritySkills([]);
    setManualSkillInput("");
    setExperienceLabel(null);
    setInterviewExperience(null);
    try {
      const result = await analyzeCV(selectedFile);
      setDetectedDomain(result.domain);
      setDetectedSkills(result.skills || []);
      setExperienceLabel(buildExperienceLabel(result));
      setInterviewExperience(buildInterviewExperienceFromCv(result as Record<string, unknown>));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to analyze document. Please upload a valid CV.";
      setError(message);
      setFile(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  }, []);
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragActive(false);
      const f = e.dataTransfer.files[0];
      if (f) processFile(f);
    },
    [processFile],
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (f) processFile(f);
    },
    [processFile],
  );

  const handleStart = () => {
    if (file && detectedDomain) {
      navigate("/interview", {
        state: {
          domain: detectedDomain,
          skills: detectedSkills,
          prioritySkills,
          yearsExperience: interviewExperience?.yearsExperience,
          totalExperienceMonths: interviewExperience?.totalExperienceMonths,
          jobs: interviewExperience?.jobs,
        },
      });
    }
  };

  const addPrioritySkill = useCallback(() => {
    const skill = normalizeSkill(manualSkillInput);
    if (!skill) return;
    setPrioritySkills((prev) => {
      if (prev.includes(skill)) return prev;
      return prev.length >= 5 ? prev : [...prev, skill];
    });
    setManualSkillInput("");
  }, [manualSkillInput]);

  const removePrioritySkill = useCallback((skillToRemove: string) => {
    setPrioritySkills((prev) => prev.filter((skill) => skill !== skillToRemove));
  }, []);

  const handleManualSkillKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();
        addPrioritySkill();
        return;
      }
      if (e.key === "Backspace" && !manualSkillInput && prioritySkills.length > 0) {
        e.preventDefault();
        setPrioritySkills((prev) => prev.slice(0, -1));
      }
    },
    [addPrioritySkill, manualSkillInput, prioritySkills.length],
  );

  const canStart = !!file && !!detectedDomain && !isLoading;
  const hasProfile = Boolean(detectedDomain && detectedSkills.length > 0);

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <header className="flex shrink-0 items-center justify-between border-b border-border bg-card px-4 py-2.5 sm:px-6 sm:py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
            <Brain className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="text-sm font-semibold text-foreground">InterviewAI</span>
        </div>
        <span className="text-xs text-muted-foreground">AI-Powered Interview Coaching</span>
      </header>

      <div
        className={`flex min-h-0 flex-1 flex-col px-4 py-3 sm:px-6 sm:py-4 ${
          hasProfile ? "items-stretch" : "items-center justify-center py-8 sm:py-12"
        }`}
      >
        <div className="flex min-h-0 w-full max-w-5xl flex-1 flex-col lg:mx-auto">
          <div className={`shrink-0 text-center ${hasProfile ? "mb-3 sm:mb-4" : "mb-8 sm:mb-10"}`}>
            <h1
              className={`font-bold tracking-tight text-foreground ${hasProfile ? "text-xl sm:text-2xl" : "mb-3 text-3xl"}`}
            >
              Start Your Mock Interview
            </h1>
            {!hasProfile && (
              <p className="mx-auto max-w-md text-muted-foreground">
                Upload your CV and our AI will tailor a technical interview to your skills and experience.
              </p>
            )}
          </div>

          <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-12 lg:gap-6 lg:items-stretch">
            <div className="flex h-full min-h-0 flex-col gap-3 lg:col-span-7 lg:gap-3">
              <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pr-0.5">
              <div className={`card-elevated shrink-0 ${hasProfile ? "p-4" : "p-6"}`}>
                <p className={`font-medium text-foreground ${hasProfile ? "mb-2 text-xs sm:text-sm" : "mb-4 text-sm"}`}>
                  Upload your CV
                </p>

                <input type="file" id="cv-upload" className="hidden" accept=".pdf,.docx" onChange={handleFileInput} />

                <label
                  htmlFor="cv-upload"
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={
                    hasProfile && file && detectedDomain && !isLoading
                      ? `flex cursor-pointer items-center gap-3 rounded-xl border-2 border-dashed p-3.5 transition-all duration-200 sm:p-4
                        ${isDragActive ? "border-primary bg-primary/5" : "border-primary/35 bg-primary/5 hover:border-primary/60 hover:bg-muted/30"}
                        ${error ? "border-destructive/40" : ""}`
                      : `flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed transition-all duration-200 sm:gap-4
                        ${hasProfile ? "p-6 sm:p-8" : "p-8 sm:p-10"}
                        ${isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/60 hover:bg-muted/30"}
                        ${file && !error ? "border-primary/40 bg-primary/5" : ""}`
                  }
                >
                  {isLoading ? (
                    <>
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 sm:h-14 sm:w-14">
                        <Loader2 className="h-6 w-6 animate-spin text-primary sm:h-7 sm:w-7" />
                      </div>
                      <div className="min-w-0 flex-1 text-center sm:text-left">
                        <p className="text-sm font-medium text-foreground">Analyzing your CV...</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">This takes a few seconds</p>
                      </div>
                      <div className="hidden h-1 w-32 shrink-0 overflow-hidden rounded-full bg-muted sm:block">
                        <div className="h-full w-2/3 animate-pulse rounded-full bg-primary" />
                      </div>
                    </>
                  ) : hasProfile && file && detectedDomain ? (
                    <>
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-green-500/10">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-foreground">{file.name}</p>
                        <p className="text-xs text-green-600">CV analyzed — click to replace</p>
                      </div>
                      <span className="shrink-0 text-xs font-medium text-primary underline-offset-2 hover:underline">
                        Change
                      </span>
                    </>
                  ) : (
                    <>
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted sm:h-14 sm:w-14">
                        <Upload className="h-6 w-6 text-muted-foreground sm:h-7 sm:w-7" />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-semibold text-foreground">Drop your CV here</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">or click to browse</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="rounded-md bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">PDF</span>
                        <span className="rounded-md bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">DOCX</span>
                      </div>
                    </>
                  )}
                </label>

                {error && (
                  <div className="mt-4 flex items-start gap-2.5 rounded-lg border border-destructive/25 bg-destructive/8 p-3.5">
                    <X className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                    <p className="text-sm text-destructive">{error}</p>
                  </div>
                )}
              </div>

              {detectedDomain && detectedSkills.length > 0 && (
                <div className="card-elevated flex min-h-0 flex-1 flex-col overflow-hidden p-0 lg:min-h-0">
                  <div className="flex shrink-0 flex-col gap-2 border-b border-border bg-muted/25 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5 sm:py-3.5">
                    <div className="flex min-w-0 items-center gap-2.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/15">
                        <FileText className="h-4 w-4" aria-hidden />
                      </div>
                      <h2 className="text-sm font-semibold tracking-tight text-foreground">Detected profile</h2>
                    </div>
                    <span className="inline-flex w-fit items-center rounded-full border border-border bg-background px-2.5 py-0.5 text-[11px] font-medium tabular-nums text-muted-foreground shadow-sm sm:shrink-0">
                      {detectedSkills.length} skills
                    </span>
                  </div>

                  <div className="flex min-h-0 flex-1 flex-col gap-3 px-4 py-3 sm:px-5 sm:py-4">
                    <div className={`grid shrink-0 gap-2.5 ${experienceLabel ? "sm:grid-cols-2" : "grid-cols-1"}`}>
                      <div className="rounded-lg border border-border bg-background p-3 shadow-sm ring-1 ring-black/[0.03] dark:ring-white/[0.04] sm:p-3.5">
                        <div className="flex gap-2.5 sm:gap-3">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary sm:h-9 sm:w-9">
                            <Briefcase className="h-4 w-4 sm:h-[18px] sm:w-[18px]" aria-hidden />
                          </div>
                          <div className="min-w-0 flex-1 space-y-0.5">
                            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Domain</p>
                            <p className="text-sm font-semibold capitalize leading-snug text-foreground sm:text-[15px]">
                              {detectedDomain}
                            </p>
                          </div>
                        </div>
                      </div>
                      {experienceLabel ? (
                        <div className="rounded-lg border border-border bg-background p-3 shadow-sm ring-1 ring-black/[0.03] dark:ring-white/[0.04] sm:p-3.5">
                          <div className="flex gap-2.5 sm:gap-3">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary sm:h-9 sm:w-9">
                              <Clock className="h-4 w-4 sm:h-[18px] sm:w-[18px]" aria-hidden />
                            </div>
                            <div className="min-w-0 flex-1 space-y-0.5">
                              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                                Experience
                              </p>
                              <p className="text-sm font-semibold leading-snug text-foreground sm:text-[15px]">{experienceLabel}</p>
                            </div>
                          </div>
                        </div>
                      ) : null}
                    </div>

                    <div className="shrink-0 border-t border-border pt-2.5">
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                          Priority skills
                        </p>
                        <span className="text-[10px] text-muted-foreground">{prioritySkills.length}/5</span>
                      </div>
                      {prioritySkills.length > 0 && (
                        <div className="mb-2 flex flex-wrap gap-2">
                          {prioritySkills.map((skill) => (
                            <span
                              key={skill}
                              className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary"
                            >
                              {skill}
                              <button
                                type="button"
                                onClick={() => removePrioritySkill(skill)}
                                className="rounded-full p-0.5 text-primary/80 transition hover:bg-primary/15 hover:text-primary"
                                aria-label={`Remove ${skill}`}
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={manualSkillInput}
                          onChange={(e) => setManualSkillInput(e.target.value)}
                          onKeyDown={handleManualSkillKeyDown}
                          placeholder="Add must-ask skill"
                          className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 placeholder:text-muted-foreground focus:border-primary"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          onClick={addPrioritySkill}
                          disabled={!manualSkillInput.trim() || prioritySkills.length >= 5}
                          className="shrink-0"
                        >
                          <Plus className="mr-1 h-4 w-4" />
                          Add
                        </Button>
                      </div>
                      <p className="mt-1.5 text-xs text-muted-foreground">
                        Press Enter to turn a skill into a block. Click x to remove it.
                      </p>
                    </div>

                    <div className="flex min-h-0 flex-1 flex-col border-t border-border pt-2.5">
                      <p className="mb-2 shrink-0 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                        Skills
                      </p>
                      <div className="min-h-0 max-h-[30vh] flex-1 overflow-y-auto overscroll-contain pr-0.5 sm:max-h-[34vh]">
                        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 sm:gap-2">
                          {detectedSkills.map((skill) => (
                            <span
                              key={skill}
                              title={skill}
                              className="truncate rounded-md border border-border bg-muted/50 px-2 py-1 text-center text-[11px] font-medium capitalize text-foreground sm:text-xs"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              </div>

              <Button
                onClick={handleStart}
                disabled={!canStart}
                size="lg"
                className="h-11 w-full shrink-0 text-sm font-semibold sm:h-12"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing...
                  </>
                ) : (
                  <>
                    <span>Start Interview</span>
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>

            <aside className="flex w-full flex-col lg:col-span-5 lg:self-start">
              <div className="flex flex-col overflow-hidden rounded-xl border border-border bg-card shadow-sm">
                <button
                  type="button"
                  onClick={() => setHowItWorksOpen((o) => !o)}
                  className={`flex w-full shrink-0 items-center justify-between gap-2 border-border bg-muted/30 px-4 py-3 text-left transition-colors hover:bg-muted/45 sm:px-4 sm:py-3.5 ${
                    howItWorksOpen ? "rounded-t-xl border-b" : "rounded-xl border-b-0"
                  }`}
                  aria-expanded={howItWorksOpen}
                >
                  <span className="text-sm font-semibold text-foreground">How it works</span>
                  <ChevronDown
                    className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 ${
                      howItWorksOpen ? "rotate-180" : ""
                    }`}
                    aria-hidden
                  />
                </button>

                {howItWorksOpen ? (
                  <div className="px-4 py-3 sm:px-4 sm:py-4">
                    <div className="space-y-2.5 sm:space-y-3">
                      {[
                        {
                          step: "01",
                          icon: Upload,
                          title: "Upload your CV",
                          desc: "Our AI reads your skills, experience, and domain to personalize the session.",
                        },
                        {
                          step: "02",
                          icon: Mic,
                          title: "Answer questions",
                          desc: "Speak your answers naturally. Questions adapt based on your performance.",
                        },
                        {
                          step: "03",
                          icon: BarChart2,
                          title: "Get scored live",
                          desc: "Every answer is evaluated instantly with a score and constructive feedback.",
                        },
                        {
                          step: "04",
                          icon: ShieldCheck,
                          title: "Review your report",
                          desc: "Receive a full breakdown of strengths, weaknesses, and recommendations.",
                        },
                      ].map((item) => (
                        <div
                          key={item.step}
                          className="flex items-start gap-3 rounded-lg border border-border bg-background p-3.5 transition-colors hover:border-primary/35 sm:gap-3.5 sm:p-4"
                        >
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                            <item.icon className="h-4 w-4 text-primary sm:h-[18px] sm:w-[18px]" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="mb-1 flex flex-wrap items-center gap-x-2 gap-y-0.5">
                              <span className="text-[11px] font-bold tracking-widest text-primary/70">{item.step}</span>
                              <p className="text-sm font-semibold leading-snug text-foreground">{item.title}</p>
                            </div>
                            <p className="text-xs leading-relaxed text-muted-foreground sm:text-[13px] sm:leading-relaxed">
                              {item.desc}
                            </p>
                          </div>
                        </div>
                      ))}

                      <div className="flex items-start gap-2.5 rounded-lg border border-border bg-muted/40 p-3 sm:p-3.5">
                        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                        <p className="text-xs leading-relaxed text-muted-foreground sm:text-[13px]">
                          Your CV is processed securely and is not stored permanently after analysis.
                        </p>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </aside>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CVUpload;
