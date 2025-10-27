import { test, expect } from '@playwright/test'

test.describe('SOC Platform E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:3000')
  })

  test('should display login page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('SOC Security Platform')
    await expect(page.locator('input[placeholder="用户名"]')).toBeVisible()
    await expect(page.locator('input[placeholder="密码"]')).toBeVisible()
    await expect(page.locator('button:has-text("登录")')).toBeVisible()
  })

  test('should login with valid credentials', async ({ page }) => {
    // Fill login form
    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')

    // Click login button
    await page.click('button:has-text("登录")')

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/)
    await expect(page.locator('h1')).toContainText('安全态势总览')
  })

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill login form with invalid credentials
    await page.fill('input[placeholder="用户名"]', 'invalid')
    await page.fill('input[placeholder="密码"]', 'invalid')

    // Click login button
    await page.click('button:has-text("登录")')

    // Should show error message
    await expect(page.locator('.el-message--error')).toBeVisible()
  })

  test('should navigate to dashboard after login', async ({ page }) => {
    // Login
    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')
    await page.click('button:has-text("登录")')

    // Wait for dashboard to load
    await page.waitForURL(/.*dashboard/)

    // Check dashboard elements
    await expect(page.locator('h1')).toContainText('安全态势总览')
    await expect(page.locator('.stat-card')).toHaveCount(4)
    await expect(page.locator('.chart-card')).toHaveCount(2)
  })

  test('should navigate between pages using sidebar', async ({ page }) => {
    // Login first
    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')
    await page.click('button:has-text("登录")')
    await page.waitForURL(/.*dashboard/)

    // Navigate to assets page
    await page.click('.sidebar-menu a[href="/assets"]')
    await expect(page).toHaveURL(/.*assets/)
    await expect(page.locator('h1')).toContainText('资产管理')

    // Navigate to tasks page
    await page.click('.sidebar-menu a[href="/tasks"]')
    await expect(page).toHaveURL(/.*tasks/)
    await expect(page.locator('h1')).toContainText('扫描任务')

    // Navigate to vulnerabilities page
    await page.click('.sidebar-menu a[href="/vulnerabilities"]')
    await expect(page).toHaveURL(/.*vulnerabilities/)
    await expect(page.locator('h1')).toContainText('漏洞管理')
  })

  test('should create new asset', async ({ page }) => {
    // Login
    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')
    await page.click('button:has-text("登录")')
    await page.waitForURL(/.*dashboard/)

    // Navigate to assets page
    await page.click('.sidebar-menu a[href="/assets"]')
    await page.waitForURL(/.*assets/)

    // Click create asset button
    await page.click('button:has-text("添加资产")')
    await expect(page).toHaveURL(/.*assets\/create/)

    // Fill asset form
    await page.fill('input[placeholder="请输入资产名称"]', 'Test Asset')
    await page.selectOption('select[placeholder="请选择资产类型"]', 'domain')
    await page.fill('input[placeholder*="example.com"]', 'test.example.com')

    // Submit form
    await page.click('button:has-text("添加资产")')

    // Should redirect back to assets list
    await expect(page).toHaveURL(/.*assets$/)
  })

  test('should toggle dark theme', async ({ page }) => {
    // Login
    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')
    await page.click('button:has-text("登录")')
    await page.waitForURL(/.*dashboard/)

    // Check initial theme
    const html = page.locator('html')
    await expect(html).not.toHaveClass('dark')

    // Click theme toggle button
    await page.click('.header-right button:has(.el-icon)')

    // Check dark theme is applied
    await expect(html).toHaveClass('dark')

    // Click again to toggle back
    await page.click('.header-right button:has(.el-icon)')
    await expect(html).not.toHaveClass('dark')
  })

  test('should logout successfully', async ({ page }) => {
    // Login
    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')
    await page.click('button:has-text("登录")')
    await page.waitForURL(/.*dashboard/)

    // Click user dropdown
    await page.click('.user-dropdown')

    // Click logout
    await page.click('text="退出登录"')

    // Confirm logout
    await page.click('button:has-text("确定")')

    // Should redirect to login page
    await expect(page).toHaveURL('/')
    await expect(page.locator('h1')).toContainText('SOC Security Platform')
  })

  test('should display asset statistics on dashboard', async ({ page }) => {
    // Login
    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')
    await page.click('button:has-text("登录")')
    await page.waitForURL(/.*dashboard/)

    // Check statistics cards
    const statCards = page.locator('.stat-card')
    await expect(statCards).toHaveCount(4)

    // Check that numbers are displayed
    await expect(statCards.first().locator('.stat-number')).toContainText(/\d+/)
  })

  test('should filter assets by type', async ({ page }) => {
    // Login
    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')
    await page.click('button:has-text("登录")')
    await page.waitForURL(/.*dashboard/)

    // Navigate to assets
    await page.click('.sidebar-menu a[href="/assets"]')
    await page.waitForURL(/.*assets/)

    // Use type filter
    await page.selectOption('select[placeholder="资产类型"]', 'domain')

    // Check that table updates (this would require actual data)
    await expect(page.locator('.el-table')).toBeVisible()
  })
})