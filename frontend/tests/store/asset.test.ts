import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAssetStore } from '@/store/asset'

// Mock request utility
vi.mock('@/utils/request', () => ({
  request: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('Asset Store', () => {
  let store
  let mockRequest

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useAssetStore()
    mockRequest = vi.mocked(await import('@/utils/request')).request
  })

  it('initializes with empty state', () => {
    expect(store.assets).toEqual([])
    expect(store.currentAsset).toBe(null)
    expect(store.loading).toBe(false)
  })

  it('gets assets list', async () => {
    const mockResponse = {
      data: {
        items: [
          { id: '1', name: 'Test Asset', type: 'domain', value: 'example.com' }
        ],
        total: 1
      }
    }
    mockRequest.get.mockResolvedValue(mockResponse)

    const result = await store.getAssets({ page: 1, limit: 10 })

    expect(mockRequest.get).toHaveBeenCalledWith('/api/assets', {
      params: { page: 1, limit: 10 }
    })
    expect(result).toEqual(mockResponse.data)
  })

  it('gets single asset', async () => {
    const mockAsset = { id: '1', name: 'Test Asset', type: 'domain' }
    mockRequest.get.mockResolvedValue({ data: mockAsset })

    const result = await store.getAsset('1')

    expect(mockRequest.get).toHaveBeenCalledWith('/api/assets/1')
    expect(result).toEqual(mockAsset)
  })

  it('creates new asset', async () => {
    const newAsset = { name: 'New Asset', type: 'ip', value: '192.168.1.1' }
    const mockResponse = { data: { id: '2', ...newAsset } }
    mockRequest.post.mockResolvedValue(mockResponse)

    const result = await store.createAsset(newAsset)

    expect(mockRequest.post).toHaveBeenCalledWith('/api/assets', newAsset)
    expect(result).toEqual(mockResponse.data)
  })

  it('updates existing asset', async () => {
    const updateData = { name: 'Updated Asset' }
    const mockResponse = { data: { id: '1', ...updateData } }
    mockRequest.put.mockResolvedValue(mockResponse)

    const result = await store.updateAsset('1', updateData)

    expect(mockRequest.put).toHaveBeenCalledWith('/api/assets/1', updateData)
    expect(result).toEqual(mockResponse.data)
  })

  it('deletes asset', async () => {
    mockRequest.delete.mockResolvedValue({})

    await store.deleteAsset('1')

    expect(mockRequest.delete).toHaveBeenCalledWith('/api/assets/1')
  })

  it('bulk creates assets', async () => {
    const assets = [
      { name: 'Asset 1', type: 'ip', value: '192.168.1.1' },
      { name: 'Asset 2', type: 'domain', value: 'example.com' }
    ]
    const mockResponse = { data: assets.map((a, i) => ({ id: i + 1, ...a })) }
    mockRequest.post.mockResolvedValue(mockResponse)

    const result = await store.bulkCreate(assets)

    expect(mockRequest.post).toHaveBeenCalledWith('/api/assets/bulk', { assets })
    expect(result).toEqual(mockResponse.data)
  })

  it('scans asset', async () => {
    mockRequest.post.mockResolvedValue({})

    await store.scanAsset('1')

    expect(mockRequest.post).toHaveBeenCalledWith('/api/assets/1/scan')
  })

  it('handles API errors', async () => {
    const error = new Error('Network error')
    mockRequest.get.mockRejectedValue(error)

    await expect(store.getAssets()).rejects.toThrow('Network error')
  })

  it('gets asset vulnerabilities', async () => {
    const mockVulns = [
      { id: '1', name: 'SQL Injection', severity: 'high' }
    ]
    mockRequest.get.mockResolvedValue({ data: mockVulns })

    const result = await store.getAssetVulnerabilities('1')

    expect(mockRequest.get).toHaveBeenCalledWith('/api/assets/1/vulnerabilities')
    expect(result).toEqual(mockVulns)
  })

  it('gets asset scan history', async () => {
    const mockHistory = [
      { id: '1', task_name: 'Port Scan', status: 'completed' }
    ]
    mockRequest.get.mockResolvedValue({ data: mockHistory })

    const result = await store.getAssetScanHistory('1')

    expect(mockRequest.get).toHaveBeenCalledWith('/api/assets/1/scan-history')
    expect(result).toEqual(mockHistory)
  })
})