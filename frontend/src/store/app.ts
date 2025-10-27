import { defineStore } from 'pinia'

interface AppState {
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
  language: string
  loading: boolean
}

export const useAppStore = defineStore('app', {
  state: (): AppState => ({
    sidebarCollapsed: false,
    theme: 'light',
    language: 'zh-CN',
    loading: false
  }),

  getters: {
    isDark: (state) => state.theme === 'dark'
  },

  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },

    setSidebarCollapsed(collapsed: boolean) {
      this.sidebarCollapsed = collapsed
    },

    toggleTheme() {
      this.theme = this.theme === 'light' ? 'dark' : 'light'
      this.applyTheme()
    },

    setTheme(theme: 'light' | 'dark') {
      this.theme = theme
      this.applyTheme()
    },

    applyTheme() {
      const html = document.documentElement
      if (this.theme === 'dark') {
        html.classList.add('dark')
      } else {
        html.classList.remove('dark')
      }
      localStorage.setItem('theme', this.theme)
    },

    setLanguage(language: string) {
      this.language = language
      localStorage.setItem('language', language)
    },

    setLoading(loading: boolean) {
      this.loading = loading
    },

    initApp() {
      // Initialize theme
      const savedTheme = localStorage.getItem('theme') as 'light' | 'dark'
      if (savedTheme) {
        this.setTheme(savedTheme)
      }

      // Initialize language
      const savedLanguage = localStorage.getItem('language')
      if (savedLanguage) {
        this.setLanguage(savedLanguage)
      }

      // Initialize sidebar state
      const sidebarState = localStorage.getItem('sidebarCollapsed')
      if (sidebarState) {
        this.setSidebarCollapsed(JSON.parse(sidebarState))
      }
    }
  }
})