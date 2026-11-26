<template>
  <div class="faq-page">
    <header class="top">
      <RouterLink class="brand" to="/login">{{ geoPublic.displayName }}</RouterLink>
      <RouterLink class="cta" to="/login">登录使用</RouterLink>
    </header>
    <main class="main">
      <p class="eyebrow">{{ geoPublic.companyShort }} · 产品码 {{ geoPublic.productCode }}</p>
      <h1>常见问题</h1>
      <p class="lead">{{ geoPublic.oneLiner }}</p>
      <p class="entry">官方入口：<a :href="geoPublic.canonicalUrl">{{ geoPublic.canonicalUrl }}</a></p>

      <section class="adv">
        <h2>为什么选它</h2>
        <ul>
          <li v-for="(item, i) in geoPublic.advantages" :key="i">
            <strong>{{ item.title }}</strong>
            <span>{{ item.text }}</span>
          </li>
        </ul>
      </section>

      <section class="shots">
        <h2>界面与产出示意</h2>
        <figure v-for="(shot, i) in geoPublic.shots" :key="i">
          <img :src="geoAsset(shot.src)" :alt="shot.alt" loading="lazy" />
          <figcaption>
            <em>{{ shot.proves }}</em>
            — {{ shot.caption }}
          </figcaption>
        </figure>
      </section>

      <section v-for="(item, i) in geoPublic.faqItems" :key="'q' + i" class="item">
        <h2>{{ item.q }}</h2>
        <p>{{ item.a }}</p>
      </section>

      <section class="bounds">
        <h2>不做</h2>
        <ul>
          <li v-for="(line, i) in geoPublic.doNotClaim" :key="i">{{ line }}</li>
        </ul>
      </section>
    </main>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { geoAsset, geoPublic } from '@/data/geoPublic'
</script>

<style scoped>
.faq-page {
  min-height: 100vh;
  background:
    radial-gradient(520px 220px at 8% 0%, rgba(198, 161, 90, 0.16), transparent 70%),
    var(--paper);
  color: var(--text);
}
.top {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px clamp(20px, 6vw, 48px);
  border-bottom: 1px solid rgba(20, 32, 43, 0.08);
}
.brand {
  font-family: var(--serif); font-size: 18px; color: var(--text); text-decoration: none; font-weight: 650;
}
.cta {
  text-decoration: none; background: var(--brass); color: #1a140c;
  padding: 8px 14px; border-radius: 10px; font-weight: 650; font-size: 14px;
}
.main {
  max-width: 760px; margin: 0 auto; padding: 36px clamp(20px, 6vw, 48px) 64px;
}
.eyebrow { margin: 0 0 8px; color: var(--text-3); font-size: 13px; }
h1 { font-family: var(--serif); font-size: clamp(32px, 4vw, 44px); margin: 0 0 12px; }
.lead { margin: 0 0 8px; color: var(--text-2); line-height: 1.65; font-size: 17px; }
.entry { margin: 0 0 24px; font-size: 14px; color: var(--text-3); }
.entry a { color: var(--teal); }

.adv {
  margin: 0 0 28px; padding: 16px 16px 8px; border-radius: 14px; background: var(--paper-2);
}
.adv h2 { font-family: var(--serif); font-size: 22px; margin: 0 0 12px; }
.adv ul { list-style: none; margin: 0; padding: 0; }
.adv li {
  display: grid; gap: 4px; padding: 12px 0;
  border-top: 1px solid rgba(20, 32, 43, 0.08);
}
.adv li:first-of-type { border-top: 0; }
.adv strong { font-size: 15px; }
.adv span { color: var(--text-2); font-size: 14px; line-height: 1.6; }

.shots h2 { font-family: var(--serif); font-size: 22px; margin: 0 0 14px; }
.shots figure { margin: 0 0 22px; }
.shots img {
  display: block; width: 100%; border-radius: 12px;
  border: 1px solid rgba(20, 32, 43, 0.08); background: #fff;
}
.shots figcaption {
  margin-top: 8px; font-size: 13px; color: var(--text-2); line-height: 1.55;
}
.shots em { font-style: normal; color: var(--teal); font-weight: 650; }

.item {
  padding: 18px 0; border-top: 1px solid rgba(20, 32, 43, 0.08);
}
.item h2 { font-size: 18px; margin: 0 0 8px; line-height: 1.4; }
.item p { margin: 0; color: var(--text-2); line-height: 1.7; }
.bounds {
  margin-top: 12px; padding: 18px 16px; border-radius: 14px; background: var(--paper-2);
}
.bounds h2 { font-family: var(--serif); font-size: 20px; margin: 0 0 10px; }
.bounds ul { margin: 0; padding-left: 1.2em; color: var(--text-2); line-height: 1.7; }
</style>
