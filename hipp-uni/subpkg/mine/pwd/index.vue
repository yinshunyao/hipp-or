<template>
  <view :class="themeClass" class="page-with-nav">
    <uni-nav-bar
      title="修改密码"
      fixed
      status-bar
      :border="false"
      :background-color="'var(--t-nav-bg)'"
      :color="'var(--t-nav-text)'"
      left-icon="left"
      @clickLeft="navBack"
    />
    <view class="pwd-container page-with-nav__body">
    <view class="form-wrap">
      <u--form ref="formRef" label-position="left" label-width="90px" :model="form" :rules="rules">
        <u-form-item prop="old_password" label="当前密码" border-bottom required>
          <u--input v-model="form.old_password" type="password" placeholder="请输入当前密码" border="none" :custom-style="inputStyle"></u--input>
        </u-form-item>
        <u-form-item prop="password" label="新密码" border-bottom required>
          <u--input v-model="form.password" type="password" placeholder="请输入新密码" border="none" :custom-style="inputStyle"></u--input>
        </u-form-item>
        <u-form-item prop="password_two" label="确认密码" border-bottom required>
          <u--input v-model="form.password_two" type="password" placeholder="请确认新密码" border="none" :custom-style="inputStyle"></u--input>
        </u-form-item>
      </u--form>
      <view class="btn-wrap">
        <button class="submit-btn" hover-class="submit-btn--hover" @click="submit">
          <text class="submit-text">提交</text>
        </button>
      </view>
    </view>
    </view>
  </view>
</template>

<script>
import { postCurrentUserResetPassword } from '@/common/request/api/vadmin/auth/user.js'
import { themeMixin } from '@/common/mixins/theme.js'
import navBackMixin from '@/common/mixins/nav-back.js'

export default {
  mixins: [themeMixin, navBackMixin],
  data() {
    return {
      form: { old_password: undefined, password: undefined, password_two: undefined },
      rules: {
        old_password: [
          { type: 'string', required: true, message: '当前密码不能为空', trigger: ['blur', 'change'] }
        ],
        password: [
          { type: 'string', required: true, message: '新密码不能为空', trigger: ['blur', 'change'] },
          { validator: (rule, value) => { const len = String(value || '').length; return len >= 8 && len <= 20 }, message: '长度在 8 到 20 个字符', trigger: ['blur', 'change'] }
        ],
        password_two: [
          { type: 'string', required: true, message: '确认密码不能为空', trigger: ['blur', 'change'] },
          { validator: (rule, value) => this.form.password === value, message: '两次输入的密码不一致', trigger: ['blur', 'change'] }
        ]
      }
    }
  },
  computed: {
    inputStyle() { return { color: this.tc.text1 } }
  },
  onReady() { this.$refs.formRef.setRules(this.rules) },
  methods: {
    submit() {
      this.$refs.formRef.validate().then(() => {
        this.$modal.loading('正在提交')
        postCurrentUserResetPassword(this.form).then(() => { this.form = { old_password: '', password: '', password_two: '' }; this.$modal.msgSuccess('修改成功') }).finally(() => { this.$modal.closeLoading() })
      })
    }
  }
}
</script>

<style lang="scss">
page { background-color: var(--t-root, #F5F3EE); }
.pwd-container { min-height: 100vh; background: var(--t-root); }
.form-wrap { padding: 36rpx 30rpx; }
.btn-wrap { margin-top: 48rpx; }
.submit-btn {
  width: 100%; height: 96rpx; border-radius: 48rpx;
  background: linear-gradient(135deg, var(--t-accent-from), var(--t-accent-to));
  display: flex; align-items: center; justify-content: center; border: none;
  box-shadow: 0 6rpx 24rpx var(--t-accent-shadow);
}
.submit-btn::after { border: none; }
.submit-btn--hover { opacity: 0.88; }
.submit-text { font-size: 32rpx; font-weight: 600; color: var(--t-accent-text); }
</style>
