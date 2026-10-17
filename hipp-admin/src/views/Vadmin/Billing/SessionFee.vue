<script setup lang="tsx">
import { reactive, ref, unref } from 'vue'
import {
  deleteUserSessionFeeApi,
  getSessionFeeGlobalApi,
  getSessionFeeUsersApi,
  putSessionFeeGlobalApi,
  putUserSessionFeeApi
} from '@/api/vadmin/billing'
import { useTable } from '@/hooks/web/useTable'
import { Table, TableColumn } from '@/components/Table'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { BaseButton } from '@/components/Button'
import { ElInputNumber, ElMessage, ElMessageBox, ElRow, ElCol, ElTag } from 'element-plus'

defineOptions({
  name: 'BillingSessionFee'
})

const globalAmount = ref(0.1)
const globalBusy = ref(false)

const loadGlobal = async () => {
  const res = await getSessionFeeGlobalApi()
  if (res.code === 200 && res.data) {
    globalAmount.value = Number(res.data.amount ?? 0.1)
  }
}

const saveGlobal = async () => {
  const n = Number(globalAmount.value)
  if (!Number.isFinite(n) || n < 0) {
    ElMessage.error('请输入有效金额（≥ 0）')
    return
  }
  globalBusy.value = true
  try {
    const res = await putSessionFeeGlobalApi(Number(n.toFixed(2)))
    if (res.code === 200) {
      ElMessage.success('全局费用已保存')
      await loadGlobal()
      await getList()
    }
  } finally {
    globalBusy.value = false
  }
}

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const { pageSize, currentPage } = tableState
    const res = await getSessionFeeUsersApi({
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
      placeholder: '手机号 / 姓名 / 昵称'
    }
  }
])

const setOverride = async (row: any) => {
  const { value } = await ElMessageBox.prompt(
    `为 ${row.name || row.telephone} 设定专属费用（元）`,
    '用户专属费用',
    {
      inputValue: String(row.override_amount ?? row.effective_amount ?? globalAmount.value),
      inputPattern: /^\d+(\.\d{1,2})?$/,
      inputErrorMessage: '请输入有效金额，最多两位小数',
      confirmButtonText: '保存',
      cancelButtonText: '取消'
    }
  )
  const amount = Number(value)
  const res = await putUserSessionFeeApi(row.user_id, amount)
  if (res.code === 200) {
    ElMessage.success('已设定专属费用')
    await getList()
  }
}

const clearOverride = async (row: any) => {
  await ElMessageBox.confirm(
    `清除 ${row.name || row.telephone} 的专属费用，恢复跟随全局？`,
    '确认',
    {
      type: 'warning'
    }
  )
  const res = await deleteUserSessionFeeApi(row.user_id)
  if (res.code === 200) {
    ElMessage.success('已清除专属费用')
    await getList()
  }
}

const tableColumns = reactive<TableColumn[]>([
  { field: 'user_id', label: '用户ID', width: '90px', show: true },
  { field: 'name', label: '姓名', show: true },
  { field: 'nickname', label: '昵称', show: true },
  { field: 'telephone', label: '手机号', width: '130px', show: true },
  {
    field: 'is_override',
    label: '类型',
    width: '100px',
    show: true,
    slots: {
      default: (data: any) => {
        return data.row.is_override ? (
          <ElTag type="warning">专属</ElTag>
        ) : (
          <ElTag type="info">全局</ElTag>
        )
      }
    }
  },
  {
    field: 'override_amount',
    label: '专属金额',
    width: '110px',
    show: true,
    slots: {
      default: (data: any) => {
        const v = data.row.override_amount
        return <span>{v == null ? '—' : `¥${Number(v).toFixed(2)}`}</span>
      }
    }
  },
  {
    field: 'effective_amount',
    label: '生效金额',
    width: '110px',
    show: true,
    slots: {
      default: (data: any) => <span>¥{Number(data.row.effective_amount || 0).toFixed(2)}</span>
    }
  },
  {
    field: 'action',
    label: '操作',
    width: '200px',
    show: true,
    slots: {
      default: (data: any) => (
        <>
          <BaseButton type="primary" link onClick={() => setOverride(data.row)}>
            设定
          </BaseButton>
          {data.row.is_override ? (
            <BaseButton type="danger" link onClick={() => clearOverride(data.row)}>
              清除
            </BaseButton>
          ) : null}
        </>
      )
    }
  }
])

loadGlobal()
</script>

<template>
  <ContentWrap title="会话咨询费用">
    <div class="global-box">
      <div class="global-label">全局每次会话费用（元）</div>
      <ElRow :gutter="12" align="middle">
        <ElCol :span="8">
          <ElInputNumber
            v-model="globalAmount"
            :min="0"
            :max="999999.99"
            :precision="2"
            :step="0.1"
            style="width: 100%"
          />
        </ElCol>
        <ElCol :span="4">
          <BaseButton type="primary" :loading="globalBusy" @click="saveGlobal">保存全局</BaseButton>
        </ElCol>
      </ElRow>
      <p class="hint">未设定专属费用的用户按全局金额计费。默认 0.10 元。</p>
    </div>

    <Search :schema="searchSchema" @search="setSearchParams" @reset="setSearchParams" />

    <Table
      v-model:pageSize="pageSize"
      v-model:currentPage="currentPage"
      :columns="tableColumns"
      :data="dataList"
      :loading="loading"
      :pagination="{ total }"
      @register="tableRegister"
    />
  </ContentWrap>
</template>

<style scoped>
.global-box {
  max-width: 520px;
  margin-bottom: 24px;
  padding: 16px 18px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}
.global-label {
  font-weight: 600;
  margin-bottom: 10px;
}
.hint {
  margin: 10px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>
