import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { testApi } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Plus,
  Settings,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
  X,
  Play,
  Tag,
  Code,
  Sparkles,
  Wand2,
  Layers,
  Save,
} from 'lucide-react'
import { useState } from 'react'
import type { Profile, ProfileTestResult, ProfileStartResponse, AuthConfig, InitStep, LLMConfig, AIProfileGenerateRequest, AITestGenerateResponse } from '@/types'

const AUTH_TYPES = [
  { value: 'none', label: 'None' },
  { value: 'basic', label: 'Basic Auth' },
  { value: 'bearer', label: 'Bearer Token' },
  { value: 'api_key', label: 'API Key' },
  { value: 'form', label: 'Form Login' },
  { value: 'jwt', label: 'JWT' },
  { value: 'oauth', label: 'OAuth' },
  { value: 'custom', label: 'Custom Headers' },
]

const BROWSER_TYPES = [
  { value: 'chromium', label: 'Chromium (Recommended)' },
  { value: 'chrome', label: 'Google Chrome' },
  { value: 'firefox', label: 'Firefox' },
  { value: 'webkit', label: 'WebKit (Safari)' },
]

const LLM_PROVIDERS = [
  { value: 'claude-code-cli', label: 'Claude Code CLI' },
  { value: 'claude-sdk', label: 'Claude SDK' },
  { value: 'claude-api', label: 'Claude API' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'ollama', label: 'Ollama (Local)' },
  { value: 'custom', label: 'Custom' },
]

interface ProfileFormData extends Partial<Profile> {
  name: string
  base_url: string
}

const defaultFormData: ProfileFormData = {
  name: '',
  description: '',
  profile_type: 'environment',
  execution_mode: 'automated',
  base_url: '',
  init_steps: [],
  auth_config: {
    type: 'none',
  },
  browser_config: {
    browser_type: 'chromium',
    framework: 'playwright',
    headless: true,
    viewport: { width: 1920, height: 1080 },
  },
  llm_config: {
    enabled: false,
  },
  tags: [],
}

