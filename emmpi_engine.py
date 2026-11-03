# -*- coding: utf-8 -*-
"""
موتور پرسشنامه غربالگری خانوار مبتنی بر EM-MPI
Port وفادارانه از reference repository (Next.js/TypeScript) به Python
سند مرجع: github.com/hjalilvand2004-coder/porseshnameh — src/lib/mpi/

این فایل دقیقاً منطق engine.ts، rules.ts، types.ts، national-id.ts،
registration.ts و web-services.ts را در Python پیاده می‌کند. هیچ قاعده، وزن
یا آستانه‌ای بدون تصویب مرجع تغییر نمی‌کند.
"""

import re
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# ═══════════════════════════════════════════════════════════
# ۱) RULE_SET و ثابت‌ها — port از rules.ts
# ═══════════════════════════════════════════════════════════

RULE_SET = {
    "id": "EM-MPI-RF",
    "version": "1.0.0-demo",
    "demo": True,
    "fullId": "EM-MPI-RF-1.0.0-demo",
}

INDICATOR_TITLES: Dict[str, str] = {
    "A1": "بیماری مزمن یا جدی",
    "A2": "محدودیت عملکردی پایدار",
    "A3": "درمان ضروری انجام‌نشده",
    "A4": "فشار هزینه‌های درمانی",
    "A5": "پوشش بیمه‌ای مؤثر",
    "A6": "ناامنی غذایی ۳۰ روز اخیر",
    "A7": "سلامت روان و ایمنی خانوار",
    "B1": "ترک تحصیل و دسترسی به آموزش اجباری",
    "B2": "خطر ترک تحصیل",
    "B3": "سواد کارکردی مسئول امور",
    "B4": "مانع واقعی دسترسی به آموزش",
    "B5": "ابزار دیجیتال آموزشی",
    "B6": "نیاز آموزشی ویژه",
    "B7": "مهارت و مسیر توانمندسازی",
    "C1": "بی‌خانمانی و تهدید سکونت",
    "C2": "ایمنی و قابلیت سکونت",
    "C3": "پایداری حق سکونت",
    "C4": "تراکم سکونت و فضای خواب ایمن",
    "C5": "آب، برق و انرژی پخت‌وپز",
    "C6": "بهداشت محیط مسکن",
    "C7": "وسایل ضروری زندگی",
    "C8": "فشار هزینه مسکن",
    "C9": "دسترسی به خدمات پایه",
    "D1": "اشتغال و استمرار درآمد تأمین‌کننده اصلی",
    "D2": "بیکاری سایر اعضای توانمند",
    "D3": "کفایت منابع قابل اتکا",
    "E1": "چشم‌انداز معیشت ۱۲ ماه آینده",
    "E2": "بار مراقبت و پشتیبانی آن",
    "E3": "پشتوانه اجتماعی در بحران",
    "E4": "مانع هویتی، حقوقی یا اداری",
}

DIMENSIONS: Dict[str, Dict[str, Any]] = {
    "A": {"title": "سلامت و امنیت زیستی", "cap": 250},
    "B": {"title": "آموزش و رشد انسانی", "cap": 200},
    "C": {"title": "استاندارد زندگی و مسکن", "cap": 300},
    "D": {"title": "معیشت، اشتغال و درآمد", "cap": 150},
    "E": {"title": "ظرفیت مراقبت و پشتوانه اجتماعی", "cap": 100},
}

INDICATORS_BY_DIM: Dict[str, List[str]] = {
    "A": ["A1", "A2", "A3", "A4", "A5", "A6", "A7"],
    "B": ["B1", "B2", "B3", "B4", "B5", "B6", "B7"],
    "C": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"],
    "D": ["D1", "D2", "D3"],
    "E": ["E1", "E2", "E3", "E4"],
}

WEIGHTS: Dict[str, int] = {
    "A1": 35, "A2": 35, "A3": 50, "A4": 35, "A5": 20, "A6": 45, "A7": 30,
    "B1": 60, "B2": 25, "B3": 20, "B4": 20, "B5": 15, "B6": 30, "B7": 40,
    "C1": 60, "C2": 45, "C3": 35, "C4": 25, "C5": 30, "C6": 20, "C7": 25, "C8": 35, "C9": 25,
    "D1": 45, "D2": 25, "D3": 80,
    "E1": 35, "E2": 25, "E3": 20, "E4": 20,
}

TOTAL_CAP = 1000

SCALE_THREE = [0, 0.5, 1]
SCALE_FIVE = [0, 0.25, 0.5, 0.75, 1]
FIVE_STATE = ["A6", "C4", "C8", "D3"]

def scale_of(ind_id: str) -> List[float]:
    return SCALE_FIVE if ind_id in FIVE_STATE else SCALE_THREE

def coeff_allowed(ind_id: str, coeff: float) -> bool:
    return coeff in scale_of(ind_id)

LEVELS = [
    {"index": 1, "min": 0, "max": 150, "label": "سطح ۱ — محرومیت کم"},
    {"index": 2, "min": 150, "max": 300, "label": "سطح ۲ — محرومیت متوسط"},
    {"index": 3, "min": 300, "max": 450, "label": "سطح ۳ — محرومیت نسبتاً شدید"},
    {"index": 4, "min": 450, "max": 600, "label": "سطح ۴ — محرومیت شدید"},
    {"index": 5, "min": 600, "max": 1000, "label": "سطح ۵ — محرومیت بسیار شدید"},
]

def level_of(total: float) -> Optional[Dict]:
    if total < 0 or total > TOTAL_CAP:
        return None
    for l in LEVELS:
        if total >= l["min"] and total < l["max"]:
            return l
    return LEVELS[4]

LEVEL_LABELS_PENDING_APPROVAL = True

FLAG_DEFS: Dict[str, Dict[str, Any]] = {
    "R1": {"title": "خطر جانی یا فوریت پزشکی", "desc": "وضعیتی که تأخیر در رسیدگی می‌تواند به سلامت یا زندگی فرد آسیب جدی بزند.", "strict": True, "pendingApproval": True},
    "R2": {"title": "بی‌خانمانی یا اخطار تخلیه قریب‌الوقوع", "desc": "نبود محل خواب ایمن یا اخطار معتبر تخلیه/فقدان مسکن در کوتاه‌مدت.", "strict": True, "pendingApproval": True},
    "R3": {"title": "سوءتغذیه کودک یا نیاز تغذیه‌ای ویژه", "desc": "کودک با سوءتغذیه مشکوک/تشخیص‌شده یا مادر باردار/شیرده نیازمند تغذیه و درمان.", "strict": False, "pendingApproval": True},
    "R4": {"title": "کودک کار یا کودک در خطر", "desc": "کودکی که کار یا مسئولیت اجباری، امنیت، سلامت یا تحصیل او را مختل کرده است.", "strict": False, "pendingApproval": True},
    "R5": {"title": "خشونت یا خطر آسیب به خود/دیگران", "desc": "نشانه خشونت خانگی، خودآسیبی یا خطر آسیب به دیگران — ثبت محدود و محرمانه.", "strict": True, "pendingApproval": True},
    "R6": {"title": "فقدان مراقب برای فرد وابسته", "desc": "کودک، سالمند یا فرد نیازمند مراقبت بدون مراقب قابل اتکا.", "strict": False, "pendingApproval": True},
    "R7": {"title": "قطع خدمت حیاتی", "desc": "قطع آب/برق/دارو/غذای ضروری بدون جایگزین ایمن در دسترس.", "strict": False, "pendingApproval": True},
    "R8": {"title": "مانع حقوقی/اداری مسدودکننده خدمت حیاتی", "desc": "نبود مدرک هویتی یا مانع حقوقی/اداری که دسترسی به خدمت یا حق اساسی را مسدود کرده باشد.", "strict": False, "pendingApproval": True},
    "R9": {"title": "تناقض یا شبهه جدی در داده نیازمند راستی‌آزمایی", "desc": "مغایرت بین مدارک، اظهارات یا مشاهدات که اعتبار ارزیابی را زیر سؤال می‌برد.", "strict": False, "pendingApproval": True},
}

REFERRAL_PATHS = [
    {"id": "monitoring", "label": "پایش و خدمات عمومی"},
    {"id": "admin_service", "label": "پاسخ اداری یا خدمت مشخص"},
    {"id": "further_review", "label": "بررسی تکمیلی"},
    {"id": "cdi_normal", "label": "ارجاع عادی به CDI"},
    {"id": "cdi_priority", "label": "ارجاع اولویت‌دار"},
    {"id": "cdi_fast_multi", "label": "ارجاع سریع و چندبخشی"},
    {"id": "immediate", "label": "رسیدگی فوری (مستقل از امتیاز)"},
    {"id": "preventive", "label": "ارجاع پیشگیرانه"},
    {"id": "data_verification", "label": "راستی‌آزمایی داده"},
]

OBSERVATION_META_FIELDS = [
    "منبع یا منابع داده",
    "تاریخ مشاهده یا دریافت",
    "ثبت‌کننده و نقش او",
    "مدرک مرتبط (در صورت ضرورت و مجوز)",
    "وضعیت کفایت و اعتبار داده",
    "تناقض یا اطلاعات ناقص",
    "ضریب شدت محاسبه‌شده مطابق قواعد",
    "وضعیت تأیید یا اصلاح مستند",
    "دلیل اصلاح و سابقه تغییر",
    "نشانه خطر و وضعیت بررسی آن",
]

