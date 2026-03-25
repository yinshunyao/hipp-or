<template>
  <view :class="themeClass" class="login-root">
    <view class="login-ambient"></view>
    <view class="login-glow"></view>

    <view class="logo-area">
      <view class="logo-ring">
        <image v-if="logo" class="logo-img" :src="logoImage" mode="aspectFill" />
      </view>
      <text class="brand-name">{{ title }}</text>
      <text class="brand-sub">智能需求分析平台</text>
    </view>

    <view class="form-card">
      <view class="field" :class="{ 'field--focus': phoneFocus }">
        <view class="iconfont icon-user field-icon"></view>
        <input
          v-model="loginForm.telephone"
          class="field-input"
          type="text"
          placeholder="手机号或账号"
          :placeholder-style="'color:' + tc.text3"
          maxlength="50"
          @focus="phoneFocus = true"
          @blur="phoneFocus = false"
        />
      </view>
      <view class="field" :class="{ 'field--focus': pwdFocus }">
        <view class="iconfont icon-password field-icon"></view>
        <input
          v-model="loginForm.password"
          type="password"
          class="field-input"
          placeholder="密码"
          :placeholder-style="'color:' + tc.text3"
          maxlength="20"
          @focus="pwdFocus = true"
          @blur="pwdFocus = false"
        />
      </view>

      <button class="login-btn" hover-class="login-btn--hover" @click="handleLogin">
        <text class="login-btn-text">登 录</text>
      </button>

      <view class="agree-row">
        <zb-tooltip :visible.sync="tooltipVisible" content="请阅读并同意" placement="top" ref="tooltip">
          <view>
            <u-checkbox-group v-model="isAgrement" shape="circle" @change="checkboxChange" :active-color="tc.accent">
              <u-checkbox></u-checkbox>
            </u-checkbox-group>
          </view>
        </zb-tooltip>
        <view class="agree-text">
          <text class="agree-grey">允许我们在必要场景下，合理使用您的个人信息，且阅读并同意</text>
          <text class="agree-link" @click="handleUserAgrement">《用户协议》、</text>
          <text class="agree-link" @click="handlePrivacy">《隐私协议》、</text>
          <text class="agree-grey">等内容</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { wxLoginMixins } from '@/common/mixins/auth.js'
import { themeMixin } from '@/common/mixins/theme.js'

export default {
  mixins: [wxLoginMixins, themeMixin],
  data() {
    return {
      loginForm: { telephone: '', password: '' },
      isAgrement: false,
      tooltipVisible: false,
      phoneFocus: false,
      pwdFocus: false
    }
  },
  computed: {
    title() { return this.$store.state.app.title },
    logo() { return this.$store.state.app.logo },
    logoImage() { return this.$store.state.app.logoImage },
    privacy() { return this.$store.state.app.privacy },
    agreement() { return this.$store.state.app.agreement },
    isResetPassword() { return this.$store.state.auth.isResetPassword }
  },
  methods: {
    handlePrivacy() {
      this.$tab.navigateTo(`/subpkg/common/webview/index?title=隐私政策&url=${this.privacy}`)
    },
    handleUserAgrement() {
      this.$tab.navigateTo(`/subpkg/common/webview/index?title=用户协议&url=${this.agreement}`)
    },
    async handleLogin() {
      if (this.isAgrement) {
        if (!this.loginForm.telephone) this.$modal.msgError('请输入您的手机号')
        else if (!this.loginForm.password) this.$modal.msgError('请输入您的密码')
        else { this.$modal.loading('正在登录中...'); this.pwdLogin() }
      } else { this.tooltipVisible = true }
    },
    async pwdLogin() {
      this.$store.dispatch('auth/Login', this.loginForm).then(() => {
        this.$modal.closeLoading(); this.loginSuccess()
      })
    },
    loginSuccess() {
      this.$tab.reLaunch(this.isResetPassword ? '/pages/requirement/index' : '/subpkg/mine/pwd/index')
    },
    wxLogin(detail) {
      if (this.isAgrement) { this.onGetPhoneNumber(detail).then(() => this.loginSuccess()) }
      else { this.tooltipVisible = true }
    },
    checkboxChange() { this.isAgrement = !this.isAgrement; this.tooltipVisible = false }
  }
}
</script>

<style lang="scss">
page { background-color: var(--t-root, #F5F3EE); }

.login-root {
  width: 100%; min-height: 100vh; position: relative;
  background: var(--t-root); overflow: hidden;
}
.login-ambient {
  position: absolute; top: -30%; left: -20%; width: 140%; height: 70%;
  background: radial-gradient(ellipse at 50% 40%, var(--t-login-ambient) 0%, transparent 70%);
  pointer-events: none;
}
.login-glow {
  position: absolute; bottom: 10%; right: -30%; width: 80%; height: 50%;
  background: radial-gradient(ellipse at center, var(--t-login-glow) 0%, transparent 70%);
  pointer-events: none;
}
.logo-area {
  display: flex; flex-direction: column; align-items: center;
  padding-top: 18%; position: relative; z-index: 1;
}
.logo-ring {
  width: 140rpx; height: 140rpx; border-radius: 36rpx;
  background: linear-gradient(145deg, var(--t-ring-from), var(--t-ring-to));
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.12), 0 0 60rpx var(--t-ring-shadow-glow), inset 0 1rpx 0 var(--t-logo-inset);
  border: 1rpx solid var(--t-ring-border);
}
.logo-img { width: 100rpx; height: 100rpx; border-radius: 20rpx; }
.brand-name {
  margin-top: 28rpx; font-size: 44rpx; font-weight: 700;
  color: var(--t-text-1); letter-spacing: 4rpx;
}
.brand-sub {
  margin-top: 10rpx; font-size: 24rpx; color: var(--t-text-3); letter-spacing: 2rpx;
}
.form-card { margin: 10% 44rpx 0; position: relative; z-index: 1; }
.field {
  display: flex; align-items: center; height: 104rpx; margin-bottom: 24rpx;
  background: var(--t-surface); border-radius: 52rpx;
  border: 2rpx solid var(--t-border); padding: 0 32rpx;
  box-sizing: border-box; transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.field--focus {
  border-color: var(--t-border-focus);
  box-shadow: 0 0 24rpx var(--t-accent-bg);
}
.field-icon {
  font-size: 36rpx; color: var(--t-text-3); margin-right: 16rpx;
  transition: color 0.25s ease;
}
.field--focus .field-icon { color: var(--t-accent); }
.field-input {
  flex: 1; width: 100%; height: 100%; font-size: 30rpx;
  color: var(--t-text-1); background: transparent;
}
.login-btn {
  margin-top: 40rpx; width: 100%; height: 104rpx; border-radius: 52rpx;
  background: linear-gradient(135deg, var(--t-accent-from), var(--t-accent-to));
  display: flex; align-items: center; justify-content: center; border: none;
  box-shadow: 0 8rpx 32rpx var(--t-accent-shadow);
  transition: opacity 0.2s ease, transform 0.15s ease;
}
.login-btn::after { border: none; }
.login-btn--hover { opacity: 0.88; transform: scale(0.98); }
.login-btn-text {
  font-size: 34rpx; font-weight: 700; color: var(--t-accent-text); letter-spacing: 8rpx;
}
.agree-row { display: flex; align-items: flex-start; margin-top: 36rpx; }
.agree-text { flex: 1; font-size: 22rpx; line-height: 34rpx; }
.agree-grey { color: var(--t-text-3); }
.agree-link { color: var(--t-accent); }
</style>
