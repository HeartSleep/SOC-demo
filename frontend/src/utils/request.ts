import axios, { AxiosResponse, AxiosError, AxiosRequestConfig } from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { getToken, removeToken, getCsrfToken, fetchCsrfToken } from '@/utils/auth'
import router from '@/router'

// 请求配置
interface RequestConfig extends AxiosRequestConfig {
  __showedLoading?: boolean
  __retryCount?: number
}

// 重试配置
const RETRY_CONFIG = {
  maxRetries: 3,           // 最大重试次数
  retryDelay: 1000,        // 重试延迟（毫秒）
  retryStatusCodes: [408, 429, 500, 502, 503, 504]  // 需要重试的 HTTP 状态码
}

// 超时配置
const TIMEOUT_CONFIG = {
  default: 30000,          // 默认超时 30s
  long: 120000,            // 长请求超时 120s
  file: 300000              // 文件操作超时 300s
}

// Create axios instance with optimized defaults
const service = axios.create({
  baseURL: '/api/v1',
  timeout: TIMEOUT_CONFIG.default,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 重试拦截器
service.interceptors.response.use(
  undefined,
  async (error: AxiosError) => {
    const config = error.config as RequestConfig | undefined
    
    // 检查是否应该重试
    if (config && !config.__retryCount) {
      config.__retryCount = 0
    }
    
    const shouldRetry = 
      config &&
      !config.__retryCount &&
      config.__retryCount < RETRY_CONFIG.maxRetries &&
      error.response &&
      RETRY_CONFIG.retryStatusCodes.includes(error.response.status)
    
    if (shouldRetry) {
      config!.__retryCount!++
      
      // 指数退避延迟
      const delay = RETRY_CONFIG.retryDelay * Math.pow(2, config!.__retryCount! - 1)
      
      console.log(`Request failed with ${error.response?.status}, retrying in ${delay}ms (attempt ${config!.__retryCount})`)
      
      await new Promise(resolve => setTimeout(resolve, delay))
      return service(config!)
    }
    
    // 超过重试次数或不需要重试，继续处理错误
    return Promise.reject(error)
  }
)

let loadingInstance: ReturnType<typeof ElLoading.service> | null = null
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
    (config as RequestConfig).__showedLoading = shouldShowLoading

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
    const config = error.config as RequestConfig | undefined
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
    const config = response.config as RequestConfig | undefined
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
    const config = error.config as RequestConfig | undefined
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
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        case 502:
        case 503:
        case 504:
          ElMessage.error('服务暂不可用，请稍后再试')
          break
        default:
          // 处理后端返回的错误详情
          const errorMessage = (data as { detail?: string })?.detail || 
                             (data as { message?: string })?.message ||
                             `请求失败: ${status}`
          ElMessage.error(errorMessage)
      }
    } else {
      // 网络错误处理
      if (error.code === 'ECONNABORTED') {
        ElMessage.error('请求超时，请检查网络连接')
      } else if (error.message?.includes('Network Error')) {
        ElMessage.error('网络错误，请检查网络连接')
      } else {
        ElMessage.error('网络错误，请检查网络连接')
      }
    }

    return Promise.reject(error)
  }
)

// 导出带超时配置的请求方法
export const requestWithTimeout = {
  get: <T = unknown>(url: string, config?: AxiosRequestConfig & { timeout?: number }): Promise<T> => {
    return service.get(url, { ...config, timeout: config?.timeout || TIMEOUT_CONFIG.default })
  },
  post: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig & { timeout?: number }): Promise<T> => {
    return service.post(url, data, { ...config, timeout: config?.timeout || TIMEOUT_CONFIG.default })
  },
  put: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig & { timeout?: number }): Promise<T> => {
    return service.put(url, data, { ...config, timeout: config?.timeout || TIMEOUT_CONFIG.default })
  },
  delete: <T = unknown>(url: string, config?: AxiosRequestConfig & { timeout?: number }): Promise<T> => {
    return service.delete(url, { ...config, timeout: config?.timeout || TIMEOUT_CONFIG.default })
  }
}

export default service
export { service as request, TIMEOUT_CONFIG }