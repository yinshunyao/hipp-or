<template>
  <view :class="themeClass" class="page-with-nav">
    <uni-nav-bar
      :title="barTitle"
      fixed
      status-bar
      :border="false"
      :background-color="'var(--t-nav-bg)'"
      :color="'var(--t-nav-text)'"
    />
    <view class="inbox page-with-nav__body">
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
          :style="{ background: avatarBackground(row) }"
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
    <view
      v-if="actionSheetVisible"
      class="topic-action-mask"
      @click="closeActionSheet"
      @touchmove.stop.prevent
    >
      <view class="topic-action-sheet" @click.stop>
        <view
          v-for="(item, index) in actionSheetItems"
          :key="item.key"
          class="topic-action-item"
          :class="{ 'topic-action-item--danger': item.danger }"
          @click="onActionItemTap(index)"
        >
          {{ item.label }}
        </view>
        <view class="topic-action-cancel" @click="closeActionSheet">取消</view>
      </view>
    </view>
    </view>
  </view>
</template>

<script>
import { getChatInbox, getStaffChatInbox, patchChatSession, deleteChatSession } from '@/common/request/api/mp/chat.js'
import { themeMixin } from '@/common/mixins/theme.js'

export default {
  mixins: [themeMixin],
  data() {
    return {
      keyword: '',
      items: [],
      loading: false,
      actionSheetVisible: false,
      actionSheetItems: [],
      actionSheetRow: null
    }
  },
  computed: {
    barTitle() {
      return this.isHumanStaff ? '客服接待' : '对话'
    },
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
    avatarBackground(row) {
      const ag = row.agent || {}
      const raw = String(ag.icon_background || '').trim()
      if (!raw) return 'linear-gradient(145deg, var(--t-ring-from), var(--t-ring-to))'
      const rgb = this.parseColorToRgb(raw)
      if (!rgb) return raw
      return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.22)`
    },
    parseColorToRgb(color) {
      if (!color) return null
      const hex = color.match(/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/)
      if (hex) {
        const v = hex[1]
        const full = v.length === 3 ? v.split('').map((c) => `${c}${c}`).join('') : v
        return {
          r: parseInt(full.slice(0, 2), 16),
          g: parseInt(full.slice(2, 4), 16),
          b: parseInt(full.slice(4, 6), 16)
        }
      }
      const rgb = color.match(/^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*[\d.]+\s*)?\)$/i)
      if (rgb) {
        return {
          r: Math.max(0, Math.min(255, Math.round(Number(rgb[1])))),
          g: Math.max(0, Math.min(255, Math.round(Number(rgb[2])))),
          b: Math.max(0, Math.min(255, Math.round(Number(rgb[3]))))
        }
      }
      return null
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
      const closed = !!row.session.is_topic_closed
      const pinLabel = row.session.is_pinned ? '取消置顶' : '置顶'
      const actions = closed
        ? [
            { key: 'resume', label: '继续对话' },
            { key: 'pin', label: pinLabel },
            { key: 'rename', label: '修改标题' },
            { key: 'delete', label: '删除会话', danger: true }
          ]
        : [
            { key: 'pin', label: pinLabel },
            { key: 'rename', label: '修改标题' },
            { key: 'delete', label: '删除会话', danger: true }
          ]
      this.actionSheetRow = row
      this.actionSheetItems = actions
      this.actionSheetVisible = true
    },
    closeActionSheet() {
      this.actionSheetVisible = false
      this.actionSheetItems = []
      this.actionSheetRow = null
    },
    async onActionItemTap(index) {
      const row = this.actionSheetRow
      const action = this.actionSheetItems[index]
      this.closeActionSheet()
      if (!row || !row.session || !action) return
      const sid = row.session.id
      if (!sid) return
      if (action.key === 'resume') {
        try {
          await patchChatSession(sid, { resume_topic: true })
          await this.loadInbox()
          uni.navigateTo({ url: `/subpkg/chat/chat?sessionId=${sid}` })
          try { uni.setStorageSync('last_active_session_id', String(sid)) } catch (e) {}
        } catch (e) {}
        return
      }
      if (action.key === 'pin') {
        try { await patchChatSession(sid, { is_pinned: !row.session.is_pinned }); this.loadInbox() } catch (e) {}
        return
      }
      if (action.key === 'rename') {
        uni.showModal({
          title: '修改标题',
          editable: true,
          placeholderText: row.session.display_title || row.session.title || '',
          success: async (r) => {
            if (r.confirm && r.content) {
              try { await patchChatSession(sid, { title: r.content }); this.loadInbox() } catch (e) {}
            }
          }
        })
        return
      }
      if (action.key === 'delete') {
        uni.showModal({
          title: '确认删除',
          content: '删除后不可恢复',
          success: async (r) => {
            if (r.confirm) {
              try { await deleteChatSession(sid); this.loadInbox() } catch (e) {}
            }
          }
        })
      }
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
@import '@/uni.scss';

.inbox { display: flex; flex-direction: column; min-height: 0; flex: 1; background: var(--t-root); }
.list-wrap { flex: 1; min-height: 0; padding-bottom: calc(var(--custom-tabbar-height) + env(safe-area-inset-bottom)); box-sizing: border-box; }
.hint {
  display: flex; flex-direction: column; align-items: center;
  padding: $mp-topic-empty-y $mp-gap-9;
}
.hint-dot {
  width: $mp-topic-dot; height: $mp-topic-dot; border-radius: 50%;
  background: var(--t-accent); margin-bottom: $mp-gap-5; opacity: 0.6;
}
.hint-text { color: var(--t-text-3); font-size: $mp-font-body; }
.row {
  display: flex; align-items: center; padding: $mp-gap-7 $mp-topic-row-x;
  background: var(--t-surface); border-bottom: 1rpx solid var(--t-divider);
  transition: background-color 0.15s ease;
  &:active { background-color: var(--t-elevated); }
}
.avatar {
  width: $mp-topic-avatar; height: $mp-topic-avatar; border-radius: $mp-radius-avatar;
  margin-right: $mp-gap-6;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; flex-shrink: 0;
  background: linear-gradient(145deg, var(--t-ring-from), var(--t-ring-to));
  border: 1rpx solid var(--t-ring-border);
  box-shadow: var(--t-shadow);
}
.avatar-text { font-size: $mp-topic-avatar-font; color: var(--t-text-1); }
.avatar-img { width: $mp-topic-avatar; height: $mp-topic-avatar; }
.meta { flex: 1; min-width: 0; }
.title-line { display: flex; align-items: flex-start; }
.name-wrap { flex: 1; min-width: 0; padding-right: $mp-gap-2; }
.name {
  font-size: $mp-font-title; color: var(--t-text-1); font-weight: 600;
  overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; word-break: break-word;
}
.title-tags {
  flex-shrink: 0; display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end;
  gap: $mp-gap-2; padding-top: $mp-gap-micro;
}
.pin {
  font-size: $mp-font-caption; color: var(--t-pin-color); background: var(--t-pin-bg);
  border-radius: $mp-radius-sm; padding: $mp-gap-1 $mp-gap-3; font-weight: 500;
}
.state {
  font-size: $mp-font-caption; color: var(--t-state-color); background: var(--t-state-bg);
  border-radius: $mp-radius-sm; padding: $mp-gap-1 $mp-gap-3; font-weight: 500;
}
.topic-end {
  font-size: $mp-font-caption; color: var(--t-end-color); background: var(--t-end-bg);
  border-radius: $mp-radius-sm; padding: $mp-gap-1 $mp-gap-3; font-weight: 500;
}
.human-tag {
  font-size: $mp-font-caption; color: var(--t-accent); background: var(--t-accent-bg);
  border-radius: $mp-radius-sm; padding: $mp-gap-1 $mp-gap-3; font-weight: 500;
}
.preview {
  font-size: $mp-font-sub; color: var(--t-text-3); margin-top: $mp-gap-2;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

::v-deep .van-search {
  background: var(--t-surface) !important;
  padding: $mp-gap-4 $mp-gap-5 !important;
}

::v-deep .van-search__content {
  background: var(--t-elevated) !important;
  border: 1rpx solid var(--t-border) !important;
  border-radius: $mp-radius-pill !important;
}

::v-deep .van-field__control {
  color: var(--t-text-1) !important;
}

::v-deep .van-field__control::placeholder {
  color: var(--t-text-3) !important;
}

.topic-action-mask {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.42);
  display: flex;
  align-items: flex-end;
}

.topic-action-sheet {
  width: 100%;
  padding: 0 24rpx calc(24rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.topic-action-item,
.topic-action-cancel {
  background: var(--t-surface);
  color: var(--t-text-1);
  font-size: $mp-font-title;
  line-height: 100rpx;
  text-align: center;
  border-bottom: 1rpx solid var(--t-divider);
}

.topic-action-item:first-child {
  border-top-left-radius: 24rpx;
  border-top-right-radius: 24rpx;
}

.topic-action-item:last-child {
  border-bottom: none;
  border-bottom-left-radius: 24rpx;
  border-bottom-right-radius: 24rpx;
}

.topic-action-item--danger {
  color: var(--t-error);
}

.topic-action-cancel {
  margin-top: 16rpx;
  border-radius: 24rpx;
  border-bottom: none;
}
</style>
