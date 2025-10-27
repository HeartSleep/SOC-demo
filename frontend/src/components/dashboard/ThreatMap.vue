<template>
  <div class="threat-map-container">
    <div ref="mapContainer" class="map-canvas"></div>

    <!-- 威胁统计悬浮面板 -->
    <div class="threat-stats">
      <div class="stat-item" v-for="stat in threatStats" :key="stat.type">
        <div class="stat-icon" :style="{ background: stat.color }">
          <el-icon><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ stat.value }}</div>
        </div>
      </div>
    </div>

    <!-- 实时攻击动画 -->
    <div class="attack-lines" v-if="showAttackLines">
      <svg class="attack-svg">
        <defs>
          <linearGradient id="attackGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#ff6b6b;stop-opacity:0" />
            <stop offset="50%" style="stop-color:#ff6b6b;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#ff6b6b;stop-opacity:0" />
          </linearGradient>
        </defs>
        <line
          v-for="attack in activeAttacks"
          :key="attack.id"
          :x1="attack.x1"
          :y1="attack.y1"
          :x2="attack.x2"
          :y2="attack.y2"
          class="attack-line"
          stroke="url(#attackGradient)"
        />
      </svg>
    </div>

    <!-- 图例 -->
    <div class="map-legend">
      <div class="legend-title">威胁等级</div>
      <div class="legend-items">
        <div class="legend-item" v-for="level in threatLevels" :key="level.name">
          <span class="legend-color" :style="{ background: level.color }"></span>
          <span class="legend-label">{{ level.name }}</span>
          <span class="legend-count">({{ level.count }})</span>
        </div>
      </div>
    </div>

    <!-- 控制面板 -->
    <div class="map-controls">
      <el-tooltip content="热力图" placement="left">
        <el-button
          :type="viewMode === 'heatmap' ? 'primary' : ''"
          :icon="Grid"
          circle
          @click="viewMode = 'heatmap'"
        />
      </el-tooltip>
      <el-tooltip content="标记点" placement="left">
        <el-button
          :type="viewMode === 'markers' ? 'primary' : ''"
          :icon="Location"
          circle
          @click="viewMode = 'markers'"
        />
      </el-tooltip>
      <el-tooltip content="攻击线" placement="left">
        <el-button
          :type="showAttackLines ? 'primary' : ''"
          :icon="Connection"
          circle
          @click="showAttackLines = !showAttackLines"
        />
      </el-tooltip>
      <el-tooltip content="全屏" placement="left">
        <el-button :icon="FullScreen" circle @click="toggleFullscreen" />
      </el-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import 'echarts/extension/bmap/bmap'
import {
  Grid,
  Location,
  Connection,
  FullScreen,
  WarnTriangleFilled,
  CircleCheckFilled,
  InfoFilled
} from '@element-plus/icons-vue'

interface Props {
  view?: 'world' | 'china'
  data?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  view: 'world',
  data: () => []
})

const mapContainer = ref<HTMLDivElement>()
const viewMode = ref<'heatmap' | 'markers'>('heatmap')
const showAttackLines = ref(true)
let mapInstance: echarts.ECharts | null = null

// 威胁统计
const threatStats = ref([
  {
    type: 'critical',
    label: '严重威胁',
    value: '23',
    color: '#ff4757',
    icon: 'WarnTriangleFilled'
  },
  {
    type: 'active',
    label: '活跃攻击',
    value: '156',
    color: '#ffa502',
    icon: 'InfoFilled'
  },
  {
    type: 'blocked',
    label: '已拦截',
    value: '1,234',
    color: '#26de81',
    icon: 'CircleCheckFilled'
  }
])

// 威胁等级
const threatLevels = ref([
  { name: '严重', color: '#ff4757', count: 23 },
  { name: '高危', color: '#ff6348', count: 45 },
  { name: '中危', color: '#ffa502', count: 89 },
  { name: '低危', color: '#fdcb6e', count: 156 },
  { name: '信息', color: '#74b9ff', count: 234 }
])

// 活跃攻击线
const activeAttacks = ref<any[]>([])

