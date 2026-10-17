import { defineStore } from 'pinia'

const KEY = 'hipp_web_theme'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: localStorage.getItem(KEY) === 'dark' ? 'dark' : 'light'
  }),
  getters: {
    isDark: (s) => s.mode === 'dark'
  },
  actions: {
    apply() {
      document.documentElement.dataset.theme = this.mode
    },
    toggle() {
      this.mode = this.mode === 'dark' ? 'light' : 'dark'
      localStorage.setItem(KEY, this.mode)
      this.apply()
    }
  }
})
