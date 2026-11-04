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

  // ─── مرحله ۱: پاک‌کردن داده‌های دمو در حالت ثبت‌نام جدید ───
  // برنامه استاتیک ۸ پرونده نمونه دارد که در نخستین اجرا بارگذاری می‌شوند
  // این داده‌ها دارای وضعیت submitted/closed هستند و باعث redirect زودهنگام می‌شوند
  if (!hid) {
    console.log('[Bridge] New registration mode — clearing localStorage');
    localStorage.removeItem(STORE_KEY);
    // همچنین پاک‌کردن کلیدهای مرتبط
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);
      if (key && key.includes('porsesh')) {
        localStorage.removeItem(key);
      }
    }
  }

  // ─── مرحله ۲: متغیرهای حالت ───
  let initialized = false;
  let lastStatus = {};  // {assessmentId: lastKnownStatus}
  let monitoringActive = false;

  // ─── بارگذاری داده از Flask (فقط در حالت بازبینی همیار) ───
  async function loadFromFlask() {
    if (!hid) {
      console.log('[Bridge] No hid — fresh registration mode, localStorage cleared');
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

  // ─── ذخیره داده در Flask ───
  let saveTimer = null;
  async function saveToFlask() {
    if (!monitoringActive) return;  // فقط پس از فعال‌شدن نظارت

    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return;
    let parsed;
    try { parsed = JSON.parse(raw); } catch { return; }
    const assessments = parsed?.state?.assessments || {};
    const activeId = parsed?.state?.activeId || Object.keys(assessments)[0];
    const assessment = assessments[activeId];
    if (!assessment) return;

    const currentStatus = assessment.status || 'draft';
    const previousStatus = lastStatus[activeId] || 'draft';

    console.log('[Bridge] Status check — activeId:', activeId,
                'current:', currentStatus, 'previous:', previousStatus);

    // ─── فقط در صورت تغییر وضعیت به submitted/closed اقدام کن ───
    // این از redirect زودهنگام به‌خاطر داده‌های دمو جلوگیری می‌کند
    if ((currentStatus === 'submitted' || currentStatus === 'closed') &&
        previousStatus !== 'submitted' && previousStatus !== 'closed') {

      console.log('[Bridge] Status transition to', currentStatus, '— saving to Flask');
      monitoringActive = false;  // توقف نظارت برای جلوگیری از ذخیره مضاعف

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
          setTimeout(() => {
            if (role === 'assistant') {
              window.location.href = `/assistant/review/${result.hid}?done=1`;
            } else {
              window.location.href = `/registration-success/${result.hid}`;
            }
          }, 2000);  // تأخیر بیشتر برای نمایش نتیجه در برنامه
        }
      } catch(e) { console.error('[Bridge] Save error:', e); monitoringActive = true; }
    } else if (hid && currentStatus !== previousStatus) {
      // ذخیره دوره‌ای در حالت بازبینی همیار (فقط برای تغییرات غیر submitted)
      try {
        await fetch(`/api/assessment/${hid}`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({assessments: assessments, hid: hid}),
        });
        console.log('[Bridge] Auto-saved (status:', currentStatus, ')');
      } catch(e) { console.error('[Bridge] Auto-save error:', e); }
    }

    // به‌روزرسانی وضعیت قبلی
    lastStatus[activeId] = currentStatus;
  }

  // ─── نظارت بر تغییرات localStorage ───
  function startMonitoring() {
    // ابتدا وضعیت فعلی را ثبت کن (بدون اقدام)
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        const assessments = parsed?.state?.assessments || {};
        for (const [id, a] of Object.entries(assessments)) {
          lastStatus[id] = a.status || 'draft';
          console.log('[Bridge] Initial status for', id, ':', lastStatus[id]);
        }
      } catch {}
    }

    // تأخیر ۳ ثانیه قبل از فعال‌شدن نظارت
    // این به کاربر زمان می‌دهد تا ثبت‌نام کند و پرسشنامه را شروع کند
    setTimeout(() => {
      monitoringActive = true;
      console.log('[Bridge] Monitoring activated (after 3s delay)');
    }, 3000);

    // نظارت با storage event
    window.addEventListener('storage', (e) => {
      if (e.key === STORE_KEY) {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(saveToFlask, 1500);
      }
    });

    // Polling برای تشخیص تغییرات در همان tab
    let lastHash = '';
    setInterval(() => {
      if (!monitoringActive) return;
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return;
      const hash = raw.length + ':' + raw.substring(0, 80);
      if (hash !== lastHash) {
        lastHash = hash;
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(saveToFlask, 2000);
      }
    }, 2000);
  }

  // ─── نشان نقش ───
  function showRoleBadge() {
    if (role === 'assistant') {
      const badge = document.createElement('div');
      badge.style.cssText = 'position:fixed;top:8px;left:8px;z-index:9999;background:#1d3d63;color:#fff;padding:6px 14px;border-radius:20px;font-size:12px;font-family:Vazirmatn,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.2);display:flex;align-items:center;gap:6px;';
      badge.innerHTML = '🛡️ <span>حالت بازبینی همیار</span>';
      document.body.appendChild(badge);
    } else if (hid) {
      const badge = document.createElement('div');
      badge.style.cssText = 'position:fixed;top:8px;left:8px;z-index:9999;background:#12938d;color:#fff;padding:6px 14px;border-radius:20px;font-size:12px;font-family:Vazirmatn,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.2);';
      badge.innerHTML = '📝 حالت خوداظهاری';
      document.body.appendChild(badge);
    }
  }

  // ─── اجرا ───
  loadFromFlask().then(() => {
    startMonitoring();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', showRoleBadge);
    } else {
      showRoleBadge();
    }
    console.log('[Bridge] Ready — monitoring starts in 3s');
  });

  window.addEventListener('beforeunload', () => {
    if (monitoringActive) saveToFlask();
  });
})();
