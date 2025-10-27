<template>
  <div class="task-create">
    <div class="page-header">
      <h1>{{ isEdit ? '编辑任务' : '创建扫描任务' }}</h1>
      <p>{{ isEdit ? '修改扫描任务配置' : '创建新的安全扫描任务' }}</p>
    </div>

    <el-card>
      <el-form
        ref="taskForm"
        :model="taskData"
        :rules="rules"
        label-width="120px"
        @submit.prevent="handleSubmit"
      >
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="任务名称" prop="name">
              <el-input
                v-model="taskData.name"
                placeholder="请输入任务名称"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="扫描类型" prop="type">
              <el-select
                v-model="taskData.type"
                placeholder="请选择扫描类型"
                @change="handleTypeChange"
              >
                <el-option label="端口扫描" value="port_scan" />
                <el-option label="漏洞扫描" value="vulnerability_scan" />
                <el-option label="Web发现" value="web_discovery" />
                <el-option label="子域名枚举" value="subdomain_enum" />
                <el-option label="综合扫描" value="comprehensive" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="taskData.priority" placeholder="请选择优先级">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="紧急" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="执行时间">
              <el-radio-group v-model="taskData.schedule_type">
                <el-radio label="immediate">立即执行</el-radio>
                <el-radio label="scheduled">定时执行</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24" v-if="taskData.schedule_type === 'scheduled'">
          <el-col :span="12">
            <el-form-item label="执行时间" prop="scheduled_at">
              <el-date-picker
                v-model="taskData.scheduled_at"
                type="datetime"
                placeholder="选择执行时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="重复执行">
              <el-select v-model="taskData.recurring" placeholder="选择重复频率">
                <el-option label="不重复" value="" />
                <el-option label="每小时" value="hourly" />
                <el-option label="每日" value="daily" />
                <el-option label="每周" value="weekly" />
                <el-option label="每月" value="monthly" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- Target Selection -->
        <el-form-item label="目标资产" prop="target_assets">
          <div class="target-selection">
            <el-radio-group v-model="targetSelectionType" @change="handleTargetTypeChange">
              <el-radio label="assets">选择现有资产</el-radio>
              <el-radio label="manual">手动输入目标</el-radio>
            </el-radio-group>

            <div v-if="targetSelectionType === 'assets'" class="asset-selection">
              <el-select
                v-model="taskData.target_assets"
                multiple
                filterable
                placeholder="选择目标资产"
                style="width: 100%"
                @change="handleAssetChange"
              >
                <el-option
                  v-for="asset in availableAssets"
                  :key="asset.id"
                  :label="`${asset.name} (${getAssetTarget(asset)})`"
                  :value="asset.id"
                >
                  <span style="float: left">{{ asset.name }}</span>
                  <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">
                    {{ getAssetTypeLabel(asset.type || asset.asset_type) }}
                  </span>
                </el-option>
              </el-select>

              <div v-if="taskData.target_assets?.length" class="selected-assets">
                <h4>已选择的资产 ({{ taskData.target_assets.length }})</h4>
                <el-tag
                  v-for="assetId in taskData.target_assets"
                  :key="assetId"
                  closable
                  @close="removeAsset(assetId)"
                  style="margin-right: 8px; margin-bottom: 8px;"
                >
                  {{ getAssetName(assetId) }}
                </el-tag>
              </div>
            </div>

            <div v-else class="manual-targets">
              <el-input
                v-model="taskData.manual_targets"
                type="textarea"
                :rows="5"
                placeholder="每行一个目标，支持以下格式：&#10;• 域名: example.com&#10;• IP地址: 192.168.1.1 或 192.168.1.0/24&#10;• URL: https://test.com&#10;• IP范围: 192.168.1.1-192.168.1.10"
              />
            </div>
          </div>
        </el-form-item>

        <el-form-item label="任务描述">
          <el-input
            v-model="taskData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>

        <!-- Scan Configuration -->
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="扫描配置" name="config">
            <!-- Port Scan Config -->
            <div v-if="needsPortConfig" class="config-section">
              <h4>端口扫描配置</h4>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="端口范围">
                    <el-input
                      v-model="taskData.config.port_range"
                      placeholder="例如: 1-1000,8080,8443"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="扫描速度">
                    <el-select v-model="taskData.config.scan_speed">
                      <el-option label="慢速 (-T1)" value="1" />
                      <el-option label="正常 (-T3)" value="3" />
                      <el-option label="快速 (-T4)" value="4" />
                      <el-option label="极速 (-T5)" value="5" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="检测选项">
                    <el-checkbox-group v-model="taskData.config.port_options">
                      <el-checkbox label="service_detection">服务识别 (-sV)</el-checkbox>
                      <el-checkbox label="os_detection">操作系统检测 (-O)</el-checkbox>
                      <el-checkbox label="script_scan">脚本扫描 (-sC)</el-checkbox>
                    </el-checkbox-group>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- Vulnerability Scan Config -->
            <div v-if="needsVulnConfig" class="config-section">
              <h4>漏洞扫描配置</h4>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="扫描引擎">
                    <el-checkbox-group v-model="taskData.config.vuln_engines">
                      <el-checkbox label="nuclei">Nuclei</el-checkbox>
                      <el-checkbox label="xray">Xray</el-checkbox>
                    </el-checkbox-group>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="严重程度过滤">
                    <el-checkbox-group v-model="taskData.config.severity_filter">
                      <el-checkbox label="critical">严重</el-checkbox>
                      <el-checkbox label="high">高危</el-checkbox>
                      <el-checkbox label="medium">中危</el-checkbox>
                      <el-checkbox label="low">低危</el-checkbox>
                    </el-checkbox-group>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- Web Discovery Config -->
            <div v-if="needsWebConfig" class="config-section">
              <h4>Web发现配置</h4>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="爬取深度">
                    <el-input-number
                      v-model="taskData.config.crawl_depth"
                      :min="1"
                      :max="10"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="超时时间(秒)">
                    <el-input-number
                      v-model="taskData.config.timeout"
                      :min="10"
                      :max="300"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="Web选项">
                <el-checkbox-group v-model="taskData.config.web_options">
                  <el-checkbox label="screenshot">网页截图</el-checkbox>
                  <el-checkbox label="technology_detection">技术栈识别</el-checkbox>
                  <el-checkbox label="directory_scan">目录扫描</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </div>

            <!-- Subdomain Config -->
            <div v-if="needsSubdomainConfig" class="config-section">
              <h4>子域名枚举配置</h4>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="枚举方法">
                    <el-checkbox-group v-model="taskData.config.subdomain_methods">
                      <el-checkbox label="dns_brute">DNS爆破</el-checkbox>
                      <el-checkbox label="certificate_search">证书透明度</el-checkbox>
                      <el-checkbox label="search_engine">搜索引擎</el-checkbox>
                    </el-checkbox-group>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="字典文件">
                    <el-select v-model="taskData.config.wordlist">
                      <el-option label="小字典 (1K)" value="small" />
                      <el-option label="中字典 (10K)" value="medium" />
                      <el-option label="大字典 (100K)" value="large" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- General Options -->
            <div class="config-section">
              <h4>通用配置</h4>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="并发数">
                    <el-input-number
                      v-model="taskData.config.concurrency"
                      :min="1"
                      :max="100"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="重试次数">
                    <el-input-number
                      v-model="taskData.config.retry_count"
                      :min="0"
                      :max="5"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="排除规则">
                <el-input
                  v-model="taskData.config.exclude_patterns"
                  type="textarea"
                  :rows="3"
                  placeholder="每行一个排除规则，支持正则表达式"
                />
              </el-form-item>
            </div>
          </el-collapse-item>
        </el-collapse>

        <!-- Notification Settings -->
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="通知设置" name="notification">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="任务完成通知">
                  <el-switch v-model="taskData.notifications.on_complete" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="发现漏洞通知">
                  <el-switch v-model="taskData.notifications.on_vulnerability" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="任务失败通知">
                  <el-switch v-model="taskData.notifications.on_failure" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="通知方式">
                  <el-select v-model="taskData.notifications.methods" multiple>
                    <el-option label="系统通知" value="system" />
                    <el-option label="邮件通知" value="email" />
                    <el-option label="企业微信" value="wechat" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>

        <el-form-item class="form-actions">
          <el-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ isEdit ? '更新任务' : '创建任务' }}
          </el-button>
          <el-button
            v-if="!isEdit"
            type="success"
            :loading="loading"
            @click="handleSubmitAndStart"
          >
            创建并立即执行
          </el-button>
          <el-button @click="router.back()">
            取消
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/store/task'
import { useAssetStore } from '@/store/asset'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()
const assetStore = useAssetStore()

