export const themeMixin = {
  computed: {
    themeMode() {
      return this.$store.state.theme.mode
    },
    themeClass() {
      return this.$store.state.theme.mode === 'dark' ? 'theme-dark' : 'theme-light'
    },
    tc() {
      return this.$store.getters['theme/colors']
    }
  },
  onShow() {
    this._applySystemTheme(this.themeMode)
  },
  watch: {
    themeMode(mode) {
      this._applySystemTheme(mode)
    }
  },
  methods: {
    _applySystemTheme(mode) {
      const isDark = mode === 'dark'
      try {
        uni.setNavigationBarColor({
          frontColor: isDark ? '#ffffff' : '#000000',
          backgroundColor: isDark ? '#1C1B22' : '#FFFFFF',
          animation: { duration: 200, timingFunc: 'easeIn' }
        })
      } catch (e) {}
      try {
        uni.setTabBarStyle({
          color: isDark ? '#6B6779' : '#A8A29E',
          selectedColor: isDark ? '#FFB020' : '#C47F0A',
          backgroundColor: isDark ? '#1C1B22' : '#FFFFFF',
          borderStyle: isDark ? 'black' : 'white'
        })
      } catch (e) {}
    }
  }
}
