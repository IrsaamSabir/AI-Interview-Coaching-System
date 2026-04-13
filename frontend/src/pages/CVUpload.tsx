import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload, FileText, CheckCircle, Loader2, X,
  ArrowRight, Mic, BarChart2, Brain, ShieldCheck
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { analyzeCV } from "@/lib/api";

const CVUpload = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [detectedDomain, setDetectedDomain] = useState<string | null>(null);
  const [detectedSkills, setDetectedSkills] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processFile = useCallback(async (selectedFile: File) => {
    setFile(selectedFile);
    setIsLoading(true);
    setError(null);
    setDetectedDomain(null);
    setDetectedSkills([]);
    try {
      const result = await analyzeCV(selectedFile);
      setDetectedDomain(result.domain);
      setDetectedSkills(result.skills || []);
    } catch (err: any) {
      setError(err?.message || "Failed to analyze document. Please upload a valid CV.");
      setFile(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleDragOver  = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragActive(true); }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragActive(false); }, []);
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    const f = e.dataTransfer.files[0];
    if (f) processFile(f);
  }, [processFile]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) processFile(f);
  }, [processFile]);

  const handleStart = () => {
    if (file && detectedDomain) {
      navigate("/interview", { state: { domain: detectedDomain, skills: detectedSkills } });
    }
  };

  const canStart = !!file && !!detectedDomain && !isLoading;

  return (
    <div className="min-h-screen bg-background flex flex-col">

      {/* Top nav bar */}
      <header className="border-b border-border bg-card px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
            <Brain className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-semibold text-foreground text-sm">InterviewAI</span>
        </div>
        <span className="text-xs text-muted-foreground">AI-Powered Interview Coaching</span>
      </header>

      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-5xl">

          {/* Page title */}
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold text-foreground tracking-tight mb-3">
              Start Your Mock Interview
            </h1>
            <p className="text-muted-foreground max-w-md mx-auto">
              Upload your CV and our AI will tailor a technical interview to your skills and experience.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

            {/* Left — Upload panel (3 cols) */}
            <div className="lg:col-span-3 flex flex-col gap-4">

              {/* Dropzone */}
              <div className="card-elevated p-6">
                <p className="text-sm font-medium text-foreground mb-4">Upload your CV</p>

                <input
                  type="file"
                  id="cv-upload"
                  className="hidden"
                  accept=".pdf,.docx"
                  onChange={handleFileInput}
                />

                <label
                  htmlFor="cv-upload"
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`flex flex-col items-center justify-center gap-4 border-2 border-dashed rounded-xl p-10 cursor-pointer transition-all duration-200
                    ${isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/60 hover:bg-muted/30"}
                    ${file && !error ? "border-primary/40 bg-primary/5" : ""}
                  `}
                >
                  {isLoading ? (
                    <>
                      <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center">
                        <Loader2 className="w-7 h-7 text-primary animate-spin" />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-medium text-foreground">Analyzing your CV...</p>
                        <p className="text-xs text-muted-foreground mt-1">This takes a few seconds</p>
                      </div>
                      <div className="w-48 h-1 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-primary rounded-full animate-pulse w-2/3" />
                      </div>
                    </>
                  ) : file && detectedDomain ? (
                    <>
                      <div className="w-14 h-14 rounded-2xl bg-green-500/10 flex items-center justify-center">
                        <CheckCircle className="w-7 h-7 text-green-600" />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-semibold text-foreground">{file.name}</p>
                        <p className="text-xs text-green-600 mt-1">CV analyzed successfully</p>
                      </div>
                      <span className="text-xs text-muted-foreground underline underline-offset-2">Upload a different file</span>
                    </>
                  ) : (
                    <>
                      <div className="w-14 h-14 rounded-2xl bg-muted flex items-center justify-center">
                        <Upload className="w-7 h-7 text-muted-foreground" />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-semibold text-foreground">Drop your CV here</p>
                        <p className="text-xs text-muted-foreground mt-1">or click to browse</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-1 bg-muted rounded-md text-xs text-muted-foreground font-medium">PDF</span>
                        <span className="px-2.5 py-1 bg-muted rounded-md text-xs text-muted-foreground font-medium">DOCX</span>
                      </div>
                    </>
                  )}
                </label>

                {/* Error */}
                {error && (
                  <div className="mt-4 flex items-start gap-2.5 p-3.5 bg-destructive/8 border border-destructive/25 rounded-lg">
                    <X className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-destructive">{error}</p>
                  </div>
                )}
              </div>

              {/* Detected result */}
              {detectedDomain && detectedSkills.length > 0 && (
                <div className="card-elevated p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-primary" />
                      <p className="text-sm font-medium text-foreground">Detected Profile</p>
                    </div>
                    <span className="text-xs font-semibold px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 capitalize">
                      {detectedDomain}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">{detectedSkills.length} skills identified</p>
                  <div className="flex flex-wrap gap-1.5">
                    {detectedSkills.map((skill) => (
                      <span
                        key={skill}
                        className="px-2.5 py-1 rounded-full text-xs font-medium bg-muted border border-border text-foreground capitalize"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* CTA */}
              <Button
                onClick={handleStart}
                disabled={!canStart}
                size="lg"
                className="w-full h-12 text-sm font-semibold"
              >
                {isLoading ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Analyzing...</>
                ) : (
                  <><span>Start Interview</span><ArrowRight className="w-4 h-4 ml-2" /></>
                )}
              </Button>
            </div>

            {/* Right — How it works (2 cols) */}
            <div className="lg:col-span-2 flex flex-col gap-3">
              <p className="text-sm font-medium text-foreground mb-1">How it works</p>

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
                <div key={item.step} className="flex items-start gap-4 p-4 rounded-xl border border-border bg-card hover:border-primary/30 transition-colors">
                  <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
                    <item.icon className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-bold text-primary/60 tracking-widest">{item.step}</span>
                      <p className="text-sm font-semibold text-foreground">{item.title}</p>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}

              {/* Privacy note */}
              <div className="mt-2 flex items-center gap-2 p-3 rounded-lg bg-muted/50 border border-border">
                <ShieldCheck className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                <p className="text-xs text-muted-foreground">Your CV is processed securely and never stored permanently.</p>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default CVUpload;
