<template>
  <div class="home">
    <header class="top">
      <RouterLink class="brand" to="/">
        <span class="mark">AI</span>
        <span>爱宝喜宝软件工作室</span>
      </RouterLink>
      <nav>
        <a href="#work">案例</a>
        <a href="#contact">联系</a>
        <RouterLink v-if="auth.loggedIn" to="/topics">进入话题</RouterLink>
        <RouterLink v-else to="/login">登录</RouterLink>
      </nav>
    </header>

    <section class="hero">
      <div class="copy">
        <p class="eyebrow">Chengdu Studio · Since the craft</p>
        <h1>智能 AI 应用<br />系统定制专家</h1>
        <p class="lede">
          专注于图像识别、智能客服和标注平台等 AI 应用系统的定制开发。用技术赋能业务，用 AI 驱动未来。
        </p>
        <div class="tags">
          <span>图像识别</span>
          <span>智能客服</span>
          <span>标注平台</span>
        </div>
        <div class="cta">
          <button type="button" class="primary" @click="go('/requirement')">需求咨询</button>
        </div>
      </div>
      <aside class="panel">
        <p class="panel-kicker">01 — 04</p>
        <ol>
          <li v-for="(item, i) in techItems" :key="item.title">
            <em>{{ String(i + 1).padStart(2, '0') }}</em>
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.text }}</span>
            </div>
          </li>
        </ol>
      </aside>
    </section>

    <section id="work" class="work">
      <div class="section-head">
        <p>Selected work</p>
        <h2>成功案例</h2>
      </div>
      <div class="cases">
        <article v-for="item in cases" :key="item.title">
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
          <div class="tags slim">
            <span v-for="tag in item.tags" :key="tag">{{ tag }}</span>
          </div>
        </article>
      </div>
    </section>

    <section id="contact" class="contact">
      <div>
        <p class="eyebrow light">Contact</p>
        <h2>准备开始您的 AI 项目了吗？</h2>
        <p>登录后可进行需求咨询，话题结束后会归档到话题列表。</p>
      </div>
      <div class="cards">
        <a class="card" href="tel:17302868369">
          <span>微信电话</span>
          <strong>17302868369</strong>
          <em>殷先生</em>
        </a>
        <div class="card">
          <span>工作室地址</span>
          <strong>锦江区锦华路一段 8 号</strong>
          <em>四川省成都市锦江区东湖街道锦华路一段8号1栋11单元26层2649号</em>
        </div>
      </div>
    </section>

    <footer>
      <span>© {{ year }} 爱宝喜宝软件工作室</span>
      <span>专业的 AI 应用系统定制服务提供商</span>
      <span>备案号：蜀ICP备2026013590号-2X</span>
    </footer>

    <button class="fab" type="button" @click="go('/requirement')">需求<br />咨询</button>
  </div>
</template>

<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const year = new Date().getFullYear()
const techItems = [
  { title: '千万级产品经验', text: '多个千万级用户规模的产品级交付经验，大规模系统架构与性能优化。' },
  { title: '模型训练调优', text: '独立研发与模型训练调优经验，针对不同场景优化 AI 模型性能。' },
  { title: '高效交付', text: '敏捷流程与项目管理经验，交付效率高、响应速度快。' },
  { title: '成都工匠获得者', text: '秉承诚信为本的工匠精神，项目精益求精。' }
]
const cases = [
  { title: '图像识别系统', desc: '企业定制高精度图像识别，支持多场景检测、分类与定位。', tags: ['深度学习', '计算机视觉'] },
  { title: '智能客服平台', desc: '基于自然语言处理的智能客服，多渠道接入与智能问答。', tags: ['自然语言处理', '智能对话'] },
  { title: '数据标注平台', desc: '图像、文本、音频等多类型标注与质检审核流程。', tags: ['数据管理', '质量控制'] }
]

function go(path) {
  if (auth.loggedIn) router.push(path)
  else router.push({ name: 'login', query: { redirect: path } })
}
</script>

