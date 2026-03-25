<template>
  <view :class="themeClass" class="container">
    <view class="form-wrap">
      <u--form ref="formRef" label-position="left" label-width="100px" :model="form" :rules="rules">
        <u-form-item label="用户姓名" prop="name" border-bottom :required="true">
          <u--input v-model="form.name" placeholder="请输入用户姓名" border="none" :custom-style="inputStyle"></u--input>
        </u-form-item>
        <u-form-item label="用户昵称" prop="nickname" border-bottom :required="false">
          <u--input v-model="form.nickname" placeholder="请输入用户昵称" border="none" :custom-style="inputStyle"></u--input>
        </u-form-item>
        <u-form-item label="手机号码" prop="telephone" border-bottom :required="true">
          <u--input v-model="form.telephone" placeholder="请输入手机号码" border="none" :custom-style="inputStyle"></u--input>
        </u-form-item>
        <u-form-item label="用户性别" prop="gender" border-bottom :required="false">
          <u-radio-group v-model="form.gender">
            <u-radio v-for="(item, index) in genderOptions" :key="index" :custom-style="{ marginRight: '16px' }" :label="item.label" :name="item.value" :active-color="tc.accent" />
          </u-radio-group>
        </u-form-item>
      </u--form>
      <view class="btn-wrap">
        <button class="submit-btn" :loading="btnLoading" hover-class="submit-btn--hover" @click="submit">
          <text class="submit-text">提交</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script>
import { getInfo } from '@/common/request/api/login'
import { updateCurrentUser } from '@/common/request/api/vadmin/auth/user.js'
import { themeMixin } from '@/common/mixins/theme.js'

export default {
  mixins: [themeMixin],
  data() {
    return {
      btnLoading: false,
      form: { name: '', nickname: '', telephone: '', gender: '' },
      rules: {
        name: { type: 'string', required: true, message: '请填写姓名', trigger: ['blur', 'change'] },
        telephone: [
          { type: 'string', required: true, message: '请填写正确手机号', trigger: ['blur', 'change'] },
          { validator: (rule, value, callback) => /^1\d{10}$/.test(String(value || '')), message: '手机号码不正确', trigger: ['change', 'blur'] }
        ]
      },
      genderOptions: []
    }
  },
  computed: {
    inputStyle() { return { color: this.tc.text1 } }
  },
  onLoad() {
    this.$store.dispatch('dict/getDicts', ['sys_vadmin_gender']).then((result) => { this.genderOptions = result.sys_vadmin_gender })
    this.getUser()
  },
  onReady() { this.$refs.formRef.setRules(this.rules) },
  methods: {
    getUser() {
      this.$modal.loading('加载中')
      getInfo().then((res) => { this.form = res.data }).finally(() => { this.$modal.closeLoading() })
    },
    submit() {
      this.$refs.formRef.validate().then(() => {
        this.btnLoading = true
        updateCurrentUser(this.form).then((res) => { this.$store.dispatch('auth/UpdateInfo', res.data); this.$modal.msgSuccess('更新成功') }).finally(() => { this.btnLoading = false })
      })
    }
  }
}
</script>

<style lang="scss">
page { background-color: var(--t-root, #F5F3EE); }
.container { min-height: 100vh; background: var(--t-root); }
.form-wrap { padding: 20px; }
.btn-wrap { margin-top: 40rpx; }
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
