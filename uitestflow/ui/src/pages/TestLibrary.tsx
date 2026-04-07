import { useState } from 'react'
import { useTests, useDeleteTest } from '@/hooks/useTests'
import { TestCard } from '@/components/TestCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Plus, Search } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export function TestLibrary() {
  const navigate = useNavigate()
  const { data: tests, isLoading } = useTests()
  const deleteTest = useDeleteTest()
  const [searchQuery, setSearchQuery] = useState('')

  const filteredTests = tests?.filter(
    (test: any) =>
      test.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      test.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      test.tags.some((tag: any) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const handleRunTest = (testId: string) => {
    navigate(`/runner?test=${testId}`)
  }

  const handleEditTest = (testId: string) => {
    navigate(`/tests/${testId}/edit`)
  }

  const handleDeleteTest = async (testId: string) => {
    if (confirm('Are you sure you want to delete this test?')) {
      await deleteTest.mutateAsync(testId)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading tests...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Test Library</h1>
          <p className="text-muted-foreground">
            Manage your test definitions
          </p>
        </div>
        <Button onClick={() => navigate('/tests/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Create Test
        </Button>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tests..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {!filteredTests || filteredTests.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">
            {searchQuery ? 'No tests found matching your search' : 'No tests yet'}
          </p>
          {!searchQuery && (
            <Button onClick={() => navigate('/tests/new')}>
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Test
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredTests.map((test: any) => (
            <TestCard
              key={test.id}
              test={test}
              onRun={() => handleRunTest(test.id)}
              onEdit={() => handleEditTest(test.id)}
              onDelete={() => handleDeleteTest(test.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
