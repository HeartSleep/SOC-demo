<template>
  <div class="main-layout">
    <!-- Sidebar -->
    <el-aside :width="sidebarWidth" class="sidebar">
      <div class="logo">
        <div class="logo-icon">SOC</div>
        <span v-if="!appStore.sidebarCollapsed">Platform</span>
      </div>

      <el-menu
        :default-active="route.path"
        class="sidebar-menu"
        :collapse="appStore.sidebarCollapsed"
        :unique-opened="true"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>

        <el-sub-menu index="assets">
          <template #title>
            <el-icon><List /></el-icon>
            <span>资产管理</span>
          </template>
          <el-menu-item index="/assets">
            <span>资产列表</span>
          </el-menu-item>
          <el-menu-item index="/assets/create">
            <span>添加资产</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="tasks">
          <template #title>
            <el-icon><Operation /></el-icon>
            <span>扫描任务</span>
          </template>
          <el-menu-item index="/tasks">
            <span>任务列表</span>
          </el-menu-item>
          <el-menu-item index="/tasks/create">
            <span>创建任务</span>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/vulnerabilities">
          <el-icon><Warning /></el-icon>
          <span>漏洞管理</span>
        </el-menu-item>

        <el-sub-menu index="reports">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>报告中心</span>
          </template>
          <el-menu-item index="/reports">
            <span>报告列表</span>
          </el-menu-item>
          <el-menu-item index="/reports/create">
            <span>生成报告</span>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item
          v-if="userStore.hasPermission('system:admin')"
          index="/settings"
        >
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- Main Content -->
    <el-container class="main-container">
      <!-- Header -->
      <el-header class="header">
        <div class="header-left">
          <el-button
            type="text"
            @click="appStore.toggleSidebar"
          >
            <el-icon size="20">
              <Expand v-if="appStore.sidebarCollapsed" />
              <Fold v-else />
            </el-icon>
          </el-button>

          <el-breadcrumb separator="/">
            <el-breadcrumb-item
              v-for="item in breadcrumbs"
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-button
            type="text"
            @click="appStore.toggleTheme"
          >
            <el-icon>
              <Sunny v-if="appStore.isDark" />
              <Moon v-else />
            </el-icon>
          </el-button>

          <el-dropdown @command="handleCommand">
            <div class="user-dropdown">
              <el-avatar :src="userStore.userInfo?.avatar_url" />
              <span>{{ userStore.userInfo?.full_name }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Content -->
      <el-main class="content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/store/app'
import { useUserStore } from '@/store/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()

const sidebarWidth = computed(() =>
  appStore.sidebarCollapsed ? '64px' : '250px'
)

const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    path: item.path,
    title: item.meta?.title
  }))
})

const handleCommand = async (command: string) => {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning'
    })
    userStore.logout()
  } else if (command === 'profile') {
    // Navigate to profile page
  }
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
  display: flex;
}

.sidebar {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  transition: width 0.3s;

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    padding: 0 20px;
    border-bottom: 1px solid var(--el-border-color);
    font-weight: bold;
    font-size: 18px;

    .logo-icon {
      width: 32px;
      height: 32px;
      margin-right: 10px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: bold;
    }
  }

  .sidebar-menu {
    border-right: none;
    height: calc(100vh - 60px);
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);

  .header-left {
    display: flex;
    align-items: center;
    gap: 20px;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 15px;

    .user-dropdown {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 8px;
      border-radius: 4px;

      &:hover {
        background: var(--el-fill-color-light);
      }
    }
  }
}

.content {
  background: var(--el-bg-color-page);
  padding: 20px;
}
</style>