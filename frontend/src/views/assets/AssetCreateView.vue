<template>
  <div class="asset-create">
    <div class="page-header">
      <h1>{{ isEdit ? '编辑资产' : '添加资产' }}</h1>
      <p>{{ isEdit ? '修改资产信息和配置' : '添加新的网络安全资产到系统' }}</p>
    </div>

    <el-card>
      <el-form
        ref="assetForm"
        :model="assetData"
        :rules="rules"
        label-width="100px"
        @submit.prevent="handleSubmit"
      >
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="资产名称" prop="name">
              <el-input
                v-model="assetData.name"
                placeholder="请输入资产名称"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="资产类型" prop="type">
              <el-select
                v-model="assetData.type"
                placeholder="请选择资产类型"
                @change="handleTypeChange"
              >
                <el-option label="域名" value="domain" />
                <el-option label="IP地址" value="ip" />
                <el-option label="URL" value="url" />
                <el-option label="端口范围" value="port" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="资产值" prop="value">
              <el-input
                v-model="assetData.value"
                :placeholder="getValuePlaceholder()"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="assetData.priority" placeholder="请选择优先级">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="紧急" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="标签">
              <el-select
                v-model="assetData.tags"
                multiple
                filterable
                allow-create
                placeholder="输入或选择标签"
              >
                <el-option
                  v-for="tag in availableTags"
                  :key="tag"
                  :label="tag"
                  :value="tag"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="所属部门">
              <el-input
                v-model="assetData.department"
                placeholder="请输入所属部门"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input
            v-model="assetData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入资产描述"
          />
        </el-form-item>

        <!-- 高级配置 -->
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="高级配置" name="advanced">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="扫描配置">
                  <el-checkbox-group v-model="assetData.scan_config.enabled_scans">
                    <el-checkbox label="port_scan">端口扫描</el-checkbox>
                    <el-checkbox label="vulnerability_scan">漏洞扫描</el-checkbox>
                    <el-checkbox label="web_discovery">Web发现</el-checkbox>
                    <el-checkbox label="subdomain_enum">子域名枚举</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
              </el-col>

              <el-col :span="12">
                <el-form-item label="扫描频率">
                  <el-select
                    v-model="assetData.scan_config.schedule"
                    placeholder="请选择扫描频率"
                  >
                    <el-option label="不定期" value="manual" />
                    <el-option label="每日" value="daily" />
                    <el-option label="每周" value="weekly" />
                    <el-option label="每月" value="monthly" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="端口范围">
                  <el-input
                    v-model="assetData.scan_config.port_range"
                    placeholder="例如: 1-1000,8080,8443"
                  />
                </el-form-item>
              </el-col>

              <el-col :span="12">
                <el-form-item label="扫描强度">
                  <el-select
                    v-model="assetData.scan_config.intensity"
                    placeholder="请选择扫描强度"
                  >
                    <el-option label="轻量" value="light" />
                    <el-option label="标准" value="normal" />
                    <el-option label="深度" value="intensive" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="排除规则">
              <el-input
                v-model="assetData.scan_config.exclude_patterns"
                type="textarea"
                :rows="2"
                placeholder="每行一个排除规则，支持正则表达式"
              />
            </el-form-item>
          </el-collapse-item>
        </el-collapse>

        <!-- 批量导入 -->
        <el-collapse v-if="!isEdit" v-model="activeCollapse">
          <el-collapse-item title="批量导入" name="bulk">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="导入方式">
                  <el-radio-group v-model="bulkImportType">
                    <el-radio label="text">文本输入</el-radio>
                    <el-radio label="file">文件上传</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item v-if="bulkImportType === 'text'" label="批量资产">
              <el-input
                v-model="bulkAssets"
                type="textarea"
                :rows="5"
                placeholder="每行一个资产，支持域名、IP、URL等格式"
              />
            </el-form-item>

            <el-form-item v-if="bulkImportType === 'file'" label="文件上传">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :show-file-list="false"
                accept=".txt,.csv"
                @change="handleFileChange"
              >
                <el-button>选择文件</el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 .txt 和 .csv 格式，每行一个资产
                  </div>
                </template>
              </el-upload>
              <div v-if="uploadFile" class="upload-file-info">
                已选择文件: {{ uploadFile.name }}
              </div>
            </el-form-item>
          </el-collapse-item>
        </el-collapse>

        <el-form-item class="form-actions">
          <el-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ isEdit ? '更新资产' : '添加资产' }}
          </el-button>
          <el-button
            v-if="!isEdit && (bulkAssets || uploadFile)"
            type="success"
            :loading="bulkLoading"
            @click="handleBulkImport"
          >
            批量导入
          </el-button>
          <el-button @click="$router.back()">
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
import { useAssetStore } from '@/store/asset'

const route = useRoute()
const router = useRouter()
const assetStore = useAssetStore()

