import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import App from './App.vue'
import router from './router'
import './styles/index.scss'
import { fetchCsrfToken } from '@/utils/auth'

const app = createApp(App)

// Register Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// Initialize CSRF token before mounting
fetchCsrfToken().then(() => {
  console.log('CSRF token initialized')
}).catch(err => {
  console.warn('Failed to initialize CSRF token:', err)
}).finally(() => {
  app.mount('#app')
})