import { useState, useCallback } from 'react'
import { mcpApi, GenerateTestRequest, GenerateTestResponse } from '@/api/mcpClient'

export interface GenerationState {
  isLoading: boolean
  isError: boolean
  error: Error | null
  data: GenerateTestResponse | null
}

export interface GenerationOptions {
  onSuccess?: (data: GenerateTestResponse) => void
  onError?: (error: Error) => void
}

export function useMCPGeneration(options?: GenerationOptions) {
  const [state, setState] = useState<GenerationState>({
    isLoading: false,
    isError: false,
    error: null,
    data: null,
  })

  const generate = useCallback(
    async (request: GenerateTestRequest) => {
      setState({
        isLoading: true,
        isError: false,
        error: null,
        data: null,
      })

      try {
        const response = await mcpApi.generateTest(request)

        setState({
          isLoading: false,
          isError: false,
          error: null,
          data: response.data,
        })

        options?.onSuccess?.(response.data)

        return response.data
      } catch (err) {
        const error = err as Error

        setState({
          isLoading: false,
          isError: true,
          error,
          data: null,
        })

        options?.onError?.(error)

        throw error
      }
    },
    [options]
  )

  const reset = useCallback(() => {
    setState({
      isLoading: false,
      isError: false,
      error: null,
      data: null,
    })
  }, [])

  const retry = useCallback(
    async (request: GenerateTestRequest) => {
      return generate(request)
    },
    [generate]
  )

  return {
    ...state,
    generate,
    reset,
    retry,
  }
}