// 初始化地图
const initMap = () => {
  if (!mapContainer.value) return

  mapInstance = echarts.init(mapContainer.value, 'dark')

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `
          <div style="padding: 10px;">
            <div style="font-weight: bold; margin-bottom: 5px;">${params.name}</div>
            <div>威胁等级: ${params.data?.level || '未知'}</div>
            <div>攻击次数: ${params.data?.count || 0}</div>
            <div>最后活动: ${params.data?.lastActive || '无'}</div>
          </div>
        `
      }
    },
    visualMap: {
      min: 0,
      max: 1000,
      calculable: true,
      inRange: {
        color: ['#74b9ff', '#fdcb6e', '#ffa502', '#ff6348', '#ff4757']
      },
      show: false
    },
    geo: {
      map: props.view === 'china' ? 'china' : 'world',
      roam: true,
      zoom: 1.2,
      label: {
        emphasis: {
          show: false
        }
      },
      itemStyle: {
        normal: {
          areaColor: '#1e3a5f',
          borderColor: '#2c5282',
          borderWidth: 1
        },
        emphasis: {
          areaColor: '#2c5282'
        }
      }
    },
    series: []
  }

  // 根据视图模式添加系列
  if (viewMode.value === 'heatmap') {
    option.series.push({
      name: '威胁热力图',
      type: 'heatmap',
      coordinateSystem: 'geo',
      data: generateHeatmapData(),
      pointSize: 5,
      blurSize: 6
    })
  } else {
    option.series.push({
      name: '威胁标记',
      type: 'effectScatter',
      coordinateSystem: 'geo',
      data: generateMarkerData(),
      symbolSize: (val: any) => Math.max(val[2] / 10, 8),
      showEffectOn: 'render',
      rippleEffect: {
        brushType: 'stroke',
        scale: 3,
        period: 4
      },
      label: {
        formatter: '{b}',
        position: 'right',
        show: false
      },
      itemStyle: {
        color: (params: any) => {
          const value = params.data.value[2]
          if (value > 800) return '#ff4757'
          if (value > 600) return '#ff6348'
          if (value > 400) return '#ffa502'
          if (value > 200) return '#fdcb6e'
          return '#74b9ff'
        },
        shadowBlur: 10,
        shadowColor: '#333'
      },
      zlevel: 1
    })
  }

  // 添加攻击线路
  if (showAttackLines.value) {
    option.series.push({
      name: '攻击路径',
      type: 'lines',
      coordinateSystem: 'geo',
      zlevel: 2,
      large: true,
      effect: {
        show: true,
        constantSpeed: 30,
        symbol: 'circle',
        symbolSize: 3,
        trailLength: 0.2
      },
      lineStyle: {
        normal: {
          color: '#ff6b6b',
          width: 1,
          opacity: 0.6,
          curveness: 0.3
        }
      },
      data: generateAttackLines()
    })
  }

  mapInstance.setOption(option)

  // 注册地图数据
  if (props.view === 'china') {
    import('./china.json').then((chinaJson) => {
      echarts.registerMap('china', chinaJson.default)
      mapInstance?.setOption(option)
    })
  } else {
    import('./world.json').then((worldJson) => {
      echarts.registerMap('world', worldJson.default)
      mapInstance?.setOption(option)
    })
  }
}

// 生成热力图数据
const generateHeatmapData = () => {
  const points = []
  for (let i = 0; i < 200; i++) {
    points.push([
      -180 + Math.random() * 360,
      -90 + Math.random() * 180,
      Math.random() * 1000
    ])
  }
  return points
}

// 生成标记数据
const generateMarkerData = () => {
  const cities = [
    { name: '北京', value: [116.46, 39.92, 980] },
    { name: '上海', value: [121.48, 31.22, 850] },
    { name: '纽约', value: [-74.0, 40.71, 920] },
    { name: '伦敦', value: [-0.13, 51.51, 780] },
    { name: '东京', value: [139.69, 35.68, 890] },
    { name: '新加坡', value: [103.82, 1.35, 650] },
    { name: '悉尼', value: [151.21, -33.87, 720] },
    { name: '莫斯科', value: [37.62, 55.76, 810] },
    { name: '迪拜', value: [55.27, 25.20, 580] },
    { name: '孟买', value: [72.88, 19.08, 690] }
  ]
  return cities
}

