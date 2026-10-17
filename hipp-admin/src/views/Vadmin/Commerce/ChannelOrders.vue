<script setup lang="tsx">
import { reactive, ref, unref } from 'vue'
import {
  createOfflineOrderApi,
  getChannelOrdersApi,
  refundChannelOrderApi
} from '@/api/vadmin/commerce'
import { useTable } from '@/hooks/web/useTable'
import { Table, TableColumn } from '@/components/Table'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { BaseButton } from '@/components/Button'
import { ElMessage, ElMessageBox, ElTag } from 'element-plus'

defineOptions({
  name: 'CommerceChannelOrders'
})

/** 中文界面枚举展示（见 .cursor/rules/rules-i18n-enum-labels.mdc） */
const CHANNEL_LABEL: Record<string, string> = {
  manual: '手工',
  offline: '线下',
  xhs: '小红书'
}

const channelLabel = (c: string) => CHANNEL_LABEL[c] || c || '-'

const offlineBusy = ref(false)

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const { pageSize, currentPage } = tableState
    const res = await getChannelOrdersApi({
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

const searchParams = ref<Record<string, any>>({})
const setSearchParams = (data: any) => {
  searchParams.value = data || {}
  currentPage.value = 1
  getList()
}

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'q',
    label: '关键词',
    component: 'Input',
    componentProps: {
      placeholder: '订单号 / 渠道 / 短链'
    }
  },
  {
    field: 'status',
    label: '状态',
    component: 'Select',
    componentProps: {
      clearable: true,
      options: [
        { label: '已支付', value: 'paid' },
        { label: '已核销', value: 'redeemed' },
        { label: '已退费', value: 'refunded' }
      ]
    }
  }
])

const statusType = (s: string) => {
  if (s === 'paid') return 'warning'
  if (s === 'redeemed') return 'success'
  if (s === 'refunded') return 'info'
  return 'info'
}

const copyUrl = async (row: any) => {
  const url = row.short_url || ''
  if (!url) {
    ElMessage.warning('无短链')
    return
  }
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('已复制短链')
  } catch {
    ElMessageBox.alert(url, '短链')
  }
}

const offlineCreate = async () => {
  try {
    const { value } = await ElMessageBox.prompt(
      '将生成 1 条「已支付」订单与可用短链，交给线下买家即可（等同线下收款后交付）。可选填备注。',
      '线下出链 · 1 次需求分析',
      {
        inputPlaceholder: '备注（如客户名、收款方式，可选）',
        confirmButtonText: '生成短链',
        cancelButtonText: '取消',
        inputValidator: () => true
      }
    )
    offlineBusy.value = true
    try {
      const res = await createOfflineOrderApi({
        remark: value || undefined,
        expires_days: 30
      })
      if (res.code === 200 && res.data) {
        const url = res.data.short_url || ''
        if (url) {
          try {
            await navigator.clipboard.writeText(url)
            ElMessage.success('已生成并复制短链')
          } catch {
            ElMessageBox.alert(url, '短链已生成')
          }
        } else {
          ElMessage.success('已生成')
        }
        await getList()
      }
    } finally {
      offlineBusy.value = false
    }
  } catch {
    /* 取消 */
  }
}

const refundRow = async (row: any) => {
  await ElMessageBox.confirm(
    `确认退费？短链将失效。真实退款请在千帆等渠道完成。\n订单 ${row.external_order_id || row.id}`,
    '退费确认',
    { type: 'warning', confirmButtonText: '退费', cancelButtonText: '取消' }
  )
  const res = await refundChannelOrderApi(row.id, { remark: '管理端退费' })
  if (res.code === 200) {
    ElMessage.success('已标记退费，短链已失效')
    await getList()
  }
}

const columns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: 70, show: true },
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
  { field: 'external_order_id', label: '渠道订单号', minWidth: 160, show: true },
  {
    field: 'status_label',
    label: '状态',
    width: 100,
    show: true,
    slots: {
      default: (data: any) => (
        <ElTag type={statusType(data.row.status)} size="small">
          {data.row.status_label || data.row.status}
        </ElTag>
      )
    }
  },
  {
    field: 'short_url',
    label: '短链',
    minWidth: 200,
    show: true,
    slots: {
      default: (data: any) => <span class="url">{data.row.short_url}</span>
    }
  },
  { field: 'paid_at', label: '已支付', width: 160, show: true },
  { field: 'redeemed_at', label: '已核销', width: 160, show: true },
  { field: 'refunded_at', label: '已退费', width: 160, show: true },
  { field: 'refund_operator', label: '退费人', width: 100, show: true },
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
            复制短链
          </BaseButton>
          {data.row.status === 'paid' || data.row.status === 'redeemed' ? (
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
  <ContentWrap title="电商渠道订单">
    <div class="toolbar">
      <BaseButton type="primary" :loading="offlineBusy" @click="offlineCreate">
        线下出链（1 次需求分析）
      </BaseButton>
      <p class="hint">
        线下收款后点此生成短链发给买家。状态：已支付 →
        已核销（做完咨询）或退费作废。小红书等线上单由回调自动入账。
      </p>
    </div>
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
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.hint {
  margin: 0;
  flex: 1;
  min-width: 220px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.5;
}
:deep(.url) {
  word-break: break-all;
  font-size: 12px;
}
</style>
