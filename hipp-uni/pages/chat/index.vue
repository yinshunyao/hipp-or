<template>
  <view class="inbox">
    <view class="search-row">
      <view class="search-inner">
        <input
          v-model="keyword"
          class="search-input"
          type="text"
          :placeholder="searchFocused ? '' : '搜索会话或智能体'"
          confirm-type="search"
          @focus="searchFocused = true"
          @blur="searchFocused = false"
          @confirm="loadInbox"
        />
      </view>
    </view>
    <scroll-view scroll-y class="list-wrap">
      <view v-if="loading" class="hint">加载中...</view>
      <view v-else-if="!items.length" class="hint">暂无数据，下拉刷新</view>
      <view
        v-for="(row, idx) in items"
        :key="idx"
        class="row"
        @click="onRowTap(row)"
        @longpress="onRowLong(row)"
      >
        <view
          class="avatar"
          :style="'background-color:' + ((row.agent && row.agent.icon_background) ? row.agent.icon_background : '#f0f0f0')"
        >
          <text v-if="avatarText(row)" class="avatar-text">{{ avatarText(row) }}</text>
          <image v-else-if="avatarUrl(row)" class="avatar-img" :src="avatarUrl(row)" mode="aspectFill" />
        </view>
        <view class="meta">
          <view class="title-line">
            <text class="name">{{ displayName(row) }}</text>
            <text v-if="row.kind === 'session' && statusLabel(row)" class="state">{{ statusLabel(row) }}</text>
            <text v-if="row.kind === 'session' && row.session && row.session.is_pinned" class="pin">置顶</text>
          </view>
          <text class="preview">{{ previewText(row) }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { getChatInbox, createChatSession, patchChatSession, deleteChatSession } from '@/common/request/api/mp/chat.js'

export default {
  data() {
    return {
      keyword: '',
      searchFocused: false,
      items: [],
      loading: false
    }
  },
  onShow() {
    this.loadInbox()
  },
  onPullDownRefresh() {
    this.loadInbox().finally(() => uni.stopPullDownRefresh())
  },
  methods: {
    async loadInbox() {
      this.loading = true
      try {
        const res = await getChatInbox(this.keyword.trim())
        this.items = (res.data && res.data.items) || []
      } catch (e) {
        this.items = []
      } finally {
        this.loading = false
      }
    },
    displayName(row) {
      const ag = row.agent || {}
      if (row.kind === 'session' && row.session) {
        return row.session.title || ag.name || '对话'
      }
      return ag.name || '智能助手'
    },
    previewText(row) {
      if (row.kind === 'session' && row.session && row.session.last_message_preview) {
        return row.session.last_message_preview
      }
      if (row.kind === 'session' && row.session && row.session.agent_status && row.session.agent_status !== 'active') {
        return '仅可查看历史消息'
      }
      if (row.kind === 'agent') {
        return '点击开始对话'
      }
      return ' '
    },
    statusLabel(row) {
      const status = row && row.session && row.session.agent_status
      if (status === 'offline') return '已下架'
      if (status === 'deleted') return '已删除'
      return ''
    },
    avatarText(row) {
      const ag = row.agent || {}
      if (ag.icon_type === 'emoji' && ag.icon) {
        return ag.icon
      }
      const name = (ag.name || '智').trim()
      return name.slice(0, 1)
    },
    avatarUrl(row) {
      const ag = row.agent || {}
      if (ag.icon_type === 'image' && ag.icon_url) {
        return ag.icon_url
      }
      return ''
    },
    async onRowTap(row) {
      if (row.kind === 'session' && row.session) {
        uni.navigateTo({
          url: `/pages/chat/chat?sessionId=${row.session.id}`
        })
        try {
          uni.setStorageSync('last_active_session_id', String(row.session.id))
        } catch (e) {}
        return
      }
      if (row.kind === 'agent' && row.agent) {
        try {
          const res = await createChatSession(row.agent.id)
          const sid = res.data && res.data.id
          if (sid) {
            uni.navigateTo({ url: `/pages/chat/chat?sessionId=${sid}` })
            try {
              uni.setStorageSync('last_active_session_id', String(sid))
            } catch (e) {}
          }
        } catch (e) {
          uni.showToast({ title: '创建会话失败', icon: 'none' })
        }
      }
    },
    onRowLong(row) {
      if (row.kind !== 'session' || !row.session) {
        return
      }
      const sid = row.session.id
      uni.showActionSheet({
        itemList: ['置顶/取消置顶', '修改标题', '删除会话'],
        success: async (res) => {
          if (res.tapIndex === 0) {
            try {
              await patchChatSession(sid, { is_pinned: !row.session.is_pinned })
              this.loadInbox()
            } catch (e) {}
          } else if (res.tapIndex === 1) {
            uni.showModal({
              title: '修改标题',
              editable: true,
              placeholderText: row.session.title || '',
              success: async (r) => {
                if (r.confirm && r.content) {
                  try {
                    await patchChatSession(sid, { title: r.content })
                    this.loadInbox()
                  } catch (e) {}
                }
              }
            })
          } else if (res.tapIndex === 2) {
            uni.showModal({
              title: '确认删除',
              content: '删除后不可恢复',
              success: async (r) => {
                if (r.confirm) {
                  try {
                    await deleteChatSession(sid)
                    this.loadInbox()
                  } catch (e) {}
                }
              }
            })
          }
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.inbox {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f5f5f5;
  box-sizing: border-box;
}
.search-row {
  flex-shrink: 0;
  padding: 20rpx 24rpx 24rpx;
  background: #fff;
}
.search-inner {
  display: flex;
  align-items: center;
  min-height: 88rpx;
  background: #f0f0f0;
  border-radius: 16rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
}
.search-input {
  flex: 1;
  width: 100%;
  height: 88rpx;
  min-height: 88rpx;
  line-height: 44rpx;
  padding: 22rpx 0;
  font-size: 30rpx;
  background: transparent;
  box-sizing: border-box;
}
.list-wrap {
  flex: 1;
  min-height: 0;
}
.hint {
  text-align: center;
  color: #999;
  padding: 40rpx;
  font-size: 28rpx;
}
.row {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 24rpx;
  background: #fff;
  border-bottom: 1rpx solid #eee;
}
.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 8rpx;
  margin-right: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.avatar-text {
  font-size: 40rpx;
}
.avatar-img {
  width: 96rpx;
  height: 96rpx;
}
.meta {
  flex: 1;
  min-width: 0;
}
.title-line {
  display: flex;
  flex-direction: row;
  align-items: center;
}
.name {
  font-size: 32rpx;
  color: #222;
  font-weight: 500;
}
.pin {
  margin-left: 12rpx;
  font-size: 22rpx;
  color: #007aff;
}
.state {
  margin-left: 12rpx;
  font-size: 22rpx;
  color: #b26a00;
  background: #fff3df;
  border-radius: 8rpx;
  padding: 2rpx 10rpx;
}
.preview {
  font-size: 26rpx;
  color: #888;
  margin-top: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
