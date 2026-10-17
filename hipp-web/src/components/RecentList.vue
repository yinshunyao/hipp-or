<template>
  <div class="recent" :class="{ row }">
    <p class="label">最近</p>
    <button v-if="creatable" class="create" type="button" @click="$emit('create')">
      <Icon name="plus" />
      <span>新会话</span>
    </button>
    <p v-if="!items.length" class="empty">暂无会话</p>
    <div
      v-for="item in items"
      :key="item.id"
      class="item"
      :class="{ on: item.id === activeId }"
      @click="$emit('open', item)"
    >
      <span class="name">{{ item.title }}</span>
      <span class="acts" @click.stop>
        <button
          v-if="item.closed"
          class="share"
          type="button"
          :aria-label="item.shared ? '复制链接' : '分享'"
          :data-tip="item.shared ? '复制链接' : '分享'"
          @click.stop="$emit('share', item)"
        >
          <Icon :name="item.shared ? 'link' : 'share'" />
        </button>
        <button
          v-if="item.closed && item.shared"
          class="share stop"
          type="button"
          aria-label="停止分享"
          data-tip="停止分享"
          @click.stop="$emit('unshare', item)"
        >
          <Icon name="unlink" />
        </button>
        <button class="file" type="button" aria-label="归档" data-tip="归档" @click.stop="$emit('file', item)">
          <Icon name="box" />
        </button>
      </span>
    </div>
    <button class="folder" type="button" @click="archiveOpen = !archiveOpen">
      <Icon name="chev" class="chev" :class="{ open: archiveOpen }" />
      <Icon name="box" />
      归档
    </button>
    <div v-if="archiveOpen" class="archive">
      <p v-if="!archiveItems.length" class="empty">暂无归档</p>
      <div
        v-for="item in archiveItems"
        :key="item.id"
        class="item filed"
        :class="{ on: item.id === activeId }"
        @click="$emit('open', item)"
      >
        <span class="name">{{ item.title }}</span>
        <span class="meta">{{ item.when }} · {{ item.tokensLabel }}</span>
        <span v-if="item.closed" class="acts">
          <button
            class="share"
            type="button"
            :aria-label="item.shared ? '复制链接' : '分享'"
            :data-tip="item.shared ? '复制链接' : '分享'"
            @click.stop="$emit('share', item)"
          >
            <Icon :name="item.shared ? 'link' : 'share'" />
          </button>
          <button
            v-if="item.shared"
            class="share stop"
            type="button"
            aria-label="停止分享"
            data-tip="停止分享"
            @click.stop="$emit('unshare', item)"
          >
            <Icon name="unlink" />
          </button>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Icon from '@/components/Icon.vue'

defineProps({
  items: { type: Array, default: () => [] },
  archiveItems: { type: Array, default: () => [] },
  activeId: { type: Number, default: 0 },
  row: { type: Boolean, default: false },
  creatable: { type: Boolean, default: false }
})
defineEmits(['open', 'create', 'file', 'share', 'unshare'])
const archiveOpen = ref(false)
</script>

<style scoped>
.recent { display: flex; flex-direction: column; gap: 2px; min-height: 0; }
.label {
  margin: 8px 12px 4px;
  font-size: 12px;
  letter-spacing: 0.12em;
  color: rgba(244, 239, 230, 0.55);
}
.empty { margin: 4px 12px; color: rgba(244, 239, 230, 0.45); font-size: 13px; }
.item, .folder, .create {
  border: 0;
  background: transparent;
  color: rgba(244, 239, 230, 0.82);
  text-align: left;
  padding: 8px 10px;
  border-radius: 10px;
}
.item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.name {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item.on, .item:hover, .folder:hover { background: rgba(244, 239, 230, 0.08); color: #fff; }
.create {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 2px 8px 6px;
  color: #1a140c;
  font-weight: 650;
  background: var(--brass-2, #e6c98a);
}
.create:hover { color: #1a140c; filter: brightness(1.06); }
.item.on { box-shadow: inset 2px 0 0 var(--brass-2); }
.file, .share {
  position: relative;
  flex: none;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: rgba(230, 201, 138, 0.95);
  padding: 0;
}
.file:hover, .share:hover, .file:focus-visible, .share:focus-visible { background: rgba(230, 201, 138, 0.14); }
.file :deep(.ico), .share :deep(.ico) { width: 14px; height: 14px; }
.file::after, .share::after {
  content: attr(data-tip);
  position: absolute;
  left: 50%;
  bottom: calc(100% + 6px);
  transform: translateX(-50%);
  padding: 3px 7px;
  border-radius: 6px;
  background: #f4efe6;
  color: #1a140c;
  font-size: 12px;
  line-height: 1.3;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  z-index: 4;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.28);
}
.file:hover::after, .share:hover::after,
.file:focus-visible::after, .share:focus-visible::after { opacity: 1; }
.item:hover, .item:focus-within { position: relative; z-index: 2; }
.folder {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  color: rgba(244, 239, 230, 0.72);
}
.chev { transition: transform 0.15s ease; }
.chev.open { transform: rotate(90deg); }
.archive { display: flex; flex-direction: column; gap: 2px; }
.filed { align-items: flex-start; flex-direction: column; gap: 2px; }
.meta {
  color: rgba(244, 239, 230, 0.45);
  font-size: 12px;
  white-space: nowrap;
}
.share { align-self: center; color: var(--brass-2, #e6c98a); }
.acts { display: flex; align-items: center; gap: 2px; flex: none; align-self: center; }
.filed .acts { align-self: flex-start; }
.stop { color: rgba(244, 239, 230, 0.55); }
.stop:hover, .stop:focus-visible { color: #fff; }
.row { flex-direction: row; align-items: center; gap: 8px; overflow-x: auto; }
.row .label { margin: 0 4px 0 0; flex: none; color: var(--text-3); }
.row .empty { margin: 0; color: var(--text-3); flex: none; }
.row .item, .row .folder, .row .create {
  flex: none;
  max-width: 220px;
  color: var(--text);
  background: var(--paper-2);
  border: 0;
}
.row .item.on { color: var(--text); background: var(--surface); box-shadow: inset 0 -2px 0 var(--brass); }
.row .create { color: #1a140c; background: var(--brass-2); }
.row .folder { margin-top: 0; color: var(--text-2); }
.row .archive { flex-direction: row; }
.row .filed { flex-direction: column; }
.row .meta { color: var(--text-3); }
.row .share { color: var(--brass); }
.row .share:hover, .row .share:focus-visible { color: var(--text); background: rgba(0, 0, 0, 0.05); }
.row .stop { color: var(--text-3); }
.row .file::after, .row .share::after { background: #1a140c; color: #f4efe6; }
</style>
