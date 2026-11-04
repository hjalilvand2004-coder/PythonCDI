// ═══════════════════════════════════════════════════════════
// پل ارتباطی بین برنامه استاتیک پرسشنامه و Flask
// ═══════════════════════════════════════════════════════════
(function() {
  'use strict';

  const STORE_KEY = 'porseshnameh-db';
  const hid = window.BRIDGE_HID || '';
  const role = window.BRIDGE_ROLE || 'beneficiary';

  console.log('[Bridge] Init — hid:', hid || '(new)', 'role:', role);

  let baselineStatus = {};
  let monitoringActive = false;
  let saveTimer = null;
  let redirecting = false;
  let povertyLineFetched = false;
  let beneficiaryAnswers = null;  // snapshot برای امتیاز شهروندی زنده

  // ─── بارگذاری داده از Flask ───
  async function loadFromFlask() {
    if (!hid) {
      console.log('[Bridge] New registration mode');
      return;
    }
    try {
      const resp = await fetch(`/api/assessment/${hid}`);
      if (!resp.ok) return;
      const data = await resp.json();
      if (!data?.assessments) return;

      // دریافت snapshot پاسخ‌های نیازمند برای امتیاز شهروندی
      const assessment = data.assessments[hid] || {};
      beneficiaryAnswers = assessment.beneficiary_answers || null;
      console.log('[Bridge] Beneficiary answers loaded:', beneficiaryAnswers ? Object.keys(beneficiaryAnswers).length + ' keys' : 'none');

      const storeData = {
        state: { assessments: data.assessments, activeId: hid },
        version: 0,
      };
      localStorage.setItem(STORE_KEY, JSON.stringify(storeData));
      console.log('[Bridge] Data loaded from Flask, activeId:', hid);
    } catch(e) { console.error('[Bridge] Load error:', e); }
  }

  // ─── باز کردن مستقیم پرونده در برنامه استاتیک ───
  function forceOpenAssessment() {
    if (!hid) return;
    // برنامه استاتیک ممکن است در صفحه اصلی بماند
    // سعی می‌کنیم با کلیک روی پرونده فعال، آن را باز کنیم
    setTimeout(() => {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return;
      try {
        const parsed = JSON.parse(raw);
        if (parsed?.state?.activeId !== hid) {
          parsed.state.activeId = hid;
          localStorage.setItem(STORE_KEY, JSON.stringify(parsed));
          console.log('[Bridge] Forced activeId to', hid);
        }
      } catch {}
    }, 2000);

    // تلاش برای کلیک روی دکمه «ادامه» یا پرونده فعال
    setTimeout(() => {
      // جستجوی دکمه‌ای که به پرونده فعال مربوط است
      const buttons = document.querySelectorAll('button, a');
      for (const btn of buttons) {
        const text = btn.textContent || '';
        if (text.includes('ادامه') || text.includes('باز کردن') || text.includes('ادامهٔ')) {
          // بررسی اینکه آیا این دکمه برای hid فعلی است
          btn.click();
          console.log('[Bridge] Clicked open button');
          break;
        }
      }
    }, 3500);
  }

  // ─── پنل امتیاز شهروندی زنده ───
  function createCitizenshipPanel() {
    if (role !== 'assistant' || !beneficiaryAnswers) return;

    const panel = document.createElement('div');
    panel.id = 'citizenshipPanel';
    panel.style.cssText = `
      position:fixed; bottom:16px; left:16px; z-index:9999;
      background:#fff; border:2px solid #1d3d63; border-radius:14px;
      padding:14px 18px; min-width:220px; max-width:300px;
      box-shadow:0 6px 24px rgba(0,0,0,.15); font-family:Vazirmatn,sans-serif;
    `;
    panel.innerHTML = `
      <div style="font-size:13px;font-weight:700;color:#1d3d63;margin-bottom:8px;display:flex;align-items:center;gap:6px;">
        🛡️ امتیاز شهروندی (زنده)
      </div>
      <div id="csScore" style="font-size:32px;font-weight:700;text-align:center;color:#16a34a;">۱۰۰</div>
      <div style="font-size:11px;color:#64748b;text-align:center;margin-bottom:8px;">از ۱۰۰</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;text-align:center;font-size:11px;">
        <div style="background:#f0fdf4;padding:6px;border-radius:6px;">
          <div id="csMatched" style="font-weight:700;color:#16a34a;font-size:14px;">۰</div>
          <div style="color:#64748b;">تطابق</div>
        </div>
        <div style="background:#fef2f2;padding:6px;border-radius:6px;">
          <div id="csChanged" style="font-weight:700;color:#dc2626;font-size:14px;">۰</div>
          <div style="color:#64748b;">اصلاحات</div>
        </div>
      </div>
      <div id="csLevel" style="font-size:11px;color:#1d3d63;margin-top:8px;text-align:center;font-weight:600;">
        بسیار صادق — تطابق بالا
      </div>
    `;
    document.body.appendChild(panel);
    console.log('[Bridge] Citizenship panel created');
  }

  // ─── محاسبه زنده امتیاز شهروندی ───
  function updateLiveCitizenship() {
    if (role !== 'assistant' || !beneficiaryAnswers) return;

    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      const assessments = parsed?.state?.assessments || {};
      const activeId = parsed?.state?.activeId || hid;
      const assessment = assessments[activeId];
      if (!assessment) return;
      const currentAnswers = assessment.answers || {};

      // محاسبه ساده امتیاز (بدون نیاز به سرور)
      const scoredPrefixes = ['A1_','A2_','A3_','A4_','A5_','A6_','A7_','A_malnut','A_pregnant',
        'B1_','B2_','B3_','B4_','B5_','B6_','B7_',
        'C1_','C2_','C3_','C4_','C5_','C6_','C7_','C8_','C9_',
        'D1_','D2_','D3_','E1_','E2_','E3_','E4_'];
      const allKeys = new Set([...Object.keys(beneficiaryAnswers), ...Object.keys(currentAnswers)]);
      const scoredKeys = [...allKeys].filter(k => scoredPrefixes.some(p => k.startsWith(p)));

      let matched = 0, changed = 0;
      for (const key of scoredKeys) {
        const oldV = JSON.stringify(beneficiaryAnswers[key] || null);
        const newV = JSON.stringify(currentAnswers[key] || null);
        if (oldV === newV) matched++;
        else changed++;
      }
      const total = scoredKeys.length;
      const score = total > 0 ? Math.round((matched / total) * 100) : 100;

      // سطح
      let level = 'بسیار صادق — تطابق بالا', color = '#16a34a';
      if (score < 85) { level = 'صادق — تطابق متوسط'; color = '#f59e0b'; }
      if (score < 65) { level = 'نقض جزئی — تطابق پایین'; color = '#dc2626'; }
      if (score < 40) { level = 'نقض شدید — مغایرت گسترده'; color = '#dc2626'; }

      // به‌روزرسانی پنل
      const scoreEl = document.getElementById('csScore');
      const matchedEl = document.getElementById('csMatched');
      const changedEl = document.getElementById('csChanged');
      const levelEl = document.getElementById('csLevel');
      if (scoreEl) { scoreEl.textContent = score.toLocaleString('fa-IR'); scoreEl.style.color = color; }
      if (matchedEl) matchedEl.textContent = matched.toLocaleString('fa-IR');
      if (changedEl) changedEl.textContent = changed.toLocaleString('fa-IR');
      if (levelEl) { levelEl.textContent = level; levelEl.style.color = color; }

      console.log('[Bridge] Live citizenship — score:', score, 'matched:', matched, 'changed:', changed);
    } catch(e) {}
  }

  // ─── ثبت baseline ───
  function recordBaseline() {
    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      const assessments = parsed?.state?.assessments || {};
      baselineStatus = {};
      for (const [id, a] of Object.entries(assessments)) {
        baselineStatus[id] = a.status || 'draft';
      }
    } catch(e) {}
  }

  // ─── ذخیره در Flask ───
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

    if (currentStatus !== 'submitted' && currentStatus !== 'closed') return;
    if (baseline === 'submitted' || baseline === 'closed') return;

    if (baseline === undefined) {
      const hh = assessment.household || {};
      if (!hh.headNationalId) return;
    }

    console.log('[Bridge] REAL submission — saving to Flask');
    redirecting = true;
    monitoringActive = false;

    const url = hid ? `/api/assessment/${hid}/complete` : '/api/assessment/create';
    try {
      // اطمینان از اینکه beneficiary_answers در assessment موجود است
      if (hid && beneficiaryAnswers && !assessment.beneficiary_answers) {
        assessment.beneficiary_answers = beneficiaryAnswers;
        assessments[activeId] = assessment;
        parsed.state.assessments = assessments;
      }
      const resp = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({assessments: assessments, activeId: activeId, hid: hid, role: role}),
      });
      const result = await resp.json();
      if (result.hid) {
        setTimeout(() => {
          if (role === 'assistant') {
            window.location.href = `/registration-success/${result.hid}`;
          } else {
            window.location.href = `/registration-success/${result.hid}`;
          }
        }, 3000);
      }
    } catch(e) { redirecting = false; monitoringActive = true; }
  }

  // ─── واکشی خط فقر ───
  async function fetchPovertyLine() {
    if (povertyLineFetched || !monitoringActive) return;
    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return;
    let parsed;
    try { parsed = JSON.parse(raw); } catch { return; }
    const assessments = parsed?.state?.assessments || {};
    const activeId = parsed?.state?.activeId || Object.keys(assessments)[0];
    const assessment = assessments[activeId];
    if (!assessment) return;
    const hh = assessment.household || {};
    if (hh.povertyLine?.source?.includes('رصد فقر')) { povertyLineFetched = true; return; }
    const members = assessment.members || [];
    const postalCode = hh.postalCode || '';
    const province = hh.province || '';
    if (members.length === 0 || (!province && !postalCode)) return;
    const ages = members.map(m => m.age || 35).filter(a => a > 0);
    try {
      const params = new URLSearchParams({province, postal_code: postalCode, ages: ages.join(','), members: String(members.length), urban: '1'});
      const resp = await fetch(`/api/poverty-line?${params}`);
      if (!resp.ok) return;
      const pl = await resp.json();
      hh.povertyLine = {monthlyPerCapita: pl.monthlyPerCapita, region: pl.province, source: pl.source, validAsOf: pl.validAsOf, status: pl.status, householdTotal: pl.householdTotal, details: pl.details, factors: pl.factors};
      assessment.household = hh;
      assessments[activeId] = assessment;
      parsed.state.assessments = assessments;
      localStorage.setItem(STORE_KEY, JSON.stringify(parsed));
      povertyLineFetched = true;
      showPovertyNotification(pl);
    } catch(e) {}
  }

  function showPovertyNotification(pl) {
    const n = document.createElement('div');
    n.style.cssText = 'position:fixed;bottom:80px;right:16px;z-index:9999;background:#fff;border:1px solid #12938d;border-right:4px solid #12938d;border-radius:12px;padding:14px 18px;max-width:340px;box-shadow:0 4px 20px rgba(0,0,0,.15);font-family:Vazirmatn,sans-serif;';
    n.innerHTML = `<div style="font-size:13px;font-weight:700;color:#12938d;margin-bottom:4px;">📊 خط فقر منطقه‌ای — مرکز رصد فقر</div><div style="font-size:12px;color:#1a2b3c;line-height:1.7;">استان: ${pl.province}<br>خط فقر سرانه: ${pl.monthlyPerCapita?.toLocaleString('fa-IR')} تومان<br>خط فقر کل خانوار: ${pl.householdTotal?.toLocaleString('fa-IR')} تومان<br><span style="color:#64748b;font-size:11px;">${pl.source} — ${pl.validAsOf}</span></div>`;
    document.body.appendChild(n);
    setTimeout(() => { n.style.transition='opacity .5s'; n.style.opacity='0'; setTimeout(() => n.remove(), 500); }, 8000);
  }

  // ─── نشان نقش ───
  function showRoleBadge() {
    if (role === 'assistant') {
      const b = document.createElement('div');
      b.style.cssText = 'position:fixed;top:8px;left:8px;z-index:9999;background:#1d3d63;color:#fff;padding:6px 14px;border-radius:20px;font-size:12px;font-family:Vazirmatn,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.2);display:flex;align-items:center;gap:6px;';
      b.innerHTML = '🛡️ <span>حالت بازبینی همیار — امتیاز شهروندی فعال</span>';
      document.body.appendChild(b);
    } else if (hid) {
      const b = document.createElement('div');
      b.style.cssText = 'position:fixed;top:8px;left:8px;z-index:9999;background:#12938d;color:#fff;padding:6px 14px;border-radius:20px;font-size:12px;font-family:Vazirmatn,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.2);';
      b.innerHTML = '📝 حالت خوداظهاری نیازمند';
      document.body.appendChild(b);
    }
  }

  // ─── نظارت ───
  function startMonitoring() {
    window.addEventListener('storage', (e) => {
      if (e.key === STORE_KEY) {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(() => { checkAndSave(); updateLiveCitizenship(); }, 1500);
      }
    });
    let lastRaw = '';
    setInterval(() => {
      if (!monitoringActive || redirecting) return;
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return;
      if (!povertyLineFetched) fetchPovertyLine();
      if (raw !== lastRaw) {
        lastRaw = raw;
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(() => { checkAndSave(); updateLiveCitizenship(); }, 2000);
      }
    }, 2000);
  }

  // ─── اجرا ───
  loadFromFlask().then(() => {
    showRoleBadge();
    recordBaseline();
    // باز کردن مستقیم پرونده (برای حالت همیار)
    if (hid) forceOpenAssessment();
    // ایجاد پنل امتیاز شهروندی زنده (برای همیار)
    if (role === 'assistant') {
      setTimeout(createCitizenshipPanel, 3000);
    }
    setTimeout(() => {
      recordBaseline();
      monitoringActive = true;
      checkAndSave();
      updateLiveCitizenship();
    }, 5000);
    let bc = 0;
    const bi = setInterval(() => { recordBaseline(); bc++; if (bc >= 5) clearInterval(bi); }, 2000);
    startMonitoring();
    console.log('[Bridge] Ready');
  });

  window.addEventListener('beforeunload', () => {
    if (monitoringActive && !redirecting) checkAndSave();
  });
})();
