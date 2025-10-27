<template>
  <div class="stat-card" :style="{ '--accent-color': color }">
    <div class="stat-icon">
      <component :is="iconComponent" />
    </div>
    <div class="stat-content">
      <div class="stat-title">{{ title }}</div>
      <div class="stat-value" v-if="!loading">
        <CountUp :end-val="numericValue" :duration="2" />
        <span v-if="suffix" class="stat-suffix">{{ suffix }}</span>
      </div>
      <el-skeleton v-else animated>
        <template #default>
          <div class="stat-value">--</div>
        </template>
      </el-skeleton>
      <div class="stat-change" :class="changeClass">
        <el-icon v-if="changeDirection">
          <component :is="changeDirection === 'up' ? 'TrendCharts' : 'Bottom'" />
        </el-icon>
        {{ change }}
      </div>
    </div>
    <div class="stat-chart">
      <canvas ref="miniChart"></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  Monitor,
  WarnTriangleFilled,
  Bell,
  CircleCheckFilled,
  TrendCharts,
  Bottom
} from '@element-plus/icons-vue'
import CountUp from 'vue-countup-v3'
import Chart from 'chart.js/auto'

interface Props {
  title: string
  value: string | number
  change?: string
  icon?: string
  color?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  change: '',
  icon: 'Monitor',
  color: '#409EFF',
  loading: false
})

const miniChart = ref<HTMLCanvasElement>()
let chartInstance: Chart | null = null

// 图标映射
const iconMap = {
  Monitor,
  WarnTriangleFilled,
  Bell,
  CircleCheckFilled
}

const iconComponent = computed(() => iconMap[props.icon] || Monitor)

// 提取数值和后缀
const numericValue = computed(() => {
  const value = String(props.value)
  const match = value.match(/^([\d,]+\.?\d*)(.*)$/)
  if (match) {
    return parseFloat(match[1].replace(/,/g, ''))
  }
  return 0
})

const suffix = computed(() => {
  const value = String(props.value)
  const match = value.match(/^[\d,]+\.?\d*(.*)$/)
  return match ? match[1] : ''
})

// 变化方向
const changeDirection = computed(() => {
  if (!props.change) return null
  return props.change.startsWith('+') ? 'up' : props.change.startsWith('-') ? 'down' : null
})

const changeClass = computed(() => {
  if (!changeDirection.value) return ''
  return changeDirection.value === 'up' ? 'positive' : 'negative'
})

// 创建迷你图表
const createMiniChart = () => {
  if (!miniChart.value) return

  const ctx = miniChart.value.getContext('2d')
  if (!ctx) return

  // 生成模拟数据
  const data = Array.from({ length: 7 }, () => Math.random() * 100)

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['', '', '', '', '', '', ''],
      datasets: [{
        data,
        borderColor: props.color,
        backgroundColor: `${props.color}20`,
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }
      },
      scales: {
        x: { display: false },
        y: { display: false }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    }
  })
}

// 更新图表
const updateChart = () => {
  if (chartInstance) {
    const newData = Array.from({ length: 7 }, () => Math.random() * 100)
    chartInstance.data.datasets[0].data = newData
    chartInstance.update('none')
  }
}

onMounted(() => {
  createMiniChart()
})

watch(() => props.value, () => {
  updateChart()
})
</script>

<style lang="scss" scoped>
.stat-card {
  --accent-color: #409EFF;
  background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
  border-radius: 16px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border: 1px solid rgba(0, 0, 0, 0.05);

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--accent-color);
    transition: width 0.3s ease;
  }

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);

    &::before {
      width: 8px;
    }

    .stat-icon {
      transform: scale(1.1) rotate(5deg);
    }
  }

  .stat-icon {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, var(--accent-color), var(--accent-color)dd);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

    :deep(.el-icon) {
      font-size: 28px;
      color: white;
    }
  }

  .stat-content {
    position: relative;
    z-index: 1;

    .stat-title {
      font-size: 14px;
      color: #909399;
      margin-bottom: 12px;
      font-weight: 500;
      letter-spacing: 0.5px;
    }

    .stat-value {
      font-size: 32px;
      font-weight: 700;
      color: #303133;
      line-height: 1.2;
      margin-bottom: 8px;
      display: flex;
      align-items: baseline;
      gap: 4px;

      .stat-suffix {
        font-size: 20px;
        font-weight: 500;
        color: #606266;
      }
    }

    .stat-change {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 14px;
      font-weight: 500;
      padding: 4px 8px;
      border-radius: 6px;
      transition: all 0.3s ease;

      &.positive {
        color: #67C23A;
        background: rgba(103, 194, 58, 0.1);
      }

      &.negative {
        color: #F56C6C;
        background: rgba(245, 108, 108, 0.1);
      }

      .el-icon {
        font-size: 12px;
      }
    }
  }

  .stat-chart {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    opacity: 0.3;
    transition: opacity 0.3s ease;

    canvas {
      width: 100% !important;
      height: 100% !important;
    }
  }

  &:hover .stat-chart {
    opacity: 0.5;
  }
}

// 加载动画
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

// 暗黑模式
@media (prefers-color-scheme: dark) {
  .stat-card {
    background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
    border-color: rgba(255, 255, 255, 0.1);

    .stat-content {
      .stat-title {
        color: #909399;
      }

      .stat-value {
        color: #f0f0f0;

        .stat-suffix {
          color: #b0b0b0;
        }
      }
    }
  }
}

// 响应式
@media (max-width: 768px) {
  .stat-card {
    padding: 20px;

    .stat-icon {
      width: 50px;
      height: 50px;

      :deep(.el-icon) {
        font-size: 24px;
      }
    }

    .stat-content {
      .stat-value {
        font-size: 28px;

        .stat-suffix {
          font-size: 18px;
        }
      }
    }
  }
}
</style>