<template>
  <div v-loading="loading" class="report-detail">
    <div v-if="error" class="error-state">
      <el-empty description="报告加载失败">
        <el-button type="primary" @click="retry">重试</el-button>
        <el-button @click="$router.push('/reports')">返回报告列表</el-button>
      </el-empty>
    </div>
    <div v-else-if="report" class="report-content">
      <!-- Header -->
      <div class="report-header">
        <div class="header-left">
          <h1>{{ report.title }}</h1>
          <div class="report-meta">
            <el-tag :type="getTypeTagType(report.type)">
              {{ getTypeLabel(report.type) }}
            </el-tag>
            <el-tag :type="getStatusTagType(report.status)">
              {{ getStatusLabel(report.status) }}
            </el-tag>
            <el-tag :type="getClassificationTagType(report.classification)">
              {{ getClassificationLabel(report.classification) }}
            </el-tag>
            <el-tag v-for="fmt in report.format" :key="fmt">
              {{ fmt.toUpperCase() }}
            </el-tag>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            v-if="report.status === 'completed'"
            type="primary"
            :loading="actionLoading"
            @click="handleDownload"
          >
            <el-icon><Download /></el-icon>
            下载报告
          </el-button>
          <el-button v-if="report.status === 'completed'" @click="handlePreview">
            <el-icon><View /></el-icon>
            在线预览
          </el-button>
          <el-dropdown @command="handleCommand">
            <el-button>
              更多操作
              <el-icon><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="report.status === 'completed'" command="regenerate">
                  重新生成
                </el-dropdown-item>
                <el-dropdown-item command="share">分享报告</el-dropdown-item>
                <el-dropdown-item command="export">导出</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除报告</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- Progress (if generating) -->
      <el-card v-if="report.status === 'generating'" class="progress-card">
        <div class="progress-info">
          <div class="progress-text">
            <span>报告生成中</span>
            <span>请稍候...</span>
          </div>
          <el-progress :percentage="75" :indeterminate="true" :stroke-width="8" />
        </div>
      </el-card>

      <!-- Statistics -->
      <el-row v-if="report.statistics" :gutter="16" class="overview-cards">
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ report.statistics.total_pages || 0 }}</div>
              <div class="stat-label">总页数</div>
            </div>
            <el-icon class="stat-icon"><Document /></el-icon>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ report.statistics.findings_count || 0 }}</div>
              <div class="stat-label">发现问题</div>
            </div>
            <el-icon class="stat-icon"><Warning /></el-icon>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ report.download_count || 0 }}</div>
              <div class="stat-label">下载次数</div>
            </div>
            <el-icon class="stat-icon"><Download /></el-icon>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ formatFileSize(report.file_size) }}</div>
              <div class="stat-label">文件大小</div>
            </div>
            <el-icon class="stat-icon"><Files /></el-icon>
          </el-card>
        </el-col>
      </el-row>

      <!-- Main Content -->
      <el-row :gutter="16">
        <el-col :xs="24" :lg="16">
          <!-- Details -->
          <el-card>
            <el-tabs v-model="activeTab">
              <!-- Overview -->
              <el-tab-pane label="报告概览" name="overview">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="报告标题" :span="2">
                    {{ report.title }}
                  </el-descriptions-item>
                  <el-descriptions-item label="报告类型">
                    <el-tag :type="getTypeTagType(report.type)">
                      {{ getTypeLabel(report.type) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag :type="getStatusTagType(report.status)">
                      {{ getStatusLabel(report.status) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="密级">
                    <el-tag :type="getClassificationTagType(report.classification)">
                      {{ getClassificationLabel(report.classification) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="模板">
                    {{ report.template }}
                  </el-descriptions-item>
                  <el-descriptions-item label="语言">
                    {{ report.language === 'zh-CN' ? '中文' : 'English' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="输出格式">
                    <el-tag v-for="fmt in report.format" :key="fmt" style="margin-right: 4px">
                      {{ fmt.toUpperCase() }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="创建时间">
                    {{ formatDate(report.created_at) }}
                  </el-descriptions-item>
                  <el-descriptions-item v-if="report.generated_at" label="生成时间">
                    {{ formatDate(report.generated_at) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="创建者">
                    {{ report.created_by || '系统' }}
                  </el-descriptions-item>
                  <el-descriptions-item v-if="report.last_accessed" label="最后访问">
                    {{ formatDate(report.last_accessed, 'relative') }}
                  </el-descriptions-item>
                  <el-descriptions-item v-if="report.description" label="描述" :span="2">
                    {{ report.description }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>

              <!-- Config -->
              <el-tab-pane label="配置信息" name="config">
                <div class="config-display">
                  <el-descriptions title="报告配置" :column="1" border>
                    <el-descriptions-item label="时间范围">
                      {{ getDateRangeLabel(report.config) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="包含章节">
                      <el-tag
                        v-for="section in report.config.sections"
                        :key="section"
                        size="small"
                        style="margin-right: 4px"
                      >
                        {{ getSectionLabel(section) }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="包含图表">
                      {{ report.config.include_charts ? '是' : '否' }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-tab-pane>

              <!-- Files -->
              <el-tab-pane v-if="report.files && report.files.length" label="文件列表" name="files">
                <el-table :data="report.files" stripe>
                  <el-table-column prop="name" label="文件名" min-width="200" />
                  <el-table-column prop="format" label="格式" width="80">
                    <template #default="{ row }">
                      <el-tag size="small">{{ row.format.toUpperCase() }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="size" label="大小" width="100">
                    <template #default="{ row }">
                      {{ formatFileSize(row.size) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="created_at" label="创建时间" width="150">
                    <template #default="{ row }">
                      {{ formatDate(row.created_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="100">
                    <template #default="{ row }">
                      <el-button size="small" type="primary" @click="downloadFile(row)">
                        下载
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>

              <!-- Statistics -->
              <el-tab-pane v-if="report.statistics" label="统计信息" name="statistics">
                <div class="statistics-section">
                  <el-descriptions title="统计数据" :column="2" border>
                    <el-descriptions-item label="总页数">
                      {{ report.statistics.total_pages }}
                    </el-descriptions-item>
                    <el-descriptions-item label="发现总数">
                      {{ report.statistics.findings_count }}
                    </el-descriptions-item>
                    <el-descriptions-item label="资产数量">
                      {{ report.statistics.assets_count }}
                    </el-descriptions-item>
                    <el-descriptions-item label="漏洞数量">
                      {{ report.statistics.vulnerabilities_count }}
                    </el-descriptions-item>
                    <el-descriptions-item label="任务数量">
                      {{ report.statistics.tasks_count }}
                    </el-descriptions-item>
                    <el-descriptions-item label="严重问题">
                      <el-tag type="danger">{{ report.statistics.critical_issues }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="高危问题">
                      <el-tag type="warning">{{ report.statistics.high_issues }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="中危问题">
                      <el-tag type="info">{{ report.statistics.medium_issues }}</el-tag>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8">
          <!-- Actions -->
          <el-card class="actions-card">
            <template #header>
              <h3>快速操作</h3>
            </template>
            <div class="quick-actions">
              <el-button
                type="primary"
                block
                :disabled="report.status !== 'completed'"
                @click="handleDownload"
              >
                <el-icon><Download /></el-icon>
                下载报告
              </el-button>
              <el-button block :disabled="report.status !== 'completed'" @click="handlePreview">
                <el-icon><View /></el-icon>
                在线预览
              </el-button>
              <el-button block :disabled="report.status !== 'completed'" @click="handleShare">
                <el-icon><Share /></el-icon>
                分享报告
              </el-button>
            </div>
          </el-card>

          <!-- Info -->
          <el-card class="info-card">
            <template #header>
              <h3>访问统计</h3>
            </template>
            <div class="access-stats">
              <div class="stat-item">
                <span class="label">查看次数</span>
                <span class="value">{{ report.view_count || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="label">下载次数</span>
                <span class="value">{{ report.download_count || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="label">分享次数</span>
                <span class="value">{{ report.share_count || 0 }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    <div v-else-if="!loading" class="empty-state">
      <el-empty description="报告不存在">
        <el-button type="primary" @click="$router.push('/reports')">返回报告列表</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useReportStore } from '@/store/report'
import { formatDate } from '@/utils/date'

const route = useRoute()
const router = useRouter()
const reportStore = useReportStore()

const loading = ref(false)
const actionLoading = ref(false)
const error = ref(false)
const report = ref(null)
const activeTab = ref('overview')

onMounted(async () => {
  await loadReport()
})

const loadReport = async () => {
  loading.value = true
  error.value = false
  try {
    report.value = await reportStore.getReport(route.params.id)
  } catch (err) {
    console.error('Failed to load report:', err)
    error.value = true
    ElMessage.error('加载报告信息失败')
  } finally {
    loading.value = false
  }
}

const retry = () => {
  loadReport()
}

const handleDownload = async () => {
  actionLoading.value = true
  try {
    const blob = await reportStore.downloadReport(report.value.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${report.value.title}.${report.value.format[0] || 'pdf'}`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  } finally {
    actionLoading.value = false
  }
}

const handlePreview = async () => {
  try {
    const url = await reportStore.getPreviewUrl(report.value.id)
    window.open(url, '_blank')
  } catch (error) {
    ElMessage.error('预览功能暂不可用')
  }
}

const handleShare = async () => {
  ElMessage.info('分享功能开发中')
}

const handleCommand = async command => {
  switch (command) {
    case 'regenerate':
      await handleRegenerate()
      break
    case 'share':
      await handleShare()
      break
    case 'export':
      await handleDownload()
      break
    case 'delete':
      await handleDelete()
      break
  }
}

const handleRegenerate = async () => {
  await ElMessageBox.confirm('确定要重新生成这个报告吗？', '确认', {
    type: 'info'
  })
  try {
    await reportStore.regenerateReport(report.value.id)
    ElMessage.success('报告生成任务已启动')
    loadReport()
  } catch (error) {
    ElMessage.error('启动失败')
  }
}

const handleDelete = async () => {
  await ElMessageBox.confirm('确定要删除这个报告吗？删除后无法恢复。', '确认删除', {
    type: 'warning'
  })
  try {
    await reportStore.deleteReport(report.value.id)
    ElMessage.success('删除成功')
    router.push('/reports')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const downloadFile = async file => {
  ElMessage.info(`下载文件: ${file.name}`)
}

const formatFileSize = bytes => {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

const getDateRangeLabel = config => {
  if (config.period) {
    const labels = {
      last_7_days: '最近7天',
      last_30_days: '最近30天',
      last_90_days: '最近90天',
      this_month: '本月',
      last_month: '上月',
      all_time: '全部时间'
    }
    return labels[config.period] || config.period
  }
  if (config.date_range) {
    return `${config.date_range[0]} ~ ${config.date_range[1]}`
  }
  return '未指定'
}

const getSectionLabel = section => {
  const labels = {
    summary: '概览摘要',
    assets: '资产信息',
    vulnerabilities: '漏洞详情',
    tasks: '扫描任务',
    trends: '趋势分析',
    recommendations: '修复建议'
  }
  return labels[section] || section
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
.report-detail {
  .report-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--el-border-color-light);

    .header-left {
      flex: 1;

      h1 {
        font-size: 28px;
        margin-bottom: 12px;
        color: var(--el-text-color-primary);
      }

      .report-meta {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
    }

    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }

  .progress-card {
    margin-bottom: 16px;
  }

  .overview-cards {
    margin-bottom: 16px;

    .stat-card {
      position: relative;
      overflow: hidden;

      :deep(.el-card__body) {
        padding: 20px;
      }

      .stat-content {
        position: relative;
        z-index: 2;

        .stat-number {
          font-size: 28px;
          font-weight: bold;
          color: var(--el-color-primary);
          margin-bottom: 8px;
        }

        .stat-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
        }
      }

      .stat-icon {
        position: absolute;
        right: 20px;
        bottom: 20px;
        font-size: 48px;
        color: var(--el-color-primary);
        opacity: 0.15;
      }
    }
  }

  .actions-card,
  .info-card {
    margin-bottom: 16px;

    h3 {
      margin: 0;
      font-size: 16px;
      color: var(--el-text-color-primary);
    }
  }

  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .access-stats {
    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);

      &:last-child {
        border-bottom: none;
      }

      .label {
        color: var(--el-text-color-regular);
      }

      .value {
        font-size: 18px;
        font-weight: bold;
        color: var(--el-color-primary);
      }
    }
  }
}

@media (max-width: 768px) {
  .report-detail .report-header {
    flex-direction: column;
    gap: 16px;

    .header-actions {
      width: 100%;
      justify-content: flex-start;
      flex-wrap: wrap;
    }
  }
}
</style>
