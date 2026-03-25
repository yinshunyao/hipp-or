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
  ElDescriptionsItem,
  ElSelect,
  ElOption,
  ElUpload
} from 'element-plus'
import { addAgentApi, putAgentApi, testAgentApi, publishAgentApi } from '@/api/vadmin/agent_manager'
import { BaseButton } from '@/components/Button'
import { useAuthStore } from '@/store/modules/auth'
import type { UploadProps } from 'element-plus'

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
const DEFAULT_SERVICE_TYPES = ['需求分析', '商业评估'] as const

const authStore = useAuthStore()
const token = computed(() => authStore.getToken)

const formData = ref({
  id: null as number | null,
  api_server: '',
  app_key: '',
  service_type: '' as string,
  remark: ''
})

const agentInfo = ref<any>(null)
const saveLoading = ref(false)
const testLoading = ref(false)
const publishLoading = ref(false)
const isTested = ref(false)
const avatarNonce = ref(0)
const avatarUploading = ref(false)

const withCacheBust = (
  url: string | null | undefined,
  version: string | number | null | undefined
) => {
  if (!url) return ''
  const v = version ?? Date.now()
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}v=${encodeURIComponent(String(v))}`
}

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
          service_type: props.currentRow.service_type || '',
          remark: props.currentRow.remark || ''
        }
        isTested.value = props.currentRow.is_tested || false
        if (props.currentRow.name) {
          agentInfo.value = props.currentRow
        } else {
          agentInfo.value = null
        }
      } else {
        formData.value = { id: null, api_server: '', app_key: '', service_type: '', remark: '' }
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

const ensureTagsString = (tags: string[] | null | undefined) => {
  const arr = (tags || []).map((t) => String(t).trim()).filter(Boolean)
  return JSON.stringify(arr)
}

const getEditableTags = () => {
  return parseTags(agentInfo.value?.tags || null)
}

const setEditableTags = (tags: string[]) => {
  if (!agentInfo.value) agentInfo.value = {}
  agentInfo.value.tags = ensureTagsString(tags)
}

const beforeAvatarUpload: UploadProps['beforeUpload'] = (rawFile) => {
  const isIMAGE = ['image/jpeg', 'image/gif', 'image/png'].includes(rawFile.type)
  const isLtSize = rawFile.size / 1024 / 1024 < 5
  if (!isIMAGE) ElMessage.error('头像图片必须是 JPG/GIF/PNG 格式!')
  if (!isLtSize) ElMessage.error('头像图片大小不能超过 5MB!')
  return isIMAGE && isLtSize
}

const handleAvatarSuccess: UploadProps['onSuccess'] = (response) => {
  avatarUploading.value = false
  if (response?.code === 200) {
    const url = response?.data?.remote_path || response?.data
    if (!url) {
      ElMessage.error('上传失败：未返回图片地址')
      return
    }
    if (!agentInfo.value) agentInfo.value = {}
    agentInfo.value.icon_type = 'image'
    agentInfo.value.icon = null
    agentInfo.value.icon_url = url
    avatarNonce.value += 1
  } else {
    ElMessage.error(response?.message || '上传失败')
  }
}

const handleAvatarError: UploadProps['onError'] = () => {
  avatarUploading.value = false
  ElMessage.error('上传失败')
}

const handleAvatarProgress: UploadProps['onProgress'] = () => {
  avatarUploading.value = true
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
      remark: formData.value.remark || null,
      service_type: formData.value.service_type?.trim() || null
    })
    if (res.code === 200) {
      ElMessage.success('测试成功')
      agentInfo.value = res.data
      isTested.value = true
      avatarNonce.value += 1
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
    data.service_type = formData.value.service_type?.trim() || null
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
      <ElFormItem label="智能客服类型" prop="service_type">
        <ElSelect
          v-model="formData.service_type"
          filterable
          allow-create
          default-first-option
          clearable
          placeholder="选择或输入类型"
          style="width: 100%"
        >
          <ElOption v-for="t in DEFAULT_SERVICE_TYPES" :key="t" :label="t" :value="t" />
        </ElSelect>
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
      <ElForm label-width="120px" style="margin-bottom: 12px">
        <ElFormItem label="头像">
          <div style="display: flex; align-items: center; gap: 12px">
            <img
              v-if="agentInfo.icon_url"
              :src="withCacheBust(agentInfo.icon_url, agentInfo.update_datetime || avatarNonce)"
              style="width: 56px; height: 56px; border-radius: 8px; object-fit: cover"
            />
            <span
              v-else-if="agentInfo.icon"
              :style="{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '56px',
                height: '56px',
                borderRadius: '8px',
                backgroundColor: agentInfo.icon_background || '#E0E0E0',
                fontSize: '28px'
              }"
            >
              {{ agentInfo.icon }}
            </span>
            <span
              v-else
              style="width: 56px; height: 56px; border-radius: 8px; background: #f2f2f2"
            ></span>

            <ElUpload
              class="agent-avatar-uploader"
              action="/api/vadmin/system/upload/image/to/local"
              :data="{ path: 'agent' }"
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :on-success="handleAvatarSuccess"
              :on-error="handleAvatarError"
              :on-progress="handleAvatarProgress"
              accept="image/jpeg,image/gif,image/png"
              name="file"
              :headers="{ Authorization: token }"
              :disabled="avatarUploading"
            >
              <BaseButton type="primary" :loading="avatarUploading">上传头像</BaseButton>
            </ElUpload>
          </div>
        </ElFormItem>

        <ElFormItem label="名称">
          <ElInput v-model="agentInfo.name" placeholder="请输入名称" />
        </ElFormItem>

        <ElFormItem label="描述">
          <ElInput
            v-model="agentInfo.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </ElFormItem>

        <ElFormItem label="标签">
          <ElSelect
            :model-value="getEditableTags()"
            multiple
            filterable
            allow-create
            default-first-option
            clearable
            placeholder="选择或输入标签"
            style="width: 100%"
            @update:model-value="(v: any) => setEditableTags(v as string[])"
          />
        </ElFormItem>
      </ElForm>

      <ElDescriptions title="智能客服信息" :column="2" border>
        <ElDescriptionsItem label="头像">
          <img
            v-if="agentInfo.icon_url"
            :src="withCacheBust(agentInfo.icon_url, agentInfo.update_datetime || avatarNonce)"
            style="width: 40px; height: 40px; border-radius: 6px"
          />
          <span
            v-else-if="agentInfo.icon"
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
          <span v-else>-</span>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="名称">{{ agentInfo.name || '-' }}</ElDescriptionsItem>
        <ElDescriptionsItem label="类型">
          {{ agentInfo.service_type || formData.service_type || '-' }}
        </ElDescriptionsItem>
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
