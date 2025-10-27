<template>
  <div class="report-create">
    <div class="page-header">
      <h1>生成报告</h1>
      <p>创建新的安全评估报告</p>
    </div>

    <el-card>
      <el-form
        ref="reportForm"
        :model="reportData"
        :rules="rules"
        label-width="120px"
        @submit.prevent="handleSubmit"
      >
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="报告标题" prop="title">
              <el-input v-model="reportData.title" placeholder="请输入报告标题" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="报告类型" prop="type">
              <el-select v-model="reportData.type" placeholder="请选择报告类型">
                <el-option label="漏洞报告" value="vulnerability" />
                <el-option label="资产报告" value="asset" />
                <el-option label="扫描报告" value="scan" />
                <el-option label="综合报告" value="comprehensive" />
                <el-option label="合规报告" value="compliance" />
                <el-option label="趋势报告" value="trend" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="密级" prop="classification">
              <el-select v-model="reportData.classification" placeholder="请选择报告密级">
                <el-option label="公开" value="public" />
                <el-option label="内部" value="internal" />
                <el-option label="机密" value="confidential" />
                <el-option label="绝密" value="secret" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="报告模板" prop="template">
              <el-select v-model="reportData.template" placeholder="选择报告模板">
                <el-option label="标准模板" value="standard" />
                <el-option label="简洁模板" value="simple" />
                <el-option label="详细模板" value="detailed" />
                <el-option label="执行摘要模板" value="executive" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="报告描述">
          <el-input
            v-model="reportData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入报告描述"
          />
        </el-form-item>

        <el-form-item label="输出格式" prop="format">
          <el-checkbox-group v-model="reportData.config.formats">
            <el-checkbox label="pdf">PDF</el-checkbox>
            <el-checkbox label="html">HTML</el-checkbox>
            <el-checkbox label="word">Word</el-checkbox>
            <el-checkbox label="excel">Excel</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="报告内容" prop="sections">
          <el-checkbox-group v-model="reportData.config.sections">
            <el-checkbox label="summary">概览摘要</el-checkbox>
            <el-checkbox label="assets">资产信息</el-checkbox>
            <el-checkbox label="vulnerabilities">漏洞详情</el-checkbox>
            <el-checkbox label="tasks">扫描任务</el-checkbox>
            <el-checkbox label="trends">趋势分析</el-checkbox>
            <el-checkbox label="recommendations">修复建议</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-radio-group v-model="periodType">
            <el-radio label="preset">预设时间段</el-radio>
            <el-radio label="custom">自定义</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-row :gutter="24">
          <el-col v-if="periodType === 'preset'" :span="12">
            <el-form-item label="时间段">
              <el-select v-model="reportData.config.period">
                <el-option label="最近7天" value="last_7_days" />
                <el-option label="最近30天" value="last_30_days" />
                <el-option label="最近90天" value="last_90_days" />
                <el-option label="本月" value="this_month" />
                <el-option label="上月" value="last_month" />
                <el-option label="全部" value="all_time" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col v-if="periodType === 'custom'" :span="12">
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="reportData.config.date_range"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="高级选项" name="advanced">
            <el-form-item label="包含图表">
              <el-switch v-model="reportData.config.include_charts" />
            </el-form-item>

            <el-form-item label="语言">
              <el-select v-model="reportData.language">
                <el-option label="中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>

            <el-form-item label="自动发送">
              <el-switch v-model="reportData.config.auto_send" />
            </el-form-item>

            <el-form-item v-if="reportData.config.auto_send" label="收件人">
              <el-select
                v-model="reportData.config.recipients"
                multiple
                filterable
                allow-create
                placeholder="输入邮箱地址"
                style="width: 100%"
              >
                <el-option
                  v-for="email in commonEmails"
                  :key="email"
                  :label="email"
                  :value="email"
                />
              </el-select>
            </el-form-item>
          </el-collapse-item>
        </el-collapse>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">生成报告</el-button>
          <el-button @click="handlePreview">预览</el-button>
          <el-button @click="$router.push('/reports')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useReportStore } from '@/store/report'

const router = useRouter()
const reportStore = useReportStore()

const reportForm = ref()
const submitting = ref(false)
const periodType = ref('preset')
const activeCollapse = ref([])

const reportData = reactive({
  title: '',
  type: 'vulnerability',
  description: '',
  classification: 'internal',
  template: 'standard',
  language: 'zh-CN',
  config: {
    formats: ['pdf'],
    sections: ['summary', 'vulnerabilities', 'recommendations'],
    period: 'last_30_days',
    date_range: null,
    include_charts: true,
    auto_send: false,
    recipients: []
  }
})

const commonEmails = ref(['admin@example.com', 'security@example.com', 'report@example.com'])

const rules = {
  title: [{ required: true, message: '请输入报告标题', trigger: 'blur' }],
  type: [{ required: true, message: '请选择报告类型', trigger: 'change' }],
  classification: [{ required: true, message: '请选择报告密级', trigger: 'change' }],
  template: [{ required: true, message: '请选择报告模板', trigger: 'change' }]
}

const handleSubmit = async () => {
  try {
    await reportForm.value.validate()
    submitting.value = true

    const submitData = {
      title: reportData.title,
      type: reportData.type,
      description: reportData.description,
      classification: reportData.classification,
      template: reportData.template,
      language: reportData.language,
      config: {
        ...reportData.config,
        formats: reportData.config.formats
      }
    }

    await reportStore.createReport(submitData)
    ElMessage.success('报告生成任务已提交')
    router.push('/reports')
  } catch (error) {
    if (error.errors) {
      return
    }
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

const handlePreview = () => {
  ElMessage.info('预览功能开发中')
}
</script>

<style scoped lang="scss">
.report-create {
  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: 24px;
      margin-bottom: 8px;
      color: var(--el-text-color-primary);
    }

    p {
      color: var(--el-text-color-regular);
      margin: 0;
    }
  }

  .el-form {
    max-width: 1200px;
  }

  .config-section {
    margin-bottom: 24px;
    padding: 16px;
    background: var(--el-fill-color-light);
    border-radius: 4px;

    h4 {
      margin-top: 0;
      margin-bottom: 16px;
      font-size: 16px;
      color: var(--el-text-color-primary);
    }
  }
}
</style>
