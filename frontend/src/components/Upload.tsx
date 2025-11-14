/**
 * Image upload component with drag-and-drop support.
 *
 * Handles file selection, validation, and upload to backend.
 * Supports JPEG, PNG, TIFF, WebP, HEIC/HEIF formats.
 * Features image preview and enhanced animations.
 */
import { useCallback, useState, type DragEvent, type ChangeEvent } from 'react'
import { Upload as UploadIcon, Image as ImageIcon, X, FileImage } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { uploadImage, type UploadResponse } from '@/lib/api'

interface UploadProps {
  onUploadComplete: (result: UploadResponse) => void
}

export function Upload({ onUploadComplete }: UploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [fileSize, setFileSize] = useState<number | null>(null)

  const validateFile = (file: File): string | null => {
    const validTypes = [
      'image/jpeg',
      'image/png',
      'image/tiff',
      'image/webp',
      'image/heic',
      'image/heif',
    ]

    if (!validTypes.includes(file.type)) {
      return 'Unsupported file format. Please upload JPEG, PNG, TIFF, WebP, or HEIC/HEIF.'
    }

    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      return 'File too large. Maximum size is 50MB.'
    }

    return null
  }

  const handleFile = useCallback(
    async (file: File) => {
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        return
      }

      setError(null)
      setIsUploading(true)
      setUploadProgress(0)

      // Create preview
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreviewUrl(e.target?.result as string)
      }
      reader.readAsDataURL(file)

      setFileName(file.name)
      setFileSize(file.size)

      try {
        // Simulate progress (since we don't have real upload progress)
        const progressInterval = setInterval(() => {
          setUploadProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval)
              return prev
            }
            return prev + 10
          })
        }, 100)

        const result = await uploadImage(file)
        clearInterval(progressInterval)
        setUploadProgress(100)

        setTimeout(() => {
          onUploadComplete(result)
        }, 300)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed')
        setPreviewUrl(null)
      } finally {
        setTimeout(() => {
          setIsUploading(false)
          setUploadProgress(0)
        }, 500)
      }
    },
    [onUploadComplete]
  )

  const clearPreview = useCallback(() => {
    setPreviewUrl(null)
    setFileName(null)
    setFileSize(null)
    setError(null)
  }, [])

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setIsDragging(false)

      const file = e.dataTransfer.files[0]
      if (file) {
        handleFile(file)
      }
    },
    [handleFile]
  )

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setIsDragging(false)
  }, [])

  const handleFileInput = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        handleFile(file)
      }
    },
    [handleFile]
  )

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <Card className="animate-scale-in">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <FileImage className="w-5 h-5" />
          Upload Image
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6 pt-0">
        {!previewUrl ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300
              ${
                isDragging
                  ? 'border-primary bg-primary/10 scale-105'
                  : 'border-muted-foreground/25 hover:border-primary/50'
              }
              ${isUploading ? 'opacity-50 pointer-events-none' : 'cursor-pointer'}
            `}
          >
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".jpg,.jpeg,.png,.tiff,.tif,.webp,.heic,.heif"
              onChange={handleFileInput}
              disabled={isUploading}
            />

            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="flex flex-col items-center space-y-4">
                {isUploading ? (
                  <UploadIcon className="w-12 h-12 text-primary animate-pulse" />
                ) : (
                  <ImageIcon
                    className={`w-12 h-12 transition-colors ${isDragging ? 'text-primary' : 'text-muted-foreground'}`}
                  />
                )}

                <div>
                  <p className="text-lg font-medium">
                    {isUploading ? 'Uploading...' : isDragging ? 'Drop it here!' : 'Drop your image here'}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    or click to browse (JPEG, PNG, TIFF, WebP, HEIC/HEIF)
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">Maximum file size: 50MB</p>
                </div>

                {!isUploading && (
                  <Button type="button" variant="outline" size="sm">
                    <UploadIcon className="w-4 h-4 mr-2" />
                    Choose File
                  </Button>
                )}
              </div>
            </label>
          </div>
        ) : (
          <div className="space-y-4 animate-fade-in">
            <div className="relative group">
              <img
                src={previewUrl}
                alt="Preview"
                className="w-full h-48 object-cover rounded-lg border-2 border-border"
              />
              <Button
                variant="destructive"
                size="icon"
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={clearPreview}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium truncate max-w-[180px]">{fileName}</span>
              </div>
              {fileSize && <Badge variant="secondary">{formatFileSize(fileSize)}</Badge>}
            </div>
          </div>
        )}

        {isUploading && (
          <div className="mt-4 space-y-2 animate-slide-down">
            <Progress value={uploadProgress} className="h-2" />
            <p className="text-sm text-center text-muted-foreground">{uploadProgress}%</p>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm animate-slide-up flex items-start gap-2">
            <X className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
