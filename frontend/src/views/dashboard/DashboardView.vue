<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>安全态势总览</h1>
      <p>实时监控您的安全资产和威胁态势</p>
    </div>

    <!-- Statistics Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon assets">
            <el-icon><List /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.totalAssets }}</h3>
            <p>总资产数</p>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon vulnerabilities">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.totalVulnerabilities }}</h3>
            <p>发现漏洞</p>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon tasks">
            <el-icon><Operation /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.runningTasks }}</h3>
            <p>运行任务</p>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon reports">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.recentReports }}</h3>
            <p>最近报告</p>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Charts Row -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <h3>漏洞严重程度分布</h3>
          </template>
          <div ref="severityChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <h3>扫描任务趋势</h3>
          </template>
          <div ref="taskChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Activities -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="16">
        <el-card class="activity-card">
          <template #header>
            <h3>最近活动</h3>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="activity in activities"
              :key="activity.id"
              :timestamp="activity.timestamp"
              :type="activity.type"
            >
              {{ activity.description }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="quick-actions-card">
          <template #header>
            <h3>快速操作</h3>
          </template>
          <div class="quick-actions">
            <el-button
              type="primary"
              size="large"
              @click="$router.push('/assets/create')"
            >
              <el-icon><Plus /></el-icon>
              添加资产
            </el-button>
            <el-button
              type="success"
              size="large"
              @click="$router.push('/tasks/create')"
            >
              <el-icon><Operation /></el-icon>
              创建扫描
            </el-button>
            <el-button
              type="warning"
              size="large"
              @click="$router.push('/reports/create')"
            >
              <el-icon><Document /></el-icon>
              生成报告
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const stats = ref({
  totalAssets: 1250,
  totalVulnerabilities: 89,
  runningTasks: 5,
  recentReports: 12
})

const activities = ref([
  {
    id: 1,
    description: '完成了域名 example.com 的端口扫描',
    timestamp: '2024-01-15 14:30',
    type: 'success'
  },
  {
    id: 2,
    description: '发现高危漏洞：SQL注入漏洞',
    timestamp: '2024-01-15 13:45',
    type: 'danger'
  },
  {
    id: 3,
    description: '生成了周度安全报告',
    timestamp: '2024-01-15 10:20',
    type: 'info'
  },
  {
    id: 4,
    description: '导入了150个新资产',
    timestamp: '2024-01-15 09:15',
    type: 'success'
  }
])

const severityChart = ref()
const taskChart = ref()

onMounted(async () => {
  await nextTick()
  initCharts()
})

const initCharts = () => {
  // Severity Distribution Chart
  if (severityChart.value) {
    const severityChartInstance = echarts.init(severityChart.value)
    severityChartInstance.setOption({
      tooltip: {
        trigger: 'item'
      },
      series: [
        {
          type: 'pie',
          radius: '70%',
          data: [
            { value: 5, name: '严重', itemStyle: { color: '#f56c6c' } },
            { value: 15, name: '高危', itemStyle: { color: '#e6a23c' } },
            { value: 35, name: '中危', itemStyle: { color: '#409eff' } },
            { value: 34, name: '低危', itemStyle: { color: '#67c23a' } }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    })
  }

  // Task Trend Chart
  if (taskChart.value) {
    const taskChartInstance = echarts.init(taskChart.value)
    taskChartInstance.setOption({
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          type: 'line',
          data: [8, 12, 15, 10, 18, 6, 9],
          smooth: true,
          itemStyle: { color: '#409eff' },
          areaStyle: { opacity: 0.3 }
        }
      ]
    })
  }
}
</script>

<style scoped lang="scss">
.dashboard {
  .dashboard-header {
    margin-bottom: 30px;

    h1 {
      font-size: 28px;
      margin-bottom: 8px;
      color: var(--el-text-color-primary);
    }

    p {
      color: var(--el-text-color-regular);
      margin: 0;
    }
  }

  .stats-row {
    margin-bottom: 30px;

    .stat-card {
      background: var(--el-bg-color);
      border-radius: 8px;
      padding: 20px;
      display: flex;
      align-items: center;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      transition: transform 0.3s;

      &:hover {
        transform: translateY(-2px);
      }

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;

        .el-icon {
          font-size: 24px;
          color: white;
        }

        &.assets {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        &.vulnerabilities {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        &.tasks {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }

        &.reports {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }

      .stat-content {
        h3 {
          font-size: 32px;
          font-weight: bold;
          margin-bottom: 5px;
          color: var(--el-text-color-primary);
        }

        p {
          color: var(--el-text-color-regular);
          margin: 0;
          font-size: 14px;
        }
      }
    }
  }

  .charts-row {
    margin-bottom: 30px;

    .chart-card {
      .chart-container {
        height: 300px;
      }
    }
  }

  .activity-card {
    height: 400px;

    .el-timeline {
      max-height: 320px;
      overflow-y: auto;
    }
  }

  .quick-actions-card {
    height: 400px;

    .quick-actions {
      display: flex;
      flex-direction: column;
      gap: 15px;

      .el-button {
        height: 50px;
        font-size: 16px;

        .el-icon {
          margin-right: 8px;
        }
      }
    }
  }
}
</style>