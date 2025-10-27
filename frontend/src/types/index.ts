// Common types
export interface BaseEntity {
  id: string
  created_at: string
  updated_at?: string
}

export interface PaginationParams {
  page?: number
  size?: number
  limit?: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// User types
export interface User extends BaseEntity {
  email: string
  username: string
  full_name: string
  role: UserRole
  is_active: boolean
  last_login?: string
  permissions: string[]
}

export type UserRole = 'admin' | 'security_analyst' | 'operator' | 'viewer'

export interface UserCreate {
  email: string
  username: string
  full_name: string
  password: string
  role: UserRole
  is_active?: boolean
}

export interface UserUpdate {
  email?: string
  username?: string
  full_name?: string
  password?: string
  role?: UserRole
  is_active?: boolean
}

// Asset types
export interface Asset extends BaseEntity {
  name: string
  type: AssetType
  value: string
  description?: string
  priority: Priority
  status: AssetStatus
  tags: string[]
  metadata?: Record<string, any>
  last_scan?: string
  vulnerability_count: number
  ports?: PortInfo[]
  technologies?: string[]
  location?: string
  owner?: string
  criticality_level?: string
}

export type AssetType = 'domain' | 'subdomain' | 'ip' | 'cidr' | 'url' | 'service' | 'application'
export type AssetStatus = 'active' | 'inactive' | 'unknown' | 'archived'
export type Priority = 'low' | 'medium' | 'high' | 'critical'

export interface AssetCreate {
  name: string
  type: AssetType
  value: string
  description?: string
  priority: Priority
  tags?: string[]
  metadata?: Record<string, any>
}

export interface AssetUpdate {
  name?: string
  type?: AssetType
  value?: string
  description?: string
  priority?: Priority
  tags?: string[]
  metadata?: Record<string, any>
}

export interface PortInfo {
  port: number
  protocol: string
  state: string
  service?: string
  version?: string
  banner?: string
}

// Task types
export interface Task extends BaseEntity {
  name: string
  type: TaskType
  description?: string
  status: TaskStatus
  priority: Priority
  progress: number
  target_assets: string[]
  config: TaskConfig
  results?: TaskResults
  scheduled_at?: string
  started_at?: string
  completed_at?: string
  error_message?: string
  duration?: number
  created_by: string
  current_step?: string
}

export type TaskType = 'port_scan' | 'vulnerability_scan' | 'web_discovery' | 'subdomain_enum' | 'comprehensive'
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'stopped' | 'cancelled'

export interface TaskConfig {
  timeout?: number
  max_threads?: number
  rate_limit?: number
  ports?: string
  scan_speed?: number
  deep_scan?: boolean
  custom_options?: Record<string, any>
}

export interface TaskResults {
  summary?: string
  findings_count: number
  vulnerabilities_found: number
  assets_scanned: number
  execution_time: number
  output_files?: string[]
  detailed_results?: any[]
}

export interface TaskCreate {
  name: string
  type: TaskType
  description?: string
  priority: Priority
  target_assets: string[]
  config?: TaskConfig
  scheduled_at?: string
}

export interface TaskUpdate {
  name?: string
  description?: string
  priority?: Priority
  target_assets?: string[]
  config?: TaskConfig
  scheduled_at?: string
}

// Vulnerability types
export interface Vulnerability extends BaseEntity {
  name: string
  description: string
  severity: VulnerabilitySeverity
  cvss_score?: number
  cve_id?: string
  status: VulnerabilityStatus
  asset_id?: string
  asset_name?: string
  affected_assets?: string[]
  first_discovered: string
  last_seen: string
  verified: boolean
  verified_at?: string
  fixed_at?: string
  closed_at?: string
  false_positive: boolean
  tags: string[]
  details?: VulnerabilityDetails
  proof_of_concept?: string
  reproduction_steps?: string[]
  remediation?: string
  references?: VulnerabilityReference[]
  patch_available?: boolean
  vendor_response?: string
  risk_score?: number
  business_impact?: string
  technical_impact?: string
  exploitability?: string
}

export type VulnerabilitySeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type VulnerabilityStatus = 'open' | 'verified' | 'fixed' | 'closed' | 'duplicate' | 'false_positive'

export interface VulnerabilityDetails {
  location?: string
  parameter?: string
  method?: string
  port?: number
  protocol?: string
  service?: string
  payload?: string
  response?: string
  evidence?: string
}

export interface VulnerabilityReference {
  title?: string
  url: string
  type?: string
}

export interface VulnerabilityCreate {
  name: string
  description: string
  severity: VulnerabilitySeverity
  cvss_score?: number
  cve_id?: string
  asset_id?: string
  tags?: string[]
  details?: VulnerabilityDetails
  proof_of_concept?: string
  reproduction_steps?: string[]
  remediation?: string
  references?: VulnerabilityReference[]
}

export interface VulnerabilityUpdate {
  name?: string
  description?: string
  severity?: VulnerabilitySeverity
  cvss_score?: number
  cve_id?: string
  status?: VulnerabilityStatus
  verified?: boolean
  false_positive?: boolean
  tags?: string[]
  details?: VulnerabilityDetails
  proof_of_concept?: string
  reproduction_steps?: string[]
  remediation?: string
  references?: VulnerabilityReference[]
}

// Report types
export interface Report extends BaseEntity {
  title: string
  type: ReportType
  description?: string
  status: ReportStatus
  format: string[]
  classification: ReportClassification
  config: ReportConfig
  statistics?: ReportStatistics
  files?: ReportFile[]
  generated_at?: string
  file_size?: number
  generation_time?: number
  view_count: number
  download_count: number
  share_count: number
  last_accessed?: string
  created_by: string
  language: string
  template: string
  scheduled?: boolean
  schedule_config?: ScheduleConfig
}

export type ReportType = 'vulnerability' | 'asset' | 'scan' | 'comprehensive' | 'compliance' | 'trend'
export type ReportStatus = 'draft' | 'generating' | 'completed' | 'failed' | 'scheduled'
export type ReportClassification = 'public' | 'internal' | 'confidential' | 'secret'

export interface ReportConfig {
  period?: string
  date_range?: [string, string]
  include_assets?: boolean
  selected_assets?: string[]
  include_vulnerabilities?: boolean
  vulnerability_filters?: {
    severities?: VulnerabilitySeverity[]
    statuses?: VulnerabilityStatus[]
    tags?: string[]
  }
  include_tasks?: boolean
  task_filters?: {
    types?: TaskType[]
    statuses?: TaskStatus[]
  }
  sections: string[]
  include_charts?: boolean
  chart_types?: string[]
  formats: string[]
  auto_send?: boolean
  recipients?: string[]
}

export interface ReportStatistics {
  total_pages: number
  findings_count: number
  assets_count: number
  vulnerabilities_count: number
  tasks_count: number
  critical_issues: number
  high_issues: number
  medium_issues: number
  low_issues: number
}

export interface ReportFile {
  id: string
  name: string
  format: string
  size: number
  url: string
  created_at: string
}

export interface ScheduleConfig {
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly'
  time: string
  day_of_week?: number
  day_of_month?: number
  timezone: string
  enabled: boolean
}

export interface ReportCreate {
  title: string
  type: ReportType
  description?: string
  classification: ReportClassification
  config: ReportConfig
  language?: string
  template?: string
  scheduled?: boolean
  schedule_config?: ScheduleConfig
}

export interface ReportUpdate {
  title?: string
  type?: ReportType
  description?: string
  classification?: ReportClassification
  config?: ReportConfig
  language?: string
  template?: string
}

// Settings types
export interface SystemSettings {
  general: GeneralSettings
  security: SecuritySettings
  notifications: NotificationSettings
  scanning: ScanningSettings
  integrations: IntegrationSettings
  system: SystemConfig
}

export interface GeneralSettings {
  platform_name: string
  platform_description: string
  default_language: string
  timezone: string
  default_page_size: number
}

export interface SecuritySettings {
  min_password_length: number
  password_requirements: string[]
  password_expiry_days: number
  session_timeout: number
  max_concurrent_sessions: number
  enable_login_lockout: boolean
  login_failure_threshold: number
  lockout_duration: number
  enable_two_factor: boolean
}

export interface NotificationSettings {
  email_enabled: boolean
  smtp_host: string
  smtp_port: number
  sender_email: string
  sender_password: string
  smtp_tls: boolean
  new_vulnerability_notification: string[]
  task_completed_notification: string[]
  system_alert_notification: string[]
}

export interface ScanningSettings {
  max_concurrent_tasks: number
  default_timeout: number
  max_retries: number
  nmap_path: string
  nuclei_path: string
  xray_path: string
  auto_cleanup: boolean
  cleanup_days: number
  enable_proxy: boolean
  proxy_url: string
}

export interface IntegrationSettings {
  fofa_enabled: boolean
  fofa_api_key: string
  fofa_email: string
  slack_enabled: boolean
  slack_webhook_url: string
  slack_channel: string
  webhook_enabled: boolean
  webhook_url: string
  webhook_token: string
}

export interface SystemConfig {
  db_pool_size: number
  db_query_timeout: number
  cache_enabled: boolean
  cache_ttl: number
  log_level: string
  log_retention_days: number
  worker_processes: number
  rate_limit_rpm: number
}

// System monitoring types
export interface SystemInfo {
  version: string
  uptime: number
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  active_users: number
  active_tasks: number
  database_status: string
  cache_status: string
}

export interface SystemMetrics {
  timestamp: string
  cpu_percent: number
  memory_percent: number
  disk_percent: number
  network_io: {
    bytes_sent: number
    bytes_recv: number
  }
  active_connections: number
}

export interface SystemAlert {
  id: string
  title: string
  message: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  resolved: boolean
  component: string
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  version: string
  components: Record<string, {
    status: string
    response_time?: string
    error?: string
    [key: string]: any
  }>
}

// Dashboard types
export interface DashboardStats {
  overview: {
    total_assets: number
    total_vulnerabilities: number
    active_tasks: number
    generated_reports: number
  }
  security_status: {
    critical_vulnerabilities: number
    high_vulnerabilities: number
    medium_vulnerabilities: number
    low_vulnerabilities: number
  }
  task_status: {
    pending: number
    running: number
    completed: number
    failed: number
  }
  recent_activities: Activity[]
  system_health: {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_status: string
  }
}

export interface Activity {
  type: string
  message: string
  timestamp: string
  user?: string
  entity_id?: string
  entity_type?: string
}

// Chart data types
export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
}

