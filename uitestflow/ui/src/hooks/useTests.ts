import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { testApi } from '@/lib/api'
import type { TestDefinition } from '@/types'

export function useTests() {
  return useQuery({
    queryKey: ['tests'],
    queryFn: async () => {
      const response = await testApi.getTests()
      // API returns { tests: [], total: 0, page: 1, page_size: 20 }
      return (response.data as any)?.tests || []
    },
  })
}

export function useTest(id: string) {
  return useQuery({
    queryKey: ['tests', id],
    queryFn: async () => {
      const response = await testApi.getTest(id)
      return response.data
    },
    enabled: !!id,
  })
}

export function useCreateTest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (test: Partial<TestDefinition>) => testApi.createTest(test),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
    },
  })
}

export function useUpdateTest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, test }: { id: string; test: Partial<TestDefinition> }) =>
      testApi.updateTest(id, test),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      queryClient.invalidateQueries({ queryKey: ['tests', variables.id] })
    },
  })
}

export function useDeleteTest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => testApi.deleteTest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
    },
  })
}

export function useImportTest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (url: string) => testApi.importTest(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
    },
  })
}
