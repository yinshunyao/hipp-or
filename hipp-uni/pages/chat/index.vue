<template>
  <view :class="themeClass" class="inbox">
    <van-search
      :value="keyword"
      input-align="center"
      :placeholder="searchPlaceholder"
      @change="onSearchChange"
      @search="loadInbox"
    />
    <scroll-view scroll-y class="list-wrap">
      <view v-if="loading" class="hint">
        <view class="hint-dot"></view>
        <text class="hint-text">加载中...</text>
      </view>
      <view v-else-if="!items.length" class="hint">
        <text class="hint-text">{{ emptyHint }}</text>
      </view>
      <view
        v-for="(row, idx) in items"
        :key="idx"
        class="row"
        @click="onRowTap(row)"
        @longpress="onRowLongPress(row)"
      >
        <view
          class="avatar"
          :style="'background:' + ((row.agent && row.agent.icon_background) ? row.agent.icon_background : '')"
        >
          <text v-if="avatarText(row)" class="avatar-text">{{ avatarText(row) }}</text>
          <image v-else-if="avatarUrl(row)" class="avatar-img" :src="avatarUrl(row)" mode="aspectFill" />
        </view>
        <view class="meta">
          <view class="title-line">
            <view class="name-wrap">
              <view class="name">{{ displayName(row) }}</view>
            </view>
            <view class="title-tags">
              <text v-if="row.session && row.session.session_kind === 'human_support'" class="human-tag">人工</text>
              <text v-if="row.session && statusLabel(row)" class="state">{{ statusLabel(row) }}</text>
              <text v-if="row.session && row.session.is_pinned" class="pin">置顶</text>
              <text v-if="row.session && row.session.session_kind !== 'human_support' && row.session.is_topic_closed" class="topic-end">已结束</text>
            </view>
          </view>
          <text class="preview">{{ previewText(row) }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { getChatInbox, getStaffChatInbox, patchChatSession, deleteChatSession } from '@/common/request/api/mp/chat.js'
import { themeMixin } from '@/common/mixins/theme.js'

export default {
  mixins: [themeMixin],
  data() {
    return { keyword: '', items: [], loading: false }
  },
  computed: {
    isHumanStaff() {
      return this.$auth && this.$auth.hasRole('人工客服')
    },
    searchPlaceholder() {
      return this.isHumanStaff ? '搜索用户或消息' : '请输入搜索关键词'
    },
    emptyHint() {
      return this.isHumanStaff ? '暂无分配给你的会话，下拉刷新' : '暂无归档话题，下拉刷新'
    }
  },
  onShow() {
    try {
      uni.setNavigationBarTitle({ title: this.isHumanStaff ? '客服接待' : '对话' })
    } catch (e) {}
    this.loadInbox()
  },
  onPullDownRefresh() {
    this.loadInbox().finally(() => uni.stopPullDownRefresh())
  },
  methods: {
    onSearchChange(e) {
      const d = e && e.detail
      this.keyword = d != null && typeof d === 'object' && 'value' in d ? String(d.value) : String(d != null ? d : '')
    },
    async loadInbox() {
      this.loading = true
      try {
        const q = this.keyword.trim()
        const res = this.isHumanStaff ? await getStaffChatInbox(q) : await getChatInbox(q)
        this.items = (res.data && res.data.items) || []
      } catch (e) { this.items = [] } finally { this.loading = false }
    },
    displayName(row) {
      const ag = row.agent || {}
      if (row.session) {
        return row.session.display_title || row.session.title || ag.name || '对话'
      }
      return '对话'
    },
    previewText(row) {
      if (row.session && row.session.last_message_preview) return row.session.last_message_preview
      if (row.session && row.session.agent_status && row.session.agent_status !== 'active') return '仅可查看历史消息'
      return ' '
    },
    statusLabel(row) {
      const s = row && row.session && row.session.agent_status
      if (s === 'offline') return '已下架'
      if (s === 'deleted') return '已删除'
      return ''
    },
    avatarText(row) {
      const ag = row.agent || {}
      if (ag.icon_type === 'emoji' && ag.icon) return ag.icon
      return (ag.name || '智').trim().slice(0, 1)
    },
    avatarUrl(row) {
      const ag = row.agent || {}
      return (ag.icon_type === 'image' && ag.icon_url) ? ag.icon_url : ''
    },
    async onRowTap(row) {
      const sid = row && row.session && row.session.id
      if (!sid) {
        uni.showToast({ title: '会话参数缺失', icon: 'none' })
        return
      }
      uni.navigateTo({
        url: `/subpkg/chat/chat?sessionId=${sid}`,
        fail: () => {
          uni.showToast({ title: '打开会话失败', icon: 'none' })
        }
      })
      try { uni.setStorageSync('last_active_session_id', String(sid)) } catch (e) {}
    },
    onRowLongPress(row) {
      if (this.isHumanStaff) return
      this.onRowLong(row)
    },
    onRowLong(row) {
      if (!row.session) return
      const sid = row.session.id
      const closed = !!row.session.is_topic_closed
      const pinLabel = row.session.is_pinned ? '取消置顶' : '置顶'
      const itemList = closed ? ['继续对话', pinLabel, '修改标题', '删除会话'] : [pinLabel, '修改标题', '删除会话']
      uni.showActionSheet({
        itemList,
        success: async (res) => {
          let tap = res.tapIndex
          if (closed) {
            if (tap === 0) {
              try { await patchChatSession(sid, { resume_topic: true }); await this.loadInbox(); uni.navigateTo({ url: `/subpkg/chat/chat?sessionId=${sid}` }); try { uni.setStorageSync('last_active_session_id', String(sid)) } catch (e) {} } catch (e) {}
              return
            }
            tap -= 1
          }
          if (tap === 0) { try { await patchChatSession(sid, { is_pinned: !row.session.is_pinned }); this.loadInbox() } catch (e) {} }
          else if (tap === 1) { uni.showModal({ title: '修改标题', editable: true, placeholderText: row.session.display_title || row.session.title || '', success: async (r) => { if (r.confirm && r.content) { try { await patchChatSession(sid, { title: r.content }); this.loadInbox() } catch (e) {} } } }) }
          else if (tap === 2) { uni.showModal({ title: '确认删除', content: '删除后不可恢复', success: async (r) => { if (r.confirm) { try { await deleteChatSession(sid); this.loadInbox() } catch (e) {} } } }) }
        }
      })
    }
  }
}
</script>

<style lang="scss">
page {
  height: 100%;
  box-sizing: border-box;
}
</style>

<style lang="scss" scoped>
.inbox { display: flex; flex-direction: column; min-height: 100%; background: var(--t-root); }
.list-wrap { flex: 1; min-height: 0; }
.hint { display: flex; flex-direction: column; align-items: center; padding: 100rpx 40rpx; }
.hint-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: var(--t-accent); margin-bottom: 20rpx; opacity: 0.6; }
.hint-text { color: var(--t-text-3); font-size: 28rpx; }
.row {
  display: flex; align-items: center; padding: 28rpx 30rpx;
  background: var(--t-surface); border-bottom: 1rpx solid var(--t-divider);
  transition: background-color 0.15s ease;
  &:active { background-color: var(--t-elevated); }
}
.avatar {
  width: 104rpx; height: 104rpx; border-radius: 28rpx; margin-right: 24rpx;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; flex-shrink: 0;
  background: linear-gradient(145deg, var(--t-ring-from), var(--t-ring-to));
  box-shadow: var(--t-shadow);
}
.avatar-text { font-size: 40rpx; color: var(--t-text-1); }
.avatar-img { width: 104rpx; height: 104rpx; }
.meta { flex: 1; min-width: 0; }
.title-line { display: flex; align-items: flex-start; }
.name-wrap { flex: 1; min-width: 0; padding-right: 8rpx; }
.name {
  font-size: 32rpx; color: var(--t-text-1); font-weight: 600;
  overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; word-break: break-word;
}
.title-tags { flex-shrink: 0; display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 8rpx; padding-top: 2rpx; }
.pin { font-size: 20rpx; color: var(--t-pin-color); background: var(--t-pin-bg); border-radius: 8rpx; padding: 4rpx 12rpx; font-weight: 500; }
.state { font-size: 20rpx; color: var(--t-state-color); background: var(--t-state-bg); border-radius: 8rpx; padding: 4rpx 12rpx; font-weight: 500; }
.topic-end { font-size: 20rpx; color: var(--t-end-color); background: var(--t-end-bg); border-radius: 8rpx; padding: 4rpx 12rpx; font-weight: 500; }
.human-tag { font-size: 20rpx; color: var(--t-accent); background: var(--t-accent-bg); border-radius: 8rpx; padding: 4rpx 12rpx; font-weight: 500; }
.preview { font-size: 26rpx; color: var(--t-text-3); margin-top: 8rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
