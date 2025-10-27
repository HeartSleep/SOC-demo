/**
 * GraphQL Queries for SOC Platform
 */

import { gql } from '@apollo/client'

// User Queries
export const GET_CURRENT_USER = gql`
  query GetCurrentUser {
    me {
      id
      username
      email
      fullName
      role
      isActive
      permissions
      lastLogin
      activityCount(days: 7)
    }
  }
`

export const GET_USER = gql`
  query GetUser($id: String!) {
    user(id: $id) {
      id
      username
      email
      fullName
      role
      isActive
      createdAt
      lastLogin
      permissions
      tasks {
        id
        name
        status
        priority
      }
      activityCount(days: 30)
    }
  }
`

export const GET_USERS = gql`
  query GetUsers($first: Int = 20, $after: String, $role: String, $isActive: Boolean) {
    users(first: $first, after: $after, role: $role, isActive: $isActive) {
      edges {
        id
        username
        email
        fullName
        role
        isActive
        lastLogin
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
      totalCount
    }
  }
`

// Asset Queries
export const GET_ASSET = gql`
  query GetAsset($id: String!) {
    asset(id: $id) {
      id
      name
      assetType
      status
      ipAddress
      domain
      tags
      criticality
      organization
      owner
      createdAt
      updatedAt
      lastScan
      vulnerabilities(limit: 10) {
        id
        title
        severity
        status
        cvssScore
      }
      riskScore
      scanHistory(limit: 5) {
        id
        scanType
        status
        startedAt
        completedAt
        findingsCount
      }
    }
  }
`

export const GET_ASSETS = gql`
  query GetAssets(
    $first: Int = 20
    $after: String
    $assetType: AssetType
    $criticality: Severity
    $tags: [String]
    $search: String
  ) {
    assets(
      first: $first
      after: $after
      assetType: $assetType
      criticality: $criticality
      tags: $tags
      search: $search
    ) {
      edges {
        id
        name
        assetType
        status
        ipAddress
        domain
        tags
        criticality
        owner
        lastScan
        riskScore
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
      totalCount
    }
  }
`

// Vulnerability Queries
export const GET_VULNERABILITIES = gql`
  query GetVulnerabilities(
    $assetId: String
    $severity: Severity
    $status: String
    $limit: Int = 50
  ) {
    vulnerabilities(
      assetId: $assetId
      severity: $severity
      status: $status
      limit: $limit
    ) {
      id
      title
      description
      severity
      status
      assetId
      cvssScore
      cveId
      discoveredAt
      updatedAt
      resolvedAt
      asset {
        id
        name
        assetType
      }
      remediation
    }
  }
`

// Task Queries
export const GET_TASKS = gql`
  query GetTasks(
    $assignedTo: String
    $status: TaskStatus
    $priority: Severity
    $limit: Int = 20
  ) {
    tasks(
      assignedTo: $assignedTo
      status: $status
      priority: $priority
      limit: $limit
    ) {
      id
      name
      type
      status
      priority
      assignedTo
      progress
      createdAt
      updatedAt
      eta
      assignedUser {
        id
        username
        fullName
      }
    }
  }
`

// Dashboard Queries
export const GET_DASHBOARD_STATS = gql`
  query GetDashboardStats {
    dashboardStats {
      totalAssets
      activeVulnerabilities
      criticalVulnerabilities
      tasksInProgress
      recentScans
      complianceScore
      riskScore
    }
    systemMetrics {
      uptimeSeconds
      totalRequests
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

// Search Query
export const GLOBAL_SEARCH = gql`
  query GlobalSearch($query: String!, $types: [String], $limit: Int = 10) {
    search(query: $query, types: $types, limit: $limit) {
      ... on User {
        __typename
        id
        username
        email
        fullName
      }
      ... on Asset {
        __typename
        id
        name
        assetType
        criticality
      }
      ... on Vulnerability {
        __typename
        id
        title
        severity
        status
      }
      ... on Task {
        __typename
        id
        name
        status
        priority
      }
    }
  }
`

// Notification Query
export const GET_NOTIFICATIONS = gql`
  query GetNotifications($unreadOnly: Boolean = false, $limit: Int = 20) {
    notifications(unreadOnly: $unreadOnly, limit: $limit) {
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

// System Metrics Query
export const GET_SYSTEM_METRICS = gql`
  query GetSystemMetrics {
    systemMetrics {
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