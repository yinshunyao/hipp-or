<template>
  <div class="shell">
    <aside class="rail">
      <div class="brand">
        <span class="mark">需求</span>
        <span class="brand-copy">
          <span class="brand-kicker">HIPP</span>
          <span class="brand-name">智臻善算</span>
        </span>
      </div>
      <div class="menu">
        <div class="group">
          <RouterLink to="/requirement" :class="{ on: expanded === 'requirement' }">
            <Icon name="req" />
            <span>需求</span>
          </RouterLink>
          <RecentList
            v-if="!auth.isEntitlement && expanded === 'requirement'"
            class="recent-desk"
            creatable
            :items="requirementItems"
            :archive-items="nav.requirementArchived"
            :active-id="activeId"
            @open="openSession"
            @create="newSession"
            @file="fileSession"
            @share="shareSession"
            @unshare="unshareSession"
          />
        </div>
        <div v-if="showBusiness && !auth.isEntitlement" class="group">
          <RouterLink to="/business" :class="{ on: expanded === 'business' }">
            <Icon name="biz" />
            <span>商业</span>
          </RouterLink>
          <RecentList
            v-if="expanded === 'business'"
            class="recent-desk"
            creatable
            :items="businessItems"
            :archive-items="nav.businessArchived"
            :active-id="activeId"
            @open="openSession"
            @create="newSession"
            @file="fileSession"
            @share="shareSession"
            @unshare="unshareSession"
          />
        </div>
      </div>
      <button class="who" type="button" @click="toggleAccount">
        <UserAvatar :src="auth.avatarSrc" :name="auth.displayName" />
        <span class="who-copy">
          <span class="who-kicker">账号</span>
          <span class="who-name">{{ auth.displayName }}</span>
        </span>
      </button>
      <button class="contact" type="button" @click="aboutOpen = true">
        <Icon name="mail" />
        <span>联系我们</span>
      </button>
    </aside>
    <main class="stage">
      <RecentList
        v-if="!auth.isEntitlement"
        class="recent-mobile"
        row
        creatable
        :items="mobileItems"
        :archive-items="mobileArchived"
        :active-id="activeId"
        @open="openSession"
        @create="newSession"
        @file="fileSession"
        @share="shareSession"
        @unshare="unshareSession"
      />
      <div class="stage-body">
        <slot />
        <AccountPanel
          :open="accountOpen"
          :initial-section="accountSection"
          :about="aboutOpen"
          @close-about="aboutOpen = false"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, provide, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AccountPanel from '@/components/AccountPanel.vue'
import Icon from '@/components/Icon.vue'
import RecentList from '@/components/RecentList.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { createChatShare, deleteChatShare, patchChatSession } from '@/api/chat'
import { SHOW_BUSINESS_SCENE } from '@/config/features'
import { useAuthStore } from '@/stores/auth'
import { giveShareLink } from '@/utils/share'
import { toast } from '@/utils/toast'
import { useSessionNav } from '@/stores/sessions'

const auth = useAuthStore()
const nav = useSessionNav()
const route = useRoute()
const router = useRouter()
const showBusiness = SHOW_BUSINESS_SCENE
const accountOpen = ref(false)
const accountSection = ref('')
const aboutOpen = ref(false)
function openAbout() { aboutOpen.value = true }
provide('openAbout', openAbout)

