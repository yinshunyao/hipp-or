const STORAGE_KEY = 'app_theme_mode'

const lightColors = {
  text1: '#1C1917',
  text2: '#78716C',
  text3: '#A8A29E',
  aiText: '#44403C',
  accent: '#C47F0A',
  codeBg: 'rgba(0,0,0,0.05)',
  codeColor: '#C47F0A',
  strongColor: '#1C1917',
  linkColor: '#C47F0A',
  quoteBorder: '#C47F0A',
  quoteBg: 'rgba(196,127,10,0.06)',
  quoteText: '#78716C',
  preBg: '#F0EDE6',
  preBorder: '#E7E5E4',
  preText: '#44403C',
  thBg: 'rgba(0,0,0,0.03)',
  thText: '#1C1917',
  tdText: '#44403C',
  tableBorder: '#E7E5E4'
}

const darkColors = {
  text1: '#F0ECE2',
  text2: '#9B97A8',
  text3: '#6B6779',
  aiText: '#C8C4B8',
  accent: '#FFB020',
  codeBg: 'rgba(255,255,255,0.08)',
  codeColor: '#FFB020',
  strongColor: '#F0ECE2',
  linkColor: '#FFB020',
  quoteBorder: '#FFB020',
  quoteBg: 'rgba(255,176,32,0.06)',
  quoteText: '#9B97A8',
  preBg: '#1C1B22',
  preBorder: 'rgba(255,255,255,0.06)',
  preText: '#C8C4B8',
  thBg: 'rgba(255,255,255,0.04)',
  thText: '#F0ECE2',
  tdText: '#C8C4B8',
  tableBorder: 'rgba(255,255,255,0.08)'
}

const state = {
  mode: uni.getStorageSync(STORAGE_KEY) || 'light'
}

const mutations = {
  SET_MODE(state, mode) {
    state.mode = mode
    try { uni.setStorageSync(STORAGE_KEY, mode) } catch (e) {}
  }
}

const actions = {
  toggle({ commit, state }) {
    commit('SET_MODE', state.mode === 'dark' ? 'light' : 'dark')
  },
  setMode({ commit }, mode) {
    commit('SET_MODE', mode)
  }
}

const getters = {
  isDark: state => state.mode === 'dark',
  colors: state => state.mode === 'dark' ? darkColors : lightColors
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
