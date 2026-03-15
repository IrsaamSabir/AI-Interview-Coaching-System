import { useNavigate, useLocation } from "react-router-dom";
import { Download, RefreshCcw, CheckCircle, AlertTriangle, XCircle, Eye, Volume2, Mic, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";

type FeedbackLevel = "good" | "average" | "needs-improvement";

interface FeedbackItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  level: FeedbackLevel;
  description: string;
}

const Feedback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const domain = location.state?.domain || "Software Engineering";

  const verbalFeedback: FeedbackItem[] = [
    {
      label: "Clarity",
      icon: Mic,
      level: "good",
      description: "Your speech was clear and well-articulated throughout the interview."
    },
    {
      label: "Confidence",
      icon: Shield,
      level: "average",
      description: "Moderate confidence detected. Consider projecting more assurance in your responses."
    },
    {
      label: "Loudness",
      icon: Volume2,
      level: "good",
      description: "Your voice volume was appropriate and consistent."
    },
  ];

  const nonVerbalFeedback: FeedbackItem[] = [
    {
      label: "Eye Movement",
      icon: Eye,
      level: "average",
      description: "Eye contact was inconsistent. Try to maintain focus on the camera more frequently."
    },
  ];

  const areasToImprove = [
    "Practice maintaining steady eye contact with the camera to simulate real interviewer interaction.",
    "Work on projecting confidence, especially when discussing technical achievements.",
    "Consider pausing briefly before answering to structure your thoughts.",
    "Use specific examples and metrics when describing past experiences."
  ];

  const getLevelStyles = (level: FeedbackLevel) => {
    switch (level) {
      case "good":
        return {
          badge: "status-good",
          icon: CheckCircle,
          text: "Good"
        };
      case "average":
        return {
          badge: "status-average",
          icon: AlertTriangle,
          text: "Average"
        };
      case "needs-improvement":
        return {
          badge: "status-needs-work",
          icon: XCircle,
          text: "Needs Improvement"
        };
    }
  };

  const FeedbackCard = ({ item }: { item: FeedbackItem }) => {
    const levelStyles = getLevelStyles(item.level);
    const StatusIcon = levelStyles.icon;

    return (
      <div className="card-section">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <item.icon className="w-5 h-5 text-primary" />
            </div>
            <h3 className="font-medium text-foreground">{item.label}</h3>
          </div>
          <div className={`status-indicator ${levelStyles.badge}`}>
            <StatusIcon className="w-4 h-4" />
            <span>{levelStyles.text}</span>
          </div>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {item.description}
        </p>
      </div>
    );
  };

  const handleRetry = () => {
    navigate("/");
  };

  return (
    <div className="page-container">
      <div className="max-w-[800px] mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-2xl font-semibold text-foreground mb-2">
            Interview Feedback
          </h1>
          <p className="text-muted-foreground">
            Domain: {domain}
          </p>
        </div>

        {/* Verbal Communication Section */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-foreground mb-4">
            Verbal Communication
          </h2>
          <div className="space-y-4">
            {verbalFeedback.map((item, index) => (
              <FeedbackCard key={index} item={item} />
            ))}
          </div>
        </section>

        {/* Non-Verbal Communication Section */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-foreground mb-4">
            Non-Verbal Communication
          </h2>
          <div className="space-y-4">
            {nonVerbalFeedback.map((item, index) => (
              <FeedbackCard key={index} item={item} />
            ))}
          </div>
        </section>

        {/* Areas to Improve Section */}
        <section className="mb-10">
          <h2 className="text-lg font-semibold text-foreground mb-4">
            Areas to Improve
          </h2>
          <div className="card-section">
            <ul className="space-y-3">
              {areasToImprove.map((area, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-xs font-semibold text-primary">{index + 1}</span>
                  </span>
                  <span className="text-sm text-muted-foreground leading-relaxed">
                    {area}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Action Buttons */}
        <div className="flex items-center justify-center gap-4">
          <Button onClick={handleRetry} size="lg" className="px-8">
            <RefreshCcw className="w-4 h-4 mr-2" />
            Retry Interview
          </Button>
          <Button variant="outline" size="lg" className="px-8">
            <Download className="w-4 h-4 mr-2" />
            Download Report
          </Button>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-muted-foreground mt-10">
          This feedback is generated by AI analysis and is intended for practice purposes only.
        </p>
      </div>
    </div>
  );
};

export default Feedback;