// 生成攻击线数据
const generateAttackLines = () => {
  const lines = []
  const cities = generateMarkerData()

  for (let i = 0; i < 20; i++) {
    const from = cities[Math.floor(Math.random() * cities.length)]
    const to = cities[Math.floor(Math.random() * cities.length)]

    if (from !== to) {
      lines.push({
        fromName: from.name,
        toName: to.name,
        coords: [
          [from.value[0], from.value[1]],
          [to.value[0], to.value[1]]
        ]
      })
    }
  }

  return lines
}

// 生成实时攻击动画
const generateAttackAnimation = () => {
  const attacks = []
  for (let i = 0; i < 5; i++) {
    attacks.push({
      id: Date.now() + i,
      x1: Math.random() * 100,
      y1: Math.random() * 100,
      x2: Math.random() * 100,
      y2: Math.random() * 100
    })
  }
  activeAttacks.value = attacks
}

// 全屏切换
const toggleFullscreen = () => {
  if (mapContainer.value) {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      mapContainer.value.requestFullscreen()
    }
  }
}

// 窗口调整
const handleResize = () => {
  mapInstance?.resize()
}

// 监听属性变化
watch(() => props.view, () => {
  initMap()
})

watch(viewMode, () => {
  initMap()
})

watch(showAttackLines, () => {
  initMap()
})

// 定时更新数据
let updateTimer: NodeJS.Timeout

onMounted(() => {
  initMap()
  window.addEventListener('resize', handleResize)

  // 定时更新攻击动画
  updateTimer = setInterval(() => {
    generateAttackAnimation()
  }, 3000)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  mapInstance?.dispose()
  clearInterval(updateTimer)
})
</script>

<style lang="scss" scoped>
.threat-map-container {
  position: relative;
  width: 100%;
  height: 500px;
  background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
  border-radius: 12px;
  overflow: hidden;

  .map-canvas {
    width: 100%;
    height: 100%;
  }

  // 威胁统计面板
  .threat-stats {
    position: absolute;
    top: 20px;
    left: 20px;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    z-index: 10;

    .stat-item {
      display: flex;
      align-items: center;
      gap: 12px;

      .stat-icon {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;

        .el-icon {
          color: white;
          font-size: 20px;
        }
      }

      .stat-info {
        .stat-label {
          font-size: 12px;
          color: #909399;
          margin-bottom: 2px;
        }

        .stat-value {
          font-size: 18px;
          font-weight: bold;
          color: white;
        }
      }
    }
  }

  // 攻击线动画
  .attack-lines {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 5;

    .attack-svg {
      width: 100%;
      height: 100%;

      .attack-line {
        stroke-width: 2;
        animation: attackPulse 2s infinite;
      }
    }
  }

  // 图例
  .map-legend {
    position: absolute;
    bottom: 20px;
    left: 20px;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 16px;
    z-index: 10;

    .legend-title {
      font-size: 14px;
      color: white;
      margin-bottom: 12px;
      font-weight: 600;
    }

    .legend-items {
      display: flex;
      flex-direction: column;
      gap: 8px;

      .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        color: #c0c0c0;

        .legend-color {
          width: 12px;
          height: 12px;
          border-radius: 2px;
        }

        .legend-count {
          margin-left: auto;
          color: #909399;
        }
      }
    }
  }

  // 控制面板
  .map-controls {
    position: absolute;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    z-index: 10;

    .el-button {
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: white;

      &:hover {
        background: rgba(0, 0, 0, 0.9);
        border-color: #409eff;
      }

      &.el-button--primary {
        background: #409eff;
        border-color: #409eff;
      }
    }
  }

  // 动画
  @keyframes attackPulse {
    0% {
      opacity: 0;
    }
    50% {
      opacity: 1;
    }
    100% {
      opacity: 0;
    }
  }

  // 全屏模式
  &:fullscreen {
    border-radius: 0;

    .map-canvas {
      height: 100vh;
    }
  }
}

// 响应式
@media (max-width: 768px) {
  .threat-map-container {
    height: 400px;

    .threat-stats {
      transform: scale(0.9);
      transform-origin: top left;
    }

    .map-legend {
      transform: scale(0.9);
      transform-origin: bottom left;
    }
  }
}
</style>