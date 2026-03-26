/**
 * 自定义 tabBar 会随 tab 页重建，data 会回到初始值，需按栈同步 activePath。
 * switchTab 后页面栈更新晚于 nextTick，deferSyncActive 内立即 + 80ms 二次 sync。
 * onChange 不提前 setData(activePath)，避免旧页 tabBar 先高亮再销毁造成闪烁/延迟感；
 * 激活态仅由当前页 pageLifetimes.show → deferSyncActive → syncActive 决定。
 */
const TAB_THEME = require('./theme.js')
const THEME_STORAGE_KEY = 'app_theme_mode'

Component({
  data: {
    iconSize: `${TAB_THEME.TAB_ICON_PX}px`,
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
      this.deferSyncActive("attach");
    },
    detached() {
      this.clearSyncTimers();
    }
  },
  pageLifetimes: {
    show() {
      this.syncThemeMode();
      this.deferSyncActive("show");
    }
  },
  methods: {
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
      if (this._attachTimer) {
        clearTimeout(this._attachTimer);
        this._attachTimer = null;
      }
      if (this._showTimer) {
        clearTimeout(this._showTimer);
        this._showTimer = null;
      }
    },
    /**
     * 先立即读栈同步一次，再在 80ms 后同步一次（覆盖 switchTab 栈未就绪）
     */
    deferSyncActive(source) {
      this.syncActive();
      const key = source === "show" ? "_showTimer" : "_attachTimer";
      if (this[key]) {
        clearTimeout(this[key]);
        this[key] = null;
      }
      this[key] = setTimeout(() => {
        this[key] = null;
        this.syncActive();
      }, 80);
    },
    normalizeRoute(route) {
      if (!route) return "";
      const r = String(route).trim().split("?")[0];
      return r.startsWith("/") ? r : `/${r}`;
    },
    syncActive() {
      // 每次同步激活态前都重读主题，覆盖部分机型上 pageLifetimes.show 触发不稳定的情况
      this.syncThemeMode();
      const pages = getCurrentPages();
      if (!pages || !pages.length) return;
      const current = pages[pages.length - 1];
      const route = this.normalizeRoute(current && current.route);
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
      this.setData({ isSwitching: true });
      wx.switchTab({
        url: tab.path,
        complete: () => {
          this.setData({ isSwitching: false });
        },
        fail: () => {
          this.setData({ isSwitching: false });
        }
      });
    }
  }
});
