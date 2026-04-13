import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { RefreshCcw, Loader2, CheckCircle, XCircle, AlertTriangle, TrendingUp, Award, Target, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getReport } from "@/lib/api";

interface AnswerRecord {
  question: string;
  answer: string;
  score: number;
  feedback: string;
  layer?: string;
}

interface Report {
  overall_score: number;
  average_score: number;
  level: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  skill_scores: Record<string, number>;
  recommendation: string;
  domain: string;
  stack: string;
  answered: number;
  total_questions: number;
  answers: AnswerRecord[];
  scores: number[];
  status: string;
}

const scoreColor = (s: number) =>
  s >= 7 ? "text-green-600" : s >= 4 ? "text-yellow-600" : "text-red-500";

const scoreBg = (s: number) =>
  s >= 7 ? "bg-green-500/10 border-green-500/20"
  : s >= 4 ? "bg-yellow-500/10 border-yellow-500/20"
  : "bg-red-500/10 border-red-500/20";

const scoreBarColor = (s: number) =>
  s >= 7 ? "bg-green-500" : s >= 4 ? "bg-yellow-500" : "bg-red-500";

const ScoreIcon = ({ score }: { score: number }) =>
  score >= 7 ? <CheckCircle className="w-4 h-4 text-green-600" />
  : score >= 4 ? <AlertTriangle className="w-4 h-4 text-yellow-600" />
  : <XCircle className="w-4 h-4 text-red-500" />;

const layerBadge = (layer?: string) =>
  layer === "advanced" ? "bg-red-500/10 text-red-600 border-red-500/20"
  : layer === "intermediate" ? "bg-yellow-500/10 text-yellow-600 border-yellow-500/20"
  : "bg-green-500/10 text-green-600 border-green-500/20";

const getLevel = (s: number) =>
  s >= 8.5 ? "Expert" : s >= 7 ? "Advanced" : s >= 5 ? "Intermediate" : "Beginner";

const levelColor = (l: string) =>
  l === "Expert" ? "bg-purple-500/10 text-purple-600 border-purple-500/20"
  : l === "Advanced" ? "bg-blue-500/10 text-blue-600 border-blue-500/20"
  : l === "Intermediate" ? "bg-yellow-500/10 text-yellow-600 border-yellow-500/20"
  : "bg-red-500/10 text-red-500 border-red-500/20";

