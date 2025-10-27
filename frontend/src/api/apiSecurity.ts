import request from '@/utils/request'

// API扫描任务接口

export interface APIScanConfig {
  enable_js_extraction?: boolean
  enable_api_discovery?: boolean
  enable_microservice_detection?: boolean
  enable_unauthorized_check?: boolean
  enable_sensitive_info_check?: boolean
  use_ai?: boolean
  timeout?: number
  max_js_files?: number
  max_apis?: number
}

export interface APIScanTask {
  id: string
  name: string
  target_url: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  scan_config: Record<string, any>
  total_js_files: number
  total_apis: number
  total_services: number
  total_issues: number
  critical_issues: number
  high_issues: number
  medium_issues: number
  low_issues: number
  progress: number
  current_phase?: string
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  error_message?: string
  created_at: string
  updated_at: string
  created_by: string
}

export interface JSResource {
  id: string
  scan_task_id: string
  url: string
  base_url?: string
  file_name?: string
  file_size?: number
  extraction_method?: string
  has_apis: boolean
  has_base_api_path: boolean
  has_sensitive_info: boolean
  extracted_apis: string[]
  extracted_base_paths: string[]
  discovered_at: string
}

export interface APIEndpoint {
  id: string
  scan_task_id: string
  base_url: string
  base_api_path?: string
  service_path?: string
  api_path: string
  full_url: string
  http_method: string
  status_code?: number
  response_time?: number
  discovery_method?: string
  is_public_api?: boolean
  requires_auth?: boolean
  is_404: boolean
  discovered_at: string
}

export interface MicroserviceInfo {
  id: string
  scan_task_id: string
  base_url: string
  service_name: string
  service_full_path: string
  total_endpoints: number
  unique_paths: string[]
  detected_technologies: string[]
  has_vulnerabilities: boolean
  vulnerability_details: any[]
  discovered_at: string
}

export interface APISecurityIssue {
  id: string
  scan_task_id: string
  title: string
  description: string
  issue_type: 'unauthorized_access' | 'sensitive_data_leak' | 'component_vulnerability' | 'weak_authentication' | 'other'
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  target_url: string
  target_api?: string
  evidence: Record<string, any>
  ai_verified: boolean
  remediation?: string
  is_verified: boolean
  is_false_positive: boolean
  is_resolved: boolean
  discovered_at: string
  created_at: string
}

export interface APIScanStatistics {
  total_scans: number
  completed_scans: number
  running_scans: number
  failed_scans: number
  total_apis_discovered: number
  total_js_files: number
  total_microservices: number
  total_issues: number
  critical_issues: number
  high_issues: number
  medium_issues: number
  low_issues: number
  issues_by_type: Record<string, number>
}

// API函数

/**
 * 创建API扫描任务
 */
export function createAPIScanTask(data: {
  name: string
  target_url: string
  scan_config?: APIScanConfig
}) {
  return request<APIScanTask>({
    url: '/api/v1/api-security/scans',
    method: 'post',
    data
  })
}

/**
 * 获取扫描任务列表
 */
export function getAPIScanTasks(params?: {
  status?: string
  skip?: number
  limit?: number
}) {
  return request<APIScanTask[]>({
    url: '/api/v1/api-security/scans',
    method: 'get',
    params
  })
}

/**
 * 获取扫描任务详情
 */
export function getAPIScanTask(scanId: string) {
  return request<APIScanTask>({
    url: `/api/v1/api-security/scans/${scanId}`,
    method: 'get'
  })
}

/**
 * 更新扫描任务
 */
export function updateAPIScanTask(scanId: string, data: Partial<APIScanTask>) {
  return request<APIScanTask>({
    url: `/api/v1/api-security/scans/${scanId}`,
    method: 'patch',
    data
  })
}

/**
 * 删除扫描任务
 */
export function deleteAPIScanTask(scanId: string) {
  return request({
    url: `/api/v1/api-security/scans/${scanId}`,
    method: 'delete'
  })
}

/**
 * 获取JS资源列表
 */
export function getJSResources(scanId: string, params?: {
  skip?: number
  limit?: number
}) {
  return request<JSResource[]>({
    url: `/api/v1/api-security/scans/${scanId}/js-resources`,
    method: 'get',
    params
  })
}

/**
 * 获取API接口列表
 */
export function getAPIEndpoints(scanId: string, params?: {
  service_path?: string
  skip?: number
  limit?: number
}) {
  return request<APIEndpoint[]>({
    url: `/api/v1/api-security/scans/${scanId}/apis`,
    method: 'get',
    params
  })
}

/**
 * 获取微服务列表
 */
export function getMicroservices(scanId: string) {
  return request<MicroserviceInfo[]>({
    url: `/api/v1/api-security/scans/${scanId}/microservices`,
    method: 'get'
  })
}

/**
 * 获取安全问题列表
 */
export function getSecurityIssues(scanId: string, params?: {
  issue_type?: string
  severity?: string
  is_verified?: boolean
  skip?: number
  limit?: number
}) {
  return request<APISecurityIssue[]>({
    url: `/api/v1/api-security/scans/${scanId}/issues`,
    method: 'get',
    params
  })
}

/**
 * 更新安全问题
 */
export function updateSecurityIssue(issueId: string, data: {
  is_verified?: boolean
  is_false_positive?: boolean
  verification_notes?: string
  is_resolved?: boolean
}) {
  return request<APISecurityIssue>({
    url: `/api/v1/api-security/issues/${issueId}`,
    method: 'patch',
    data
  })
}

/**
 * 获取统计信息
 */
export function getAPIScanStatistics() {
  return request<APIScanStatistics>({
    url: '/api/v1/api-security/statistics',
    method: 'get'
  })
}
