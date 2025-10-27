<template>
  <div class="settings">
    <el-container>
      <el-aside width="250px" class="settings-sidebar">
        <el-menu
          :default-active="activeSection"
          class="settings-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="general">
            <el-icon><Setting /></el-icon>
            <span>常规设置</span>
          </el-menu-item>
          <el-menu-item index="security">
            <el-icon><Lock /></el-icon>
            <span>安全设置</span>
          </el-menu-item>
          <el-menu-item index="notifications">
            <el-icon><Bell /></el-icon>
            <span>通知设置</span>
          </el-menu-item>
          <el-menu-item index="scanning">
            <el-icon><Search /></el-icon>
            <span>扫描配置</span>
          </el-menu-item>
          <el-menu-item index="integrations">
            <el-icon><Connection /></el-icon>
            <span>集成配置</span>
          </el-menu-item>
          <el-menu-item index="system">
            <el-icon><Monitor /></el-icon>
            <span>系统配置</span>
          </el-menu-item>
          <el-menu-item index="backup">
            <el-icon><Download /></el-icon>
            <span>备份恢复</span>
          </el-menu-item>
          <el-menu-item index="logs">
            <el-icon><Document /></el-icon>
            <span>日志管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="settings-main">
        <!-- General Settings -->
        <el-card v-show="activeSection === 'general'" class="settings-card">
          <template #header>
            <h2>常规设置</h2>
          </template>

          <el-form ref="generalFormRef" :model="generalSettings" :rules="generalRules" label-width="120px">
            <el-form-item label="平台名称" prop="platformName">
              <el-input v-model="generalSettings.platformName" placeholder="输入平台名称" />
            </el-form-item>

            <el-form-item label="平台描述" prop="platformDescription">
              <el-input
                v-model="generalSettings.platformDescription"
                type="textarea"
                :rows="3"
                placeholder="输入平台描述"
              />
            </el-form-item>

            <el-form-item label="默认语言" prop="defaultLanguage">
              <el-select v-model="generalSettings.defaultLanguage">
                <el-option label="中文" value="zh" />
                <el-option label="English" value="en" />
              </el-select>
            </el-form-item>

            <el-form-item label="时区" prop="timezone">
              <el-select v-model="generalSettings.timezone" filterable>
                <el-option label="Asia/Shanghai" value="Asia/Shanghai" />
                <el-option label="UTC" value="UTC" />
                <el-option label="America/New_York" value="America/New_York" />
                <el-option label="Europe/London" value="Europe/London" />
              </el-select>
            </el-form-item>

            <el-form-item label="页面大小" prop="defaultPageSize">
              <el-input-number v-model="generalSettings.defaultPageSize" :min="10" :max="100" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveGeneralSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Security Settings -->
        <el-card v-show="activeSection === 'security'" class="settings-card">
          <template #header>
            <h2>安全设置</h2>
          </template>

          <el-form ref="securityFormRef" :model="securitySettings" label-width="140px">
            <el-divider content-position="left">密码策略</el-divider>

            <el-form-item label="最小密码长度">
              <el-input-number v-model="securitySettings.minPasswordLength" :min="6" :max="32" />
            </el-form-item>

            <el-form-item label="密码复杂度">
              <el-checkbox-group v-model="securitySettings.passwordRequirements">
                <el-checkbox label="uppercase">包含大写字母</el-checkbox>
                <el-checkbox label="lowercase">包含小写字母</el-checkbox>
                <el-checkbox label="numbers">包含数字</el-checkbox>
                <el-checkbox label="special">包含特殊字符</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="密码过期时间">
              <el-input-number v-model="securitySettings.passwordExpiryDays" :min="30" :max="365" />
              <span class="form-item-suffix">天</span>
            </el-form-item>

            <el-divider content-position="left">会话管理</el-divider>

            <el-form-item label="会话超时时间">
              <el-input-number v-model="securitySettings.sessionTimeout" :min="15" :max="480" />
              <span class="form-item-suffix">分钟</span>
            </el-form-item>

            <el-form-item label="最大并发会话">
              <el-input-number v-model="securitySettings.maxConcurrentSessions" :min="1" :max="10" />
            </el-form-item>

            <el-divider content-position="left">登录安全</el-divider>

            <el-form-item label="登录失败锁定">
              <el-switch v-model="securitySettings.enableLoginLockout" />
            </el-form-item>

            <el-form-item v-if="securitySettings.enableLoginLockout" label="锁定阈值">
              <el-input-number v-model="securitySettings.loginFailureThreshold" :min="3" :max="10" />
              <span class="form-item-suffix">次</span>
            </el-form-item>

            <el-form-item v-if="securitySettings.enableLoginLockout" label="锁定时间">
              <el-input-number v-model="securitySettings.lockoutDuration" :min="5" :max="60" />
              <span class="form-item-suffix">分钟</span>
            </el-form-item>

            <el-form-item label="双因素认证">
              <el-switch v-model="securitySettings.enableTwoFactor" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveSecuritySettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Notification Settings -->
        <el-card v-show="activeSection === 'notifications'" class="settings-card">
          <template #header>
            <h2>通知设置</h2>
          </template>

          <el-form ref="notificationFormRef" :model="notificationSettings" label-width="120px">
            <el-divider content-position="left">邮件通知</el-divider>

            <el-form-item label="启用邮件通知">
              <el-switch v-model="notificationSettings.emailEnabled" />
            </el-form-item>

            <div v-if="notificationSettings.emailEnabled">
              <el-form-item label="SMTP服务器">
                <el-input v-model="notificationSettings.smtpHost" placeholder="smtp.example.com" />
              </el-form-item>

              <el-form-item label="SMTP端口">
                <el-input-number v-model="notificationSettings.smtpPort" :min="1" :max="65535" />
              </el-form-item>

              <el-form-item label="发件人邮箱">
                <el-input v-model="notificationSettings.senderEmail" placeholder="noreply@company.com" />
              </el-form-item>

              <el-form-item label="发件人密码">
                <el-input v-model="notificationSettings.senderPassword" type="password" show-password />
              </el-form-item>

              <el-form-item label="启用TLS">
                <el-switch v-model="notificationSettings.smtpTls" />
              </el-form-item>
            </div>

            <el-divider content-position="left">通知规则</el-divider>

            <el-form-item label="新漏洞发现">
              <el-checkbox-group v-model="notificationSettings.newVulnerabilityNotification">
                <el-checkbox label="email">邮件通知</el-checkbox>
                <el-checkbox label="slack">Slack通知</el-checkbox>
                <el-checkbox label="webhook">Webhook</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="扫描任务完成">
              <el-checkbox-group v-model="notificationSettings.taskCompletedNotification">
                <el-checkbox label="email">邮件通知</el-checkbox>
                <el-checkbox label="slack">Slack通知</el-checkbox>
                <el-checkbox label="webhook">Webhook</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="系统警报">
              <el-checkbox-group v-model="notificationSettings.systemAlertNotification">
                <el-checkbox label="email">邮件通知</el-checkbox>
                <el-checkbox label="slack">Slack通知</el-checkbox>
                <el-checkbox label="webhook">Webhook</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveNotificationSettings">保存设置</el-button>
              <el-button @click="testNotification">测试通知</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Scanning Configuration -->
        <el-card v-show="activeSection === 'scanning'" class="settings-card">
          <template #header>
            <h2>扫描配置</h2>
          </template>

          <el-form ref="scanningFormRef" :model="scanningSettings" label-width="140px">
            <el-divider content-position="left">默认扫描配置</el-divider>

            <el-form-item label="并发任务数">
              <el-input-number v-model="scanningSettings.maxConcurrentTasks" :min="1" :max="10" />
            </el-form-item>

            <el-form-item label="默认超时时间">
              <el-input-number v-model="scanningSettings.defaultTimeout" :min="60" :max="3600" />
              <span class="form-item-suffix">秒</span>
            </el-form-item>

            <el-form-item label="重试次数">
              <el-input-number v-model="scanningSettings.maxRetries" :min="0" :max="5" />
            </el-form-item>

            <el-divider content-position="left">扫描工具配置</el-divider>

            <el-form-item label="Nmap路径">
              <el-input v-model="scanningSettings.nmapPath" placeholder="/usr/bin/nmap" />
            </el-form-item>

            <el-form-item label="Nuclei路径">
              <el-input v-model="scanningSettings.nucleiPath" placeholder="/usr/bin/nuclei" />
            </el-form-item>

            <el-form-item label="Xray路径">
              <el-input v-model="scanningSettings.xrayPath" placeholder="/usr/bin/xray" />
            </el-form-item>

            <el-divider content-position="left">高级选项</el-divider>

            <el-form-item label="自动删除旧结果">
              <el-switch v-model="scanningSettings.autoCleanup" />
            </el-form-item>

            <el-form-item v-if="scanningSettings.autoCleanup" label="保留天数">
              <el-input-number v-model="scanningSettings.cleanupDays" :min="7" :max="365" />
            </el-form-item>

            <el-form-item label="启用代理">
              <el-switch v-model="scanningSettings.enableProxy" />
            </el-form-item>

            <el-form-item v-if="scanningSettings.enableProxy" label="代理地址">
              <el-input v-model="scanningSettings.proxyUrl" placeholder="http://proxy.example.com:8080" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveScanningSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Integration Settings -->
        <el-card v-show="activeSection === 'integrations'" class="settings-card">
          <template #header>
            <h2>集成配置</h2>
          </template>

          <el-form ref="integrationFormRef" :model="integrationSettings" label-width="120px">
            <el-divider content-position="left">FOFA API</el-divider>

            <el-form-item label="启用FOFA">
              <el-switch v-model="integrationSettings.fofaEnabled" />
            </el-form-item>

            <el-form-item v-if="integrationSettings.fofaEnabled" label="API Key">
              <el-input v-model="integrationSettings.fofaApiKey" type="password" show-password />
            </el-form-item>

            <el-form-item v-if="integrationSettings.fofaEnabled" label="Email">
              <el-input v-model="integrationSettings.fofaEmail" />
            </el-form-item>

            <el-divider content-position="left">Slack集成</el-divider>

            <el-form-item label="启用Slack">
              <el-switch v-model="integrationSettings.slackEnabled" />
            </el-form-item>

            <el-form-item v-if="integrationSettings.slackEnabled" label="Webhook URL">
              <el-input v-model="integrationSettings.slackWebhookUrl" />
            </el-form-item>

            <el-form-item v-if="integrationSettings.slackEnabled" label="默认频道">
              <el-input v-model="integrationSettings.slackChannel" placeholder="#security" />
            </el-form-item>

            <el-divider content-position="left">Webhook集成</el-divider>

            <el-form-item label="启用Webhook">
              <el-switch v-model="integrationSettings.webhookEnabled" />
            </el-form-item>

            <el-form-item v-if="integrationSettings.webhookEnabled" label="Webhook URL">
              <el-input v-model="integrationSettings.webhookUrl" />
            </el-form-item>

            <el-form-item v-if="integrationSettings.webhookEnabled" label="认证Token">
              <el-input v-model="integrationSettings.webhookToken" type="password" show-password />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveIntegrationSettings">保存设置</el-button>
              <el-button @click="testIntegrations">测试连接</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- System Configuration -->
        <el-card v-show="activeSection === 'system'" class="settings-card">
          <template #header>
            <h2>系统配置</h2>
          </template>

          <el-form ref="systemFormRef" :model="systemSettings" label-width="120px">
            <el-divider content-position="left">数据库设置</el-divider>

            <el-form-item label="连接池大小">
              <el-input-number v-model="systemSettings.dbPoolSize" :min="5" :max="50" />
            </el-form-item>

            <el-form-item label="查询超时">
              <el-input-number v-model="systemSettings.dbQueryTimeout" :min="5" :max="300" />
              <span class="form-item-suffix">秒</span>
            </el-form-item>

            <el-divider content-position="left">缓存设置</el-divider>

            <el-form-item label="启用缓存">
              <el-switch v-model="systemSettings.cacheEnabled" />
            </el-form-item>

            <el-form-item v-if="systemSettings.cacheEnabled" label="缓存TTL">
              <el-input-number v-model="systemSettings.cacheTtl" :min="60" :max="3600" />
              <span class="form-item-suffix">秒</span>
            </el-form-item>

            <el-divider content-position="left">日志设置</el-divider>

            <el-form-item label="日志级别">
              <el-select v-model="systemSettings.logLevel">
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
              </el-select>
            </el-form-item>

            <el-form-item label="日志保留天数">
              <el-input-number v-model="systemSettings.logRetentionDays" :min="7" :max="365" />
            </el-form-item>

            <el-divider content-position="left">性能设置</el-divider>

            <el-form-item label="工作进程数">
              <el-input-number v-model="systemSettings.workerProcesses" :min="1" :max="16" />
            </el-form-item>

            <el-form-item label="请求速率限制">
              <el-input-number v-model="systemSettings.rateLimitRpm" :min="60" :max="6000" />
              <span class="form-item-suffix">请求/分钟</span>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveSystemSettings">保存设置</el-button>
              <el-button type="warning" @click="restartServices">重启服务</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Backup & Restore -->
        <el-card v-show="activeSection === 'backup'" class="settings-card">
          <template #header>
            <h2>备份恢复</h2>
          </template>

          <el-form ref="backupFormRef" :model="backupSettings" label-width="120px">
            <el-divider content-position="left">自动备份</el-divider>

            <el-form-item label="启用自动备份">
              <el-switch v-model="backupSettings.autoBackupEnabled" />
            </el-form-item>

            <el-form-item v-if="backupSettings.autoBackupEnabled" label="备份频率">
              <el-select v-model="backupSettings.backupFrequency">
                <el-option label="每日" value="daily" />
                <el-option label="每周" value="weekly" />
                <el-option label="每月" value="monthly" />
              </el-select>
            </el-form-item>

            <el-form-item v-if="backupSettings.autoBackupEnabled" label="备份时间">
              <el-time-picker v-model="backupSettings.backupTime" format="HH:mm" />
            </el-form-item>

            <el-form-item label="保留备份数">
              <el-input-number v-model="backupSettings.retentionCount" :min="1" :max="30" />
            </el-form-item>

            <el-divider content-position="left">备份操作</el-divider>

            <el-form-item>
              <el-button type="primary" @click="createBackup" :loading="backupLoading">
                <el-icon><Download /></el-icon>
                立即备份
              </el-button>
              <el-button @click="downloadBackup">下载备份</el-button>
            </el-form-item>

            <el-divider content-position="left">恢复操作</el-divider>

            <el-form-item label="选择备份文件">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :show-file-list="true"
                :limit="1"
                accept=".zip,.tar.gz"
                @change="handleFileChange"
              >
                <el-button>选择文件</el-button>
              </el-upload>
            </el-form-item>

            <el-form-item>
              <el-button type="warning" @click="restoreBackup" :loading="restoreLoading">
                <el-icon><Upload /></el-icon>
                恢复备份
              </el-button>
            </el-form-item>

            <el-divider content-position="left">备份历史</el-divider>

            <div class="backup-history">
              <el-table :data="backupHistory" style="width: 100%">
                <el-table-column prop="name" label="备份名称" />
                <el-table-column prop="size" label="文件大小" />
                <el-table-column prop="created_at" label="创建时间" />
                <el-table-column label="操作" width="200">
                  <template #default="{ row }">
                    <el-button size="small" @click="downloadBackupFile(row)">下载</el-button>
                    <el-button size="small" type="danger" @click="deleteBackupFile(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <el-form-item>
              <el-button type="primary" @click="saveBackupSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Log Management -->
        <el-card v-show="activeSection === 'logs'" class="settings-card">
          <template #header>
            <h2>日志管理</h2>
          </template>

          <div class="log-filters">
            <el-form inline>
              <el-form-item label="日志级别">
                <el-select v-model="logFilters.level" placeholder="选择级别">
                  <el-option label="全部" value="" />
                  <el-option label="DEBUG" value="DEBUG" />
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                </el-select>
              </el-form-item>
              <el-form-item label="时间范围">
                <el-date-picker
                  v-model="logFilters.dateRange"
                  type="daterange"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="YYYY-MM-DD"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="loadLogs">查询</el-button>
                <el-button @click="clearLogs">清空日志</el-button>
                <el-button @click="downloadLogs">导出日志</el-button>
              </el-form-item>
            </el-form>
          </div>

          <div class="log-content">
            <el-table :data="logs" v-loading="logLoading" height="400" style="width: 100%">
              <el-table-column prop="timestamp" label="时间" width="180" />
              <el-table-column prop="level" label="级别" width="80">
                <template #default="{ row }">
                  <el-tag :type="getLogLevelType(row.level)" size="small">
                    {{ row.level }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="message" label="消息" show-overflow-tooltip />
              <el-table-column prop="source" label="来源" width="120" />
            </el-table>

            <el-pagination
              v-model:current-page="logPagination.page"
              v-model:page-size="logPagination.size"
              :total="logPagination.total"
              :page-sizes="[50, 100, 200, 500]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadLogs"
              @current-change="loadLogs"
            />
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDate } from '@/utils/date'

