import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Task, TaskFilters, TaskCreateData, TaskUpdateData } from '@/types/task'
import { request } from '@/utils/request'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)

  const getTasks = async (params?: TaskFilters) => {
    const response = await request.get('/tasks/', { params })
    return response
  }

  const getTask = async (id: string): Promise<Task> => {
    const response = await request.get(`/tasks/${id}`)
    return response
  }

  const createTask = async (data: TaskCreateData): Promise<Task> => {
    const response = await request.post('/tasks/', data)
    return response
  }

  const updateTask = async (id: string, data: TaskUpdateData): Promise<Task> => {
    const response = await request.put(`/tasks/${id}`, data)
    return response
  }

  const deleteTask = async (id: string): Promise<void> => {
    await request.delete(`/tasks/${id}`)
  }

  const startTask = async (id: string): Promise<void> => {
    await request.post(`/tasks/${id}/start`)
  }

  const stopTask = async (id: string): Promise<void> => {
    await request.post(`/tasks/${id}/stop`)
  }

  const restartTask = async (id: string): Promise<void> => {
    await request.post(`/tasks/${id}/restart`)
  }

  const bulkStop = async (ids: string[]): Promise<void> => {
    await request.post('/tasks/bulk-stop', { ids })
  }

  const bulkDelete = async (ids: string[]): Promise<void> => {
    await request.delete('/tasks/bulk', { data: { ids } })
  }

  const cloneTask = async (id: string): Promise<Task> => {
    const response = await request.post(`/tasks/${id}/clone`)
    return response
  }

  const exportTaskResults = async (id: string) => {
    const response = await request.get(`/tasks/${id}/export`)
    return response
  }

  const getTaskLogs = async (id: string) => {
    const response = await request.get(`/tasks/${id}/logs`)
    return response
  }

  const getTaskResults = async (id: string) => {
    const response = await request.get(`/tasks/${id}/results`)
    return response
  }

  return {
    tasks,
    currentTask,
    loading,
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