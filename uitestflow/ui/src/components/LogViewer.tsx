import { useState, useMemo } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import type { LogEntry } from '@/types'

interface LogViewerProps {
  logs: LogEntry[] | string[]
}

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

// Convert string logs to LogEntry format
function normalizeLog(log: LogEntry | string, index: number): LogEntry {
  if (typeof log === 'string') {
    // Parse log level from string if present
    let level: LogLevel = 'info'
    const lowerLog = log.toLowerCase()
    if (lowerLog.startsWith('error') || lowerLog.includes('failed') || lowerLog.includes('steps failed')) {
      level = 'error'
    } else if (lowerLog.startsWith('warn')) {
      level = 'warn'
    } else if (lowerLog.startsWith('debug')) {
      level = 'debug'
    }
    return {
      id: `log-${index}`,
      test_run_id: '',
      timestamp: new Date().toISOString(),
      level,
      message: log,
    }
  }
  return log
}

export function LogViewer({ logs }: LogViewerProps) {
  const [filter, setFilter] = useState('')

  const normalizedLogs = useMemo(() => {
    return logs.map((log, index) => normalizeLog(log, index))
  }, [logs])

  const filteredLogs = useMemo(() => {
    return normalizedLogs.filter((log) => {
      const matchesSearch = log.message.toLowerCase().includes(filter.toLowerCase())
      return matchesSearch
    })
  }, [normalizedLogs, filter])

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'text-red-600 dark:text-red-400'
      case 'warn':
        return 'text-yellow-600 dark:text-yellow-400'
      case 'info':
        return 'text-blue-600 dark:text-blue-400'
      case 'debug':
        return 'text-gray-600 dark:text-gray-400'
      default:
        return ''
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Execution Log</CardTitle>
          <div className="flex gap-2">
            <Badge variant="outline">
              {filteredLogs.length} / {logs.length} entries
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Filter logs..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="flex-1"
            />
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredLogs.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No logs found
              </p>
            ) : (
              filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex gap-2 text-sm font-mono p-2 rounded bg-muted/50"
                >
                  <Badge
                    variant="outline"
                    className={`${getLevelColor(log.level)} whitespace-nowrap`}
                  >
                    {log.level.toUpperCase()}
                  </Badge>
                  <span className="flex-1 break-all">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
