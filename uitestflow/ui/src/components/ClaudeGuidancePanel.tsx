import { useState } from 'react'
import { ChevronDown, ChevronRight, Copy, Check, Lightbulb, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export interface GuidanceItem {
  step_index: number
  step_name: string
  guidance?: string
  selector_adapted: boolean
  original_selector?: string
  adapted_selector?: string
  recovery_attempted: boolean
  recovery_action?: string
  success: boolean
}

interface ClaudeGuidancePanelProps {
  guidance: GuidanceItem[]
  currentStepIndex?: number
  className?: string
}

export function ClaudeGuidancePanel({
  guidance,
  currentStepIndex = -1,
  className,
}: ClaudeGuidancePanelProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set([currentStepIndex]))
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  const toggleStep = (index: number) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedSteps(newExpanded)
  }

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  if (guidance.length === 0) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="text-center text-muted-foreground">
          <Lightbulb className="h-8 w-8 mx-auto mb-2" />
          <p>No Claude guidance available yet</p>
          <p className="text-sm mt-1">Guidance will appear as tests execute with Claude enabled</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className={cn('p-4', className)}>
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="h-5 w-5 text-primary" />
        <h3 className="font-semibold">Claude Guidance</h3>
        <Badge variant="outline" className="ml-auto">
          {guidance.length} steps
        </Badge>
      </div>

      <div className="space-y-2">
        {guidance.map((item, index) => {
          const isExpanded = expandedSteps.has(index)
          const isCurrent = index === currentStepIndex
          const hasGuidance = !!item.guidance
          const hasAdaptation = item.selector_adapted
          const hasRecovery = item.recovery_attempted

          return (
            <div
              key={index}
              className={cn(
                'border rounded-lg overflow-hidden transition-colors',
                isCurrent && 'ring-2 ring-primary',
                item.success ? 'border-green-500/50' : 'border-red-500/50'
              )}
            >
              {/* Header */}
              <button
                onClick={() => toggleStep(index)}
                className={cn(
                  'w-full px-4 py-3 flex items-center gap-3 hover:bg-accent transition-colors text-left',
                  isCurrent && 'bg-primary/5'
                )}
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4 flex-shrink-0" />
                ) : (
                  <ChevronRight className="h-4 w-4 flex-shrink-0" />
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">
                      {item.step_index + 1}. {item.step_name}
                    </span>
                    {isCurrent && (
                      <Badge variant="default" className="text-xs">
                        Current
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    {hasGuidance && (
                      <Badge variant="outline" className="text-xs">
                        <Lightbulb className="h-3 w-3 mr-1" />
                        Guidance
                      </Badge>
                    )}
                    {hasAdaptation && (
                      <Badge variant="outline" className="text-xs">
                        <RefreshCw className="h-3 w-3 mr-1" />
                        Adapted
                      </Badge>
                    )}
                    {hasRecovery && (
                      <Badge variant="outline" className="text-xs">
                        <AlertCircle className="h-3 w-3 mr-1" />
                        Recovered
                      </Badge>
                    )}
                  </div>
                </div>

                {item.success ? (
                  <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                )}
              </button>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 py-3 space-y-3 border-t bg-muted/50">
                  {/* Main Guidance */}
                  {hasGuidance && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-muted-foreground">Guidance</p>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => copyToClipboard(item.guidance!, index)}
                        >
                          {copiedIndex === index ? (
                            <Check className="h-4 w-4" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                      <p className="text-sm bg-background p-3 rounded border">
                        {item.guidance}
                      </p>
                    </div>
                  )}

                  {/* Selector Adaptation */}
                  {hasAdaptation && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-muted-foreground">
                        Selector Adaptation
                      </p>
                      <div className="bg-background p-3 rounded border space-y-2">
                        <div>
                          <p className="text-xs text-muted-foreground">Original</p>
                          <code className="text-xs text-red-600 line-through">
                            {item.original_selector}
                          </code>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Adapted</p>
                          <code className="text-xs text-green-600 font-medium">
                            {item.adapted_selector}
                          </code>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Error Recovery */}
                  {hasRecovery && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-muted-foreground">
                        Error Recovery
                      </p>
                      <div className="bg-background p-3 rounded border">
                        <p className="text-sm">{item.recovery_action}</p>
                      </div>
                    </div>
                  )}

                  {/* Status */}
                  <div className="pt-2 border-t">
                    <div className="flex items-center gap-2">
                      <p className="text-xs text-muted-foreground">Status:</p>
                      {item.success ? (
                        <Badge variant="default" className="bg-green-500">
                          Success
                        </Badge>
                      ) : (
                        <Badge variant="destructive">Failed</Badge>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}
