import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CheckCircle2, XCircle, Clock, Loader2, StopCircle } from 'lucide-react'
import type { TestRun } from '@/types'
import { formatDuration, getStatusBadgeVariant } from '@/lib/utils'
import { useWebSocket } from '@/hooks/useWebSocket'

interface TestRunViewerProps {
  run: TestRun
  onAbort?: () => void
}

export function TestRunViewer({ run, onAbort }: TestRunViewerProps) {
  const { isConnected } = useWebSocket(run.id)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return run.result?.passed ? (
          <CheckCircle2 className="h-5 w-5 text-green-600" />
        ) : (
          <XCircle className="h-5 w-5 text-red-600" />
        )
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-600" />
      case 'aborted':
        return <StopCircle className="h-5 w-5 text-gray-600" />
      default:
        return null
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon(run.status)}
            <CardTitle>Test Run {run.id.slice(0, 8)}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {isConnected && run.status === 'running' && (
              <Badge variant="secondary" className="animate-pulse">
                Live
              </Badge>
            )}
            <Badge variant={getStatusBadgeVariant(run.status)}>
              {run.status.toUpperCase()}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Profile</p>
              <p className="font-medium">{run.profile}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Triggered By</p>
              <p className="font-medium capitalize">{run.triggered_by}</p>
            </div>
            {run.started_at && (
              <div>
                <p className="text-muted-foreground">Started At</p>
                <p className="font-medium">
                  {new Date(run.started_at).toLocaleString()}
                </p>
              </div>
            )}
            {run.duration_ms && (
              <div>
                <p className="text-muted-foreground">Duration</p>
                <p className="font-medium">{formatDuration(run.duration_ms)}</p>
              </div>
            )}
          </div>

          {run.result && (
            <div className="border rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold">Test Result</h4>
                <Badge variant={run.result.passed ? 'default' : 'destructive'}>
                  {run.result.passed ? 'PASSED' : 'FAILED'}
                </Badge>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Steps Executed</p>
                  <p className="font-medium">{run.result.steps_executed}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Steps Passed</p>
                  <p className="font-medium text-green-600">
                    {run.result.steps_passed}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Steps Failed</p>
                  <p className="font-medium text-red-600">
                    {run.result.steps_failed}
                  </p>
                </div>
              </div>
              <div className="text-sm">
                <p className="text-muted-foreground">Score</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{ width: `${run.result.score * 100}%` }}
                    />
                  </div>
                  <span className="font-medium">
                    {Math.round(run.result.score * 100)}%
                  </span>
                </div>
              </div>

              {run.result.evaluator_results && run.result.evaluator_results.length > 0 && (
                <div className="space-y-2">
                  <h5 className="font-medium text-sm">Evaluators</h5>
                  {run.result.evaluator_results.map((evalResult, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between text-sm p-2 rounded bg-muted/50"
                    >
                      <span>{evalResult.evaluator_name}</span>
                      <div className="flex items-center gap-2">
                        {evalResult.passed ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-600" />
                        )}
                        <span className="text-muted-foreground">
                          {Math.round(evalResult.score * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {run.status === 'running' && onAbort && (
            <Button variant="destructive" onClick={onAbort} className="w-full">
              <StopCircle className="mr-2 h-4 w-4" />
              Abort Test Run
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
