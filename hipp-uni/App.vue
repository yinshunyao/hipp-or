<script>
export default {
  onLaunch: function () {
    this.initApp()
  },
  methods: {
    initApp() {
      this.$store.dispatch('app/InitConfig')
      // 尽早换取游客 token，避免首屏切到「需求/商业」时 scene-agent 先于路由守卫完成而无 Authorization
      // #ifdef MP-WEIXIN
      this.$store.dispatch('auth/EnsureGuestToken').catch(() => {})
      // #endif
    }
  }
}
</script>

<style lang="scss">
@import '@/static/scss/theme-css-vars.scss';
@import '@/static/scss/index.scss';

/* uView component overrides */
.u-button--primary {
  background: linear-gradient(135deg, var(--t-accent-from), var(--t-accent-to)) !important;
  border-color: var(--t-accent) !important;
  color: var(--t-accent-text) !important;
}

.u-form-item__body__left__content__label {
  color: var(--t-text-2) !important;
}

.u-input__content__field-wrapper__field {
  color: var(--t-text-1) !important;
}

.u-line {
  border-color: var(--t-border) !important;
}

.u-checkbox__icon-wrap--checked {
  background-color: var(--t-accent) !important;
  border-color: var(--t-accent) !important;
}
</style>
