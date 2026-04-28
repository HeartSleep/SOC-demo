<template>
  <div class="report-create-view">
    <div class="page-header">
      <el-button @click="handleBack">
        <el-icon><Back /></el-icon>
        返回
      </el-button>
      <h2>生成报告</h2>
    </div>

    <el-card>
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="报告名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入报告名称" />
        </el-form-item>

        <el-form-item label="报告类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择报告类型">
            <el-option label="漏洞报告" value="vulnerability" />
            <el-option label="资产报告" value="asset" />
            <el-option label="综合报告" value="summary" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围" prop="dateRange">
          <el-date-picker
            v-model="formData.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>

        <el-form-item label="包含内容">
          <el-checkbox-group v-model="formData.includeItems">
            <el-checkbox label="漏洞详情">漏洞详情</el-checkbox>
            <el-checkbox label="资产清单">资产清单</el-checkbox>
            <el-checkbox label="趋势分析">趋势分析</el-checkbox>
            <el-checkbox label="修复建议">修复建议</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="报告格式">
          <el-radio-group v-model="formData.format">
            <el-radio label="pdf">PDF</el-radio>
            <el-radio label="html">HTML</el-radio>
            <el-radio label="docx">Word</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            生成报告
          </el-button>
          <el-button @click="handleBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back } from '@element-plus/icons-vue'
import { useReportStore } from '@/store/report'
import type { ReportCreateData } from '@/types/report'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const reportStore = useReportStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const formData = reactive<ReportCreateData & {
  dateRange: [Date, Date] | null
  includeItems: string[]
  format: string
}>({
  name: '',
  type: 'summary',
  dateRange: null,
  includeItems: ['漏洞详情', '资产清单'],
  format: 'pdf'
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入报告名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择报告类型', trigger: 'change' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    const submitData: ReportCreateData = {
      name: formData.name,
      type: formData.type as ReportCreateData['type']
    }

    await reportStore.createReport(submitData)
    ElMessage.success('报告生成中，请稍后查看')
    router.push('/reports')
  } catch (error) {
    console.error('创建报告失败:', error)
  } finally {
    loading.value = false
  }
}

const handleBack = () => {
  router.back()
}
</script>

<style scoped>
.report-create-view {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}
</style>
