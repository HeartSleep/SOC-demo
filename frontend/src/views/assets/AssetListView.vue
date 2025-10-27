<template>
  <div class="asset-list">
    <div class="page-header">
      <h1>资产管理</h1>
      <p>管理和监控您的网络安全资产</p>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <el-button
          type="primary"
          @click="$router.push('/assets/create')"
        >
          <el-icon><Plus /></el-icon>
          添加资产
        </el-button>
        <el-button
          @click="handleBulkScan"
          :disabled="selectedAssets.length === 0"
        >
          <el-icon><Operation /></el-icon>
          批量扫描
        </el-button>
        <el-button
          type="danger"
          @click="handleBulkDelete"
          :disabled="selectedAssets.length === 0"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>

      <div class="toolbar-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索资产..."
          prefix-icon="Search"
          clearable
          @input="handleSearch"
        />
        <el-select v-model="typeFilter" placeholder="资产类型" clearable>
          <el-option label="全部" value="" />
          <el-option label="域名" value="domain" />
          <el-option label="IP地址" value="ip" />
          <el-option label="URL" value="url" />
          <el-option label="端口" value="port" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态" clearable>
          <el-option label="全部" value="" />
          <el-option label="活跃" value="active" />
          <el-option label="非活跃" value="inactive" />
          <el-option label="未知" value="unknown" />
        </el-select>
      </div>
    </div>

    <el-card>
      <el-table
        :data="assets"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="name" label="资产名称" min-width="150">
          <template #default="{ row }">
            <router-link :to="`/assets/${row.id}`" class="asset-link">
              {{ row.name }}
            </router-link>
          </template>
        </el-table-column>

        <el-table-column prop="asset_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.asset_type)">
              {{ getTypeLabel(row.asset_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="资产值" min-width="200">
          <template #default="{ row }">
            {{ getAssetValue(row) }}
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="端口数" width="80">
          <template #default="{ row }">
            {{ (row.open_ports && row.open_ports.length) || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="漏洞数" width="80">
          <template #default="{ row }">
            <el-tag
              v-if="row.vulnerability_count && row.vulnerability_count > 0"
              type="danger"
            >
              {{ row.vulnerability_count }}
            </el-tag>
            <span v-else>0</span>
          </template>
        </el-table-column>

        <el-table-column prop="last_scan" label="最后扫描" width="150">
          <template #default="{ row }">
            {{ formatDate(row.last_scan) }}
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleScan(row)"
            >
              扫描
            </el-button>
            <el-button
              size="small"
              @click="$router.push(`/assets/${row.id}`)"
            >
              详情
            </el-button>
            <el-dropdown @command="(cmd) => handleCommand(cmd, row)">
              <el-button size="small" type="info">
                更多<el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAssetStore } from '@/store/asset'
import { formatDate } from '@/utils/date'

const router = useRouter()
const assetStore = useAssetStore()

const loading = ref(false)
const assets = ref([])
const selectedAssets = ref([])
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
  fetchAssets()
})

const fetchAssets = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.currentPage - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      asset_type: typeFilter.value,
      status: statusFilter.value
    }
    const response = await assetStore.getAssets(params)
    assets.value = response.data || []
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('获取资产列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.currentPage = 1
  fetchAssets()
}

const handleSelectionChange = (selection) => {
  selectedAssets.value = selection
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  fetchAssets()
}

const handleCurrentChange = (page) => {
  pagination.currentPage = page
  fetchAssets()
}

const handleScan = async (asset) => {
  try {
    await assetStore.scanAsset(asset.id)
    ElMessage.success('扫描任务已启动')
    fetchAssets()
  } catch (error) {
    ElMessage.error('启动扫描失败')
  }
}

const handleBulkScan = async () => {
  const ids = selectedAssets.value.map(asset => asset.id)
  try {
    await assetStore.bulkScan(ids)
    ElMessage.success('批量扫描任务已启动')
    selectedAssets.value = []
    fetchAssets()
  } catch (error) {
    ElMessage.error('启动批量扫描失败')
  }
}

const handleBulkDelete = async () => {
  await ElMessageBox.confirm(
    `确定要删除选中的 ${selectedAssets.value.length} 个资产吗？`,
    '确认删除',
    { type: 'warning' }
  )

  const ids = selectedAssets.value.map(asset => asset.id)
  try {
    await assetStore.bulkDelete(ids)
    ElMessage.success('批量删除成功')
    selectedAssets.value = []
    fetchAssets()
  } catch (error) {
    ElMessage.error('批量删除失败')
  }
}

const handleCommand = async (command, asset) => {
  if (command === 'edit') {
    router.push(`/assets/${asset.id}/edit`)
  } else if (command === 'delete') {
    await ElMessageBox.confirm('确定要删除这个资产吗？', '确认删除', {
      type: 'warning'
    })
    try {
      await assetStore.deleteAsset(asset.id)
      ElMessage.success('删除成功')
      fetchAssets()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }
}

const getAssetValue = (asset) => {
  if (asset.domain) return asset.domain
  if (asset.ip_address) return asset.ip_address
  if (asset.url) return asset.url
  if (asset.port) return `Port ${asset.port}`
  return asset.name || 'N/A'
}

const getTypeLabel = (type) => {
  const labels = {
    domain: '域名',
    ip: 'IP',
    url: 'URL',
    port: '端口'
  }
  return labels[type] || type
}

const getTypeTagType = (type) => {
  const types = {
    domain: 'primary',
    ip: 'success',
    url: 'info',
    port: 'warning'
  }
  return types[type] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    active: '活跃',
    inactive: '非活跃',
    unknown: '未知'
  }
  return labels[status] || status
}

const getStatusTagType = (status) => {
  const types = {
    active: 'success',
    inactive: 'danger',
    unknown: 'info'
  }
  return types[status] || 'info'
}
</script>

<style scoped lang="scss">
.asset-list {
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

  .asset-link {
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
  .asset-list .toolbar {
    flex-direction: column;
    align-items: stretch;

    .toolbar-left,
    .toolbar-right {
      justify-content: center;
    }

    .toolbar-right {
      .el-input {
        width: 100%;
      }
    }
  }
}
</style>