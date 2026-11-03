// ═══════════════════════════════════════════════════════════
// Mobile App JS — ثبت Service Worker + ناوبری
// ═══════════════════════════════════════════════════════════

// ثبت Service Worker برای PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then(reg => console.log('[PWA] SW registered:', reg.scope))
      .catch(err => console.log('[PWA] SW failed:', err));
  });
}

// تنظیم viewport برای موبایل
function setViewport() {
  let meta = document.querySelector('meta[name="viewport"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.name = 'viewport';
    document.head.appendChild(meta);
  }
  meta.content = 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover';
}
setViewport();

// اضافه‌کردن meta tags موبایل
function addMobileMeta() {
  const metas = [
    { name: 'apple-mobile-web-app-capable', content: 'yes' },
    { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' },
    { name: 'apple-mobile-web-app-title', content: 'CDI امداد' },
    { name: 'mobile-web-app-capable', content: 'yes' },
    { name: 'theme-color', content: '#1d3d63' },
    { name: 'application-name', content: 'CDI امداد' },
  ];
  metas.forEach(m => {
    if (!document.querySelector(`meta[name="${m.name}"]`)) {
      const el = document.createElement('meta');
      el.name = m.name;
      el.content = m.content;
      document.head.appendChild(el);
    }
  });
  // manifest
  if (!document.querySelector('link[rel="manifest"]')) {
    const link = document.createElement('link');
    link.rel = 'manifest';
    link.href = '/static/manifest.json';
    document.head.appendChild(link);
  }
  // apple touch icon
  if (!document.querySelector('link[rel="apple-touch-icon"]')) {
    const link = document.createElement('link');
    link.rel = 'apple-touch-icon';
    link.href = '/static/icons/icon-192.png';
    document.head.appendChild(link);
  }
}
addMobileMeta();

// نوار ناوبری پایین — بر اساس نقش کاربر
function renderBottomNav(role, activeTab) {
  const nav = document.getElementById('bottomNav');
  if (!nav) return;

  const tabs = {
    beneficiary: [
      { id: 'home', icon: '🏠', label: 'خانه', url: '/' },
      { id: 'status', icon: '📋', label: 'وضعیت', url: '/beneficiary/status' },
      { id: 'questionnaire', icon: '📝', label: 'پرسشنامه', url: '/questionnaire' },
      { id: 'profile', icon: '👤', label: 'پروفایل', url: '/profile' },
    ],
    assistant: [
      { id: 'pool', icon: '🏊', label: 'استخر', url: '/assistant/pool' },
      { id: 'cases', icon: '📁', label: 'پرونده‌ها', url: '/assistant/pool?filter=mine' },
      { id: 'questionnaire', icon: '📝', label: 'پرسشنامه', url: '/questionnaire' },
      { id: 'profile', icon: '👤', label: 'پروفایل', url: '/profile' },
    ],
    manager: [
      { id: 'dashboard', icon: '📊', label: 'داشبورد', url: '/' },
      { id: 'oversight', icon: '👁️', label: 'نظارت', url: '/hq/oversight' },
      { id: 'reports', icon: '📈', label: 'گزارش', url: '/hq/performance' },
      { id: 'profile', icon: '👤', label: 'پروفایل', url: '/profile' },
    ],
    default: [
      { id: 'home', icon: '🏠', label: 'خانه', url: '/' },
      { id: 'login', icon: '🔑', label: 'ورود', url: '/login' },
      { id: 'register', icon: '📝', label: 'ثبت‌نام', url: '/questionnaire' },
    ],
  };

  const roleTabs = tabs[role] || tabs.default;
  nav.innerHTML = roleTabs.map(t => `
    <a href="${t.url}" class="tab ${activeTab === t.id ? 'active' : ''}">
      <span style="font-size:20px">${t.icon}</span>
      <span>${t.label}</span>
    </a>
  `).join('');
}

// هدر اپلیکیشن
function renderAppHeader(title, subtitle) {
  const header = document.getElementById('appHeader');
  if (!header) return;
  header.innerHTML = `
    <button class="icon-btn" onclick="history.back()">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
        <path d="M15 18l-6-6 6-6"/>
      </svg>
    </button>
    <div style="flex:1">
      <div class="title">${title}</div>
      ${subtitle ? `<div class="subtitle">${subtitle}</div>` : ''}
    </div>
    <button class="icon-btn" onclick="window.location.href='/logout'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
        <polyline points="16 17 21 12 16 7"/>
        <line x1="21" y1="12" x2="9" y2="12"/>
      </svg>
    </button>
  `;
}

// تشخیص موبایل
function isMobile() {
  return window.innerWidth <= 768 || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
}

// اعمال app shell اگر موبایل است
function applyAppShell() {
  if (isMobile()) {
    document.body.classList.add('app-shell');
    if (!document.getElementById('appHeader')) {
      const h = document.createElement('div');
      h.id = 'appHeader'; h.className = 'app-header';
      document.body.insertBefore(h, document.body.firstChild);
    }
    if (!document.getElementById('bottomNav')) {
      const n = document.createElement('div');
      n.id = 'bottomNav'; n.className = 'bottom-nav';
      document.body.appendChild(n);
    }
  }
}

// اجرای اولیه
document.addEventListener('DOMContentLoaded', () => {
  applyAppShell();
});