// Form types
export interface FormRule {
  required?: boolean
  message?: string
  trigger?: string | string[]
  min?: number
  max?: number
  type?: string
  validator?: (rule: any, value: any, callback: any) => void
}

export interface FormRules {
  [key: string]: FormRule[]
}

// Filter types
export interface AssetFilters {
  type?: AssetType
  status?: AssetStatus
  priority?: Priority
  tags?: string[]
  search?: string
  owner?: string
  created_after?: string
  created_before?: string
}

export interface VulnerabilityFilters {
  severity?: VulnerabilitySeverity[]
  status?: VulnerabilityStatus[]
  asset_id?: string
  tags?: string[]
  search?: string
  verified?: boolean
  false_positive?: boolean
  discovered_after?: string
  discovered_before?: string
}

export interface TaskFilters {
  type?: TaskType[]
  status?: TaskStatus[]
  priority?: Priority[]
  created_by?: string
  search?: string
  created_after?: string
  created_before?: string
}

export interface ReportFilters {
  type?: ReportType[]
  status?: ReportStatus[]
  classification?: ReportClassification[]
  created_by?: string
  search?: string
  created_after?: string
  created_before?: string
}

export interface UserFilters {
  role?: UserRole[]
  is_active?: boolean
  search?: string
  created_after?: string
  created_before?: string
}

// Export types
export interface ExportOptions {
  format: 'json' | 'csv' | 'xlsx' | 'pdf'
  filters?: any
  fields?: string[]
  include_related?: boolean
}

// Import types
export interface ImportResult {
  total: number
  success: number
  failed: number
  errors?: string[]
  warnings?: string[]
}

// Navigation types
export interface MenuItem {
  title: string
  path: string
  icon?: string
  children?: MenuItem[]
  permission?: string
  badge?: string | number
}

// Theme types
export interface ThemeConfig {
  primary: string
  success: string
  warning: string
  danger: string
  info: string
  dark: boolean
}

// Notification types
export interface Notification {
  id: string
  title: string
  message: string
  type: 'success' | 'warning' | 'error' | 'info'
  timestamp: string
  read: boolean
  action?: {
    text: string
    url: string
  }
}