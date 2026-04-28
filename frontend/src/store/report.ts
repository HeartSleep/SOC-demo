import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Report, ReportFilters, ReportCreateData } from '@/types/report'
import { request } from '@/utils/request'

// 定义后端不存在的接口，需要在调用时处理错误
interface UnimplementedApi {
  getPreviewUrl: null
  cancelReport: null
  bulkDownload: null
  bulkDelete: null
  generateShareLink: null
  generateQuickReport: null
  getReportTemplates: null
}

export const useReportStore = defineStore('report', () => {
  const reports = ref<Report[]>([])
  const currentReport = ref<Report | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 后端已实现的接口
  const getReports = async (params?: ReportFilters) => {
    error.value = null
    try {
      const response = await request.get('/reports', { params })
      return response
    } catch (err: any) {
      error.value = err.message || '获取报告列表失败'
      throw err
    }
  }

  const getReport = async (id: string): Promise<Report> => {
    error.value = null
    try {
      const response = await request.get(`/reports/${id}`)
      return response
    } catch (err: any) {
      error.value = err.message || '获取报告详情失败'
      throw err
    }
  }

  const createReport = async (data: ReportCreateData): Promise<Report> => {
    error.value = null
    loading.value = true
    try {
      const response = await request.post('/reports', data)
      return response
    } catch (err: any) {
      error.value = err.message || '创建报告失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteReport = async (id: string): Promise<void> => {
    error.value = null
    loading.value = true
    try {
      await request.delete(`/reports/${id}`)
    } catch (err: any) {
      error.value = err.message || '删除报告失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const downloadReport = async (id: string): Promise<Blob> => {
    error.value = null
    try {
      const response = await request.get(`/reports/${id}/download`, {
        responseType: 'blob'
      })
      return response
    } catch (err: any) {
      error.value = err.message || '下载报告失败'
      throw err
    }
  }

  const regenerateReport = async (id: string): Promise<void> => {
    error.value = null
    loading.value = true
    try {
      await request.post(`/reports/${id}/regenerate`)
    } catch (err: any) {
      error.value = err.message || '重新生成报告失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ==================== 以下接口后端未实现，调用时会抛出明确错误 ====================

  /**
   * @deprecated 后端未实现预览接口
   * @throws Error 后端接口不存在
   */
  const getPreviewUrl = async (id: string): Promise<string> => {
    const err = new Error('预览接口后端未实现')
    error.value = err.message
    throw err
  }

  /**
   * @deprecated 后端未实现取消报告接口
   * @throws Error 后端接口不存在
   */
  const cancelReport = async (id: string): Promise<void> => {
    const err = new Error('取消报告接口后端未实现')
    error.value = err.message
    throw err
  }

  /**
   * @deprecated 后端未实现批量下载接口
   * @throws Error 后端接口不存在
   */
  const bulkDownload = async (ids: string[]): Promise<Blob> => {
    const err = new Error('批量下载接口后端未实现')
    error.value = err.message
    throw err
  }

  /**
   * @deprecated 后端未实现批量删除接口（使用单个删除替代）
   * @throws Error 后端接口不存在
   */
  const bulkDelete = async (ids: string[]): Promise<void> => {
    const err = new Error('批量删除接口后端未实现，请逐个删除')
    error.value = err.message
    throw err
  }

  /**
   * @deprecated 后端未实现分享链接接口
   * @throws Error 后端接口不存在
   */
  const generateShareLink = async (id: string, options: unknown) => {
    const err = new Error('分享链接接口后端未实现')
    error.value = err.message
    throw err
  }

  /**
   * @deprecated 后端未实现快速报告接口
   * @throws Error 后端接口不存在
   */
  const generateQuickReport = async (data: unknown): Promise<Report> => {
    const err = new Error('快速报告接口后端未实现')
    error.value = err.message
    throw err
  }

  /**
   * @deprecated 后端未实现报告模板接口
   * @throws Error 后端接口不存在
   */
  const getReportTemplates = async () => {
    const err = new Error('报告模板接口后端未实现')
    error.value = err.message
    throw err
  }

  return {
    reports,
    currentReport,
    loading,
    error,
    getReports,
    getReport,
    createReport,
    deleteReport,
    downloadReport,
    regenerateReport,
    // 未实现的接口
    getPreviewUrl,
    cancelReport,
    bulkDownload,
    bulkDelete,
    generateShareLink,
    generateQuickReport,
    getReportTemplates
  }
})