PENDING_APPROVALS = [
    {"scope": "B", "item": "ناسازگاری سند مرجع: مجموع وزن‌های بُعد B برابر ۲۱۰ است ولی سقف برابر ۲۰۰", "why": "مرجع باید یکی از وزن‌ها یا سقف را اصلاح کند."},
    {"scope": "A6", "item": "تعداد تجربه‌های ناامنی غذایی برای ضرایب پنج‌حالته", "why": "آستانه عددی در سند مرجع صریح نشده."},
    {"scope": "C4", "item": "آستانه نفر بر اتاق برای ضرایب پنج‌حالته", "why": "مطابق آستانه‌های مرجع باید تصویب شود."},
    {"scope": "C8", "item": "نسبت هزینه مسکن به منابع و مدیریت معوقه", "why": "نسبت و مرزها در سند مرجع مشخص نیست."},
    {"scope": "D3", "item": "برش‌های نسبت منابع قابل اتکا به خط فقر منطقه‌ای", "why": "برش‌های D3 پیشنهادی و نیازمند اعتبارسنجی است."},
    {"scope": "D3", "item": "مقیاس معادل‌سازی اندازه/ترکیب خانوار", "why": "تعریف واحد اندازه‌گیری خانوار باید تعیین شود."},
    {"scope": "B1", "item": "حداقل مدت وقفه تحصیل برای ضریب میانی", "why": "دوره ارزیابی واحد در سند تعیین نشده."},
    {"scope": "سطوح", "item": "برچسب‌های رسمی سطوح ۱ تا ۵ محرومیت", "why": "مرزهای عددی از سند مرجع است؛ برچسب‌ها پیشنهادی‌اند."},
    {"scope": "R1 تا R9", "item": "تعریف عملیاتی دقیق نشانه‌های خطر", "why": "فهرست نام برده ولی تعریف کامل ارائه نشده."},
    {"scope": "خط فقر", "item": "نسخه معتبر خط فقر منطقه‌ای و تاریخ اعتبار", "why": "ورود دستی فعلاً «تأییدنشده» است."},
    {"scope": "ارجاع", "item": "تفاوت «امکان ارجاع» و «ارجاع عادی» در بازه ۳۰۰ تا ۴۴۹", "why": "اختلاف اسناد برای تأیید مرجع."},
    {"scope": "C8/D3", "item": "مدیریت درآمد صفر و جداکردن ودیعه", "why": "قاعده مرجع اعمال شد ولی صورت‌بندی نیازمند تأیید است."},
    {"scope": "D1", "item": "دوره ارزیابی واحد و آستانه «نوسان جدی»", "why": "دوره واحد باید رسمی تعیین شود."},
    {"scope": "D1", "item": "نبود فرد اصلی دارای توان و امکان کار", "why": "وضعیت کاربرد باید رسماً تعیین شود."},
    {"scope": "شاخص‌های عضو‌محور", "item": "قاعده تجمیع چند عضو", "why": "قاعده باید برای هر شاخص مصوب شود."},
    {"scope": "C4", "item": "وضعیت صفر اتاق و فقدان فضای خواب ایمن", "why": "تقسیم بر صفر ممنوع است."},
    {"scope": "C8", "item": "فرمول دقیق منابع قابل‌دسترس", "why": "مبلغ «درآمد خالص» مشترک استفاده نشود."},
    {"scope": "اعتبار منابع", "item": "تفکیک اولویت دریافت خدمات از اعتبار شواهد", "why": "قاعده اولویت باید تصویب شود."},
    {"scope": "پرچم قرمز", "item": "گردش کار انسانی: ثبت بی‌درنگ، تأیید، تداوم، خاتمه", "why": "تأیید و خاتمه در فرایند انسانی مستقل."},
]

DEPRECATED_REFS = ["D4", "D5", "D6", "E6"]

# ═══════════════════════════════════════════════════════════
# ۲) SPECIAL_ANSWERS — port از types.ts
# ═══════════════════════════════════════════════════════════

SPECIAL_ANSWERS = {
    "DONT_KNOW": "__dontknow__",
    "REFUSE": "__refuse__",
    "NEED_REVIEW": "__needreview__",
    "NONE": "__none__",
}

def is_special(v: Any) -> bool:
    return v in (SPECIAL_ANSWERS["DONT_KNOW"], SPECIAL_ANSWERS["REFUSE"],
                 SPECIAL_ANSWERS["NEED_REVIEW"], SPECIAL_ANSWERS["NONE"])

# ═══════════════════════════════════════════════════════════
# ۳) اعتبارسنجی شناسه‌ها — port از national-id.ts
# ═══════════════════════════════════════════════════════════

_FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"

def normalize_digits(s: str) -> str:
    """تبدیل ارقام فارسی/عربی به لاتین + حذف جداکننده‌ها"""
    if not s:
        return ""
    result = []
    for c in str(s):
        idx = _FA_DIGITS.find(c)
        if idx >= 0:
            result.append(str(idx))
            continue
        idx = _AR_DIGITS.find(c)
        if idx >= 0:
            result.append(str(idx))
            continue
        if c in " \t-_":
            continue
        result.append(c)
    return "".join(result)

def is_valid_iranian_national_id(input_str: str) -> bool:
    """اعتبارسنجی کد ملی ۱۰ رقمی ایران — الگوریتم رقم کنترل"""
    nid = normalize_digits(input_str)
    if not re.match(r"^\d{10}$", nid):
        return False
    if re.match(r"^(\d)\1{9}$", nid):
        return False
    digits = [int(d) for d in nid]
    check = digits[9]
    s = sum(digits[i] * (10 - i) for i in range(9))
    rem = s % 11
    return check == rem if rem < 2 else check == (11 - rem)

def is_valid_postal_code(input_str: str) -> bool:
    return bool(re.match(r"^\d{10}$", normalize_digits(input_str)))

def national_id_error(input_str: str) -> Optional[str]:
    nid = normalize_digits(input_str)
    if len(nid) == 0:
        return "کد ملی سرپرست اجباری است — کلید شناسایی خانوار و مبنای استعلام همه مراجع."
    if len(nid) != 10:
        return f"کد ملی باید دقیقاً ۱۰ رقم باشد ({len(nid)} رقم وارد شده)"
    if not re.match(r"^\d{10}$", nid):
        return "کد ملی فقط می‌تواند رقم باشد."
    if not is_valid_iranian_national_id(nid):
        return "کد ملی با الگوریتم ثبت احوال تطبیق ندارد — رقم کنترل نادرست است."
    return None

# ═══════════════════════════════════════════════════════════
# ۴) اعتبارسنجی ثبت‌نام — port از registration.ts
# ═══════════════════════════════════════════════════════════

def is_valid_mobile(input_str: str) -> bool:
    return bool(re.match(r"^09\d{9}$", normalize_digits(input_str)))

def mobile_error(input_str: str) -> Optional[str]:
    m = normalize_digits(input_str)
    if len(m) == 0:
        return "شماره موبایل اجباری است — کد تأیید و اطلاع‌رسانی پیگیری درخواست به همین شماره ارسال می‌شود."
    if not m.startswith("09"):
        return "شماره موبایل باید با ۰۹ شروع شود (مثلاً ۰۹۱۲۳۴۵۶۷۸۹)."
    if len(m) != 11:
        return f"شماره موبایل باید ۱۱ رقم باشد ({len(m)} رقم وارد شده)."
    if not is_valid_mobile(m):
        return "شماره موبایل معتبر نیست — فقط رقم مجاز است."
    return None

def _jalali_month_length(year: int, month: int) -> int:
    if month <= 6:
        return 31
    if month <= 11:
        return 30
    rem = year % 33
    leap = rem in [1, 5, 9, 13, 17, 22, 26, 30]
    return 30 if leap else 29

def normalize_jalali_date(input_str: str) -> Optional[str]:
    s = normalize_digits(input_str).replace(".", "/").replace("-", "/")
    parts = [p for p in s.split("/") if p]
    if len(parts) == 3:
        y, m, d = parts
    elif len(s) == 8 and s.isdigit():
        y, m, d = s[:4], s[4:6], s[6:8]
    else:
        return None
    if not (re.match(r"^\d{4}$", y) and re.match(r"^\d{1,2}$", m) and re.match(r"^\d{1,2}$", d)):
        return None
    yy, mm, dd = int(y), int(m), int(d)
    if yy < 1300 or yy > 1420:
        return None
    if mm < 1 or mm > 12:
        return None
    if dd < 1 or dd > _jalali_month_length(yy, mm):
        return None
    return f"{y}/{m.zfill(2)}/{d.zfill(2)}"

def birth_date_error(input_str: str) -> Optional[str]:
    if len(normalize_digits(input_str)) == 0:
        return "تاریخ تولد اجباری است — با کد ملی و تاریخ تولد، هویت از ثبت احوال تطبیق داده می‌شود."
    if not normalize_jalali_date(input_str):
        return "تاریخ تولد شمسی معتبر نیست — قالب مثال: ۱۳۶۲/۰۵/۱۲."
    return None

_FORBIDDEN_PW_CHARS = '&<>"\\/;,*|=%'

def password_error(pw: str) -> Optional[str]:
    if len(pw) == 0:
        return "رمز عبور اجباری است."
    bad = [c for c in pw if c in _FORBIDDEN_PW_CHARS]
    if bad:
        return f"برای رمز عبور از کاراکترهای {_FORBIDDEN_PW_CHARS} استفاده نکنید."
    if len(pw) != 6:
        return f"رمز عبور باید شامل ۶ کاراکتر باشد ({len(pw)} کاراکتر وارد شده)."
    if not re.match(r"^[A-Za-z0-9]+$", pw):
        return "رمز عبور فقط می‌تواند ترکیبی از اعداد و حروف انگلیسی باشد."
    if not re.search(r"[A-Za-z]", pw):
        return "رمز عبور باید ترکیبی باشد — حداقل یک حرف انگلیسی در آن باشد."
    if not re.search(r"\d", pw):
        return "رمز عبور باید ترکیبی باشد — حداقل یک عدد در آن باشد."
    return None

