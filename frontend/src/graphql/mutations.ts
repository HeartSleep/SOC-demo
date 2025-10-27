/**
 * GraphQL Mutations for SOC Platform
 */

import { gql } from '@apollo/client'

// User Mutations
export const CREATE_USER = gql`
  mutation CreateUser($input: CreateUserInput!) {
    createUser(input: $input) {
      id
      username
      email
      fullName
      role
      isActive
      permissions
    }
  }
`

export const UPDATE_USER = gql`
  mutation UpdateUser($input: UpdateUserInput!) {
    updateUser(input: $input) {
      id
      username
      email
      fullName
      role
      isActive
      permissions
    }
  }
`

export const DELETE_USER = gql`
  mutation DeleteUser($id: String!) {
    deleteUser(id: $id)
  }
`

// Asset Mutations
export const CREATE_ASSET = gql`
  mutation CreateAsset($input: CreateAssetInput!) {
    createAsset(input: $input) {
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
    }
  }
`

export const UPDATE_ASSET = gql`
  mutation UpdateAsset($input: UpdateAssetInput!) {
    updateAsset(input: $input) {
      id
      name
      assetType
      status
      tags
      criticality
      owner
      updatedAt
    }
  }
`

export const DELETE_ASSET = gql`
  mutation DeleteAsset($id: String!) {
    deleteAsset(id: $id)
  }
`

// Scan Mutations
export const SCAN_ASSET = gql`
  mutation ScanAsset($input: ScanAssetInput!) {
    scanAsset(input: $input) {
      id
      name
      type
      status
      priority
      assignedTo
      progress
      createdAt
      eta
    }
  }
`

export const TRIGGER_FULL_SCAN = gql`
  mutation TriggerFullScan {
    triggerFullScan {
      id
      name
      type
      status
      priority
      progress
      createdAt
      eta
    }
  }
`

// Task Mutations
export const CREATE_TASK = gql`
  mutation CreateTask($input: CreateTaskInput!) {
    createTask(input: $input) {
      id
      name
      type
      status
      priority
      assignedTo
      progress
      createdAt
    }
  }
`

export const UPDATE_TASK_STATUS = gql`
  mutation UpdateTaskStatus($id: String!, $status: TaskStatus!, $progress: Int) {
    updateTaskStatus(id: $id, status: $status, progress: $progress) {
      id
      status
      progress
      updatedAt
    }
  }
`

// Vulnerability Mutations
export const MARK_VULNERABILITY_RESOLVED = gql`
  mutation MarkVulnerabilityResolved($id: String!, $resolutionNotes: String) {
    markVulnerabilityResolved(id: $id, resolutionNotes: $resolutionNotes) {
      id
      status
      resolvedAt
    }
  }
`

// Notification Mutations
export const MARK_NOTIFICATION_READ = gql`
  mutation MarkNotificationRead($id: String!) {
    markNotificationRead(id: $id) {
      id
      read
    }
  }
`