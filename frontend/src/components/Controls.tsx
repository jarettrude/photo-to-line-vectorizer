/**
 * Processing controls component.
 *
 * Provides user interface for configuring processing parameters
 * including canvas size, line width, and processing options.
 */
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Label } from './ui/label'
import { Input } from './ui/input'
import { Switch } from './ui/switch'
import { Button } from './ui/button'
import { Settings, Play } from 'lucide-react'
import type { ProcessParams } from '@/lib/api'

interface ControlsProps {
  onProcess: (_: ProcessParams) => void
  disabled: boolean
}

export function Controls({ onProcess, disabled }: ControlsProps) {
  const [canvasWidth, setCanvasWidth] = useState(300)
  const [canvasHeight, setCanvasHeight] = useState(200)
  const [lineWidth, setLineWidth] = useState(0.3)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const [isolateSubject, setIsolateSubject] = useState(false)
  const [useMl, setUseMl] = useState(false)
  const [hatchingEnabled, setHatchingEnabled] = useState(false)

  const [edgeThresholdLow, setEdgeThresholdLow] = useState(50)
  const [edgeThresholdHigh, setEdgeThresholdHigh] = useState(150)
  const [lineThreshold, setLineThreshold] = useState(16)
  const [mergeTolerance, setMergeTolerance] = useState(0.5)
  const [simplifyTolerance, setSimplifyTolerance] = useState(0.2)
  const [hatchDensity, setHatchDensity] = useState(2.0)
  const [darknessThreshold, setDarknessThreshold] = useState(100)

  const handleProcess = () => {
    const params: ProcessParams = {
      canvas_width_mm: canvasWidth,
      canvas_height_mm: canvasHeight,
      line_width_mm: lineWidth,
      isolate_subject: isolateSubject,
      use_ml: useMl,
      edge_threshold: [edgeThresholdLow, edgeThresholdHigh],
      line_threshold: lineThreshold,
      merge_tolerance: mergeTolerance,
      simplify_tolerance: simplifyTolerance,
      hatching_enabled: hatchingEnabled,
      hatch_density: hatchDensity,
      hatch_angle: 45,
      darkness_threshold: darknessThreshold,
    }
    onProcess(params)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Processing Controls</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="canvas-width">Canvas Width (mm)</Label>
          <Input
            id="canvas-width"
            type="number"
            value={canvasWidth}
            onChange={(e) => setCanvasWidth(Number(e.target.value))}
            min={10}
            max={2000}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="canvas-height">Canvas Height (mm)</Label>
          <Input
            id="canvas-height"
            type="number"
            value={canvasHeight}
            onChange={(e) => setCanvasHeight(Number(e.target.value))}
            min={10}
            max={2000}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="line-width">Line Width (mm)</Label>
          <Input
            id="line-width"
            type="number"
            value={lineWidth}
            onChange={(e) => setLineWidth(Number(e.target.value))}
            min={0.1}
            max={5}
            step={0.1}
          />
        </div>

        <div className="flex items-center space-x-2">
          <Switch
            id="isolate-subject"
            checked={isolateSubject}
            onCheckedChange={setIsolateSubject}
          />
          <Label htmlFor="isolate-subject">Isolate Subject</Label>
        </div>

        <div className="flex items-center space-x-2">
          <Switch id="use-ml" checked={useMl} onCheckedChange={setUseMl} />
          <Label htmlFor="use-ml">Use ML-assisted Vectorization</Label>
        </div>

        <div className="flex items-center space-x-2">
          <Switch id="hatching" checked={hatchingEnabled} onCheckedChange={setHatchingEnabled} />
          <Label htmlFor="hatching">Enable Hatching</Label>
        </div>

        <div className="pt-4 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full"
          >
            <Settings className="w-4 h-4 mr-2" />
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </Button>
        </div>

        {showAdvanced && (
          <div className="space-y-4 pt-4 border-t">
            <div className="space-y-2">
              <Label htmlFor="edge-threshold-low">Edge Threshold Low</Label>
              <Input
                id="edge-threshold-low"
                type="number"
                value={edgeThresholdLow}
                onChange={(e) => setEdgeThresholdLow(Number(e.target.value))}
                min={0}
                max={255}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edge-threshold-high">Edge Threshold High</Label>
              <Input
                id="edge-threshold-high"
                type="number"
                value={edgeThresholdHigh}
                onChange={(e) => setEdgeThresholdHigh(Number(e.target.value))}
                min={0}
                max={255}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="merge-tolerance">Merge Tolerance (mm)</Label>
              <Input
                id="merge-tolerance"
                type="number"
                value={mergeTolerance}
                onChange={(e) => setMergeTolerance(Number(e.target.value))}
                min={0}
                max={5}
                step={0.1}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="line-threshold">Line Threshold</Label>
              <Input
                id="line-threshold"
                type="number"
                value={lineThreshold}
                onChange={(e) => setLineThreshold(Number(e.target.value))}
                min={0}
                max={255}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="simplify-tolerance">Simplify Tolerance (mm)</Label>
              <Input
                id="simplify-tolerance"
                type="number"
                value={simplifyTolerance}
                onChange={(e) => setSimplifyTolerance(Number(e.target.value))}
                min={0}
                max={5}
                step={0.1}
              />
            </div>

            {hatchingEnabled && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="hatch-density">Hatch Density</Label>
                  <Input
                    id="hatch-density"
                    type="number"
                    value={hatchDensity}
                    onChange={(e) => setHatchDensity(Number(e.target.value))}
                    min={0.5}
                    max={5}
                    step={0.1}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="darkness-threshold">Darkness Threshold</Label>
                  <Input
                    id="darkness-threshold"
                    type="number"
                    value={darknessThreshold}
                    onChange={(e) => setDarknessThreshold(Number(e.target.value))}
                    min={0}
                    max={255}
                  />
                </div>
              </>
            )}
          </div>
        )}

        <Button onClick={handleProcess} disabled={disabled} className="w-full" size="lg">
          <Play className="w-4 h-4 mr-2" />
          Process Image
        </Button>
      </CardContent>
    </Card>
  )
}
