import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { login, getUserInfo, logout } from '@/api/auth'
import { setToken, getToken, removeToken } from '@/utils/auth'
import router from '@/router'

interface UserInfo {
  id: string
  username: string
  email: string
  full_name: string
  role: string
  permissions: string[]
  avatar_url?: string
}

interface UserState {
  token: string | null
  userInfo: UserInfo | null
  permissions: string[]
  loading: boolean
  error: string | null
}

// 通用错误处理函数
const handleError = (err: unknown, defaultMessage: string): string => {
  if (err instanceof Error) {
    return err.message || defaultMessage
  }
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const errorWithResponse = err as { response?: { data?: { detail?: string } } }
    return errorWithResponse.response?.data?.detail || defaultMessage
  }
  return defaultMessage
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: getToken(),
    userInfo: null,
    permissions: [],
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    hasPermission: (state) => (permission: string) => {
      return state.permissions.includes(permission) || state.userInfo?.role === 'admin'
    }
  },

  actions: {
    async login(loginData: { username: string; password: string }) {
      this.error = null
      this.loading = true
      try {
        const response = await login(loginData)

        this.token = response.access_token
        this.userInfo = response.user
        this.permissions = response.user.permissions || []

        setToken(response.access_token)

        ElMessage.success('登录成功')
        router.push('/dashboard')

        return response
      } catch (err) {
        this.error = handleError(err, '登录失败')
        ElMessage.error(this.error)
        throw err
      } finally {
        this.loading = false
      }
    },

    async logout() {
      this.loading = true
      try {
        await logout()
      } catch (error) {
        console.error('Logout API failed:', error)
      } finally {
        this.token = null
        this.userInfo = null
        this.permissions = []
        this.loading = false
        this.error = null
        removeToken()
        router.push('/login')
        ElMessage.success('已退出登录')
      }
    },

    async getUserInfo() {
      this.error = null
      this.loading = true
      try {
        const response = await getUserInfo()
        this.userInfo = response
        this.permissions = response.permissions || []
        return response
      } catch (err) {
        this.error = handleError(err, '获取用户信息失败')
        this.logout()
        throw err
      } finally {
        this.loading = false
      }
    },

    async restoreSession() {
      if (!this.token) {
        return false
      }

      try {
        await this.getUserInfo()
        return true
      } catch (error) {
        this.logout()
        return false
      }
    },

    updateUserInfo(userInfo: Partial<UserInfo>) {
      if (this.userInfo) {
        this.userInfo = { ...this.userInfo, ...userInfo }
      }
    },

    async getUsers() {
      // For demo mode, return mock users
      return [
        { id: 'demo_admin', username: 'admin', full_name: 'Demo Admin', role: 'admin' },
        { id: 'demo_analyst', username: 'analyst', full_name: 'Demo Analyst', role: 'analyst' },
        { id: 'demo_user', username: 'demo', full_name: 'Demo User', role: 'viewer' }
      ]
    }
  }
})