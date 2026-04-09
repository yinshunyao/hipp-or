<template>
  <view :class="themeClass" class="corp-home">
    <scroll-view scroll-y class="corp-home__scroll" :show-scrollbar="false">
      <view class="corp-hero">
        <view class="corp-hero__inner">
          <view class="corp-hero__brand">
            <view class="corp-hero__logo">AI</view>
            <text class="corp-hero__brand-name">爱宝喜宝软件工作室</text>
          </view>
          <text class="corp-hero__title">智能AI应用\n系统定制专家</text>
          <text class="corp-hero__sub">专注于图像识别、智能客服和标注平台等AI应用系统的定制开发\n用技术赋能业务，用AI驱动未来</text>
          <view class="corp-hero__tags">
            <text class="corp-hero__tag">图像识别</text>
            <text class="corp-hero__tag">智能客服</text>
            <text class="corp-hero__tag">标注平台</text>
          </view>
        </view>
      </view>

      <view class="corp-section corp-section--white">
        <text class="corp-section__title">核心技术优势</text>
        <text class="corp-section__desc">多年实战经验积累，专业AI技术团队，为您提供高品质的定制化解决方案</text>
        <view class="corp-grid">
          <view v-for="(it, i) in techItems" :key="i" class="corp-card">
            <view class="corp-card__icon">{{ it.icon }}</view>
            <text class="corp-card__h">{{ it.title }}</text>
            <text class="corp-card__p">{{ it.text }}</text>
          </view>
        </view>
      </view>

      <view class="corp-section corp-section--muted">
        <text class="corp-section__title">成功案例展示</text>
        <text class="corp-section__desc">我们为各行业客户提供专业的AI应用系统定制服务</text>
        <view class="corp-cases">
          <view v-for="(c, j) in cases" :key="j" class="corp-case">
            <view class="corp-case__head">
              <text class="corp-case__head-icon">{{ c.icon }}</text>
              <text class="corp-case__head-title">{{ c.title }}</text>
            </view>
            <text class="corp-case__body">{{ c.desc }}</text>
            <view class="corp-case__tags">
              <text v-for="(t, k) in c.tags" :key="k" class="corp-case__tag">{{ t }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="corp-section corp-section--white">
        <text class="corp-section__title">联系我们</text>
        <text class="corp-section__desc">立即获取专业的AI应用系统定制解决方案</text>
        <view class="corp-contact">
          <view class="corp-contact__block">
            <text class="corp-contact__label">微信电话</text>
            <text class="corp-contact__value" @click="callPhone">17302868369</text>
            <text class="corp-contact__hint">殷先生</text>
          </view>
          <view class="corp-contact__block">
            <text class="corp-contact__label">工作室地址</text>
            <text class="corp-contact__addr">四川省成都市锦江区东湖街道锦华路一段8号1栋11单元26层2649号</text>
          </view>
        </view>
      </view>

      <view class="corp-cta">
        <text class="corp-cta__title">准备开始您的AI项目了吗？</text>
        <text class="corp-cta__sub">选择下方「需求」或「商业」Tab 进行智能咨询（未登录各场景可体验 2 次完整对话，以话题归档为准）</text>
        <view class="corp-cta__row">
          <button class="corp-cta__btn corp-cta__btn--primary" hover-class="corp-cta__btn--hover" @tap="goRequirement">需求咨询</button>
          <button class="corp-cta__btn" hover-class="corp-cta__btn--hover" @tap="goBusiness">商业咨询</button>
        </view>
      </view>

      <view class="corp-footer">
        <text class="corp-footer__line">© {{ year }} 爱宝喜宝软件工作室</text>
        <text class="corp-footer__line corp-footer__muted">专业的AI应用系统定制服务提供商</text>
        <text class="corp-footer__line corp-footer__icp">备案号：蜀ICP备2026013590号-2X</text>
      </view>
      <view class="corp-safe" />
    </scroll-view>

    <view class="corp-home__fab" hover-class="corp-home__fab--hover" @tap="goRequirement">
      <text class="corp-home__fab-line">需求</text>
      <text class="corp-home__fab-line">咨询</text>
    </view>
  </view>
</template>

<script>
import { themeMixin } from '@/common/mixins/theme.js'

export default {
  mixins: [themeMixin],
  data() {
    return {
      year: new Date().getFullYear(),
      techItems: [
        { icon: '🏆', title: '千万级产品经验', text: '多个千万级用户规模的产品级交付经验，大规模系统架构与性能优化。' },
        { icon: '🧠', title: '模型训练调优', text: '独立研发与模型训练调优经验，针对不同场景优化AI模型性能。' },
        { icon: '🚀', title: '高效交付', text: '敏捷流程与项目管理经验，交付效率高、响应速度快。' },
        { icon: '🎖️', title: '成都工匠获得者', text: '秉承诚信为本的工匠精神，项目精益求精。' }
      ],
      cases: [
        {
          icon: '👁️',
          title: '图像识别系统',
          desc: '企业定制高精度图像识别，支持多场景检测、分类与定位。',
          tags: ['深度学习', '计算机视觉']
        },
        {
          icon: '💬',
          title: '智能客服平台',
          desc: '基于NLP的智能客服，多渠道接入与智能问答，提升服务效率。',
          tags: ['自然语言处理', '智能对话']
        },
        {
          icon: '🏷️',
          title: '数据标注平台',
          desc: '图像、文本、音频等多类型标注与质检审核流程。',
          tags: ['数据管理', '质量控制']
        }
      ]
    }
  },
  onShow() {
    if (typeof this.$mp && this.$mp.page && this.$mp.page.getTabBar) {
      const tab = this.$mp.page.getTabBar()
      if (tab && typeof tab.syncActive === 'function') tab.syncActive()
    }
  },
  methods: {
    goRequirement() {
      uni.switchTab({ url: '/pages/requirement/index' })
    },
    goBusiness() {
      uni.switchTab({ url: '/pages/business/index' })
    },
    callPhone() {
      uni.makePhoneCall({ phoneNumber: '17302868369' })
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/uni.scss';

.corp-home {
  min-height: 100vh;
  background: #f8f9fa;
}

.corp-home__scroll {
  height: 100vh;
  box-sizing: border-box;
}

/* 置于 scroll-view 外，fixed 相对屏幕固定，滚动时长页仍可见 */
.corp-home__fab {
  position: fixed;
  right: 24rpx;
  bottom: calc(140rpx + env(safe-area-inset-bottom));
  z-index: 200;
  width: 104rpx;
  padding: 20rpx 12rpx;
  box-sizing: border-box;
  border-radius: 52rpx;
  background: linear-gradient(165deg, #2e8cc9 0%, #2980b9 45%, #1f6dad 100%);
  box-shadow: 0 10rpx 28rpx rgba(41, 128, 185, 0.42);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}

.corp-home__fab-line {
  font-size: 24rpx;
  font-weight: 600;
  color: #fff;
  line-height: 1.2;
}

.corp-home__fab--hover {
  opacity: 0.9;
}

.corp-hero {
  background: linear-gradient(160deg, #1e2a3a 0%, #2c3e50 45%, #243342 100%);
  padding: calc(88rpx + env(safe-area-inset-top)) 40rpx 72rpx;
  position: relative;
}

.corp-hero__inner {
  max-width: 680rpx;
  margin: 0 auto;
}

.corp-hero__brand {
  display: flex;
  align-items: center;
  margin-bottom: 36rpx;
}

.corp-hero__logo {
  width: 64rpx;
  height: 64rpx;
  background: #34495e;
  border-radius: 8rpx;
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
}

.corp-hero__brand-name {
  font-size: 34rpx;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.corp-hero__title {
  display: block;
  font-size: 48rpx;
  font-weight: 700;
  color: #fff;
  line-height: 1.25;
  margin-bottom: 24rpx;
  white-space: pre-line;
}

.corp-hero__sub {
  display: block;
  font-size: 28rpx;
  color: #ced4da;
  line-height: 1.65;
  margin-bottom: 32rpx;
  white-space: pre-line;
}

.corp-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-bottom: 8rpx;
}

.corp-hero__tag {
  font-size: 24rpx;
  color: #e9ecef;
  padding: 12rpx 20rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.25);
  border-radius: 4rpx;
  background: rgba(255, 255, 255, 0.06);
}

.corp-section {
  padding: 56rpx 32rpx 64rpx;
}

.corp-section--white {
  background: #fff;
  border-bottom: 1rpx solid #e9ecef;
}

.corp-section--muted {
  background: #f8f9fa;
  border-bottom: 1rpx solid #e9ecef;
}

.corp-section__title {
  display: block;
  text-align: center;
  font-size: 40rpx;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 16rpx;
}

.corp-section__desc {
  display: block;
  text-align: center;
  font-size: 28rpx;
  color: #6c757d;
  line-height: 1.6;
  margin-bottom: 40rpx;
  padding: 0 8rpx;
}

.corp-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 24rpx 0;
}

.corp-card {
  width: 48%;
  background: #fafbfc;
  border: 1rpx solid #e9ecef;
  border-radius: 4rpx;
  padding: 28rpx 20rpx;
  box-sizing: border-box;
}

.corp-card__icon {
  font-size: 44rpx;
  text-align: center;
  margin-bottom: 16rpx;
}

.corp-card__h {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #212529;
  margin-bottom: 12rpx;
  text-align: center;
}

.corp-card__p {
  font-size: 24rpx;
  color: #495057;
  line-height: 1.55;
}

.corp-cases {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.corp-case {
  background: #fff;
  border: 1rpx solid #e9ecef;
  border-radius: 4rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 8rpx rgba(44, 62, 80, 0.06);
}

.corp-case__head {
  background: #34495e;
  padding: 32rpx 28rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.corp-case__head-icon {
  font-size: 40rpx;
}

.corp-case__head-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}

.corp-case__body {
  display: block;
  padding: 28rpx;
  font-size: 26rpx;
  color: #495057;
  line-height: 1.55;
}

.corp-case__tags {
  padding: 0 28rpx 28rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.corp-case__tag {
  font-size: 22rpx;
  color: #495057;
  background: #e9ecef;
  padding: 6rpx 14rpx;
  border-radius: 4rpx;
}

.corp-contact__block {
  background: #fafbfc;
  border: 1rpx solid #e9ecef;
  border-radius: 4rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.corp-contact__label {
  display: block;
  font-size: 24rpx;
  color: #6c757d;
  margin-bottom: 8rpx;
}

.corp-contact__value {
  display: block;
  font-size: 36rpx;
  font-weight: 600;
  color: #212529;
}

.corp-contact__hint {
  display: block;
  font-size: 24rpx;
  color: #6c757d;
  margin-top: 8rpx;
}

.corp-contact__addr {
  font-size: 26rpx;
  color: #212529;
  line-height: 1.55;
}

.corp-cta {
  margin: 24rpx 32rpx 40rpx;
  padding: 40rpx 28rpx;
  background: #2c3e50;
  border-radius: 8rpx;
  border: 1rpx solid #243342;
}

.corp-cta__title {
  display: block;
  text-align: center;
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
  margin-bottom: 12rpx;
}

.corp-cta__sub {
  display: block;
  text-align: center;
  font-size: 24rpx;
  color: #bdc3c7;
  line-height: 1.5;
  margin-bottom: 28rpx;
}

.corp-cta__row {
  display: flex;
  gap: 20rpx;
  justify-content: center;
}

.corp-cta__btn {
  flex: 1;
  max-width: 280rpx;
  font-size: 28rpx;
  font-weight: 600;
  padding: 20rpx 16rpx;
  border-radius: 8rpx;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  border: 1rpx solid rgba(255, 255, 255, 0.35);
}

.corp-cta__btn--primary {
  background: #2980b9;
  border-color: #2980b9;
}

.corp-cta__btn--hover {
  opacity: 0.88;
}

.corp-footer {
  padding: 32rpx 24rpx 24rpx;
  text-align: center;
}

.corp-footer__line {
  display: block;
  font-size: 24rpx;
  color: #868e96;
  margin-bottom: 8rpx;
}

.corp-footer__muted {
  color: #adb5bd;
}

.corp-footer__icp {
  margin-top: 12rpx;
  font-size: 22rpx;
  color: #868e96;
}

.corp-safe {
  height: calc(120rpx + env(safe-area-inset-bottom));
}
</style>
