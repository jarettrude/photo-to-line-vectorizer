/**
 * Welcome/Landing screen component.
 *
 * Displays introduction and features when no image is uploaded.
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Paintbrush, Zap, Sparkles, CheckCircle2 } from 'lucide-react'

export function WelcomeScreen() {
  return (
    <div className="space-y-6 animate-fade-in">
      <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
              <Paintbrush className="w-6 h-6 text-primary" />
            </div>
            <div>
              <CardTitle className="text-2xl">Photo to Line Vectorizer</CardTitle>
              <CardDescription className="text-base">
                Transform your photos into plotter-ready line art
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Upload an image to get started. Our advanced processing pipeline will convert your photo
            into clean, optimized SVG paths perfect for pen plotters, laser engravers, and CNC
            machines.
          </p>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              <CardTitle className="text-lg">Fast Processing</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              GPU-accelerated processing with real-time progress updates via WebSocket connection.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-500" />
              <CardTitle className="text-lg">Advanced Features</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              ML-assisted vectorization, subject isolation, hatching effects, and extensive
              customization options.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Supported Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 gap-3">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium">Edge Detection</p>
                <p className="text-xs text-muted-foreground">
                  Advanced Canny edge detection with customizable thresholds
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium">Line Optimization</p>
                <p className="text-xs text-muted-foreground">
                  Automatic path merging and simplification
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium">Hatching Effects</p>
                <p className="text-xs text-muted-foreground">
                  Add shading with customizable hatching patterns
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium">Subject Isolation</p>
                <p className="text-xs text-muted-foreground">
                  Automatic background removal for cleaner results
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle className="text-lg">Supported Formats</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">JPEG</Badge>
            <Badge variant="secondary">PNG</Badge>
            <Badge variant="secondary">TIFF</Badge>
            <Badge variant="secondary">WebP</Badge>
            <Badge variant="secondary">HEIC/HEIF</Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            Maximum file size: 50MB • Output: Optimized SVG with plotter-friendly paths
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