const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const activeCollapse = ref(['config'])
const targetSelectionType = ref('assets')
const availableAssets = ref([])

const taskData = reactive({
  name: '',
  type: 'port_scan',
  priority: 'medium',
  schedule_type: 'immediate',
  scheduled_at: null,
  recurring: '',
  target_assets: [],
  manual_targets: '',
  description: '',
  config: {
    // Port scan config
    port_range: '1-1000,8080,8443,3389,5432,3306,1433,6379,11211,9200',
    scan_speed: '3',
    port_options: ['service_detection'],

    // Vulnerability scan config
    vuln_engines: ['nuclei'],
    severity_filter: ['critical', 'high', 'medium'],

    // Web discovery config
    crawl_depth: 3,
    timeout: 30,
    web_options: ['screenshot', 'technology_detection'],

    // Subdomain config
    subdomain_methods: ['dns_brute', 'certificate_search'],
    wordlist: 'medium',

    // General config
    concurrency: 10,
    retry_count: 2,
    exclude_patterns: ''
  },
  notifications: {
    on_complete: true,
    on_vulnerability: true,
    on_failure: true,
    methods: ['system']
  }
})

const validateTargets = (rule, value, callback) => {
  if (targetSelectionType.value === 'assets') {
    if (!taskData.target_assets || taskData.target_assets.length === 0) {
      callback(new Error('请选择至少一个目标资产'))
      return
    }
  } else {
    if (!taskData.manual_targets || taskData.manual_targets.trim() === '') {
      callback(new Error('请输入手动目标'))
      return
    }

    // Validate manual targets format
    const targets = taskData.manual_targets.split('\n').map(line => line.trim()).filter(line => line)
    const invalidTargets = []

    for (const target of targets) {
      if (!isValidTarget(target)) {
        invalidTargets.push(target)
      }
    }

    if (invalidTargets.length > 0) {
      callback(new Error(`以下目标格式不正确: ${invalidTargets.join(', ')}`))
      return
    }
  }
  callback()
}

