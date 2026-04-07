import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Editor from '@monaco-editor/react'
import * as yaml from 'js-yaml'
import { testApi } from '@/lib/api'
import { TestDefinition, TestStep } from '@/types'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import {
  Save,
  AlertCircle,
  CheckCircle2,
  FileCode,
  Eye,
  Loader2,
} from 'lucide-react'

const TEMPLATES = {
  empty: {
    name: 'Empty Test',
    yaml: `name: "New Test"
description: "Test description"
version: "1.0"
url: "https://example.com"

browser_config:
  type: chromium
  headless: true

steps:
  - name: "Navigate to page"
    action: navigate
    value: "{{ url }}"

  - name: "Wait for page load"
    action: wait
    selector: "body"

evaluators:
  - name: "Page Load Time"
    type: page_load_time
    max_ms: 3000
`,
  },
  login: {
    name: 'Login Flow',
    yaml: `name: "Login Test"
description: "Test user login functionality"
version: "1.0"
url: "https://example.com/login"

browser_config:
  type: chromium
  headless: true

steps:
  - name: "Navigate to login page"
    action: navigate
    value: "{{ url }}"

  - name: "Fill username"
    action: fill
    selector: 'input[name="username"]'
    value: "testuser"

  - name: "Fill password"
    action: fill
    selector: 'input[name="password"]'
    value: "{{ password }}"

  - name: "Click login button"
    action: click
    selector: 'button[type="submit"]'

  - name: "Wait for dashboard"
    action: wait
    selector: ".dashboard"
    screenshot: true

evaluators:
  - name: "Console Errors"
    type: console_errors
    max_errors: 0

  - name: "Page Load Time"
    type: page_load_time
    max_ms: 3000
`,
  },
  form: {
    name: 'Form Submission',
    yaml: `name: "Form Test"
description: "Test form submission"
version: "1.0"
url: "https://example.com/form"

browser_config:
  type: chromium
  headless: true

steps:
  - name: "Navigate to form"
    action: navigate
    value: "{{ url }}"

  - name: "Fill name field"
    action: fill
    selector: 'input[name="name"]'
    value: "John Doe"

  - name: "Fill email field"
    action: fill
    selector: 'input[name="email"]'
    value: "john@example.com"

  - name: "Select option"
    action: select
    selector: 'select[name="country"]'
    value: "US"

  - name: "Check terms checkbox"
    action: check
    selector: 'input[name="terms"]'

  - name: "Submit form"
    action: click
    selector: 'button[type="submit"]'
    screenshot: true

  - name: "Wait for success message"
    action: wait
    selector: ".success-message"
    screenshot: true

evaluators:
  - name: "No Console Errors"
    type: console_errors
    max_errors: 0

  - name: "Success Message Present"
    type: element_present
    selector: ".success-message"
`,
  },
  navigation: {
    name: 'Navigation Test',
    yaml: `name: "Navigation Test"
description: "Test site navigation"
version: "1.0"
url: "https://example.com"

browser_config:
  type: chromium
  headless: true

steps:
  - name: "Navigate to homepage"
    action: navigate
    value: "{{ url }}"
    screenshot: true

  - name: "Click About link"
    action: click
    selector: 'a[href="/about"]'

  - name: "Wait for About page"
    action: wait
    selector: ".about-page"
    screenshot: true

  - name: "Click Products link"
    action: click
    selector: 'a[href="/products"]'

  - name: "Wait for Products page"
    action: wait
    selector: ".products-page"
    screenshot: true

  - name: "Click Contact link"
    action: click
    selector: 'a[href="/contact"]'

  - name: "Wait for Contact page"
    action: wait
    selector: ".contact-page"
    screenshot: true

evaluators:
  - name: "No Broken Links"
    type: console_errors
    max_errors: 0

  - name: "Fast Page Loads"
    type: page_load_time
    max_ms: 2000
`,
  },
}

interface ParsedTest {
  name?: string
  description?: string
  version?: string
  url?: string
  steps?: TestStep[]
  evaluators?: any[]
  browser_config?: any
  auth_config?: any
  timeout?: number
  retry_config?: any
  tags?: string[]
}

