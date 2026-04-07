import { useParams } from 'react-router-dom'
import { useTestRun, useScreenshots, useLogs, useAbortRun } from '@/hooks/useTestRuns'
import { TestRunViewer } from '@/components/TestRunViewer'
import { ScreenshotGallery } from '@/components/ScreenshotGallery'
import { LogViewer } from '@/components/LogViewer'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Download, ExternalLink } from 'lucide-react'

export function TestResults() {
  const { runId } = useParams<{ runId: string }>()
  const { data: run, isLoading } = useTestRun(runId || '')
  const { data: screenshots } = useScreenshots(runId || '', run?.status)
  const { data: logs } = useLogs(runId || '', run?.status)
  const abortRun = useAbortRun()

  const handleAbort = async () => {
    if (runId && confirm('Are you sure you want to abort this test run?')) {
      await abortRun.mutateAsync(runId)
    }
  }

  const handleDownloadReport = () => {
    if (runId) {
      window.open(`/api/runs/${runId}/report`, '_blank')
    }
  }

  const handleDownloadTrace = () => {
    if (runId) {
      window.open(`/api/runs/${runId}/trace`, '_blank')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading test run...</p>
        </div>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Test run not found</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Test Results</h1>
          <p className="text-muted-foreground">
            Detailed test execution report
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleDownloadReport}>
            <Download className="mr-2 h-4 w-4" />
            Download Report
          </Button>
          {run.trace_url && (
            <Button variant="outline" onClick={handleDownloadTrace}>
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Trace
            </Button>
          )}
        </div>
      </div>

      <TestRunViewer
        run={run}
        onAbort={run.status === 'running' ? handleAbort : undefined}
      />

      <Tabs defaultValue="screenshots">
        <TabsList>
          <TabsTrigger value="screenshots">
            Screenshots ({screenshots?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="logs">
            Logs ({logs?.length || 0})
          </TabsTrigger>
          {run.video_url && (
            <TabsTrigger value="video">
              Video
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="screenshots">
          <ScreenshotGallery screenshots={screenshots || []} />
        </TabsContent>

        <TabsContent value="logs">
          <LogViewer logs={logs || []} />
        </TabsContent>

        {run.video_url && (
          <TabsContent value="video">
            <div className="border rounded-lg p-4">
              <video
                controls
                className="w-full rounded"
                src={run.video_url}
              >
                Your browser does not support the video tag.
              </video>
            </div>
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}
