// ═══════════════════════════════════════════════════════════
// پل ارتباطی بین برنامه استاتیک پرسشنامه و Flask
// دو حالت: ۱) بدون hid (ثبت‌نام جدید) ۲) با hid (بازبینی همیار)
// ═══════════════════════════════════════════════════════════
(function() {
  'use strict';

  const STORE_KEY = 'porseshnameh-db';
  const hid = window.BRIDGE_HID || '';
  const role = window.BRIDGE_ROLE || 'beneficiary';

  console.log('[Bridge] Init — hid:', hid || '(new)', 'role:', role);

  // ─── حالت ۱: بدون hid → نیازمند جدید، در زمان تکمیل household بساز ───
  // ─── حالت ۲: با hid → همیار در حال بازبینی، داده را از Flask بارگذاری کن ───

  async function loadFromFlask() {
    if (!hid) {
      console.log('[Bridge] No hid — fresh registration mode');
      // پاک‌کردن داده قدیمی localStorage برای شروع تازه
      localStorage.removeItem(STORE_KEY);
      return;
    }
    try {
      const resp = await fetch(`/api/assessment/${hid}`);
      if (!resp.ok) { console.log('[Bridge] No data on server'); return; }
      const data = await resp.json();
      if (!data?.assessments) return;
      const storeData = {
        state: { assessments: data.assessments, activeId: hid },
        version: 0,
      };
      localStorage.setItem(STORE_KEY, JSON.stringify(storeData));
      console.log('[Bridge] Data loaded from Flask');
    } catch(e) { console.error('[Bridge] Load error:', e); }
  }

  let saveTimer = null;
  async function saveToFlask() {
    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return;
    let parsed;
    try { parsed = JSON.parse(raw); } catch { return; }
    const assessments = parsed?.state?.assessments || {};
    // یافتن assessment فعال یا آخرین
    const activeId = parsed?.state?.activeId || Object.keys(assessments)[0];
    const assessment = assessments[activeId];
    if (!assessment) return;

    const status = assessment.status || 'draft';
    console.log('[Bridge] Status:', status, 'activeId:', activeId);

    if (status === 'submitted' || status === 'closed') {
      // تکمیل شده → ذخیره نهایی در Flask
      const url = hid ? `/api/assessment/${hid}/complete` : '/api/assessment/create';
      try {
        const body = JSON.stringify({
          assessments: assessments,
          activeId: activeId,
          hid: hid,
          role: role,
        });
        const resp = await fetch(url, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: body,
        });
        const result = await resp.json();
        console.log('[Bridge] Saved to Flask:', result);
        if (result.hid) {
          // هدایت به صفحه موفقیت (برای نیازمند) یا بازبینی (برای همیار)
          setTimeout(() => {
            if (role === 'assistant') {
              window.location.href = `/assistant/review/${result.hid}?done=1`;
            } else {
              window.location.href = `/registration-success/${result.hid}`;
            }
          }, 1500);
        }
      } catch(e) { console.error('[Bridge] Save error:', e); }
    } else if (hid) {
      // ذخیره دوره‌ای (فقط در حالت بازبینی همیار)
      try {
        await fetch(`/api/assessment/${hid}`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({assessments: assessments, hid: hid}),
        });
        console.log('[Bridge] Auto-saved');
      } catch(e) { console.error('[Bridge] Auto-save error:', e); }
    }
  }

  function startMonitoring() {
    window.addEventListener('storage', (e) => {
      if (e.key === STORE_KEY) {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(saveToFlask, 1000);
      }
    });
    // Polling برای تشخیص تغییرات در همان tab
    let lastHash = '';
    setInterval(() => {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return;
      const hash = raw.length + ':' + raw.substring(0, 50);
      if (hash !== lastHash) {
        lastHash = hash;
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(saveToFlask, 2000);
      }
    }, 2000);
  }

  // نمایش نشان نقش (امتیاز شهروندی برای همیار)
  function showRoleBadge() {
    if (role === 'assistant') {
      const badge = document.createElement('div');
      badge.style.cssText = 'position:fixed;top:8px;left:8px;z-index:9999;background:#1d3d63;color:#fff;padding:6px 14px;border-radius:20px;font-size:12px;font-family:Vazirmatn,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.2);display:flex;align-items:center;gap:6px;';
      badge.innerHTML = '🛡️ <span>حالت بازبینی همیار — امتیاز شهروندی فعال</span>';
      document.body.appendChild(badge);
    } else if (hid) {
      const badge = document.createElement('div');
      badge.style.cssText = 'position:fixed;top:8px;left:8px;z-index:9999;background:#12938d;color:#fff;padding:6px 14px;border-radius:20px;font-size:12px;font-family:Vazirmatn,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.2);';
      badge.innerHTML = '📝 حالت خوداظهاری نیازمند';
      document.body.appendChild(badge);
    }
  }

  loadFromFlask().then(() => {
    startMonitoring();
    // نمایش نشان پس از بارگذاری DOM
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', showRoleBadge);
    } else {
      showRoleBadge();
    }
    console.log('[Bridge] Ready');
  });

  window.addEventListener('beforeunload', () => { saveToFlask(); });
})();