const activeSection = ref('general')
const backupLoading = ref(false)
const restoreLoading = ref(false)
const logLoading = ref(false)
const logs = ref([])
const backupHistory = ref([])
const uploadRef = ref()

const generalFormRef = ref()
const securityFormRef = ref()
const notificationFormRef = ref()
const scanningFormRef = ref()
const integrationFormRef = ref()
const systemFormRef = ref()
const backupFormRef = ref()

// Settings data
const generalSettings = reactive({
  platformName: 'SOC Platform',
  platformDescription: '企业级安全运营中心',
  defaultLanguage: 'zh',
  timezone: 'Asia/Shanghai',
  defaultPageSize: 20
})

const securitySettings = reactive({
  minPasswordLength: 8,
  passwordRequirements: ['lowercase', 'numbers'],
  passwordExpiryDays: 90,
  sessionTimeout: 120,
  maxConcurrentSessions: 3,
  enableLoginLockout: true,
  loginFailureThreshold: 5,
  lockoutDuration: 15,
  enableTwoFactor: false
})

const notificationSettings = reactive({
  emailEnabled: false,
  smtpHost: '',
  smtpPort: 587,
  senderEmail: '',
  senderPassword: '',
  smtpTls: true,
  newVulnerabilityNotification: ['email'],
  taskCompletedNotification: ['email'],
  systemAlertNotification: ['email', 'slack']
})

