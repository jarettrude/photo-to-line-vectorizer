/**
 * Image upload component with drag-and-drop support.
 *
 * Handles file selection, validation, and upload to backend.
 * Supports JPEG, PNG, TIFF, WebP, HEIC/HEIF formats.
 */
import { useCallback, useState, type DragEvent, type ChangeEvent } from 'react'
import { Upload as UploadIcon, Image as ImageIcon } from 'lucide-react'
import { Card, CardContent } from './ui/card'
import { Button } from './ui/button'
import { uploadImage, type UploadResponse } from '@/lib/api'

interface UploadProps {
  onUploadComplete: (result: UploadResponse) => void
}

export function Upload({ onUploadComplete }: UploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

      try {
        const result = await uploadImage(file)
        onUploadComplete(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed')
      } finally {
        setIsUploading(false)
      }
    },
    [onUploadComplete]
  )

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

  return (
    <Card>
      <CardContent className="p-6">
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors
            ${isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
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
                <ImageIcon className="w-12 h-12 text-muted-foreground" />
              )}

              <div>
                <p className="text-lg font-medium">
                  {isUploading ? 'Uploading...' : 'Drop your image here'}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  or click to browse (JPEG, PNG, TIFF, WebP, HEIC/HEIF)
                </p>
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

        {error && (
          <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
            {error}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
