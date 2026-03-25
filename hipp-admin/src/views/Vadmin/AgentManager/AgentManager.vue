<script setup lang="tsx">
import { reactive, ref, unref } from 'vue'
import {
  getAgentListApi,
  delAgentListApi,
  publishAgentApi,
  unpublishAgentApi,
  testAgentApi
} from '@/api/vadmin/agent_manager'
import { useTable } from '@/hooks/web/useTable'
import { Table, TableColumn } from '@/components/Table'
import { ElTag, ElRow, ElCol, ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { BaseButton } from '@/components/Button'
import Write from './components/Write.vue'

defineOptions({
  name: 'AgentManager'
})

const withCacheBust = (
  url: string | null | undefined,
  version: string | number | null | undefined
) => {
  if (!url) return ''
  const v = version ?? Date.now()
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}v=${encodeURIComponent(String(v))}`
}

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const { pageSize, currentPage } = tableState
    const res = await getAgentListApi({
      page: unref(currentPage),
      limit: unref(pageSize),
      ...unref(searchParams)
    })
    return {
      list: res.data || [],
      total: res.count || 0
    }
  },
  fetchDelApi: async (value) => {
    const res = await delAgentListApi(value)
    return res.code === 200
  }
})

const { dataList, loading, total, pageSize, currentPage } = tableState
const { getList, delList } = tableMethods

const parseTags = (tagsStr: string | null): string[] => {
  if (!tagsStr) return []
  try {
    return JSON.parse(tagsStr)
  } catch {
    return []
  }
}

const tableColumns = reactive<TableColumn[]>([
  {
    field: 'id',
    label: '编号',
    show: true,
    disabled: true,
    width: '80px'
  },
  {
    field: 'icon',
    label: '头像',
    show: true,
    width: '80px',
    slots: {
      default: (data: any) => {
        const row = data.row
        if (row.icon_url) {
          return (
            <img
              src={withCacheBust(row.icon_url, row.update_datetime)}
              style={{ width: '36px', height: '36px', borderRadius: '6px' }}
            />
          )
        } else if (row.icon) {
          return (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '36px',
                height: '36px',
                borderRadius: '6px',
                backgroundColor: row.icon_background || '#E0E0E0',
                fontSize: '20px'
              }}
            >
              {row.icon}
            </span>
          )
        }
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: '6px',
              backgroundColor: '#E0E0E0',
              fontSize: '20px'
            }}
          >
            🤖
          </span>
        )
      }
    }
  },
  {
    field: 'name',
    label: '名称',
    show: true,
    width: '160px'
  },
  {
    field: 'description',
    label: '描述',
    show: true
  },
  {
    field: 'tags',
    label: '标签',
    show: true,
    width: '200px',
    slots: {
      default: (data: any) => {
        const tags = parseTags(data.row.tags)
        return (
          <div>
            {tags.map((tag: string) => (
              <ElTag size="small" style={{ marginRight: '4px', marginBottom: '2px' }}>
                {tag}
              </ElTag>
            ))}
          </div>
        )
      }
    }
  },
  {
    field: 'service_type',
    label: '类型',
    show: true,
    width: '120px'
  },
  {
    field: 'remark',
    label: '备注',
    show: true,
    width: '140px'
  },
  {
    field: 'status',
    label: '上架状态',
    show: true,
    width: '100px',
    slots: {
      default: (data: any) => {
        const row = data.row
        return (
          <ElTag type={row.status === 'published' ? 'success' : 'info'}>
            {row.status === 'published' ? '已上架' : '草稿'}
          </ElTag>
        )
      }
    }
  },
  {
    field: 'action',
    width: '240px',
    label: '操作',
    show: true,
    slots: {
      default: (data: any) => {
        const row = data.row
        return (
          <>
            <BaseButton type="primary" link size="small" onClick={() => editAction(row)}>
              编辑
            </BaseButton>
            {row.status === 'draft' ? (
              <BaseButton type="success" link size="small" onClick={() => handlePublish(row)}>
                上架
              </BaseButton>
            ) : (
              <BaseButton type="warning" link size="small" onClick={() => handleUnpublish(row)}>
                下架
              </BaseButton>
            )}
            <BaseButton type="primary" link size="small" onClick={() => handleTest(row)}>
              测试
            </BaseButton>
            <BaseButton
              type="danger"
              loading={delLoading.value}
              link
              size="small"
              onClick={() => delData(row)}
            >
              删除
            </BaseButton>
          </>
        )
      }
    }
  }
])

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'keyword',
    label: '关键词',
    component: 'Input',
    componentProps: {
      clearable: true,
      placeholder: '搜索名称/描述/标签',
      style: {
        width: '240px'
      }
    }
  },
  {
    field: 'status',
    label: '上架状态',
    component: 'Select',
    componentProps: {
      clearable: true,
      placeholder: '全部',
      style: {
        width: '140px'
      },
      options: [
        { label: '草稿', value: 'draft' },
        { label: '已上架', value: 'published' }
      ]
    }
  },
  {
    field: 'service_type',
    label: '类型',
    component: 'Select',
    componentProps: {
      clearable: true,
      filterable: true,
      allowCreate: true,
      defaultFirstOption: true,
      placeholder: '全部',
      style: {
        width: '160px'
      },
      options: [
        { label: '需求分析', value: '需求分析' },
        { label: '商业评估', value: '商业评估' }
      ]
    }
  }
])

const searchParams = ref({})
const setSearchParams = (data: any) => {
  currentPage.value = 1
  searchParams.value = data
  getList()
}

const delLoading = ref(false)

const delData = async (row: any) => {
  delLoading.value = true
  await delList(true, [row.id]).finally(() => {
    delLoading.value = false
  })
}

const handlePublish = async (row: any) => {
  try {
    const res = await publishAgentApi(row.id)
    if (res.code === 200) {
      ElMessage.success('上架成功')
      getList()
    } else {
      ElMessage.error(res.message || '上架失败')
    }
  } catch {
    ElMessage.error('上架失败')
  }
}

const handleUnpublish = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要下架该智能客服吗？', '提示', { type: 'warning' })
    const res = await unpublishAgentApi(row.id)
    if (res.code === 200) {
      ElMessage.success('下架成功')
      getList()
    }
  } catch {
    // cancelled
  }
}

const handleTest = async (row: any) => {
  try {
    const res = await testAgentApi({
      id: row.id,
      api_server: row.api_server,
      app_key: row.app_key,
      remark: row.remark ?? null,
      service_type: row.service_type ?? null
    })
    if (res.code === 200) {
      ElMessage.success('测试成功，信息已同步')
      getList()
    } else {
      ElMessage.error(res.message || '测试失败')
    }
  } catch {
    ElMessage.error('测试失败')
  }
}

const dialogVisible = ref(false)
const dialogTitle = ref('新增智能客服')
const currentRow = ref<any>(null)

const addAction = () => {
  dialogTitle.value = '新增智能客服'
  currentRow.value = null
  dialogVisible.value = true
}

const editAction = (row: any) => {
  dialogTitle.value = '编辑智能客服'
  currentRow.value = row
  dialogVisible.value = true
}

const onSaveSuccess = () => {
  dialogVisible.value = false
  getList()
}
</script>

<template>
  <ContentWrap>
    <Search :schema="searchSchema" @reset="setSearchParams" @search="setSearchParams" />
    <Table
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      showAction
      :columns="tableColumns"
      default-expand-all
      node-key="id"
      :data="dataList"
      :loading="loading"
      :pagination="{ total }"
      @register="tableRegister"
      @refresh="getList"
    >
      <template #toolbar>
        <ElRow :gutter="10">
          <ElCol :span="1.5">
            <BaseButton type="primary" @click="addAction">新增智能客服</BaseButton>
          </ElCol>
        </ElRow>
      </template>
    </Table>
  </ContentWrap>

  <Write
    v-model="dialogVisible"
    :title="dialogTitle"
    :current-row="currentRow"
    @save-success="onSaveSuccess"
  />
</template>
