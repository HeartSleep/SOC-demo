<template>
  <div class="report-list-view">
    <div class="page-header">
      <h2>报告中心</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        生成报告
      </el-button>
    </div>

    <el-card>
      <el-table
        v-loading="loading"
        :data="reports"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="报告名称" min-width="150" />
        <el-table-column prop="type" label="报告类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getReportTypeTag(row.type)">
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">
              查看
            </el-button>
            <el-button link type="primary" @click="handleDownload(row)">
              下载
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchReports"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useReportStore } from '@/store/report'
import type { Report } from '@/types/report'

const router = useRouter()
const reportStore = useReportStore()

const loading = ref(false)
const reports = ref<Report[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedIds = ref<string[]>([])

const fetchReports = async () => {
  loading.value = true
  try {
    const response = await reportStore.getReports({
      page: currentPage.value,
      page_size: pageSize.value
    })
    reports.value = response.items || response.data || []
    total.value = response.total || reports.value.length
  } catch (error) {
    console.error('获取报告列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (selection: Report[]) => {
  selectedIds.value = selection.map(item => item.id)
}

const handleCreate = () => {
  router.push('/reports/create')
}

const handleView = (row: Report) => {
  router.push(`/reports/${row.id}`)
}

const handleDownload = async (row: Report) => {
  try {
    const blob = await reportStore.downloadReport(row.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${row.name || 'report'}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载报告失败:', error)
  }
}

const handleDelete = async (row: Report) => {
  try {
    await ElMessageBox.confirm('确定要删除这个报告吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await reportStore.deleteReport(row.id)
    ElMessage.success('删除成功')
    fetchReports()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除报告失败:', error)
    }
  }
}

const getReportTypeTag = (type: string) => {
  const typeMap: Record<string, string> = {
    vulnerability: 'danger',
    asset: 'success',
    summary: 'primary'
  }
  return typeMap[type] || 'info'
}

const getStatusTag = (status: string) => {
  const statusMap: Record<string, string> = {
    completed: 'success',
    pending: 'warning',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.report-list-view {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