def hash_password(pw: str) -> str:
    """هش FNV-1a (نسخه نمایشی) — متن ساده هرگز ذخیره نمی‌شود"""
    h = 2166136261
    for c in pw:
        h ^= ord(c)
        h = (h * 16777619) & 0xFFFFFFFF
    return f"fnv1a:{h:08x}"

REGISTRATION_KINDS = [
    {"value": "need_service", "label": "اعلام نیازمندی و دریافت خدمات دارم.",
     "desc": "پرسشنامه غربالگری محرومیت خانوار (EM-MPI) برای شما آغاز می‌شود."},
    {"value": "provide_service", "label": "متقاضی ارائه خدمت به مددجویان و نیازمندان هستم",
     "desc": "پرسشنامه محرومیت برای شما تکمیل نمی‌شود؛ به داشبورد حرفه‌ای هدایت می‌شوید."},
]

BANK_AGREEMENT_PARAGRAPHS = [
    {"h": "۱) هدف دسترسی",
     "p": "با رضایت شما، وضعیت حساب و گردش بانکی سرپرست فقط برای «راستی‌آزمایی معیشت و درآمد» (بُعد D) از طریق شاپرک استعلام می‌شود."},
    {"h": "۲) دامنه دسترسی",
     "p": "مانده حساب، گردش ۹۰ روز اخیر به‌صورت تجمیعی، وضعیت تسهیلات و چک برگشتی؛ جزئیات خرید مشاهده نمی‌شوند."},
    {"h": "۳) محرمانگی و محدودیت استفاده",
     "p": "داده بانکی فقط در همین پرونده استفاده می‌شود، امتیاز مستقل ایجاد نمی‌کند، در اختیار ثالث قرار نمی‌گیرد و دسترسی نقش‌محور است."},
    {"h": "۴) مدت و لغو رضایت",
     "p": "این رضایت تا بستن پرونده معتبر است و هر زمان قابل لغو است؛ لغو مانع ادامه ارزیابی سایر بخش‌ها نیست."},
]

# ═══════════════════════════════════════════════════════════
# ۵) شبیه‌سازی ۸ سرویس وب — port از web-services.ts
# ═══════════════════════════════════════════════════════════

def _hash_str(s: str) -> int:
    """FNV-1a 32-bit hash"""
    h = 2166136261
    for c in s:
        h ^= ord(c)
        h = (h * 16777619) & 0xFFFFFFFF
    return h

def _pick(seed: int, pool: List, salt: int = 0) -> Any:
    """انتخاب قطعی از pool با seed"""
    return pool[(seed + salt * 2654435761) % len(pool)]

MALE_NAMES = ["علی", "محمد", "حسین", "رضا", "مهدی", "امیر", "سعید", "حمید", "کریم", "جواد"]
FEMALE_NAMES = ["فاطمه", "زهرا", "مریم", "سارا", "نرگس", "لیلا", "معصومه", "الهام", "شیما", "پریسا"]
LAST_NAMES = ["احمدی", "محمدی", "حسینی", "رضایی", "کریمی", "موسوی", "جلیلوند", "شریفی", "نوروزی", "قاسمی", "صادقی", "بهرامی"]
RELATIONS_POOL = ["همسر", "فرزند", "فرزند", "فرزند", "مادر", "پدر", "خواهر", "برادر"]
PROVINCES = ["تهران", "البرز", "خراسان رضوی", "اصفهان", "فارس", "خوزستان", "مازندران", "آذربایجان شرقی", "گیلان", "کرمان"]
COUNTY_SUFFIX = ["مرکزی", "شهرستان جدید", "بهارستان", "پارس‌آباد", "زرندیه"]
STREET_NAMES = ["خیابان امام خمینی", "خیابان شهید بهشتی", "بلوار ولی‌عصر", "خیابان شریعتی", "بلوار شهید کاظمی", "خیابان انقلاب"]
MARRIAGE = ["متأهل", "متأهل", "مجرد", "متأهل — رویداد ازدواج اخیر ثبت شده", "متروکه (سابقه ثبتی)"]
FUND_NAMES = ["تأمین اجتماعی", "بیمه روستاییان و عشایر", "خدمات درمانی کشوری", "نیروهای مسلح"]
INS_COVER = [
    {"v": "effective", "label": "پوشش معتبر"},
    {"v": "effective", "label": "پوشش معتبر"},
    {"v": "barriers", "label": "پوشش با مانع (فرانشیز/فاصله)"},
    {"v": "none", "label": "بدون پوشش فعال"},
]
EDU_STATUS = [
    {"v": "enrolled", "label": "ثبت‌نام فعال"},
    {"v": "enrolled", "label": "ثبت‌نام فعال"},
    {"v": "interrupted", "label": "وقفه تحصیل"},
    {"v": "dropped", "label": "ترک تحصیل"},
]
DEGREES = ["کارشناسی", "دیپلم", "کارشناسی ارشد", "کاردانی"]
SUPPORT_SERVICES = ["اکرام اطعام", "کمک تغذیه", "کمک شهریه دانش‌آموزی", "بسته معاشی ماهانه", "کمک اجاره مسکن", "خدمات بهداشتی و درمانی حمایتی", "وام اشتغال‌زای کوچک", "بسته آموزشی دانش‌آموزان"]

def _digits_only(s: str) -> str:
    if not s:
        return ""
    out = []
    for c in str(s):
        idx = _FA_DIGITS.find(c)
        if idx >= 0:
            out.append(str(idx))
            continue
        idx = _AR_DIGITS.find(c)
        if idx >= 0:
            out.append(str(idx))
            continue
        if c.isdigit():
            out.append(c)
    return "".join(out)

def _svc_result(service_id: str, status: str, data: Dict[str, str],
                note: str = None, prefills: Dict = None) -> Dict:
    return {
        "serviceId": service_id, "status": status,
        "fetchedAt": datetime.now().isoformat(),
        "data": data, "note": note, "prefills": prefills,
    }

