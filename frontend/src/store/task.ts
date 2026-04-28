import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Task, TaskFilters, TaskCreateData, TaskUpdateData } from '@/types/task'
import { request } from '@/utils/request'

// 通用错误处理函数
const handleError = (err: unknown, defaultMessage: string): string => {
  if (err instanceof Error) {
    return err.message || defaultMessage
  }
  return defaultMessage
}

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 后端已实现的接口
  const getTasks = async (params?: TaskFilters) => {
    error.value = null
    try {
      const response = await request.get('/tasks/', { params })
      return response
    } catch (err) {
      error.value = handleError(err, '获取任务列表失败')
      throw err
    }
  }

  const getTask = async (id: string): Promise<Task> => {
    error.value = null
    try {
      const response = await request.get(`/tasks/${id}`)
      return response
    } catch (err) {
      error.value = handleError(err, '获取任务详情失败')
      throw err
    }
  }

  const createTask = async (data: TaskCreateData): Promise<Task> => {
    error.value = null
    loading.value = true
    try {
      const response = await request.post('/tasks/', data)
      return response
    } catch (err) {
      error.value = handleError(err, '创建任务失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateTask = async (id: string, data: TaskUpdateData): Promise<Task> => {
    error.value = null
    loading.value = true
    try {
      const response = await request.put(`/tasks/${id}`, data)
      return response
    } catch (err) {
      error.value = handleError(err, '更新任务失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteTask = async (id: string): Promise<void> => {
    error.value = null
    loading.value = true
    try {
      await request.delete(`/tasks/${id}`)
    } catch (err) {
      error.value = handleError(err, '删除任务失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const startTask = async (id: string): Promise<void> => {
    error.value = null
    loading.value = true
    try {
      await request.post(`/tasks/${id}/start`)
    } catch (err) {
      error.value = handleError(err, '启动任务失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const stopTask = async (id: string): Promise<void> => {
    error.value = null
    loading.value = true
    try {
      await request.post(`/tasks/${id}/stop`)
    } catch (err) {
      error.value = handleError(err, '停止任务失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const restartTask = async (id: string): Promise<void> => {
    error.value = null
    loading.value = true
    try {
      await request.post(`/tasks/${id}/restart`)
    } catch (err) {
      error.value = handleError(err, '重启任务失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const bulkStop = async (ids: string[]): Promise<void> => {
    error.value = null
    loading.value = true
    try {
      await request.post('/tasks/bulk-stop', { ids })
    } catch (err) {
      error.value = handleError(err, '批量停止任务失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const bulkDelete = async (ids: string[]): Promise<void> => {
    error.value = null
    loading.value = true
    try {
      await request.delete('/tasks/bulk', { data: { ids } })
    } catch (err) {
      error.value = handleError(err, '批量删除任务失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const cloneTask = async (id: string): Promise<Task> => {
    error.value = null
    loading.value = true
    try {
      const response = await request.post(`/tasks/${id}/clone`)
      return response
    } catch (err) {
      error.value = handleError(err, '克隆任务失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const exportTaskResults = async (id: string) => {
    error.value = null
    try {
      const response = await request.get(`/tasks/${id}/export`)
      return response
    } catch (err) {
      error.value = handleError(err, '导出任务结果失败')
      throw err
    }
  }

  const getTaskLogs = async (id: string) => {
    error.value = null
    try {
      const response = await request.get(`/tasks/${id}/logs`)
      return response
    } catch (err) {
      error.value = handleError(err, '获取任务日志失败')
      throw err
    }
  }

  const getTaskResults = async (id: string) => {
    error.value = null
    try {
      const response = await request.get(`/tasks/${id}/results`)
      return response
    } catch (err) {
      error.value = handleError(err, '获取任务结果失败')
      throw err
    }
  }

  return {
    tasks,
    currentTask,
    loading,
    error,
    getTasks,
    getTask,
    createTask,
    updateTask,
    deleteTask,
    startTask,
    stopTask,
    restartTask,
    bulkStop,
    bulkDelete,
    cloneTask,
    exportTaskResults,
    getTaskLogs,
    getTaskResults
  }
})