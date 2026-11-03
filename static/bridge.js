// ═══════════════════════════════════════════════════════════
// پل ارتباطی بین برنامه استاتیک پرسشنامه و Flask
// این فایل قبل از بارگذاری برنامه اصلی اجرا می‌شود
// ═══════════════════════════════════════════════════════════
(function() {
  'use strict';

  // دریافت hid از URL یا متغیر تزریق‌شده
  const params = new URLSearchParams(window.location.search);
  const hid = window.BRIDGE_HID || params.get('hid') || '';
  const role = window.BRIDGE_ROLE || params.get('role') || 'beneficiary';

  if (!hid) {
    console.log('[Bridge] No hid in URL, running standalone');
    return;
  }

  const STORE_KEY = 'porseshnameh-db';
  console.log('[Bridge] Initializing for hid:', hid, 'role:', role);

  // ─── ۱) قبل از بارگذاری برنامه: بارگذاری داده از Flask ───
  async function loadFromFlask() {
    try {
      const resp = await fetch(`/api/assessment/${hid}`);
      if (!resp.ok) {
        console.log('[Bridge] No existing data on server');
        return false;
      }
      const data = await resp.json();
      if (!data || !data.assessments) {
        console.log('[Bridge] Invalid data format');
        return false;
      }

      // ساخت ساختار Zustand persist
      const storeData = {
        state: {
          assessments: data.assessments,
          activeId: hid,
        },
        version: 0,
      };

      // ذخیره در localStorage قبل از بارگذاری برنامه
      localStorage.setItem(STORE_KEY, JSON.stringify(storeData));
      console.log('[Bridge] Data loaded from Flask and injected into localStorage');
      return true;
    } catch (e) {
      console.error('[Bridge] Error loading from Flask:', e);
      return false;
    }
  }

  // ─── ۲) ذخیره داده در Flask ───
  let saveTimer = null;
  async function saveToFlask() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      const assessments = parsed?.state?.assessments || {};

      // بررسی وضعیت assessment
      const assessment = assessments[hid];
      if (!assessment) return;

      const status = assessment.status || 'draft';
      console.log('[Bridge] Assessment status:', status);

      const resp = await fetch(`/api/assessment/${hid}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          assessments: assessments,
          status: status,
          hid: hid,
        }),
      });

      if (resp.ok) {
        console.log('[Bridge] Data saved to Flask');
      }

      // اگر وضعیت submitted یا closed است، هدایت به Flask
      if (status === 'submitted' || status === 'closed') {
        console.log('[Bridge] Assessment completed, redirecting...');
        // ذخیره نهایی
        await fetch(`/api/assessment/${hid}/complete`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            assessments: assessments,
            hid: hid,
            role: role,
          }),
        });
        // هدایت به صفحه وضعیت
        setTimeout(() => {
          window.location.href = role === 'assistant'
            ? `/assistant/review/${hid}`
            : `/beneficiary/status/${hid}`;
        }, 1500);
      }
    } catch (e) {
      console.error('[Bridge] Error saving to Flask:', e);
    }
  }

  // ─── ۳) نظارت بر تغییرات localStorage ───
  function startMonitoring() {
    // نظارت با storage event
    window.addEventListener('storage', (e) => {
      if (e.key === STORE_KEY) {
        console.log('[Bridge] localStorage changed');
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(saveToFlask, 1000);
      }
    });

    // نظارت با polling (چون storage event در همان tab فعال نمی‌شود)
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

  // ─── ۴) اجرا ───
  loadFromFlask().then(() => {
    startMonitoring();
    console.log('[Bridge] Monitoring started');
  });

  // ─── ۵) قبل از خروج، ذخیره نهایی ───
  window.addEventListener('beforeunload', () => {
    saveToFlask();
  });

})();
