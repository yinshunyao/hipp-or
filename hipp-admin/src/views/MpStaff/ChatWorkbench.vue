<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMpStaffInboxApi, getMpChatMessagesApi, postMpChatMessageApi } from '@/api/mp/chat'

defineOptions({ name: 'MpStaffChatWorkbench' })

const loading = ref(false)
const sessions = ref<{ id: number; title: string; preview: string }[]>([])
const activeId = ref<number | null>(null)
const messages = ref<{ id: number; role: string; content: string }[]>([])
const replyText = ref('')
const msgLoading = ref(false)

const loadSessions = async () => {
  loading.value = true
  try {
    const res: any = await getMpStaffInboxApi()
    const items = res?.data?.items ?? []
    sessions.value = (items || [])
      .map((row: any) => ({
        id: row.session?.id,
        title: row.session?.display_title || row.session?.title || row.agent?.name || '会话',
        preview: row.session?.last_message_preview || ''
      }))
      .filter((x: { id: number }) => x.id)
  } catch (e) {
    sessions.value = []
    ElMessage.error('加载会话失败')
  } finally {
    loading.value = false
  }
}

const openSession = async (id: number) => {
  activeId.value = id
  msgLoading.value = true
  try {
    const res: any = await getMpChatMessagesApi(id, 1, 200)
    const data = res?.data
    messages.value = Array.isArray(data) ? data : []
  } catch (e) {
    messages.value = []
    ElMessage.error('加载消息失败')
  } finally {
    msgLoading.value = false
  }
}

const sendReply = async () => {
  const id = activeId.value
  const t = replyText.value.trim()
  if (!id || !t) return
  try {
    await postMpChatMessageApi(id, t)
    replyText.value = ''
    await openSession(id)
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

onMounted(() => {
  loadSessions()
})
</script>

<template>
  <div class="p-4">
    <h2 class="mb-4 text-lg font-semibold">人工客服工作台</h2>
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never" v-loading="loading">
          <template #header>分配给我的会话</template>
          <el-scrollbar max-height="480px">
            <el-empty v-if="!sessions.length" description="暂无会话" />
            <div
              v-for="s in sessions"
              :key="s.id"
              class="p-3 mb-2 rounded cursor-pointer border border-gray-200 hover:bg-gray-50"
              :class="{ 'bg-blue-50': activeId === s.id }"
              @click="openSession(s.id)"
            >
              <div class="font-medium">{{ s.title }}</div>
              <div class="text-xs text-gray-500 truncate">{{ s.preview }}</div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card shadow="never" v-loading="msgLoading">
          <template #header>消息与回复</template>
          <el-empty v-if="!activeId" description="请选择左侧会话" />
          <div v-else>
            <el-scrollbar max-height="360px" class="mb-4">
              <div
                v-for="m in messages"
                :key="m.id"
                class="mb-2 text-sm"
                :class="
                  m.role === 'user'
                    ? 'text-gray-800'
                    : m.role === 'system'
                      ? 'text-amber-700'
                      : 'text-blue-800'
                "
              >
                <span class="font-medium">{{ m.role }}：</span>
                <span class="whitespace-pre-wrap">{{ m.content }}</span>
              </div>
            </el-scrollbar>
            <el-input
              v-model="replyText"
              type="textarea"
              :rows="3"
              placeholder="输入回复后发送"
              @keydown.enter.exact.prevent="sendReply"
            />
            <el-button type="primary" class="mt-2" @click="sendReply">发送</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
