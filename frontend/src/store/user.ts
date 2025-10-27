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
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: getToken(),
    userInfo: null,
    permissions: []
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    hasPermission: (state) => (permission: string) => {
      return state.permissions.includes(permission) || state.userInfo?.role === 'admin'
    }
  },

  actions: {
    async login(loginData: { username: string; password: string }) {
      try {
        const response = await login(loginData)

        this.token = response.access_token
        this.userInfo = response.user
        this.permissions = response.user.permissions || []

        setToken(response.access_token)

        ElMessage.success('登录成功')
        router.push('/dashboard')

        return response
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '登录失败')
        throw error
      }
    },

    async logout() {
      try {
        await logout()
      } catch (error) {
        console.error('Logout API failed:', error)
      } finally {
        this.token = null
        this.userInfo = null
        this.permissions = []
        removeToken()
        router.push('/login')
        ElMessage.success('已退出登录')
      }
    },

    async getUserInfo() {
      try {
        const response = await getUserInfo()
        this.userInfo = response
        this.permissions = response.permissions || []
        return response
      } catch (error) {
        this.logout()
        throw error
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