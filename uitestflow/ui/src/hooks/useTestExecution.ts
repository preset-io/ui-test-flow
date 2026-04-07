import { useEffect, useRef, useState, useCallback } from 'react'
import { mcpApi, ExecuteTestRequest } from '@/api/mcpClient'

export interface ExecutionStep {
  step_index: number
  step_name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  screenshot_url?: string
  error?: string
  guidance?: string
  duration_ms?: number
}

export interface ExecutionState {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'aborted'
  runId: string | null
  steps: ExecutionStep[]
  currentStepIndex: number
  screenshots: string[]
  logs: string[]
  progress: number
  startTime: number | null
  endTime: number | null
  isConnected: boolean
  error: string | null
}

export interface WebSocketMessage {
  type: string
  run_id?: string
  step_index?: number
  step_name?: string
  status?: string
  screenshot_url?: string
  guidance?: string
  error?: string
  passed?: boolean
  duration_ms?: number
  timestamp?: number
  message?: string
  level?: string
}

export function useTestExecution() {
  const [state, setState] = useState<ExecutionState>({
    status: 'idle',
    runId: null,
    steps: [],
    currentStepIndex: -1,
    screenshots: [],
    logs: [],
    progress: 0,
    startTime: null,
    endTime: null,
    isConnected: false,
    error: null,
  })

  const wsRef = useRef<WebSocket | null>(null)

  const execute = useCallback(async (request: ExecuteTestRequest) => {
    try {
      const response = await mcpApi.executeTest(request)

      setState((prev) => ({
        ...prev,
        status: 'running',
        runId: response.data.run_id,
        startTime: Date.now(),
        error: null,
      }))

      // Connect to WebSocket for real-time updates
      connectWebSocket(response.data.run_id)

      return response.data
    } catch (err) {
      const error = err as Error
      setState((prev) => ({
        ...prev,
        status: 'failed',
        error: error.message,
      }))
      throw error
    }
  }, [])

  const connectWebSocket = useCallback((runId: string) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Use localhost:8018 for backend API
    const wsUrl = `${protocol}//localhost:8018/ws/runs/${runId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setState((prev) => ({ ...prev, isConnected: true }))
      console.log('WebSocket connected for run:', runId)
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        handleWebSocketMessage(message)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setState((prev) => ({ ...prev, isConnected: false }))
    }

    ws.onclose = () => {
      setState((prev) => ({ ...prev, isConnected: false }))
      console.log('WebSocket disconnected')
    }
  }, [])

  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    console.log('WebSocket message:', message)

    switch (message.type) {
      case 'test_started':
        setState((prev) => ({
          ...prev,
          status: 'running',
          startTime: Date.now(),
        }))
        break

      case 'step_started':
        setState((prev) => {
          const steps = [...prev.steps]
          const stepIndex = message.step_index ?? steps.length

          if (stepIndex >= steps.length) {
            steps.push({
              step_index: stepIndex,
              step_name: message.step_name || `Step ${stepIndex + 1}`,
              status: 'running',
            })
          } else {
            steps[stepIndex].status = 'running'
          }

          return {
            ...prev,
            steps,
            currentStepIndex: stepIndex,
          }
        })
        break

      case 'step_completed':
        setState((prev) => {
          const steps = [...prev.steps]
          const stepIndex = message.step_index ?? prev.currentStepIndex

          if (stepIndex >= 0 && stepIndex < steps.length) {
            steps[stepIndex] = {
              ...steps[stepIndex],
              status: message.status === 'failed' ? 'failed' : 'completed',
              screenshot_url: message.screenshot_url,
              error: message.error,
              duration_ms: message.duration_ms,
            }
          }

          const completedSteps = steps.filter(
            (s) => s.status === 'completed' || s.status === 'failed'
          ).length
          const progress = steps.length > 0 ? (completedSteps / steps.length) * 100 : 0

          return {
            ...prev,
            steps,
            progress,
          }
        })
        break

      case 'claude_guidance':
        setState((prev) => {
          const steps = [...prev.steps]
          const stepIndex = message.step_index ?? prev.currentStepIndex

          if (stepIndex >= 0 && stepIndex < steps.length) {
            steps[stepIndex] = {
              ...steps[stepIndex],
              guidance: message.guidance,
            }
          }

          return { ...prev, steps }
        })
        break

      case 'screenshot_captured':
        setState((prev) => ({
          ...prev,
          screenshots: [...prev.screenshots, message.screenshot_url || ''],
        }))
        break

      case 'console_log':
        setState((prev) => ({
          ...prev,
          logs: [
            ...prev.logs,
            `[${message.level || 'info'}] ${message.message || ''}`,
          ],
        }))
        break

      case 'test_completed':
        setState((prev) => ({
          ...prev,
          status: message.passed ? 'completed' : 'failed',
          endTime: Date.now(),
          progress: 100,
        }))
        break

      case 'test_error':
        setState((prev) => ({
          ...prev,
          status: 'failed',
          error: message.error || 'Unknown error',
          endTime: Date.now(),
        }))
        break

      default:
        console.log('Unknown message type:', message.type)
    }
  }, [])

  const abort = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    setState((prev) => ({
      ...prev,
      status: 'aborted',
      endTime: Date.now(),
    }))
  }, [])

  const reset = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    setState({
      status: 'idle',
      runId: null,
      steps: [],
      currentStepIndex: -1,
      screenshots: [],
      logs: [],
      progress: 0,
      startTime: null,
      endTime: null,
      isConnected: false,
      error: null,
    })
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return {
    ...state,
    execute,
    abort,
    reset,
  }
}
