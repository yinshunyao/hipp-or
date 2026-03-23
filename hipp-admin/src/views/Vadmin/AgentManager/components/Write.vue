<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import {
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElTag,
  ElDescriptions,
  ElDescriptionsItem
} from 'element-plus'
import { addAgentApi, putAgentApi, testAgentApi, publishAgentApi } from '@/api/vadmin/agent_manager'
import { BaseButton } from '@/components/Button'

interface Props {
  modelValue: boolean
  title?: string
  currentRow?: any
}

const props = withDefaults(defineProps<Props>(), {
  title: '新增智能客服',
  currentRow: null
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'save-success'): void
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref()
const formData = ref({
  id: null as number | null,
  api_server: '',
  app_key: '',
  remark: ''
})

const agentInfo = ref<any>(null)
const saveLoading = ref(false)
const testLoading = ref(false)
const publishLoading = ref(false)
const isTested = ref(false)

const rules = {
  api_server: [{ required: true, message: '请输入API服务器地址', trigger: 'blur' }],
  app_key: [{ required: true, message: '请输入APP_KEY', trigger: 'blur' }]
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      if (props.currentRow) {
        formData.value = {
          id: props.currentRow.id,
          api_server: props.currentRow.api_server || '',
          app_key: props.currentRow.app_key || '',
          remark: props.currentRow.remark || ''
        }
        isTested.value = props.currentRow.is_tested || false
        if (props.currentRow.name) {
          agentInfo.value = props.currentRow
        } else {
          agentInfo.value = null
        }
      } else {
        formData.value = { id: null, api_server: '', app_key: '', remark: '' }
        agentInfo.value = null
        isTested.value = false
      }
    }
  }
)

const parseTags = (tagsStr: string | null): string[] => {
  if (!tagsStr) return []
  try {
    return JSON.parse(tagsStr)
  } catch {
    return []
  }
}

const handleTest = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  testLoading.value = true
  try {
    const res = await testAgentApi({
      id: formData.value.id,
      api_server: formData.value.api_server,
      app_key: formData.value.app_key,
      remark: formData.value.remark || null
    })
    if (res.code === 200) {
      ElMessage.success('测试成功')
      agentInfo.value = res.data
      isTested.value = true
      if (res.data?.id != null) {
        formData.value.id = res.data.id
      }
    } else {
      ElMessage.error(res.message || '测试失败')
    }
  } catch {
    ElMessage.error('测试失败')
  } finally {
    testLoading.value = false
  }
}

const handleSave = async (silent = false) => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saveLoading.value = true
  try {
    const data: Record<string, any> = { ...formData.value, is_tested: isTested.value }
    const info = agentInfo.value
    if (info) {
      const keys = [
        'name',
        'description',
        'tags',
        'mode',
        'icon_type',
        'icon',
        'icon_background',
        'icon_url',
        'webapp_config'
      ] as const
      keys.forEach((k) => {
        if (info[k] != null && info[k] !== '') {
          data[k] = info[k]
        }
      })
    }
    let res
    if (data.id) {
      res = await putAgentApi(data)
    } else {
      res = await addAgentApi(data)
    }
    if (res.code === 200) {
      if (!silent) {
        ElMessage.success('保存成功')
        emit('save-success')
      }
      if (res.data?.id) {
        formData.value.id = res.data.id
      }
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saveLoading.value = false
  }
}

const handlePublish = async () => {
  if (!isTested.value) {
    ElMessage.warning('请先通过连通性测试后再上架')
    return
  }
  if (!formData.value.id) {
    ElMessage.warning('请先保存数据')
    return
  }

  publishLoading.value = true
  try {
    const res = await publishAgentApi(formData.value.id!)
    if (res.code === 200) {
      ElMessage.success('上架成功')
      emit('save-success')
    } else {
      ElMessage.error(res.message || '上架失败')
    }
  } catch {
    ElMessage.error('上架失败')
  } finally {
    publishLoading.value = false
  }
}
</script>

<template>
  <ElDialog v-model="dialogVisible" :title="title" width="640px" destroy-on-close>
    <ElForm ref="formRef" :model="formData" :rules="rules" label-width="120px">
      <ElFormItem label="API服务器地址" prop="api_server">
        <ElInput v-model="formData.api_server" placeholder="例如 http://192.168.1.123/v1" />
      </ElFormItem>
      <ElFormItem label="APP_KEY" prop="app_key">
        <ElInput v-model="formData.app_key" placeholder="请输入Dify应用的APP_KEY" />
      </ElFormItem>
      <ElFormItem label="备注">
        <ElInput v-model="formData.remark" placeholder="请输入备注（可选）" />
      </ElFormItem>
      <ElFormItem>
        <BaseButton type="primary" :loading="testLoading" @click="handleTest">测试</BaseButton>
        <BaseButton type="success" :loading="saveLoading" @click="() => handleSave(false)">
          保存
        </BaseButton>
        <BaseButton type="warning" :loading="publishLoading" @click="handlePublish">
          上架
        </BaseButton>
      </ElFormItem>
    </ElForm>

    <template v-if="agentInfo">
      <el-divider />
      <ElDescriptions title="智能客服信息" :column="2" border>
        <ElDescriptionsItem label="头像">
          <span
            v-if="agentInfo.icon"
            :style="{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '40px',
              height: '40px',
              borderRadius: '6px',
              backgroundColor: agentInfo.icon_background || '#E0E0E0',
              fontSize: '22px'
            }"
          >
            {{ agentInfo.icon }}
          </span>
          <img
            v-else-if="agentInfo.icon_url"
            :src="agentInfo.icon_url"
            style="width: 40px; height: 40px; border-radius: 6px"
          />
          <span v-else>-</span>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="名称">{{ agentInfo.name || '-' }}</ElDescriptionsItem>
        <ElDescriptionsItem label="描述" :span="2">
          {{ agentInfo.description || '-' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="标签" :span="2">
          <ElTag
            v-for="tag in parseTags(agentInfo.tags)"
            :key="tag"
            size="small"
            style="margin-right: 4px"
          >
            {{ tag }}
          </ElTag>
          <span v-if="parseTags(agentInfo.tags).length === 0">-</span>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="备注">{{ agentInfo.remark || '-' }}</ElDescriptionsItem>
        <ElDescriptionsItem label="上架状态">
          <ElTag :type="agentInfo.status === 'published' ? 'success' : 'info'">
            {{ agentInfo.status === 'published' ? '已上架' : '草稿' }}
          </ElTag>
        </ElDescriptionsItem>
      </ElDescriptions>
    </template>
  </ElDialog>
</template>
