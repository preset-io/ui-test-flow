import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Wand2, Copy, Save, Eye, Settings, Play, Square, RotateCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useMCPGeneration } from '@/hooks/useMCPGeneration'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import SyntaxHighlighter from 'react-syntax-highlighter'
import { vs2015 } from 'react-syntax-highlighter/dist/esm/styles/hljs'
import yaml from 'js-yaml'
import { testApi } from '@/lib/api'
import { useQuery, useMutation } from '@tanstack/react-query'
import type { Profile, ProfileStartResponse } from '@/types'

export function MCPTestGenerator() {
  const navigate = useNavigate()
  const [generationMode, setGenerationMode] = useState<'description' | 'profile'>('description')

  // Description-based generation state
  const [description, setDescription] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [model, setModel] = useState('claude-3-5-haiku-20241022')
  const [temperature, setTemperature] = useState(0.0)
  const [editedTest, setEditedTest] = useState<any>(null)

  // Profile-based generation state
  const [selectedProfileId, setSelectedProfileId] = useState<string>('')
  const [coverageLevel, setCoverageLevel] = useState<'smoke' | 'canary' | 'medium' | 'deep'>('medium')
  const [crawlDepth, setCrawlDepth] = useState(1)
  const [generatingFromProfile, setGeneratingFromProfile] = useState(false)
  const [profileGenError, setProfileGenError] = useState<string | null>(null)
  const [generatedTests, setGeneratedTests] = useState<any[]>([])
  const [selectedTestIndex, setSelectedTestIndex] = useState<number | null>(null)

  // Profile session management state
  const [startingProfile, setStartingProfile] = useState<string | null>(null)
  const [startResults, setStartResults] = useState<Record<string, ProfileStartResponse>>({})

  // Fetch profiles
  const { data: profilesData } = useQuery({
    queryKey: ['profiles'],
    queryFn: async () => {
      const response = await testApi.getProfiles()
      return response.data
    },
  })

  const profiles = (profilesData as any)?.profiles || []

  const { isLoading, isError, error, data, generate, reset } = useMCPGeneration({
    onSuccess: (data) => {
      setEditedTest(data.test_definition)
    },
  })

  // Profile start mutation
  const startProfile = useMutation({
    mutationFn: ({ id, options }: { id: string; options: any }) =>
      testApi.startProfile(id, options),
    onSuccess: (response, variables) => {
      setStartResults((prev) => ({
        ...prev,
        [variables.id]: response.data,
      }))
      setStartingProfile(null)
    },
    onError: (error: any, variables) => {
      setStartResults((prev) => ({
        ...prev,
        [variables.id]: {
          success: false,
          steps_executed: 0,
          errors: [error.response?.data?.detail || error.message || 'Start failed'],
          message: 'Failed to start profile',
        },
      }))
      setStartingProfile(null)
    },
  })

  const handleGenerateFromDescription = async () => {
    if (!description.trim()) {
      return
    }

    await generate({
      description,
      base_url: baseUrl || undefined,
      model,
      temperature,
      save: true,
    })
  }

  const handleGenerateFromProfile = async () => {
    if (!selectedProfileId) {
      setProfileGenError('Please select a profile')
      return
    }

    setGeneratingFromProfile(true)
    setProfileGenError(null)
    try {
      const response = await testApi.generateTests({
        profile_id: selectedProfileId,
        coverage_level: coverageLevel,
        crawl_depth: crawlDepth,
      })

      if (response.data.success) {
        setGeneratedTests(response.data.tests || [])
        if (response.data.tests && response.data.tests.length > 0) {
          setSelectedTestIndex(0)
          setEditedTest(response.data.tests[0])
        }
      } else {
        setProfileGenError(response.data.message)
      }
    } catch (error: any) {
      console.error('Profile-based generation error:', error)
      const errorDetail = error.response?.data?.detail || 'Test generation failed'

      // Check for Anthropic API overload error
      if (errorDetail.includes('Overloaded') || errorDetail.includes('529')) {
        setProfileGenError('Anthropic API is temporarily overloaded. Please wait 1-2 minutes and try again.')
      } else {
        setProfileGenError(errorDetail)
      }
    } finally {
      setGeneratingFromProfile(false)
    }
  }

  const handleSaveTest = async (test?: any) => {
    const testToSave = test || editedTest
    if (!testToSave) return

    try {
      const response = await testApi.createTest({
        name: testToSave.name,
        description: testToSave.description,
        tags: testToSave.tags || [],
        steps: testToSave.steps,
        evaluators: testToSave.evaluators,
        url: testToSave.url || baseUrl,
      })

      if (response.data.id) {
        navigate(`/tests/${response.data.id}/edit`)
      }
    } catch (error) {
      console.error('Error saving test:', error)
    }
  }

  const handleRun = () => {
    if (data?.test_id) {
      navigate(`/tests/${data.test_id}/execute`)
    }
  }

  const handleCopyJson = () => {
    if (editedTest) {
      navigator.clipboard.writeText(JSON.stringify(editedTest, null, 2))
    }
  }

  const handleCopyYaml = () => {
    if (editedTest) {
      const yamlStr = yaml.dump(editedTest)
      navigator.clipboard.writeText(yamlStr)
    }
  }

  const handleReset = () => {
    setDescription('')
    setBaseUrl('')
    setEditedTest(null)
    setGeneratedTests([])
    setSelectedTestIndex(null)
    setProfileGenError(null)
    reset()
  }

  const handleSelectGeneratedTest = (index: number) => {
    setSelectedTestIndex(index)
    setEditedTest(generatedTests[index])
  }

  const handleStartProfile = async (profileId: string) => {
    setStartingProfile(profileId)
    await startProfile.mutateAsync({
      id: profileId,
      options: {
        execution_mode: 'manual',
        headless: false,
        with_claude: true,
      },
    })
  }

  const isProfileRunning = (profileId: string) => {
    return startResults[profileId]?.success === true
  }

  const getProfileStatus = (profileId: string) => {
    if (startingProfile === profileId) return 'starting'
    if (isProfileRunning(profileId)) return 'running'
    return 'stopped'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Generate Tests with AI</h1>
          <p className="text-muted-foreground mt-2">
            Create tests from descriptions or analyze initialized environments
          </p>
        </div>
      </div>

      {/* Generation Mode Selector */}
      <Card className="p-4">
        <div className="flex gap-4">
          <button
            onClick={() => setGenerationMode('description')}
            className={`flex-1 p-4 rounded-lg border-2 text-left transition-all ${
              generationMode === 'description'
                ? 'border-primary bg-primary/10'
                : 'border-border hover:border-primary/50'
            }`}
          >
            <div className="font-semibold">Description-based</div>
            <div className="text-xs text-muted-foreground mt-1">
              Generate a single test from natural language description
            </div>
          </button>
          <button
            onClick={() => setGenerationMode('profile')}
            className={`flex-1 p-4 rounded-lg border-2 text-left transition-all ${
              generationMode === 'profile'
                ? 'border-primary bg-primary/10'
                : 'border-border hover:border-primary/50'
            }`}
          >
            <div className="font-semibold">Environment-based</div>
            <div className="text-xs text-muted-foreground mt-1">
              Generate test suite from initialized profile (requires active session)
            </div>
          </button>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <Card className="p-6">
          {generationMode === 'description' ? (
            /* Description-based mode */
            <div className="space-y-4">
              <div>
                <Label htmlFor="description">Test Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Example: Login to the application with username 'admin' and password 'password123', then navigate to the dashboard and verify the welcome message is displayed."
                  className="min-h-[150px] mt-2"
                  disabled={isLoading}
                />
              </div>

              <div>
                <Label htmlFor="baseUrl">Base URL (Optional)</Label>
                <Input
                  id="baseUrl"
                  type="url"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="mt-2"
                  disabled={isLoading}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="model">Model</Label>
                  <select
                    id="model"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full mt-2 px-3 py-2 border rounded-md bg-background"
                    disabled={isLoading}
                  >
                    <option value="claude-3-5-haiku-20241022">Haiku (Fast)</option>
                    <option value="claude-3-5-sonnet-20241022">Sonnet (Powerful)</option>
                  </select>
                </div>

                <div>
                  <Label htmlFor="temperature">Temperature: {temperature.toFixed(1)}</Label>
                  <input
                    id="temperature"
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full mt-2"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  onClick={handleGenerateFromDescription}
                  disabled={!description.trim() || isLoading}
                  className="flex-1"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Wand2 className="mr-2 h-4 w-4" />
                      Generate Test
                    </>
                  )}
                </Button>

                {(data || generatedTests.length > 0) && (
                  <Button onClick={handleReset} variant="outline">
                    Reset
                  </Button>
                )}
              </div>

              {isError && error && (
                <div className="p-4 bg-destructive/10 text-destructive rounded-md">
                  <p className="font-semibold">Generation Failed</p>
                  <p className="text-sm mt-1">{error.message}</p>
                </div>
              )}

              {data && (
                <div className="p-4 bg-primary/10 text-primary rounded-md">
                  <p className="font-semibold">Test Generated!</p>
                  <p className="text-sm mt-1">
                    Generated in {data.generation_time_ms}ms using {data.model_used}
                  </p>
                </div>
              )}
            </div>
          ) : (
            /* Profile-based mode */
            <div className="space-y-4">
              <div>
                <Label htmlFor="profile">Select Profile</Label>
                <select
                  id="profile"
                  value={selectedProfileId}
                  onChange={(e) => setSelectedProfileId(e.target.value)}
                  className="w-full mt-2 px-3 py-2 border rounded-md bg-background"
                  disabled={generatingFromProfile}
                >
                  <option value="">Choose a profile...</option>
                  {profiles.map((profile: Profile) => (
                    <option key={profile.id} value={profile.id}>
                      {profile.name} ({profile.id})
                    </option>
                  ))}
                </select>
              </div>

              {/* Profile Session Controls */}
              {selectedProfileId && (
                <div className="border rounded-lg p-4 space-y-3 bg-muted/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          getProfileStatus(selectedProfileId) === 'running'
                            ? 'bg-green-500 animate-pulse'
                            : getProfileStatus(selectedProfileId) === 'starting'
                            ? 'bg-yellow-500 animate-pulse'
                            : 'bg-gray-400'
                        }`}
                      />
                      <span className="text-sm font-medium">
                        {getProfileStatus(selectedProfileId) === 'running'
                          ? 'Session Active'
                          : getProfileStatus(selectedProfileId) === 'starting'
                          ? 'Starting...'
                          : 'No Active Session'}
                      </span>
                    </div>
                    <Button
                      size="sm"
                      variant={getProfileStatus(selectedProfileId) === 'running' ? 'outline' : 'default'}
                      onClick={() => handleStartProfile(selectedProfileId)}
                      disabled={
                        getProfileStatus(selectedProfileId) === 'starting' ||
                        getProfileStatus(selectedProfileId) === 'running'
                      }
                    >
                      {getProfileStatus(selectedProfileId) === 'starting' ? (
                        <>
                          <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                          Starting...
                        </>
                      ) : getProfileStatus(selectedProfileId) === 'running' ? (
                        <>
                          <Square className="mr-2 h-3 w-3" />
                          Running
                        </>
                      ) : (
                        <>
                          <Play className="mr-2 h-3 w-3" />
                          Start Session
                        </>
                      )}
                    </Button>
                  </div>

                  {startResults[selectedProfileId] && (
                    <div
                      className={`text-xs p-2 rounded ${
                        startResults[selectedProfileId].success
                          ? 'bg-green-50 dark:bg-green-950 text-green-900 dark:text-green-100'
                          : 'bg-red-50 dark:bg-red-950 text-red-900 dark:text-red-100'
                      }`}
                    >
                      {startResults[selectedProfileId].message}
                      {startResults[selectedProfileId].errors &&
                        startResults[selectedProfileId].errors.length > 0 && (
                          <div className="mt-1">
                            {startResults[selectedProfileId].errors.map((err, i) => (
                              <div key={i}>• {err}</div>
                            ))}
                          </div>
                        )}
                    </div>
                  )}

                  <p className="text-xs text-muted-foreground">
                    Start the profile in manual mode to enable test generation
                  </p>
                </div>
              )}

              <div>
                <Label>Coverage Level</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {[
                    { value: 'smoke', label: 'Smoke', desc: '5-10 tests' },
                    { value: 'canary', label: 'Canary', desc: '15-25 tests' },
                    { value: 'medium', label: 'Medium', desc: '30-50 tests' },
                    { value: 'deep', label: 'Deep', desc: '50+ tests' },
                  ].map((level) => (
                    <button
                      key={level.value}
                      onClick={() => setCoverageLevel(level.value as any)}
                      disabled={generatingFromProfile}
                      className={`p-3 rounded-lg border-2 text-left transition-all ${
                        coverageLevel === level.value
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <div className="font-semibold text-sm">{level.label}</div>
                      <div className="text-xs text-muted-foreground">{level.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <Label>Crawl Depth: {crawlDepth}</Label>
                <input
                  type="range"
                  min="0"
                  max="5"
                  value={crawlDepth}
                  onChange={(e) => setCrawlDepth(parseInt(e.target.value))}
                  className="w-full mt-2"
                  disabled={generatingFromProfile}
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>Current page</span>
                  <span>Deep exploration</span>
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  onClick={handleGenerateFromProfile}
                  disabled={!selectedProfileId || generatingFromProfile}
                  className="flex-1"
                >
                  {generatingFromProfile ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing & Generating...
                    </>
                  ) : (
                    <>
                      <Wand2 className="mr-2 h-4 w-4" />
                      Generate Tests
                    </>
                  )}
                </Button>

                {generatedTests.length > 0 && (
                  <Button onClick={handleReset} variant="outline">
                    Reset
                  </Button>
                )}
              </div>

              {profileGenError && (
                <div className="p-4 bg-destructive/10 text-destructive rounded-md">
                  <p className="font-semibold">Generation Failed</p>
                  <p className="text-sm mt-1">{profileGenError}</p>
                </div>
              )}

              {generatedTests.length > 0 && (
                <div className="p-4 bg-primary/10 text-primary rounded-md">
                  <p className="font-semibold">Generated {generatedTests.length} tests!</p>
                  <p className="text-sm mt-1">Select a test below to view and save</p>
                </div>
              )}

              {/* Test selector for profile-based generation */}
              {generatedTests.length > 0 && (
                <div className="space-y-2">
                  <Label>Generated Tests ({generatedTests.length})</Label>
                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {generatedTests.map((test, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-md border transition-all ${
                          selectedTestIndex === index
                            ? 'border-primary bg-primary/10'
                            : 'border-border'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <button
                            onClick={() => handleSelectGeneratedTest(index)}
                            className="flex-1 text-left"
                          >
                            <div className="font-medium text-sm">{test.name}</div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {test.steps?.length || 0} steps • {test.tags?.join(', ')}
                            </div>
                          </button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleSaveTest(test)}
                            className="shrink-0"
                          >
                            <Save className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* Output Section */}
        <Card className="p-6">
          {!editedTest ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Wand2 className="h-12 w-12 mb-4" />
              <p className="text-lg font-medium">No test generated yet</p>
              <p className="text-sm mt-2 text-center">
                {generationMode === 'description'
                  ? 'Fill in the form and click Generate to create a test'
                  : 'Select a profile and click Generate to create tests'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  {generationMode === 'profile' && selectedTestIndex !== null
                    ? `Test ${selectedTestIndex + 1} of ${generatedTests.length}`
                    : 'Generated Test'}
                </h3>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => handleSaveTest()}>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                  {data?.test_id && (
                    <Button size="sm" onClick={handleRun}>
                      <Eye className="mr-2 h-4 w-4" />
                      Run
                    </Button>
                  )}
                </div>
              </div>

              <Tabs defaultValue="preview">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="preview">Preview</TabsTrigger>
                  <TabsTrigger value="json">JSON</TabsTrigger>
                  <TabsTrigger value="yaml">YAML</TabsTrigger>
                </TabsList>

                <TabsContent value="preview" className="space-y-3">
                  <div className="border rounded-md p-4 space-y-3">
                    <div>
                      <p className="text-sm text-muted-foreground">Name</p>
                      <p className="font-medium">{editedTest?.name || 'Untitled'}</p>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground">Description</p>
                      <p className="text-sm">{editedTest?.description || 'No description'}</p>
                    </div>

                    {editedTest?.url && (
                      <div>
                        <p className="text-sm text-muted-foreground">URL</p>
                        <p className="text-sm font-mono">{editedTest.url}</p>
                      </div>
                    )}

                    {editedTest?.tags && editedTest.tags.length > 0 && (
                      <div>
                        <p className="text-sm text-muted-foreground">Tags</p>
                        <div className="flex gap-2 mt-1">
                          {editedTest.tags.map((tag: string, i: number) => (
                            <span key={i} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {editedTest?.priority && (
                      <div>
                        <p className="text-sm text-muted-foreground">Priority</p>
                        <p className="text-sm capitalize">{editedTest.priority}</p>
                      </div>
                    )}

                    <div>
                      <p className="text-sm text-muted-foreground">Steps ({editedTest?.steps?.length || 0})</p>
                      <ul className="mt-2 space-y-2">
                        {editedTest?.steps?.map((step: any, i: number) => (
                          <li key={i} className="text-sm p-2 bg-muted rounded">
                            <span className="font-medium">{i + 1}. {step.name}</span>
                            <span className="text-muted-foreground ml-2">- {step.action}</span>
                            {step.selector && (
                              <code className="ml-2 text-xs">{step.selector}</code>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground">
                        Evaluators ({editedTest?.evaluators?.length || 0})
                      </p>
                      <ul className="mt-2 space-y-1">
                        {editedTest?.evaluators?.map((ev: any, i: number) => (
                          <li key={i} className="text-sm">
                            <span className="font-medium">{ev.name}</span>
                            <span className="text-muted-foreground ml-2">({ev.type})</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="json">
                  <div className="relative">
                    <Button
                      size="sm"
                      variant="outline"
                      className="absolute top-2 right-2 z-10"
                      onClick={handleCopyJson}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <SyntaxHighlighter
                      language="json"
                      style={vs2015}
                      customStyle={{
                        borderRadius: '0.375rem',
                        fontSize: '0.875rem',
                        maxHeight: '500px',
                      }}
                    >
                      {JSON.stringify(editedTest, null, 2)}
                    </SyntaxHighlighter>
                  </div>
                </TabsContent>

                <TabsContent value="yaml">
                  <div className="relative">
                    <Button
                      size="sm"
                      variant="outline"
                      className="absolute top-2 right-2 z-10"
                      onClick={handleCopyYaml}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <SyntaxHighlighter
                      language="yaml"
                      style={vs2015}
                      customStyle={{
                        borderRadius: '0.375rem',
                        fontSize: '0.875rem',
                        maxHeight: '500px',
                      }}
                    >
                      {yaml.dump(editedTest)}
                    </SyntaxHighlighter>
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