export function Profiles() {
  const queryClient = useQueryClient()
  const [testingProfile, setTestingProfile] = useState<string | null>(null)
  const [startingProfile, setStartingProfile] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, ProfileTestResult>>({})
  const [startResults, setStartResults] = useState<Record<string, ProfileStartResponse>>({})
  const [showModal, setShowModal] = useState(false)
  const [showStartModal, setShowStartModal] = useState(false)
  const [showStepsModal, setShowStepsModal] = useState(false)
  const [showAIGenerateModal, setShowAIGenerateModal] = useState(false)
  const [aiDescription, setAiDescription] = useState('')
  const [aiGeneratedProfiles, setAiGeneratedProfiles] = useState<Partial<Profile>[]>([])
  const [aiReasoning, setAiReasoning] = useState('')
  const [selectedProfileForSteps, setSelectedProfileForSteps] = useState<Profile | null>(null)
  const [formData, setFormData] = useState<ProfileFormData>(defaultFormData)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [selectedProfileForStart, setSelectedProfileForStart] = useState<Profile | null>(null)
  const [startOptions, setStartOptions] = useState({
    execution_mode: undefined as 'automated' | 'manual' | 'hybrid' | undefined,
    headless: true,
    with_claude: true,
  })
  const [showTestGenerateModal, setShowTestGenerateModal] = useState(false)
  const [selectedProfileForTestGen, setSelectedProfileForTestGen] = useState<Profile | null>(null)
  const [generatingTests, setGeneratingTests] = useState(false)
  const [testGenerateConfig, setTestGenerateConfig] = useState({
    coverage_level: 'medium' as 'smoke' | 'canary' | 'medium' | 'deep',
    crawl_depth: 1,
  })
  const [generatedTests, setGeneratedTests] = useState<any[]>([])
  const [testGenResult, setTestGenResult] = useState<AITestGenerateResponse | null>(null)

  const { data: profilesData, isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: async () => {
      const response = await testApi.getProfiles()
      return response.data
    },
  })

  const profiles = (profilesData as any)?.profiles || []

  const createProfile = useMutation({
    mutationFn: (data: ProfileFormData) => testApi.createProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      setShowModal(false)
      setFormData(defaultFormData)
      setEditingId(null)
    },
  })

  const updateProfile = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProfileFormData }) =>
      testApi.updateProfile(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      setShowModal(false)
      setFormData(defaultFormData)
      setEditingId(null)
    },
  })

  const deleteProfile = useMutation({
    mutationFn: (id: string) => testApi.deleteProfile(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
    },
  })

  const generateProfilesWithAI = useMutation({
    mutationFn: (request: AIProfileGenerateRequest) => testApi.generateProfiles(request),
    onSuccess: (response) => {
      const data = response.data
      if (data.success && data.profiles.length > 0) {
        setAiGeneratedProfiles(data.profiles)
        setAiReasoning(data.reasoning || '')
      }
    },
  })

  const testProfile = useMutation({
    mutationFn: (id: string) => testApi.testProfile(id),
    onSuccess: (response, profileId) => {
      setTestResults((prev) => ({
        ...prev,
        [profileId]: response.data,
      }))
      setTestingProfile(null)
    },
    onError: (error: any, profileId) => {
      setTestResults((prev) => ({
        ...prev,
        [profileId]: {
          success: false,
          error: error.response?.data?.detail || error.message || 'Test failed',
          tested_at: new Date().toISOString(),
        },
      }))
      setTestingProfile(null)
    },
  })

  const startProfile = useMutation({
    mutationFn: ({ id, options }: { id: string; options: typeof startOptions }) =>
      testApi.startProfile(id, options),
    onSuccess: (response, variables) => {
      setStartResults((prev) => ({
        ...prev,
        [variables.id]: response.data,
      }))
      setStartingProfile(null)
      setShowStartModal(false)
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

  const handleTestProfile = async (id: string) => {
    setTestingProfile(id)
    await testProfile.mutateAsync(id)
  }

  const handleDeleteProfile = async (id: string) => {
    if (confirm('Are you sure you want to delete this profile?')) {
      await deleteProfile.mutateAsync(id)
    }
  }

  const handleOpenCreate = () => {
    setFormData(defaultFormData)
    setEditingId(null)
    setShowModal(true)
  }

  const handleOpenEdit = (profile: Profile) => {
    setFormData({
      name: profile.name,
      description: profile.description || '',
      profile_type: profile.profile_type || 'environment',
      execution_mode: profile.execution_mode || 'automated',
      base_url: profile.base_url,
      init_steps: profile.init_steps || [],
      auth_config: profile.auth_config || { type: 'none' },
      browser_config: profile.browser_config || defaultFormData.browser_config,
      llm_config: profile.llm_config || { enabled: false },
      tags: profile.tags || [],
    })
    setEditingId(profile.id)
    setShowModal(true)
  }

  const handleOpenStart = (profile: Profile) => {
    setSelectedProfileForStart(profile)
    setStartOptions({
      execution_mode: profile.execution_mode,
      headless: profile.browser_config?.headless ?? true,
      with_claude: profile.llm_config?.enabled ?? true,
    })
    setShowStartModal(true)
  }

  const handleStartProfile = async () => {
    if (!selectedProfileForStart) return
    setStartingProfile(selectedProfileForStart.id)
    await startProfile.mutateAsync({
      id: selectedProfileForStart.id,
      options: startOptions,
    })
  }

  const handleOpenTestGenerate = (profile: Profile) => {
    setSelectedProfileForTestGen(profile)
    setShowTestGenerateModal(true)
    setTestGenResult(null)
    setGeneratedTests([])
  }

  const handleGenerateTests = async () => {
    if (!selectedProfileForTestGen) return

    setGeneratingTests(true)
    try {
      const response = await testApi.generateTests({
        profile_id: selectedProfileForTestGen.id,
        coverage_level: testGenerateConfig.coverage_level,
        crawl_depth: testGenerateConfig.crawl_depth,
      })

      setTestGenResult(response.data)
      setGeneratedTests(response.data.tests || [])
    } catch (error: any) {
      console.error('Test generation error:', error)
      setTestGenResult({
        success: false,
        tests: [],
        count: 0,
        coverage_level: '',
        message: error.response?.data?.detail || 'Test generation failed',
      })
    } finally {
      setGeneratingTests(false)
    }
  }

  const handleSaveGeneratedTest = async (test: any, index: number) => {
    try {
      await testApi.createTest({
        name: test.name,
        description: test.description,
        tags: test.tags || [],
        steps: test.steps,
        evaluators: test.evaluators,
        url: selectedProfileForTestGen?.base_url,
      })

      // Remove from generated tests
      setGeneratedTests(prev => prev.filter((_, i) => i !== index))
    } catch (error) {
      console.error('Error saving test:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editingId) {
      await updateProfile.mutateAsync({ id: editingId, data: formData })
    } else {
      await createProfile.mutateAsync(formData)
    }
  }

  const updateAuthConfig = (key: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      auth_config: {
        ...prev.auth_config,
        [key]: value,
      } as AuthConfig,
    }))
  }

  const addInitStep = () => {
    const newStep: InitStep = {
      name: 'New Step',
      action: 'click',
      critical: true,
    }
    setFormData((prev) => ({
      ...prev,
      init_steps: [...(prev.init_steps || []), newStep],
    }))
  }

  const updateInitStep = (index: number, field: keyof InitStep, value: any) => {
    setFormData((prev) => ({
      ...prev,
      init_steps: prev.init_steps?.map((step, i) =>
        i === index ? { ...step, [field]: value } : step
      ),
    }))
  }

  const removeInitStep = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      init_steps: prev.init_steps?.filter((_, i) => i !== index),
    }))
  }

  const updateLLMConfig = (key: keyof LLMConfig, value: any) => {
    setFormData((prev) => ({
      ...prev,
      llm_config: {
        ...prev.llm_config,
        [key]: value,
      } as LLMConfig,
    }))
  }

  const addTag = (tag: string) => {
    if (tag && !formData.tags?.includes(tag)) {
      setFormData((prev) => ({
        ...prev,
        tags: [...(prev.tags || []), tag],
      }))
    }
  }

  const removeTag = (tag: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags?.filter((t) => t !== tag),
    }))
  }

  const renderAuthFields = () => {
    const authType = formData.auth_config?.type

    switch (authType) {
      case 'basic':
      case 'form':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={formData.auth_config?.username || ''}
                onChange={(e) => updateAuthConfig('username', e.target.value)}
                placeholder="Enter username or ${ENV_VAR}"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={formData.auth_config?.password || ''}
                onChange={(e) => updateAuthConfig('password', e.target.value)}
                placeholder="Enter password or ${ENV_VAR}"
              />
            </div>
          </>
        )

      case 'bearer':
        return (
          <div className="space-y-2">
            <Label htmlFor="token">Bearer Token</Label>
            <Input
              id="token"
              value={formData.auth_config?.token || ''}
              onChange={(e) => updateAuthConfig('token', e.target.value)}
              placeholder="Enter bearer token or ${ENV_VAR}"
            />
          </div>
        )

      case 'api_key':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="api_key">API Key</Label>
              <Input
                id="api_key"
                value={formData.auth_config?.api_key || ''}
                onChange={(e) => updateAuthConfig('api_key', e.target.value)}
                placeholder="Enter API key or ${ENV_VAR}"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="api_key_header">Header Name</Label>
              <Input
                id="api_key_header"
                value={formData.auth_config?.api_key_header || 'X-API-Key'}
                onChange={(e) => updateAuthConfig('api_key_header', e.target.value)}
                placeholder="X-API-Key"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="api_key_prefix">Prefix (optional)</Label>
              <Input
                id="api_key_prefix"
                value={formData.auth_config?.api_key_prefix || ''}
                onChange={(e) => updateAuthConfig('api_key_prefix', e.target.value)}
                placeholder="e.g., Bearer"
              />
            </div>
          </>
        )

      case 'jwt':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="api_url">API URL</Label>
              <Input
                id="api_url"
                value={formData.auth_config?.api_url || ''}
                onChange={(e) => updateAuthConfig('api_url', e.target.value)}
                placeholder="https://api.example.com/auth"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="api_token">API Token</Label>
              <Input
                id="api_token"
                value={formData.auth_config?.api_token || ''}
                onChange={(e) => updateAuthConfig('api_token', e.target.value)}
                placeholder="Enter API token or ${ENV_VAR}"
              />
            </div>
          </>
        )

      case 'oauth':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="client_id">Client ID</Label>
              <Input
                id="client_id"
                value={formData.auth_config?.client_id || ''}
                onChange={(e) => updateAuthConfig('client_id', e.target.value)}
                placeholder="Enter OAuth client ID"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="client_secret">Client Secret</Label>
              <Input
                id="client_secret"
                type="password"
                value={formData.auth_config?.client_secret || ''}
                onChange={(e) => updateAuthConfig('client_secret', e.target.value)}
                placeholder="Enter OAuth client secret"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="token_url">Token URL</Label>
              <Input
                id="token_url"
                value={formData.auth_config?.token_url || ''}
                onChange={(e) => updateAuthConfig('token_url', e.target.value)}
                placeholder="https://auth.example.com/oauth/token"
              />
            </div>
          </>
        )

      default:
        return null
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading profiles...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Environment Profiles</h1>
          <p className="text-muted-foreground">Manage test environment configurations with init steps and LLM integration</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowAIGenerateModal(true)}>
            <Sparkles className="mr-2 h-4 w-4" />
            Generate with AI
          </Button>
          <Button onClick={handleOpenCreate}>
            <Plus className="mr-2 h-4 w-4" />
            Create Profile
          </Button>
        </div>
      </div>

      {!profiles || profiles.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">No profiles yet</p>
          <Button onClick={handleOpenCreate}>
            <Plus className="mr-2 h-4 w-4" />
            Create Your First Profile
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {profiles.map((profile: Profile) => (
            <Card key={profile.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{profile.name}</CardTitle>
                    {profile.description && (
                      <CardDescription className="mt-1 text-xs">{profile.description}</CardDescription>
                    )}
                    <CardDescription className="mt-1 text-xs">{profile.id}</CardDescription>
                  </div>
                  <div className="flex flex-col gap-1">
                    <Badge variant="outline" className="text-xs">
                      {profile.profile_type || 'environment'}
                    </Badge>
                    <Badge variant="secondary" className="text-xs">
                      {profile.execution_mode || 'automated'}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2 text-sm">
                    <div>
                      <p className="text-muted-foreground">Base URL</p>
                      <p className="font-medium break-all text-xs">{profile.base_url}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <p className="text-muted-foreground">Auth</p>
                        <p className="font-medium capitalize text-xs">
                          {profile.auth_config?.type?.replace('_', ' ') || 'none'}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Browser</p>
                        <p className="font-medium text-xs">
                          {profile.browser_config?.browser_type || profile.browser_config?.type || 'chromium'}
                        </p>
                      </div>
                    </div>
                    {profile.init_steps && profile.init_steps.length > 0 && (
                      <div>
                        <p className="text-muted-foreground">Init Steps</p>
                        <p className="font-medium text-xs">{profile.init_steps.length} steps configured</p>
                      </div>
                    )}
                    {profile.llm_config?.enabled && (
                      <div className="flex items-center gap-2">
                        <Code className="h-3 w-3 text-purple-500" />
                        <span className="text-xs text-purple-600 font-medium">
                          LLM: {profile.llm_config.provider || 'claude-code-cli'}
                        </span>
                      </div>
                    )}
                    {profile.tags && profile.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {profile.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            <Tag className="h-2 w-2 mr-1" />
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  {testResults[profile.id] && (
                    <div
                      className={`p-3 rounded-md text-sm ${
                        testResults[profile.id].success
                          ? 'bg-green-50 text-green-800 border border-green-200'
                          : 'bg-red-50 text-red-800 border border-red-200'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {testResults[profile.id].success ? (
                          <>
                            <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            <div>
                              <div className="font-medium">Connected</div>
                              {testResults[profile.id].latency_ms && (
                                <div className="text-xs mt-1">
                                  Response time: {testResults[profile.id].latency_ms}ms
                                </div>
                              )}
                            </div>
                          </>
                        ) : (
                          <>
                            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            <div>
                              <div className="font-medium">Failed</div>
                              {testResults[profile.id].error && (
                                <div className="text-xs mt-1 break-words">{testResults[profile.id].error}</div>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  )}

                  {startResults[profile.id] && (
                    <div
                      className={`p-3 rounded-md text-sm ${
                        startResults[profile.id].success
                          ? 'bg-blue-50 text-blue-800 border border-blue-200'
                          : 'bg-red-50 text-red-800 border border-red-200'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {startResults[profile.id].success ? (
                          <>
                            <Play className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            <div>
                              <div className="font-medium">{startResults[profile.id].message}</div>
                              <div className="text-xs mt-1">
                                Steps executed: {startResults[profile.id].steps_executed}
                              </div>
                            </div>
                          </>
                        ) : (
                          <>
                            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            <div>
                              <div className="font-medium">Start Failed</div>
                              {startResults[profile.id].errors.length > 0 && (
                                <div className="text-xs mt-1">{startResults[profile.id].errors[0]}</div>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleOpenStart(profile)}
                      disabled={startingProfile === profile.id}
                    >
                      {startingProfile === profile.id ? (
                        <>
                          <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                          Starting...
                        </>
                      ) : (
                        <>
                          <Play className="mr-2 h-3 w-3" />
                          Start
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestProfile(profile.id)}
                      disabled={testingProfile === profile.id}
                    >
                      {testingProfile === profile.id ? (
                        <>
                          <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                          Testing...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="mr-2 h-3 w-3" />
                          Test
                        </>
                      )}
                    </Button>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleOpenTestGenerate(profile)}
                    title="Generate tests from this environment"
                    className="w-full"
                  >
                    <Wand2 className="mr-2 h-3 w-3" />
                    Generate Tests
                  </Button>

                  <div className="flex gap-2">
                    {profile.init_steps && profile.init_steps.length > 0 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedProfileForSteps(profile)
                          setShowStepsModal(true)
                        }}
                        title="View init steps"
                      >
                        <Code className="mr-2 h-3 w-3" />
                        View {profile.init_steps.length} Step{profile.init_steps.length !== 1 ? 's' : ''}
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleOpenEdit(profile)}
                    >
                      <Settings className="mr-2 h-3 w-3" />
                      Edit
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => handleDeleteProfile(profile.id)}>
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Profile Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-background rounded-lg shadow-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-background z-10">
              <h2 className="text-lg font-semibold">{editingId ? 'Edit Profile' : 'Create Profile'}</h2>
              <Button variant="ghost" size="sm" onClick={() => setShowModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-6">
              {/* Basic Info */}
              <div className="space-y-4">
                <h3 className="text-md font-semibold">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Profile Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                      placeholder="e.g., Staging Environment"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="profile_type">Profile Type</Label>
                    <Select
                      value={formData.profile_type}
                      onValueChange={(value: 'environment' | 'workflow' | 'custom') =>
                        setFormData((prev) => ({ ...prev, profile_type: value }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="environment">Environment</SelectItem>
                        <SelectItem value="workflow">Workflow</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="base_url">Base URL *</Label>
                    <Input
                      id="base_url"
                      value={formData.base_url}
                      onChange={(e) => setFormData((prev) => ({ ...prev, base_url: e.target.value }))}
                      placeholder="https://app.example.com"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="execution_mode">Execution Mode</Label>
                    <Select
                      value={formData.execution_mode}
                      onValueChange={(value: 'automated' | 'manual' | 'hybrid') =>
                        setFormData((prev) => ({ ...prev, execution_mode: value }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="automated">Automated</SelectItem>
                        <SelectItem value="manual">Manual (Headed, Paused)</SelectItem>
                        <SelectItem value="hybrid">Hybrid (Mixed)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description || ''}
                    onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe this profile's purpose..."
                    rows={2}
                  />
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-4">
                <h3 className="text-md font-semibold">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {formData.tags?.map((tag) => (
                    <Badge key={tag} variant="secondary" className="gap-1">
                      <Tag className="h-3 w-3" />
                      {tag}
                      <button type="button" onClick={() => removeTag(tag)} className="ml-1">
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    id="new_tag"
                    placeholder="Add tag..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addTag(e.currentTarget.value)
                        e.currentTarget.value = ''
                      }
                    }}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      const input = document.getElementById('new_tag') as HTMLInputElement
                      addTag(input.value)
                      input.value = ''
                    }}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Init Steps */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-md font-semibold">Initialization Steps</h3>
                  <Button type="button" variant="outline" size="sm" onClick={addInitStep}>
                    <Plus className="mr-2 h-3 w-3" />
                    Add Step
                  </Button>
                </div>
                {formData.init_steps && formData.init_steps.length > 0 ? (
                  <div className="space-y-3">
                    {formData.init_steps.map((step, index) => (
                      <div key={index} className="p-3 border rounded-md space-y-2 bg-muted/30">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Step {index + 1}</span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeInitStep(index)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            placeholder="Step name"
                            value={step.name}
                            onChange={(e) => updateInitStep(index, 'name', e.target.value)}
                          />
                          <Select
                            value={step.action}
                            onValueChange={(value) => updateInitStep(index, 'action', value)}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="goto">Navigate (goto)</SelectItem>
                              <SelectItem value="click">Click</SelectItem>
                              <SelectItem value="fill">Fill Input</SelectItem>
                              <SelectItem value="wait_for">Wait For Element</SelectItem>
                              <SelectItem value="wait">Wait (delay)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        {step.action !== 'wait' && (
                          <Input
                            placeholder={step.action === 'goto' ? 'URL' : 'Selector'}
                            value={(step.action === 'goto' ? step.url : step.selector) || ''}
                            onChange={(e) =>
                              updateInitStep(
                                index,
                                step.action === 'goto' ? 'url' : 'selector',
                                e.target.value
                              )
                            }
                          />
                        )}
                        {step.action === 'fill' && (
                          <Input
                            placeholder="Value (use ${ENV_VAR} for env variables)"
                            value={(step.value as string) || ''}
                            onChange={(e) => updateInitStep(index, 'value', e.target.value)}
                          />
                        )}
                        <div className="flex items-center gap-4">
                          <label className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={step.critical ?? true}
                              onChange={(e) => updateInitStep(index, 'critical', e.target.checked)}
                              className="rounded"
                            />
                            Critical step
                          </label>
                          <label className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={step.screenshot ?? false}
                              onChange={(e) => updateInitStep(index, 'screenshot', e.target.checked)}
                              className="rounded"
                            />
                            Screenshot
                          </label>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No init steps configured. Add steps to set up the environment (e.g., login, navigate).
                  </p>
                )}
              </div>

              {/* Authentication */}
              <div className="space-y-4">
                <h3 className="text-md font-semibold">Authentication</h3>
                <div className="space-y-2">
                  <Label htmlFor="auth_type">Authentication Type</Label>
                  <Select
                    value={formData.auth_config?.type}
                    onValueChange={(value) =>
                      setFormData((prev) => ({
                        ...prev,
                        auth_config: { type: value as AuthConfig['type'] },
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select auth type" />
                    </SelectTrigger>
                    <SelectContent>
                      {AUTH_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {renderAuthFields()}
              </div>

              {/* Browser Configuration */}
              <div className="space-y-4">
                <h3 className="text-md font-semibold">Browser Configuration</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="browser_type">Browser</Label>
                    <Select
                      value={formData.browser_config?.browser_type || 'chromium'}
                      onValueChange={(value: any) =>
                        setFormData((prev) => ({
                          ...prev,
                          browser_config: { ...prev.browser_config!, browser_type: value },
                        }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {BROWSER_TYPES.map((browser) => (
                          <SelectItem key={browser.value} value={browser.value}>
                            {browser.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="framework">Framework</Label>
                    <Select
                      value={formData.browser_config?.framework || 'playwright'}
                      onValueChange={(value: any) =>
                        setFormData((prev) => ({
                          ...prev,
                          browser_config: { ...prev.browser_config!, framework: value },
                        }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="playwright">Playwright</SelectItem>
                        <SelectItem value="selenium">Selenium</SelectItem>
                        <SelectItem value="puppeteer">Puppeteer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.browser_config?.headless ?? true}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          browser_config: { ...prev.browser_config!, headless: e.target.checked },
                        }))
                      }
                      className="rounded"
                    />
                    <Label>Headless mode</Label>
                  </label>
                </div>
              </div>

              {/* LLM Configuration */}
              <div className="space-y-4">
                <h3 className="text-md font-semibold">LLM Configuration</h3>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="llm_enabled"
                    checked={formData.llm_config?.enabled ?? false}
                    onChange={(e) => updateLLMConfig('enabled', e.target.checked)}
                    className="rounded"
                  />
                  <Label htmlFor="llm_enabled">Enable LLM features</Label>
                </div>
                {formData.llm_config?.enabled && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="llm_provider">Provider</Label>
                        <Select
                          value={formData.llm_config.provider || 'claude-code-cli'}
                          onValueChange={(value: any) => updateLLMConfig('provider', value)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {LLM_PROVIDERS.map((provider) => (
                              <SelectItem key={provider.value} value={provider.value}>
                                {provider.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="llm_model">Model</Label>
                        <Input
                          id="llm_model"
                          value={formData.llm_config.model || 'claude-sonnet-4-5'}
                          onChange={(e) => updateLLMConfig('model', e.target.value)}
                          placeholder="claude-sonnet-4-5"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="llm_api_key_env">API Key Environment Variable</Label>
                      <Input
                        id="llm_api_key_env"
                        value={formData.llm_config.api_key_env || ''}
                        onChange={(e) => updateLLMConfig('api_key_env', e.target.value)}
                        placeholder="ANTHROPIC_API_KEY"
                      />
                      <p className="text-xs text-muted-foreground">
                        Environment variable containing the API key
                      </p>
                    </div>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.llm_config.use_for_test_generation ?? true}
                          onChange={(e) =>
                            updateLLMConfig('use_for_test_generation', e.target.checked)
                          }
                          className="rounded"
                        />
                        Test Generation
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.llm_config.use_for_selector_healing ?? true}
                          onChange={(e) =>
                            updateLLMConfig('use_for_selector_healing', e.target.checked)
                          }
                          className="rounded"
                        />
                        Selector Healing
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.llm_config.use_for_error_recovery ?? true}
                          onChange={(e) => updateLLMConfig('use_for_error_recovery', e.target.checked)}
                          className="rounded"
                        />
                        Error Recovery
                      </label>
                    </div>
                  </>
                )}
              </div>

              <div className="flex gap-2 pt-4 border-t sticky bottom-0 bg-background">
                <Button type="button" variant="outline" className="flex-1" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1"
                  disabled={createProfile.isPending || updateProfile.isPending}
                >
                  {createProfile.isPending || updateProfile.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : editingId ? (
                    'Update Profile'
                  ) : (
                    'Create Profile'
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Init Steps Visualization Modal */}
      {showStepsModal && selectedProfileForSteps && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-background rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-background z-10">
              <h2 className="text-lg font-semibold">
                Init Steps: {selectedProfileForSteps.name}
              </h2>
              <Button variant="ghost" size="sm" onClick={() => setShowStepsModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="p-6">
              {/* Steps Timeline */}
              <div className="space-y-4">
                {selectedProfileForSteps.init_steps?.map((step, index) => (
                  <div key={index} className="flex gap-4">
                    {/* Step Number */}
                    <div className="flex flex-col items-center">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 font-semibold text-sm">
                        {index + 1}
                      </div>
                      {index < (selectedProfileForSteps.init_steps?.length || 0) - 1 && (
                        <div className="w-0.5 h-full bg-blue-200 mt-2"></div>
                      )}
                    </div>

                    {/* Step Details */}
                    <div className="flex-1 pb-6">
                      <div className="bg-muted/50 rounded-lg p-4 border">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h3 className="font-semibold text-base">{step.name}</h3>
                            <Badge variant="outline" className="mt-1">
                              {step.action}
                            </Badge>
                            {step.critical && (
                              <Badge variant="destructive" className="mt-1 ml-2">
                                Critical
                              </Badge>
                            )}
                          </div>
                          {step.screenshot && (
                            <Badge variant="secondary">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Screenshot
                            </Badge>
                          )}
                        </div>

                        {step.description && (
                          <p className="text-sm text-muted-foreground mb-3">{step.description}</p>
                        )}

                        <div className="grid grid-cols-2 gap-3 text-sm">
                          {step.url && (
                            <div>
                              <span className="text-muted-foreground">URL:</span>
                              <code className="ml-2 px-2 py-1 bg-background rounded text-xs">
                                {step.url}
                              </code>
                            </div>
                          )}
                          {step.selector && (
                            <div>
                              <span className="text-muted-foreground">Selector:</span>
                              <code className="ml-2 px-2 py-1 bg-background rounded text-xs">
                                {step.selector}
                              </code>
                            </div>
                          )}
                          {step.value && (
                            <div>
                              <span className="text-muted-foreground">Value:</span>
                              <code className="ml-2 px-2 py-1 bg-background rounded text-xs">
                                {typeof step.value === 'string' ? step.value : JSON.stringify(step.value)}
                              </code>
                            </div>
                          )}
                          {step.timeout && (
                            <div>
                              <span className="text-muted-foreground">Timeout:</span>
                              <span className="ml-2">{step.timeout}ms</span>
                            </div>
                          )}
                          {step.wait_after && step.wait_after > 0 && (
                            <div>
                              <span className="text-muted-foreground">Wait After:</span>
                              <span className="ml-2">{step.wait_after}ms</span>
                            </div>
                          )}
                          {step.condition && (
                            <div className="col-span-2">
                              <span className="text-muted-foreground">Condition:</span>
                              <code className="ml-2 px-2 py-1 bg-background rounded text-xs">
                                {step.condition}
                              </code>
                            </div>
                          )}
                        </div>

                        {/* Execution Flow Indicators */}
                        <div className="mt-3 flex gap-2 text-xs">
                          {step.action === 'goto' && (
                            <Badge variant="outline" className="bg-purple-50">
                              → Navigate
                            </Badge>
                          )}
                          {step.action === 'click' && (
                            <Badge variant="outline" className="bg-blue-50">
                              ⊙ Click
                            </Badge>
                          )}
                          {step.action === 'fill' && (
                            <Badge variant="outline" className="bg-green-50">
                              ✎ Fill
                            </Badge>
                          )}
                          {step.action === 'wait_for' && (
                            <Badge variant="outline" className="bg-yellow-50">
                              ⏱ Wait For
                            </Badge>
                          )}
                          {step.action === 'wait' && (
                            <Badge variant="outline" className="bg-gray-50">
                              ⏸ Pause
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Summary */}
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-semibold text-sm mb-2">Execution Summary</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Total Steps:</span>
                    <span className="ml-2 font-medium">
                      {selectedProfileForSteps.init_steps?.length || 0}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Critical Steps:</span>
                    <span className="ml-2 font-medium">
                      {selectedProfileForSteps.init_steps?.filter((s) => s.critical).length || 0}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Screenshots:</span>
                    <span className="ml-2 font-medium">
                      {selectedProfileForSteps.init_steps?.filter((s) => s.screenshot).length || 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Close Button */}
              <div className="mt-6">
                <Button onClick={() => setShowStepsModal(false)} className="w-full">
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Profile Start Modal */}
      {showStartModal && selectedProfileForStart && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-background rounded-lg shadow-lg max-w-md w-full">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Start Profile: {selectedProfileForStart.name}</h2>
              <Button variant="ghost" size="sm" onClick={() => setShowStartModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="p-4 space-y-4">
              <p className="text-sm text-muted-foreground">
                Configure options for starting this profile. The profile will execute {selectedProfileForStart.init_steps?.length || 0} initialization steps.
              </p>

              <div className="space-y-2">
                <Label htmlFor="start_execution_mode">Execution Mode</Label>
                <Select
                  value={startOptions.execution_mode || selectedProfileForStart.execution_mode || 'automated'}
                  onValueChange={(value: any) =>
                    setStartOptions((prev) => ({ ...prev, execution_mode: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="automated">Automated (Headless)</SelectItem>
                    <SelectItem value="manual">Manual (Headed, Interactive)</SelectItem>
                    <SelectItem value="hybrid">Hybrid (Mixed)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={startOptions.headless}
                    onChange={(e) => setStartOptions((prev) => ({ ...prev, headless: e.target.checked }))}
                    className="rounded"
                  />
                  <Label>Headless mode</Label>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={startOptions.with_claude}
                    onChange={(e) =>
                      setStartOptions((prev) => ({ ...prev, with_claude: e.target.checked }))
                    }
                    className="rounded"
                  />
                  <Label>Enable Claude AI</Label>
                </label>
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowStartModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleStartProfile}
                  disabled={startingProfile === selectedProfileForStart.id}
                >
                  {startingProfile === selectedProfileForStart.id ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Start Profile
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Profile Generation Modal */}
      {showAIGenerateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg shadow-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    <Sparkles className="h-6 w-6 text-purple-500" />
                    Generate Profiles with AI
                  </h2>
                  <p className="text-muted-foreground mt-1">
                    Describe the profiles you want to create in natural language
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowAIGenerateModal(false)
                    setAiDescription('')
                    setAiGeneratedProfiles([])
                    setAiReasoning('')
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="ai-description">Description</Label>
                  <Textarea
                    id="ai-description"
                    placeholder="Example: Create two profiles for Superset running on localhost:9001. One pre-auth profile that just navigates to the login page, and one authenticated profile that logs in with admin/admin credentials."
                    value={aiDescription}
                    onChange={(e) => setAiDescription(e.target.value)}
                    rows={6}
                    className="mt-2"
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    Tip: Be specific about URLs, credentials, and workflow steps
                  </p>
                </div>

                <div className="flex gap-4">
                  <Button
                    onClick={() => {
                      generateProfilesWithAI.mutate({
                        description: aiDescription,
                        provider: 'anthropic',
                        model: 'claude-sonnet-4-5-20250929',
                        api_key_env: 'ANTHROPIC_API_KEY',
                      })
                    }}
                    disabled={!aiDescription.trim() || generateProfilesWithAI.isPending}
                    className="flex-1"
                  >
                    {generateProfilesWithAI.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Generate Profiles
                      </>
                    )}
                  </Button>
                </div>

                {generateProfilesWithAI.isError && (
                  <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                    <p className="text-sm text-destructive">
                      {(generateProfilesWithAI.error as any)?.response?.data?.message ||
                        'Failed to generate profiles. Please try again.'}
                    </p>
                  </div>
                )}

                {aiReasoning && (
                  <div className="bg-muted rounded-lg p-4">
                    <h3 className="font-semibold mb-2">AI Reasoning</h3>
                    <p className="text-sm text-muted-foreground">{aiReasoning}</p>
                  </div>
                )}

                {aiGeneratedProfiles.length > 0 && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">Generated Profiles ({aiGeneratedProfiles.length})</h3>
                      <Button
                        size="sm"
                        onClick={async () => {
                          // Create all generated profiles
                          for (const profile of aiGeneratedProfiles) {
                            await createProfile.mutateAsync(profile as any)
                          }
                          setShowAIGenerateModal(false)
                          setAiDescription('')
                          setAiGeneratedProfiles([])
                          setAiReasoning('')
                        }}
                        disabled={createProfile.isPending}
                      >
                        {createProfile.isPending ? (
                          <>
                            <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                            Creating...
                          </>
                        ) : (
                          <>Create All</>
                        )}
                      </Button>
                    </div>

                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {aiGeneratedProfiles.map((profile, index) => (
                        <Card key={index} className="bg-muted/50">
                          <CardHeader className="pb-3">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <CardTitle className="text-lg">{profile.name}</CardTitle>
                                <CardDescription className="mt-1">{profile.description}</CardDescription>
                              </div>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={async () => {
                                  await createProfile.mutateAsync(profile as any)
                                  setAiGeneratedProfiles((prev) => prev.filter((_, i) => i !== index))
                                  if (aiGeneratedProfiles.length === 1) {
                                    setShowAIGenerateModal(false)
                                    setAiDescription('')
                                    setAiReasoning('')
                                  }
                                }}
                                disabled={createProfile.isPending}
                              >
                                Create
                              </Button>
                            </div>
                          </CardHeader>
                          <CardContent className="space-y-2">
                            <div className="flex gap-2 flex-wrap">
                              <Badge variant="outline">{profile.profile_type}</Badge>
                              <Badge variant="outline">{profile.execution_mode}</Badge>
                              {profile.init_steps && profile.init_steps.length > 0 && (
                                <Badge variant="secondary">{profile.init_steps.length} init steps</Badge>
                              )}
                              {profile.tags?.map((tag) => (
                                <Badge key={tag} variant="secondary">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              <strong>URL:</strong> {profile.base_url}
                            </div>
                            {profile.init_steps && profile.init_steps.length > 0 && (
                              <div className="text-xs text-muted-foreground">
                                Init steps:{' '}
                                {profile.init_steps.map((step: any) => step.name).join(' → ')}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Test Generation Modal */}
      {showTestGenerateModal && selectedProfileForTestGen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg shadow-lg max-w-5xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    <Wand2 className="h-6 w-6 text-purple-500" />
                    Generate Tests from Environment
                  </h2>
                  <p className="text-muted-foreground mt-1">
                    {selectedProfileForTestGen.name}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTestGenerateModal(false)}
                >
                  ✕
                </Button>
              </div>

              {/* Configuration */}
              {!testGenResult && (
                <div className="space-y-4">
                  <div>
                    <Label>Coverage Level</Label>
                    <div className="grid grid-cols-4 gap-2 mt-2">
                      {[
                        { value: 'smoke', label: 'Smoke', desc: '5-10 tests, <5 min', color: 'bg-green-500' },
                        { value: 'canary', label: 'Canary', desc: '15-25 tests, 10-15 min', color: 'bg-blue-500' },
                        { value: 'medium', label: 'Medium', desc: '30-50 tests, 30-45 min', color: 'bg-yellow-500' },
                        { value: 'deep', label: 'Deep', desc: '50+ tests, 1-2 hours', color: 'bg-red-500' },
                      ].map((level) => (
                        <button
                          key={level.value}
                          onClick={() => setTestGenerateConfig(prev => ({ ...prev, coverage_level: level.value as any }))}
                          className={`p-4 rounded-lg border-2 text-left transition-all ${
                            testGenerateConfig.coverage_level === level.value
                              ? 'border-primary bg-primary/10'
                              : 'border-border hover:border-primary/50'
                          }`}
                        >
                          <div className={`w-2 h-2 rounded-full ${level.color} mb-2`} />
                          <div className="font-semibold">{level.label}</div>
                          <div className="text-xs text-muted-foreground">{level.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <Label>Crawl Depth: {testGenerateConfig.crawl_depth}</Label>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      value={testGenerateConfig.crawl_depth}
                      onChange={(e) => setTestGenerateConfig(prev => ({ ...prev, crawl_depth: parseInt(e.target.value) }))}
                      className="w-full mt-2"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>Current page only</span>
                      <span>Deep exploration</span>
                    </div>
                  </div>

                  <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
                    <p className="text-sm">
                      ⚠️ <strong>Important:</strong> This profile must be started first with an active browser session.
                      Click "Start" and ensure the browser is open before generating tests.
                    </p>
                  </div>

                  <Button
                    onClick={handleGenerateTests}
                    disabled={generatingTests}
                    className="w-full"
                  >
                    {generatingTests ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing environment and generating tests...
                      </>
                    ) : (
                      <>
                        <Wand2 className="mr-2 h-4 w-4" />
                        Generate Tests
                      </>
                    )}
                  </Button>
                </div>
              )}

              {/* Results */}
              {testGenResult && (
                <div className="space-y-4">
                  {testGenResult.success ? (
                    <>
                      <div className="bg-green-50 dark:bg-green-950 p-4 rounded-lg">
                        <p className="font-semibold text-green-900 dark:text-green-100">
                          ✓ Generated {testGenResult.count} tests for {testGenResult.coverage_level} coverage
                        </p>
                        {testGenResult.reasoning && (
                          <p className="text-sm mt-2 text-green-800 dark:text-green-200">
                            {testGenResult.reasoning}
                          </p>
                        )}
                      </div>

                      <div className="space-y-3 max-h-[400px] overflow-y-auto">
                        {generatedTests.map((test, index) => (
                          <div key={index} className="border rounded-lg p-4">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h3 className="font-semibold">{test.name}</h3>
                                <p className="text-sm text-muted-foreground mt-1">{test.description}</p>
                                <div className="flex gap-2 mt-2">
                                  {test.tags?.map((tag: string, i: number) => (
                                    <span key={i} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                                <div className="text-xs text-muted-foreground mt-2">
                                  {test.steps?.length || 0} steps • Priority: {test.priority}
                                </div>
                              </div>
                              <Button
                                size="sm"
                                onClick={() => handleSaveGeneratedTest(test, index)}
                              >
                                <Save className="mr-2 h-3 w-3" />
                                Save
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          onClick={() => {
                            setTestGenResult(null)
                            setGeneratedTests([])
                          }}
                        >
                          Generate More
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => setShowTestGenerateModal(false)}
                          className="flex-1"
                        >
                          Close
                        </Button>
                      </div>
                    </>
                  ) : (
                    <div className="bg-red-50 dark:bg-red-950 p-4 rounded-lg">
                      <p className="font-semibold text-red-900 dark:text-red-100">
                        ✗ {testGenResult.message}
                      </p>
                      <Button
                        variant="outline"
                        onClick={() => setTestGenResult(null)}
                        className="mt-4"
                      >
                        Try Again
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
