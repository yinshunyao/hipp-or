<script setup lang="ts">
import {
  ElAlert,
  ElButton,
  ElMessage,
  ElUpload,
  UploadProps,
  ElDescriptions,
  ElDescriptionsItem
} from 'element-plus'
import { ref } from 'vue'
import {
  postDataMigrationExportApi,
  postDataMigrationImportApi
} from '@/api/vadmin/system/dataMigration'

defineOptions({
  name: 'DataImportExport'
})

const exportLoading = ref(false)
const importLoading = ref(false)
const lastImportResult = ref<Recordable | null>(null)
const importFile = ref<File | null>(null)

const beforeUpload: UploadProps['beforeUpload'] = (rawFile) => {
  const ok = rawFile.name.toLowerCase().endsWith('.zip')
  if (!ok) {
    ElMessage.error('请上传 ZIP 格式的导出包')
  }
  const maxMb = 100
  if (rawFile.size / 1024 / 1024 > maxMb) {
    ElMessage.error(`文件不能超过 ${maxMb}MB`)
    return false
  }
  return ok
}

const onFileChange: UploadProps['onChange'] = (uploadFile) => {
  importFile.value = uploadFile.raw || null
  lastImportResult.value = null
}

const handleExport = async () => {
  exportLoading.value = true
  try {
    const res = await postDataMigrationExportApi()
    const blob = res.data as Blob
    if (blob.type && blob.type.includes('json')) {
      const text = await blob.text()
      try {
        const j = JSON.parse(text)
        ElMessage.error(j.message || '导出失败')
      } catch {
        ElMessage.error('导出失败')
      }
      return
    }
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `hipp-or-data-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.zip`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出已开始下载')
  } finally {
    exportLoading.value = false
  }
}

const handleImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请先选择 ZIP 文件')
    return
  }
  importLoading.value = true
  lastImportResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    const res = await postDataMigrationImportApi(formData)
    if (res) {
      lastImportResult.value = res.data as Recordable
      ElMessage.success((res.data as Recordable)?.message || '导入完成')
    }
  } finally {
    importLoading.value = false
  }
}
</script>

<template>
  <div class="data-import-export">
    <ElAlert
      type="warning"
      show-icon
      :closable="false"
      title="导入将清空并覆盖当前库中与导出包一致的各业务表数据（全量替换）。请在操作前自行备份，并仅在可信来源的包上执行导入。"
      class="mb-16px"
    />

    <div class="mb-24px">
      <h3 class="text-16px font-600 mb-8px">导出</h3>
      <p class="text-14px text-[var(--el-text-color-secondary)] mb-12px">
        生成包含 manifest 与各表 JSON 的 ZIP，可用于环境迁移或离线存档。导出记录操作者信息于
        manifest。
      </p>
      <ElButton type="primary" :loading="exportLoading" @click="handleExport">导出数据</ElButton>
    </div>

    <div>
      <h3 class="text-16px font-600 mb-8px">导入</h3>
      <p class="text-14px text-[var(--el-text-color-secondary)] mb-12px">
        仅支持由本系统同版本导出的 ZIP；表清单不一致将拒绝导入。
      </p>
      <div class="flex flex-wrap items-center gap-12px mb-12px">
        <ElUpload
          :show-file-list="true"
          :limit="1"
          :auto-upload="false"
          :before-upload="beforeUpload"
          :on-change="onFileChange"
          accept=".zip"
        >
          <ElButton type="default">选择 ZIP 文件</ElButton>
        </ElUpload>
        <ElButton
          type="danger"
          :loading="importLoading"
          :disabled="!importFile"
          @click="handleImport"
        >
          执行导入
        </ElButton>
      </div>

      <ElDescriptions v-if="lastImportResult" :column="1" border class="max-w-800px">
        <ElDescriptionsItem label="策略">{{ lastImportResult.import_strategy }}</ElDescriptionsItem>
        <ElDescriptionsItem label="写入行数">
          {{ lastImportResult.rows_inserted }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="说明">{{ lastImportResult.message }}</ElDescriptionsItem>
      </ElDescriptions>
    </div>
  </div>
</template>

<style scoped lang="less"></style>