function withLive(recent, live, archived) {
  const hidden = new Set((archived || []).map((item) => item.id))
  const list = recent.map((item) => {
    if (live && item.id === live.id && live.title) return { ...item, title: live.title }
    return item
  })
  if (live && live.id && !hidden.has(live.id) && !list.some((item) => item.id === live.id)) list.unshift(live)
  return list
}
const requirementItems = computed(() => withLive(nav.requirement, nav.requirementLive, nav.requirementArchived))
const businessItems = computed(() => withLive(nav.business, nav.businessLive, nav.businessArchived))
const mobileArchived = computed(() => {
  if (!showBusiness) return nav.requirementArchived
  if (route.name === 'business') return nav.businessArchived
  if (route.name === 'chat') {
    const id = Number(route.params.id)
    if (nav.business.some((item) => item.id === id) || nav.businessArchived.some((item) => item.id === id)) {
      return nav.businessArchived
    }
  }
  return nav.requirementArchived
})
const mobileItems = computed(() => {
  if (!showBusiness) return requirementItems.value
  if (route.name === 'business') return businessItems.value
  if (route.name === 'chat') {
    const id = Number(route.params.id)
    if (businessItems.value.some((item) => item.id === id) || nav.businessArchived.some((item) => item.id === id)) {
      return businessItems.value
    }
  }
  return requirementItems.value
})
const expanded = computed(() => {
  if (!showBusiness) return 'requirement'
  if (route.name === 'business') return 'business'
  if (route.name === 'chat') {
    const id = Number(route.params.id)
    if (businessItems.value.some((item) => item.id === id) || nav.businessArchived.some((item) => item.id === id)) return 'business'
  }
  return 'requirement'
})
const activeId = computed(() => {
  if (route.name === 'chat') return Number(route.params.id) || 0
  if (showBusiness && route.name === 'business') return nav.businessLive ? nav.businessLive.id : 0
  return nav.requirementLive ? nav.requirementLive.id : 0
})