const rules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择扫描类型', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  target_assets: [
    {
      required: true,
      message: '请选择目标资产或输入手动目标',
      trigger: 'change',
      validator: validateTargets
    }
  ],
  scheduled_at: [
    {
      required: true,
      message: '请选择执行时间',
      trigger: 'change',
      validator: (rule, value, callback) => {
        if (taskData.schedule_type === 'scheduled' && !value) {
          callback(new Error('请选择执行时间'))
        } else {
          callback()
        }
      }
    }
  ]
}

const taskForm = ref()

// Computed properties for config sections
const needsPortConfig = computed(() =>
  ['port_scan', 'comprehensive'].includes(taskData.type)
)

const needsVulnConfig = computed(() =>
  ['vulnerability_scan', 'comprehensive'].includes(taskData.type)
)

const needsWebConfig = computed(() =>
  ['web_discovery', 'comprehensive'].includes(taskData.type)
)

const needsSubdomainConfig = computed(() =>
  ['subdomain_enum', 'comprehensive'].includes(taskData.type)
)

onMounted(async () => {
  await loadAssets()
  if (isEdit.value) {
    await loadTask()
  }
})

const loadAssets = async () => {
  try {
    const response = await assetStore.getAssets({ limit: 1000 })
    availableAssets.value = response || []
    console.log(`Loaded ${availableAssets.value.length} assets for task creation`, availableAssets.value)
  } catch (error) {
    console.error('Failed to load assets:', error)
    ElMessage.error('加载资产列表失败')
  }
}

const loadTask = async () => {
  loading.value = true
  try {
    const task = await taskStore.getTask(route.params.id)
    Object.assign(taskData, task)

    if (task.target_assets?.length) {
      targetSelectionType.value = 'assets'
    } else if (task.manual_targets) {
      targetSelectionType.value = 'manual'
    }
  } catch (error) {
    ElMessage.error('加载任务信息失败')
    router.back()
  } finally {
    loading.value = false
  }
}

const handleTypeChange = () => {
  // Reset type-specific config when type changes
  const name = taskData.name
  if (name.includes(' - ')) {
    taskData.name = name.split(' - ')[0] + ' - ' + getTypeLabel(taskData.type)
  } else {
    taskData.name = name + ' - ' + getTypeLabel(taskData.type)
  }
}

