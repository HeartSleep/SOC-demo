<template>
  <div class="task-detail" v-loading="loading">
    <div v-if="error" class="error-state">
      <el-empty description="任务加载失败">
        <el-button type="primary" @click="retry">重试</el-button>
        <el-button @click="$router.push('/tasks')">返回任务列表</el-button>
      </el-empty>
    </div>
    <div v-else-if="task" class="task-content">
      <!-- Header -->
      <div class="task-header">
        <div class="header-left">
          <h1>{{ task.name }}</h1>
          <div class="task-meta">
            <el-tag :type="getTypeTagType(task.type)">
              {{ getTypeLabel(task.type) }}
            </el-tag>
            <el-tag :type="getStatusTagType(task.status)">
              {{ getStatusLabel(task.status) }}
            </el-tag>
            <el-tag :type="getPriorityTagType(task.priority)">
              {{ getPriorityLabel(task.priority) }}
            </el-tag>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            v-if="task.status === 'pending' || task.status === 'stopped'"
            type="primary"
            @click="handleStart"
            :loading="actionLoading"
          >
            <el-icon><VideoPlay /></el-icon>
            开始执行
          </el-button>
          <el-button
            v-if="task.status === 'running'"
            type="warning"
            @click="handleStop"
            :loading="actionLoading"
          >
            <el-icon><VideoPause /></el-icon>
            停止执行
          </el-button>
          <el-button @click="$router.push(`/tasks/${task.id}/edit`)">
            <el-icon><Edit /></el-icon>
            编辑任务
          </el-button>
          <el-dropdown @command="handleCommand">
            <el-button>
              更多操作<el-icon><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="clone">克隆任务</el-dropdown-item>
                <el-dropdown-item command="export">导出结果</el-dropdown-item>
                <el-dropdown-item command="restart" :disabled="task.status === 'running'">重新执行</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除任务</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- Progress -->
      <el-card v-if="task.status === 'running'" class="progress-card">
        <div class="progress-info">
          <div class="progress-text">
            <span>任务进度</span>
            <span>{{ task.progress || 0 }}%</span>
          </div>
          <el-progress
            :percentage="task.progress || 0"
            :status="task.status === 'failed' ? 'exception' : undefined"
            :stroke-width="8"
          />
          <div v-if="task.current_step" class="current-step">
            当前步骤: {{ task.current_step }}
          </div>
        </div>
      </el-card>

      <!-- Overview -->
      <el-row :gutter="16" class="overview-cards">
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ task.target_assets?.length || 0 }}</div>
              <div class="stat-label">目标资产</div>
            </div>
            <el-icon class="stat-icon"><List /></el-icon>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ results.vulnerabilities_found || 0 }}</div>
              <div class="stat-label">发现漏洞</div>
            </div>
            <el-icon class="stat-icon"><Warning /></el-icon>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ formatDuration(task.duration) }}</div>
              <div class="stat-label">执行时间</div>
            </div>
            <el-icon class="stat-icon"><Clock /></el-icon>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ formatDate(task.created_at, 'relative') }}</div>
              <div class="stat-label">创建时间</div>
            </div>
            <el-icon class="stat-icon"><Calendar /></el-icon>
          </el-card>
        </el-col>
      </el-row>

      <!-- Main Content -->
      <el-row :gutter="16">
        <el-col :xs="24" :lg="16">
          <!-- Tabs -->
          <el-card>
            <el-tabs v-model="activeTab" @tab-change="handleTabChange">
              <!-- Overview -->
              <el-tab-pane label="任务概览" name="overview">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="任务名称">
                    {{ task.name }}
                  </el-descriptions-item>
                  <el-descriptions-item label="扫描类型">
                    <el-tag :type="getTypeTagType(task.type)">
                      {{ getTypeLabel(task.type) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="优先级">
                    <el-tag :type="getPriorityTagType(task.priority)">
                      {{ getPriorityLabel(task.priority) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag :type="getStatusTagType(task.status)">
                      {{ getStatusLabel(task.status) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="创建者">
                    {{ task.created_by || '系统' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="计划执行时间">
                    {{ task.scheduled_at ? formatDate(task.scheduled_at) : '立即执行' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="描述" :span="2">
                    {{ task.description || '无描述' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="目标资产" :span="2">
                    <div class="target-assets">
                      <el-tag
                        v-for="assetId in task.target_assets"
                        :key="assetId"
                        size="small"
                        style="margin-right: 8px; margin-bottom: 4px;"
                      >
                        {{ getAssetName(assetId) }}
                      </el-tag>
                    </div>
                  </el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>

              <!-- Configuration -->
              <el-tab-pane label="配置信息" name="config">
                <div class="config-display">
                  <el-descriptions title="扫描配置" :column="1" border>
                    <el-descriptions-item
                      v-for="(value, key) in task.config"
                      :key="key"
                      :label="getConfigLabel(key)"
                    >
                      {{ formatConfigValue(key, value) }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-tab-pane>

              <!-- Results -->
              <el-tab-pane label="扫描结果" name="results">
                <div v-if="results.summary">
                  <el-alert
                    :title="`扫描完成，共发现 ${results.vulnerabilities_found || 0} 个问题`"
                    type="info"
                    :closable="false"
                    show-icon
                  />

                  <div class="results-section">
                    <h4>漏洞统计</h4>
                    <el-row :gutter="16">
                      <el-col :span="6" v-for="severity in severityStats" :key="severity.name">
                        <div class="severity-stat">
                          <div class="severity-count" :class="severity.name">{{ severity.count }}</div>
                          <div class="severity-label">{{ severity.label }}</div>
                        </div>
                      </el-col>
                    </el-row>
                  </div>

                  <div v-if="results.vulnerabilities?.length" class="vulnerability-list">
                    <h4>发现的漏洞</h4>
                    <el-table :data="results.vulnerabilities" stripe>
                      <el-table-column prop="name" label="漏洞名称" min-width="200" />
                      <el-table-column prop="severity" label="严重程度" width="100">
                        <template #default="{ row }">
                          <el-tag :type="getSeverityTagType(row.severity)">
                            {{ getSeverityLabel(row.severity) }}
                          </el-tag>
                        </template>
                      </el-table-column>
                      <el-table-column prop="asset" label="影响资产" width="150" />
                      <el-table-column label="操作" width="100">
                        <template #default="{ row }">
                          <el-button size="small" @click="viewVulnerability(row)">查看</el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                </div>
                <el-empty v-else description="暂无扫描结果" />
              </el-tab-pane>

              <!-- Logs -->
              <el-tab-pane label="执行日志" name="logs">
                <div class="logs-section">
                  <div class="logs-toolbar">
                    <el-button @click="refreshLogs" :loading="logsLoading">
                      <el-icon><Refresh /></el-icon>
                      刷新日志
                    </el-button>
                    <el-button @click="downloadLogs">
                      <el-icon><Download /></el-icon>
                      下载日志
                    </el-button>
                  </div>
                  <div class="logs-content">
                    <div v-if="logs.length" class="log-entries">
                      <div
                        v-for="log in logs"
                        :key="log.id"
                        class="log-entry"
                        :class="log.level"
                      >
                        <span class="log-time">{{ formatDate(log.timestamp, 'time') }}</span>
                        <span class="log-level">{{ log.level?.toUpperCase() || 'INFO' }}</span>
                        <span class="log-message">{{ log.message }}</span>
                      </div>
                    </div>
                    <el-empty v-else description="暂无日志记录" />
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8">
          <!-- Timeline -->
          <el-card class="timeline-card">
            <template #header>
              <h3>执行时间线</h3>
            </template>
            <el-timeline>
              <el-timeline-item
                v-for="event in timeline"
                :key="event.id"
                :timestamp="formatDate(event.timestamp)"
                :type="getTimelineType(event.type)"
                :icon="getTimelineIcon(event.type)"
              >
                <h4>{{ event.title }}</h4>
                <p>{{ event.description }}</p>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>
    </div>
    <div v-else-if="!loading" class="empty-state">
      <el-empty description="任务不存在">
        <el-button type="primary" @click="$router.push('/tasks')">返回任务列表</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTaskStore } from '@/store/task'
import { useAssetStore } from '@/store/asset'
import { formatDate, formatDuration } from '@/utils/date'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()
const assetStore = useAssetStore()

const loading = ref(false)
const actionLoading = ref(false)
const logsLoading = ref(false)
const error = ref(false)
const task = ref(null)
const results = ref({})
const logs = ref([])
const timeline = ref([])
const assets = ref([])
const activeTab = ref('overview')

let refreshInterval = null

const severityStats = computed(() => [
  { name: 'critical', label: '严重', count: results.value.critical || 0 },
  { name: 'high', label: '高危', count: results.value.high || 0 },
  { name: 'medium', label: '中危', count: results.value.medium || 0 },
  { name: 'low', label: '低危', count: results.value.low || 0 }
])

onMounted(async () => {
  await loadTask()
  await loadAssets()
  if (task.value?.status === 'running') {
    startPolling()
  }
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

const loadTask = async () => {
  loading.value = true
  error.value = false
  try {
    task.value = await taskStore.getTask(route.params.id)
    await loadResults()
    await loadTimeline()
  } catch (err) {
    console.error('Failed to load task:', err)
    error.value = true
    ElMessage.error('加载任务信息失败')
  } finally {
    loading.value = false
  }
}

const retry = () => {
  loadTask()
}

const loadAssets = async () => {
  try {
    const response = await assetStore.getAssets({ limit: 1000 })
    assets.value = response.data || []
  } catch (error) {
    console.error('Failed to load assets:', error)
  }
}

const loadResults = async () => {
  try {
    if (task.value?.id) {
      results.value = await taskStore.getTaskResults(task.value.id)
    }
  } catch (error) {
    // Silently handle expected 400 errors for tasks without results
    // No need to log this as it's expected behavior
    results.value = { summary: null, vulnerabilities: [] }
  }
}

const loadTimeline = async () => {
  try {
    if (task.value?.created_at) {
      timeline.value = [
        {
          id: '1',
          title: '任务创建',
          description: '扫描任务已创建',
          timestamp: task.value.created_at,
          type: 'success'
        },
        ...(task.value.started_at ? [{
          id: '2',
          title: '开始执行',
          description: '任务开始执行',
          timestamp: task.value.started_at,
          type: 'primary'
        }] : []),
        ...(task.value.completed_at ? [{
          id: '3',
          title: '执行完成',
          description: '任务执行完成',
          timestamp: task.value.completed_at,
          type: 'success'
        }] : [])
      ]
    }
  } catch (error) {
    console.error('Failed to load timeline:', error)
  }
}

const refreshLogs = async () => {
  logsLoading.value = true
  try {
    const rawLogs = await taskStore.getTaskLogs(task.value.id)
    // Convert string logs to proper format
    if (Array.isArray(rawLogs)) {
      logs.value = rawLogs.map((log, index) => {
        if (typeof log === 'string') {
          // Parse string logs like "[2025-09-28T17:25:45.570366] Task 11 started"
          const match = log.match(/^\[(.*?)\]\s*(.*)$/)
          return {
            id: `log-${index}`,
            timestamp: match ? match[1] : new Date().toISOString(),
            level: 'info',
            message: match ? match[2] : log
          }
        }
        return log
      })
    } else {
      logs.value = []
    }
  } catch (error) {
    // Silently handle expected 404 errors for logs endpoint
    logs.value = []
  } finally {
    logsLoading.value = false
  }
}

const startPolling = () => {
  refreshInterval = setInterval(async () => {
    try {
      const updatedTask = await taskStore.getTask(task.value.id)
      task.value = updatedTask

      if (updatedTask.status !== 'running') {
        clearInterval(refreshInterval)
        await loadResults()
        await loadTimeline()
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 5000)
}

const handleStart = async () => {
  actionLoading.value = true
  try {
    await taskStore.startTask(task.value.id)
    ElMessage.success('任务启动成功')
    task.value.status = 'running'
    startPolling()
  } catch (error) {
    ElMessage.error('启动任务失败')
  } finally {
    actionLoading.value = false
  }
}

const handleStop = async () => {
  actionLoading.value = true
  try {
    await taskStore.stopTask(task.value.id)
    ElMessage.success('任务停止成功')
    task.value.status = 'stopped'
    if (refreshInterval) {
      clearInterval(refreshInterval)
    }
  } catch (error) {
    ElMessage.error('停止任务失败')
  } finally {
    actionLoading.value = false
  }
}

const handleCommand = async (command) => {
  switch (command) {
    case 'clone':
      await cloneTask()
      break
    case 'export':
      await exportResults()
      break
    case 'restart':
      await restartTask()
      break
    case 'delete':
      await deleteTask()
      break
  }
}

const cloneTask = async () => {
  try {
    const newTask = await taskStore.cloneTask(task.value.id)
    ElMessage.success('任务克隆成功')
    router.push(`/tasks/${newTask.id}`)
  } catch (error) {
    ElMessage.error('克隆任务失败')
  }
}

const exportResults = async () => {
  try {
    const data = await taskStore.exportTaskResults(task.value.id)
    // Trigger download
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `task-${task.value.id}-results.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('结果导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const restartTask = async () => {
  try {
    const result = await taskStore.restartTask(task.value.id)
    if (result?.task) {
      ElMessage.success('任务重启成功')
      task.value.status = 'running'
      startPolling()
    } else {
      ElMessage.warning('任务不存在或无法重启')
    }
  } catch (error) {
    // Silently handle restart errors - task might not support restart
    ElMessage.warning('该任务暂不支持重启')
  }
}

const deleteTask = async () => {
  await ElMessageBox.confirm('确定要删除这个任务吗？', '确认删除', {
    type: 'warning'
  })

  try {
    await taskStore.deleteTask(task.value.id)
    ElMessage.success('任务删除成功')
    router.push('/tasks')
  } catch (error) {
    ElMessage.error('删除任务失败')
  }
}

const handleTabChange = (tabName) => {
  if (tabName === 'logs' && logs.value.length === 0) {
    refreshLogs()
  }
}

const downloadLogs = () => {
  const logText = logs.value.map(log =>
    `[${formatDate(log.timestamp)}] ${log.level.toUpperCase()}: ${log.message}`
  ).join('\n')

  const blob = new Blob([logText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `task-${task.value.id}-logs.txt`
  a.click()
  URL.revokeObjectURL(url)
}

const viewVulnerability = (vulnerability) => {
  router.push(`/vulnerabilities/${vulnerability.id}`)
}

const getAssetName = (assetId) => {
  const asset = assets.value.find(a => a.id === assetId)
  return asset ? asset.name : assetId
}

const getConfigLabel = (key) => {
  const labels = {
    port_range: '端口范围',
    scan_speed: '扫描速度',
    concurrency: '并发数',
    timeout: '超时时间',
    intensity: '扫描强度'
  }
  return labels[key] || key
}

const formatConfigValue = (key, value) => {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  return value
}

// Helper functions
const getTypeLabel = (type) => {
  const labels = {
    port_scan: '端口扫描',
    vulnerability_scan: '漏洞扫描',
    web_discovery: 'Web发现',
    subdomain_enum: '子域名枚举',
    comprehensive: '综合扫描'
  }
  return labels[type] || type
}

const getTypeTagType = (type) => {
  const types = {
    port_scan: 'primary',
    vulnerability_scan: 'danger',
    web_discovery: 'success',
    subdomain_enum: 'warning',
    comprehensive: 'info'
  }
  return types[type] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    stopped: '已停止'
  }
  return labels[status] || status
}

const getStatusTagType = (status) => {
  const types = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    stopped: 'info'
  }
  return types[status] || 'info'
}

const getPriorityLabel = (priority) => {
  const labels = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return labels[priority] || priority
}

const getPriorityTagType = (priority) => {
  const types = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return types[priority] || 'info'
}

const getSeverityLabel = (severity) => {
  const labels = {
    critical: '严重',
    high: '高危',
    medium: '中危',
    low: '低危'
  }
  return labels[severity] || severity
}

const getSeverityTagType = (severity) => {
  const types = {
    critical: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'success'
  }
  return types[severity] || 'info'
}

const getTimelineType = (type) => {
  const types = {
    success: 'success',
    primary: 'primary',
    warning: 'warning',
    danger: 'danger'
  }
  return types[type] || 'primary'
}

const getTimelineIcon = (type) => {
  // Return icon name based on type
  return undefined
}
</script>

<style scoped lang="scss">
.task-detail {
  .task-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;

    .header-left {
      h1 {
        font-size: 28px;
        margin-bottom: 12px;
        color: var(--el-text-color-primary);
      }

      .task-meta {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

  .progress-card {
    margin-bottom: 24px;

    .progress-info {
      .progress-text {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-weight: 500;
      }

      .current-step {
        margin-top: 8px;
        color: var(--el-text-color-regular);
        font-size: 14px;
      }
    }
  }

  .overview-cards {
    margin-bottom: 24px;

    .stat-card {
      text-align: center;
      position: relative;

      .stat-content {
        .stat-number {
          font-size: 24px;
          font-weight: bold;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }

        .stat-label {
          color: var(--el-text-color-regular);
          font-size: 14px;
        }
      }

      .stat-icon {
        position: absolute;
        right: 16px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 24px;
        color: var(--el-color-primary);
        opacity: 0.3;
      }
    }
  }

  .target-assets {
    max-height: 100px;
    overflow-y: auto;
  }

  .config-display {
    :deep(.el-descriptions__label) {
      font-weight: 500;
    }
  }

  .results-section {
    margin: 24px 0;

    h4 {
      margin-bottom: 16px;
      color: var(--el-text-color-primary);
    }

    .severity-stat {
      text-align: center;
      padding: 16px;
      border-radius: 8px;
      background: var(--el-fill-color-light);

      .severity-count {
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 4px;

        &.critical { color: var(--el-color-danger); }
        &.high { color: var(--el-color-warning); }
        &.medium { color: var(--el-color-info); }
        &.low { color: var(--el-color-success); }
      }

      .severity-label {
        color: var(--el-text-color-regular);
        font-size: 14px;
      }
    }
  }

  .vulnerability-list {
    margin-top: 24px;

    h4 {
      margin-bottom: 16px;
      color: var(--el-text-color-primary);
    }
  }

  .logs-section {
    .logs-toolbar {
      margin-bottom: 16px;
      display: flex;
      gap: 12px;
    }

    .logs-content {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid var(--el-border-color);
      border-radius: 4px;
      padding: 12px;
      background: var(--el-fill-color-extra-light);

      .log-entries {
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 12px;
        line-height: 1.4;

        .log-entry {
          margin-bottom: 4px;

          .log-time {
            color: var(--el-text-color-secondary);
            margin-right: 8px;
          }

          .log-level {
            margin-right: 8px;
            font-weight: bold;

            &.ERROR { color: var(--el-color-danger); }
            &.WARN { color: var(--el-color-warning); }
            &.INFO { color: var(--el-color-primary); }
            &.DEBUG { color: var(--el-text-color-secondary); }
          }

          .log-message {
            color: var(--el-text-color-primary);
          }
        }
      }
    }
  }

  .timeline-card {
    .el-timeline {
      padding: 12px 0;
    }
  }
}

@media (max-width: 768px) {
  .task-detail .task-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;

    .header-actions {
      justify-content: center;
    }
  }
}
</style>