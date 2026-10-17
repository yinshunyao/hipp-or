<script setup lang="tsx">
import { reactive, ref, unref } from 'vue'
import {
  createEntitlementsApi,
  getEntitlementsApi,
  voidEntitlementApi
} from '@/api/vadmin/commerce'
import { useTable } from '@/hooks/web/useTable'
import { Table, TableColumn } from '@/components/Table'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { BaseButton } from '@/components/Button'
import {
  ElInput,
  ElInputNumber,
  ElMessage,
  ElMessageBox,
  ElRow,
  ElCol,
  ElTag,
  ElSelect,
  ElOption
} from 'element-plus'

defineOptions({
  name: 'CommerceEntitlements'
})

/** 中文界面枚举展示（见 .cursor/rules/rules-i18n-enum-labels.mdc） */
const STATUS_LABEL: Record<string, string> = {
  unused: '未使用',
  bound: '已绑定',
  used: '已核销',
  void: '已作废',
  expired: '已过期'
}

const CHANNEL_LABEL: Record<string, string> = {
  manual: '手工',
  offline: '线下',
  xhs: '小红书'
}

const statusLabel = (s: string) => STATUS_LABEL[s] || s || '-'
const channelLabel = (c: string) => CHANNEL_LABEL[c] || c || '-'

const createBusy = ref(false)
const createForm = reactive({
  count: 1,
  expires_days: 30,
  remark: '',
  external_order_id: '',
  channel: 'manual'
})

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const { pageSize, currentPage } = tableState
    const res = await getEntitlementsApi({
      page: unref(currentPage),
      limit: unref(pageSize),
      ...unref(searchParams)
    })
    return {
      list: res.data || [],
      total: res.count || 0
    }
  }
})

const { dataList, loading, total, pageSize, currentPage } = tableState
const { getList } = tableMethods

const searchParams = ref({})
const setSearchParams = (data: any) => {
  searchParams.value = data
  currentPage.value = 1
  getList()
}

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'q',
    label: '关键词',
    component: 'Input',
    componentProps: {
      placeholder: 'token / 订单号 / 渠道 / 备注'
    }
  }
])

const statusType = (s: string) => {
  if (s === 'unused') return 'info'
  if (s === 'bound') return 'warning'
  if (s === 'used') return 'success'
  if (s === 'void' || s === 'expired') return 'danger'
  return 'info'
}

const createBatch = async () => {
  createBusy.value = true
  try {
    const res = await createEntitlementsApi({
      channel: createForm.channel || 'manual',
      external_order_id: createForm.external_order_id || undefined,
      expires_days: createForm.expires_days,
      remark: createForm.remark || undefined,
      count: createForm.count
    })
    if (res.code === 200) {
      const items = res.data?.items || []
      ElMessage.success(`已生成 ${items.length} 条短链`)
      if (items[0]?.short_url) {
        try {
          await navigator.clipboard.writeText(items.map((i: any) => i.short_url).join('\n'))
          ElMessage.info('短链已复制到剪贴板')
        } catch {
          /* ignore */
        }
      }
      await getList()
    }
  } finally {
    createBusy.value = false
  }
}

const copyUrl = async (row: any) => {
  const url = row.short_url || ''
  if (!url) {
    ElMessage.warning('无短链')
    return
  }
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('已复制链接')
  } catch {
    ElMessageBox.alert(url, '短链')
  }
}

const refundRow = async (row: any) => {
  await ElMessageBox.confirm(
    `退费作废短链？未消费订单将失效（资金须在渠道侧退款）。\n${row.short_url || row.token}`,
    '退费确认',
    { type: 'warning', confirmButtonText: '退费', cancelButtonText: '取消' }
  )
  const res = await voidEntitlementApi(row.id)
  if (res.code === 200) {
    ElMessage.success('已退费作废')
    await getList()
  }
}

const columns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: 70, show: true },
  {
    field: 'short_url',
    label: '短链',
    minWidth: 220,
    show: true,
    slots: {
      default: (data: any) => <span class="url">{data.row.short_url}</span>
    }
  },
  {
    field: 'status',
    label: '状态',
    width: 100,
    show: true,
    slots: {
      default: (data: any) => (
        <ElTag type={statusType(data.row.status)} size="small">
          {data.row.status_label || statusLabel(data.row.status)}
        </ElTag>
      )
    }
  },
  {
    field: 'channel',
    label: '渠道',
    width: 90,
    show: true,
    slots: {
      default: (data: any) => (
        <span>{data.row.channel_label || channelLabel(data.row.channel)}</span>
      )
    }
  },
  { field: 'external_order_id', label: '订单号', minWidth: 140, show: true },
  { field: 'expires_at', label: '过期', width: 160, show: true },
  { field: 'create_datetime', label: '创建', width: 160, show: true },
  {
    field: 'action',
    label: '操作',
    width: 160,
    fixed: 'right',
    show: true,
    slots: {
      default: (data: any) => (
        <>
          <BaseButton type="primary" link onClick={() => copyUrl(data.row)}>
            复制链接
          </BaseButton>
          {data.row.status === 'unused' || data.row.status === 'bound' ? (
            <BaseButton type="danger" link onClick={() => refundRow(data.row)}>
              退费
            </BaseButton>
          ) : null}
        </>
      )
    }
  }
])
</script>

<template>
  <ContentWrap title="电商次卡短链">
    <ElRow :gutter="12" class="mb-12px">
      <ElCol :span="4">
        <ElSelect v-model="createForm.channel" placeholder="渠道">
          <ElOption label="手工" value="manual" />
          <ElOption label="线下" value="offline" />
          <ElOption label="小红书" value="xhs" />
        </ElSelect>
      </ElCol>
      <ElCol :span="5">
        <ElInput v-model="createForm.external_order_id" placeholder="外部订单号（可选）" />
      </ElCol>
      <ElCol :span="4">
        <ElInput v-model="createForm.remark" placeholder="备注" />
      </ElCol>
      <ElCol :span="3">
        <ElInputNumber v-model="createForm.count" :min="1" :max="100" controls-position="right" />
      </ElCol>
      <ElCol :span="3">
        <ElInputNumber
          v-model="createForm.expires_days"
          :min="0"
          :max="3650"
          controls-position="right"
          placeholder="有效天数"
        />
      </ElCol>
      <ElCol :span="5">
        <BaseButton type="primary" :loading="createBusy" @click="createBatch">生成短链</BaseButton>
      </ElCol>
    </ElRow>

    <Search :schema="searchSchema" @search="setSearchParams" @reset="setSearchParams" />

    <Table
      v-model:pageSize="pageSize"
      v-model:currentPage="currentPage"
      :columns="columns"
      :data="dataList"
      :loading="loading"
      :pagination="{ total }"
      @register="tableRegister"
    />
  </ContentWrap>
</template>

<style scoped>
.url {
  word-break: break-all;
  font-size: 12px;
}
:deep(.url) {
  word-break: break-all;
  font-size: 12px;
}
</style>
