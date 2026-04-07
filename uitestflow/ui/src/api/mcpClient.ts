import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8018/api/mcp',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Add API key for MCP endpoints - set via environment variable
  const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY
  if (apiKey) {
    config.headers['x-api-key'] = apiKey
  }
  return config
})

// Types
export interface GenerateTestRequest {
  description: string
  base_url?: string
  model?: string
  temperature?: number
  save?: boolean
}

export interface GenerateTestResponse {
  test_id: string
  test_definition: any
  generation_time_ms: number
  model_used: string
}

export interface ExecuteTestRequest {
  test_id?: string
  test_definition?: any
  with_claude?: boolean
  model?: string
  headless?: boolean
}

export interface ExecuteTestResponse {
  run_id: string
  status: string
  message: string
}

export interface MCPStatusResponse {
  mcp_enabled: boolean
  server_available: boolean
  api_key_configured: boolean
  available_tools: string[]
  default_model: string
  transport: string
}

export interface FeedbackItem {
  step_index: number
  step_name: string
  guidance?: string
  selector_adapted: boolean
  original_selector?: string
  adapted_selector?: string
  recovery_attempted: boolean
  recovery_action?: string
  success: boolean
}

export interface FeedbackResponse {
  run_id: string
  test_name: string
  total_steps: number
  feedback_items: FeedbackItem[]
  overall_guidance?: string
}

// API Client
export const mcpApi = {
  /**
   * Generate a test from natural language description
   */
  generateTest: (request: GenerateTestRequest) =>
    api.post<GenerateTestResponse>('/generate', request),

  /**
   * Execute a test with optional Claude guidance
   */
  executeTest: (request: ExecuteTestRequest) =>
    api.post<ExecuteTestResponse>('/execute', request),

  /**
   * Get MCP server status
   */
  getStatus: () => api.get<MCPStatusResponse>('/status'),

  /**
   * Get Claude feedback for a test run
   */
  getFeedback: (runId: string, page = 1, pageSize = 20) =>
    api.get<FeedbackResponse>(`/feedback/${runId}`, {
      params: { page, page_size: pageSize },
    }),
}

export default mcpApi
