/**
 * Main application component.
 *
 * Orchestrates the complete photo-to-line-vectorizer workflow:
 * upload, process, preview, and download.
 */
import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Upload } from './components/Upload'
import { Controls } from './components/Controls'
import { Preview } from './components/Preview'
import { Paintbrush } from 'lucide-react'
import type { UploadResponse, ProcessParams, JobStatusResponse } from './lib/api'
import { processImage, getJobStatus } from './lib/api'

const queryClient = new QueryClient()

function AppContent() {
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  useEffect(() => {
    if (!uploadResult || !isProcessing) return

    const pollInterval = setInterval(async () => {
      try {
        const status = await getJobStatus(uploadResult.job_id)
        setJobStatus(status)

        if (status.status === 'completed' || status.status === 'failed') {
          setIsProcessing(false)
        }
      } catch (error) {
        console.error('Failed to fetch status:', error)
      }
    }, 2000)

    return () => clearInterval(pollInterval)
  }, [uploadResult, isProcessing])

  const handleUploadComplete = (result: UploadResponse) => {
    setUploadResult(result)
    setJobStatus(null)
    setIsProcessing(false)
  }

  const handleProcess = async (params: ProcessParams) => {
    if (!uploadResult) return

    try {
      setIsProcessing(true)
      await processImage(uploadResult.job_id, 'auto', params)
    } catch (error) {
      console.error('Processing failed:', error)
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-3">
            <Paintbrush className="w-8 h-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">Photo to Line Vectorizer</h1>
              <p className="text-sm text-muted-foreground">
                Convert photos to plotter-ready line art SVG
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <Upload onUploadComplete={handleUploadComplete} />
            {uploadResult && <Controls onProcess={handleProcess} disabled={isProcessing} />}
          </div>

          <div className="lg:col-span-2">
            <Preview jobStatus={jobStatus} />
          </div>
        </div>
      </main>

      <footer className="border-t mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>Professional photo-to-line-art conversion for plotters and laser engravers</p>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}