<style scoped>
.home { background: var(--paper); color: var(--text); }
.top {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 7vw;
  background: rgba(243, 238, 230, 0.86);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--line);
}
.brand { display: flex; align-items: center; gap: 10px; text-decoration: none; font-family: var(--serif); }
.mark {
  width: 34px; height: 34px; border-radius: 8px; display: grid; place-items: center;
  background: var(--ink); color: #f4efe6; font-family: var(--display);
}
nav { display: flex; gap: 18px; align-items: center; }
nav a { text-decoration: none; color: var(--text-2); }
nav a:last-child {
  color: #f6f1e8; background: var(--ink); border-radius: 999px; padding: 8px 14px;
}
.hero {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  min-height: calc(100vh - 68px);
  background:
    radial-gradient(500px 240px at 12% 20%, rgba(198, 161, 90, 0.2), transparent 60%),
    linear-gradient(165deg, #1a2836 0%, #14202b 55%, #101820 100%);
  color: #f4efe6;
}
.copy, .panel { padding: 64px 7vw; }
h1 {
  margin: 12px 0 16px;
  font-family: var(--serif);
  font-weight: 700;
  font-size: clamp(42px, 5vw, 68px);
  line-height: 1.12;
  letter-spacing: -0.03em;
  animation: rise 0.7s ease both;
}
.lede { max-width: 38rem; color: #d5dde4; font-size: 17px; animation: rise 0.7s ease 0.12s both; }
.eyebrow { letter-spacing: 0.16em; text-transform: uppercase; font-family: var(--display); color: var(--brass-2); font-size: 13px; }
.tags { display: flex; gap: 8px; flex-wrap: wrap; margin: 22px 0; }
.tags span {
  border: 1px solid rgba(244, 239, 230, 0.24);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 13px;
}
.cta { display: flex; gap: 12px; }
button, .line { border-radius: 999px; padding: 12px 18px; font-weight: 650; }
.primary { border: 0; background: linear-gradient(160deg, #e6c98a, #c6a15a); color: #1a140c; }
.line { border: 1px solid rgba(244, 239, 230, 0.4); background: transparent; color: #f4efe6; }
.panel { background: rgba(255, 255, 255, 0.03); border-left: 1px solid rgba(244, 239, 230, 0.08); }
.panel-kicker { font-family: var(--display); color: var(--brass-2); letter-spacing: 0.14em; }
ol { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 18px; }
li { display: grid; grid-template-columns: 48px 1fr; gap: 8px; }
em { font-family: var(--display); font-style: normal; color: var(--brass-2); }
strong { display: block; font-family: var(--serif); font-size: 18px; }
li span { color: #c5d0d8; font-size: 14px; }
.work, .contact { padding: 72px 7vw; }
.section-head p, .contact .eyebrow { color: var(--brass); }
.work h2, .contact h2 { font-family: var(--serif); font-size: clamp(32px, 4vw, 48px); margin: 6px 0 22px; }
.cases { display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 16px; }
article, .card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 22px;
  box-shadow: var(--shadow);
}
article:first-child { background: var(--ink); color: #f4efe6; }
article h3 { font-family: var(--serif); font-size: 26px; margin: 0 0 8px; }
.slim span { border-color: currentColor; }
.contact { display: grid; grid-template-columns: 0.8fr 1.2fr; gap: 28px; align-items: end; }
.cards { display: grid; gap: 12px; }
.card { display: flex; flex-direction: column; text-decoration: none; color: inherit; }
.card span { color: var(--brass); font-size: 13px; letter-spacing: 0.08em; }
.card strong { font-family: var(--serif); font-size: 26px; margin: 6px 0; }
.card em { font-style: normal; color: var(--text-2); }
footer {
  display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap;
  padding: 22px 7vw 40px; color: var(--text-3); font-size: 13px;
  border-top: 1px solid var(--line);
}
.fab {
  position: fixed; right: 22px; bottom: 22px; z-index: 6;
  width: 72px; height: 72px; border: 0; border-radius: 50%;
  background: linear-gradient(165deg, #2e8cc9, #1f6dad);
  color: white; font-weight: 700; line-height: 1.15;
  box-shadow: 0 12px 28px rgba(31, 109, 173, 0.35);
}
@keyframes rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: none; }
}
@media (max-width: 960px) {
  .hero, .cases, .contact { grid-template-columns: 1fr; }
  .copy, .panel, .work, .contact, .top, footer { padding-left: 20px; padding-right: 20px; }
  .panel { border-left: 0; border-top: 1px solid rgba(244, 239, 230, 0.08); }
  .fab { bottom: 18px; }
}
</style>
