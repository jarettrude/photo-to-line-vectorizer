/**
 * SVG preview component.
 *
 * Displays the processed SVG result with statistics and download option.
 * Uses WebSocket for real-time progress updates during processing.
 * Features zoom, pan, and side-by-side comparison.
 */
import { useEffect, useState, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import {
  Download,
  Loader2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Eye,
  Image as ImageIcon,
  FileText,
} from 'lucide-react'
import type { JobStatusResponse } from '@/lib/api'
import { getDownloadUrl } from '@/lib/api'
import { useWebSocket } from '@/hooks/useWebSocket'

interface PreviewProps {
  jobStatus: JobStatusResponse | null
}

export function Preview({ jobStatus }: PreviewProps) {
  const [realtimeProgress, setRealtimeProgress] = useState<number | null>(null)
  const [realtimeStage, setRealtimeStage] = useState<string | null>(null)
  const [realtimeMessage, setRealtimeMessage] = useState<string | null>(null)
  const [zoom, setZoom] = useState(100)
  const [viewMode, setViewMode] = useState<'result' | 'comparison'>('result')
  const iframeRef = useRef<HTMLIFrameElement>(null)

  // Connect to WebSocket for real-time updates when processing
  const { isConnected } = useWebSocket({
    jobId: jobStatus?.status === 'processing' ? jobStatus.job_id : null,
    onMessage: (message) => {
      if (message.type === 'progress') {
        setRealtimeProgress(message.progress)
        setRealtimeStage(message.stage || null)
        setRealtimeMessage(message.message || null)
      } else if (message.type === 'complete') {
        // Update will come from polling, just clear real-time state
        setRealtimeProgress(100)
        setRealtimeStage(null)
        setRealtimeMessage('Complete!')
      } else if (message.type === 'error') {
        setRealtimeStage(null)
        setRealtimeMessage(`Error: ${message.error}`)
      }
    },
    enabled: jobStatus?.status === 'processing',
  })

  // Reset real-time state when job changes or completes
  useEffect(() => {
    if (jobStatus?.status !== 'processing') {
      setRealtimeProgress(null)
      setRealtimeStage(null)
      setRealtimeMessage(null)
    }
  }, [jobStatus?.status])

  // Use real-time progress if available, otherwise fall back to jobStatus
  const displayProgress = realtimeProgress ?? jobStatus?.progress ?? 0
  const displayStage = realtimeStage
  const displayMessage = realtimeMessage

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 200))
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50))
  const handleZoomReset = () => setZoom(100)

  if (!jobStatus) {
    return (
      <Card className="h-full animate-scale-in">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Eye className="w-5 h-5" />
            Preview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-96 text-muted-foreground space-y-4">
            <FileText className="w-16 h-16 text-muted-foreground/50" />
            <div className="text-center">
              <p className="text-lg font-medium">No preview available</p>
              <p className="text-sm mt-1">Upload and process an image to see the result</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full animate-scale-in">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Eye className="w-5 h-5" />
            Preview
            {jobStatus.status === 'processing' && <Badge variant="warning">Processing</Badge>}
            {jobStatus.status === 'completed' && <Badge variant="success">Complete</Badge>}
            {jobStatus.status === 'failed' && <Badge variant="destructive">Failed</Badge>}
          </CardTitle>

          {jobStatus.status === 'completed' && (
            <div className="flex items-center gap-2">
              <Button variant="outline" size="icon" onClick={handleZoomOut} disabled={zoom <= 50}>
                <ZoomOut className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleZoomReset}>
                {zoom}%
              </Button>
              <Button variant="outline" size="icon" onClick={handleZoomIn} disabled={zoom >= 200}>
                <ZoomIn className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {jobStatus.status === 'processing' && (
          <div className="flex flex-col items-center justify-center h-96 space-y-4 animate-fade-in">
            <Loader2 className="w-16 h-16 animate-spin text-primary" />
            <div className="text-center space-y-3 w-full max-w-md">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium">{displayProgress}%</span>
                </div>
                <Progress value={displayProgress} className="h-3" />
              </div>

              {displayStage && (
                <Badge variant="secondary" className="capitalize">
                  {displayStage.replace(/_/g, ' ')}
                </Badge>
              )}

              {displayMessage && (
                <p className="text-sm text-muted-foreground">{displayMessage}</p>
              )}

              <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground pt-2">
                {isConnected && (
                  <div className="flex items-center gap-1">
                    <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    Live updates
                  </div>
                )}
                {jobStatus.device_used && <span>Using: {jobStatus.device_used}</span>}
              </div>
            </div>
          </div>
        )}

        {jobStatus.status === 'failed' && (
          <div className="p-6 bg-destructive/10 text-destructive rounded-lg border border-destructive/20 animate-slide-up">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-destructive/20 flex items-center justify-center flex-shrink-0">
                <Loader2 className="w-5 h-5" />
              </div>
              <div>
                <p className="font-semibold text-lg">Processing Failed</p>
                {jobStatus.error && <p className="text-sm mt-2">{jobStatus.error}</p>}
                <p className="text-xs mt-3 text-destructive/80">
                  Please try again with different settings or a different image.
                </p>
              </div>
            </div>
          </div>
        )}

        {jobStatus.status === 'completed' && jobStatus.result_url && (
          <div className="space-y-4 animate-fade-in">
            <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as typeof viewMode)}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="result">
                  <FileText className="w-4 h-4 mr-2" />
                  Result
                </TabsTrigger>
                <TabsTrigger value="comparison">
                  <ImageIcon className="w-4 h-4 mr-2" />
                  Compare
                </TabsTrigger>
              </TabsList>

              <TabsContent value="result" className="mt-4">
                <div className="border-2 rounded-lg overflow-hidden bg-white/50 backdrop-blur-sm">
                  <iframe
                    ref={iframeRef}
                    src={jobStatus.result_url}
                    className="w-full h-[500px] transition-transform duration-200"
                    style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left' }}
                    title="SVG Preview"
                  />
                </div>
              </TabsContent>

              <TabsContent value="comparison" className="mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Badge variant="outline">Original (coming soon)</Badge>
                    <div className="border-2 rounded-lg overflow-hidden bg-muted/20 h-64 flex items-center justify-center">
                      <p className="text-sm text-muted-foreground">
                        Original image comparison coming soon
                      </p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Badge variant="outline">Processed SVG</Badge>
                    <div className="border-2 rounded-lg overflow-hidden bg-white/50">
                      <iframe
                        src={jobStatus.result_url}
                        className="w-full h-64"
                        title="SVG Preview Comparison"
                      />
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            {jobStatus.stats && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="p-4 bg-gradient-to-br from-primary/5 to-primary/10 rounded-lg border border-primary/20">
                  <p className="text-xs text-muted-foreground mb-1">Path Count</p>
                  <p className="text-2xl font-bold text-primary">{jobStatus.stats.path_count}</p>
                </div>
                <div className="p-4 bg-gradient-to-br from-blue-500/5 to-blue-500/10 rounded-lg border border-blue-500/20">
                  <p className="text-xs text-muted-foreground mb-1">Total Length</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {jobStatus.stats.total_length_mm.toFixed(0)}
                    <span className="text-sm ml-1">mm</span>
                  </p>
                </div>
                {jobStatus.stats.width_mm && (
                  <div className="p-4 bg-gradient-to-br from-green-500/5 to-green-500/10 rounded-lg border border-green-500/20">
                    <p className="text-xs text-muted-foreground mb-1">Width</p>
                    <p className="text-2xl font-bold text-green-600">
                      {jobStatus.stats.width_mm.toFixed(0)}
                      <span className="text-sm ml-1">mm</span>
                    </p>
                  </div>
                )}
                {jobStatus.stats.height_mm && (
                  <div className="p-4 bg-gradient-to-br from-purple-500/5 to-purple-500/10 rounded-lg border border-purple-500/20">
                    <p className="text-xs text-muted-foreground mb-1">Height</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {jobStatus.stats.height_mm.toFixed(0)}
                      <span className="text-sm ml-1">mm</span>
                    </p>
                  </div>
                )}
              </div>
            )}

            {jobStatus.device_used && (
              <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground pt-2">
                <Badge variant="outline" className="text-xs">
                  {jobStatus.device_used}
                </Badge>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <Button asChild variant="outline" size="lg">
                <a href={jobStatus.result_url} target="_blank" rel="noopener noreferrer">
                  <Maximize2 className="w-4 h-4 mr-2" />
                  Open Full
                </a>
              </Button>
              <Button asChild className="w-full" size="lg">
                <a href={getDownloadUrl(jobStatus.job_id)} download>
                  <Download className="w-4 h-4 mr-2" />
                  Download SVG
                </a>
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