def simulate_service_fetch(service_id: str, assessment: Dict) -> Dict:
    """شبیه‌سازی واکشی از ۸ سرویس — قطعی از شناسه‌ها"""
    h = assessment.get("household", {}) or {}
    members = assessment.get("members", []) or []
    nid = _digits_only(h.get("headNationalId", ""))
    postal = _digits_only(h.get("postalCode", ""))

    if service_id == "civil_registry":
        if len(nid) != 10:
            return _svc_result(service_id, "error", {},
                               "کد ملی ده‌رقمی سرپرست وارد نشده است — استعلام ثبت احوال ممکن نیست.")
        seed = _hash_str("reg:" + nid)
        gender_head = "female" if (seed + 7) % 5 == 0 else "male"
        first = _pick(seed, MALE_NAMES if gender_head == "male" else FEMALE_NAMES)
        last = _pick(seed, LAST_NAMES, 3)
        head_name = f"{first} {last}"
        spouse_first = _pick(seed, FEMALE_NAMES if gender_head == "male" else MALE_NAMES, 5)
        spouse_name = f"{spouse_first} {last}"
        child_count = 1 + ((seed >> 5) % 3)
        member_creates = []
        if seed % 3 != 1:
            member_creates.append({
                "firstName": spouse_name, "relation": "همسر",
                "age": 25 + ((seed >> 9) % 25),
                "gender": "female" if gender_head == "male" else "male",
                "fromRegistry": True,
            })
        for i in range(child_count):
            c_seed = seed + i * 97
            cg = "male" if c_seed % 2 == 0 else "female"
            age = (c_seed >> 3) % 17
            member_creates.append({
                "firstName": f"{_pick(c_seed, MALE_NAMES if cg == 'male' else FEMALE_NAMES, i + 2)} {last}",
                "relation": "فرزند", "age": age, "gender": cg, "fromRegistry": True,
            })
        marriage = _pick(seed, MARRIAGE, 11)
        return _svc_result(service_id, "ok", {
            "نام و نام خانوادگی سرپرست": head_name,
            "کد ملی سرپرست": nid,
            "وضعیت تأهل (سابقه ثبتی)": marriage,
            "اعضای ثبت‌شده در سابقه ثبتی": f"{len(member_creates)} نفر",
        }, "پاسخ شبیه‌سازی‌شده از کد ملی — اعضای واکشی‌شده با برچسب منبع ثبت می‌شوند.",
           {"householdPatch": {"headName": head_name, "headNationalId": nid, "headNationalIdStatus": "has"},
            "memberCreates": member_creates})

    if service_id == "post":
        if len(postal) != 10:
            return _svc_result(service_id, "error", {},
                               "کد پستی ده‌رقمی وارد نشده است — استعلام نشانی ممکن نیست.")
        seed = _hash_str("post:" + postal)
        province = _pick(seed, PROVINCES)
        county = f"{province} — {_pick(seed, COUNTY_SUFFIX, 2)}"
        street = _pick(seed, STREET_NAMES, 4)
        alley = (seed % 12) + 1
        no = (seed >> 6) % 90 + 1
        address = f"{province}، {county}، {street}، کوچه {alley}، پلاک {no}"
        return _svc_result(service_id, "ok", {
            "نشانی استاندارد (از کد پستی)": address,
            "استان": province, "شهرستان / منطقه": county,
        }, "پاسخ شبیه‌سازی‌شده از کد پستی — نشانی استاندارد پست ملاک است.",
           {"householdPatch": {"province": province, "county": county, "address": address}})

    if service_id == "shaparak_bank":
        if len(nid) != 10:
            return _svc_result(service_id, "error", {}, "ابتدا کد ملی سرپرست را ثبت و واکشی کنید.")
        if not (h.get("consents") or {}).get("bankAccess"):
            return _svc_result(service_id, "error", {},
                               "توافقنامه دسترسی به اطلاعات بانکی پذیرفته نشده است.")
        seed = _hash_str("shp:" + nid)
        has_account = seed % 5 != 0
        if not has_account:
            return _svc_result(service_id, "ok", {
                "حساب فعال با این کد ملی": "یافت نشد",
            }, "حساب فعالی یافت نشد — این داده سنجش است و پیش‌داوری نیست.")
        turn = 3 + (seed % 9)
        loans = "یک تسهیلات کوچک فعال" if seed % 4 == 0 else "تسهیلات فعال ثبت نشده"
        bounced = "یک مورد سابقه چک برگشتی" if seed % 7 == 0 else "سابقه چک برگشتی ثبت نشده"
        return _svc_result(service_id, "ok", {
            "وضعیت حساب بانکی سرپرست": "حساب فعال — تطبیق با کد ملی انجام شد",
            "گردش تجمیعی ۳ ماه اخیر": f"{turn} تراکنش در ماه",
            "وضعیت تسهیلات": loans, "چک برگشتی": bounced,
        }, "فقط راستی‌آزمایی معیشت (D) — داده بانکی لایه پرونده‌ای است و امتیاز مستقل ندارد.")

    if service_id == "insurance":
        if len(nid) != 10:
            return _svc_result(service_id, "error", {}, "ابتدا کد ملی سرپرست را ثبت کنید.")
        if not members:
            return _svc_result(service_id, "error", {}, "عضوی برای تطبیق پوشش بیمه ثبت نشده است.")
        answer_prefills = []
        rows = []
        for i, m in enumerate(members):
            s2 = _hash_str(f"ins:{nid}:{m.get('nationalId') or m.get('id')}:{m.get('firstName', '')}")
            cover = _pick(s2, INS_COVER, i)
            answer_prefills.append({
                "key": f"A5_cover#{m['id']}", "value": cover["v"],
                "label": f"{m.get('firstName', '')}: {cover['label']} (A5)",
            })
            rows.append(f"{m.get('firstName', '')}: {cover['label']} — {_pick(s2, FUND_NAMES, i + 1)}")
        has_unknown = any(m.get("nationalIdStatus") == "missing" for m in members)
        return _svc_result(service_id, "partial" if has_unknown else "ok", {
            "پوشش پایه اعضا (سابقه صندوق‌ها)": " • ".join(rows),
        }, "وجود پوشش «پیش‌تکمیل ملاک» است؛ اعتبار و مانع استفاده واقعی باید جداگانه تأیید شود.",
           {"answerPrefills": answer_prefills})

    if service_id == "property":
        if len(nid) != 10:
            return _svc_result(service_id, "error", {}, "ابتدا کد ملی سرپرست را ثبت کنید.")
        seed = _hash_str("prop:" + nid)
        owned = seed % 4 == 0
        tenure = "مالک" if owned else _pick(seed, ["مستأجر", "رایگان سکونت دارد", "خدمتی", "وابسته به نهاد/فرد"], 3)
        patch = {} if h.get("tenureType") else {"tenureType": tenure}
        return _svc_result(service_id, "ok", {
            "سابقه سند مسکن به نام سرپرست": "یافت شد" if owned else "یافت نشد",
            "نوع تصرف استنباط‌شده (پیش‌تکمیل)": tenure,
        }, "نوع تصرف «پیش‌تکمیل» اعمال می‌شود؛ مستأجربودن به‌تنهایی امتیاز نمی‌گیرد.",
           {"householdPatch": patch})

    if service_id == "education_school":
        if len(nid) != 10:
            return _svc_result(service_id, "error", {}, "ابتدا کد ملی سرپرست را ثبت کنید.")
        if not members:
            return _svc_result(service_id, "error", {}, "عضوی ثبت نشده است.")
        school = [m for m in members if m.get("schoolAge") or (isinstance(m.get("age"), (int, float)) and 6 <= m["age"] <= 18)]
        if not school:
            return _svc_result(service_id, "ok", {"اعضای در سن آموزش اجباری": "۰ نفر"},
                               "عضوی در سن ۶ تا ۱۸ سال ثبت نشده — B1/B2 صحیح صفر محاسبه می‌شوند.")
        member_prefills = []
        answer_prefills = []
        rows = []
        b1_map = {"enrolled": "attending", "interrupted": "interrupted", "dropped": "dropped"}
        for i, m in enumerate(school):
            s2 = _hash_str(f"edu:{nid}:{m.get('nationalId') or m.get('id')}")
            st = _pick(s2, EDU_STATUS, i)
            member_prefills.append({"memberId": m["id"], "patch": {"educationStatus": st["v"]}, "label": f"{m.get('firstName','')}: {st['label']}"})
            answer_prefills.append({"key": f"B1_status#{m['id']}", "value": b1_map.get(st["v"], "interrupted"), "label": f"{m.get('firstName','')}: {st['label']} (B1)"})
            rows.append(f"{m.get('firstName','')}: {st['label']}")
        return _svc_result(service_id, "ok", {
            "وضعیت ثبت‌نام اعضا در سن آموزش": " • ".join(rows),
        }, "سابقه ثبتی «ملاک استعلام» است؛ حضور فعال و غیبت جاری جداگانه بررسی می‌شود.",
           {"memberPrefills": member_prefills, "answerPrefills": answer_prefills})

    if service_id == "higher_edu":
        if len(nid) != 10:
            return _svc_result(service_id, "error", {}, "ابتدا کد ملی سرپرست را ثبت کنید.")
        if not members:
            return _svc_result(service_id, "error", {}, "عضوی ثبت نشده است.")
        adults = [m for m in members if isinstance(m.get("age"), (int, float)) and m["age"] >= 19]
        member_prefills = []
        rows = []
        for i, m in enumerate(adults):
            s2 = _hash_str(f"uni:{nid}:{m.get('nationalId') or m.get('id')}")
            has = s2 % 3 == 0
            deg = _pick(s2, DEGREES, i)
            if has and not m.get("educationGrade"):
                member_prefills.append({"memberId": m["id"], "patch": {"educationGrade": deg}, "label": f"{m.get('firstName','')}: {deg}"})
                rows.append(f"{m.get('firstName','')}: {deg}")
        return _svc_result(service_id, "ok", {
            "اعضای دارای مدرک دانشگاهی": " • ".join(rows) if rows else "در سابقه ثبتی یافت نشد",
        }, None if rows else "مدارک دانشگاهی یافت نشد — مدرک شرط سنجش نیست.",
           {"memberPrefills": member_prefills} if member_prefills else None)

    if service_id == "samaneh_bank":
        if len(nid) != 10:
            return _svc_result(service_id, "error", {}, "ابتدا کد ملی سرپرست را ثبت کنید.")
        seed = _hash_str("sam:" + nid)
        has_case = seed % 4 != 0
        if not has_case:
            return _svc_result(service_id, "ok", {
                "سابقه پرونده در بانک سامانه": "یافت نشد",
            }, "سابقه حمایتی ثبت نشده — داده زمینه‌ای است و تأثیری در امتیاز ندارد.")
        start_year = 1395 + (seed % 8)
        start_month = 1 + ((seed >> 7) % 12)
        support_since = f"{start_year}/{start_month:02d}"
        svc_count = 2 + (seed % 2)
        services = [_pick(seed, SUPPORT_SERVICES, i + 1) for i in range(svc_count)]
        prior_services = "، ".join(services)
        return _svc_result(service_id, "ok", {
            "شروع دوره حمایت (سابقه سامانه)": support_since,
            "خدمات/برنامه‌های حمایتی قبلی": prior_services,
        }, "این فیلدها صرفاً از واکشی بانک سامانه ثبت می‌شود؛ ورود دستی مجاز نیست.",
           {"householdPatch": {"supportSince": support_since, "priorServices": prior_services}})

    return _svc_result(service_id, "error", {}, "سرویس شناسایی نشد.")

LOCKED_FIELDS = {
    "civil_registry": ["headName", "headNationalId", "headBirthDate"],
    "post": ["province", "county", "address"],
    "shaparak_bank": [],
    "property": [],
    "insurance": [],
    "education_school": [],
    "higher_edu": [],
    "samaneh_bank": ["supportSince", "priorServices"],
}

# ═══════════════════════════════════════════════════════════
# ۶) موتور امتیازدهی — port از engine.ts
# ═══════════════════════════════════════════════════════════

_INCOMPLETE_BASIS = "داده ضروری ناموجود یا نامطمئن است؛ بدون امتیازدهی اجباری."

def _get(a: Dict, key: str) -> Any:
    return a.get(key)

def _get_m(a: Dict, key: str, member_id: str) -> Any:
    return a.get(f"{key}#{member_id}")

def _special_status(v: Any) -> Optional[str]:
    if v in (SPECIAL_ANSWERS["DONT_KNOW"], SPECIAL_ANSWERS["REFUSE"], SPECIAL_ANSWERS["NEED_REVIEW"]):
        return "incomplete"
    return None

