export interface TestDefinition {
  id: string
  org_id: string
  name: string
  description?: string
  version: string
  url?: string
  steps: TestStep[]
  evaluators: EvaluatorConfig[]
  browser_config?: BrowserConfig
  auth_config?: AuthConfig
  timeout?: number
  retry_config?: RetryConfig
  tags: string[]
  created_at: string
  updated_at: string
  created_by: string
}

export interface TestStep {
  name: string
  action: string
  selector?: string
  value?: string
  timeout?: number
  screenshot?: boolean
  condition?: string
  retry?: RetryConfig
}

export interface EvaluatorConfig {
  name: string
  type: string
  max_errors?: number
  max_load_time?: number
  max_ms?: number
  [key: string]: any
}

export interface BrowserConfig {
  type?: 'chromium' | 'firefox' | 'webkit'  // Deprecated, use browser_type
  browser_type?: 'chromium' | 'chrome' | 'firefox' | 'webkit'
  framework?: 'playwright' | 'selenium' | 'puppeteer'
  headless: boolean
  viewport?: {
    width: number
    height: number
  }
  device?: string
  device_emulation?: DeviceEmulationConfig
  locale?: string
  timezone?: string
  permissions?: string[]
  slowmo?: number
  record_video?: boolean
  record_har?: boolean
}

export interface DeviceEmulationConfig {
  device_name?: string
  viewport?: { width: number; height: number }
  user_agent?: string
  device_scale_factor?: number
  is_mobile?: boolean
  has_touch?: boolean
  locale?: string
  timezone?: string
  geolocation?: { latitude: number; longitude: number; accuracy: number }
  permissions?: string[]
}

export interface AuthConfig {
  type: 'none' | 'form' | 'oauth' | 'jwt' | 'basic' | 'bearer' | 'api_key' | 'custom'
  username?: string
  password?: string
  provider?: string
  client_id?: string
  client_secret?: string
  token?: string
  // API Key auth
  api_key?: string
  api_key_header?: string
  api_key_prefix?: string
  [key: string]: any
}

export interface RetryConfig {
  max_attempts: number
  backoff_ms: number
}

export interface TestRun {
  id: string
  test_id: string
  test_name: string
  org_id: string
  profile: string
  triggered_by: 'manual' | 'ci' | 'scheduled' | 'api'
  context?: Record<string, any>
  status: 'pending' | 'running' | 'completed' | 'failed' | 'aborted'
  started_at?: string
  completed_at?: string
  duration_ms?: number
  result?: TestResult
  screenshots: Screenshot[]
  video_url?: string
  trace_url?: string
  logs: LogEntry[]
  har_url?: string
  created_at: string
}

export interface TestResult {
  passed: boolean
  score: number
  steps_executed: number
  steps_passed: number
  steps_failed: number
  evaluator_results: EvalResult[]
  total_duration_ms: number
  page_load_time_ms?: number
  time_to_interactive_ms?: number
  error_message?: string
  error_screenshot_url?: string
}

export interface EvalResult {
  passed: boolean
  score: number
  evaluator_name: string
  reason?: string
  details?: Record<string, any>
  screenshot_path?: string
}

export interface Screenshot {
  id: string
  test_run_id: string
  step_name: string
  step_index: number
  url: string
  thumbnail_url?: string
  timestamp: string
  file_size?: number
}

export interface LogEntry {
  id: string
  test_run_id: string
  level: 'debug' | 'info' | 'warn' | 'error'
  message: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface InitStep {
  name: string
  action: string
  selector?: string
  value?: string | Record<string, any>
  url?: string
  timeout?: number
  wait_after?: number
  screenshot?: boolean
  description?: string
  critical?: boolean
  condition?: string
}

export interface LLMConfig {
  enabled: boolean
  provider?: 'claude-code-cli' | 'claude-sdk' | 'claude-api' | 'openai' | 'ollama' | 'custom'
  model?: string
  api_key_env?: string
  api_key?: string
  base_url?: string
  temperature?: number
  max_tokens?: number
  timeout?: number
  cli_command?: string
  cli_args?: string[]
  use_for_test_generation?: boolean
  use_for_selector_healing?: boolean
  use_for_error_recovery?: boolean
}

export interface Profile {
  id: string
  org_id: string
  name: string
  description?: string
  profile_type?: 'environment' | 'workflow' | 'custom'
  execution_mode?: 'automated' | 'manual' | 'hybrid'
  base_url: string
  init_steps?: InitStep[]
  auth_config: AuthConfig
  browser_config: BrowserConfig
  llm_config?: LLMConfig
  notification_config?: NotificationConfig
  tags?: string[]
  created_at?: string
  updated_at?: string
}

export interface ProfileTestResult {
  success: boolean
  latency_ms?: number
  error?: string
  tested_at: string
}

export interface ProfileStartRequest {
  execution_mode?: 'automated' | 'manual' | 'hybrid'
  headless?: boolean
  with_claude?: boolean
}

export interface ProfileStartResponse {
  success: boolean
  session_id?: string
  steps_executed: number
  errors: string[]
  message: string
}

export interface AIProfileGenerateRequest {
  description: string
  provider?: string
  model?: string
  api_key_env?: string
}

export interface AIProfileGenerateResponse {
  success: boolean
  profiles: Partial<Profile>[]
  message: string
  reasoning?: string
}

export interface AITestGenerateRequest {
  profile_id: string
  coverage_level: 'smoke' | 'canary' | 'medium' | 'deep'
  crawl_depth: number
  provider?: string
  model?: string
  api_key_env?: string
}

export interface AITestGenerateResponse {
  success: boolean
  tests: Partial<TestDefinition>[]
  count: number
  coverage_level: string
  site_data?: any
  message: string
  reasoning?: string
}

export interface NotificationConfig {
  on_failure?: NotificationTarget[]
  on_success?: NotificationTarget[]
}

export interface NotificationTarget {
  type: 'slack' | 'email' | 'webhook'
  destination: string
}

export interface Organization {
  id: string
  name: string
  plan: 'free' | 'team' | 'enterprise'
  monthly_test_runs: number
  storage_gb: number
  retention_days: number
  settings: Record<string, any>
  created_at: string
}

export interface User {
  id: string
  email: string
  name: string
  org_id: string
  role: 'admin' | 'member' | 'viewer'
  created_at: string
  last_login?: string
}

export interface DashboardStats {
  total_tests: number
  total_runs: number
  pass_rate: number
  avg_duration_ms: number
  recent_runs: TestRun[]
  flaky_tests: Array<{
    test_id: string
    test_name: string
    flakiness_score: number
  }>
  trends: {
    dates: string[]
    passed: number[]
    failed: number[]
  }
}
