import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Mic, MicOff, Video, VideoOff, Clock, AlertCircle, Eye, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const LiveInterview = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const domain = location.state?.domain || "Software Engineering";
  
  const [timer, setTimer] = useState(0);
  const [isMicOn, setIsMicOn] = useState(true);
  const [isCameraOn, setIsCameraOn] = useState(true);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const questions = [
    "Tell me about yourself and your background in " + domain + ".",
    "What is your greatest professional achievement?",
    "Describe a challenging project you worked on and how you handled it.",
    "Where do you see yourself in five years?",
    "Why are you interested in this role?"
  ];

  const instructions = [
    { icon: Mic, text: "Please speak clearly and loudly", active: true },
    { icon: Video, text: "Ensure your face is inside the camera frame", active: true },
    { icon: AlertCircle, text: "Lighting should be sufficient", active: false },
  ];

  const analysisStatus = [
    { label: "Eye movement", status: "Tracking…" },
    { label: "Speech clarity", status: "Analyzing…" },
    { label: "Posture", status: "Monitoring…" },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setTimer((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Cycle through questions every 30 seconds for demo
    const questionInterval = setInterval(() => {
      setCurrentQuestionIndex((prev) => (prev + 1) % questions.length);
    }, 30000);
    return () => clearInterval(questionInterval);
  }, [questions.length]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleEndInterview = () => {
    navigate("/feedback", { state: { domain } });
  };

  return (
    <div className="page-container">
      <div className="max-w-[1400px] mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-foreground">Live Interview Session</h1>
          <p className="text-sm text-muted-foreground">Domain: {domain}</p>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left: Camera View */}
          <div className="col-span-8">
            <div className="camera-frame">
              {/* Camera Overlay - Top */}
              <div className="camera-overlay">
                <div className="flex items-center justify-between">
                  {/* Timer */}
                  <div className="flex items-center gap-2 bg-card/90 backdrop-blur-sm rounded-lg px-3 py-2">
                    <Clock className="w-4 h-4 text-primary" />
                    <span className="font-mono text-sm font-medium text-foreground">{formatTime(timer)}</span>
                  </div>

                  {/* Status Indicators */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setIsMicOn(!isMicOn)}
                      className={`p-2 rounded-lg transition-colors ${
                        isMicOn ? "bg-primary text-primary-foreground" : "bg-destructive text-destructive-foreground"
                      }`}
                    >
                      {isMicOn ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={() => setIsCameraOn(!isCameraOn)}
                      className={`p-2 rounded-lg transition-colors ${
                        isCameraOn ? "bg-primary text-primary-foreground" : "bg-destructive text-destructive-foreground"
                      }`}
                    >
                      {isCameraOn ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>

              {/* Camera Placeholder Content */}
              <div className="absolute inset-0 flex items-center justify-center">
                {isCameraOn ? (
                  <div className="text-center">
                    <div className="w-24 h-24 rounded-full bg-muted/20 border-2 border-dashed border-muted/40 mx-auto mb-4 flex items-center justify-center">
                      <Video className="w-10 h-10 text-muted/60" />
                    </div>
                    <p className="text-muted/80 text-sm">Camera feed active</p>
                  </div>
                ) : (
                  <div className="text-center">
                    <VideoOff className="w-16 h-16 text-muted/40 mx-auto mb-2" />
                    <p className="text-muted/60 text-sm">Camera is off</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right: Side Panel */}
          <div className="col-span-4 space-y-4">
            {/* Current Question Card */}
            <div className="card-section">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-xs font-semibold text-primary">{currentQuestionIndex + 1}</span>
                </div>
                <span className="text-sm font-medium text-muted-foreground">Current Question</span>
              </div>
              <p className="text-lg font-medium text-foreground leading-relaxed">
                {questions[currentQuestionIndex]}
              </p>
            </div>

            {/* Instructions Card */}
            <div className="card-section">
              <h3 className="text-sm font-medium text-muted-foreground mb-4">Live Instructions</h3>
              <div className="space-y-3">
                {instructions.map((instruction, index) => (
                  <div
                    key={index}
                    className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                      instruction.active ? "bg-primary/5 border border-primary/20" : "bg-muted/30"
                    }`}
                  >
                    <instruction.icon className={`w-4 h-4 ${instruction.active ? "text-primary" : "text-muted-foreground"}`} />
                    <span className={`text-sm ${instruction.active ? "text-foreground" : "text-muted-foreground"}`}>
                      {instruction.text}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Analysis Status Card */}
            <div className="card-section">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-primary animate-pulse-slow" />
                <h3 className="text-sm font-medium text-muted-foreground">AI Analysis</h3>
              </div>
              <div className="space-y-3">
                {analysisStatus.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm text-foreground">{item.label}</span>
                    </div>
                    <span className="text-sm text-muted-foreground">{item.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom: End Interview Button */}
        <div className="mt-8 flex justify-center">
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" size="lg" className="px-8">
                End Interview
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>End Interview Session?</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to end the interview? You will be redirected to view your feedback and performance analysis.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Continue Interview</AlertDialogCancel>
                <AlertDialogAction onClick={handleEndInterview}>
                  End & View Feedback
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </div>
  );
};

export default LiveInterview;