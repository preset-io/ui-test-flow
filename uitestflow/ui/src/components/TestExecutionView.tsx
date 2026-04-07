import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Play,
  Pause,
  CheckCircle,
  XCircle,
  Clock,
  Image,
  Terminal,
  Wifi,
  WifiOff,
  ArrowLeft,
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ClaudeGuidancePanel, GuidanceItem } from './ClaudeGuidancePanel'
import { useTestExecution } from '@/hooks/useTestExecution'
import { cn } from '@/lib/utils'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function TestExecutionView() {
  const { testId } = useParams<{ testId: string }>()
  const navigate = useNavigate()
  const {
    status,
    runId,
    steps,
    currentStepIndex,
    screenshots,
    logs,
    progress,
    startTime,
    endTime,
    isConnected,
    error,
    execute,
    abort,
    reset,
  } = useTestExecution()

  const [selectedScreenshot, setSelectedScreenshot] = useState<string | null>(null)
  const [withClaude, setWithClaude] = useState(true)
  const [headless, setHeadless] = useState(false)

  const handleStart = () => {
    if (testId) {
      execute({
        test_id: testId,
        with_claude: withClaude,
        headless: headless,
      })
    }
  }

  const duration = startTime && endTime ? endTime - startTime : startTime ? Date.now() - startTime : 0

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  // Status color helper - kept for potential future use
  // const getStatusColor = (stepStatus: string) => {
  //   switch (stepStatus) {
  //     case 'completed':
  //       return 'text-green-500'
  //     case 'failed':
  //       return 'text-red-500'
  //     case 'running':
  //       return 'text-blue-500'
  //     default:
  //       return 'text-muted-foreground'
  //   }
  // }

  const getStatusIcon = (stepStatus: string) => {
    switch (stepStatus) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'running':
        return <Play className="h-5 w-5 text-blue-500 animate-pulse" />
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />
    }
  }

  // Convert steps to guidance format for ClaudeGuidancePanel
  const guidanceItems: GuidanceItem[] = steps.map((step) => ({
    step_index: step.step_index,
    step_name: step.step_name,
    guidance: step.guidance,
    selector_adapted: false, // Would come from step metadata
    recovery_attempted: false, // Would come from step metadata
    success: step.status === 'completed',
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Test Execution</h1>
            <p className="text-muted-foreground mt-1">
              {runId ? `Run ID: ${runId}` : 'Preparing execution...'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Wifi className="h-5 w-5 text-green-500" />
            ) : (
              <WifiOff className="h-5 w-5 text-red-500" />
            )}
            <span className="text-sm text-muted-foreground">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Status Badge */}
          <Badge
            variant={
              status === 'completed'
                ? 'default'
                : status === 'failed'
                ? 'destructive'
                : 'secondary'
            }
            className={cn(
              status === 'running' && 'animate-pulse',
              status === 'completed' && 'bg-green-500'
            )}
          >
            {status.toUpperCase()}
          </Badge>

          {/* Action Buttons */}
          {status === 'idle' && (
            <Button onClick={handleStart} size="sm">
              <Play className="mr-2 h-4 w-4" />
              Start Test
            </Button>
          )}

          {status === 'running' && (
            <Button onClick={abort} variant="destructive" size="sm">
              <Pause className="mr-2 h-4 w-4" />
              Abort
            </Button>
          )}

          {(status === 'completed' || status === 'failed' || status === 'aborted') && (
            <Button onClick={reset} size="sm">
              Reset
            </Button>
          )}
        </div>
      </div>

      {/* Run Options (shown when idle) */}
      {status === 'idle' && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Run Options</h3>
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={withClaude}
                onChange={(e) => setWithClaude(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span>Enable Claude AI guidance</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={headless}
                onChange={(e) => setHeadless(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span>Headless mode (no browser window)</span>
            </label>
          </div>
        </Card>
      )}

      {/* Progress Bar */}
      <Card className="p-6">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Progress</span>
            <span className="text-sm text-muted-foreground">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {steps.filter((s) => s.status === 'completed' || s.status === 'failed').length} /{' '}
              {steps.length} steps completed
            </span>
            {startTime && (
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {formatDuration(duration)}
              </span>
            )}
          </div>
        </div>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="p-4 bg-destructive/10 border-destructive">
          <div className="flex items-start gap-3">
            <XCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-destructive">Execution Error</p>
              <p className="text-sm text-destructive/90 mt-1">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Steps */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Test Steps</h3>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {steps.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <Clock className="h-8 w-8 mx-auto mb-2" />
                <p>Waiting for test execution to begin...</p>
              </div>
            ) : (
              steps.map((step, index) => (
                <div
                  key={index}
                  className={cn(
                    'p-4 border rounded-lg transition-all',
                    currentStepIndex === index && 'ring-2 ring-primary bg-primary/5',
                    step.status === 'completed' && 'border-green-500/50',
                    step.status === 'failed' && 'border-red-500/50'
                  )}
                >
                  <div className="flex items-start gap-3">
                    {getStatusIcon(step.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium truncate">
                          {step.step_index + 1}. {step.step_name}
                        </p>
                        {currentStepIndex === index && (
                          <Badge variant="default" className="text-xs">
                            Running
                          </Badge>
                        )}
                      </div>
                      {step.duration_ms && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {step.duration_ms}ms
                        </p>
                      )}
                      {step.error && (
                        <p className="text-xs text-red-500 mt-1">{step.error}</p>
                      )}
                      {step.screenshot_url && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="mt-2"
                          onClick={() => setSelectedScreenshot(step.screenshot_url!)}
                        >
                          <Image className="h-3 w-3 mr-1" />
                          View Screenshot
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Right Column: Screenshots & Logs */}
        <div className="space-y-6">
          <Tabs defaultValue="screenshots">
            <Card className="p-6">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="screenshots">
                  <Image className="h-4 w-4 mr-2" />
                  Screenshots ({screenshots.length})
                </TabsTrigger>
                <TabsTrigger value="logs">
                  <Terminal className="h-4 w-4 mr-2" />
                  Logs ({logs.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="screenshots" className="mt-4">
                {screenshots.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    <Image className="h-8 w-8 mx-auto mb-2" />
                    <p>No screenshots captured yet</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-2 max-h-[400px] overflow-y-auto">
                    {screenshots.map((url, index) => (
                      <button
                        key={index}
                        onClick={() => setSelectedScreenshot(url)}
                        className="border rounded-lg overflow-hidden hover:ring-2 hover:ring-primary transition-all"
                      >
                        <img
                          src={url}
                          alt={`Screenshot ${index + 1}`}
                          className="w-full h-32 object-cover"
                        />
                      </button>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="logs" className="mt-4">
                {logs.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    <Terminal className="h-8 w-8 mx-auto mb-2" />
                    <p>No logs yet</p>
                  </div>
                ) : (
                  <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-xs max-h-[400px] overflow-y-auto">
                    {logs.map((log, index) => (
                      <div key={index} className="mb-1">
                        {log}
                      </div>
                    ))}
                  </div>
                )}
              </TabsContent>
            </Card>
          </Tabs>
        </div>
      </div>

      {/* Claude Guidance Panel */}
      <ClaudeGuidancePanel guidance={guidanceItems} currentStepIndex={currentStepIndex} />

      {/* Screenshot Modal */}
      {selectedScreenshot && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedScreenshot(null)}
        >
          <div className="max-w-5xl w-full">
            <img
              src={selectedScreenshot}
              alt="Full screenshot"
              className="w-full h-auto rounded-lg"
            />
          </div>
        </div>
      )}
    </div>
  )
}
