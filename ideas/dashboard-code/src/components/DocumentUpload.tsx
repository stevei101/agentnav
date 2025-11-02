import { useState } from 'react';
import { Upload, FileText, X, Sparkles } from 'lucide-react';

interface DocumentUploadProps {
  onSessionStart: (sessionId: string) => void;
}

export function DocumentUpload({ onSessionStart }: DocumentUploadProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [documentType, setDocumentType] = useState<'research' | 'technical' | 'codebase'>('research');
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const newFiles = Array.from(e.dataTransfer.files);
      setSelectedFiles(prev => [...prev, ...newFiles]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const newFiles = Array.from(e.target.files);
      setSelectedFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const startAnalysis = () => {
    // Generate session ID
    const sessionId = `session-${Date.now()}`;
    onSessionStart(sessionId);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl text-white mb-2">New Analysis Session</h2>
          <p className="text-gray-400">
            Upload documents for multi-agent analysis
          </p>
        </div>

        {/* Document Type Selection */}
        <div className="mb-6">
          <label className="block text-sm text-gray-300 mb-3">Document Type</label>
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => setDocumentType('research')}
              className={`p-4 rounded-lg border-2 transition-colors ${
                documentType === 'research'
                  ? 'border-blue-500 bg-blue-900/20 text-white'
                  : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'
              }`}
            >
              <FileText className="w-6 h-6 mx-auto mb-2" />
              <p className="text-sm">Research Paper</p>
            </button>
            <button
              onClick={() => setDocumentType('technical')}
              className={`p-4 rounded-lg border-2 transition-colors ${
                documentType === 'technical'
                  ? 'border-blue-500 bg-blue-900/20 text-white'
                  : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'
              }`}
            >
              <FileText className="w-6 h-6 mx-auto mb-2" />
              <p className="text-sm">Technical Doc</p>
            </button>
            <button
              onClick={() => setDocumentType('codebase')}
              className={`p-4 rounded-lg border-2 transition-colors ${
                documentType === 'codebase'
                  ? 'border-blue-500 bg-blue-900/20 text-white'
                  : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'
              }`}
            >
              <FileText className="w-6 h-6 mx-auto mb-2" />
              <p className="text-sm">Codebase</p>
            </button>
          </div>
        </div>

        {/* File Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-900/20'
              : 'border-gray-700 bg-gray-800/50'
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
            type="file"
            id="file-upload"
            multiple
            onChange={handleFileInput}
            className="hidden"
            accept=".pdf,.txt,.md,.js,.ts,.tsx,.jsx,.py,.java,.cpp"
          />
          <label
            htmlFor="file-upload"
            className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors"
          >
            Browse Files
          </label>
        </div>

        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="mt-6">
            <h3 className="text-white mb-3">Selected Files ({selectedFiles.length})</h3>
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
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analysis Options */}
        <div className="mt-6 bg-gray-800 rounded-lg p-4">
          <h4 className="text-white text-sm mb-3">Analysis Configuration</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Model</label>
              <select className="w-full bg-gray-700 text-gray-300 rounded px-3 py-2 text-sm border border-gray-600">
                <option>Gemini 1.5 Pro</option>
                <option>Gemma 2</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">GPU Acceleration</label>
              <select className="w-full bg-gray-700 text-gray-300 rounded px-3 py-2 text-sm border border-gray-600">
                <option>Enabled</option>
                <option>Disabled</option>
              </select>
            </div>
          </div>
        </div>

        {/* Start Button */}
        <button
          onClick={startAnalysis}
          disabled={selectedFiles.length === 0}
          className="w-full mt-6 px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:from-gray-700 disabled:to-gray-700 disabled:text-gray-500 transition-all flex items-center justify-center gap-2"
        >
          <Sparkles className="w-5 h-5" />
          Start Multi-Agent Analysis
        </button>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h4 className="text-white text-sm mb-2">Summarizer Agent</h4>
          <p className="text-xs text-gray-400">
            Extracts key themes and generates comprehensive summaries
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h4 className="text-white text-sm mb-2">Linker Agent</h4>
          <p className="text-xs text-gray-400">
            Identifies cross-references and concept relationships
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h4 className="text-white text-sm mb-2">Visualizer Agent</h4>
          <p className="text-xs text-gray-400">
            Creates knowledge graphs and visual representations
          </p>
        </div>
      </div>
    </div>
  );
}