const handleTargetTypeChange = () => {
  if (targetSelectionType.value === 'assets') {
    taskData.manual_targets = ''
  } else {
    taskData.target_assets = []
  }
}

const handleAssetChange = () => {
  // Update task name based on selected assets
  if (taskData.target_assets?.length === 1) {
    const asset = availableAssets.value.find(a => a.id === taskData.target_assets[0])
    if (asset && !taskData.name) {
      taskData.name = `${asset.name} - ${getTypeLabel(taskData.type)}`
    }
  }
}

const removeAsset = (assetId) => {
  const index = taskData.target_assets.indexOf(assetId)
  if (index > -1) {
    taskData.target_assets.splice(index, 1)
  }
}

const getAssetName = (assetId) => {
  const asset = availableAssets.value.find(a => a.id === assetId)
  return asset ? asset.name : 'Unknown Asset'
}

const getAssetTarget = (asset) => {
  return asset.value || asset.target || asset.domain || asset.ip_address || asset.url || 'N/A'
}

const getAssetTypeLabel = (type) => {
  const labels = {
    domain: '域名',
    ip: 'IP',
    url: 'URL',
    port: '端口',
    web_server: 'Web服务器',
    database: '数据库',
    file_server: '文件服务器'
  }
  return labels[type] || type || '未知'
}

const isValidTarget = (target) => {
  // Domain validation (improved)
  const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$/

  // IP validation (with optional CIDR)
  const ipRegex = /^(\d{1,3}\.){3}\d{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$/

  // URL validation (improved)
  const urlRegex = /^https?:\/\/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+$/

  // IP range validation (improved)
  const ipRangeRegex = /^(\d{1,3}\.){3}\d{1,3}-(\d{1,3}\.){3}\d{1,3}$/

  // Additional validations for IP octets
  if (ipRegex.test(target)) {
    const parts = target.split('/')[0].split('.')
    return parts.every(part => parseInt(part) >= 0 && parseInt(part) <= 255)
  }

  return domainRegex.test(target) || urlRegex.test(target) || ipRangeRegex.test(target)
}

const getTypeLabel = (type) => {
  const labels = {
    port_scan: '端口扫描',
    vulnerability_scan: '漏洞扫描',
    web_discovery: 'Web发现',
    subdomain_enum: '子域名枚举',
    comprehensive: '综合扫描'
  }
  return labels[type] || type
}

const handleSubmit = async (startImmediately = false) => {
  if (!taskForm.value) return

  try {
    await taskForm.value.validate()

    // Prepare submission data
    const submitData = { ...taskData }

    if (targetSelectionType.value === 'manual') {
      submitData.target_assets = []
      // Parse manual targets
      if (submitData.manual_targets) {
        submitData.manual_targets = submitData.manual_targets
          .split('\n')
          .map(line => line.trim())
          .filter(line => line)
      }
    } else {
      submitData.manual_targets = ''
    }

    loading.value = true

    let task
    if (isEdit.value) {
      task = await taskStore.updateTask(route.params.id, submitData)
      ElMessage.success('任务更新成功')
    } else {
      task = await taskStore.createTask(submitData)
      ElMessage.success('任务创建成功')

      if (startImmediately) {
        await taskStore.startTask(task.id)
        ElMessage.success('任务已开始执行')
      }
    }

    router.push(`/tasks/${task.id}`)
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}

const handleSubmitAndStart = () => {
  handleSubmit(true)
}
</script>

<style scoped lang="scss">
.task-create {
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

  .target-selection {
    .asset-selection {
      margin-top: 16px;

      .selected-assets {
        margin-top: 16px;
        padding: 16px;
        background: var(--el-fill-color-light);
        border-radius: 4px;

        h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }
    }

    .manual-targets {
      margin-top: 16px;
    }
  }

  .config-section {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);

    &:last-child {
      border-bottom: none;
    }

    h4 {
      margin: 0 0 16px 0;
      color: var(--el-text-color-primary);
      font-size: 16px;
      font-weight: 500;
    }
  }

  .form-actions {
    margin-top: 32px;
    text-align: center;

    .el-button {
      margin: 0 8px;
    }
  }

  :deep(.el-collapse-item__header) {
    font-weight: 500;
    font-size: 15px;
  }

  :deep(.el-checkbox-group) {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  :deep(.el-radio-group) {
    display: flex;
    gap: 16px;
  }
}
</style>