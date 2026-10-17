<template>
  <view :class="themeClass" class="page-with-nav">
    <uni-nav-bar
      :title="pageTitle"
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
      <u--form ref="formRef" label-position="left" label-width="90px" :model="form" :rules="formRules">
        <u-form-item v-if="!mustSetPasswordWithoutOld" prop="old_password" label="当前密码" border-bottom required>
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
import { mapState } from 'vuex'
import { postCurrentUserResetPassword } from '@/common/request/api/vadmin/auth/user.js'
import { themeMixin } from '@/common/mixins/theme.js'
import navBackMixin from '@/common/mixins/nav-back.js'

export default {
  mixins: [themeMixin, navBackMixin],
  data() {
    return {
      form: { old_password: '', password: '', password_two: '' }
    }
  },
  computed: {
    ...mapState({
      mustSetPasswordWithoutOld: (state) => state.auth.mustSetPasswordWithoutOld
    }),
    pageTitle() {
      return this.mustSetPasswordWithoutOld ? '设置密码' : '修改密码'
    },
    inputStyle() {
      return { color: this.tc.text1 }
    },
    formRules() {
      const pwdRules = [
        { type: 'string', required: true, message: '新密码不能为空', trigger: ['blur', 'change'] },
        { validator: (rule, value) => { const len = String(value || '').length; return len >= 8 && len <= 20 }, message: '长度在 8 到 20 个字符', trigger: ['blur', 'change'] }
      ]
      const twoRules = [
        { type: 'string', required: true, message: '确认密码不能为空', trigger: ['blur', 'change'] },
        { validator: (rule, value) => this.form.password === value, message: '两次输入的密码不一致', trigger: ['blur', 'change'] }
      ]
      if (this.mustSetPasswordWithoutOld) {
        return {
          password: pwdRules,
          password_two: twoRules
        }
      }
      return {
        old_password: [
          { type: 'string', required: true, message: '当前密码不能为空', trigger: ['blur', 'change'] }
        ],
        password: pwdRules,
        password_two: twoRules
      }
    }
  },
  watch: {
    mustSetPasswordWithoutOld() {
      this.$nextTick(() => {
        if (this.$refs.formRef) this.$refs.formRef.setRules(this.formRules)
      })
    }
  },
  onReady() {
    this.$refs.formRef.setRules(this.formRules)
  },
  methods: {
    submit() {
      this.$refs.formRef.validate().then(() => {
        this.$modal.loading('正在提交')
        const payload = { password: this.form.password, password_two: this.form.password_two }
        if (!this.mustSetPasswordWithoutOld) {
          payload.old_password = this.form.old_password
        }
        const newPwd = this.form.password
        const finishOk = () => {
          this.form = { old_password: '', password: '', password_two: '' }
          this.$modal.msgSuccess('修改成功')
          uni.switchTab({ url: '/pages/home/index' })
        }
        postCurrentUserResetPassword(payload)
          .then(() => {
            this.$store.commit('auth/SET_MUST_SET_PASSWORD_WITHOUT_OLD', false)
            const phone = (this.$store.state.auth.telephone || '').trim()
            if (!phone) {
              this.$modal.msgError('无法获取手机号，请退出后重新登录')
              return
            }
            return this.$store
              .dispatch('auth/Login', { telephone: phone, password: newPwd })
              .then(() => {
                finishOk()
              })
              .catch(() => {
                this.$modal.msgError('密码已更新，请返回登录页用新密码重新登录')
              })
          })
          .finally(() => {
            this.$modal.closeLoading()
          })
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
