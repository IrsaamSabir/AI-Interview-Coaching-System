import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const CVUpload = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [detectedDomain, setDetectedDomain] = useState<string | null>(null);
  const [customDomain, setCustomDomain] = useState("");

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.type === "application/pdf" || droppedFile.name.endsWith(".docx"))) {
      setFile(droppedFile);
      // Simulate domain detection
      setTimeout(() => {
        setDetectedDomain("Software Engineering");
      }, 800);
    }
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      // Simulate domain detection
      setTimeout(() => {
        setDetectedDomain("Software Engineering");
      }, 800);
    }
  }, []);

  const handleProceed = () => {
    const domain = customDomain.trim() || detectedDomain;
    if (file && domain) {
      navigate("/interview", { state: { domain } });
    }
  };

  return (
    <div className="page-centered">
      <div className="w-full max-w-[540px]">
        {/* Main Card */}
        <div className="card-elevated p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-semibold text-foreground mb-2">
              AI Interview Coach
            </h1>
            <p className="text-muted-foreground">
              Upload your CV to begin your practice interview session
            </p>
          </div>

          {/* Upload Dropzone */}
          <div
            className={`upload-dropzone mb-6 ${isDragActive ? "active" : ""} ${file ? "border-primary bg-primary/5" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="cv-upload"
              className="hidden"
              accept=".pdf,.docx"
              onChange={handleFileInput}
            />
            <label htmlFor="cv-upload" className="cursor-pointer block">
              {file ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <CheckCircle className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">{file.name}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Click or drag to replace
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                    <Upload className="w-6 h-6 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">
                      Upload your CV (PDF/DOCX)
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Drag and drop or click to browse
                    </p>
                  </div>
                </div>
              )}
            </label>
          </div>

          {/* Detected Domain */}
          {detectedDomain && (
            <div className="mb-6 p-4 bg-muted/50 rounded-lg border border-border">
              <div className="flex items-center gap-2 text-sm">
                <FileText className="w-4 h-4 text-primary" />
                <span className="text-muted-foreground">Detected domain:</span>
                <span className="font-medium text-foreground">{detectedDomain}</span>
              </div>
            </div>
          )}

          {/* Domain Override Input */}
          {file && (
            <div className="mb-8">
              <Label htmlFor="domain-input" className="text-sm font-medium text-foreground">
                Enter domain if incorrect
              </Label>
              <Input
                id="domain-input"
                type="text"
                placeholder="e.g., Data Science, Product Management"
                value={customDomain}
                onChange={(e) => setCustomDomain(e.target.value)}
                className="mt-2"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Leave empty to use the detected domain
              </p>
            </div>
          )}

          {/* Proceed Button */}
          <Button
            onClick={handleProceed}
            disabled={!file || !detectedDomain}
            className="w-full h-12 text-base font-medium"
          >
            Proceed to Interview
          </Button>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          Your data is processed securely and not stored permanently
        </p>
      </div>
    </div>
  );
};

export default CVUpload;