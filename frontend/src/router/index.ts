import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// Configure NProgress
NProgress.configure({ showSpinner: false })

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('@/layout/MainLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: { title: '仪表盘', icon: 'DataBoard' }
        },
        {
          path: 'assets',
          name: 'Assets',
          component: () => import('@/views/assets/AssetListView.vue'),
          meta: { title: '资产管理', icon: 'List' }
        },
        {
          path: 'assets/create',
          name: 'AssetCreate',
          component: () => import('@/views/assets/AssetCreateView.vue'),
          meta: { title: '添加资产', icon: 'Plus' }
        },
        {
          path: 'assets/:id',
          name: 'AssetDetail',
          component: () => import('@/views/assets/AssetDetailView.vue'),
          meta: { title: '资产详情', icon: 'View' }
        },
        {
          path: 'tasks',
          name: 'Tasks',
          component: () => import('@/views/tasks/TaskListView.vue'),
          meta: { title: '扫描任务', icon: 'Operation' }
        },
        {
          path: 'tasks/create',
          name: 'TaskCreate',
          component: () => import('@/views/tasks/TaskCreateView.vue'),
          meta: { title: '创建任务', icon: 'Plus' }
        },
        {
          path: 'tasks/:id',
          name: 'TaskDetail',
          component: () => import('@/views/tasks/TaskDetailView.vue'),
          meta: { title: '任务详情', icon: 'View' }
        },
        {
          path: 'vulnerabilities',
          name: 'Vulnerabilities',
          component: () => import('@/views/vulnerabilities/VulnerabilityListView.vue'),
          meta: { title: '漏洞管理', icon: 'Warning' }
        },
        {
          path: 'vulnerabilities/:id',
          name: 'VulnerabilityDetail',
          component: () => import('@/views/vulnerabilities/VulnerabilityDetailView.vue'),
          meta: { title: '漏洞详情', icon: 'View' }
        },
        {
          path: 'reports',
          name: 'Reports',
          component: () => import('@/views/reports/ReportListView.vue'),
          meta: { title: '报告中心', icon: 'Document' }
        },
        {
          path: 'reports/create',
          name: 'ReportCreate',
          component: () => import('@/views/reports/ReportCreateView.vue'),
          meta: { title: '生成报告', icon: 'Plus' }
        },
        {
          path: 'reports/:id',
          name: 'ReportDetail',
          component: () => import('@/views/reports/ReportDetailView.vue'),
          meta: { title: '报告详情', icon: 'View' }
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/settings/SettingsView.vue'),
          meta: { title: '系统设置', icon: 'Setting', requiresAdmin: true }
        },
        {
          path: 'api-security',
          name: 'APISecurity',
          component: () => import('@/views/api-security/APIScanListView.vue'),
          meta: { title: 'API安全检测', icon: 'Lock' }
        },
        {
          path: 'api-security/:id',
          name: 'APIScanDetail',
          component: () => import('@/views/api-security/APIScanDetailView.vue'),
          meta: { title: 'API扫描详情', icon: 'View' }
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFoundView.vue')
    }
  ]
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  NProgress.start()

  const userStore = useUserStore()

  // Check if route requires authentication
  if (to.matched.some(record => record.meta.requiresAuth !== false)) {
    if (!userStore.isAuthenticated) {
      // Try to restore user session
      const restored = await userStore.restoreSession()
      if (!restored) {
        next('/login')
        return
      }
    }

    // Check admin permissions
    if (to.matched.some(record => record.meta.requiresAdmin)) {
      if (userStore.userInfo?.role !== 'admin') {
        ElMessage.error('权限不足')
        next('/dashboard')
        return
      }
    }
  }

  // Redirect to dashboard if already authenticated and trying to access login
  if (to.path === '/login' && userStore.isAuthenticated) {
    next('/dashboard')
    return
  }

  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router