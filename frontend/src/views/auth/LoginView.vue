<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>SOC Security Platform</h1>
        <p>企业级网络安全测试扫描平台</p>
      </div>

      <el-form
        ref="loginForm"
        :model="loginData"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginData.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginData.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>&copy; 2024 SOC Security Platform. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const loading = ref(false)

const loginData = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const loginForm = ref()

const handleLogin = async () => {
  if (!loginForm.value) return

  try {
    await loginForm.value.validate()
    loading.value = true
    await userStore.login(loginData)
  } catch (error) {
    console.error('Login failed:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;

  h1 {
    font-size: 28px;
    color: #2c3e50;
    margin-bottom: 8px;
    font-weight: 600;
  }

  p {
    color: #7f8c8d;
    margin: 0;
    font-size: 14px;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 20px;
  }

  .login-button {
    width: 100%;
    height: 45px;
    font-size: 16px;
    border-radius: 6px;
  }
}

.login-footer {
  text-align: center;
  margin-top: 30px;

  p {
    color: #95a5a6;
    font-size: 12px;
    margin: 0;
  }
}
</style>