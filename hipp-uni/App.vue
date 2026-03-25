<script>
export default {
  onLaunch: function () {
    this.initApp()
  },
  methods: {
    initApp() {
      this.$store.dispatch('app/InitConfig')
    }
  }
}
</script>

<style lang="scss">
@import '@/static/scss/index.scss';

/* ═══ Luminous Paper (Light) ═══ */
.theme-light {
  --t-root: #F5F3EE;
  --t-surface: #FFFFFF;
  --t-elevated: #EBE8E1;
  --t-hover: #E5E2DB;
  --t-accent: #C47F0A;
  --t-accent-from: #E89E10;
  --t-accent-to: #C47F0A;
  --t-accent-bg: rgba(196, 127, 10, 0.07);
  --t-accent-text: #FFFFFF;
  --t-accent-shadow: rgba(196, 127, 10, 0.18);
  --t-success: #0E9F94;
  --t-error: #DC4444;
  --t-error-bg: rgba(220, 68, 68, 0.06);
  --t-error-border: rgba(220, 68, 68, 0.12);
  --t-text-1: #1C1917;
  --t-text-2: #78716C;
  --t-text-3: #A8A29E;
  --t-text-4: #D6D3D1;
  --t-border: #E7E5E4;
  --t-border-focus: rgba(196, 127, 10, 0.35);
  --t-divider: #F0EDE6;
  --t-shadow: 0 2rpx 16rpx rgba(0, 0, 0, 0.06);
  --t-shadow-heavy: 0 4rpx 24rpx rgba(0, 0, 0, 0.08);
  --t-pin-color: #C47F0A;
  --t-pin-bg: rgba(196, 127, 10, 0.08);
  --t-state-color: #DC4444;
  --t-state-bg: rgba(220, 68, 68, 0.06);
  --t-end-color: #78716C;
  --t-end-bg: rgba(0, 0, 0, 0.04);
  --t-login-ambient: rgba(196, 127, 10, 0.06);
  --t-login-glow: rgba(14, 159, 148, 0.03);
  --t-ring-from: #F0EDE6;
  --t-ring-to: #FFFFFF;
  --t-ring-border: rgba(196, 127, 10, 0.15);
  --t-ring-shadow-glow: rgba(196, 127, 10, 0.04);
  --t-logo-inset: rgba(0, 0, 0, 0.02);
}

/* ═══ Luminous Ink (Dark) ═══ */
.theme-dark {
  --t-root: #131218;
  --t-surface: #1C1B22;
  --t-elevated: #252430;
  --t-hover: #2A2938;
  --t-accent: #FFB020;
  --t-accent-from: #FFB020;
  --t-accent-to: #E89E10;
  --t-accent-bg: rgba(255, 176, 32, 0.10);
  --t-accent-text: #131218;
  --t-accent-shadow: rgba(255, 176, 32, 0.25);
  --t-success: #4ECDC4;
  --t-error: #FF6B6B;
  --t-error-bg: rgba(255, 107, 107, 0.08);
  --t-error-border: rgba(255, 107, 107, 0.18);
  --t-text-1: #F0ECE2;
  --t-text-2: #9B97A8;
  --t-text-3: #6B6779;
  --t-text-4: #4A475A;
  --t-border: rgba(255, 255, 255, 0.06);
  --t-border-focus: rgba(255, 176, 32, 0.35);
  --t-divider: rgba(255, 255, 255, 0.04);
  --t-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.3);
  --t-shadow-heavy: 0 4rpx 32rpx rgba(0, 0, 0, 0.4);
  --t-pin-color: #FFB020;
  --t-pin-bg: rgba(255, 176, 32, 0.12);
  --t-state-color: #FF6B6B;
  --t-state-bg: rgba(255, 107, 107, 0.12);
  --t-end-color: #6B6779;
  --t-end-bg: rgba(255, 255, 255, 0.06);
  --t-login-ambient: rgba(255, 176, 32, 0.08);
  --t-login-glow: rgba(78, 205, 196, 0.04);
  --t-ring-from: #252430;
  --t-ring-to: #1C1B22;
  --t-ring-border: rgba(255, 176, 32, 0.12);
  --t-ring-shadow-glow: rgba(255, 176, 32, 0.06);
  --t-logo-inset: rgba(255, 255, 255, 0.06);
}

page {
  background-color: #F5F3EE;
  color: #1C1917;
}

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
