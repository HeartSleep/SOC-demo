<template>
  <div class="report-detail-view">
    <div class="page-header">
      <el-button @click="handleBack">
        <el-icon><Back /></el-icon>
        返回
      </el-button>
      <h2>报告详情</h2>
    </div>

    <div v-loading="loading">
      <el-card v-if="report" class="report-info-card">
        <template #header>
          <div class="card-header">
            <span>{{ report.name }}</span>
            <el-tag :type="getStatusTag(report.status)">
              {{ report.status }}
            </el-tag>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="报告类型">
            {{ report.type }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(report.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建人">
            {{ report.created_by || '系统' }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ report.file_size || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="actions-card">
        <el-space>
          <el-button type="primary" @click="handleDownload">
            <el-icon><Download /></el-icon>
            下载报告
          </el-button>
          <el-button @click="handleRegenerate">
            <el-icon><Refresh /></el-icon>
            重新生成
          </el-button>
          <el-button type="danger" @click="handleDelete">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </el-space>
      </el-card>

      <el-card v-if="report?.content" class="content-card">
        <template #header>
          <span>报告内容</span>
        </template>
        <div class="report-content" v-html="report.content"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Download, Refresh, Delete } from '@element-plus/icons-vue'
import { useReportStore } from '@/store/report'
import type { Report } from '@/types/report'

const router = useRouter()
const route = useRoute()
const reportStore = useReportStore()

const loading = ref(false)
const report = ref<Report | null>(null)

const fetchReport = async () => {
  const id = route.params.id as string
  loading.value = true
  try {
    report.value = await reportStore.getReport(id)
  } catch (error) {
    console.error('获取报告详情失败:', error)
    ElMessage.error('获取报告详情失败')
  } finally {
    loading.value = false
  }
}

const handleBack = () => {
  router.back()
}

const handleDownload = async () => {
  if (!report.value) return
  try {
    const blob = await reportStore.downloadReport(report.value.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${report.value.name || 'report'}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载报告失败:', error)
  }
}

const handleRegenerate = async () => {
  if (!report.value) return
  try {
    await ElMessageBox.confirm('确定要重新生成这个报告吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await reportStore.regenerateReport(report.value.id)
    ElMessage.success('报告重新生成中')
    fetchReport()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重新生成报告失败:', error)
    }
  }
}

const handleDelete = async () => {
  if (!report.value) return
  try {
    await ElMessageBox.confirm('确定要删除这个报告吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await reportStore.deleteReport(report.value.id)
    ElMessage.success('删除成功')
    router.push('/reports')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除报告失败:', error)
    }
  }
}

const getStatusTag = (status: string) => {
  const statusMap: Record<string, string> = {
    completed: 'success',
    pending: 'warning',
    failed: 'danger',
    generating: 'info'
  }
  return statusMap[status] || 'info'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchReport()
})
</script>

<style scoped>
.report-detail-view {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.report-info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions-card {
  margin-bottom: 20px;
}

.content-card {
  min-height: 400px;
}

.report-content {
  line-height: 1.8;
}
</style>
