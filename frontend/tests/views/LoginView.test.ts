import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import LoginView from '@/views/auth/LoginView.vue'
import { useUserStore } from '@/store/user'

// Mock router
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
}

vi.mock('vue-router', () => ({
  useRouter: () => mockRouter,
  useRoute: () => ({
    params: {},
    query: {},
  }),
}))

// Mock Element Plus ElMessage
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn(),
    },
  }
})

describe('LoginView', () => {
  let wrapper
  let userStore

  beforeEach(() => {
    setActivePinia(createPinia())
    userStore = useUserStore()

    // Mock userStore.login
    userStore.login = vi.fn().mockResolvedValue({
      access_token: 'mock-token',
      user: { id: '1', username: 'testuser' }
    })

    wrapper = mount(LoginView, {
      global: {
        plugins: [createPinia()],
      },
    })
  })

  it('renders login form', () => {
    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="用户名"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="密码"]').exists()).toBe(true)
    expect(wrapper.find('button').text()).toBe('登录')
  })

  it('displays app title', () => {
    expect(wrapper.find('h1').text()).toBe('SOC Security Platform')
    expect(wrapper.find('p').text()).toBe('企业级网络安全测试扫描平台')
  })

  it('validates required fields', async () => {
    const loginButton = wrapper.find('button')

    // Try to submit without filling fields
    await loginButton.trigger('click')

    // Should not call login if validation fails
    expect(userStore.login).not.toHaveBeenCalled()
  })

  it('submits form with valid data', async () => {
    const usernameInput = wrapper.find('input[placeholder="用户名"]')
    const passwordInput = wrapper.find('input[placeholder="密码"]')
    const form = wrapper.find('form')

    // Fill in form
    await usernameInput.setValue('testuser')
    await passwordInput.setValue('testpass123')

    // Submit form
    await form.trigger('submit.prevent')

    expect(userStore.login).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'testpass123'
    })
  })

  it('handles login error', async () => {
    userStore.login = vi.fn().mockRejectedValue(new Error('Invalid credentials'))

    const usernameInput = wrapper.find('input[placeholder="用户名"]')
    const passwordInput = wrapper.find('input[placeholder="密码"]')
    const form = wrapper.find('form')

    await usernameInput.setValue('testuser')
    await passwordInput.setValue('wrongpass')
    await form.trigger('submit.prevent')

    expect(userStore.login).toHaveBeenCalled()
  })

  it('shows loading state during login', async () => {
    // Make login return a pending promise
    let resolveLogin
    userStore.login = vi.fn().mockReturnValue(new Promise(resolve => {
      resolveLogin = resolve
    }))

    const form = wrapper.find('form')
    const usernameInput = wrapper.find('input[placeholder="用户名"]')
    const passwordInput = wrapper.find('input[placeholder="密码"]')

    await usernameInput.setValue('testuser')
    await passwordInput.setValue('testpass123')
    await form.trigger('submit.prevent')

    // Button should show loading state
    const button = wrapper.find('button')
    expect(button.attributes('loading')).toBeDefined()

    // Resolve the login
    resolveLogin({ access_token: 'token' })
    await wrapper.vm.$nextTick()
  })
})