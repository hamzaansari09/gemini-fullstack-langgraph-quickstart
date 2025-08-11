import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Upload, X, Image as ImageIcon, AlertCircle } from 'lucide-react';

interface ImageUploadProps {
  onImageSelect: (imageData: string | null, fileName?: string) => void;
  selectedImage: string | null;
  disabled?: boolean;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({
  onImageSelect,
  selectedImage,
  disabled = false,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const supportedFormats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
  const maxSizeBytes = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): string | null => {
    if (!supportedFormats.includes(file.type)) {
      return 'Please upload a valid image file (JPG, PNG, or WebP)';
    }
    if (file.size > maxSizeBytes) {
      return 'Image size must be less than 10MB';
    }
    return null;
  };

  const processFile = (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      // Extract base64 data without the data URL prefix
      const base64Data = result.split(',')[1];
      onImageSelect(base64Data, file.name);
    };
    reader.readAsDataURL(file);
  };

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

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      processFile(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      processFile(files[0]);
    }
  };

  const handleButtonClick = () => {
    if (disabled) return;
    fileInputRef.current?.click();
  };

  const handleRemoveImage = () => {
    onImageSelect(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full">
      {/* File input (hidden) */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/jpg,image/png,image/webp"
        onChange={handleFileSelect}
        className="hidden"
        disabled={disabled}
      />

      {/* Upload area */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-4 transition-colors
          ${dragActive 
            ? 'border-blue-400 bg-blue-50 dark:bg-blue-950/20' 
            : 'border-neutral-300 dark:border-neutral-600'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-neutral-400 dark:hover:border-neutral-500'}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleButtonClick}
      >
        {selectedImage ? (
          // Image preview
          <div className="relative">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                <ImageIcon className="h-4 w-4" />
                <span>Ad image uploaded</span>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveImage();
                }}
                className="h-6 w-6 p-0 hover:bg-red-100 dark:hover:bg-red-900/20"
                disabled={disabled}
              >
                <X className="h-4 w-4 text-red-500" />
              </Button>
            </div>
            <div className="relative max-w-xs mx-auto">
              <img
                src={`data:image/jpeg;base64,${selectedImage}`}
                alt="Uploaded ad"
                className="w-full h-auto max-h-48 object-contain rounded border"
              />
            </div>
          </div>
        ) : (
          // Upload prompt
          <div className="text-center py-6">
            <Upload className="mx-auto h-12 w-12 text-neutral-400 dark:text-neutral-500 mb-4" />
            <div className="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
              <span className="font-medium">Click to upload</span> or drag and drop
            </div>
            <div className="text-xs text-neutral-500 dark:text-neutral-500">
              JPG, PNG, WebP up to 10MB
            </div>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-2 flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload button (alternative to drag & drop) */}
      {!selectedImage && (
        <div className="mt-3 text-center">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleButtonClick}
            disabled={disabled}
            className="text-xs"
          >
            <Upload className="h-3 w-3 mr-1" />
            Choose Ad Image
          </Button>
        </div>
      )}
    </div>
  );
};
