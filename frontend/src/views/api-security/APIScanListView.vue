<template>
  <div class="api-scan-list">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h3>API安全扫描</h3>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建扫描任务
          </el-button>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-row" v-if="statistics">
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="总扫描任务" :value="statistics.total_scans" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="发现API" :value="statistics.total_apis_discovered" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="微服务" :value="statistics.total_microservices" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic
              title="安全问题"
              :value="statistics.total_issues"
              :value-style="{ color: statistics.total_issues > 0 ? '#f56c6c' : '#67c23a' }"
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- 筛选 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filterStatus" @change="loadTasks" clearable>
            <el-option label="全部" value="" />
            <el-option label="待执行" value="pending" />
            <el-option label="执行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 任务列表 -->
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="name" label="任务名称" min-width="200" />
        <el-table-column prop="target_url" label="目标URL" min-width="250" show-overflow-tooltip />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="150">
          <template #default="{ row }">
            <el-progress
              v-if="row.status === 'running'"
              :percentage="row.progress"
              :status="row.progress === 100 ? 'success' : undefined"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="发现" width="280">
          <template #default="{ row }">
            <div class="stats-inline">
              <el-tag size="small">JS: {{ row.total_js_files }}</el-tag>
              <el-tag size="small" type="success">API: {{ row.total_apis }}</el-tag>
              <el-tag size="small" type="warning">服务: {{ row.total_services }}</el-tag>
              <el-tag size="small" type="danger">问题: {{ row.total_issues }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row.id)">详情</el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteTask(row.id)"
              :disabled="row.status === 'running'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建API扫描任务" width="600px">
      <el-form :model="createForm" label-width="120px">
        <el-form-item label="任务名称" required>
          <el-input v-model="createForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="目标URL" required>
          <el-input v-model="createForm.target_url" placeholder="https://example.com" />
        </el-form-item>
        <el-form-item label="扫描配置">
          <el-checkbox-group v-model="scanOptions">
            <el-checkbox label="enable_js_extraction">JS资源提取</el-checkbox>
            <el-checkbox label="enable_api_discovery">API发现</el-checkbox>
            <el-checkbox label="enable_microservice_detection">微服务识别</el-checkbox>
            <el-checkbox label="enable_unauthorized_check">未授权检测</el-checkbox>
            <el-checkbox label="enable_sensitive_info_check">敏感信息检测</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getAPIScanTasks,
  createAPIScanTask,
  deleteAPIScanTask,
  getAPIScanStatistics,
  type APIScanTask,
  type APIScanStatistics
} from '@/api/apiSecurity'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const tasks = ref<APIScanTask[]>([])
const statistics = ref<APIScanStatistics | null>(null)
const filterStatus = ref('')
const showCreateDialog = ref(false)

const scanOptions = ref([
  'enable_js_extraction',
  'enable_api_discovery',
  'enable_microservice_detection',
  'enable_sensitive_info_check'
])

const createForm = ref({
  name: '',
  target_url: ''
})

onMounted(() => {
  loadTasks()
  loadStatistics()
})

async function loadTasks() {
  loading.value = true
  try {
    tasks.value = await getAPIScanTasks({
      status: filterStatus.value || undefined
    })
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

async function loadStatistics() {
  try {
    statistics.value = await getAPIScanStatistics()
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

async function handleCreate() {
  if (!createForm.value.name || !createForm.value.target_url) {
    ElMessage.warning('请填写完整信息')
    return
  }

  creating.value = true
  try {
    const scanConfig: any = {}
    scanOptions.value.forEach(option => {
      scanConfig[option] = true
    })

    await createAPIScanTask({
      name: createForm.value.name,
      target_url: createForm.value.target_url,
      scan_config: scanConfig
    })

    ElMessage.success('扫描任务创建成功')
    showCreateDialog.value = false
    createForm.value = { name: '', target_url: '' }
    loadTasks()
    loadStatistics()
  } catch (error) {
    ElMessage.error('创建任务失败')
  } finally {
    creating.value = false
  }
}

function viewDetail(id: string) {
  router.push(`/api-security/${id}`)
}

async function deleteTask(id: string) {
  try {
    await ElMessageBox.confirm('确定删除此扫描任务吗？', '提示', {
      type: 'warning'
    })

    await deleteAPIScanTask(id)
    ElMessage.success('删除成功')
    loadTasks()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
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

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<style scoped>
.api-scan-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-row {
  margin-bottom: 20px;
}

.filter-form {
  margin: 20px 0;
}

.stats-inline {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
