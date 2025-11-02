import React, { useState, useRef } from "react";
import { Upload, FileText, X, Sparkles, AlertCircle } from "lucide-react";

interface DocumentUploadProps {
  onSessionStart: (sessionId: string, content: string) => void;
  isLoading?: boolean;
}

type DocumentType = "research" | "technical" | "codebase";

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onSessionStart,
  isLoading = false,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [documentType, setDocumentType] = useState<DocumentType>("research");
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setError(null);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const newFiles = Array.from(e.dataTransfer.files);
      setSelectedFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (e.target.files && e.target.files[0]) {
      const newFiles = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const readFileAsText = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        resolve(content);
      };
      reader.onerror = () => {
        reject(new Error(`Failed to read file: ${file.name}`));
      };
      reader.readAsText(file);
    });
  };

  const startAnalysis = async () => {
    if (selectedFiles.length === 0) {
      setError("Please select at least one file");
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Read all selected files
      const fileContents: string[] = [];
      for (const file of selectedFiles) {
        try {
          const content = await readFileAsText(file);
          fileContents.push(content);
        } catch (err) {
          setError(
            `Failed to read file: ${file.name}. ${err instanceof Error ? err.message : ""}`
          );
          setIsProcessing(false);
          return;
        }
      }

      // Combine all file contents
      const combinedContent = fileContents
        .map((content, idx) => {
          const fileName = selectedFiles[idx].name;
          return `--- File: ${fileName} ---\n${content}`;
        })
        .join("\n\n");

      // Determine content type based on document type
      const contentType =
        documentType === "codebase" ? "codebase" : "document";

      // Generate session ID
      const sessionId = `session-${Date.now()}`;

      // Trigger analysis
      onSessionStart(sessionId, combinedContent);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "An error occurred";
      setError(`Failed to process files: ${errorMsg}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const documentTypeConfig = {
    research: {
      icon: FileText,
      label: "Research Paper",
      description: "Academic papers, articles, reports",
    },
    technical: {
      icon: FileText,
      label: "Technical Doc",
      description: "API docs, guides, specifications",
    },
    codebase: {
      icon: FileText,
      label: "Codebase",
      description: "Source code, scripts, configs",
    },
  };

  const config = documentTypeConfig[documentType];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl text-white mb-2">New Analysis Session</h2>
          <p className="text-gray-400">
            Upload documents for multi-agent real-time analysis with WebSocket streaming
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-900/30 border border-red-500/30 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        {/* Document Type Selection */}
        <div className="mb-6">
          <label className="block text-sm text-gray-300 mb-3">
            Document Type
          </label>
          <div className="grid grid-cols-3 gap-3">
            {(["research", "technical", "codebase"] as DocumentType[]).map(
              (type) => (
                <button
                  key={type}
                  onClick={() => {
                    setDocumentType(type);
                    setError(null);
                  }}
                  className={`p-4 rounded-lg border-2 transition-colors ${
                    documentType === type
                      ? "border-blue-500 bg-blue-900/20 text-white"
                      : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
                  }`}
                >
                  <FileText className="w-6 h-6 mx-auto mb-2" />
                  <p className="text-sm">{documentTypeConfig[type].label}</p>
                  <p className="text-xs text-gray-500">
                    {documentTypeConfig[type].description}
                  </p>
                </button>
              )
            )}
          </div>
        </div>

        {/* File Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive
              ? "border-blue-500 bg-blue-900/20"
              : "border-gray-700 bg-gray-800/50"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <Upload className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-300 mb-2">
            Drag and drop files here, or click to browse
          </p>
          <p className="text-sm text-gray-500 mb-4">
            Supports PDF, TXT, MD, and code files
          </p>
          <input
            ref={fileInputRef}
            type="file"
            id="file-upload"
            multiple
            onChange={handleFileInput}
            className="hidden"
            accept=".pdf,.txt,.md,.js,.ts,.tsx,.jsx,.py,.java,.cpp"
            disabled={isProcessing || isLoading}
          />
          <label
            htmlFor="file-upload"
            className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Browse Files
          </label>
        </div>

        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="mt-6">
            <h3 className="text-white mb-3">
              Selected Files ({selectedFiles.length})
            </h3>
            <div className="space-y-2">
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between bg-gray-800 rounded-lg p-3"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-blue-500" />
                    <div>
                      <p className="text-gray-300 text-sm">{file.name}</p>
                      <p className="text-xs text-gray-500">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    disabled={isProcessing || isLoading}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analysis Info */}
        <div className="mt-6 bg-gray-800 rounded-lg p-4">
          <h4 className="text-white text-sm mb-3">Analysis Pipeline</h4>
          <p className="text-xs text-gray-400 mb-3">
            Your documents will be processed through our multi-agent system with real-time streaming:
          </p>
          <div className="grid grid-cols-3 gap-2">
            <div className="text-xs">
              <div className="text-blue-400 mb-1">①</div>
              <p className="text-gray-300">Summarizer Agent</p>
              <p className="text-gray-500 text-xs">Key themes</p>
            </div>
            <div className="text-xs">
              <div className="text-purple-400 mb-1">②</div>
              <p className="text-gray-300">Linker Agent</p>
              <p className="text-gray-500 text-xs">Relationships</p>
            </div>
            <div className="text-xs">
              <div className="text-orange-400 mb-1">③</div>
              <p className="text-gray-300">Visualizer Agent</p>
              <p className="text-gray-500 text-xs">Knowledge graph</p>
            </div>
          </div>
        </div>

        {/* Start Button */}
        <button
          onClick={startAnalysis}
          disabled={selectedFiles.length === 0 || isProcessing || isLoading}
          className="w-full mt-6 px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:from-gray-700 disabled:to-gray-700 disabled:text-gray-500 transition-all flex items-center justify-center gap-2 font-medium"
        >
          {isProcessing || isLoading ? (
            <>
              <div className="animate-spin">
                <Sparkles className="w-5 h-5" />
              </div>
              Processing Files...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Start Multi-Agent Analysis
            </>
          )}
        </button>
      </div>

      {/* Agent Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-blue-500/50 transition-colors">
          <div className="w-10 h-10 bg-blue-900/30 rounded-lg flex items-center justify-center mb-3">
            <FileText className="w-6 h-6 text-blue-400" />
          </div>
          <h4 className="text-white text-sm mb-2 font-semibold">
            Summarizer Agent
          </h4>
          <p className="text-xs text-gray-400">
            Extracts key themes, concepts, and generates comprehensive summaries
            from your documents
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-purple-500/50 transition-colors">
          <div className="w-10 h-10 bg-purple-900/30 rounded-lg flex items-center justify-center mb-3">
            <FileText className="w-6 h-6 text-purple-400" />
          </div>
          <h4 className="text-white text-sm mb-2 font-semibold">
            Linker Agent
          </h4>
          <p className="text-xs text-gray-400">
            Identifies cross-references, entities, and concept relationships
            between document sections
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-orange-500/50 transition-colors">
          <div className="w-10 h-10 bg-orange-900/30 rounded-lg flex items-center justify-center mb-3">
            <FileText className="w-6 h-6 text-orange-400" />
          </div>
          <h4 className="text-white text-sm mb-2 font-semibold">
            Visualizer Agent
          </h4>
          <p className="text-xs text-gray-400">
            Creates knowledge graphs, dependency diagrams, and visual
            representations of document structure
          </p>
        </div>
      </div>
    </div>
  );
};