const Feedback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId: string | null = location.state?.sessionId || null;
  const domain = location.state?.domain || "Software Engineering";
  const cachedReport = location.state?.cachedReport || null;

  const [report, setReport] = useState<Report | null>(cachedReport);
  const [isLoading, setIsLoading] = useState(!cachedReport);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cachedReport) return;
    if (!sessionId) {
      setError("No session found. Please complete an interview first.");
      setIsLoading(false);
      return;
    }
    getReport(sessionId)
      .then(setReport)
      .catch(() => setError("Failed to load report. Please try again."))
      .finally(() => setIsLoading(false));
  }, [sessionId]);

  if (isLoading) {
    return (
      <div className="page-centered">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Generating your report...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="page-centered">
        <div className="text-center space-y-4">
          <p className="text-destructive">{error || "No report available."}</p>
          <Button onClick={() => navigate("/")}>Back to Home</Button>
        </div>
      </div>
    );
  }

  const overallScore = report.overall_score ?? report.average_score ?? 0;
  const level = report.level || getLevel(overallScore);
  const scorePercent = (overallScore / 10) * 100;
  const answers: AnswerRecord[] = report.answers || [];

  // Score distribution
  const scores = report.scores || answers.map(a => a.score);
  const highCount = scores.filter(s => s >= 7).length;
  const midCount  = scores.filter(s => s >= 4 && s < 7).length;
  const lowCount  = scores.filter(s => s < 4).length;

  return (
    <div className="page-container">
      <div className="max-w-[860px] mx-auto">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold text-foreground mb-1">Interview Report</h1>
          <p className="text-sm text-muted-foreground">
            {report.domain || domain}{report.stack ? ` · ${report.stack}` : ""}
          </p>
        </div>

        {/* Score Hero */}
        <div className="card-section mb-6">
          <div className="flex flex-col sm:flex-row items-center gap-6">
            {/* Circular score */}
            <div className="relative flex-shrink-0">
              <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/30" />
                <circle
                  cx="50" cy="50" r="42" fill="none" strokeWidth="8"
                  strokeLinecap="round"
                  className={overallScore >= 7 ? "text-green-500" : overallScore >= 4 ? "text-yellow-500" : "text-red-500"}
                  stroke="currentColor"
                  strokeDasharray={`${2 * Math.PI * 42}`}
                  strokeDashoffset={`${2 * Math.PI * 42 * (1 - scorePercent / 100)}`}
                  style={{ transition: "stroke-dashoffset 1s ease" }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-2xl font-bold ${scoreColor(overallScore)}`}>{overallScore.toFixed(1)}</span>
                <span className="text-xs text-muted-foreground">/10</span>
              </div>
            </div>

            {/* Level + summary */}
            <div className="flex-1 text-center sm:text-left">
              <span className={`inline-block text-xs font-semibold px-3 py-1 rounded-full border mb-2 ${levelColor(level)}`}>
                {level}
              </span>
              <p className="text-sm text-muted-foreground leading-relaxed">{report.summary}</p>
            </div>

            {/* Quick stats */}
            <div className="flex sm:flex-col gap-4 sm:gap-2 flex-shrink-0 text-center">
              <div>
                <p className="text-lg font-bold text-foreground">{report.answered ?? answers.length}</p>
                <p className="text-xs text-muted-foreground">Questions</p>
              </div>
              <div>
                <p className={`text-lg font-bold ${scoreColor(overallScore)}`}>{overallScore.toFixed(1)}</p>
                <p className="text-xs text-muted-foreground">Avg Score</p>
              </div>
              <div>
                <p className="text-lg font-bold text-green-600">{highCount}</p>
                <p className="text-xs text-muted-foreground">Strong</p>
              </div>
            </div>
          </div>

          {/* Score distribution bar */}
          {scores.length > 0 && (
            <div className="mt-5 pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground mb-2">Score distribution</p>
              <div className="flex h-2 rounded-full overflow-hidden gap-0.5">
                {highCount > 0 && <div className="bg-green-500 rounded-full" style={{ flex: highCount }} />}
                {midCount  > 0 && <div className="bg-yellow-500 rounded-full" style={{ flex: midCount }} />}
                {lowCount  > 0 && <div className="bg-red-500 rounded-full" style={{ flex: lowCount }} />}
              </div>
              <div className="flex gap-4 mt-1.5">
                <span className="text-xs text-green-600">{highCount} strong</span>
                <span className="text-xs text-yellow-600">{midCount} average</span>
                <span className="text-xs text-red-500">{lowCount} weak</span>
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          {/* Strengths */}
          <div className="card-section">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <h2 className="text-sm font-semibold text-foreground">Strengths</h2>
            </div>
            <ul className="space-y-2">
              {report.strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2">
                  <CheckCircle className="w-3.5 h-3.5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-xs text-muted-foreground">{s}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Weaknesses */}
          <div className="card-section">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-4 h-4 text-orange-500" />
              <h2 className="text-sm font-semibold text-foreground">Areas to Improve</h2>
            </div>
            <ul className="space-y-2">
              {report.weaknesses.map((w, i) => (
                <li key={i} className="flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-orange-500 flex-shrink-0 mt-0.5" />
                  <span className="text-xs text-muted-foreground">{w}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Skill Scores */}
        {Object.keys(report.skill_scores).length > 0 && (
          <div className="card-section mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Award className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">Skill Breakdown</h2>
            </div>
            <div className="space-y-3">
              {Object.entries(report.skill_scores).map(([skill, score]) => (
                <div key={skill}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-foreground capitalize">{skill}</span>
                    <span className={`text-xs font-semibold ${scoreColor(score)}`}>{score}/10</span>
                  </div>
                  <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${scoreBarColor(score)}`}
                      style={{ width: `${(score / 10) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Per-question breakdown */}
        {answers.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">Question Breakdown</h2>
            </div>
            <div className="space-y-3">
              {answers.map((a, i) => (
                <div key={i} className={`card-section border ${scoreBg(a.score)}`}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <span className="text-xs font-semibold text-muted-foreground flex-shrink-0">Q{i + 1}</span>
                      <p className="text-sm font-medium text-foreground truncate">{a.question}</p>
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {a.layer && (
                        <span className={`text-xs px-1.5 py-0.5 rounded border capitalize ${layerBadge(a.layer)}`}>
                          {a.layer}
                        </span>
                      )}
                      <ScoreIcon score={a.score} />
                      <span className={`text-sm font-bold ${scoreColor(a.score)}`}>{a.score}/10</span>
                    </div>
                  </div>
                  {a.answer && (
                    <p className="text-xs text-muted-foreground italic mb-1.5 line-clamp-2">"{a.answer}"</p>
                  )}
                  <p className="text-xs text-muted-foreground">{a.feedback}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendation */}
        <div className="card-section mb-8 border border-primary/20 bg-primary/5">
          <p className="text-xs font-semibold text-primary mb-1 uppercase tracking-wide">Recommendation</p>
          <p className="text-sm text-foreground leading-relaxed">{report.recommendation}</p>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <Button onClick={() => navigate("/")} size="lg" className="px-8">
            <RefreshCcw className="w-4 h-4 mr-2" />
            New Interview
          </Button>
          <Button variant="outline" size="lg" className="px-8" onClick={() => window.print()}>
            Print Report
          </Button>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          AI-generated feedback for practice purposes only.
        </p>
      </div>
    </div>
  );
};

export default Feedback;
