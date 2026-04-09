<template>
  <view class="page-with-nav">
    <uni-nav-bar
      title="登录"
      fixed
      status-bar
      :border="false"
      background-color="#FFFFFF"
      color="#1F1F1F"
    />
    <view :class="themeClass" class="login-root page-with-nav__body">
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
      <view class="login-mode-row">
        <view
          class="login-mode-item"
          :class="{ 'login-mode-item--active': loginMode === 'sms' }"
          @click="setLoginMode('sms')"
        >
          短信登录
        </view>
        <view
          class="login-mode-item"
          :class="{ 'login-mode-item--active': loginMode === 'password' }"
          @click="setLoginMode('password')"
        >
          账号密码
        </view>
      </view>

      <view class="field" :class="{ 'field--focus': phoneFocus }">
        <view class="iconfont icon-user field-icon"></view>
        <input
          v-model="loginForm.telephone"
          class="field-input"
          type="number"
          :placeholder="loginMode === 'sms' ? '手机号' : '手机号或账号'"
          :placeholder-style="'color:' + tc.text3"
          maxlength="11"
          @focus="phoneFocus = true"
          @blur="phoneFocus = false"
        />
      </view>

      <template v-if="loginMode === 'sms'">
        <view class="field" :class="{ 'field--focus': codeFocus }">
          <view class="iconfont icon-password field-icon"></view>
          <input
            v-model="smsCode"
            class="field-input"
            type="number"
            placeholder="验证码"
            :placeholder-style="'color:' + tc.text3"
            maxlength="8"
            @focus="codeFocus = true"
            @blur="codeFocus = false"
          />
          <view
            class="field-suffix field-suffix--btn"
            :class="{ 'field-suffix--disabled': smsCooldown > 0 }"
            @click="sendSmsCode"
          >
            {{ smsCooldown > 0 ? `${smsCooldown}s` : '获取验证码' }}
          </view>
        </view>
      </template>

      <template v-else>
        <view class="field" :class="{ 'field--focus': pwdFocus }">
          <view class="iconfont icon-password field-icon"></view>
          <input
            v-model="loginForm.password"
            :password="!passwordVisible"
            class="field-input"
            placeholder="密码"
            :placeholder-style="'color:' + tc.text3"
            maxlength="20"
            @focus="pwdFocus = true"
            @blur="pwdFocus = false"
          />
          <view class="field-suffix" @click="togglePasswordVisible">
            {{ passwordVisible ? '隐藏' : '显示' }}
          </view>
        </view>
      </template>

      <button class="login-btn" hover-class="login-btn--hover" @click="handleLogin">
        <text class="login-btn-text">登 录</text>
      </button>
      <view class="home-entry" @click="goHome">返回首页</view>

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
  </view>
</template>

<script>
import { themeMixin } from '@/common/mixins/theme.js'
import { sendLoginSms } from '@/common/request/api/login.js'

