<script setup lang="ts">
import { ElTabs, ElTabPane } from 'element-plus'
import { ref } from 'vue'
import Basic from './components/Basic.vue'
import Privacy from './components/Privacy.vue'
import Agreement from './components/Agreement.vue'
import WXClient from './components/WechatServer.vue'
import Email from './components/Email.vue'
import SMS from './components/SMS.vue'
import DataImportExport from './components/DataImportExport.vue'
import { ContentWrap } from '@/components/ContentWrap'
import { getSystemSettingsTabsApi } from '@/api/vadmin/system/settings'

defineOptions({
  name: 'SystemSettings'
})

const activeName = ref('web_basic')

const tabs = ref([] as Recordable[])

/** 系统配置页固定 Tab：数据导入导出（不依赖后台 settings_tab 配置） */
const staticTabs: Recordable[] = [
  { id: 0, tab_name: 'data_import_export', tab_label: '数据导入导出', hidden: false }
]

const getList = async () => {
  const res = await getSystemSettingsTabsApi(['web', 'aliyun'])
  if (res) {
    tabs.value = [...res.data, ...staticTabs]
  }
}

getList()
</script>

<template>
  <ContentWrap>
    <ElTabs v-model="activeName">
      <template v-for="item in tabs" :key="item.id">
        <ElTabPane v-if="!item.hidden" :name="item.tab_name" :label="item.tab_label">
          <Basic v-if="item.tab_name === 'web_basic'" :tab-id="item.id" />
          <Privacy v-else-if="item.tab_name === 'web_privacy'" :tab-id="item.id" />
          <Agreement v-else-if="item.tab_name === 'web_agreement'" :tab-id="item.id" />
          <WXClient v-else-if="item.tab_name === 'wx_server'" :tab-id="item.id" />
          <Email v-else-if="item.tab_name === 'web_email'" :tab-id="item.id" />
          <SMS v-else-if="item.tab_name === 'aliyun_sms'" :tab-id="item.id" />
          <DataImportExport v-else-if="item.tab_name === 'data_import_export'" />
        </ElTabPane>
      </template>
    </ElTabs>
  </ContentWrap>
</template>

<style scoped lang="less"></style>
