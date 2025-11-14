/**
 * Main application component.
 *
 * Orchestrates the complete photo-to-line-vectorizer workflow:
 * upload, process, preview, and download.
 * Features error boundary, welcome screen, and polished UI.
 */
import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Upload } from './components/Upload'
import { Controls } from './components/Controls'
import { Preview } from './components/Preview'
import { WelcomeScreen } from './components/WelcomeScreen'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Badge } from './components/ui/badge'
import { Paintbrush, Github, Info } from 'lucide-react'
import type { UploadResponse, ProcessParams, JobStatusResponse } from './lib/api'
import { processImage, getJobStatus } from './lib/api'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5000,
    },
  },
})

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
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Paintbrush className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Photo to Line Vectorizer</h1>
                <p className="text-sm text-muted-foreground">
                  Convert photos to plotter-ready line art SVG
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {jobStatus?.status === 'processing' && (
                <Badge variant="warning" className="animate-pulse">
                  Processing
                </Badge>
              )}
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
                aria-label="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <Upload onUploadComplete={handleUploadComplete} />
            {uploadResult && <Controls onProcess={handleProcess} disabled={isProcessing} />}
            {!uploadResult && !jobStatus && (
              <div className="hidden lg:block">
                <div className="p-4 bg-muted/50 rounded-lg border border-border">
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                    <div className="text-sm space-y-1">
                      <p className="font-medium">Quick Tip</p>
                      <p className="text-muted-foreground text-xs">
                        For best results, use high-contrast images with clear subjects. The edge
                        detection works best on photos with distinct boundaries.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            {!uploadResult && !jobStatus ? <WelcomeScreen /> : <Preview jobStatus={jobStatus} />}
          </div>
        </div>
      </main>

      <footer className="border-t mt-12 bg-card/30">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              Professional photo-to-line-art conversion for plotters and laser engravers
            </p>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>Built with React + Vite + TailwindCSS</span>
              <span>•</span>
              <span>Powered by PyTorch</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AppContent />
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
