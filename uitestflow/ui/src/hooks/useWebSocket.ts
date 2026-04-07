import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

interface WebSocketMessage {
  type: 'run_update' | 'run_started' | 'run_completed' | 'step_completed' | 'screenshot_captured'
  run_id: string
  data: any
}

export function useWebSocket(runId?: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!runId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/runs/${runId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        setLastMessage(message)

        // Invalidate relevant queries on updates
        if (message.type === 'run_update' || message.type === 'run_completed') {
          queryClient.invalidateQueries({ queryKey: ['runs', runId] })
        }

        if (message.type === 'step_completed') {
          queryClient.invalidateQueries({ queryKey: ['runs', runId] })
        }

        if (message.type === 'screenshot_captured') {
          queryClient.invalidateQueries({ queryKey: ['runs', runId, 'screenshots'] })
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      setIsConnected(false)
      console.log('WebSocket disconnected')
    }

    return () => {
      ws.close()
    }
  }, [runId, queryClient])

  return {
    isConnected,
    lastMessage,
  }
}
