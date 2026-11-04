// ═══════════════════════════════════════════════════════════
// پل ارتباطی بین برنامه استاتیک پرسشنامه و Flask
// مشکل: برنامه استاتیک ۸ پرونده دمو دارد که در localStorage با وضعیت
// submitted قرار می‌گیرند. bridge نباید این داده‌ها را ذخیره کند.
//
// راه‌حل: localStorage پاک نمی‌شود. در عوض، پس از بارگذاری کامل برنامه،
// وضعیت همه assessmentها به‌عنوان baseline ثبت می‌شود. فقط تغییر وضعیت
// از baseline به submitted باعث ذخیره و redirect می‌شود.
// ═══════════════════════════════════════════════════════════
(function() {
  'use strict';

  const STORE_KEY = 'porseshnameh-db';
  const hid = window.BRIDGE_HID || '';
  const role = window.BRIDGE_ROLE || 'beneficiary';

  console.log('[Bridge] Init — hid:', hid || '(new)', 'role:', role);

  // ─── متغیرهای حالت ───
  let baselineStatus = {};  // وضعیت اولیه assessmentها پس از بارگذاری
  let monitoringActive = false;
  let saveTimer = null;
  let redirecting = false;

  // ─── بارگذاری داده از Flask (فقط در حالت بازبینی همیار) ───
  async function loadFromFlask() {
    if (!hid) {
      // حالت ثبت‌نام جدید — localStorage را پاک نمی‌کنیم!
      // برنامه استاتیک خودش داده‌های دمو را بارگذاری می‌کند.
      // ما فقط وضعیت baseline را ثبت می‌کنیم تا تغییرات واقعی را تشخیص دهیم.
      console.log('[Bridge] New registration mode — will record baseline after app loads');
      return;
    }
    try {
      const resp = await fetch(`/api/assessment/${hid}`);
      if (!resp.ok) { return; }
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

  // ─── ثبت وضعیت baseline ───
  // پس از بارگذاری کامل برنامه، وضعیت همه assessmentها را ثبت می‌کنیم.
  // این شامل داده‌های دمو هم می‌شود. بعداً فقط تغییرات از این baseline
  // باعث ذخیره می‌شوند.
  function recordBaseline() {
    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) {
      console.log('[Bridge] No data in localStorage yet for baseline');
      return;
    }
    try {
      const parsed = JSON.parse(raw);
      const assessments = parsed?.state?.assessments || {};
      baselineStatus = {};
      for (const [id, a] of Object.entries(assessments)) {
        baselineStatus[id] = a.status || 'draft';
        console.log('[Bridge] Baseline —', id, ':', baselineStatus[id]);
      }
      console.log('[Bridge] Baseline recorded for', Object.keys(baselineStatus).length, 'assessments');
    } catch(e) {
      console.error('[Bridge] Baseline error:', e);
    }
  }

  // ─── ذخیره داده در Flask ───
  async function checkAndSave() {
    if (!monitoringActive || redirecting) return;

    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return;
    let parsed;
    try { parsed = JSON.parse(raw); } catch { return; }
    const assessments = parsed?.state?.assessments || {};
    const activeId = parsed?.state?.activeId || Object.keys(assessments)[0];
    const assessment = assessments[activeId];
    if (!assessment) return;

    const currentStatus = assessment.status || 'draft';
    const baseline = baselineStatus[activeId];

    // ─── منطق کلیدی: فقط در صورت تغییر وضعیت از baseline ───
    // اگر assessment در baseline بود و وضعیتش تغییر کرده → ممکن است واقعی باشد
    // اگر assessment در baseline نبود (جدید) و وضعیت submitted دارد → بررسی بیشتر
    if (currentStatus !== 'submitted' && currentStatus !== 'closed') {
      return;  // فقط وضعیت‌های submitted/closed مهم هستند
    }

    // اگر این assessment در baseline بود و وضعیتش همان submitted بود → نادیده بگیر
    if (baseline === 'submitted' || baseline === 'closed') {
      console.log('[Bridge] Ignoring — assessment was already submitted in baseline:', activeId);
      return;
    }

    // اگر assessment جدید است (در baseline نبود) و submitted است →
    // فقط اگر قبلاً آن را به‌عنوان draft دیده‌ایم (یعنی کاربر واقعاً آن را پر کرده)
    if (baseline === undefined) {
      // assessment جدید — بررسی کنیم آیا قبلاً در baseline بود یا نه
      // اگر در baseline نبود و الان submitted است، ممکن است دمو باشد
      // اما اگر کاربر آن را ایجاد کرده باشد، باید اول draft دیده باشیم
      // چون baseline را بعد از بارگذاری کامل ثبت کردیم، هر assessment که در baseline
      // نبود ولی الان submitted است، احتمالاً دمو است که بعد از baseline اضافه شده
      // یا کاربر واقعاً آن را ایجاد و تکمیل کرده
      // برای اطمینان، فقط assessmentهایی را ذخیره می‌کنیم که دارای household.headNationalId باشند
      // (یعنی کاربر واقعاً ثبت‌نام کرده)
      const hh = assessment.household || {};
      if (!hh.headNationalId) {
        console.log('[Bridge] Ignoring — no national ID in assessment:', activeId);
        return;
      }
    }

    // ─── ذخیره واقعی ───
    console.log('[Bridge] REAL submission detected — saving to Flask');
    redirecting = true;
    monitoringActive = false;

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
        }, 3000);  // تأخیر ۳ ثانیه برای نمایش نتیجه در برنامه
      }
    } catch(e) {
      console.error('[Bridge] Save error:', e);
      redirecting = false;
      monitoringActive = true;
    }
  }

  // ─── نظارت بر تغییرات localStorage ───
  function startMonitoring() {
    // نظارت با storage event (برای tabهای دیگر)
    window.addEventListener('storage', (e) => {
      if (e.key === STORE_KEY) {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(checkAndSave, 2000);
      }
    });

    // Polling برای تشخیص تغییرات در همان tab
    let lastRaw = '';
    setInterval(() => {
      if (!monitoringActive || redirecting) return;
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return;
      if (raw !== lastRaw) {
        lastRaw = raw;
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(checkAndSave, 2000);
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
    showRoleBadge();

    // مرحله ۱: ثبت baseline اولیه (قبل از بارگذاری کامل برنامه)
    recordBaseline();

    // مرحله ۲: تأخیر ۵ ثانیه برای بارگذاری کامل برنامه استاتیک
    // برنامه Next.js ممکن است داده‌های دمو را بعد از چند ثانیه بارگذاری کند
    setTimeout(() => {
      // ثبت مجدد baseline پس از بارگذاری کامل
      recordBaseline();
      // فعال‌کردن نظارت
      monitoringActive = true;
      console.log('[Bridge] Monitoring activated (after 5s delay)');
      // بررسی اولیه
      checkAndSave();
    }, 5000);

    // مرحله ۳: ثبت مجدد baseline هر ۲ ثانیه برای ۱۰ ثانیه اول
    // این برای تشخیص داده‌های دمو است که با تأخیر بارگذاری می‌شوند
    let baselineCount = 0;
    const baselineInterval = setInterval(() => {
      recordBaseline();
      baselineCount++;
      if (baselineCount >= 5) {  // ۵ بار × ۲ ثانیه = ۱۰ ثانیه
        clearInterval(baselineInterval);
        console.log('[Bridge] Baseline recording complete');
      }
    }, 2000);

    startMonitoring();
    console.log('[Bridge] Ready — monitoring starts after 5s');
  });

  window.addEventListener('beforeunload', () => {
    if (monitoringActive && !redirecting) checkAndSave();
  });
})();
