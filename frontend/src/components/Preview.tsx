/**
 * SVG preview component.
 *
 * Displays the processed SVG result with statistics and download option.
 */
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Download, Loader2 } from 'lucide-react'
import type { JobStatusResponse } from '@/lib/api'
import { getDownloadUrl } from '@/lib/api'

interface PreviewProps {
  jobStatus: JobStatusResponse | null
}

export function Preview({ jobStatus }: PreviewProps) {
  if (!jobStatus) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-lg">Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            Upload and process an image to see the result
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg">Preview</CardTitle>
      </CardHeader>
      <CardContent>
        {jobStatus.status === 'processing' && (
          <div className="flex flex-col items-center justify-center h-64 space-y-4">
            <Loader2 className="w-12 h-12 animate-spin text-primary" />
            <p className="text-muted-foreground">Processing... {jobStatus.progress}%</p>
            {jobStatus.device_used && (
              <p className="text-sm text-muted-foreground">Using: {jobStatus.device_used}</p>
            )}
          </div>
        )}

        {jobStatus.status === 'failed' && (
          <div className="p-4 bg-destructive/10 text-destructive rounded-md">
            <p className="font-medium">Processing failed</p>
            {jobStatus.error && <p className="text-sm mt-1">{jobStatus.error}</p>}
          </div>
        )}

        {jobStatus.status === 'completed' && jobStatus.result_url && (
          <div className="space-y-4">
            <div className="border rounded-lg overflow-hidden bg-white">
              <iframe src={jobStatus.result_url} className="w-full h-96" title="SVG Preview" />
            </div>

            {jobStatus.stats && (
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="p-3 bg-muted rounded-md">
                  <p className="text-muted-foreground">Path Count</p>
                  <p className="font-medium">{jobStatus.stats.path_count}</p>
                </div>
                <div className="p-3 bg-muted rounded-md">
                  <p className="text-muted-foreground">Total Length</p>
                  <p className="font-medium">{jobStatus.stats.total_length_mm.toFixed(2)} mm</p>
                </div>
                {jobStatus.stats.width_mm && (
                  <div className="p-3 bg-muted rounded-md">
                    <p className="text-muted-foreground">Width</p>
                    <p className="font-medium">{jobStatus.stats.width_mm.toFixed(2)} mm</p>
                  </div>
                )}
                {jobStatus.stats.height_mm && (
                  <div className="p-3 bg-muted rounded-md">
                    <p className="text-muted-foreground">Height</p>
                    <p className="font-medium">{jobStatus.stats.height_mm.toFixed(2)} mm</p>
                  </div>
                )}
              </div>
            )}

            {jobStatus.device_used && (
              <div className="text-sm text-muted-foreground">
                Processed using: {jobStatus.device_used}
              </div>
            )}

            <Button asChild className="w-full" size="lg">
              <a href={getDownloadUrl(jobStatus.job_id)} download>
                <Download className="w-4 h-4 mr-2" />
                Download SVG
              </a>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
