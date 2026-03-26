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
    _syncCustomTabBarTheme(mode) {
      const isDark = mode === 'dark'
      const patch = {
        tabBarThemeClass: isDark ? 'custom-vant-tabbar--dark' : 'custom-vant-tabbar--light',
        activeColor: isDark ? '#FFB020' : '#183B63',
        inactiveColor: isDark ? '#9B97A8' : '#8C95A3',
        tabBarBg: isDark ? '#1C1B22' : '#FFFFFF',
        tabBarBorderColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(24, 59, 99, 0.08)'
      }
      try {
        const page = this.$scope
        if (page && typeof page.getTabBar === 'function') {
          const tabBar = page.getTabBar()
          if (tabBar) {
            if (typeof tabBar.syncThemeMode === 'function') tabBar.syncThemeMode()
            else if (typeof tabBar.setData === 'function') tabBar.setData(patch)
          }
        }
      } catch (e) {}
    },
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
          color: isDark ? '#6B6779' : '#6B6B6B',
          selectedColor: isDark ? '#FFB020' : '#B46B00',
          backgroundColor: isDark ? '#1C1B22' : '#FFFFFF',
          borderStyle: isDark ? 'black' : 'white'
        })
      } catch (e) {}
      this._syncCustomTabBarTheme(mode)
    }
  }
}