const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const bulkLoading = ref(false)
const activeCollapse = ref([])
const bulkImportType = ref('text')
const bulkAssets = ref('')
const uploadFile = ref(null)

const assetData = reactive({
  name: '',
  type: 'domain',
  value: '',
  priority: 'medium',
  tags: [],
  department: '',
  description: '',
  scan_config: {
    enabled_scans: ['port_scan'],
    schedule: 'manual',
    port_range: '1-1000,8080,8443',
    intensity: 'normal',
    exclude_patterns: ''
  }
})

const availableTags = ref(['内网', '外网', '生产', '测试', '开发', 'Web应用', '数据库', '中间件'])

const rules = {
  name: [
    { required: true, message: '请输入资产名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择资产类型', trigger: 'change' }
  ],
  value: [
    { required: true, message: '请输入资产值', trigger: 'blur' },
    { validator: validateAssetValue, trigger: 'blur' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ]
}

const assetForm = ref()

onMounted(async () => {
  if (isEdit.value) {
    await loadAsset()
  }
})

const loadAsset = async () => {
  loading.value = true
  try {
    const asset = await assetStore.getAsset(route.params.id)
    Object.assign(assetData, asset)
  } catch (error) {
    ElMessage.error('加载资产信息失败')
    router.back()
  } finally {
    loading.value = false
  }
}

const handleTypeChange = () => {
  assetData.value = ''
}

const getValuePlaceholder = () => {
  const placeholders = {
    domain: '例如: example.com',
    ip: '例如: 192.168.1.1 或 192.168.1.0/24',
    url: '例如: https://example.com',
    port: '例如: 192.168.1.1:80-443'
  }
  return placeholders[assetData.type] || '请输入资产值'
}

function validateAssetValue(rule, value, callback) {
  if (!value) {
    callback(new Error('请输入资产值'))
    return
  }

  const { type } = assetData
  let isValid = false

  switch (type) {
    case 'domain':
      isValid = /^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$/.test(value)
      break
    case 'ip':
      isValid = /^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/.test(value)
      break
    case 'url':
      isValid = /^https?:\/\/[^\s]+$/.test(value)
      break
    case 'port':
      isValid = /^(\d{1,3}\.){3}\d{1,3}:\d+(-\d+)?$/.test(value)
      break
  }

  if (!isValid) {
    callback(new Error(`请输入有效的${getTypeLabel(type)}`))
  } else {
    callback()
  }
}

const getTypeLabel = (type) => {
  const labels = {
    domain: '域名',
    ip: 'IP地址',
    url: 'URL',
    port: '端口范围'
  }
  return labels[type] || type
}

const handleSubmit = async () => {
  if (!assetForm.value) return

  try {
    await assetForm.value.validate()
    loading.value = true

    if (isEdit.value) {
      await assetStore.updateAsset(route.params.id, assetData)
      ElMessage.success('资产更新成功')
    } else {
      await assetStore.createAsset(assetData)
      ElMessage.success('资产添加成功')
    }

    router.push('/assets')
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}

const handleBulkImport = async () => {
  let assets = []

  if (bulkImportType.value === 'text' && bulkAssets.value) {
    assets = bulkAssets.value
      .split('\n')
      .map(line => line.trim())
      .filter(line => line)
  } else if (bulkImportType.value === 'file' && uploadFile.value) {
    try {
      const text = await readFileAsText(uploadFile.value.raw)
      assets = text
        .split('\n')
        .map(line => line.trim())
        .filter(line => line)
    } catch (error) {
      ElMessage.error('文件读取失败')
      return
    }
  }

  if (assets.length === 0) {
    ElMessage.warning('请输入要导入的资产')
    return
  }

  bulkLoading.value = true
  try {
    await assetStore.bulkCreate(assets.map(asset => ({
      ...assetData,
      name: asset,
      value: asset,
      type: detectAssetType(asset)
    })))

    ElMessage.success(`成功导入 ${assets.length} 个资产`)
    router.push('/assets')
  } catch (error) {
    ElMessage.error('批量导入失败')
  } finally {
    bulkLoading.value = false
  }
}

const handleFileChange = (file) => {
  uploadFile.value = file
}

const readFileAsText = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

const detectAssetType = (value) => {
  if (/^https?:\/\//.test(value)) return 'url'
  if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/.test(value)) return 'ip'
  if (/^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$/.test(value)) return 'domain'
  return 'domain'
}
</script>

<style scoped lang="scss">
.asset-create {
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

  .form-actions {
    margin-top: 32px;
    text-align: center;

    .el-button {
      margin: 0 8px;
    }
  }

  .upload-file-info {
    margin-top: 8px;
    color: var(--el-text-color-regular);
    font-size: 14px;
  }

  :deep(.el-collapse-item__header) {
    font-weight: 500;
  }
}
</style>