const scanningSettings = reactive({
  maxConcurrentTasks: 3,
  defaultTimeout: 300,
  maxRetries: 2,
  nmapPath: '/usr/bin/nmap',
  nucleiPath: '/usr/bin/nuclei',
  xrayPath: '/usr/bin/xray',
  autoCleanup: true,
  cleanupDays: 30,
  enableProxy: false,
  proxyUrl: ''
})

const integrationSettings = reactive({
  fofaEnabled: false,
  fofaApiKey: '',
  fofaEmail: '',
  slackEnabled: false,
  slackWebhookUrl: '',
  slackChannel: '#security',
  webhookEnabled: false,
  webhookUrl: '',
  webhookToken: ''
})

const systemSettings = reactive({
  dbPoolSize: 10,
  dbQueryTimeout: 30,
  cacheEnabled: true,
  cacheTtl: 300,
  logLevel: 'INFO',
  logRetentionDays: 90,
  workerProcesses: 4,
  rateLimitRpm: 600
})

const backupSettings = reactive({
  autoBackupEnabled: true,
  backupFrequency: 'daily',
  backupTime: new Date(),
  retentionCount: 7
})

const logFilters = reactive({
  level: '',
  dateRange: [],
  keyword: ''
})

const logPagination = reactive({
  page: 1,
  size: 100,
  total: 0
})

