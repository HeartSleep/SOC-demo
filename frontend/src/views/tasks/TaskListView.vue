<template>
  <div class="task-list">
    <div class="page-header">
      <h1>扫描任务</h1>
      <p>管理和监控您的安全扫描任务</p>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <el-button
          type="primary"
          @click="$router.push('/tasks/create')"
        >
          <el-icon><Plus /></el-icon>
          创建任务
        </el-button>
        <el-button
          @click="handleBulkStop"
          :disabled="selectedTasks.length === 0"
        >
          <el-icon><VideoPause /></el-icon>
          批量停止
        </el-button>
        <el-button
          type="danger"
          @click="handleBulkDelete"
          :disabled="selectedTasks.length === 0"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>

      <div class="toolbar-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索任务..."
          prefix-icon="Search"
          clearable
          @input="handleSearch"
        />
        <el-select v-model="statusFilter" placeholder="状态" clearable>
          <el-option label="全部" value="" />
          <el-option label="等待中" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
          <el-option label="已停止" value="stopped" />
        </el-select>
        <el-select v-model="typeFilter" placeholder="类型" clearable>
          <el-option label="全部" value="" />
          <el-option label="端口扫描" value="port_scan" />
          <el-option label="漏洞扫描" value="vulnerability_scan" />
          <el-option label="Web发现" value="web_discovery" />
          <el-option label="子域名枚举" value="subdomain_enum" />
        </el-select>
        <el-button @click="fetchTasks">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-card>
      <el-table
        :data="tasks"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="name" label="任务名称" min-width="200">
          <template #default="{ row }">
            <router-link :to="`/tasks/${row.id}`" class="task-link">
              {{ row.name }}
            </router-link>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="扫描类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="target_count" label="目标数量" width="100">
          <template #default="{ row }">
            {{ row.target_assets?.length || 0 }}
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="progress" label="进度" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress || 0"
              :status="getProgressStatus(row.status)"
              :stroke-width="6"
            />
          </template>
        </el-table-column>

        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getPriorityTagType(row.priority)"
              size="small"
            >
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="created_by" label="创建者" width="120" />

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending' || row.status === 'running'"
              type="warning"
              size="small"
              @click="handleStop(row)"
            >
              停止
            </el-button>
            <el-button
              v-else-if="row.status === 'stopped' || row.status === 'failed'"
              type="success"
              size="small"
              @click="handleRestart(row)"
            >
              重启
            </el-button>
            <el-button
              size="small"
              @click="$router.push(`/tasks/${row.id}`)"
            >
              详情
            </el-button>
            <el-dropdown @command="(cmd) => handleCommand(cmd, row)">
              <el-button size="small" type="info">
                更多<el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="clone">克隆任务</el-dropdown-item>
                  <el-dropdown-item command="export">导出结果</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, toRefs } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTaskStore } from '@/store/task'
import { formatDate, formatDuration } from '@/utils/date'

const router = useRouter()
const taskStore = useTaskStore()

const loading = ref(false)
const tasks = ref([])
const selectedTasks = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

const { currentPage, pageSize, total } = toRefs(pagination)

let refreshInterval = null

onMounted(() => {
  fetchTasks()
  // Auto refresh every 10 seconds
  refreshInterval = setInterval(fetchTasks, 10000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.currentPage - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      search: searchQuery.value,
      status: statusFilter.value,
      type: typeFilter.value
    }
    const response = await taskStore.getTasks(params)
    tasks.value = response.data || []
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.currentPage = 1
  fetchTasks()
}

const handleSelectionChange = (selection) => {
  selectedTasks.value = selection
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  fetchTasks()
}

const handleCurrentChange = (page) => {
  pagination.currentPage = page
  fetchTasks()
}

const handleStop = async (task) => {
  try {
    await taskStore.stopTask(task.id)
    ElMessage.success('任务停止成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error('停止任务失败')
  }
}

const handleRestart = async (task) => {
  try {
    await taskStore.restartTask(task.id)
    ElMessage.success('任务重启成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error('重启任务失败')
  }
}

const handleBulkStop = async () => {
  const runningTasks = selectedTasks.value.filter(
    task => task.status === 'running' || task.status === 'pending'
  )

  if (runningTasks.length === 0) {
    ElMessage.warning('没有可停止的任务')
    return
  }

  await ElMessageBox.confirm(
    `确定要停止选中的 ${runningTasks.length} 个任务吗？`,
    '确认停止',
    { type: 'warning' }
  )

  const ids = runningTasks.map(task => task.id)
  try {
    await taskStore.bulkStop(ids)
    ElMessage.success('批量停止成功')
    selectedTasks.value = []
    fetchTasks()
  } catch (error) {
    ElMessage.error('批量停止失败')
  }
}

const handleBulkDelete = async () => {
  await ElMessageBox.confirm(
    `确定要删除选中的 ${selectedTasks.value.length} 个任务吗？`,
    '确认删除',
    { type: 'warning' }
  )

  const ids = selectedTasks.value.map(task => task.id)
  try {
    await taskStore.bulkDelete(ids)
    ElMessage.success('批量删除成功')
    selectedTasks.value = []
    fetchTasks()
  } catch (error) {
    ElMessage.error('批量删除失败')
  }
}

const handleCommand = async (command, task) => {
  switch (command) {
    case 'clone':
      await cloneTask(task)
      break
    case 'export':
      await exportTaskResults(task)
      break
    case 'delete':
      await deleteTask(task)
      break
  }
}

const cloneTask = async (task) => {
  try {
    const newTask = await taskStore.cloneTask(task.id)
    ElMessage.success('任务克隆成功')
    router.push(`/tasks/${newTask.id}`)
  } catch (error) {
    ElMessage.error('克隆任务失败')
  }
}

const exportTaskResults = async (task) => {
  try {
    const data = await taskStore.exportTaskResults(task.id)
    // Trigger download
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${task.name}-results.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('结果导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const deleteTask = async (task) => {
  await ElMessageBox.confirm('确定要删除这个任务吗？', '确认删除', {
    type: 'warning'
  })

  try {
    await taskStore.deleteTask(task.id)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// Helper functions
const getTypeLabel = (type) => {
  const labels = {
    port_scan: '端口扫描',
    vulnerability_scan: '漏洞扫描',
    web_discovery: 'Web发现',
    subdomain_enum: '子域名枚举'
  }
  return labels[type] || type
}

const getTypeTagType = (type) => {
  const types = {
    port_scan: 'primary',
    vulnerability_scan: 'danger',
    web_discovery: 'success',
    subdomain_enum: 'warning'
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

const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
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
</script>

<style scoped lang="scss">
.task-list {
  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: 24px;
      margin-bottom: 8px;
      color: var(--el-text-color-primary);
    }

    p {
      color: var(--el-text-color-regular);
      margin: 0;
    }
  }

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 16px;

    .toolbar-left {
      display: flex;
      gap: 12px;
    }

    .toolbar-right {
      display: flex;
      gap: 12px;
      align-items: center;

      .el-input {
        width: 240px;
      }

      .el-select {
        width: 120px;
      }
    }
  }

  .task-link {
    color: var(--el-color-primary);
    text-decoration: none;
    font-weight: 500;

    &:hover {
      text-decoration: underline;
    }
  }

  .pagination {
    margin-top: 20px;
    text-align: right;
  }
}

@media (max-width: 768px) {
  .task-list .toolbar {
    flex-direction: column;
    align-items: stretch;

    .toolbar-left,
    .toolbar-right {
      justify-content: center;
    }

    .toolbar-right {
      .el-input {
        width: 100%;
      }
    }
  }
}
</style>