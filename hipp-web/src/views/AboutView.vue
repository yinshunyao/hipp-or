<template>
  <section class="page">
    <RouterLink class="back" to="/mine">返回我的</RouterLink>
    <div class="mark">AI</div>
    <h1>{{ title }}</h1>
    <dl>
      <div><dt>版本信息</dt><dd>v{{ version }}</dd></div>
      <div><dt>官方邮箱</dt><dd>{{ email || '—' }}</dd></div>
      <div><dt>服务热线</dt><dd>{{ phone || '17302868369' }}</dd></div>
      <div><dt>公司网站</dt><dd><a v-if="site" :href="site" target="_blank" rel="noopener">{{ site }}</a><template v-else>—</template></dd></div>
    </dl>
    <p class="copy">{{ footer }}</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getBaseConfig } from '@/api/auth'

const title = ref('爱宝喜宝软件工作室')
const version = ref('1.0.0')
const email = ref('yinshunyao@qq.com')
const phone = ref('17302868369')
const site = ref('')
const footer = ref('© 爱宝喜宝软件工作室')

onMounted(async () => {
  try {
    const res = await getBaseConfig()
    const data = res.data || {}
    if (data.web_title) title.value = data.web_title
    if (data.web_copyright) footer.value = data.web_copyright
    if (data.wx_server_email) email.value = data.wx_server_email
    if (data.wx_server_phone) phone.value = data.wx_server_phone
    if (data.wx_server_site) site.value = data.wx_server_site
  } catch (err) { /* 保留默认介绍 */ }
})
</script>

<style scoped>
.page { max-width: 680px; margin: 0 auto; padding: 28px 20px 64px; text-align: center; }
.back { display: block; text-align: left; color: var(--text-3); text-decoration: none; }
.mark {
  width: 72px; height: 72px; margin: 24px auto 8px; border-radius: 20px; display: grid; place-items: center;
  background: linear-gradient(145deg, #3d5368, #1c5f68); color: #f4efe6; font-family: var(--display); font-size: 24px;
}
h1 { font-family: var(--serif); }
dl { text-align: left; margin: 24px 0; }
div { display: flex; justify-content: space-between; gap: 12px; padding: 14px 0; border-bottom: 1px solid var(--line); }
dt { color: var(--text-2); }
dd { margin: 0; }
a { color: var(--teal); }
.copy { color: var(--text-3); font-size: 13px; }
</style>
