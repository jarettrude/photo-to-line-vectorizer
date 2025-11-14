/**
 * WebSocket hook for real-time progress updates.
 *
 * Manages WebSocket connection lifecycle and message handling.
 */
import { useEffect, useRef, useState } from 'react'

export interface ProgressMessage {
  type: 'progress' | 'complete' | 'error' | 'keepalive'
  job_id: string
  progress: number
  stage?: string
  message?: string
  result_url?: string
  stats?: {
    path_count: number
    total_length_mm: number
    width_mm: number | null
    height_mm: number | null
  }
  error?: string
}

interface UseWebSocketParams {
  jobId: string | null
  onMessage?: (message: ProgressMessage) => void
  onError?: (error: Event) => void
  onClose?: () => void
  enabled?: boolean
}

export function useWebSocket({
  jobId,
  onMessage,
  onError,
  onClose,
  enabled = true,
}: UseWebSocketParams) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<ProgressMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    if (!jobId || !enabled) {
      return
    }

    // Construct WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.VITE_API_URL
      ? new URL(import.meta.env.VITE_API_URL).host
      : window.location.host
    const wsUrl = `${protocol}//${host}/ws/status/${jobId}`

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          console.log(`WebSocket connected for job ${jobId}`)
          setIsConnected(true)

          // Send initial ping
          ws.send('ping')
        }

        ws.onmessage = (event) => {
          try {
            const message: ProgressMessage = JSON.parse(event.data)
            setLastMessage(message)

            // Ignore keepalive messages
            if (message.type !== 'keepalive') {
              onMessage?.(message)
            }

            // Auto-disconnect on completion or error
            if (message.type === 'complete' || message.type === 'error') {
              // Close connection after a brief delay
              setTimeout(() => {
                if (wsRef.current) {
                  wsRef.current.close()
                }
              }, 1000)
            }
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e)
          }
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          onError?.(error)
        }

        ws.onclose = () => {
          console.log(`WebSocket closed for job ${jobId}`)
          setIsConnected(false)
          onClose?.()

          // Clean up ref
          if (wsRef.current === ws) {
            wsRef.current = null
          }
        }
      } catch (e) {
        console.error('Failed to connect WebSocket:', e)
      }
    }

    // Initial connection
    connect()

    // Cleanup on unmount
    return () => {
      // eslint-disable-next-line react-hooks/exhaustive-deps -- Cleanup function correctness
      const timeout = reconnectTimeoutRef.current
      if (timeout) {
        clearTimeout(timeout)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [jobId, enabled, onMessage, onError, onClose])

  // Send ping to keep connection alive
  useEffect(() => {
    if (!isConnected || !wsRef.current) {
      return
    }

    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 25000) // Ping every 25 seconds

    return () => {
      clearInterval(pingInterval)
    }
  }, [isConnected])

  return {
    isConnected,
    lastMessage,
  }
}
