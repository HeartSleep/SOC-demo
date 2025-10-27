import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Asset, AssetFilters, AssetCreateData, AssetUpdateData } from '@/types/asset'
import { request } from '@/utils/request'
import { ElMessage } from 'element-plus'

export const useAssetStore = defineStore('asset', () => {
  const assets = ref<Asset[]>([])
  const currentAsset = ref<Asset | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Helper function for error handling
  const handleError = (err: any, defaultMessage: string) => {
    const message = err?.response?.data?.detail || err?.message || defaultMessage
    error.value = message
    ElMessage.error(message)
    console.error('Asset Store Error:', err)
  }

  const getAssets = async (params?: AssetFilters) => {
    loading.value = true
    error.value = null
    try {
      // Remove empty string parameters
      const cleanParams = Object.fromEntries(
        Object.entries(params || {}).filter(([_, v]) => v !== '' && v !== null && v !== undefined)
      )

      const response = await request.get('/assets/', { params: cleanParams })
      // Backend returns array directly now
      const assetsList = Array.isArray(response) ? response : (response.items || response.data || [])
      assets.value = assetsList
      return { data: assetsList, total: assetsList.length }
    } catch (err) {
      handleError(err, 'Failed to fetch assets')
      return { data: [], total: 0 }
    } finally {
      loading.value = false
    }
  }

  const getAsset = async (id: string): Promise<Asset | null> => {
    loading.value = true
    error.value = null
    try {
      const response = await request.get(`/assets/${id}`)
      currentAsset.value = response
      return response
    } catch (err) {
      handleError(err, `Failed to fetch asset ${id}`)
      return null
    } finally {
      loading.value = false
    }
  }

  const createAsset = async (data: AssetCreateData): Promise<Asset | null> => {
    loading.value = true
    error.value = null
    try {
      const response = await request.post('/assets/', data)
      ElMessage.success('Asset created successfully')
      return response
    } catch (err) {
      handleError(err, 'Failed to create asset')
      return null
    } finally {
      loading.value = false
    }
  }

  const updateAsset = async (id: string, data: AssetUpdateData): Promise<Asset | null> => {
    loading.value = true
    error.value = null
    try {
      const response = await request.put(`/assets/${id}`, data)
      ElMessage.success('Asset updated successfully')
      return response
    } catch (err) {
      handleError(err, `Failed to update asset ${id}`)
      return null
    } finally {
      loading.value = false
    }
  }

  const deleteAsset = async (id: string): Promise<boolean> => {
    loading.value = true
    error.value = null
    try {
      await request.delete(`/assets/${id}`)
      ElMessage.success('Asset deleted successfully')
      return true
    } catch (err) {
      handleError(err, `Failed to delete asset ${id}`)
      return false
    } finally {
      loading.value = false
    }
  }

  const bulkCreate = async (assets: AssetCreateData[]): Promise<Asset[]> => {
    loading.value = true
    error.value = null
    try {
      const response = await request.post('/assets/bulk', { assets })
      ElMessage.success(`Created ${assets.length} assets successfully`)
      return response
    } catch (err) {
      handleError(err, 'Failed to bulk create assets')
      return []
    } finally {
      loading.value = false
    }
  }

  const bulkDelete = async (ids: string[]): Promise<boolean> => {
    loading.value = true
    error.value = null
    try {
      await request.delete('/assets/bulk', { data: { ids } })
      ElMessage.success(`Deleted ${ids.length} assets successfully`)
      return true
    } catch (err) {
      handleError(err, 'Failed to bulk delete assets')
      return false
    } finally {
      loading.value = false
    }
  }

  const scanAsset = async (id: string): Promise<boolean> => {
    loading.value = true
    error.value = null
    try {
      await request.post(`/assets/${id}/scan`)
      ElMessage.success('Asset scan started successfully')
      return true
    } catch (err) {
      handleError(err, `Failed to start scan for asset ${id}`)
      return false
    } finally {
      loading.value = false
    }
  }

  const bulkScan = async (ids: string[]): Promise<boolean> => {
    loading.value = true
    error.value = null
    try {
      await request.post('/assets/bulk-scan', { ids })
      ElMessage.success(`Started scan for ${ids.length} assets`)
      return true
    } catch (err) {
      handleError(err, 'Failed to start bulk scan')
      return false
    } finally {
      loading.value = false
    }
  }

  const getAssetVulnerabilities = async (id: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await request.get(`/assets/${id}/vulnerabilities`)
      return response
    } catch (err) {
      handleError(err, `Failed to fetch vulnerabilities for asset ${id}`)
      return { items: [], total: 0 }
    } finally {
      loading.value = false
    }
  }

  const getAssetScanHistory = async (id: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await request.get(`/assets/${id}/scan-history`)
      return response
    } catch (err) {
      handleError(err, `Failed to fetch scan history for asset ${id}`)
      return []
    } finally {
      loading.value = false
    }
  }

  const getAssetActivities = async (id: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await request.get(`/assets/${id}/activities`)
      return response
    } catch (err) {
      handleError(err, `Failed to fetch activities for asset ${id}`)
      return []
    } finally {
      loading.value = false
    }
  }

  const exportAsset = async (id: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await request.get(`/assets/${id}/export`)
      ElMessage.success('Asset exported successfully')
      return response
    } catch (err) {
      handleError(err, `Failed to export asset ${id}`)
      return null
    } finally {
      loading.value = false
    }
  }

  // Clear error state
  const clearError = () => {
    error.value = null
  }

  return {
    assets,
    currentAsset,
    loading,
    error,
    getAssets,
    getAsset,
    createAsset,
    updateAsset,
    deleteAsset,
    bulkCreate,
    bulkDelete,
    scanAsset,
    bulkScan,
    getAssetVulnerabilities,
    getAssetScanHistory,
    getAssetActivities,
    exportAsset,
    clearError
  }
})