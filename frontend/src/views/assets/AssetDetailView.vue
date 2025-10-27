<template>
  <div class="asset-detail" v-loading="loading">
    <div v-if="asset" class="asset-content">
      <!-- Header -->
      <div class="asset-header">
        <div class="header-left">
          <h1>{{ asset.name }}</h1>
          <div class="asset-meta">
            <el-tag :type="getTypeTagType(asset.type)">
              {{ getTypeLabel(asset.type) }}
            </el-tag>
            <el-tag :type="getStatusTagType(asset.status)">
              {{ getStatusLabel(asset.status) }}
            </el-tag>
            <el-tag :type="getPriorityTagType(asset.priority)">
              {{ getPriorityLabel(asset.priority) }}
            </el-tag>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            type="primary"
            @click="handleScan"
            :loading="scanLoading"
          >
            <el-icon><Operation /></el-icon>
            开始扫描
          </el-button>
          <el-button @click="$router.push(`/assets/${asset.id}/edit`)">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-dropdown @command="handleCommand">
            <el-button>
              更多操作<el-icon><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="export">导出数据</el-dropdown-item>
                <el-dropdown-item command="clone">克隆资产</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除资产</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- Overview Cards -->
      <el-row :gutter="16" class="overview-cards">
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ asset.ports?.length || 0 }}</div>
              <div class="stat-label">开放端口</div>
            </div>
            <el-icon class="stat-icon"><Connection /></el-icon>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card vulnerabilities">
            <div class="stat-content">
              <div class="stat-number">{{ asset.vulnerabilities?.length || 0 }}</div>
              <div class="stat-label">发现漏洞</div>
            </div>
            <el-icon class="stat-icon"><Warning /></el-icon>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ asset.scan_count || 0 }}</div>
              <div class="stat-label">扫描次数</div>
            </div>
            <el-icon class="stat-icon"><DataAnalysis /></el-icon>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ formatDate(asset.last_scan, 'relative') }}</div>
              <div class="stat-label">最后扫描</div>
            </div>
            <el-icon class="stat-icon"><Clock /></el-icon>
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
              <el-tab-pane label="基本信息" name="overview">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="资产名称">
                    {{ asset.name }}
                  </el-descriptions-item>
                  <el-descriptions-item label="资产类型">
                    <el-tag :type="getTypeTagType(asset.type)">
                      {{ getTypeLabel(asset.type) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="资产值">
                    {{ asset.value }}
                  </el-descriptions-item>
                  <el-descriptions-item label="优先级">
                    <el-tag :type="getPriorityTagType(asset.priority)">
                      {{ getPriorityLabel(asset.priority) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag :type="getStatusTagType(asset.status)">
                      {{ getStatusLabel(asset.status) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="所属部门">
                    {{ asset.department || '未设置' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="标签" :span="2">
                    <el-tag
                      v-for="tag in asset.tags"
                      :key="tag"
                      size="small"
                      style="margin-right: 8px;"
                    >
                      {{ tag }}
                    </el-tag>
                    <span v-if="!asset.tags?.length">无</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="描述" :span="2">
                    {{ asset.description || '无描述' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="创建时间">
                    {{ formatDate(asset.created_at) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="更新时间">
                    {{ formatDate(asset.updated_at) }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>

              <!-- Ports -->
              <el-tab-pane label="端口信息" name="ports">
                <div v-if="asset.ports?.length">
                  <el-table :data="asset.ports" stripe>
                    <el-table-column prop="port" label="端口" width="80" />
                    <el-table-column prop="protocol" label="协议" width="80" />
                    <el-table-column prop="service" label="服务" width="120" />
                    <el-table-column prop="version" label="版本" />
                    <el-table-column prop="state" label="状态" width="80">
                      <template #default="{ row }">
                        <el-tag
                          :type="row.state === 'open' ? 'success' : 'info'"
                          size="small"
                        >
                          {{ row.state }}
                        </el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="暂无端口信息" />
              </el-tab-pane>

              <!-- Vulnerabilities -->
              <el-tab-pane label="漏洞信息" name="vulnerabilities">
                <div v-if="vulnerabilities?.length">
                  <el-table :data="vulnerabilities" stripe>
                    <el-table-column prop="name" label="漏洞名称" min-width="200" />
                    <el-table-column prop="severity" label="严重程度" width="100">
                      <template #default="{ row }">
                        <el-tag :type="getSeverityTagType(row.severity)">
                          {{ getSeverityLabel(row.severity) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="cvss_score" label="CVSS评分" width="100" />
                    <el-table-column prop="status" label="状态" width="100">
                      <template #default="{ row }">
                        <el-tag :type="getVulnStatusTagType(row.status)" size="small">
                          {{ getVulnStatusLabel(row.status) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="150">
                      <template #default="{ row }">
                        <el-button
                          size="small"
                          @click="$router.push(`/vulnerabilities/${row.id}`)"
                        >
                          详情
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="暂无漏洞信息" />
              </el-tab-pane>

              <!-- Scan History -->
              <el-tab-pane label="扫描历史" name="scans">
                <div v-if="scanHistory?.length">
                  <el-table :data="scanHistory" stripe>
                    <el-table-column prop="task_name" label="任务名称" />
                    <el-table-column prop="scan_type" label="扫描类型" width="120" />
                    <el-table-column prop="status" label="状态" width="100">
                      <template #default="{ row }">
                        <el-tag :type="getTaskStatusTagType(row.status)" size="small">
                          {{ getTaskStatusLabel(row.status) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="duration" label="耗时" width="100" />
                    <el-table-column prop="created_at" label="开始时间" width="150">
                      <template #default="{ row }">
                        {{ formatDate(row.created_at) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="150">
                      <template #default="{ row }">
                        <el-button
                          size="small"
                          @click="$router.push(`/tasks/${row.id}`)"
                        >
                          查看
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="暂无扫描历史" />
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8">
          <!-- Quick Actions -->
          <el-card class="quick-actions-card">
            <template #header>
              <h3>快速操作</h3>
            </template>
            <div class="quick-actions">
              <el-button
                type="primary"
                size="large"
                @click="createQuickTask('port_scan')"
              >
                <el-icon><Connection /></el-icon>
                端口扫描
              </el-button>
              <el-button
                type="success"
                size="large"
                @click="createQuickTask('vulnerability_scan')"
              >
                <el-icon><Warning /></el-icon>
                漏洞扫描
              </el-button>
              <el-button
                type="info"
                size="large"
                @click="createQuickTask('web_discovery')"
              >
                <el-icon><Globe /></el-icon>
                Web发现
              </el-button>
            </div>
          </el-card>

          <!-- Recent Activity -->
          <el-card class="activity-card">
            <template #header>
              <h3>最近活动</h3>
            </template>
            <el-timeline v-if="activities?.length">
              <el-timeline-item
                v-for="activity in activities.slice(0, 5)"
                :key="activity.id"
                :timestamp="formatDate(activity.timestamp)"
                :type="activity.type"
              >
                {{ activity.description }}
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无活动记录" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAssetStore } from '@/store/asset'
import { useTaskStore } from '@/store/task'
import { formatDate } from '@/utils/date'

const route = useRoute()
const router = useRouter()
const assetStore = useAssetStore()
const taskStore = useTaskStore()

const loading = ref(false)
const scanLoading = ref(false)
const asset = ref(null)
const vulnerabilities = ref([])
const scanHistory = ref([])
const activities = ref([])
const activeTab = ref('overview')

onMounted(async () => {
  await loadAsset()
  await loadVulnerabilities()
  await loadScanHistory()
  await loadActivities()
})

const loadAsset = async () => {
  loading.value = true
  try {
    asset.value = await assetStore.getAsset(route.params.id)
  } catch (error) {
    ElMessage.error('加载资产信息失败')
    router.back()
  } finally {
    loading.value = false
  }
}

const loadVulnerabilities = async () => {
  try {
    vulnerabilities.value = await assetStore.getAssetVulnerabilities(route.params.id)
  } catch (error) {
    console.error('Failed to load vulnerabilities:', error)
  }
}

const loadScanHistory = async () => {
  try {
    scanHistory.value = await assetStore.getAssetScanHistory(route.params.id)
  } catch (error) {
    console.error('Failed to load scan history:', error)
  }
}

const loadActivities = async () => {
  try {
    activities.value = await assetStore.getAssetActivities(route.params.id)
  } catch (error) {
    console.error('Failed to load activities:', error)
  }
}

const handleTabChange = (tabName) => {
  activeTab.value = tabName
}

const handleScan = async () => {
  scanLoading.value = true
  try {
    await assetStore.scanAsset(asset.value.id)
    ElMessage.success('扫描任务已启动')
    await loadScanHistory()
  } catch (error) {
    ElMessage.error('启动扫描失败')
  } finally {
    scanLoading.value = false
  }
}

const createQuickTask = async (taskType) => {
  try {
    const taskData = {
      name: `${asset.value.name} - ${getTaskTypeLabel(taskType)}`,
      type: taskType,
      target_assets: [asset.value.id],
      priority: asset.value.priority
    }

    const task = await taskStore.createTask(taskData)
    ElMessage.success('任务创建成功')
    router.push(`/tasks/${task.id}`)
  } catch (error) {
    ElMessage.error('创建任务失败')
  }
}

const handleCommand = async (command) => {
  switch (command) {
    case 'export':
      await exportAssetData()
      break
    case 'clone':
      await cloneAsset()
      break
    case 'delete':
      await deleteAsset()
      break
  }
}

const exportAssetData = async () => {
  try {
    const data = await assetStore.exportAsset(asset.value.id)
    // Trigger download
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${asset.value.name}-export.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('数据导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const cloneAsset = () => {
  router.push(`/assets/create?clone=${asset.value.id}`)
}

const deleteAsset = async () => {
  await ElMessageBox.confirm('确定要删除这个资产吗？此操作不可恢复。', '确认删除', {
    type: 'warning'
  })

  try {
    await assetStore.deleteAsset(asset.value.id)
    ElMessage.success('资产删除成功')
    router.push('/assets')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// Helper functions
const getTypeLabel = (type) => {
  const labels = { domain: '域名', ip: 'IP', url: 'URL', port: '端口' }
  return labels[type] || type
}

const getTypeTagType = (type) => {
  const types = { domain: 'primary', ip: 'success', url: 'info', port: 'warning' }
  return types[type] || 'info'
}

const getStatusLabel = (status) => {
  const labels = { active: '活跃', inactive: '非活跃', unknown: '未知' }
  return labels[status] || status
}

const getStatusTagType = (status) => {
  const types = { active: 'success', inactive: 'danger', unknown: 'info' }
  return types[status] || 'info'
}

const getPriorityLabel = (priority) => {
  const labels = { low: '低', medium: '中', high: '高', critical: '紧急' }
  return labels[priority] || priority
}

const getPriorityTagType = (priority) => {
  const types = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return types[priority] || 'info'
}

const getSeverityLabel = (severity) => {
  const labels = { critical: '严重', high: '高危', medium: '中危', low: '低危' }
  return labels[severity] || severity
}

const getSeverityTagType = (severity) => {
  const types = { critical: 'danger', high: 'warning', medium: 'info', low: 'success' }
  return types[severity] || 'info'
}

const getVulnStatusLabel = (status) => {
  const labels = { open: '待修复', fixed: '已修复', false_positive: '误报' }
  return labels[status] || status
}

const getVulnStatusTagType = (status) => {
  const types = { open: 'danger', fixed: 'success', false_positive: 'info' }
  return types[status] || 'info'
}

const getTaskStatusLabel = (status) => {
  const labels = { pending: '等待中', running: '运行中', completed: '已完成', failed: '失败' }
  return labels[status] || status
}

const getTaskStatusTagType = (status) => {
  const types = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }
  return types[status] || 'info'
}

const getTaskTypeLabel = (type) => {
  const labels = { port_scan: '端口扫描', vulnerability_scan: '漏洞扫描', web_discovery: 'Web发现' }
  return labels[type] || type
}
</script>

<style scoped lang="scss">
.asset-detail {
  .asset-header {
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

      .asset-meta {
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

  .overview-cards {
    margin-bottom: 24px;

    .stat-card {
      text-align: center;
      position: relative;
      overflow: hidden;

      .stat-content {
        position: relative;
        z-index: 2;

        .stat-number {
          font-size: 28px;
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
        font-size: 32px;
        color: var(--el-color-primary);
        opacity: 0.3;
      }

      &.vulnerabilities .stat-icon {
        color: var(--el-color-danger);
      }
    }
  }

  .quick-actions-card {
    margin-bottom: 20px;

    .quick-actions {
      display: flex;
      flex-direction: column;
      gap: 12px;

      .el-button {
        height: 48px;
        font-size: 15px;

        .el-icon {
          margin-right: 8px;
        }
      }
    }
  }

  .activity-card {
    .el-timeline {
      padding-top: 12px;
    }
  }
}

@media (max-width: 768px) {
  .asset-detail .asset-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;

    .header-actions {
      justify-content: center;
    }
  }
}
</style>