function toggleAccount() {
  accountOpen.value = !accountOpen.value
  if (accountOpen.value) accountSection.value = auth.mustSetPasswordWithoutOld ? 'password' : ''
}
function newSession() {
  const scene = showBusiness && expanded.value === 'business' ? 'business' : 'requirement'
  accountOpen.value = false
  if (route.name === scene) {
    nav.askNew()
    return
  }
  router.push({ name: scene, query: { fresh: '1' } })
}
async function shareSession(item) {
  if (!item || !item.id) return
  try {
    const res = await createChatShare(item.id)
    const token = res.data && res.data.share_token
    if (!token) return
    await giveShareLink(token)
    if (!item.shared) await nav.refresh()
  } catch (err) { /* 接口已提示 */ }
}
async function unshareSession(item) {
  if (!item || !item.id) return
  try {
    await deleteChatShare(item.id)
    toast('已停止分享')
    await nav.refresh()
  } catch (err) { /* 接口已提示 */ }
}
async function fileSession(item) {
  if (!item || !item.id) return
  try {
    await patchChatSession(item.id, { is_archived: true })
    if (nav.requirementLive && nav.requirementLive.id === item.id) nav.setLive('requirement', null)
    if (nav.businessLive && nav.businessLive.id === item.id) nav.setLive('business', null)
    await nav.refresh()
  } catch (err) { /* 保持原列表 */ }
}
function openSession(item) {
  if (!item || !item.id) return
  if (route.name === 'chat' && Number(route.params.id) === item.id) return
  accountOpen.value = false
  if (nav.requirementLive && nav.requirementLive.id === item.id) {
    if (route.name !== 'requirement') router.push('/requirement')
    return
  }
  if (showBusiness && nav.businessLive && nav.businessLive.id === item.id) {
    if (route.name !== 'business') router.push('/business')
    return
  }
  router.push(`/chat/${item.id}`)
}
watch(() => auth.token, () => { nav.refresh() }, { immediate: true })
watch(
  () => route.name,
  (name) => {
    if (name === 'wallet') accountOpen.value = false
  }
)
watch(() => route.query.account, (value) => {
  if (value !== 'profile' && value !== 'password' && value !== 'about') return
  accountOpen.value = true
  accountSection.value = value
  const query = { ...route.query }
  delete query.account
  router.replace({ query })
}, { immediate: true })
watch(() => auth.mustSetPasswordWithoutOld, (value) => {
  if (value && route.meta.shell) {
    accountOpen.value = true
    accountSection.value = 'password'
  }
}, { immediate: true })
</script>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: var(--rail) 1fr;
}
.rail {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 20px 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background:
    linear-gradient(180deg, rgba(198, 161, 90, 0.16), transparent 120px),
    linear-gradient(90deg, transparent, rgba(198, 161, 90, 0.18) 1px, transparent 1px),
    var(--ink);
  background-size: auto, 100% 100%, auto;
  color: #f4efe6;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
  padding: 2px 8px 4px;
  flex: none;
}
.mark {
  min-width: 40px;
  height: 40px;
  padding: 0 8px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 32% 28%, #3d5366, #15202a 72%);
  box-shadow: inset 0 0 0 1px rgba(230, 201, 138, 0.28);
  font-family: var(--serif);
  font-size: 13px;
  font-weight: 650;
  letter-spacing: 0.04em;
}
.brand-copy { display: flex; flex-direction: column; min-width: 0; }
.brand-kicker {
  font-family: var(--display);
  font-size: 10px;
  letter-spacing: 0.18em;
  color: var(--brass-2);
  line-height: 1.2;
}
.brand-name { font-family: var(--serif); font-size: 18px; line-height: 1.2; }
.menu { flex: 1; min-height: 0; overflow: auto; display: flex; flex-direction: column; gap: 8px; }
.group { display: flex; flex-direction: column; gap: 2px; }
.menu a {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  padding: 10px 12px;
  border-radius: 12px;
  color: rgba(244, 239, 230, 0.72);
  font-weight: 500;
}
.menu a.on, .menu a:hover { background: rgba(244, 239, 230, 0.08); color: #fff; }
.menu a.on {
  background: rgba(198, 161, 90, 0.14);
  box-shadow: inset 2px 0 0 var(--brass-2);
}
.recent-desk { overflow: visible; }
.contact {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 0;
  background: rgba(244, 239, 230, 0.06);
  color: rgba(244, 239, 230, 0.82);
  text-align: left;
  padding: 9px 12px;
  border-radius: 12px;
  flex: none;
}
.contact:hover { background: rgba(244, 239, 230, 0.12); color: #fff; }
.who {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  border: 0;
  background: rgba(244, 239, 230, 0.06);
  color: inherit;
  text-align: left;
  padding: 8px;
  border-radius: 14px;
  flex: none;
}
.who:hover { background: rgba(244, 239, 230, 0.12); }
.who-copy { min-width: 0; display: flex; flex-direction: column; }
.who-kicker { font-size: 10px; letter-spacing: 0.14em; color: rgba(230, 201, 138, 0.8); line-height: 1.2; }
.who-name { font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
.stage {
  min-width: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.stage-body {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
}
.recent-mobile { display: none; }

@media (max-width: 860px) {
  .shell { grid-template-columns: 1fr; }
  .rail {
    position: fixed;
    z-index: 20;
    left: 0;
    right: 0;
    bottom: 0;
    top: auto;
    height: auto;
    flex-direction: row;
    align-items: center;
    padding: 8px 10px calc(8px + env(safe-area-inset-bottom));
    gap: 8px;
  }
  .brand-copy, .who-copy, .recent-desk, .contact span { display: none; }
  .menu { flex-direction: row; flex: 1; overflow: visible; justify-content: space-around; gap: 0; }
  .group { flex-direction: row; }
  .menu a { flex-direction: column; gap: 2px; font-size: 11px; padding: 6px 4px; }
  .menu a.on { box-shadow: inset 0 -2px 0 var(--brass-2); }
  .who, .contact { width: auto; margin-top: 0; padding: 4px 8px; background: transparent; }
  .stage { height: 100vh; padding-bottom: 76px; box-sizing: border-box; }
  .recent-mobile {
    display: flex;
    flex: none;
    padding: 10px 12px;
    border-bottom: 1px solid var(--line);
    background: var(--paper);
  }
}
</style>