export function TestEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEditMode = Boolean(id)

  const [yamlContent, setYamlContent] = useState(TEMPLATES.empty.yaml)
  const [validationError, setValidationError] = useState<string | null>(null)
  const [parsedTest, setParsedTest] = useState<ParsedTest | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('empty')
  const [testName, setTestName] = useState('')

  const { data: existingTest, isLoading: isLoadingTest } = useQuery({
    queryKey: ['test', id],
    queryFn: async () => {
      if (!id) return null
      const response = await testApi.getTest(id)
      return response.data
    },
    enabled: isEditMode,
  })

  useEffect(() => {
    if (existingTest) {
      const yamlString = generateYamlFromTest(existingTest)
      setYamlContent(yamlString)
      setTestName(existingTest.name)
      validateYaml(yamlString)
    }
  }, [existingTest])

  const createMutation = useMutation({
    mutationFn: (test: Partial<TestDefinition>) => testApi.createTest(test),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      navigate('/library')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (test: Partial<TestDefinition>) => testApi.updateTest(id!, test),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      queryClient.invalidateQueries({ queryKey: ['test', id] })
      navigate('/library')
    },
  })

  const generateYamlFromTest = (test: TestDefinition): string => {
    const testObj: any = {
      name: test.name,
      description: test.description,
      version: test.version,
      url: test.url,
      browser_config: test.browser_config,
      steps: test.steps,
      evaluators: test.evaluators,
    }
    if (test.auth_config) testObj.auth_config = test.auth_config
    if (test.timeout) testObj.timeout = test.timeout
    if (test.retry_config) testObj.retry_config = test.retry_config
    if (test.tags && test.tags.length > 0) testObj.tags = test.tags

    return yaml.dump(testObj, { lineWidth: -1 })
  }

  const validateYaml = (content: string) => {
    try {
      const parsed = yaml.load(content) as ParsedTest
      if (!parsed || typeof parsed !== 'object') {
        throw new Error('Invalid YAML structure')
      }
      if (!parsed.name) {
        throw new Error('Test name is required')
      }
      if (!parsed.steps || !Array.isArray(parsed.steps) || parsed.steps.length === 0) {
        throw new Error('At least one step is required')
      }
      setValidationError(null)
      setParsedTest(parsed)
      return true
    } catch (error: any) {
      setValidationError(error.message)
      setParsedTest(null)
      return false
    }
  }

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setYamlContent(value)
      validateYaml(value)
    }
  }

  const handleTemplateChange = (template: string) => {
    setSelectedTemplate(template)
    const templateData = TEMPLATES[template as keyof typeof TEMPLATES]
    if (templateData) {
      setYamlContent(templateData.yaml)
      validateYaml(templateData.yaml)
    }
  }

  const handleSave = () => {
    if (!validateYaml(yamlContent)) {
      return
    }

    const testData: Partial<TestDefinition> = {
      name: parsedTest?.name || testName,
      description: parsedTest?.description,
      version: parsedTest?.version || '1.0',
      url: parsedTest?.url,
      steps: parsedTest?.steps || [],
      evaluators: parsedTest?.evaluators || [],
      browser_config: parsedTest?.browser_config,
      auth_config: parsedTest?.auth_config,
      timeout: parsedTest?.timeout,
      retry_config: parsedTest?.retry_config,
      tags: parsedTest?.tags || [],
    }

    if (isEditMode) {
      updateMutation.mutate(testData)
    } else {
      createMutation.mutate(testData)
    }
  }

  const isSaving = createMutation.isPending || updateMutation.isPending

  if (isEditMode && isLoadingTest) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading test...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {isEditMode ? 'Edit Test' : 'Create New Test'}
          </h1>
          <p className="text-muted-foreground">
            {isEditMode ? 'Modify your test definition' : 'Define a new UI test using YAML'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => navigate('/library')}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!!validationError || isSaving}
            className="gap-2"
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            {isEditMode ? 'Update Test' : 'Create Test'}
          </Button>
        </div>
      </div>

      {!isEditMode && (
        <Card>
          <CardHeader>
            <CardTitle>Template</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Select value={selectedTemplate} onValueChange={handleTemplateChange}>
                <SelectTrigger className="w-64">
                  <SelectValue placeholder="Select a template" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="empty">Empty Test</SelectItem>
                  <SelectItem value="login">Login Flow</SelectItem>
                  <SelectItem value="form">Form Submission</SelectItem>
                  <SelectItem value="navigation">Navigation Test</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Start with a template or build from scratch
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="h-[600px] flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileCode className="h-5 w-5" />
                YAML Editor
              </CardTitle>
              {validationError ? (
                <Badge variant="destructive" className="gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Invalid
                </Badge>
              ) : (
                <Badge className="gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  Valid
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            <Editor
              height="100%"
              defaultLanguage="yaml"
              value={yamlContent}
              onChange={handleEditorChange}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                rulers: [80],
                wordWrap: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
              }}
            />
          </CardContent>
        </Card>

        <Card className="h-[600px] flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Preview
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto">
            {validationError ? (
              <div className="flex items-start gap-2 p-4 bg-destructive/10 border border-destructive rounded-md">
                <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-destructive">Validation Error</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {validationError}
                  </p>
                </div>
              </div>
            ) : parsedTest ? (
              <div className="space-y-4">
                <div>
                  <Label className="text-xs text-muted-foreground">Test Name</Label>
                  <p className="font-medium">{parsedTest.name}</p>
                </div>

                {parsedTest.description && (
                  <div>
                    <Label className="text-xs text-muted-foreground">Description</Label>
                    <p className="text-sm">{parsedTest.description}</p>
                  </div>
                )}

                <div>
                  <Label className="text-xs text-muted-foreground">Version</Label>
                  <p className="text-sm">{parsedTest.version || '1.0'}</p>
                </div>

                {parsedTest.url && (
                  <div>
                    <Label className="text-xs text-muted-foreground">URL</Label>
                    <p className="text-sm font-mono text-xs bg-muted px-2 py-1 rounded">
                      {parsedTest.url}
                    </p>
                  </div>
                )}

                {parsedTest.browser_config && (
                  <div>
                    <Label className="text-xs text-muted-foreground">Browser</Label>
                    <div className="flex gap-2 mt-1">
                      <Badge variant="outline">
                        {parsedTest.browser_config.type || 'chromium'}
                      </Badge>
                      {parsedTest.browser_config.headless && (
                        <Badge variant="outline">headless</Badge>
                      )}
                    </div>
                  </div>
                )}

                <div>
                  <Label className="text-xs text-muted-foreground">
                    Steps ({parsedTest.steps?.length || 0})
                  </Label>
                  <div className="mt-2 space-y-2">
                    {parsedTest.steps?.map((step, index) => (
                      <div
                        key={index}
                        className="p-3 bg-muted rounded-md border"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-sm">{step.name}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              Action: <Badge variant="outline" className="text-xs">
                                {step.action}
                              </Badge>
                            </p>
                            {step.selector && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Selector: <code className="bg-background px-1 rounded">
                                  {step.selector}
                                </code>
                              </p>
                            )}
                            {step.value && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Value: <code className="bg-background px-1 rounded">
                                  {step.value}
                                </code>
                              </p>
                            )}
                          </div>
                          <Badge variant="secondary" className="ml-2">
                            {index + 1}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {parsedTest.evaluators && parsedTest.evaluators.length > 0 && (
                  <div>
                    <Label className="text-xs text-muted-foreground">
                      Evaluators ({parsedTest.evaluators.length})
                    </Label>
                    <div className="mt-2 space-y-2">
                      {parsedTest.evaluators.map((evaluator, index) => (
                        <div
                          key={index}
                          className="p-3 bg-muted rounded-md border"
                        >
                          <p className="font-medium text-sm">{evaluator.name}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Type: <Badge variant="outline" className="text-xs">
                              {evaluator.type}
                            </Badge>
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <p>Preview will appear here as you type</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
