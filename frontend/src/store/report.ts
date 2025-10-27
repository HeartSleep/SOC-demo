import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Report, ReportFilters, ReportCreateData } from '@/types/report'
import { request } from '@/utils/request'

export const useReportStore = defineStore('report', () => {
  const reports = ref<Report[]>([])
  const currentReport = ref<Report | null>(null)
  const loading = ref(false)

  const getReports = async (params?: ReportFilters) => {
    const response = await request.get('/reports', { params })
    return response
  }

  const getReport = async (id: string): Promise<Report> => {
    const response = await request.get(`/reports/${id}`)
    return response
  }

  const createReport = async (data: ReportCreateData): Promise<Report> => {
    const response = await request.post('/reports', data)
    return response
  }

  const deleteReport = async (id: string): Promise<void> => {
    await request.delete(`/reports/${id}`)
  }

  const downloadReport = async (id: string): Promise<Blob> => {
    const response = await request.get(`/reports/${id}/download`, {
      responseType: 'blob'
    })
    return response
  }

  const getPreviewUrl = async (id: string): Promise<string> => {
    const response = await request.get(`/reports/${id}/preview`)
    return response.url
  }

  const cancelReport = async (id: string): Promise<void> => {
    await request.post(`/reports/${id}/cancel`)
  }

  const regenerateReport = async (id: string): Promise<void> => {
    await request.post(`/reports/${id}/regenerate`)
  }

  const bulkDownload = async (ids: string[]): Promise<Blob> => {
    const response = await request.post('/reports/bulk-download',
      { ids },
      { responseType: 'blob' }
    )
    return response
  }

  const bulkDelete = async (ids: string[]): Promise<void> => {
    await request.delete('/reports/bulk', { data: { ids } })
  }

  const generateShareLink = async (id: string, options: any) => {
    const response = await request.post(`/reports/${id}/share`, options)
    return response
  }

  const generateQuickReport = async (data: any): Promise<Report> => {
    const response = await request.post('/reports/quick', data)
    return response
  }

  const getReportTemplates = async () => {
    const response = await request.get('/reports/templates')
    return response
  }

  return {
    reports,
    currentReport,
    loading,
    getReports,
    getReport,
    createReport,
    deleteReport,
    downloadReport,
    getPreviewUrl,
    cancelReport,
    regenerateReport,
    bulkDownload,
    bulkDelete,
    generateShareLink,
    generateQuickReport,
    getReportTemplates
  }
})