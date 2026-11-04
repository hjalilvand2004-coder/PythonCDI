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
    // بررسی اینکه آیا قبلاً خط فقر تأییدشده از مرکز رصد فقر موجود است
    if (hh.povertyLine?.source?.includes('رصد فقر')) { povertyLineFetched = true; return; }

    const members = assessment.members || [];
    const postalCode = hh.postalCode || '';
    const province = hh.province || '';

    // اگر هنوز اعضا یا استان موجود نیست، صبر کن
    if (members.length === 0 || (!province && !postalCode)) return;

    // استخراج سن و جنسیت اعضا برای سرویس خط فقر
    const ages = [];
    const genders = [];
    for (const m of members) {
      const a = m.age || 35;
      ages.push(a);
      genders.push(m.gender || 'male');
    }

    console.log('[Bridge] Fetching poverty line from رصد فقر — province:', province,
                'members:', members.length, 'ages:', ages, 'genders:', genders);

    try {
      // فراخوانی سرویس خط فقر با سن و جنسیت
      const resp = await fetch('/api/poverty-line', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          province: province || 'tehran',
          postal_code: postalCode,
          members: members.map(m => ({age: m.age || 35, gender: m.gender || 'male'})),
          urban: true,
        }),
      });
      if (!resp.ok) return;
      const pl = await resp.json();

      console.log('[Bridge] Poverty line received:', {
        perCapita: pl.monthlyPerCapita,
        total: pl.householdTotal,
        source: pl.source,
      });

      // تزریق خط فقر در assessment با وضعیت verified
      hh.povertyLine = {
        monthlyPerCapita: pl.monthlyPerCapita,
        householdTotal: pl.householdTotal,
        adjustedPerCapita: pl.adjustedPerCapita,
        region: pl.province,
        source: pl.source,
        validAsOf: pl.validAsOf,
        status: 'verified',  // تأییدشده توسط مرکز رصد فقر
        details: pl.details,
        factors: pl.factors,
        fetchedAt: new Date().toISOString(),
      };
      assessment.household = hh;
      assessments[activeId] = assessment;
      parsed.state.assessments = assessments;
      localStorage.setItem(STORE_KEY, JSON.stringify(parsed));

      povertyLineFetched = true;
      console.log('[Bridge] Poverty line injected — status: verified');

      // نمایش نوتیفیکیشن
      showPovertyNotification(pl);

      // به‌روزرسانی پنل خط فقر اگر موجود است
      updatePovertyPanel(pl);
    } catch(e) {
      console.error('[Bridge] Poverty line fetch error:', e);
    }
  }

  function showPovertyNotification(pl) {
    const n = document.createElement('div');
    n.id = 'povertyNotif';
    n.style.cssText = `
      position:fixed; bottom:16px; right:16px; z-index:9999;
      background:#fff; border:2px solid #12938d; border-right:5px solid #12938d;
      border-radius:14px; padding:16px 20px; max-width:380px;
      box-shadow:0 6px 24px rgba(0,0,0,.15); font-family:Vazirmatn,sans-serif;
    `;
    n.innerHTML = `
      <div style="font-size:14px;font-weight:700;color:#12938d;margin-bottom:8px;display:flex;align-items:center;gap:6px;">
        📊 خط فقر منطقه‌ای — مرکز رصد فقر
      </div>
      <div style="font-size:13px;color:#1a2b3c;line-height:1.8;">
        <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #f1f5f9;">
          <span style="color:#64748b;">استان:</span>
          <span style="font-weight:600;">${pl.province}</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #f1f5f9;">
          <span style="color:#64748b;">خط فقر سرانه:</span>
          <span style="font-weight:600;">${pl.monthlyPerCapita?.toLocaleString('fa-IR')} تومان</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #f1f5f9;">
          <span style="color:#64748b;">خط فقر کل خانوار:</span>
          <span style="font-weight:600;">${pl.householdTotal?.toLocaleString('fa-IR')} تومان</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #f1f5f9;">
          <span style="color:#64748b;">ترکیب:</span>
          <span style="font-weight:600;">${pl.factors?.adult_male || 0} مرد، ${pl.factors?.adult_female || 0} زن، ${pl.factors?.child_count || 0} کودک</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0;">
          <span style="color:#64748b;">وضعیت:</span>
          <span style="font-weight:600;color:#16a34a;">✓ تأییدشده</span>
        </div>
      </div>
      <div style="font-size:11px;color:#94a3b8;margin-top:8px;text-align:center;">
        ${pl.source} — ${pl.validAsOf}
      </div>
    `;
    document.body.appendChild(n);
    setTimeout(() => {
      n.style.transition = 'opacity .5s, transform .5s';
      n.style.opacity = '0';
      n.style.transform = 'translateY(20px)';
      setTimeout(() => n.remove(), 500);
    }, 12000);
  }

  // پنل دائمی خط فقر در گوشه صفحه
  function updatePovertyPanel(pl) {
    let panel = document.getElementById('povertyPanel');
    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'povertyPanel';
      panel.style.cssText = `
        position:fixed; top:60px; left:8px; z-index:9998;
        background:#fff; border:1px solid #12938d; border-radius:10px;
        padding:10px 14px; max-width:250px;
        box-shadow:0 4px 12px rgba(0,0,0,.1); font-family:Vazirmatn,sans-serif;
        font-size:12px;
      `;
      document.body.appendChild(panel);
    }
    panel.innerHTML = `
      <div style="font-weight:700;color:#12938d;margin-bottom:4px;">📊 خط فقر (رصد فقر)</div>
      <div style="color:#1a2b3c;line-height:1.6;">
        سرانه: ${pl.monthlyPerCapita?.toLocaleString('fa-IR')}<br>
        کل خانوار: ${pl.householdTotal?.toLocaleString('fa-IR')}<br>
        <span style="color:#16a34a;font-size:11px;">✓ تأییدشده — ${pl.validAsOf}</span>
      </div>
    `;
  }

  // ─── patch خط فقر: مخفی‌کردن فیلدهای دستی و نمایش خودکار ───
  // برنامه استاتیک فیلدهای دستی برای خط فقر دارد
  // این تابع آن‌ها را مخفی کرده و نمایش خودکار از مرکز رصد فقر جایگزین می‌کند
  let povertyPatched = false;

  function patchPovertyLineUI() {
    if (povertyPatched) return;

    // جستجوی بخش خط فقر در DOM
    const allElements = document.querySelectorAll('*');
    let povertySection = null;

    for (const el of allElements) {
      const text = el.textContent || '';
      // جستجوی عناوین مربوط به خط فقر
      if ((text.includes('خط فقر منطقه‌ای') || text.includes('نسخه خط فقر')) &&
          el.children.length > 0 && el.children.length < 50) {
        povertySection = el;
        break;
      }
    }

    if (!povertySection) return;

    // یافتن container بالاتر (کارت یا section)
    let container = povertySection;
    for (let i = 0; i < 5; i++) {
      if (container.parentElement) container = container.parentElement;
    }

    // مخفی‌کردن تمام input/select/textarea در این بخش
    const inputs = container.querySelectorAll('input, select, textarea, button');
    let hiddenCount = 0;
    for (const inp of inputs) {
      // فقط فیلدهای خط فقر (نه دکمه‌های ناوبری)
      const inpText = (inp.placeholder || '') + (inp.name || '') + (inp.id || '');
      if (inpText.includes('فقر') || inpText.includes('poverty') ||
          inpText.includes('سرانه') || inpText.includes('perCapita') ||
          inpText.includes('منبع') || inpText.includes('source') ||
          inpText.includes('اعتبار') || inpText.includes('status') ||
          inpText.includes('pl_') || inp.type === 'number' ||
          (inp.tagName === 'SELECT' && inpText === '')) {
        inp.style.display = 'none';
        hiddenCount++;
      }
    }

    // همچنین مخفی‌کردن labelهای مربوطه
    const labels = container.querySelectorAll('label');
    for (const lbl of labels) {
      const lt = lbl.textContent || '';
      if (lt.includes('سرانه') || lt.includes('منبع') || lt.includes('اعتبار') ||
          lt.includes('تأییدنشده') || lt.includes('تأییدشده') || lt.includes('نامعتبر')) {
        lbl.style.display = 'none';
      }
    }

    if (hiddenCount > 0 || true) {
      // تزریق نمایش خودکار خط فقر
      const raw = localStorage.getItem(STORE_KEY);
      let pl = null;
      if (raw) {
        try {
          const parsed = JSON.parse(raw);
          const assessments = parsed?.state?.assessments || {};
          const activeId = parsed?.state?.activeId || Object.keys(assessments)[0];
          const assessment = assessments[activeId];
          pl = assessment?.household?.povertyLine;
        } catch {}
      }

      // حذف نمایش قبلی اگر موجود است
      const oldDisplay = document.getElementById('autoPovertyDisplay');
      if (oldDisplay) oldDisplay.remove();

      // ساخت نمایش خودکار
      const display = document.createElement('div');
      display.id = 'autoPovertyDisplay';
      display.style.cssText = `
        background: linear-gradient(135deg, #e6f7f6, #dbeafe);
        border: 2px solid #12938d; border-radius: 12px;
        padding: 16px 20px; margin: 12px 0; font-family: Vazirmatn, sans-serif;
      `;

      if (pl && pl.monthlyPerCapita) {
        display.innerHTML = `
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <span style="font-size:20px;">📡</span>
            <div>
              <div style="font-size:14px;font-weight:700;color:#12938d;">خط فقر منطقه‌ای — واکشی خودکار از مرکز رصد فقر</div>
              <div style="font-size:11px;color:#64748b;">${pl.source || 'مرکز رصد فقر'} — ${pl.validAsOf || '۱۴۰۴/۰۷'}</div>
            </div>
            <span style="margin-right:auto;background:#16a34a;color:#fff;padding:3px 10px;border-radius:10px;font-size:11px;font-weight:600;">✓ تأییدشده</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div style="background:#fff;padding:12px;border-radius:8px;text-align:center;">
              <div style="font-size:11px;color:#64748b;">خط فقر سرانه ماهانه</div>
              <div style="font-size:20px;font-weight:700;color:#1d3d63;">${pl.monthlyPerCapita?.toLocaleString('fa-IR')}</div>
              <div style="font-size:10px;color:#94a3b8;">تومان / نفر</div>
            </div>
            <div style="background:#fff;padding:12px;border-radius:8px;text-align:center;">
              <div style="font-size:11px;color:#64748b;">خط فقر کل خانوار</div>
              <div style="font-size:20px;font-weight:700;color:#1d3d63;">${pl.householdTotal?.toLocaleString('fa-IR')}</div>
              <div style="font-size:10px;color:#94a3b8;">تومان / ماه</div>
            </div>
          </div>
          ${pl.factors ? `
          <details style="margin-top:10px;">
            <summary style="font-size:12px;color:#12938d;cursor:pointer;font-weight:600;">📋 جزئیات محاسبه</summary>
            <div style="font-size:11px;color:#1a2b3c;margin-top:8px;white-space:pre-line;background:#fff;padding:10px;border-radius:6px;line-height:1.8;">
              ${pl.details || ''}
            </div>
          </details>` : ''}
          <div style="font-size:10px;color:#94a3b8;margin-top:8px;text-align:center;">
            📡 این داده توسط وب‌سرویس مرکز رصد فقر محاسبه شده — ورود دستی غیرفعال است
          </div>
        `;
      } else {
        display.innerHTML = `
          <div style="text-align:center;padding:8px;">
            <span style="font-size:20px;">⏳</span>
            <div style="font-size:13px;color:#12938d;font-weight:600;margin-top:4px;">در حال واکشی خط فقر از مرکز رصد فقر...</div>
            <div style="font-size:11px;color:#64748b;margin-top:4px;">بر اساس ترکیب خانوار (تعداد، سن، جنسیت) و استان محل سکونت</div>
          </div>
        `;
      }

      // درج در بخش خط فقر
      povertySection.parentElement.insertBefore(display, povertySection.nextSibling);
      povertyPatched = true;
      console.log('[Bridge] Poverty line UI patched — manual fields hidden, auto-display shown');
    }
  }

  // ─── باز کردن خودکار مودال ثبت‌نام ───
  // وقتی کاربر از دکمه «ثبت‌نام» در صفحه لاگین CDI می‌آید،
  // مستقیماً مودال ثبت‌نام برنامه پرسشنامه باز شود
  const autoRegister = window.BRIDGE_ACTION === 'register' ||
    new URLSearchParams(window.location.search).get('action') === 'register';

  function autoOpenRegister() {
    if (!autoRegister) return;

    // جستجوی دکمه «ثبت‌نام» یا «شروع پرسشنامه» در DOM
    const buttons = document.querySelectorAll('button, a, [role="button"]');
    for (const btn of buttons) {
      const text = (btn.textContent || '').trim();
      if (text.includes('ثبت‌نام') || text.includes('شروع پرسشنامه') ||
          text.includes('پرسشنامه جدید') || text.includes('شروع') ||
          text.includes('ثبت‌نام نیازمند') || text.includes('登记') ||
          text.includes('فرم جدید') || text.includes('پرونده جدید')) {
        console.log('[Bridge] Auto-clicking register button:', text.substring(0, 30));
        btn.click();
        return true;
      }
    }
    return false;
  }

  // تلاش مکرر برای کلیک روی دکمه ثبت‌نام
  let registerAttempts = 0;
  function tryAutoRegister() {
    if (!autoRegister || registerAttempts >= 15) return;
    registerAttempts++;
    if (!autoOpenRegister()) {
      setTimeout(tryAutoRegister, 1000);
    } else {
      console.log('[Bridge] Registration modal auto-opened');
    }
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
      // واکشی خط فقر اگر هنوز انجام نشده
      if (!povertyLineFetched) fetchPovertyLine();
      // patch کردن UI خط فقر (مخفی‌کردن فیلدهای دستی)
      if (!povertyPatched) patchPovertyLineUI();
      // اگر خط فقر واکشی شده اما patch هنوز انجام نشده یا نیاز به به‌روزرسانی دارد
      if (povertyPatched && povertyLineFetched) {
        // به‌روزرسانی نمایش اگر خط فقر تازه واکشی شده
        const display = document.getElementById('autoPovertyDisplay');
        if (display && display.querySelector('⏳')) {
          povertyPatched = false;  // برای به‌روزرسانی مجدد
          patchPovertyLineUI();
        }
      }
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
    // باز کردن خودکار مودال ثبت‌نام (برای حالت ثبت‌نام نیازمند)
    if (autoRegister) {
      setTimeout(tryAutoRegister, 3000);  // بعد از بارگذاری برنامه
    }
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
