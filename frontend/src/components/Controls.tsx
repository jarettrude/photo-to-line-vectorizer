/**
 * Processing controls component.
 *
 * Provides user interface for configuring processing parameters
 * including canvas size, line width, and processing options.
 * Features tooltips, sliders, and organized sections.
 */
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Label } from './ui/label'
import { Switch } from './ui/switch'
import { Button } from './ui/button'
import { Slider } from './ui/slider'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Badge } from './ui/badge'
import { Settings, Play, HelpCircle, Sliders, Sparkles } from 'lucide-react'
import type { ProcessParams } from '@/lib/api'

interface ControlsProps {
  onProcess: (_: ProcessParams) => void
  disabled: boolean
}

interface ParamInfo {
  label: string
  description: string
  unit?: string
}

const PARAM_INFO: Record<string, ParamInfo> = {
  canvasWidth: {
    label: 'Canvas Width',
    description: 'Output width in millimeters for plotter/laser engraver',
    unit: 'mm',
  },
  canvasHeight: {
    label: 'Canvas Height',
    description: 'Output height in millimeters',
    unit: 'mm',
  },
  lineWidth: {
    label: 'Line Width',
    description: 'Thickness of drawn lines',
    unit: 'mm',
  },
  edgeThresholdLow: {
    label: 'Edge Threshold Low',
    description: 'Lower bound for edge detection (lower = more edges)',
  },
  edgeThresholdHigh: {
    label: 'Edge Threshold High',
    description: 'Upper bound for edge detection',
  },
  lineThreshold: {
    label: 'Line Threshold',
    description: 'Minimum line length to keep',
  },
  mergeTolerance: {
    label: 'Merge Tolerance',
    description: 'Distance threshold for merging nearby line endpoints',
    unit: 'mm',
  },
  simplifyTolerance: {
    label: 'Simplify Tolerance',
    description: 'Amount of path simplification (higher = simpler)',
    unit: 'mm',
  },
  hatchDensity: {
    label: 'Hatch Density',
    description: 'Spacing between hatching lines',
  },
  darknessThreshold: {
    label: 'Darkness Threshold',
    description: 'How dark a region must be to receive hatching',
  },
}

export function Controls({ onProcess, disabled }: ControlsProps) {
  const [canvasWidth, setCanvasWidth] = useState(300)
  const [canvasHeight, setCanvasHeight] = useState(200)
  const [lineWidth, setLineWidth] = useState(0.3)

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

  const ParamLabel = ({ param }: { param: string }) => {
    const info = PARAM_INFO[param]
    if (!info) return <Label>{param}</Label>

    return (
      <div className="flex items-center gap-2">
        <Label>{info.label}</Label>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
            </TooltipTrigger>
            <TooltipContent>
              <p className="max-w-xs">{info.description}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    )
  }

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
    <Card className="animate-scale-in">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Processing Controls
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="basic" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="basic">
              <Sliders className="w-4 h-4 mr-2" />
              Basic
            </TabsTrigger>
            <TabsTrigger value="advanced">
              <Sparkles className="w-4 h-4 mr-2" />
              Advanced
            </TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-4 mt-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <ParamLabel param="canvasWidth" />
                <Badge variant="secondary">{canvasWidth} mm</Badge>
              </div>
              <Slider
                value={[canvasWidth]}
                onValueChange={(v) => setCanvasWidth(v[0])}
                min={10}
                max={2000}
                step={10}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <ParamLabel param="canvasHeight" />
                <Badge variant="secondary">{canvasHeight} mm</Badge>
              </div>
              <Slider
                value={[canvasHeight]}
                onValueChange={(v) => setCanvasHeight(v[0])}
                min={10}
                max={2000}
                step={10}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <ParamLabel param="lineWidth" />
                <Badge variant="secondary">{lineWidth.toFixed(1)} mm</Badge>
              </div>
              <Slider
                value={[lineWidth]}
                onValueChange={(v) => setLineWidth(v[0])}
                min={0.1}
                max={5}
                step={0.1}
              />
            </div>

            <div className="pt-4 border-t space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Switch
                    id="isolate-subject"
                    checked={isolateSubject}
                    onCheckedChange={setIsolateSubject}
                  />
                  <Label htmlFor="isolate-subject">Isolate Subject</Label>
                </div>
                {isolateSubject && <Badge variant="success">On</Badge>}
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Switch id="use-ml" checked={useMl} onCheckedChange={setUseMl} />
                  <Label htmlFor="use-ml">ML Enhancement</Label>
                </div>
                {useMl && <Badge variant="success">On</Badge>}
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Switch
                    id="hatching"
                    checked={hatchingEnabled}
                    onCheckedChange={setHatchingEnabled}
                  />
                  <Label htmlFor="hatching">Enable Hatching</Label>
                </div>
                {hatchingEnabled && <Badge variant="success">On</Badge>}
              </div>
            </div>

            {hatchingEnabled && (
              <div className="space-y-4 pt-4 border-t animate-slide-down">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <ParamLabel param="hatchDensity" />
                    <Badge variant="secondary">{hatchDensity.toFixed(1)}</Badge>
                  </div>
                  <Slider
                    value={[hatchDensity]}
                    onValueChange={(v) => setHatchDensity(v[0])}
                    min={0.5}
                    max={5}
                    step={0.1}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <ParamLabel param="darknessThreshold" />
                    <Badge variant="secondary">{darknessThreshold}</Badge>
                  </div>
                  <Slider
                    value={[darknessThreshold]}
                    onValueChange={(v) => setDarknessThreshold(v[0])}
                    min={0}
                    max={255}
                    step={1}
                  />
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="advanced" className="space-y-4 mt-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <ParamLabel param="edgeThresholdLow" />
                <Badge variant="secondary">{edgeThresholdLow}</Badge>
              </div>
              <Slider
                value={[edgeThresholdLow]}
                onValueChange={(v) => setEdgeThresholdLow(v[0])}
                min={0}
                max={255}
                step={1}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <ParamLabel param="edgeThresholdHigh" />
                <Badge variant="secondary">{edgeThresholdHigh}</Badge>
              </div>
              <Slider
                value={[edgeThresholdHigh]}
                onValueChange={(v) => setEdgeThresholdHigh(v[0])}
                min={0}
                max={255}
                step={1}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <ParamLabel param="lineThreshold" />
                <Badge variant="secondary">{lineThreshold}</Badge>
              </div>
              <Slider
                value={[lineThreshold]}
                onValueChange={(v) => setLineThreshold(v[0])}
                min={0}
                max={255}
                step={1}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <ParamLabel param="mergeTolerance" />
                <Badge variant="secondary">{mergeTolerance.toFixed(1)} mm</Badge>
              </div>
              <Slider
                value={[mergeTolerance]}
                onValueChange={(v) => setMergeTolerance(v[0])}
                min={0}
                max={5}
                step={0.1}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <ParamLabel param="simplifyTolerance" />
                <Badge variant="secondary">{simplifyTolerance.toFixed(1)} mm</Badge>
              </div>
              <Slider
                value={[simplifyTolerance]}
                onValueChange={(v) => setSimplifyTolerance(v[0])}
                min={0}
                max={5}
                step={0.1}
              />
            </div>
          </TabsContent>
        </Tabs>

        <Button onClick={handleProcess} disabled={disabled} className="w-full mt-6" size="lg">
          <Play className="w-4 h-4 mr-2" />
          {disabled ? 'Processing...' : 'Process Image'}
        </Button>
      </CardContent>
    </Card>
  )
}