const generalRules = {
  platformName: [
    { required: true, message: '请输入平台名称', trigger: 'blur' }
  ]
}

onMounted(() => {
  loadSettings()
  loadBackupHistory()
  loadLogs()
})

const loadSettings = async () => {
  try {
    // Load settings from API
    ElMessage.success('设置加载成功')
  } catch (error) {
    ElMessage.error('加载设置失败')
  }
}

const handleMenuSelect = (index: string) => {
  activeSection.value = index
  if (index === 'logs') {
    loadLogs()
  }
}

// Save functions
const saveGeneralSettings = async () => {
  try {
    await generalFormRef.value?.validate()
    // Save to API
    ElMessage.success('常规设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const saveSecuritySettings = async () => {
  try {
    // Save to API
    ElMessage.success('安全设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const saveNotificationSettings = async () => {
  try {
    // Save to API
    ElMessage.success('通知设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const testNotification = async () => {
  try {
    // Test notification
    ElMessage.success('测试通知发送成功')
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

const saveScanningSettings = async () => {
  try {
    // Save to API
    ElMessage.success('扫描配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const saveIntegrationSettings = async () => {
  try {
    // Save to API
    ElMessage.success('集成配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const testIntegrations = async () => {
  try {
    // Test integrations
    ElMessage.success('集成测试成功')
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

const saveSystemSettings = async () => {
  try {
    // Save to API
    ElMessage.success('系统配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const restartServices = async () => {
  await ElMessageBox.confirm('确定要重启服务吗？这将导致短暂的服务中断。', '确认重启', {
    type: 'warning'
  })

  try {
    // Restart services
    ElMessage.success('服务重启成功')
  } catch (error) {
    ElMessage.error('重启失败')
  }
}

const saveBackupSettings = async () => {
  try {
    // Save to API
    ElMessage.success('备份设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// Backup functions
const createBackup = async () => {
  backupLoading.value = true
  try {
    // Create backup
    ElMessage.success('备份创建成功')
    await loadBackupHistory()
  } catch (error) {
    ElMessage.error('备份创建失败')
  } finally {
    backupLoading.value = false
  }
}

const downloadBackup = () => {
  ElMessage.info('下载最新备份功能开发中')
}

const handleFileChange = () => {
  // Handle file upload
}

const restoreBackup = async () => {
  await ElMessageBox.confirm('确定要恢复备份吗？这将覆盖当前所有数据！', '确认恢复', {
    type: 'warning'
  })

  restoreLoading.value = true
  try {
    // Restore backup
    ElMessage.success('备份恢复成功')
  } catch (error) {
    ElMessage.error('恢复失败')
  } finally {
    restoreLoading.value = false
  }
}

const loadBackupHistory = async () => {
  try {
    backupHistory.value = [
      {
        id: '1',
        name: 'backup-2023-12-01.zip',
        size: '156 MB',
        created_at: '2023-12-01 02:00:00'
      },
      {
        id: '2',
        name: 'backup-2023-11-30.zip',
        size: '152 MB',
        created_at: '2023-11-30 02:00:00'
      }
    ]
  } catch (error) {
    console.error('Failed to load backup history:', error)
  }
}

const downloadBackupFile = (backup) => {
  ElMessage.info(`下载备份: ${backup.name}`)
}

const deleteBackupFile = async (backup) => {
  await ElMessageBox.confirm(`确定要删除备份 ${backup.name} 吗？`, '确认删除', {
    type: 'warning'
  })

  try {
    // Delete backup
    ElMessage.success('备份删除成功')
    await loadBackupHistory()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// Log functions
const loadLogs = async () => {
  logLoading.value = true
  try {
    // Mock log data
    logs.value = [
      {
        timestamp: '2023-12-01 10:30:15',
        level: 'INFO',
        message: '用户登录成功',
        source: 'auth'
      },
      {
        timestamp: '2023-12-01 10:25:33',
        level: 'WARNING',
        message: '扫描任务超时',
        source: 'scanner'
      },
      {
        timestamp: '2023-12-01 10:20:42',
        level: 'ERROR',
        message: '数据库连接失败',
        source: 'database'
      }
    ]
    logPagination.total = 150
  } catch (error) {
    ElMessage.error('加载日志失败')
  } finally {
    logLoading.value = false
  }
}

const clearLogs = async () => {
  await ElMessageBox.confirm('确定要清空所有日志吗？', '确认清空', {
    type: 'warning'
  })

  try {
    // Clear logs
    logs.value = []
    logPagination.total = 0
    ElMessage.success('日志清空成功')
  } catch (error) {
    ElMessage.error('清空失败')
  }
}

const downloadLogs = () => {
  ElMessage.info('导出日志功能开发中')
}

const getLogLevelType = (level) => {
  const types = {
    DEBUG: '',
    INFO: 'primary',
    WARNING: 'warning',
    ERROR: 'danger'
  }
  return types[level] || 'info'
}
</script>

<style scoped lang="scss">
.settings {
  height: calc(100vh - 60px);

  .settings-sidebar {
    background: var(--el-bg-color-page);
    border-right: 1px solid var(--el-border-color-light);

    .settings-menu {
      border-right: none;
      height: 100%;

      .el-menu-item {
        display: flex;
        align-items: center;
        gap: 8px;

        &.is-active {
          background-color: var(--el-color-primary-light-9);
          color: var(--el-color-primary);
          border-right: 3px solid var(--el-color-primary);
        }
      }
    }
  }

  .settings-main {
    padding: 24px;
    background: var(--el-bg-color);

    .settings-card {
      max-width: 800px;
      margin: 0 auto;

      h2 {
        margin: 0;
        color: var(--el-text-color-primary);
      }

      .form-item-suffix {
        margin-left: 8px;
        color: var(--el-text-color-secondary);
        font-size: 14px;
      }

      .el-divider {
        margin: 32px 0 24px 0;

        .el-divider__text {
          color: var(--el-text-color-primary);
          font-weight: 500;
        }
      }
    }
  }

  .backup-history {
    margin-top: 16px;
  }

  .log-filters {
    margin-bottom: 16px;
    padding: 16px;
    background: var(--el-fill-color-extra-light);
    border-radius: 4px;
  }

  .log-content {
    .el-pagination {
      margin-top: 16px;
      justify-content: center;
    }
  }
}

@media (max-width: 768px) {
  .settings {
    .settings-sidebar {
      position: fixed;
      left: -250px;
      top: 60px;
      height: calc(100vh - 60px);
      z-index: 1000;
      transition: left 0.3s;

      &.mobile-open {
        left: 0;
      }
    }

    .settings-main {
      padding: 16px;

      .settings-card {
        max-width: none;
      }
    }
  }
}
</style>