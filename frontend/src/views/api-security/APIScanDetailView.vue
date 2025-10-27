<template>
  <div class="api-scan-detail">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600 mr-3">API扫描详情</span>
      </template>
    </el-page-header>

    <el-card v-if="task" class="detail-card" v-loading="loading">
      <!-- 任务基本信息 -->
      <template #header>
        <div class="card-header">
          <h3>{{ task.name }}</h3>
          <el-tag :type="getStatusType(task.status)">
            {{ getStatusText(task.status) }}
          </el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="目标URL">
          <a :href="task.target_url" target="_blank">{{ task.target_url }}</a>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(task.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ task.started_at ? formatDate(task.started_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="完成时间">
          {{ task.completed_at ? formatDate(task.completed_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="执行时长">
          {{ task.duration_seconds ? `${task.duration_seconds}秒` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="当前阶段">
          {{ task.current_phase || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 进度条 -->
      <el-progress
        v-if="task.status === 'running'"
        :percentage="task.progress"
        :status="task.progress === 100 ? 'success' : undefined"
        class="progress-bar"
      />

      <!-- 错误信息 -->
      <el-alert
        v-if="task.error_message"
        type="error"
        :title="task.error_message"
        :closable="false"
        class="error-alert"
      />
    </el-card>

    <!-- 统计信息 -->
    <el-row :gutter="20" class="stats-row" v-if="task">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="JS文件" :value="task.total_js_files" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="API接口" :value="task.total_apis" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="微服务" :value="task.total_services" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic
            title="安全问题"
            :value="task.total_issues"
            :value-style="{ color: task.total_issues > 0 ? '#f56c6c' : '#67c23a' }"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- Tabs -->
    <el-card v-if="task && task.status === 'completed'">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="安全问题" name="issues">
          <el-table :data="issues" v-loading="loadingIssues">
            <el-table-column prop="title" label="问题" min-width="250" />
            <el-table-column label="类型" width="150">
              <template #default="{ row }">
                {{ getIssueTypeText(row.issue_type) }}
              </template>
            </el-table-column>
            <el-table-column label="严重程度" width="120">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)">
                  {{ getSeverityText(row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="target_url" label="目标URL" min-width="200" show-overflow-tooltip />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-icon v-if="row.is_resolved" color="green"><Check /></el-icon>
                <el-icon v-else-if="row.is_verified" color="orange"><Warning /></el-icon>
                <el-icon v-else color="red"><Close /></el-icon>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="API接口" name="apis">
          <el-table :data="apis" v-loading="loadingApis">
            <el-table-column prop="full_url" label="API地址" min-width="300" show-overflow-tooltip />
            <el-table-column prop="http_method" label="方法" width="100" />
            <el-table-column prop="service_path" label="服务" width="120" />
            <el-table-column prop="status_code" label="状态码" width="100" />
            <el-table-column label="认证" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.requires_auth" type="warning" size="small">需要</el-tag>
                <el-tag v-else type="success" size="small">不需要</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="微服务" name="microservices">
          <el-table :data="microservices" v-loading="loadingMicroservices">
            <el-table-column prop="service_name" label="服务名称" width="150" />
            <el-table-column prop="service_full_path" label="服务路径" min-width="250" />
            <el-table-column prop="total_endpoints" label="端点数" width="100" />
            <el-table-column label="技术栈" min-width="200">
              <template #default="{ row }">
                <el-tag
                  v-for="tech in row.detected_technologies"
                  :key="tech"
                  size="small"
                  style="margin-right: 5px"
                >
                  {{ tech }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="漏洞" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.has_vulnerabilities" type="danger" size="small">
                  {{ row.vulnerability_details.length }}
                </el-tag>
                <el-tag v-else type="success" size="small">无</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="JS资源" name="js">
          <el-table :data="jsResources" v-loading="loadingJS">
            <el-table-column prop="file_name" label="文件名" width="200" />
            <el-table-column prop="url" label="URL" min-width="300" show-overflow-tooltip />
            <el-table-column label="大小" width="120">
              <template #default="{ row }">
                {{ formatFileSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column prop="extraction_method" label="提取方法" width="120" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, Warning, Close } from '@element-plus/icons-vue'
import {
  getAPIScanTask,
  getSecurityIssues,
  getAPIEndpoints,
  getMicroservices,
  getJSResources,
  type APIScanTask,
  type APISecurityIssue,
  type APIEndpoint,
  type MicroserviceInfo,
  type JSResource
} from '@/api/apiSecurity'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const task = ref<APIScanTask | null>(null)
const activeTab = ref('issues')

const issues = ref<APISecurityIssue[]>([])
const apis = ref<APIEndpoint[]>([])
const microservices = ref<MicroserviceInfo[]>([])
const jsResources = ref<JSResource[]>([])

const loadingIssues = ref(false)
const loadingApis = ref(false)
const loadingMicroservices = ref(false)
const loadingJS = ref(false)

onMounted(async () => {
  await loadTask()
  if (task.value && task.value.status === 'completed') {
    loadIssues()
    loadApis()
    loadMicroservices()
    loadJSResources()
  }
})

async function loadTask() {
  loading.value = true
  try {
    const id = route.params.id as string
    task.value = await getAPIScanTask(id)
  } catch (error) {
    ElMessage.error('加载任务详情失败')
  } finally {
    loading.value = false
  }
}

async function loadIssues() {
  loadingIssues.value = true
  try {
    const id = route.params.id as string
    issues.value = await getSecurityIssues(id)
  } catch (error) {
    console.error('加载安全问题失败', error)
  } finally {
    loadingIssues.value = false
  }
}

async function loadApis() {
  loadingApis.value = true
  try {
    const id = route.params.id as string
    apis.value = await getAPIEndpoints(id, { limit: 100 })
  } catch (error) {
    console.error('加载API失败', error)
  } finally {
    loadingApis.value = false
  }
}

async function loadMicroservices() {
  loadingMicroservices.value = true
  try {
    const id = route.params.id as string
    microservices.value = await getMicroservices(id)
  } catch (error) {
    console.error('加载微服务失败', error)
  } finally {
    loadingMicroservices.value = false
  }
}

async function loadJSResources() {
  loadingJS.value = true
  try {
    const id = route.params.id as string
    jsResources.value = await getJSResources(id, { limit: 100 })
  } catch (error) {
    console.error('加载JS资源失败', error)
  } finally {
    loadingJS.value = false
  }
}

function goBack() {
  router.push('/api-security')
}

function getStatusType(status: string) {
  const map: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

function getIssueTypeText(type: string) {
  const map: Record<string, string> = {
    unauthorized_access: '未授权访问',
    sensitive_data_leak: '敏感信息泄露',
    component_vulnerability: '组件漏洞',
    weak_authentication: '弱认证'
  }
  return map[type] || type
}

function getSeverityType(severity: string) {
  const map: Record<string, any> = {
    critical: 'danger',
    high: 'danger',
    medium: 'warning',
    low: 'success',
    info: 'info'
  }
  return map[severity] || 'info'
}

function getSeverityText(severity: string) {
  const map: Record<string, string> = {
    critical: '严重',
    high: '高危',
    medium: '中危',
    low: '低危',
    info: '提示'
  }
  return map[severity] || severity
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

function formatFileSize(bytes?: number) {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)}MB`
}
</script>

<style scoped>
.api-scan-detail {
  padding: 20px;
}

.detail-card {
  margin: 20px 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-bar {
  margin-top: 20px;
}

.error-alert {
  margin-top: 20px;
}

.stats-row {
  margin: 20px 0;
}
</style>
