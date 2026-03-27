/**
 * 自定义 tabBar 会随 tab 页重建，data 会回到初始值，需按栈同步 activePath。
 * switchTab 后页面栈更新晚于 nextTick，需多次短间隔重试同步 activePath。
 * onChange 先更新本地 activePath，再由多次 syncActive 做最终校准。
 * 激活态仅由当前页 pageLifetimes.show → deferSyncActive → syncActive 决定。
 */
const TAB_THEME = require('./theme.js')
const THEME_STORAGE_KEY = 'app_theme_mode'
const SYNC_RETRY_DELAYS = [0, 80, 180, 320, 500, 800, 1200]

Component({
  data: {
    iconSize: `${TAB_THEME.TAB_ICON_PX}px`,
    // 提升层级，避免被页面内 fixed 输入条覆盖（线上更常见）
    tabBarZIndex: 1200,
    activePath: "",
    /** 仅在实际处于 tab 页时展示，避免 login 等非 tab 页错误渲染 */
    tabBarVisible: false,
    isSwitching: false,
    activeColor: TAB_THEME.ACTIVE_COLOR,
    inactiveColor: TAB_THEME.INACTIVE_COLOR,
    tabBarThemeClass: '',
    tabBarBg: TAB_THEME.SURFACE_BG,
    tabBarBorderColor: 'rgba(24, 59, 99, 0.08)',
    list: [
      {
        path: "/pages/chat/index",
        text: "话题",
        slotIcon: true,
        slotIconName: "notes-o"
      },
      {
        path: "/pages/requirement/index",
        text: "需求",
        slotIcon: true,
        slotIconName: "question-o"
      },
      {
        path: "/pages/business/index",
        text: "商业",
        slotIcon: true,
        slotIconName: "cash-back-record-o"
      },
      {
        path: "/pages/mine/index",
        text: "我的",
        slotIcon: true,
        slotIconName: "user-o"
      }
    ]
  },
  lifetimes: {
    attached() {
      this.syncThemeMode();
      this.bindRouteSync();
      this.deferSyncActive();
    },
    detached() {
      this.unbindRouteSync();
      this.clearSyncTimers();
    }
  },
  pageLifetimes: {
    show() {
      this.syncThemeMode();
      this.deferSyncActive();
    }
  },
  methods: {
    bindRouteSync() {
      if (typeof wx.onAppRoute !== 'function') return;
      this._onAppRoute = (routeInfo) => {
        const path = this.normalizeRoute(
          routeInfo && (routeInfo.path || routeInfo.route || routeInfo.url)
        );
        this.syncActive(path);
      };
      wx.onAppRoute(this._onAppRoute);
    },
    unbindRouteSync() {
      if (!this._onAppRoute || typeof wx.offAppRoute !== 'function') return;
      wx.offAppRoute(this._onAppRoute);
      this._onAppRoute = null;
    },
    syncThemeMode() {
      let mode = 'light';
      try {
        const fromStorage = wx.getStorageSync(THEME_STORAGE_KEY);
        if (fromStorage === 'dark' || fromStorage === 'light') {
          mode = fromStorage;
        } else {
          const sys = wx.getSystemInfoSync();
          if (sys && sys.theme === 'dark') mode = 'dark';
        }
      } catch (e) {}
      const isDark = mode === 'dark';
      this.setData({
        tabBarThemeClass: isDark ? 'custom-vant-tabbar--dark' : 'custom-vant-tabbar--light',
        activeColor: isDark ? '#FFB020' : TAB_THEME.ACTIVE_COLOR,
        inactiveColor: isDark ? '#9B97A8' : TAB_THEME.INACTIVE_COLOR,
        tabBarBg: isDark ? '#1C1B22' : TAB_THEME.SURFACE_BG,
        tabBarBorderColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(24, 59, 99, 0.08)'
      });
    },
    clearSyncTimers() {
      if (Array.isArray(this._retryTimers) && this._retryTimers.length) {
        this._retryTimers.forEach((t) => clearTimeout(t));
      }
      this._retryTimers = [];
    },
    /**
     * 真机路由更新可能慢于组件 show，按阶段重试读取页面栈同步激活态
     */
    deferSyncActive() {
      this.clearSyncTimers();
      this._retryTimers = SYNC_RETRY_DELAYS.map((delay) =>
        setTimeout(() => {
          this.syncActive();
        }, delay)
      );
    },
    normalizeRoute(route) {
      if (!route) return "";
      const r = String(route).trim().split("?")[0];
      return r.startsWith("/") ? r : `/${r}`;
    },
    syncActive(routeOverride) {
      // 每次同步激活态前都重读主题，覆盖部分机型上 pageLifetimes.show 触发不稳定的情况
      this.syncThemeMode();
      let route = this.normalizeRoute(routeOverride);
      if (!route) {
        const pages = getCurrentPages();
        if (!pages || !pages.length) return;
        const current = pages[pages.length - 1];
        route = this.normalizeRoute(current && current.route);
      }
      const idx = this.data.list.findIndex((item) => item.path === route);

      if (idx < 0) {
        if (this.data.tabBarVisible || this.data.activePath !== "") {
          this.setData({ tabBarVisible: false, activePath: "" });
        }
        return;
      }

      const path = this.data.list[idx].path;
      const patch = {};
      if (!this.data.tabBarVisible) patch.tabBarVisible = true;
      // 即使与当前 activePath 相同也 setData，给 van-tabbar 一次更新信号，避免内部激活态卡住
      patch.activePath = path;
      this.setData(patch);
    },
    onChange(e) {
      const detail = e && e.detail;
      const tab =
        typeof detail === "number" && !Number.isNaN(detail)
          ? this.data.list[detail]
          : this.data.list.find((item) => item.path === this.normalizeRoute(detail));
      if (!tab || this.data.isSwitching) return;
      this.setData({ isSwitching: true, activePath: tab.path, tabBarVisible: true });
      wx.switchTab({
        url: tab.path,
        complete: () => {
          this.setData({ isSwitching: false });
          this.deferSyncActive();
        },
        fail: () => {
          this.setData({ isSwitching: false });
          this.deferSyncActive();
        }
      });
    }
  }
});