def _num(v: Any) -> Optional[float]:
    if isinstance(v, (int, float)) and not (isinstance(v, bool)):
        return float(v) if v == v else None  # NaN check
    if isinstance(v, str) and v.strip():
        try:
            return float(v)
        except ValueError:
            return None
    return None

def _str_list(v: Any) -> List[str]:
    if isinstance(v, list):
        return [x for x in v if isinstance(x, str)]
    return []

def _worst_member(a: Dict, members: List[Dict], key: str,
                  map_fn, filter_fn=None) -> Tuple[Optional[float], bool, int]:
    """تجمیع عضومحور با بیشینه اعضای مشمول"""
    rel = [m for m in members if (filter_fn is None or filter_fn(m))]
    worst = None
    all_answered = True
    for m in rel:
        v = _get_m(a, key, m["id"])
        s = _special_status(v)
        if s:
            all_answered = False
            continue
        c = map_fn(v)
        if c is None:
            all_answered = False
            continue
        worst = c if worst is None else max(worst, c)
    return worst, all_answered, len(rel)

def resolve_indicator(ind_id: str, a: Dict, hh: Dict) -> Dict:
    """حل‌کننده هر شاخص — کاملاً قطعی. خروجی: {coeff, status, basis, pendingApproval}"""
    members = hh.get("members", []) or []

    # ─── بُعد A: سلامت ───
    if ind_id == "A1":
        if not members:
            return {"status": "incomplete", "basis": "هیچ عضوی ثبت نشده است."}
        worst = 0
        for m in members:
            dis = _get_m(a, "A1_disease", m["id"])
            imp = _get_m(a, "A1_impact", m["id"])
            if _special_status(dis) or _special_status(imp) or dis is None or imp is None:
                return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
            c = 0
            if dis == "controlled":
                c = 1 if imp == "severe" else 0.5 if imp == "moderate" else 0
            elif dis == "uncontrolled":
                c = 1 if imp == "severe" else 0.5 if imp == "moderate" else 0.5
            worst = max(worst, c)
        return {"coeff": worst, "status": "ok",
                "basis": "هیچ عضو بیماری مزمن جدی مؤثر ندارد." if worst == 0 else "مبتنی بر شدیدترین وضعیت بیماری و اثر آن."}

    if ind_id == "A2":
        if not members:
            return {"status": "incomplete", "basis": "هیچ عضوی ثبت نشده است."}
        worst, all_ans, _ = _worst_member(a, members, "A2_limit",
            lambda v: 1 if v == "unmet" else 0.5 if v == "supported" else 0 if v == "none" else None)
        if worst is None or not all_ans:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        return {"coeff": worst, "status": "ok",
                "basis": "محدودیت پایدار با نیاز تأمین‌نشده." if worst == 1 else "محدودیت با کمک تأمین‌شده." if worst == 0.5 else "محدودیت عملکردی ثبت نشده."}

    if ind_id == "A3":
        if not members:
            return {"status": "incomplete", "basis": "هیچ عضوی ثبت نشده است."}
        worst, all_ans, _ = _worst_member(a, members, "A3_treatment",
            lambda v: 1 if v == "no_access" else 0.5 if v == "scheduled" else 0 if v == "none" else None)
        if worst is None or not all_ans:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        return {"coeff": worst, "status": "ok",
                "basis": "درمان ضروری بدون دسترسی." if worst == 1 else "درمان در نوبت یا با تأخیر." if worst == 0.5 else "درمان ضروری انجام‌نشده ثبت نشده."}

    if ind_id == "A4":
        v = _get(a, "A4_burden")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        effects = _str_list(_get(a, "A4_effects"))
        if v == "severe" or len(effects) >= 2:
            return {"coeff": 1, "status": "ok", "basis": "فشار سنگین هزینه درمان." if v == "severe" else "بدهی/فروش دارایی ناشی از هزینه درمان."}
        if v == "manageable" or len(effects) == 1:
            return {"coeff": 0.5, "status": "ok", "basis": "فشار قابل مدیریت یا یک اثر جانبی."}
        if v == "low":
            return {"coeff": 0, "status": "ok", "basis": "فشار معنادار هزینه درمان گزارش نشده."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "A5":
        if not members:
            return {"status": "incomplete", "basis": "هیچ عضوی ثبت نشده است."}
        worst, all_ans, _ = _worst_member(a, members, "A5_cover",
            lambda v: 1 if v == "none" else 0.5 if v == "barriers" else 0 if v == "effective" else None)
        if worst is None or not all_ans:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        return {"coeff": worst, "status": "ok",
                "basis": "عضو بدون پوشش بیمه‌ای." if worst == 1 else "پوشش با مانع." if worst == 0.5 else "پوشش معتبر با دسترسی عملی."}

    if ind_id == "A6":
        exp = _str_list(_get(a, "A6_exp"))
        now = _get(a, "A6_now")
        if _special_status(_get(a, "A6_exp")):
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        if now is None:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        coeff = min(0.25 * len(exp), 1)
        if "hunger" in exp:
            coeff = max(coeff, 0.75)
        names = {"worry": "نگرانی از اتمام غذا", "variety": "کاهش تنوع غذا",
                 "quantity": "کاهش مقدار غذا", "mealskip": "حذف وعده", "hunger": "گرسنگی"}
        basis = (f"هیچ تجربه‌ای ثبت نشده. دسترسی فعلی: {'موجود' if now else 'ناموجود'}." if not exp
                 else f"تجربه‌ها: {', '.join(names.get(e, e) for e in exp)}. دسترسی: {'موجود' if now else 'ناموجود'}. آستانه‌ها نیازمند تصویب.")
        return {"coeff": coeff, "status": "ok", "pendingApproval": True, "basis": basis}

    if ind_id == "A7":
        v = _get(a, "A7_disrupt")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": "داده حساس — پاسخ نیازمند بررسی است."}
        danger = _str_list(_get(a, "A7_danger"))
        if v == "severe":
            return {"coeff": 1, "status": "ok", "basis": "اختلال شدید عملکرد خانوار."}
        if v == "moderate":
            return {"coeff": 0.5, "status": "ok", "basis": "اختلال متوسط عملکرد."}
        if v == "none" and not danger:
            return {"coeff": 0, "status": "ok", "basis": "اختلال یا خطر ثبت نشده."}
        if v == "none" and danger:
            return {"coeff": 0.5, "status": "ok", "basis": "اختلال ثبت نشده ولی نشانه خطر ثبت شده — نیازمند بررسی محرمانه."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    # ─── بُعد B: آموزش ───
    if ind_id == "B1":
        rel = [m for m in members if m.get("schoolAge") or (isinstance(m.get("age"), (int, float)) and 6 <= m["age"] <= 18)]
        if not rel:
            return {"coeff": 0, "status": "ok", "basis": "عضو در سن آموزش اجباری ثبت نشده؛ ضریب صفر صحیح است."}
        worst, all_ans, _ = _worst_member(a, rel, "B1_status",
            lambda v: 1 if v in ("dropped", "never") else 0.5 if v == "interrupted" else 0 if v == "attending" else None)
        if worst is None or not all_ans:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        return {"coeff": worst, "status": "ok", "pendingApproval": True,
                "basis": "ترک تحصیل یا عدم ثبت‌نام." if worst == 1 else "وقفه تحصیلی." if worst == 0.5 else "ثبت‌نام و حضور فعال."}

    if ind_id == "B2":
        rel = [m for m in members if m.get("schoolAge") or (isinstance(m.get("age"), (int, float)) and 6 <= m["age"] <= 18)]
        if not rel:
            return {"coeff": 0, "status": "ok", "basis": "عضو در سن آموزش ثبت نشده."}
        worst = 0
        answered = True
        for m in rel:
            risks = _str_list(_get_m(a, "B2_risks", m["id"]))
            if _get_m(a, "B2_risks", m["id"]) is None:
                answered = False
            has_cl = "child_labor" in risks or "forced_care" in risks
            n = len([r for r in risks if r != "none"])
            if has_cl:
                c = 1 if n >= 2 else 0.5
            elif n >= 3:
                c = 1
            elif n >= 1:
                c = 0.5
            else:
                c = 0
            worst = max(worst, c)
        if not answered:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        return {"coeff": worst, "status": "ok",
                "basis": "عامل خطر ثبت نشده." if worst == 0 else "مبتنی بر تعداد و نوع عوامل خطر."}

    if ind_id == "B3":
        v = _get(a, "B3_lit")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "cannot":
            return {"coeff": 1, "status": "ok", "basis": "ناتوانی در امور پایه نوشتاری بدون کمک."}
        if v == "with_help":
            return {"coeff": 0.5, "status": "ok", "basis": "انجام امور با کمک دیگران."}
        if v == "full":
            return {"coeff": 0, "status": "ok", "basis": "توانایی انجام امور پایه."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "B4":
        v = _get(a, "B4_barriers")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "serious":
            return {"coeff": 1, "status": "ok", "basis": "مانع جدی حل‌نشده."}
        if v == "resolvable":
            return {"coeff": 0.5, "status": "ok", "basis": "مانع قابل حل."}
        if v == "none":
            return {"coeff": 0, "status": "ok", "basis": "مانع واقعی ثبت نشده."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "B5":
        v = _get(a, "B5_digital")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "missing":
            return {"coeff": 1, "status": "ok", "basis": "نیاز به ابزار دیجیتال بدون ابزار قابل استفاده."}
        if v == "insufficient":
            return {"coeff": 0.5, "status": "ok", "basis": "ابزار ناکافی یا اشتراک."}
        if v in ("adequate", "no_need"):
            return {"coeff": 0, "status": "ok", "basis": "ابزار کافی یا نیازی نیست." if v == "adequate" else "نیاز واقعی ثبت نشده."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "B6":
        if not members:
            return {"status": "incomplete", "basis": "هیچ عضوی ثبت نشده است."}
        worst, all_ans, _ = _worst_member(a, members, "B6_need",
            lambda v: 1 if v == "unmet" else 0.5 if v in ("needs_assessment", "served") else 0 if v == "none" else None)
        if worst is None or not all_ans:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        return {"coeff": worst, "status": "ok",
                "basis": "نیاز تأییدشده بدون خدمت." if worst == 1 else "نیاز با خدمت یا در ارزیابی." if worst == 0.5 else "نیاز ویژه ثبت نشده."}

    if ind_id == "B7":
        v = _get(a, "B7_path")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "no_capability":
            return {"coeff": 1, "status": "ok", "basis": "واجد شرایط بدون مسیر آموزش/مهارت."}
        if v == "interested_no_path":
            return {"coeff": 0.5, "status": "ok", "basis": "علاقه‌مندی بدون مسیر فعال."}
        if v == "active":
            return {"coeff": 0, "status": "ok", "basis": "مسیر فعال آموزش/مهارت."}
        if v == "no_eligible":
            return {"coeff": 0, "status": "ok", "basis": "فاقد عضو واجد شرایط؛ ضریب صفر صحیح است."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    # ─── بُعد C: مسکن ───
    if ind_id == "C1":
        place = _get(a, "C1_place")
        evict = _get(a, "C1_eviction")
        if _special_status(place) or _special_status(evict):
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        if place == "nonresidential":
            return {"coeff": 1, "status": "ok", "basis": "محل خواب غیرمسکونی/فضای عمومی."}
        if place == "temporary":
            return {"coeff": 0.5, "status": "ok", "basis": "سکونت موقت یا مرکز نگهداری."}
        if place == "stable" and evict == "imminent":
            return {"coeff": 0.5, "status": "ok", "basis": "سکونت پایدار ولی اخطار تخلیه قریب‌الوقوع."}
        if place == "stable" and evict == "credible":
            return {"coeff": 0.5, "status": "ok", "basis": "سکونت پایدار ولی اخطار/خطر تخلیه."}
        if place == "stable" and evict == "no":
            return {"coeff": 0, "status": "ok", "basis": "محل خواب پایدار بدون اخطار."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "C2":
        issues = _str_list(_get(a, "C2_issues"))
        if _get(a, "C2_issues") is None:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        if "uninhabitable" in issues or "structural" in issues:
            return {"coeff": 1, "status": "ok", "basis": "خطر بحرانی سازه یا غیرقابل سکونت."}
        if len(issues) >= 2:
            return {"coeff": 0.5, "status": "ok", "basis": f"دو یا چند نقص: {', '.join(issues)}."}
        if len(issues) == 1:
            return {"coeff": 0.5, "status": "ok", "basis": f"یک نقص: {issues[0]}."}
        return {"coeff": 0, "status": "ok", "basis": "نقص بحرانی ثبت نشده."}

    if ind_id == "C3":
        v = _get(a, "C3_right")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "risk":
            return {"coeff": 1, "status": "ok", "basis": "خطر جدی ازدست‌دادن مسکن."}
        if v == "ambiguous":
            return {"coeff": 0.5, "status": "ok", "basis": "حق سکونت مبهم."}
        if v == "clear":
            return {"coeff": 0, "status": "ok", "basis": "حق سکونت روشن."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "C4":
        rooms = _num(_get(a, "C4_rooms"))
        safe = _get(a, "C4_safesleep")
        if rooms is None or rooms < 0:
            return {"status": "incomplete", "basis": "تعداد اتاق ثبت نشده."}
        if _special_status(safe):
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        if safe == "none":
            return {"coeff": 1, "status": "ok", "pendingApproval": True, "basis": "فضای خواب ایمن وجود ندارد."}
        n = max(len(members), 1)
        ppr = n / max(rooms, 1)
        if ppr <= 1.5:
            base = 0
        elif ppr <= 2.5:
            base = 0.25
        elif ppr <= 3.5:
            base = 0.5
        elif ppr <= 5:
            base = 0.75
        else:
            base = 1
        coeff = max(base, 0.5) if safe == "partial" else base
        return {"coeff": coeff, "status": "ok", "pendingApproval": True,
                "basis": f"{n} عضو در {rooms} اتاق (نفر بر اتاق ≈ {ppr:.2f})؛ فضای خواب: {'برای همه' if safe == 'all' else 'جزئی'}. آستانه‌ها نیازمند تصویب."}

    if ind_id == "C5":
        keys = ["C5_water", "C5_elec", "C5_cook"]
        answered = True
        worst = 0
        for k in keys:
            v = _get(a, k)
            if _special_status(v) or v is None:
                answered = False
            if v == "off":
                worst = max(worst, 1)
            elif v == "unstable":
                worst = max(worst, 0.5)
        if not answered:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        return {"coeff": worst, "status": "ok",
                "basis": "قطع حیاتی خدمات." if worst == 1 else "قطعی‌های مکرر." if worst == 0.5 else "دسترسی پایدار."}

    if ind_id == "C6":
        v = _get(a, "C6_san")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "unsafe_missing":
            return {"coeff": 1, "status": "ok", "basis": "سرویس/حمام ناسالم یا مفقود."}
        if v == "shared_minor":
            return {"coeff": 0.5, "status": "ok", "basis": "مشترک یا نقص جزئی."}
        if v == "good":
            return {"coeff": 0, "status": "ok", "basis": "سرویس بهداشتی قابل استفاده و بهداشتی."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "C7":
        missing = _str_list(_get(a, "C7_missing"))
        impact = _get(a, "C7_impact")
        if _get(a, "C7_missing") is None:
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        if impact == "disruptive" or len(missing) >= 3:
            return {"coeff": 1, "status": "ok", "basis": f"فقدان {len(missing)} وسیله با اختلال جدی." if len(missing) >= 3 else "فقدان وسیله با اختلال جدی."}
        if impact == "minor" or len(missing) >= 1:
            return {"coeff": 0.5, "status": "ok", "basis": f"فقدان وسایل: {', '.join(missing) or '—'} با اثر جزئی."}
        if impact == "none" and not missing:
            return {"coeff": 0, "status": "ok", "basis": "وسایل ضروری موجود و سالم."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "C8":
        household = hh.get("household", {}) or {}
        rent = _num(household.get("monthlyRent")) or 0
        charge = _num(household.get("monthlyCharge")) or 0
        bills = _num(household.get("monthlyBills")) or 0
        housing = rent + charge + bills  # ودیعه جدا
        reliable = sum(s.get("monthlyAmount", 0) or 0 for s in hh.get("incomeSources", [])
                       if s.get("continuity") == "regular" and s.get("reliability") == "reliable")
        pl = household.get("povertyLine") or {}
        pl_valid = bool(pl and pl.get("monthlyPerCapita") and pl["monthlyPerCapita"] > 0 and pl.get("status") != "invalid")
        arrears_sev = _get(a, "C8_arrears_severity")
        if _special_status(arrears_sev):
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        if arrears_sev is None:
            return {"status": "incomplete", "basis": "وضعیت معوقات ثبت نشده."}
        denom = reliable if reliable > 0 else (pl["monthlyPerCapita"] * max(len(members), 1) if pl_valid else None)
        if denom is None or denom <= 0:
            return {"status": "incomplete", "basis": "منبع قابل اتکا صفر و خط فقر معتبر ثبت نشده؛ نتیجه غیرنهایی."}
        ratio = housing / denom
        if ratio < 0.25:
            coeff = 0
        elif ratio < 0.4:
            coeff = 0.25
        elif ratio < 0.55:
            coeff = 0.5
        elif ratio < 0.7:
            coeff = 0.75
        else:
            coeff = 1
        if arrears_sev == "significant":
            coeff = max(coeff, 0.75)
        elif arrears_sev == "minor":
            coeff = max(coeff, 0.5)
        basis = (f"هزینه مسکن {housing:.0f} بر مبنای {'منابع قابل اتکا' if reliable > 0 else 'خط فقر'}؛ "
                 f"نسبت ≈ {ratio:.2f}؛ معوقه: {'ندارد' if arrears_sev == 'none' else 'جزئی' if arrears_sev == 'minor' else 'معنادار'}. "
                 f"ودیعه در محاسبه لحاظ نشده.")
        return {"coeff": coeff, "status": "ok", "pendingApproval": True, "basis": basis}

    if ind_id == "C9":
        v = _get(a, "C9_access")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "serious":
            return {"coeff": 1, "status": "ok", "basis": "مانع پایدار و جدی دسترسی."}
        if v == "manageable":
            return {"coeff": 0.5, "status": "ok", "basis": "دسترسی با بار قابل مدیریت."}
        if v == "adequate":
            return {"coeff": 0, "status": "ok", "basis": "دسترسی مناسب."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    # ─── بُعد D: معیشت ───
    if ind_id == "D1":
        no_provider = _get(a, "D1_no_provider")
        if no_provider is True:
            return {"coeff": 1, "status": "ok", "basis": "خانوار بدون تأمین‌کننده با درآمد فعال."}
        provider = next((m for m in members if m.get("isMainProvider")), None)
        if not provider:
            return {"status": "incomplete", "basis": "تأمین‌کننده اصلی مشخص نشده."}
        cont = _get_m(a, "D1_continuity", provider["id"])
        ability = _get_m(a, "D1_ability", provider["id"])
        seasonal = _get_m(a, "D1_seasonal", provider["id"]) is True
        if _special_status(cont) or _special_status(ability):
            return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}
        if cont == "stable":
            return {"coeff": 0, "status": "ok", "basis": "درآمد مستمر."}
        if cont == "irregular":
            return {"coeff": 0.5, "status": "ok", "basis": "ناپایداری درآمد احرازشده."}
        if cont == "none":
            if ability == "unable":
                return {"coeff": 1, "status": "ok", "basis": "بدون درآمد و ناتوانی از کار."}
            if seasonal:
                return {"coeff": 0.5, "status": "ok", "basis": "قطع موقت در فعالیت فصلی."}
            return {"coeff": 1, "status": "ok", "basis": "بدون درآمد فعال."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "D2":
        provider_id = next((m["id"] for m in members if m.get("isMainProvider")), None)
        eligible = [m for m in members if m["id"] != provider_id and m.get("employmentStatus") == "unemployed_seeking"]
        if not members:
            return {"status": "incomplete", "basis": "هیچ عضوی ثبت نشده."}
        n = len(eligible)
        coeff = 0 if n == 0 else 0.5 if n == 1 else 1
        return {"coeff": coeff, "status": "ok",
                "basis": f"فاقد عضو جویای کار؛ ضریب صفر صحیح." if n == 0 else f"{n} عضو جویای کار (غیر تأمین‌کننده)."}

    if ind_id == "D3":
        household = hh.get("household", {}) or {}
        pl = household.get("povertyLine") or {}
        pl_valid = bool(pl and pl.get("monthlyPerCapita") and pl["monthlyPerCapita"] > 0 and pl.get("source") and pl.get("status") != "invalid")
        if not pl_valid:
            return {"status": "incomplete", "basis": "خط فقر معتبر ثبت نشده؛ نتیجه D3 غیرنهایی."}
        reliable = sum(s.get("monthlyAmount", 0) or 0 for s in hh.get("incomeSources", [])
                       if s.get("continuity") == "regular" and s.get("reliability") == "reliable")
        n = max(len(members), 1)
        per_capita = reliable / n
        ratio = per_capita / pl["monthlyPerCapita"]
        if ratio >= 1.2:
            coeff = 0
        elif ratio >= 0.8:
            coeff = 0.25
        elif ratio >= 0.6:
            coeff = 0.5
        elif ratio >= 0.3:
            coeff = 0.75
        else:
            coeff = 1
        basis = (f"درآمد قابل اتکا {reliable:.0f} تومان برای {n} نفر (سرانه ≈ {per_capita:.0f}) "
                 f"نسبت به خط فقر {pl['monthlyPerCapita']:.0f}؛ نسبت ≈ {ratio:.2f}. برش‌ها پیشنهادی.")
        return {"coeff": coeff, "status": "ok", "pendingApproval": True, "basis": basis}

    # ─── بُعد E: مراقبت ───
    if ind_id == "E1":
        v = _get(a, "E1_outlook")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "none":
            return {"coeff": 1, "status": "ok", "basis": "بدون مسیر واقعی حفظ معاش."}
        if v == "uncertain":
            return {"coeff": 0.5, "status": "ok", "basis": "مسیر نامطمئن."}
        if v == "clear":
            return {"coeff": 0, "status": "ok", "basis": "مسیر محتمل حفظ معاش."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "E2":
        needing = [m for m in members if m.get("needsCare")]
        support = _get(a, "E2_support")
        s = _special_status(support)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if not needing:
            return {"coeff": 0, "status": "ok", "basis": "عضو نیازمند مراقبت ثبت نشده."}
        if support == "none":
            return {"coeff": 1, "status": "ok", "basis": "نیاز مراقبتی بدون مراقب."}
        if support == "partial":
            return {"coeff": 0.5, "status": "ok", "basis": "بار سنگین با پشتیبانی ناکافی."}
        if support == "adequate":
            return {"coeff": 0, "status": "ok", "basis": "نیاز مراقبتی تأمین‌شده."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "E3":
        v = _get(a, "E3_support")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "none":
            return {"coeff": 1, "status": "ok", "basis": "فرد/نهاد مؤثر در بحران وجود ندارد."}
        if v == "sporadic":
            return {"coeff": 0.5, "status": "ok", "basis": "حمایت موردی و ناپایدار."}
        if v == "reliable":
            return {"coeff": 0, "status": "ok", "basis": "حمایت مستمر و قابل اتکا."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    if ind_id == "E4":
        v = _get(a, "E4_barrier")
        s = _special_status(v)
        if s:
            return {"status": s, "basis": _INCOMPLETE_BASIS}
        if v == "blocking":
            return {"coeff": 1, "status": "ok", "basis": "مانع مسدودکننده خدمت حیاتی."}
        if v == "in_progress":
            return {"coeff": 0.5, "status": "ok", "basis": "مانع با راه‌حل در جریان."}
        if v == "none":
            return {"coeff": 0, "status": "ok", "basis": "مانع مؤثر ثبت نشده."}
        return {"status": "incomplete", "basis": _INCOMPLETE_BASIS}

    return {"status": "incomplete", "basis": "شاخص ناشناخته."}

def compute_assessment(hh: Dict) -> Dict:
    """محاسبه کل ارزیابی — port از computeAssessment در engine.ts"""
    a = hh.get("answers", {}) or {}
    indicators = []
    for dim_id in DIMENSIONS:
        for ind_id in INDICATORS_BY_DIM[dim_id]:
            out = resolve_indicator(ind_id, a, hh)
            indicators.append({
                "id": ind_id, "dimension": dim_id, "weight": WEIGHTS[ind_id],
                "coeff": out.get("coeff"),
                "score": WEIGHTS[ind_id] * out["coeff"] if out.get("coeff") is not None else None,
                "status": out["status"], "basis": out["basis"],
                "pendingApproval": out.get("pendingApproval", False),
            })

    dimensions = []
    for dim_id, dim_meta in DIMENSIONS.items():
        items = [i for i in indicators if i["dimension"] == dim_id]
        score = sum(i.get("score") or 0 for i in items)
        complete = all(i["status"] == "ok" for i in items)
        dimensions.append({
            "id": dim_id, "title": dim_meta["title"], "cap": dim_meta["cap"],
            "score": score, "pct": min(100, score / dim_meta["cap"] * 100) if dim_meta["cap"] > 0 else 0,
            "complete": complete,
        })

    finalized = [i for i in indicators if i["status"] == "ok"]
    partial_sum = sum(i.get("score") or 0 for i in finalized)
    completeness = round(len(finalized) / len(indicators) * 100) if indicators else 0
    all_ok = len(finalized) == len(indicators)

    result = {
        "indicators": indicators, "dimensions": dimensions,
        "partialSum": partial_sum, "status": "final" if all_ok else "nonfinal",
        "completeness": completeness, "finalizedCount": len(finalized),
    }
    if all_ok:
        total = min(partial_sum, TOTAL_CAP)
        result["total"] = total
        result["totalPct"] = total / TOTAL_CAP * 100
        lv = level_of(total)
        if lv:
            result["level"] = {"index": lv["index"], "label": lv["label"], "min": lv["min"], "max": lv["max"]}
    return result

def suggest_flags(hh: Dict) -> List[Dict]:
    """پیشنهاد خودکار R1-R9"""
    out = []
    members = hh.get("members", []) or []
    a = hh.get("answers", {}) or {}

    def add(code, title, detail, strict=False):
        out.append({"code": code, "title": title, "detail": detail,
                    "suggested": True, "confidentiality": "strict" if strict else "restricted"})

    # R1
    for m in members:
        if _get_m(a, "A3_treatment", m["id"]) == "no_access" and _get_m(a, "A3_urgent", m["id"]) is True:
            add("R1", "خطر جانی یا فوریت پزشکی", f"{m.get('firstName', '')}: درمان ضروری بدون دسترسی با فوریت.")
            break
    # R2
    if _get(a, "C1_place") == "nonresidential" or _get(a, "C1_eviction") == "imminent":
        add("R2", "بی‌خانمانی یا اخطار تخلیه قریب‌الوقوع", "بر اساس پاسخ‌های بخش مسکن.")
    # R3
    for m in members:
        if _get_m(a, "A_malnut", m["id"]) is True:
            add("R3", "سوءتغذیه کودک یا نیاز تغذیه‌ای ویژه", f"{m.get('firstName', '')}: نیازمند بررسی.")
            break
    # R4
    for m in members:
        risks = _str_list(_get_m(a, "B2_risks", m["id"]))
        if "child_labor" in risks or (isinstance(m.get("age"), (int, float)) and m["age"] < 15 and m.get("employmentStatus") == "employed"):
            add("R4", "کودک کار یا کودک در خطر", f"{m.get('firstName', '')}: اثر کار بر تحصیل.")
            break
    # R5
    if _str_list(_get(a, "A7_danger")):
        add("R5", "خشونت یا خطر آسیب به خود/دیگران", "نشانه خطر — نیازمند تأیید تخصصی محرمانه.", True)
    # R6
    needing_care = [m for m in members if m.get("needsCare")]
    caregiver = next((m for m in members if m.get("isMainCaregiver")), None)
    if needing_care and not caregiver:
        add("R6", "فقدان مراقب برای فرد وابسته", f"{len(needing_care)} عضو نیازمند مراقبت بدون مراقب.")
    # R7
    if _get(a, "A6_now") is False or _get(a, "C5_water") == "off" or _get(a, "C5_elec") == "off" or _get(a, "C5_cook") == "off":
        add("R7", "قطع خدمت حیاتی", "قطع دسترسی به غذا/آب/برق بدون جایگزین.")
    # R8
    if _get(a, "E4_barrier") == "blocking":
        add("R8", "مانع حقوقی/اداری مسدودکننده", str(_get(a, "E4_service") or "نیازمند بررسی."))
    # R9
    if detect_conflicts(hh):
        add("R9", "تناقض یا شبهه جدی در داده", "مغایرت نیازمند راستی‌آزمایی.")
    return out

def detect_conflicts(hh: Dict) -> List[str]:
    """۴ قاعده خودکار کشف تناقض"""
    out = []
    a = hh.get("answers", {}) or {}
    h = hh.get("household", {}) or {}
    nonresidential = (h.get("dwellingType") in ("غیرمسکونی", "خودرو/فضای عمومی") or _get(a, "C1_place") == "nonresidential")
    if nonresidential and _get(a, "C1_place") == "stable":
        out.append("نوع محل سکونت «غیرمسکونی» ثبت شده ولی وضعیت محل خواب «پایدار» است.")
    if h.get("tenureType") == "مالک" and (h.get("monthlyRent") or 0) > 0:
        out.append("نوع حق سکونت «مالک» است ولی اجاره مثبت ثبت شده.")
    pl = h.get("povertyLine") or {}
    if pl and pl.get("status") == "verified" and not pl.get("source"):
        out.append("خط فقر «تأییدشده» ثبت شده ولی منبع ثبت نشده.")
    members = hh.get("members", []) or []
    has_effective = any(_get_m(a, "A5_cover", m["id"]) == "effective" for m in members)
    no_access = any(_get_m(a, "A3_treatment", m["id"]) == "no_access" for m in members)
    if has_effective and no_access:
        out.append("پوشش بیمه‌ای مؤثر ثبت شده ولی درمان ضروری بدون دسترسی است.")
    return out

def auto_quality_issues(hh: Dict) -> List[Dict]:
    """مسائل کیفیت داده خودکار"""
    out = []
    a = hh.get("answers", {}) or {}
    for key, val in a.items():
        scope = key.split("#")[0]
        if val == SPECIAL_ANSWERS["DONT_KNOW"]:
            out.append({"scope": scope, "type": "special_answer", "description": f"پاسخ «نمی‌دانم» برای {scope}."})
        elif val == SPECIAL_ANSWERS["REFUSE"]:
            out.append({"scope": scope, "type": "special_answer", "description": f"پاسخ «مایل نیستم» برای {scope}."})
        elif val == SPECIAL_ANSWERS["NEED_REVIEW"]:
            out.append({"scope": scope, "type": "special_answer", "description": f"پاسخ «نیازمند بررسی» برای {scope}."})
    for c in detect_conflicts(hh):
        out.append({"type": "conflict", "description": c})
    if not hh.get("members"):
        out.append({"type": "missing", "description": "هیچ عضوی ثبت نشده."})
    return out

def validate_weights() -> Dict:
    """آزمون اعتبارسنجی وزن‌ها"""
    total = 0
    per_dim = {}
    for d in DIMENSIONS:
        s = sum(WEIGHTS[i] for i in INDICATORS_BY_DIM[d])
        total += s
        per_dim[d] = {"sum": s, "cap": DIMENSIONS[d]["cap"], "ok": s == DIMENSIONS[d]["cap"]}
    return {"ok": total == TOTAL_CAP, "total": total, "perDim": per_dim}

def indicator_title(ind_id: str) -> str:
    return INDICATOR_TITLES.get(ind_id, ind_id)

# ═══════════════════════════════════════════════════════════
# ۷) سازگاری با API قدیمی CDI (legacy aliases)
# ═══════════════════════════════════════════════════════════
# ساخت INDICATORS dict برای backward compat با main.py قدیمی
INDICATORS = {}
for _dim_id, _ind_ids in INDICATORS_BY_DIM.items():
    for _ind_id in _ind_ids:
        INDICATORS[_ind_id] = {
            "dim": _dim_id,
            "weight": WEIGHTS[_ind_id],
            "title": INDICATOR_TITLES[_ind_id],
            "scale": scale_of(_ind_id),
            "level": "member" if _ind_id in ("A1","A2","A3","A5","B1","B2","B6","D1") else "household",
            "definition": INDICATOR_TITLES[_ind_id],
            "red_flags": [],
            "questions": [],
        }

DEPRIVATION_LEVELS = [{"code": f"L{i['index']-1}", **i} for i in LEVELS]
RED_FLAGS = FLAG_DEFS
REFERRAL_PATHS_DICT = {p["id"]: p for p in REFERRAL_PATHS}
AI_RED_LINES = [
    "هیچ خروجی الگوریتمی به‌تنهایی تصمیم نهایی نیست.",
    "شدت محرومیت مستقیم پرسیده نمی‌شود.",
    "پاسخ‌های خاص هرگز به امتیاز تبدیل نمی‌شوند.",
    "فقدان داده ≠ نبود محرومیت.",
    "پرچم‌های R امتیاز اضافه نمی‌کنند.",
    "ودیعه هرگز در هزینه مسکن لحاظ نمی‌شود.",
    "ارجاعات منسوخ D4, D5, D6, E6 تولید نمی‌شوند.",
]
SEVERITY_OPTIONS = [
    {"value": 0, "label": "فاقد محرومیت", "coeff": 0},
    {"value": 1, "label": "متوسط", "coeff": 0.5},
    {"value": 2, "label": "شدید", "coeff": 1},
]

def compute_emmpi(answers, members=None, household=None, income_sources=None, poverty_line=None):
    """سازگاری با API قدیمی — می‌سازد Assessment و compute_assessment می‌زند"""
    hh = {
        "answers": answers,
        "members": members or [],
        "household": household or {},
        "incomeSources": income_sources or [],
    }
    if poverty_line:
        hh["household"]["povertyLine"] = poverty_line
    result = compute_assessment(hh)
    result["ruleSetVersion"] = RULE_SET["fullId"]
    result["computedAt"] = datetime.now().isoformat()
    result["flags"] = suggest_flags(hh)
    result["qualityIssues"] = auto_quality_issues(hh)
    result["aiRedLines"] = AI_RED_LINES
    result["pendingApprovalItems"] = [p["item"] for p in PENDING_APPROVALS]
    return result

# توابع legacy برای main.py
def get_indicator_list_by_dim(dim_id=None):
    if dim_id:
        return [{"id": k, **INDICATOR_TITLES} for k in INDICATORS_BY_DIM.get(dim_id, [])]
    return {d: [{"id": k, "title": INDICATOR_TITLES[k], "weight": WEIGHTS[k],
                 "scale": scale_of(k), "dim": d}
                for k in inds] for d, inds in INDICATORS_BY_DIM.items()}

def get_indicator(ind_id):
    return {"id": ind_id, "title": INDICATOR_TITLES.get(ind_id), "weight": WEIGHTS.get(ind_id)}

def suggest_assistant(result):
    flags = [f["code"] for f in result.get("flags", [])]
    score = result.get("total") or 0
    if "R5" in flags:
        return {"role": "swclinic", "reason": "پرچم R5"}
    if "R1" in flags or "R2" in flags:
        return {"role": "worker", "reason": "پرچم سخت‌گیرانه"}
    if score >= 450:
        return {"role": "caseworker", "reason": "امتیاز بالا"}
    return {"role": "assistant", "reason": "پایش"}

SAMPLE_ASSISTANTS = []
ASSISTANT_ROLES = {"assistant": "همیار"}
MATCH_CRITERIA = {}
COMPONENT_META = {d: {"label": DIMENSIONS[d]["title"]} for d in DIMENSIONS}
def get_component_meta(d): return COMPONENT_META.get(d, {"label": d})
def get_referral_paths_visual(): return REFERRAL_PATHS
def match_assistants(household, available=None): return available or []
def compute_citizen_profile(sd_data, indicators_data, emmpi_result=None): return {"honesty_level": "H1", "match_ratio": 1.0}
SD_TO_EMPI_FULL = {}
SD_ANSWER_LABELS = {}
EMPI_SEVERITY_LABELS = {0: "فاقد محرومیت", 1: "متوسط", 2: "شدید"}
HONESTY_LEVELS = {"H1": {"label": "صادق"}}

# ═══════════════════════════════════════════════════════════
# ۸) خودآزمایی
# ═══════════════════════════════════════════════════════════
def self_test():
    wv = validate_weights()
    assert wv["total"] == 1010, f"جمع وزن‌ها باید ۱۰۱۰ باشد: {wv['total']}"
    assert len(WEIGHTS) == 30
    # قطعیت
    answers = {"A4_burden": "severe", "A4_effects": ["debt"]}
    r1 = compute_emmpi(answers)
    r2 = compute_emmpi(answers)
    assert r1["partialSum"] == r2["partialSum"]
    return {"valid": True, "weights": wv, "determinism": "passed"}

if __name__ == "__main__":
    result = self_test()
    print("آزمون موتور EM-MPI:")
    print(f"  جمع وزن‌ها: {result['weights']['total']}")
    print(f"  تعداد شاخص‌ها: {len(WEIGHTS)}")
    print(f"  قطعیت: {result['determinism']}")
    print(f"  اعتبارسنجی: {'PASS' if result['valid'] else 'FAIL'}")
    for d, info in result["weights"]["perDim"].items():
        mark = "✓" if info["ok"] else "⚠"
        print(f"  بُعد {d}: {info['sum']}/{info['cap']} {mark}")