export default {
  mixins: [themeMixin],
  data() {
    return {
      loginMode: 'sms',
      loginForm: { telephone: '', password: '' },
      smsCode: '',
      smsCooldown: 0,
      smsTimer: null,
      isAgrement: false,
      tooltipVisible: false,
      phoneFocus: false,
      pwdFocus: false,
      codeFocus: false,
      passwordVisible: false
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
  beforeDestroy() {
    if (this.smsTimer) {
      clearInterval(this.smsTimer)
      this.smsTimer = null
    }
  },
  methods: {
    setLoginMode(mode) {
      this.loginMode = mode
    },
    handlePrivacy() {
      this.$tab.navigateTo(`/subpkg/common/webview/index?title=隐私政策&url=${this.privacy}`)
    },
    handleUserAgrement() {
      this.$tab.navigateTo(`/subpkg/common/webview/index?title=用户协议&url=${this.agreement}`)
    },
    sendSmsCode() {
      if (!this.isAgrement) {
        this.tooltipVisible = true
        return
      }
      if (this.smsCooldown > 0) return
      const phone = (this.loginForm.telephone || '').trim()
      if (!phone) {
        this.$modal.msgError('请输入手机号')
        return
      }
      if (phone.length !== 11) {
        this.$modal.msgError('请输入正确手机号')
        return
      }
      this.smsCode = ''
      this.$modal.loading('发送中...')
      sendLoginSms(phone)
        .then(() => {
          this.$modal.closeLoading()
          this.$modal.msgSuccess('验证码已发送')
          this.smsCooldown = 60
          if (this.smsTimer) clearInterval(this.smsTimer)
          this.smsTimer = setInterval(() => {
            this.smsCooldown -= 1
            if (this.smsCooldown <= 0) {
              clearInterval(this.smsTimer)
              this.smsTimer = null
            }
          }, 1000)
        })
        .catch(() => {
          this.$modal.closeLoading()
        })
    },
    async handleLogin() {
      if (!this.isAgrement) {
        this.tooltipVisible = true
        return
      }
      if (this.loginMode === 'sms') {
        const phone = (this.loginForm.telephone || '').trim()
        const code = (this.smsCode || '').trim()
        if (!phone) this.$modal.msgError('请输入手机号')
        else if (!code) this.$modal.msgError('请输入验证码')
        else {
          this.$modal.loading('正在登录中...')
          this.$store.dispatch('auth/SmsLogin', { telephone: phone, code }).then(() => {
            this.$modal.closeLoading()
            this.loginSuccess()
          }).catch(() => {
            this.$modal.closeLoading()
          })
        }
      } else if (!this.loginForm.telephone) {
        this.$modal.msgError('请输入您的手机号或账号')
      } else if (!this.loginForm.password) {
        this.$modal.msgError('请输入您的密码')
      } else {
        this.$modal.loading('正在登录中...')
        this.pwdLogin()
      }
    },
    togglePasswordVisible() {
      this.passwordVisible = !this.passwordVisible
    },
    pwdLogin() {
      this.$store.dispatch('auth/Login', this.loginForm).then(() => {
        this.$modal.closeLoading()
        this.loginSuccess()
      }).catch(() => {
        this.$modal.closeLoading()
      })
    },
    loginSuccess() {
      this.$tab.reLaunch(this.isResetPassword ? '/pages/home/index' : '/subpkg/mine/pwd/index')
    },
    checkboxChange() { this.isAgrement = !this.isAgrement; this.tooltipVisible = false },
    goHome() {
      uni.switchTab({ url: '/pages/home/index' })
    }
  }
}
</script>

<style lang="scss">
@import '@/uni.scss';

page { background-color: var(--t-root, #{$t-page-root}); }

.login-root {
  width: 100%; min-height: 100vh; position: relative;
  background: var(--t-root); overflow: hidden;
}
.login-root.page-with-nav__body {
  flex: 1;
  min-height: 0;
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
  width: $mp-auth-logo; height: $mp-auth-logo; border-radius: $mp-auth-logo-r;
  background: linear-gradient(145deg, var(--t-ring-from), var(--t-ring-to));
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--t-shadow-drop), 0 0 #{$mp-auth-logo-halo} var(--t-ring-shadow-glow), inset 0 1rpx 0 var(--t-logo-inset);
  border: 1rpx solid var(--t-ring-border);
}
.logo-img {
  width: $mp-auth-logo-img; height: $mp-auth-logo-img; border-radius: $mp-radius-bubble;
}
.brand-name {
  margin-top: $mp-auth-brand-mt; font-size: $mp-font-brand; font-weight: 700;
  color: var(--t-text-1); letter-spacing: $mp-auth-brand-track;
}
.brand-sub {
  margin-top: $mp-auth-sub-mt; font-size: $mp-font-meta;
  color: var(--t-text-3); letter-spacing: $mp-auth-sub-track;
}
.form-card { margin: $mp-auth-form-mt $mp-auth-form-mx 0; position: relative; z-index: 1; }

.login-mode-row {
  display: flex;
  margin-bottom: $mp-auth-row-mb;
  border-radius: $mp-auth-row-r;
  background: var(--t-surface);
  border: $mp-border solid var(--t-border);
  overflow: hidden;
}
.login-mode-item {
  flex: 1;
  text-align: center;
  padding: 22rpx 0;
  font-size: $mp-font-meta;
  color: var(--t-text-3);
}
.login-mode-item--active {
  color: var(--t-accent);
  font-weight: 700;
  background: var(--t-accent-bg);
}

.field {
  display: flex; align-items: center; height: $mp-auth-row-h; margin-bottom: $mp-auth-row-mb;
  background: var(--t-surface); border-radius: $mp-auth-row-r;
  border: $mp-border solid var(--t-border); padding: 0 $mp-auth-row-px;
  box-sizing: border-box; transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.field--focus {
  border-color: var(--t-border-focus);
  box-shadow: 0 0 #{$mp-auth-field-focus-blur} var(--t-accent-bg);
}
.field-icon {
  font-size: $mp-hit-fab-icon; color: var(--t-text-3); margin-right: $mp-auth-icon-mr;
  transition: color 0.25s ease;
}
.field--focus .field-icon { color: var(--t-accent); }
.field-input {
  flex: 1; width: 100%; height: 100%; font-size: $mp-font-input;
  color: var(--t-text-1); background: transparent;
}
.field-suffix {
  font-size: $mp-font-meta;
  color: var(--t-accent);
  padding-left: 16rpx;
  flex-shrink: 0;
}
.field-suffix--btn {
  min-width: 160rpx;
  text-align: right;
}
.field-suffix--disabled {
  color: var(--t-text-3);
  pointer-events: none;
}
.login-btn {
  margin-top: $mp-auth-btn-mt; width: 100%; height: $mp-auth-row-h; border-radius: $mp-auth-row-r;
  background: linear-gradient(135deg, var(--t-accent-from), var(--t-accent-to));
  display: flex; align-items: center; justify-content: center; border: none;
  box-shadow: 0 $mp-auth-btn-shadow-y $mp-auth-btn-shadow-blur var(--t-accent-shadow);
  transition: opacity 0.2s ease, transform 0.15s ease;
}
.login-btn::after { border: none; }
.login-btn--hover { opacity: 0.88; transform: scale(0.98); }
.login-btn-text {
  font-size: $mp-font-cta; font-weight: 700; color: var(--t-accent-text);
  letter-spacing: $mp-auth-btn-track;
}

.home-entry {
  margin-top: 28rpx;
  text-align: center;
  font-size: 28rpx;
  color: var(--t-accent);
  padding: 12rpx 0;
}

.agree-row { display: flex; align-items: flex-start; margin-top: $mp-auth-agree-mt; }
.agree-text { flex: 1; font-size: $mp-font-legal; line-height: $mp-lh-legal; }
.agree-grey { color: var(--t-text-3); }
.agree-link { color: var(--t-accent); }
</style>
