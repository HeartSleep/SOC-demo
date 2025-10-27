import type {
  Asset, AssetCreate, AssetUpdate, AssetFilters,
  Task, TaskCreate, TaskUpdate, TaskFilters,
  Vulnerability, VulnerabilityCreate, VulnerabilityUpdate, VulnerabilityFilters,
  Report, ReportCreate, ReportUpdate, ReportFilters,
  User, UserCreate, UserUpdate, UserFilters,
  SystemSettings, SystemInfo, SystemMetrics, SystemAlert, HealthCheck, DashboardStats,
  PaginatedResponse, PaginationParams, ApiResponse, ExportOptions, ImportResult
} from './index'

// API Base Configuration
export interface ApiConfig {
  baseURL: string
  timeout: number
  withCredentials: boolean
}

export interface RequestConfig {
  headers?: Record<string, string>
  params?: Record<string, any>
  timeout?: number
}

// Authentication API
export interface LoginRequest {
  username: string
  password: string
  remember_me?: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token?: string
  user: User
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface ResetPasswordRequest {
  email: string
}

export interface ResetPasswordConfirmRequest {
  token: string
  new_password: string
}

// Asset API
export interface AssetListParams extends PaginationParams, AssetFilters {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface AssetBulkUpdateRequest {
  asset_ids: string[]
  updates: Partial<AssetUpdate>
}

export interface AssetBulkDeleteRequest {
  asset_ids: string[]
}

export interface AssetImportRequest {
  format: 'csv' | 'json' | 'nmap' | 'masscan'
  data: string | File
  options?: {
    skip_duplicates?: boolean
    update_existing?: boolean
    default_priority?: string
    default_tags?: string[]
  }
}

export interface AssetScanRequest {
  asset_ids: string[]
  scan_type: 'port_scan' | 'vulnerability_scan' | 'full_scan'
  config?: {
    timeout?: number
    ports?: string
    intensity?: number
  }
}

// Task API
export interface TaskListParams extends PaginationParams, TaskFilters {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface TaskStartRequest {
  task_id: string
  force?: boolean
}

export interface TaskStopRequest {
  task_id: string
  reason?: string
}

export interface TaskCloneRequest {
  task_id: string
  new_name?: string
  modifications?: Partial<TaskUpdate>
}

export interface TaskBulkOperationRequest {
  task_ids: string[]
  operation: 'start' | 'stop' | 'delete' | 'clone'
  options?: any
}

// Vulnerability API
export interface VulnerabilityListParams extends PaginationParams, VulnerabilityFilters {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface VulnerabilityVerifyRequest {
  vulnerability_id: string
  verification_notes?: string
  proof_files?: File[]
}

export interface VulnerabilityFixRequest {
  vulnerability_id: string
  fix_notes?: string
  fix_verification?: string
}

export interface VulnerabilityBulkUpdateRequest {
  vulnerability_ids: string[]
  updates: Partial<VulnerabilityUpdate>
}

export interface VulnerabilityRetestRequest {
  vulnerability_id: string
  retest_config?: any
}

// Report API
export interface ReportListParams extends PaginationParams, ReportFilters {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface ReportGenerateRequest {
  report_id: string
  force_regenerate?: boolean
}

export interface ReportShareRequest {
  report_id: string
  recipients: string[]
  message?: string
  expires_at?: string
}

export interface ReportTemplateListResponse {
  templates: ReportTemplate[]
}

export interface ReportTemplate {
  id: string
  name: string
  description: string
  type: string
  sections: string[]
  variables: Record<string, any>
}

// User API
export interface UserListParams extends PaginationParams, UserFilters {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface UserRoleUpdateRequest {
  user_id: string
  role: string
  reason?: string
}

export interface UserActivationRequest {
  user_id: string
  active: boolean
  reason?: string
}

export interface UserPasswordResetRequest {
  user_id: string
  temporary_password?: boolean
  send_email?: boolean
}

// Settings API
export interface SettingsUpdateRequest {
  category: string
  settings: Record<string, any>
}

export interface SettingsTestRequest {
  category: string
  test_type: string
  config?: Record<string, any>
}

export interface BackupCreateRequest {
  name?: string
  include_files?: boolean
  compression?: 'none' | 'gzip' | 'bzip2'
}

export interface BackupRestoreRequest {
  backup_id: string
  options?: {
    restore_files?: boolean
    restore_database?: boolean
    restore_config?: boolean
  }
}

export interface BackupListResponse {
  backups: BackupInfo[]
}

export interface BackupInfo {
  id: string
  name: string
  size: number
  created_at: string
  type: 'manual' | 'automatic'
  status: 'completed' | 'in_progress' | 'failed'
}

// System API
export interface SystemLogsParams extends PaginationParams {
  level?: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  source?: string
  start_date?: string
  end_date?: string
  search?: string
}

export interface SystemLogsResponse extends PaginatedResponse<LogEntry> {}

export interface LogEntry {
  id: string
  timestamp: string
  level: string
  message: string
  source: string
  user_id?: string
  request_id?: string
  extra?: Record<string, any>
}

export interface SystemServiceStatus {
  name: string
  status: 'running' | 'stopped' | 'error'
  pid?: number
  uptime?: string
  memory?: string
  cpu?: string
}

export interface SystemServicesResponse {
  services: Record<string, SystemServiceStatus>
  last_updated: string
}

export interface SystemPerformanceStats {
  response_times: {
    api_avg: string
    database_avg: string
    cache_avg: string
  }
  request_stats: {
    total_requests: number
    requests_per_minute: number
    error_rate: string
  }
  resource_usage: {
    cpu_cores: number
    cpu_usage: string
    memory_total: string
    memory_used: string
    disk_total: string
    disk_used: string
  }
  database_stats: {
    connections: number
    max_connections: number
    slow_queries: number
    cache_hit_rate: string
  }
}

// Notification API
export interface NotificationListParams extends PaginationParams {
  read?: boolean
  type?: string
  start_date?: string
  end_date?: string
}

export interface NotificationMarkReadRequest {
  notification_ids: string[]
}

export interface NotificationSendRequest {
  recipients: string[]
  title: string
  message: string
  type?: 'info' | 'warning' | 'error' | 'success'
  action_url?: string
  action_text?: string
}

// Integration API
export interface IntegrationTestRequest {
  integration_type: 'fofa' | 'slack' | 'webhook' | 'email'
  config?: Record<string, any>
}

export interface IntegrationTestResponse {
  success: boolean
  message: string
  response_time?: number
  details?: any
}

export interface WebhookDelivery {
  id: string
  url: string
  event: string
  status: 'pending' | 'delivered' | 'failed'
  attempts: number
  created_at: string
  delivered_at?: string
  response_code?: number
  response_body?: string
}

// File Upload/Download API
export interface FileUploadResponse {
  file_id: string
  filename: string
  size: number
  content_type: string
  url: string
}

export interface BulkOperationResult {
  total: number
  success: number
  failed: number
  errors: Array<{
    id: string
    error: string
  }>
}

// Search API
export interface SearchParams {
  query: string
  types?: ('assets' | 'vulnerabilities' | 'tasks' | 'reports')[]
  limit?: number
  highlight?: boolean
}

export interface SearchResult {
  type: string
  id: string
  title: string
  description?: string
  score: number
  highlights?: Record<string, string[]>
  entity: any
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  took: number
  aggregations?: Record<string, any>
}

// Statistics API
export interface StatisticsParams {
  start_date?: string
  end_date?: string
  granularity?: 'hour' | 'day' | 'week' | 'month'
  metrics?: string[]
}

export interface StatisticsResponse {
  metrics: Record<string, StatisticMetric[]>
  summary: Record<string, number>
}

export interface StatisticMetric {
  timestamp: string
  value: number
  metadata?: Record<string, any>
}

// Export/Import API
export interface ExportRequest extends ExportOptions {
  entity_type: 'assets' | 'vulnerabilities' | 'tasks' | 'reports'
  entity_ids?: string[]
}

export interface ExportResponse {
  job_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  download_url?: string
  expires_at?: string
}

export interface ImportRequest {
  entity_type: 'assets' | 'vulnerabilities' | 'tasks'
  format: string
  file: File
  options?: Record<string, any>
}

// Webhook API
export interface WebhookConfig {
  url: string
  events: string[]
  secret?: string
  active: boolean
  ssl_verification?: boolean
  content_type?: 'json' | 'form'
}

export interface WebhookCreateRequest extends WebhookConfig {}
export interface WebhookUpdateRequest extends Partial<WebhookConfig> {}

export interface WebhookListResponse {
  webhooks: Webhook[]
}

export interface Webhook extends WebhookConfig {
  id: string
  created_at: string
  updated_at: string
  last_delivery?: string
  deliveries_count: number
}

// Error types
export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
  field_errors?: Record<string, string[]>
}

export interface ValidationError extends ApiError {
  field_errors: Record<string, string[]>
}