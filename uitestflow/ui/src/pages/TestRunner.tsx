import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useTest } from '@/hooks/useTests'
import { useCreateRun } from '@/hooks/useTestRuns'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { testApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Play, Loader2, Power, AlertCircle, CheckCircle2 } from 'lucide-react'

export function TestRunner() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const testId = searchParams.get('test')
  const [selectedProfile, setSelectedProfile] = useState('')

  const { data: test } = useTest(testId || '')
  const { data: profilesData } = useQuery({
    queryKey: ['profiles'],
    queryFn: async () => {
      const response = await testApi.getProfiles()
      return response.data
    },
  })

  const profiles = (profilesData as any)?.profiles || []

  // Get selected profile details
  const { data: profileDetails, refetch: refetchProfile } = useQuery({
    queryKey: ['profile', selectedProfile],
    queryFn: async () => {
      if (!selectedProfile) return null
      const response = await testApi.getProfile(selectedProfile)
      return response.data
    },
    enabled: !!selectedProfile,
  })

  // Start profile mutation
  const startProfile = useMutation({
    mutationFn: async (profileId: string) => {
      const response = await testApi.startProfile(profileId, {
        headless: false,
        with_claude: true,
      })
      return response.data
    },
    onSuccess: () => {
      // Refetch profile to get updated status
      refetchProfile()
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
    },
  })

  const createRun = useCreateRun()

  useEffect(() => {
    if (profiles && profiles.length > 0 && !selectedProfile) {
      setSelectedProfile(profiles[0].id)
    }
  }, [profiles, selectedProfile])

  const handleRunTest = async () => {
    if (!testId || !selectedProfile) return

    const result = await createRun.mutateAsync({
      test_id: testId,
      profile: selectedProfile,
      context: {
        triggered_from: 'web-ui',
      },
    })

    if (result.data) {
      navigate(`/results/${result.data.id}`)
    }
  }

  if (!testId) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No test selected</p>
        <Button className="mt-4" onClick={() => navigate('/library')}>
          Go to Test Library
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold">Run Test</h1>
        <p className="text-muted-foreground">
          Configure and execute your test
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Test Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Test Name</Label>
            <p className="text-lg font-medium mt-1">{test?.name || 'Loading...'}</p>
            {test?.description && (
              <p className="text-sm text-muted-foreground mt-1">
                {test.description}
              </p>
            )}
          </div>

          <div>
            <Label htmlFor="profile">Profile</Label>
            <select
              id="profile"
              value={selectedProfile}
              onChange={(e) => setSelectedProfile(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 mt-1"
            >
              {profiles?.map((profile: any) => (
                <option key={profile.id} value={profile.id}>
                  {profile.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground mt-1">
              Select the environment profile to run against
            </p>
          </div>

          {/* Profile Status and Start Button */}
          {profileDetails && (
            <div className="border rounded-lg p-4 bg-muted/50 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Label>Environment Status</Label>
                  {profileDetails.environment_status === 'running' ? (
                    <div className="flex items-center gap-1 text-green-600">
                      <CheckCircle2 className="h-4 w-4" />
                      <span className="text-sm font-medium">Running</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-amber-600">
                      <AlertCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">
                        {profileDetails.environment_status || 'Not Started'}
                      </span>
                    </div>
                  )}
                </div>
                {profileDetails.environment_status !== 'running' && (
                  <Button
                    onClick={() => startProfile.mutate(selectedProfile)}
                    disabled={startProfile.isPending}
                    variant="outline"
                    size="sm"
                  >
                    {startProfile.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                        Starting...
                      </>
                    ) : (
                      <>
                        <Power className="mr-2 h-3 w-3" />
                        Start Environment
                      </>
                    )}
                  </Button>
                )}
              </div>
              {profileDetails.base_url && (
                <div>
                  <span className="text-xs text-muted-foreground">Base URL:</span>
                  <span className="text-xs ml-2">{profileDetails.base_url}</span>
                </div>
              )}
              {profileDetails.environment_status !== 'running' && (
                <p className="text-xs text-amber-600">
                  ⚠️ Environment must be started before running tests
                </p>
              )}
            </div>
          )}

          {test && (
            <div className="border rounded-lg p-4 bg-muted/50">
              <h4 className="font-medium mb-2">Test Steps</h4>
              <ol className="space-y-2 text-sm">
                {test.steps.map((step, index) => (
                  <li key={index} className="flex gap-2">
                    <span className="text-muted-foreground">{index + 1}.</span>
                    <span>{step.name}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          <Button
            onClick={handleRunTest}
            disabled={!selectedProfile || createRun.isPending}
            className="w-full"
            size="lg"
          >
            {createRun.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting Test...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Run Test
              </>
            )}
          </Button>
          {profileDetails?.environment_status !== 'running' && (
            <p className="text-xs text-center text-muted-foreground mt-2">
              Environment will be started automatically when test runs
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
