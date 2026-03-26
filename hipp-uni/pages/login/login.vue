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

      <button class="login-btn" hover-class="login-btn--hover" @click="handleLogin">
        <text class="login-btn-text">登 录</text>
      </button>
      <button class="wx-login-btn" @click="openWxAuthDialog">
        微信授权登录
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

    <view v-if="wxAuthDialogVisible" class="wx-auth-mask" @click="closeWxAuthDialog">
      <view class="wx-auth-dialog" @click.stop>
        <view class="wx-auth-title">微信授权登录</view>
        <view class="wx-auth-table">
          <view class="wx-auth-row">
            <text class="wx-auth-label">头像</text>
            <view class="wx-auth-value">
              <button class="wx-avatar-btn" open-type="chooseAvatar" @chooseavatar="onChooseAvatar">
                <image v-if="wxAuthForm.avatar" class="wx-avatar" :src="wxAuthForm.avatar" mode="aspectFill" />
                <text v-else class="wx-auth-placeholder">点击选择</text>
              </button>
            </view>
          </view>
          <view class="wx-auth-row">
            <text class="wx-auth-label">昵称</text>
            <view class="wx-auth-value">
              <input
                v-model="wxAuthForm.nickname"
                class="wx-auth-input"
                type="nickname"
                placeholder="请输入昵称"
                :placeholder-style="'color:' + tc.text3"
                maxlength="20"
              />
            </view>
          </view>
          <view class="wx-auth-row">
            <text class="wx-auth-label">手机号</text>
            <view class="wx-auth-value">
              <text :class="wxAuthForm.phone ? 'wx-auth-phone' : 'wx-auth-placeholder'">
                {{ wxAuthForm.phone || '授权前为空' }}
              </text>
            </view>
          </view>
        </view>
        <view class="wx-auth-actions">
          <button class="wx-auth-cancel" @click="closeWxAuthDialog">取消</button>
          <button
            class="wx-auth-confirm"
            open-type="getPhoneNumber"
            @getphonenumber="onWxGetPhoneNumber"
          >
            授权手机号并登录
          </button>
        </view>
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
      pwdFocus: false,
      passwordVisible: false,
      wxAuthDialogVisible: false,
      wxAuthForm: { avatar: '', nickname: '', phone: '' }
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
    togglePasswordVisible() {
      this.passwordVisible = !this.passwordVisible
    },
    openWxAuthDialog() {
      if (!this.isAgrement) {
        this.tooltipVisible = true
        return
      }
      this.wxAuthDialogVisible = true
    },
    closeWxAuthDialog() {
      this.wxAuthDialogVisible = false
    },
    onChooseAvatar(e) {
      this.wxAuthForm.avatar = (e && e.detail && e.detail.avatarUrl) || ''
    },
    async pwdLogin() {
      this.$store.dispatch('auth/Login', this.loginForm).then(() => {
        this.$modal.closeLoading(); this.loginSuccess()
      })
    },
    loginSuccess() {
      this.$tab.reLaunch(this.isResetPassword ? '/pages/requirement/index' : '/subpkg/mine/pwd/index')
    },
    onWxGetPhoneNumber(detail) {
      const profile = {
        nickname: (this.wxAuthForm.nickname || '').trim(),
        avatar: this.wxAuthForm.avatar || ''
      }
      this.onGetPhoneNumber(detail, profile).then((res) => {
        const telephone = (res && res.data && res.data.telephone) || this.$store.state.auth.telephone || ''
        this.wxAuthForm.phone = telephone
        this.closeWxAuthDialog()
        this.loginSuccess()
      })
    },
    checkboxChange() { this.isAgrement = !this.isAgrement; this.tooltipVisible = false }
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
.wx-login-btn {
  margin-top: 20rpx;
  width: 100%;
  height: $mp-auth-row-h;
  border-radius: $mp-auth-row-r;
  border: $mp-border solid var(--t-border);
  background: var(--t-surface);
  color: var(--t-text-1);
  font-size: $mp-font-input;
  /* 与主登录按钮一致：原生 button 默认 padding/line-height 会导致文字偏上 */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
  box-sizing: border-box;
}
.wx-login-btn::after { border: none; }

.wx-auth-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 36rpx;
}
.wx-auth-dialog {
  width: 100%;
  background: var(--t-surface);
  border-radius: 24rpx;
  border: $mp-border solid var(--t-border);
  padding: 28rpx;
  box-sizing: border-box;
}
.wx-auth-title {
  font-size: $mp-font-input;
  color: var(--t-text-1);
  font-weight: 700;
  text-align: center;
  margin-bottom: 20rpx;
}
.wx-auth-table {
  border: $mp-border solid var(--t-border);
  border-radius: 16rpx;
  overflow: hidden;
}
.wx-auth-row {
  min-height: 86rpx;
  display: flex;
  align-items: center;
  border-bottom: $mp-border solid var(--t-border);
  padding: 0 18rpx;
}
.wx-auth-row:last-child { border-bottom: none; }
.wx-auth-label {
  width: 140rpx;
  color: var(--t-text-2);
  font-size: $mp-font-meta;
}
.wx-auth-value {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}
.wx-auth-placeholder {
  color: var(--t-text-3);
  font-size: $mp-font-meta;
}
.wx-avatar-btn {
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  line-height: 1;
}
.wx-avatar-btn::after { border: none; }
.wx-avatar {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
}
.wx-auth-input {
  width: 260rpx;
  text-align: right;
  color: var(--t-text-1);
  font-size: $mp-font-meta;
}
.wx-auth-phone {
  color: var(--t-text-1);
  font-size: $mp-font-meta;
}
.wx-auth-actions {
  margin-top: 20rpx;
  display: flex;
  gap: 12rpx;
}
.wx-auth-cancel,
.wx-auth-confirm {
  flex: 1;
  height: 78rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $mp-font-meta;
  padding: 0;
}
.wx-auth-cancel {
  background: var(--t-root);
  color: var(--t-text-2);
  border: $mp-border solid var(--t-border);
}
.wx-auth-confirm {
  background: linear-gradient(135deg, var(--t-accent-from), var(--t-accent-to));
  color: var(--t-accent-text);
  border: none;
}
.wx-auth-cancel::after,
.wx-auth-confirm::after { border: none; }

.agree-row { display: flex; align-items: flex-start; margin-top: $mp-auth-agree-mt; }
.agree-text { flex: 1; font-size: $mp-font-legal; line-height: $mp-lh-legal; }
.agree-grey { color: var(--t-text-3); }
.agree-link { color: var(--t-accent); }
</style>
