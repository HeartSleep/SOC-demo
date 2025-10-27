<template>
  <div class="report-list">
    <div class="page-header">
      <h1>报告中心</h1>
      <p>管理和查看生成的安全报告</p>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <el-button type="primary" @click="$router.push('/reports/create')">
          <el-icon><Plus /></el-icon>
          生成报告
        </el-button>
        <el-button :disabled="selectedReports.length === 0" @click="handleBulkDownload">
          <el-icon><Download /></el-icon>
          批量下载
        </el-button>
        <el-button type="danger" :disabled="selectedReports.length === 0" @click="handleBulkDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>

      <div class="toolbar-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索报告..."
          prefix-icon="Search"
          clearable
          @input="handleSearch"
        />
        <el-select v-model="typeFilter" placeholder="报告类型" clearable>
          <el-option label="全部" value="" />
          <el-option label="漏洞报告" value="vulnerability" />
          <el-option label="资产报告" value="asset" />
          <el-option label="扫描报告" value="scan" />
          <el-option label="综合报告" value="comprehensive" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态" clearable>
          <el-option label="全部" value="" />
          <el-option label="生成中" value="generating" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
    </div>

    <el-card>
      <el-table
        v-loading="loading"
        :data="reports"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="title" label="报告标题" min-width="200">
          <template #default="{ row }">
            <router-link :to="`/reports/${row.id}`" class="report-link">
              {{ row.title }}
            </router-link>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="format" label="格式" width="120">
          <template #default="{ row }">
            <el-tag
              v-for="fmt in row.format"
              :key="fmt"
              size="small"
              style="margin-right: 4px"
            >
              {{ fmt.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="classification" label="密级" width="100">
          <template #default="{ row }">
            <el-tag :type="getClassificationTagType(row.classification)">
              {{ getClassificationLabel(row.classification) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              type="primary"
              size="small"
              @click="handleDownload(row)"
            >
              下载
            </el-button>
            <el-button size="small" @click="$router.push(`/reports/${row.id}`)">详情</el-button>
            <el-dropdown @command="cmd => handleCommand(cmd, row)">
              <el-button size="small" type="info">
                更多
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="row.status === 'completed'" command="regenerate">
                    重新生成
                  </el-dropdown-item>
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
import { ref, reactive, onMounted, toRefs } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useReportStore } from '@/store/report'
import { formatDate } from '@/utils/date'

const reportStore = useReportStore()

const loading = ref(false)
const reports = ref([])
const selectedReports = ref([])
const searchQuery = ref('')
const typeFilter = ref('')
const statusFilter = ref('')

const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

const { currentPage, pageSize, total } = toRefs(pagination)

onMounted(() => {
  fetchReports()
})

const fetchReports = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.currentPage - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      type: typeFilter.value,
      status: statusFilter.value,
      search: searchQuery.value
    }
    const response = await reportStore.getReports(params)
    reports.value = response.data || []
    pagination.total = response.total || 0
  } catch (error) {
    ElMessage.error('获取报告列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.currentPage = 1
  fetchReports()
}

const handleSelectionChange = selection => {
  selectedReports.value = selection
}

const handleSizeChange = size => {
  pagination.pageSize = size
  fetchReports()
}

const handleCurrentChange = page => {
  pagination.currentPage = page
  fetchReports()
}

const handleDownload = async report => {
  try {
    const blob = await reportStore.downloadReport(report.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${report.title}.${report.format[0] || 'pdf'}`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const handleBulkDownload = async () => {
  const ids = selectedReports.value.map(report => report.id)
  try {
    const blob = await reportStore.bulkDownload(ids)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `reports-${Date.now()}.zip`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('批量下载成功')
    selectedReports.value = []
  } catch (error) {
    ElMessage.error('批量下载失败')
  }
}

const handleBulkDelete = async () => {
  await ElMessageBox.confirm(
    `确定要删除选中的 ${selectedReports.value.length} 个报告吗？`,
    '确认删除',
    { type: 'warning' }
  )

  const ids = selectedReports.value.map(report => report.id)
  try {
    await reportStore.bulkDelete(ids)
    ElMessage.success('批量删除成功')
    selectedReports.value = []
    fetchReports()
  } catch (error) {
    ElMessage.error('批量删除失败')
  }
}

const handleCommand = async (command, report) => {
  if (command === 'regenerate') {
    await ElMessageBox.confirm('确定要重新生成这个报告吗？', '确认', {
      type: 'info'
    })
    try {
      await reportStore.regenerateReport(report.id)
      ElMessage.success('报告生成任务已启动')
      fetchReports()
    } catch (error) {
      ElMessage.error('启动失败')
    }
  } else if (command === 'delete') {
    await ElMessageBox.confirm('确定要删除这个报告吗？', '确认删除', {
      type: 'warning'
    })
    try {
      await reportStore.deleteReport(report.id)
      ElMessage.success('删除成功')
      fetchReports()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }
}

const getTypeLabel = type => {
  const labels = {
    vulnerability: '漏洞报告',
    asset: '资产报告',
    scan: '扫描报告',
    comprehensive: '综合报告',
    compliance: '合规报告',
    trend: '趋势报告'
  }
  return labels[type] || type
}

const getTypeTagType = type => {
  const types = {
    vulnerability: 'danger',
    asset: 'primary',
    scan: 'info',
    comprehensive: 'success',
    compliance: 'warning',
    trend: 'info'
  }
  return types[type] || 'info'
}

const getStatusLabel = status => {
  const labels = {
    draft: '草稿',
    generating: '生成中',
    completed: '已完成',
    failed: '失败',
    scheduled: '已计划'
  }
  return labels[status] || status
}

const getStatusTagType = status => {
  const types = {
    draft: 'info',
    generating: 'warning',
    completed: 'success',
    failed: 'danger',
    scheduled: 'primary'
  }
  return types[status] || 'info'
}

const getClassificationLabel = classification => {
  const labels = {
    public: '公开',
    internal: '内部',
    confidential: '机密',
    secret: '绝密'
  }
  return labels[classification] || classification
}

const getClassificationTagType = classification => {
  const types = {
    public: '',
    internal: 'info',
    confidential: 'warning',
    secret: 'danger'
  }
  return types[classification] || ''
}
</script>

<style scoped lang="scss">
.report-list {
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

  .report-link {
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
  .report-list .toolbar {
    flex-direction: column;
    align-items: stretch;

    .toolbar-left,
    .toolbar-right {
      width: 100%;
      flex-wrap: wrap;
    }

    .toolbar-right {
      .el-input,
      .el-select {
        flex: 1;
        min-width: 120px;
      }
    }
  }
}
</style>
