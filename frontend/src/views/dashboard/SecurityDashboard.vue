<template>
  <div class="security-dashboard">
    <!-- 顶部统计卡片 -->
    <div class="stats-grid">
      <StatCard
        v-for="stat in statsData"
        :key="stat.id"
        :title="stat.title"
        :value="stat.value"
        :change="stat.change"
        :icon="stat.icon"
        :color="stat.color"
        :loading="loading"
      />
    </div>

    <!-- 实时威胁地图和告警 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xl="16" :lg="16" :md="24" :sm="24">
        <div class="chart-card">
          <div class="card-header">
            <h3>
              <el-icon><LocationInformation /></el-icon>
              实时威胁地图
            </h3>
            <div class="header-actions">
              <el-button-group>
                <el-button size="small" :type="mapView === 'world' ? 'primary' : ''" @click="mapView = 'world'">
                  全球
                </el-button>
                <el-button size="small" :type="mapView === 'china' ? 'primary' : ''" @click="mapView = 'china'">
                  中国
                </el-button>
              </el-button-group>
            </div>
          </div>
          <ThreatMap :view="mapView" :data="threatMapData" />
        </div>
      </el-col>

      <el-col :xl="8" :lg="8" :md="24" :sm="24">
        <div class="chart-card alerts-card">
          <div class="card-header">
            <h3>
              <el-icon><Bell /></el-icon>
              最新告警
              <el-badge :value="newAlertsCount" :max="99" class="alert-badge" />
            </h3>
            <el-link type="primary" :underline="false" @click="viewAllAlerts">
              查看全部 <el-icon><ArrowRight /></el-icon>
            </el-link>
          </div>
          <AlertsList :alerts="latestAlerts" :loading="loading" />
        </div>
      </el-col>
    </el-row>

    <!-- 漏洞分布和资产状态 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xl="8" :lg="8" :md="12" :sm="24">
        <div class="chart-card">
          <div class="card-header">
            <h3>
              <el-icon><WarnTriangleFilled /></el-icon>
              漏洞分布
            </h3>
            <el-dropdown>
              <el-button text>
                <el-icon><More /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="exportVulnerabilities">导出数据</el-dropdown-item>
                  <el-dropdown-item @click="refreshVulnerabilities">刷新</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <VulnerabilityChart :data="vulnerabilityData" />
        </div>
      </el-col>

      <el-col :xl="8" :lg="8" :md="12" :sm="24">
        <div class="chart-card">
          <div class="card-header">
            <h3>
              <el-icon><Monitor /></el-icon>
              资产状态
            </h3>
            <el-tag size="small" effect="plain">
              更新于 {{ lastUpdateTime }}
            </el-tag>
          </div>
          <AssetStatusChart :data="assetStatusData" />
        </div>
      </el-col>

      <el-col :xl="8" :lg="8" :md="24" :sm="24">
        <div class="chart-card">
          <div class="card-header">
            <h3>
              <el-icon><TrendCharts /></el-icon>
              安全趋势
            </h3>
            <el-radio-group v-model="trendPeriod" size="small">
              <el-radio-button label="7d">7天</el-radio-button>
              <el-radio-button label="30d">30天</el-radio-button>
              <el-radio-button label="90d">90天</el-radio-button>
            </el-radio-group>
          </div>
          <SecurityTrendChart :period="trendPeriod" :data="trendData" />
        </div>
      </el-col>
    </el-row>

    <!-- 扫描任务和合规状态 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xl="12" :lg="12" :md="24" :sm="24">
        <div class="chart-card">
          <div class="card-header">
            <h3>
              <el-icon><Search /></el-icon>
              扫描任务
            </h3>
            <el-button type="primary" size="small" @click="createScan">
              <el-icon><Plus /></el-icon>
              新建扫描
            </el-button>
          </div>
          <ScanTasksTable :tasks="scanTasks" :loading="loading" />
        </div>
      </el-col>

      <el-col :xl="12" :lg="12" :md="24" :sm="24">
        <div class="chart-card">
          <div class="card-header">
            <h3>
              <el-icon><CircleCheckFilled /></el-icon>
              合规状态
            </h3>
            <el-select v-model="selectedFramework" size="small" placeholder="选择框架">
              <el-option label="全部" value="all" />
              <el-option label="GDPR" value="gdpr" />
              <el-option label="HIPAA" value="hipaa" />
              <el-option label="PCI-DSS" value="pci-dss" />
              <el-option label="SOC2" value="soc2" />
            </el-select>
          </div>
          <ComplianceChart :framework="selectedFramework" :data="complianceData" />
        </div>
      </el-col>
    </el-row>

    <!-- 威胁情报和团队活动 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xl="16" :lg="16" :md="24" :sm="24">
        <div class="chart-card">
          <div class="card-header">
            <h3>
              <el-icon><InfoFilled /></el-icon>
              威胁情报
            </h3>
            <div class="header-actions">
              <el-input
                v-model="threatSearch"
                size="small"
                placeholder="搜索威胁..."
                :prefix-icon="Search"
                style="width: 200px"
              />
            </div>
          </div>
          <ThreatIntelligence :search="threatSearch" :data="threatIntelData" />
        </div>
      </el-col>

      <el-col :xl="8" :lg="8" :md="24" :sm="24">
        <div class="chart-card">
          <div class="card-header">
            <h3>
              <el-icon><User /></el-icon>
              团队活动
            </h3>
          </div>
          <TeamActivity :activities="teamActivities" />
        </div>
      </el-col>
    </el-row>

    <!-- 快速操作悬浮按钮 -->
    <div class="quick-actions">
      <el-tooltip content="快速扫描" placement="left">
        <el-button type="primary" :icon="Search" circle size="large" @click="quickScan" />
      </el-tooltip>
      <el-tooltip content="生成报告" placement="left">
        <el-button type="success" :icon="Document" circle size="large" @click="generateReport" />
      </el-tooltip>
      <el-tooltip content="紧急响应" placement="left">
        <el-button type="danger" :icon="WarnTriangleFilled" circle size="large" @click="emergencyResponse" />
      </el-tooltip>
    </div>

    <!-- WebSocket 实时连接状态 -->
    <div class="connection-status" :class="{ connected: wsConnected }">
      <el-icon :class="{ pulse: wsConnected }">
        <Connection />
      </el-icon>
      <span>{{ wsConnected ? '实时连接' : '连接断开' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  LocationInformation,
  Bell,
  ArrowRight,
  WarnTriangleFilled,
  Monitor,
  TrendCharts,
  Search,
  Plus,
  CircleCheckFilled,
  InfoFilled,
  User,
  Document,
  Connection,
  More
} from '@element-plus/icons-vue'

// 导入组件
import StatCard from '@/components/dashboard/StatCard.vue'
import ThreatMap from '@/components/dashboard/ThreatMap.vue'
import AlertsList from '@/components/dashboard/AlertsList.vue'
import VulnerabilityChart from '@/components/dashboard/VulnerabilityChart.vue'
import AssetStatusChart from '@/components/dashboard/AssetStatusChart.vue'
import SecurityTrendChart from '@/components/dashboard/SecurityTrendChart.vue'
import ScanTasksTable from '@/components/dashboard/ScanTasksTable.vue'
import ComplianceChart from '@/components/dashboard/ComplianceChart.vue'
import ThreatIntelligence from '@/components/dashboard/ThreatIntelligence.vue'
import TeamActivity from '@/components/dashboard/TeamActivity.vue'

// 导入API和工具
import { getDashboardStats, getLatestAlerts, getThreatMap } from '@/api/dashboard'
import { useWebSocket } from '@/hooks/useWebSocket'
import { formatTime } from '@/utils/format'

const router = useRouter()
const loading = ref(false)
const wsConnected = ref(false)

// 统计数据
const statsData = ref([
  {
    id: 1,
    title: '总资产',
    value: '1,234',
    change: '+12%',
    icon: 'Monitor',
    color: '#409EFF'
  },
  {
    id: 2,
    title: '高危漏洞',
    value: '56',
    change: '-8%',
    icon: 'WarnTriangleFilled',
    color: '#F56C6C'
  },
  {
    id: 3,
    title: '今日告警',
    value: '89',
    change: '+23%',
    icon: 'Bell',
    color: '#E6A23C'
  },
  {
    id: 4,
    title: '合规率',
    value: '94.5%',
    change: '+2.3%',
    icon: 'CircleCheckFilled',
    color: '#67C23A'
  }
])

// 地图视图
const mapView = ref('world')
const threatMapData = ref([])

// 告警数据
const newAlertsCount = ref(12)
const latestAlerts = ref([])

// 图表数据
const vulnerabilityData = ref({})
const assetStatusData = ref({})
const trendPeriod = ref('7d')
const trendData = ref({})
const scanTasks = ref([])
const selectedFramework = ref('all')
const complianceData = ref({})
const threatSearch = ref('')
const threatIntelData = ref([])
const teamActivities = ref([])

// 时间相关
const lastUpdateTime = computed(() => formatTime(new Date()))

// WebSocket连接
const { connect, disconnect, subscribe } = useWebSocket()

// 初始化数据
const initDashboard = async () => {
  loading.value = true
  try {
    // 获取统计数据
    const stats = await getDashboardStats()
    if (stats) {
      statsData.value = stats
    }

    // 获取最新告警
    const alerts = await getLatestAlerts()
    if (alerts) {
      latestAlerts.value = alerts
      newAlertsCount.value = alerts.filter(a => !a.read).length
    }

    // 获取威胁地图数据
    const mapData = await getThreatMap()
    if (mapData) {
      threatMapData.value = mapData
    }

    // 加载其他图表数据
    await loadChartData()
  } catch (error) {
    console.error('Failed to load dashboard:', error)
    ElMessage.error('加载仪表板数据失败')
  } finally {
    loading.value = false
  }
}

// 加载图表数据
const loadChartData = async () => {
  // 这里加载各种图表数据
  vulnerabilityData.value = {
    critical: 12,
    high: 45,
    medium: 89,
    low: 156,
    info: 234
  }

  assetStatusData.value = {
    online: 892,
    offline: 45,
    warning: 23,
    error: 8
  }

  // 模拟数据，实际应该从API获取
  scanTasks.value = [
    {
      id: 1,
      name: '主网站安全扫描',
      target: 'www.example.com',
      status: 'running',
      progress: 65
    },
    {
      id: 2,
      name: 'API接口测试',
      target: 'api.example.com',
      status: 'completed',
      progress: 100
    }
  ]
}

// 建立WebSocket连接
const setupWebSocket = () => {
  connect()

  // 订阅实时数据
  subscribe('alerts', (data) => {
    latestAlerts.value.unshift(data)
    if (latestAlerts.value.length > 10) {
      latestAlerts.value.pop()
    }
    newAlertsCount.value++
  })

  subscribe('stats', (data) => {
    statsData.value = data
  })

  subscribe('threats', (data) => {
    threatMapData.value.push(data)
  })

  wsConnected.value = true
}

// 操作函数
const viewAllAlerts = () => {
  router.push('/alerts')
}

const createScan = () => {
  router.push('/scans/create')
}

const quickScan = () => {
  ElMessage.info('启动快速扫描...')
}

const generateReport = () => {
  router.push('/reports/generate')
}

const emergencyResponse = () => {
  router.push('/incidents/create')
}

const exportVulnerabilities = () => {
  ElMessage.success('导出漏洞数据...')
}

const refreshVulnerabilities = () => {
  loadChartData()
  ElMessage.success('数据已刷新')
}

// 生命周期
onMounted(() => {
  initDashboard()
  setupWebSocket()

  // 定时刷新数据
  const refreshInterval = setInterval(() => {
    initDashboard()
  }, 60000) // 每分钟刷新

  onUnmounted(() => {
    clearInterval(refreshInterval)
    disconnect()
  })
})
</script>

<style lang="scss" scoped>
.security-dashboard {
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  position: relative;

  // 统计卡片网格
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 24px;
  }

  // 图表行
  .chart-row {
    margin-bottom: 20px;
  }

  // 通用卡片样式
  .chart-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    height: 100%;
    display: flex;
    flex-direction: column;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 2px solid #f0f2f5;

      h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #303133;
        display: flex;
        align-items: center;
        gap: 8px;

        .el-icon {
          font-size: 20px;
        }
      }

      .header-actions {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .alert-badge {
        margin-left: 8px;
      }
    }

    // 告警卡片特殊样式
    &.alerts-card {
      max-height: 450px;
      overflow: hidden;
    }
  }

  // 快速操作按钮
  .quick-actions {
    position: fixed;
    bottom: 40px;
    right: 40px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    z-index: 999;

    .el-button {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      transition: all 0.3s ease;

      &:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
      }
    }
  }

  // WebSocket连接状态
  .connection-status {
    position: fixed;
    top: 80px;
    right: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    font-size: 12px;
    color: #909399;
    transition: all 0.3s ease;
    z-index: 100;

    &.connected {
      color: #67C23A;
      background: rgba(103, 194, 58, 0.1);
    }

    .el-icon {
      &.pulse {
        animation: pulse 2s infinite;
      }
    }
  }

  // 脉冲动画
  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
    100% {
      opacity: 1;
    }
  }

  // 响应式设计
  @media (max-width: 768px) {
    padding: 12px;

    .stats-grid {
      grid-template-columns: 1fr;
    }

    .quick-actions {
      bottom: 20px;
      right: 20px;
    }

    .connection-status {
      top: auto;
      bottom: 20px;
      left: 20px;
      right: auto;
    }
  }
}

// 暗黑模式支持
@media (prefers-color-scheme: dark) {
  .security-dashboard {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);

    .chart-card {
      background: rgba(30, 30, 30, 0.95);
      color: #fff;

      .card-header {
        border-bottom-color: #404040;

        h3 {
          color: #f0f0f0;
        }
      }
    }

    .connection-status {
      background: rgba(30, 30, 30, 0.9);
      color: #a0a0a0;

      &.connected {
        background: rgba(103, 194, 58, 0.2);
      }
    }
  }
}
</style>