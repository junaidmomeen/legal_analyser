import React, { useState, useCallback, useRef } from 'react';
import { Upload, Loader, Search, FileText, File as FileIcon, X } from 'lucide-react';
import Card from './Card';
import Button from './Button';
import Alert from './Alert';
import { ApiError, SupportedFormats } from '../api/api';

interface FileUploadProps {
  onFileSelect: (file: File | null) => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
  selectedFile: File | null;
  supportedFormats: SupportedFormats | null;
  error: ApiError | null;
  onErrorClose: () => void;
  uploadProgress: number;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, onAnalyze, isAnalyzing, selectedFile, supportedFormats, error, onErrorClose, uploadProgress }) => {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) return <FileIcon className="h-16 w-16 text-primary" />;
    if (fileType === 'application/pdf') return <FileText className="h-16 w-16 text-error" />;
    return <FileIcon className="h-16 w-16 text-neutral" />;
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  }, [onFileSelect]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const handleCancel = () => {
    onFileSelect(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      <Card className="p-8">
        {!selectedFile ? (
          <>
            <div className="text-center mb-6">
              <h2 className="text-3xl font-bold text-gray-200 mb-2">Upload Your Document</h2>
              <p className="text-neutral text-md">Analyze PDF or image files for instant legal insights.</p>
            </div>
            <div
              className={`relative border-2 border-dashed rounded-lg p-10 text-center transition-all duration-300 ${dragActive ? 'border-primary bg-primary/10' : 'border-base-300 hover:border-primary/50 hover:bg-primary/5'}`}
              onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
            >
              <input ref={inputRef} type="file" id="file-upload" accept=".pdf,image/*" onChange={handleFileChange} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
              <div className="space-y-3 flex flex-col items-center">
                <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center border border-primary/20">
                  <Upload className="h-6 w-6 text-primary" />
                </div>
                <p className="text-lg font-medium text-gray-200">Drop document here or <span className='text-primary font-semibold'>browse</span></p>
                <p className="text-neutral text-sm">
                  {supportedFormats ? `Supports: ${supportedFormats.formats.join(', ')}` : 'PDF, PNG, JPG, etc.'}
                </p>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center animate-fade-in">
            <div className="mb-4">
              {getFileIcon(selectedFile.type)}
              <p className="text-gray-200 font-semibold mt-2 text-lg">{selectedFile.name}</p>
              <p className="text-neutral text-sm">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>

            {uploadProgress > 0 && (
              <div className="w-full bg-base-300 rounded-full h-2 my-4">
                <div className="bg-primary h-2 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }}></div>
              </div>
            )}

            <div className="mt-6 flex justify-center space-x-4">
              <Button onClick={handleCancel} variant="secondary">
                <X className="h-5 w-5" />
                <span>Cancel</span>
              </Button>
              <Button onClick={onAnalyze} disabled={isAnalyzing} variant="primary">
                {isAnalyzing ? <><Loader className="animate-spin h-5 w-5" /><span>Analyzing...</span></> : <><Search className="h-5 w-5" /><span>Analyze Document</span></>}
              </Button>
            </div>
          </div>
        )}

        {error && <Alert error={error} onClose={onErrorClose} />}

      </Card>
    </div>
  );
};

export default FileUpload;
