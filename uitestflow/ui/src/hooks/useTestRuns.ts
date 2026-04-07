import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { testApi } from '@/lib/api'

interface RunsParams {
  test_id?: string
  status?: string
  limit?: number
}

export function useTestRuns(params?: RunsParams) {
  return useQuery({
    queryKey: ['runs', params],
    queryFn: async () => {
      const response = await testApi.getRuns(params)
      return response.data
    },
    refetchInterval: 5000, // Poll every 5 seconds for active runs
  })
}

export function useTestRun(id: string) {
  return useQuery({
    queryKey: ['runs', id],
    queryFn: async () => {
      const response = await testApi.getRun(id)
      return response.data
    },
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll while running
      const data = query.state.data
      return data?.status === 'running' || data?.status === 'pending' ? 2000 : false
    },
  })
}

export function useCreateRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { test_id: string; profile: string; context?: Record<string, any> }) =>
      testApi.createRun(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
    },
  })
}

export function useAbortRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => testApi.abortRun(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      queryClient.invalidateQueries({ queryKey: ['runs', id] })
    },
  })
}

export function useDeleteRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => testApi.deleteRun(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
    },
  })
}

export function useScreenshots(runId: string, runStatus?: string) {
  return useQuery({
    queryKey: ['runs', runId, 'screenshots', runStatus],
    queryFn: async () => {
      const response = await testApi.getScreenshots(runId)
      // API returns {run_id, screenshots: [{name, path, url}]}
      // Transform to Screenshot interface expected by ScreenshotGallery
      const rawScreenshots = response.data?.screenshots || []
      return rawScreenshots.map((s, index) => {
        // Parse filename like "step_0_Navigate_to_Google.png"
        const match = s.name.match(/^step_(\d+)_(.+)\.png$/)
        const stepIndex = match ? parseInt(match[1], 10) : index
        const stepName = match ? match[2].replace(/_/g, ' ') : s.name

        return {
          id: `screenshot-${index}`,
          test_run_id: runId,
          step_name: stepName,
          step_index: stepIndex,
          url: s.url,
          timestamp: '', // Not available from API
        }
      })
    },
    enabled: !!runId,
    // Refetch every 3 seconds while test is running
    refetchInterval: () => {
      if (runStatus === 'running' || runStatus === 'pending') {
        return 3000
      }
      return false
    },
  })
}

export function useLogs(runId: string, runStatus?: string) {
  return useQuery({
    queryKey: ['runs', runId, 'logs', runStatus],
    queryFn: async () => {
      const response = await testApi.getLogs(runId)
      // API returns {run_id, logs: [...]}
      return response.data?.logs || response.data || []
    },
    enabled: !!runId,
    // Refetch every 3 seconds while test is running
    refetchInterval: () => {
      if (runStatus === 'running' || runStatus === 'pending') {
        return 3000
      }
      return false
    },
  })
}
