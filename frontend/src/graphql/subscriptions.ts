/**
 * GraphQL Subscriptions for SOC Platform
 * Real-time updates via WebSocket
 */

import { gql } from '@apollo/client'

// System Metrics Subscription
export const SYSTEM_METRICS_STREAM = gql`
  subscription SystemMetricsStream {
    systemMetricsStream {
      uptimeSeconds
      totalRequests
      failedRequests
      errorRate
      requestsPerMinute
      avgResponseTimeMs
      activeUsers
      cpuUsage
      memoryUsageMb
      diskUsagePercent
      timestamp
    }
  }
`

// Task Updates Subscription
export const TASK_UPDATES = gql`
  subscription TaskUpdates($taskId: String) {
    taskUpdates(taskId: $taskId) {
      id
      name
      type
      status
      priority
      assignedTo
      progress
      updatedAt
      eta
      assignedUser {
        id
        username
        fullName
      }
      logs(limit: 5)
    }
  }
`

// Vulnerability Alerts Subscription
export const VULNERABILITY_ALERTS = gql`
  subscription VulnerabilityAlerts($minSeverity: Severity = MEDIUM) {
    vulnerabilityAlerts(minSeverity: $minSeverity) {
      id
      title
      description
      severity
      status
      assetId
      cvssScore
      cveId
      discoveredAt
      asset {
        id
        name
        assetType
        criticality
      }
      remediation
    }
  }
`

// Asset Changes Subscription
export const ASSET_CHANGES = gql`
  subscription AssetChanges($assetId: String) {
    assetChanges(assetId: $assetId) {
      id
      name
      assetType
      status
      ipAddress
      domain
      tags
      criticality
      owner
      updatedAt
      lastScan
      riskScore
    }
  }
`

// User Notifications Subscription
export const NOTIFICATIONS_STREAM = gql`
  subscription NotificationsStream {
    notifications {
      id
      type
      title
      message
      severity
      timestamp
      read
    }
  }
`

// Scan Progress Subscription
export const SCAN_PROGRESS = gql`
  subscription ScanProgress($scanId: String!) {
    scanProgress(scanId: $scanId) {
      id
      assetId
      scanType
      status
      startedAt
      completedAt
      findingsCount
      highSeverityCount
      mediumSeverityCount
      lowSeverityCount
    }
  }
`