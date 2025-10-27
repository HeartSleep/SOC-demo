import axios, { AxiosResponse, AxiosError } from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { getToken, removeToken, getCsrfToken, fetchCsrfToken } from '@/utils/auth'
import router from '@/router'

// Create axios instance
const service = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

let loadingInstance: any = null
let requestCount = 0
const requestCountLock = { value: 0 }

// Helper function to safely manage request count
const incrementRequestCount = () => {
  requestCountLock.value++
  requestCount = requestCountLock.value
}

const decrementRequestCount = () => {
  requestCountLock.value = Math.max(0, requestCountLock.value - 1)
  requestCount = requestCountLock.value
}

// Request interceptor
service.interceptors.request.use(
  (config) => {
    // Only show loading for slow operations, not for quick GET requests
    const shouldShowLoading = config.method === 'post' || config.method === 'put' || config.method === 'delete'

    if (shouldShowLoading) {
      incrementRequestCount()
      if (!loadingInstance && requestCount > 0) {
        loadingInstance = ElLoading.service({
          lock: true,
          text: 'Loading...',
          background: 'rgba(0, 0, 0, 0.5)'
        })
      }
    }

    // Store loading state in config for response interceptor
    (config as any).__showedLoading = shouldShowLoading

    // Add authentication token to headers
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add CSRF token for state-changing methods
    if (['post', 'put', 'delete', 'patch'].includes(config.method?.toLowerCase() || '')) {
      let csrfToken = getCsrfToken()

      // If no CSRF token, try to fetch it
      if (!csrfToken) {
        // Note: This is sync in interceptor, token will be used on next request
        fetchCsrfToken().catch(err => console.error('CSRF token fetch failed:', err))
      } else {
        config.headers['X-CSRF-Token'] = csrfToken
      }
    }

    return config
  },
  (error: AxiosError) => {
    // Check if this request was showing loading
    const config = error.config as any
    if (config?.__showedLoading) {
      decrementRequestCount()
      if (requestCount === 0 && loadingInstance) {
        setTimeout(() => {
          if (requestCount === 0 && loadingInstance) {
            loadingInstance.close()
            loadingInstance = null
          }
        }, 100)
      }
    }
    return Promise.reject(error)
  }
)

// Response interceptor
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const config = response.config as any
    const wasShowingLoading = config?.__showedLoading

    if (wasShowingLoading) {
      decrementRequestCount()
      if (requestCount === 0 && loadingInstance) {
        setTimeout(() => {
          if (requestCount === 0 && loadingInstance) {
            loadingInstance.close()
            loadingInstance = null
          }
        }, 100)
      }
    }

    return response.data
  },
  (error: AxiosError) => {
    const config = error.config as any
    const wasShowingLoading = config?.__showedLoading

    if (wasShowingLoading) {
      decrementRequestCount()
      if (requestCount === 0 && loadingInstance) {
        setTimeout(() => {
          if (requestCount === 0 && loadingInstance) {
            loadingInstance.close()
            loadingInstance = null
          }
        }, 100)
      }
    }

    const { response } = error

    if (response) {
      const { status, data } = response

      switch (status) {
        case 401:
          ElMessage.error('未授权，请重新登录')
          removeToken()
          router.push('/login')
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error((data as any)?.detail || `请求失败: ${status}`)
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

export default service
export { service as request }