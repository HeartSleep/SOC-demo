<template>
  <div class="monitoring-dashboard">
    <el-card class="header-card">
      <h1>🎯 API Integration Monitor</h1>
      <p>Real-time monitoring of frontend-backend integration</p>
    </el-card>

    <!-- Connection Status -->
    <el-row :gutter="20" class="status-row">
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <el-badge :is-dot="true" :type="apiStatus.connected ? 'success' : 'danger'">
              <span class="status-label">API Status</span>
            </el-badge>
            <div class="status-value">{{ apiStatus.connected ? 'Connected' : 'Disconnected' }}</div>
            <div class="status-detail">{{ apiStatus.latency }}ms latency</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <el-badge :is-dot="true" :type="wsStatus.connected ? 'success' : 'warning'">
              <span class="status-label">WebSocket</span>
            </el-badge>
            <div class="status-value">{{ wsStatus.connected ? 'Connected' : 'Disconnected' }}</div>
            <div class="status-detail">{{ wsStatus.reconnectAttempts }} reconnects</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <span class="status-label">Requests/min</span>
            <div class="status-value">{{ metrics.requestsPerMinute }}</div>
            <div class="status-detail">
              <el-tag :type="metrics.errorRate > 5 ? 'danger' : 'success'" size="small">
                {{ metrics.errorRate }}% errors
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <span class="status-label">Avg Response</span>
            <div class="status-value">{{ metrics.avgResponseTime }}ms</div>
            <div class="status-detail">
              <el-progress
                :percentage="Math.min(100, (metrics.avgResponseTime / 1000) * 100)"
                :color="getResponseTimeColor(metrics.avgResponseTime)"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- API Endpoints Health -->
    <el-card class="endpoints-card">
      <template #header>
        <div class="card-header">
          <span>API Endpoints Health</span>
          <el-button size="small" @click="testAllEndpoints">Test All</el-button>
        </div>
      </template>

      <el-table :data="endpoints" style="width: 100%">
        <el-table-column prop="name" label="Endpoint" width="200" />
        <el-table-column prop="path" label="Path" />
        <el-table-column prop="method" label="Method" width="80">
          <template #default="{ row }">
            <el-tag :type="getMethodType(row.method)" size="small">
              {{ row.method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status || 'Not Tested' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="responseTime" label="Response Time" width="120">
          <template #default="{ row }">
            <span v-if="row.responseTime">{{ row.responseTime }}ms</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="lastTested" label="Last Tested" width="180">
          <template #default="{ row }">
            {{ row.lastTested ? formatTime(row.lastTested) : 'Never' }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="testEndpoint(row)">Test</el-button>
            <el-button size="small" type="primary" @click="showDetails(row)">Details</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Request History -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>Recent Requests</span>
          <el-button size="small" @click="clearHistory">Clear</el-button>
        </div>
      </template>

      <el-timeline>
        <el-timeline-item
          v-for="request in requestHistory"
          :key="request.id"
          :timestamp="formatTime(request.timestamp)"
          :type="request.success ? 'success' : 'danger'"
          placement="top"
        >
          <el-card>
            <div class="request-item">
              <div class="request-header">
                <el-tag :type="getMethodType(request.method)" size="small">
                  {{ request.method }}
                </el-tag>
                <span class="request-path">{{ request.path }}</span>
                <el-tag :type="request.success ? 'success' : 'danger'" size="small">
                  {{ request.status }}
                </el-tag>
              </div>
              <div class="request-details">
                <span>Response: {{ request.responseTime }}ms</span>
                <span v-if="request.error" class="error-message">{{ request.error }}</span>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- WebSocket Messages -->
    <el-card class="websocket-card">
      <template #header>
        <div class="card-header">
          <span>WebSocket Messages</span>
          <el-button size="small" @click="connectWebSocket" v-if="!wsStatus.connected">
            Connect
          </el-button>
          <el-button size="small" type="danger" @click="disconnectWebSocket" v-else>
            Disconnect
          </el-button>
        </div>
      </template>

      <div class="websocket-messages">
        <div v-for="msg in wsMessages" :key="msg.id" class="ws-message">
          <el-tag :type="msg.direction === 'sent' ? 'primary' : 'success'" size="small">
            {{ msg.direction }}
          </el-tag>
          <span class="ws-time">{{ formatTime(msg.timestamp) }}</span>
          <pre class="ws-data">{{ JSON.stringify(msg.data, null, 2) }}</pre>
        </div>
      </div>
    </el-card>

    <!-- Test Results Dialog -->
    <el-dialog v-model="showTestResults" title="Endpoint Test Results" width="60%">
      <div v-if="currentTestResult">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="Endpoint">{{ currentTestResult.name }}</el-descriptions-item>
          <el-descriptions-item label="Path">{{ currentTestResult.path }}</el-descriptions-item>
          <el-descriptions-item label="Method">{{ currentTestResult.method }}</el-descriptions-item>
          <el-descriptions-item label="Status">
            <el-tag :type="getStatusType(currentTestResult.status)">
              {{ currentTestResult.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Response Time">
            {{ currentTestResult.responseTime }}ms
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <div class="test-result-section">
          <h4>Request Headers</h4>
          <pre>{{ JSON.stringify(currentTestResult.requestHeaders, null, 2) }}</pre>
        </div>

        <div class="test-result-section" v-if="currentTestResult.requestBody">
          <h4>Request Body</h4>
          <pre>{{ JSON.stringify(currentTestResult.requestBody, null, 2) }}</pre>
        </div>

        <div class="test-result-section">
          <h4>Response Headers</h4>
          <pre>{{ JSON.stringify(currentTestResult.responseHeaders, null, 2) }}</pre>
        </div>

        <div class="test-result-section">
          <h4>Response Body</h4>
          <pre>{{ JSON.stringify(currentTestResult.responseBody, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// State
const apiStatus = ref({
  connected: false,
  latency: 0,
  lastCheck: null
})

const wsStatus = ref({
  connected: false,
  reconnectAttempts: 0
})

const metrics = ref({
  requestsPerMinute: 0,
  errorRate: 0,
  avgResponseTime: 0,
  totalRequests: 0,
  failedRequests: 0
})

const endpoints = ref([
  { name: 'Authentication', path: '/api/v1/auth/login', method: 'POST', status: null, responseTime: null, lastTested: null },
  { name: 'Get Current User', path: '/api/v1/auth/me', method: 'GET', status: null, responseTime: null, lastTested: null },
  { name: 'List Assets', path: '/api/v1/assets/', method: 'GET', status: null, responseTime: null, lastTested: null },
  { name: 'Create Asset', path: '/api/v1/assets/', method: 'POST', status: null, responseTime: null, lastTested: null },
  { name: 'List Users', path: '/api/v1/users/', method: 'GET', status: null, responseTime: null, lastTested: null },
  { name: 'List Tasks', path: '/api/v1/tasks/', method: 'GET', status: null, responseTime: null, lastTested: null },
  { name: 'Health Check', path: '/health', method: 'GET', status: null, responseTime: null, lastTested: null },
  { name: 'WebSocket', path: '/api/v1/ws/{user_id}', method: 'WS', status: null, responseTime: null, lastTested: null }
])

const requestHistory = ref([])
const wsMessages = ref([])
const showTestResults = ref(false)
const currentTestResult = ref(null)

let ws = null
let healthCheckInterval = null
let metricsInterval = null

// Methods
const checkApiHealth = async () => {
  const start = Date.now()
  try {
    const response = await axios.get('/health')
    const latency = Date.now() - start

    apiStatus.value = {
      connected: true,
      latency,
      lastCheck: new Date()
    }
  } catch (error) {
    apiStatus.value = {
      connected: false,
      latency: 0,
      lastCheck: new Date()
    }
  }
}

const connectWebSocket = () => {
  const token = localStorage.getItem('token')
  const userId = 'test-user'

  ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${userId}?token=${token}`)

  ws.onopen = () => {
    wsStatus.value.connected = true
    ElMessage.success('WebSocket connected')

    // Send ping
    ws.send(JSON.stringify({ type: 'ping' }))
    recordWsMessage('sent', { type: 'ping' })
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    recordWsMessage('received', data)
  }

  ws.onclose = () => {
    wsStatus.value.connected = false
    wsStatus.value.reconnectAttempts++
    ElMessage.warning('WebSocket disconnected')
  }

  ws.onerror = (error) => {
    ElMessage.error('WebSocket error')
    console.error('WebSocket error:', error)
  }
}

const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}

const testEndpoint = async (endpoint) => {
  const start = Date.now()

  try {
    let response
    const token = localStorage.getItem('token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}

    if (endpoint.method === 'GET') {
      response = await axios.get(endpoint.path, { headers })
    } else if (endpoint.method === 'POST') {
      // Use test data for POST endpoints
      const testData = getTestDataForEndpoint(endpoint.path)
      response = await axios.post(endpoint.path, testData, { headers })
    } else if (endpoint.method === 'WS') {
      // Test WebSocket connection
      connectWebSocket()
      endpoint.status = wsStatus.value.connected ? 200 : 0
      endpoint.responseTime = 0
      endpoint.lastTested = new Date()
      return
    }

    const responseTime = Date.now() - start

    endpoint.status = response.status
    endpoint.responseTime = responseTime
    endpoint.lastTested = new Date()

    // Record in history
    recordRequest({
      method: endpoint.method,
      path: endpoint.path,
      status: response.status,
      responseTime,
      success: true
    })

    // Store detailed result
    currentTestResult.value = {
      ...endpoint,
      requestHeaders: headers,
      requestBody: endpoint.method === 'POST' ? getTestDataForEndpoint(endpoint.path) : null,
      responseHeaders: response.headers,
      responseBody: response.data
    }

    ElMessage.success(`${endpoint.name} test successful`)

  } catch (error) {
    const responseTime = Date.now() - start

    endpoint.status = error.response?.status || 0
    endpoint.responseTime = responseTime
    endpoint.lastTested = new Date()

    // Record in history
    recordRequest({
      method: endpoint.method,
      path: endpoint.path,
      status: error.response?.status || 0,
      responseTime,
      success: false,
      error: error.message
    })

    ElMessage.error(`${endpoint.name} test failed: ${error.message}`)
  }
}

const testAllEndpoints = async () => {
  ElMessage.info('Testing all endpoints...')

  for (const endpoint of endpoints.value) {
    if (endpoint.method !== 'WS') {
      await testEndpoint(endpoint)
      await new Promise(resolve => setTimeout(resolve, 500)) // Delay between tests
    }
  }

  ElMessage.success('All endpoint tests completed')
}

const recordRequest = (request) => {
  requestHistory.value.unshift({
    id: Date.now(),
    timestamp: new Date(),
    ...request
  })

  // Keep only last 20 requests
  if (requestHistory.value.length > 20) {
    requestHistory.value.pop()
  }

  // Update metrics
  updateMetrics(request)
}

const recordWsMessage = (direction, data) => {
  wsMessages.value.unshift({
    id: Date.now(),
    timestamp: new Date(),
    direction,
    data
  })

  // Keep only last 10 messages
  if (wsMessages.value.length > 10) {
    wsMessages.value.pop()
  }
}

const updateMetrics = (request) => {
  metrics.value.totalRequests++

  if (!request.success) {
    metrics.value.failedRequests++
  }

  // Calculate error rate
  metrics.value.errorRate = Math.round(
    (metrics.value.failedRequests / metrics.value.totalRequests) * 100
  )

  // Update average response time (simple moving average)
  metrics.value.avgResponseTime = Math.round(
    (metrics.value.avgResponseTime * (metrics.value.totalRequests - 1) + request.responseTime) /
    metrics.value.totalRequests
  )
}

const clearHistory = () => {
  requestHistory.value = []
  ElMessage.success('History cleared')
}

const showDetails = (endpoint) => {
  if (endpoint.lastTested) {
    showTestResults.value = true
  } else {
    ElMessage.warning('Please test this endpoint first')
  }
}

const getTestDataForEndpoint = (path) => {
  if (path.includes('auth/login')) {
    return { username: 'admin', password: 'admin' }
  } else if (path.includes('assets')) {
    return {
      name: 'test-asset.com',
      asset_type: 'domain',
      domain: 'test-asset.com'
    }
  }
  return {}
}

// Utility functions
const formatTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleTimeString()
}

const getMethodType = (method) => {
  const types = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger',
    WS: 'info'
  }
  return types[method] || 'info'
}

const getStatusType = (status) => {
  if (!status) return 'info'
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'warning'
  if (status >= 400 && status < 500) return 'warning'
  if (status >= 500) return 'danger'
  return 'danger'
}

const getResponseTimeColor = (time) => {
  if (time < 200) return '#67C23A' // Green
  if (time < 500) return '#E6A23C' // Orange
  return '#F56C6C' // Red
}

// Calculate requests per minute
const calculateRequestsPerMinute = () => {
  const oneMinuteAgo = new Date(Date.now() - 60000)
  const recentRequests = requestHistory.value.filter(
    r => r.timestamp > oneMinuteAgo
  )
  metrics.value.requestsPerMinute = recentRequests.length
}

// Lifecycle
onMounted(() => {
  // Initial health check
  checkApiHealth()

  // Set up intervals
  healthCheckInterval = setInterval(checkApiHealth, 10000) // Every 10 seconds
  metricsInterval = setInterval(calculateRequestsPerMinute, 5000) // Every 5 seconds
})

onUnmounted(() => {
  if (healthCheckInterval) clearInterval(healthCheckInterval)
  if (metricsInterval) clearInterval(metricsInterval)
  disconnectWebSocket()
})
</script>

<style scoped lang="scss">
.monitoring-dashboard {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;

  .header-card {
    margin-bottom: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;

    h1 {
      margin: 0 0 10px 0;
      font-size: 28px;
    }

    p {
      margin: 0;
      opacity: 0.9;
    }
  }

  .status-row {
    margin-bottom: 20px;
  }

  .status-card {
    .status-item {
      text-align: center;
      padding: 10px;

      .status-label {
        font-size: 14px;
        color: #606266;
        display: block;
        margin-bottom: 10px;
      }

      .status-value {
        font-size: 24px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 10px;
      }

      .status-detail {
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .endpoints-card,
  .history-card,
  .websocket-card {
    margin-bottom: 20px;
  }

  .request-item {
    .request-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;

      .request-path {
        flex: 1;
        font-family: monospace;
        font-size: 14px;
      }
    }

    .request-details {
      font-size: 12px;
      color: #909399;
      display: flex;
      gap: 20px;

      .error-message {
        color: #f56c6c;
      }
    }
  }

  .websocket-messages {
    max-height: 400px;
    overflow-y: auto;

    .ws-message {
      margin-bottom: 15px;
      padding: 10px;
      background: #f5f7fa;
      border-radius: 4px;

      .ws-time {
        margin-left: 10px;
        font-size: 12px;
        color: #909399;
      }

      .ws-data {
        margin-top: 10px;
        padding: 10px;
        background: white;
        border-radius: 4px;
        font-size: 12px;
        overflow-x: auto;
      }
    }
  }

  .test-result-section {
    margin-bottom: 20px;

    h4 {
      margin-bottom: 10px;
      color: #303133;
    }

    pre {
      background: #f5f7fa;
      padding: 15px;
      border-radius: 4px;
      overflow-x: auto;
      font-size: 12px;
    }
  }
}
</style>