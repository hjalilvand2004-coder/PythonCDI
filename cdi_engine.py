# -*- coding: utf-8 -*-
"""
موتور قواعد CDI — نسخهٔ هماهنگ با سند Emdad_sanadHemayt0005

افزوده‌ها در این نسخه:
- امتیاز PEH (اولویت اجرایی خانوار) با ۶ مؤلفه و فرمول سند (بند ۲ـ۵)
- امتیاز PIM (اولویت مداخله) برای هر محور با ۶ مؤلفه (بند ۲ـ۱۰)
- تبدیل PIM به رتبه A-E (بند ۲ـ۱۰)
- امتیاز PES در صف خدمت با ۴ مؤلفه (بند ۲ـ۱۵)
- سبد مداخله با گلوگاه، خدمت شناسه‌دار، رتبه A-E، مسئول، پیش‌نیاز، مهلت، شاخص پیگیری، وضعیت (بند ۲ـ۸)
- ۹ خانواده صف خدمت (بند ۲ـ۱۳)
- روابط ۵گانهٔ اقدامات (بند ۲ـ۱۱)
- قواعد حل تساوی در رتبه خانوار و صف خدمت (بندهای ۲ـ۷ و ۲ـ۱۷)
- قواعد کنترلی و ممنوعیت‌ها (بند ۲ـ۱۸)
"""
from cdi_catalog import (AXES, AXES_BY_CODE, PRIORITY_CLASSES, SEQUENCE_STEPS,
                         SEVERITY_LABELS, LAYER3_TRIGGERS, PROFILE_PARTS, AI_RED_LINES)

# نقش‌ها → سطح حلقه (بند ۳)
ROLES = {
    "household": {"label": "خانوار", "ring": 0},
    "beneficiary": {"label": "نیازمند", "ring": 0},
    "assistant": {"label": "همیار مددکار", "ring": 1},
    "rose":      {"label": "کلینیک مشاوره «رز»", "ring": 2},
    "swclinic":  {"label": "کلینیک تخصصی مددکاری", "ring": 3},
    "worker":    {"label": "مددکار خانواده کمیته امداد", "ring": 4},
    "employ":    {"label": "کارشناس اشتغال", "ring": 4},
    "manager":   {"label": "مدیر خدمت یا مقام مجاز", "ring": 4},
    "hqmanager": {"label": "مدیر ستاد مرکزی", "ring": 5},
    "admin":     {"label": "مدیر سامانه", "ring": 4},
}

# محورهای حساس (ثبت حداقلی توسط همیار ممنوع؛ ارزیابی نیازمند حلقه تخصصی)
SENSITIVE = {"CDI-1-05", "CDI-4-04", "CDI-4-07", "CDI-3-06", "CDI-3-09"}

# نقش‌های مجاز به ارزیابی کامل محورهای حساس
SENSITIVE_ASSESS_ROLES = {"worker", "swclinic", "rose", "admin"}

# دامنه کاری کلینیک رز (مشاوره‌ای) و کارشناس اشتغال
ROSE_DOMAIN = {"CDI-1-04", "CDI-2-01", "CDI-4-02", "CDI-4-04", "CDI-4-05",
               "CDI-4-06", "CDI-4-07", "CDI-5-03", "CDI-5-04", "CDI-5-09", "CDI-1-01"}
EMPLOY_DOMAIN = {"CDI-3-01", "CDI-3-02", "CDI-3-03", "CDI-3-04", "CDI-3-05",
                 "CDI-3-06", "CDI-3-08", "CDI-3-09", "CDI-5-05"}

# پرچم قرمز EM-MPI → محورهای فعال‌شونده (لایه ۱: فعال‌سازی شاخه‌ها)
REDFLAG_TO_AXES = {
    "food":         ["CDI-1-01"],
    "housing":      ["CDI-1-02"],
    "health":       ["CDI-1-03", "CDI-2-02"],
    "caregiving":   ["CDI-1-04", "CDI-4-09"],
    "safety":       ["CDI-1-05", "CDI-4-07"],
    "utilities":    ["CDI-1-06", "CDI-2-04"],
    "shock":        ["CDI-1-07", "CDI-4-08"],
    "education":    ["CDI-2-01"],
    "identity":     ["CDI-2-03", "CDI-5-07"],
    "transport":    ["CDI-2-05", "CDI-5-06"],
    "digital":      ["CDI-2-06"],
    "service_qual": ["CDI-2-07"],
    "employment":   ["CDI-3-01", "CDI-3-03", "CDI-3-05"],
    "debt":         ["CDI-3-07"],
    "insurance":    ["CDI-3-08"],
    "literacy":     ["CDI-4-01"],
    "mental":       ["CDI-4-04", "CDI-5-03"],
    "physical":     ["CDI-4-03", "CDI-3-03"],
    "motivation":   ["CDI-4-05", "CDI-4-06"],
    "network":      ["CDI-5-01", "CDI-5-02"],
    "isolation":    ["CDI-5-03"],
    "discrimination": ["CDI-5-04"],
    "geography":    ["CDI-5-06"],
    "legal":        ["CDI-5-07"],
}

# بُعد غالب EM-MPI → بُعد(های) CDI که باید کل آن‌ها فعال شود
EMDIM_TO_CDIDIMS = {
    "health":    [1, 2],
    "education": [2],
    "living":    [1, 2],
    "work":      [3],
}

SEVERITIES = ["high", "medium", "low", "none"]

P_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}

# برنامه پایش پیشنهادی بر حسب اولویت (بند ۸ـ۲ ردیف ۱۵)
MONITORING = {
    "P0": "روزانه تا کنترل خطر",
    "P1": "هفتگی",
    "P2": "هر دو هفته",
    "P3": "ماهانه",
    "P4": "سه‌ماهه / دوره‌ای",
}

STAGES = {
    1: "بحران / حفاظت",
    2: "تثبیت نیازهای حیاتی",
    3: "رفع مانع خدمات و اشتغال",
    4: "توانمندسازی و درآمد",
    5: "پایداری و تاب‌آوری",
    6: "کاهش تدریجی حمایت و خروج پایدار",
}

# ─────────────────────────────────────────────────────────────────
# ۹ خانواده صف خدمت (بند ۲ـ۱۳)
# ─────────────────────────────────────────────────────────────────
SERVICE_QUEUE_FAMILIES = [
    {"code": "Q1", "name": "صف حفاظت و فوریت", "color": "P0",
     "services": "خدمات فوریتی: خوراک فوری، درمان فوری، در راه‌ماندگی، کفن‌ودفن، حفاظت کودک، خانواده زندانیان در بحران"},
    {"code": "Q2", "name": "صف تثبیت معیشت و حمایت پایه", "color": "P1",
     "services": "مستمری، کمک‌هزینه معیشت، حمایت موردی، لوازم ضروری، حمایت غذایی، تثبیت خانوار"},
    {"code": "Q3", "name": "صف درمان، مراقبت و سلامت", "color": "P1",
     "services": "کمک‌هزینه درمان، اتصال به بیمه، همراهی درمان، توان‌بخشی، مراقبت"},
    {"code": "Q4", "name": "صف مسکن و خدمات حیاتی", "color": "P1",
     "services": "ودیعه/اجاره، تعمیر، بازسازی، مقاوم‌سازی، ساخت/تکمیل، انشعابات آب/برق/گاز"},
    {"code": "Q5", "name": "صف دسترسی، اداری و اجتماعی", "color": "P2",
     "services": "رفع موانع هویتی، دسترسی دیجیتال، حمل‌ونقل، ارجاعات حقوقی، مشاوره خانواده"},
    {"code": "Q6", "name": "صف تحصیل، فرهنگ و رشد اجتماعی", "color": "P3",
     "services": "کمک‌هزینه تحصیلی، حمایت دانش‌آموز/دانشجو، نخبگان، اردوها، استعدادهای برتر"},
    {"code": "Q7", "name": "صف ایتام و فرزندان محسنین", "color": "P2",
     "services": "حمایت‌های اختصاصی ایتام و فرزندان محسنین با رعایت عدم تکرار و پیوند با برنامه خانوار"},
    {"code": "Q8", "name": "صف اشتغال و توانمندسازی اقتصادی", "color": "P3",
     "services": "آموزش مهارتی، مشاوره کسب‌وکار، تسهیلات اشتغال، ابزار کار، اشتغال خانگی، کارآفرینی"},
    {"code": "Q9", "name": "صف پایداری، تاب‌آوری و خروج", "color": "P4",
     "services": "بیمه، مدیریت بدهی، کاهش ریسک، شبکه‌سازی، پایش، خروج پایدار"},
]

# نگاشت محور CDI → خانواده صف خدمت (موقت؛ قابل تکمیل با cdi_catalog)
AXIS_TO_QUEUE = {
    "CDI-1-01": "Q1", "CDI-1-02": "Q4", "CDI-1-03": "Q3", "CDI-1-04": "Q3",
    "CDI-1-05": "Q1", "CDI-1-06": "Q4", "CDI-1-07": "Q9",
    "CDI-2-01": "Q6", "CDI-2-02": "Q3", "CDI-2-03": "Q5", "CDI-2-04": "Q4",
    "CDI-2-05": "Q5", "CDI-2-06": "Q5", "CDI-2-07": "Q5",
    "CDI-3-01": "Q8", "CDI-3-02": "Q8", "CDI-3-03": "Q8", "CDI-3-04": "Q8",
    "CDI-3-05": "Q8", "CDI-3-06": "Q8", "CDI-3-07": "Q9", "CDI-3-08": "Q9",
    "CDI-3-09": "Q8",
    "CDI-4-01": "Q6", "CDI-4-02": "Q5", "CDI-4-03": "Q3", "CDI-4-04": "Q3",
    "CDI-4-05": "Q5", "CDI-4-06": "Q5", "CDI-4-07": "Q1", "CDI-4-08": "Q9",
    "CDI-4-09": "Q5",
    "CDI-5-01": "Q9", "CDI-5-02": "Q9", "CDI-5-03": "Q5", "CDI-5-04": "Q5",
    "CDI-5-05": "Q8", "CDI-5-06": "Q5", "CDI-5-07": "Q5", "CDI-5-08": "Q9",
    "CDI-5-09": "Q9",
}

# ۵ نوع رابطهٔ بین اقدامات (بند ۲ـ۱۱)
ACTION_RELATIONS = [
    {"code": "prereq", "name": "پیش‌نیاز قطعی",
     "desc": "اقدام بعدی بدون اجرای این خدمت مجاز یا مؤثر نیست",
     "example": "درمان ضروری یا تثبیت مراقبت کودک پیش از ورود به اشتغال"},
    {"code": "concurrent", "name": "قابل اجرای هم‌زمان",
     "desc": "دو خدمت بدون ایجاد تعارض می‌توانند هم‌زمان اجرا شوند",
     "example": "حمایت غذایی کوتاه‌مدت همراه با فعال‌سازی بیمه"},
    {"code": "conditional", "name": "اقدام مشروط",
     "desc": "شروع اقدام منوط به تحقق شرط مشخص است",
     "example": "ابزار کار پس از احراز مهارت و بازار"},
    {"code": "alternative", "name": "اقدام جایگزین",
     "desc": "در نبود ظرفیت یا عدم تناسب، خدمت جایگزین می‌شود",
     "example": "آموزش حضوری یا غیرحضوری نزد محل سکونت"},
    {"code": "incompatible", "name": "ناسازگار یا متوقف‌شونده",
     "desc": "اجرای یک خدمت، خدمت دیگر را تا رفع مانع متوقف می‌کند",
     "example": "وام اشتغال در شرایط بدهی بحرانی یا بحران حفاظت"},
]

# ۹ معیار حل تساوی در صف خدمت (بند ۲ـ۱۷)
TIEBREAK_RULES_QUEUE = [
    "خطر بیشتر یا مهلت زمانی نزدیک‌تر",
    "وجود کودک، سالمند، بیمار یا فرد دارای معلولیت وابسته",
    "احتمال جلوگیری از آسیب برگشت‌ناپذیر",
    "نقش بیشتر خدمت در رفع گلوگاه اصلی",
    "فقدان خدمت جایگزین یا عدم دریافت خدمت مشابه",
    "مدت انتظار بیشتر در صف",
    "هزینه کمتر با اثربخشی و پایداری بیشتر",
    "رعایت تعادل جغرافیایی و جلوگیری از تمرکز غیرموجه",
    "قرعه‌کشی مستند و قابل نظارت در صورت برابری کامل",
]

# ۸ معیار حل تساوی در رتبه خانوار (بند ۲ـ۷)
TIEBREAK_RULES_HOUSEHOLD = [
    "وجود کودک، سالمند، بیمار، زن باردار یا فرد دارای معلولیت وابسته",
    "خطر یا فرصت زمان‌دار (تخلیه، درمان، ثبت‌نام، قرارداد، سررسید)",
    "احتمال آسیب برگشت‌ناپذیر در صورت تأخیر",
    "شدت و درهم‌تنیدگی گلوگاه‌های اصلی",
    "عدم دریافت خدمت مشابه یا ناکافی بودن مداخله قبلی",
    "طول مدت انتظار خانوار در صف",
    "هزینه کمتر با اثربخشی بالاتر (مشروط به برابری خطر و فوریت)",
    "تاریخ تکمیل و اعتبارسنجی نهایی پروفایل CDI",
]

# ۷ قاعدهٔ کنترلی لازم‌الاجرا (بند ۲ـ۱۸)
CONTROL_RULES = [
    "حمایت حیاتی نباید به علت آمادگی پایین خانوار به تأخیر بیفتد",
    "خدمت مشابه یا تکراری نباید بدون بررسی اثربخشی تخصیص یابد",
    "ارزان بودن خدمت، فقط در وضعیت خطر و اثربخشی برابر معیار تقدم است",
    "خانوار نباید به مسیر اشتغال یا کسب‌وکاری ناسازگار با ترجیح/سلامتش/بار مراقبتی‌اش وادار شود",
    "کاهش یا قطع حمایت و خروج، صرفاً با کاهش امتیاز EM-MPI مجاز نیست",
    "هر تغییر مهم در وضعیت خانوار باید موجب بازتنظیم امتیازها شود",
    "هوش مصنوعی و سامانه صرفاً تصمیم‌یار هستند، نه تصمیم‌گیرنده",
]


# ─────────────────────────────────────────────────────────────────
# کنترل دسترسی
# ─────────────────────────────────────────────────────────────────
def can_assess(role: str, axis_code: str) -> bool:
    """آیا این نقش اجازه ثبت ارزیابی کامل این محور را دارد؟ (ماتریس بند ۳)"""
    if role not in ROLES:
        return False
    a = AXES_BY_CODE.get(axis_code)
    if a is None:
        return False
    if role in ("worker", "admin"):
        return True
    if axis_code in SENSITIVE:
        return role in SENSITIVE_ASSESS_ROLES
    if role == "assistant":
        return True
    if role == "rose":
        return axis_code in ROSE_DOMAIN
    if role == "employ":
        return axis_code in EMPLOY_DOMAIN
    if role == "swclinic":
        return True
    return False


def alert_only(role: str, axis_code: str) -> bool:
    """همیار روی محورهای حساس فقط «هشدار + مسیر ارتباط امن» ثبت می‌کند (CDI-1-05 سند)."""
    return axis_code in SENSITIVE and role == "assistant"


def activate_axes(redflags, em_dims, extra_axes=None, worker_manual=None):
    """لایه ۱: فعال‌سازی شاخه‌ای محورها بر پایه پرچم‌های قرمز EM-MPI و ابعاد غالب."""
    active = set()
    for rf in redflags or []:
        active.update(REDFLAG_TO_AXES.get(rf, []))
    for d in em_dims or []:
        for dim in EMDIM_TO_CDIDIMS.get(d, []):
            active.update(a["code"] for a in AXES if a["dim"] == dim)
    if extra_axes:
        active.update(x for x in extra_axes if x in AXES_BY_CODE)
    # محورهای پیش‌نیاز ساختاری (همیشه فعال طبق سند)
    active.add("CDI-4-06")   # انگیزه، ترجیح و آمادگی تغییر: «در تمام اولویت‌ها باید ثبت شود»
    active.add("CDI-5-08")   # ظرفیت نهادها: «پیش‌نیاز جلوگیری از تکرار در همه Pها»
    if worker_manual:
        active.update(x for x in worker_manual if x in AXES_BY_CODE)
    return sorted(active)


def layer3_gate(state):
    """قاعده ورود به لایه سوم (بند ۴ـ۱): برمی‌گرداند (اجازه‌ورود، علل فعال)."""
    reasons = []
    if state.get("redflags"):
        reasons.append(LAYER3_TRIGGERS[0])
    if any(c in ("CDI-1-05", "CDI-4-04", "CDI-4-07") and v.get("severity") == "high"
           for c, v in state.get("answers", {}).items()):
        reasons.append(LAYER3_TRIGGERS[1])
    high_axes = [c for c, v in state.get("answers", {}).items() if v.get("severity") == "high"]
    dims_hit = {AXES_BY_CODE[c]["dim"] for c in high_axes if c in AXES_BY_CODE}
    if len(high_axes) >= 3 or len(dims_hit) >= 2:
        reasons.append(LAYER3_TRIGGERS[2])
    if any(v.get("conflict") for v in state.get("answers", {}).values()):
        reasons.append(LAYER3_TRIGGERS[3])
    if any(c in ("CDI-3-06", "CDI-3-09") and v.get("severity") in ("high", "medium")
           for c, v in state.get("answers", {}).items()):
        reasons.append(LAYER3_TRIGGERS[4])
    if state.get("repeat_crisis") or state.get("failed_intervention"):
        reasons.append(LAYER3_TRIGGERS[5])
    if state.get("family_disagreement"):
        reasons.append(LAYER3_TRIGGERS[6])
    if state.get("specialist_need"):
        reasons.append(LAYER3_TRIGGERS[7])
    if state.get("exit_ready"):
        reasons.append(LAYER3_TRIGGERS[8])
    return (len(reasons) > 0), reasons


# ─────────────────────────────────────────────────────────────────
# امتیاز PEH (بند ۲ـ۵) — فرمول ۶ مؤلفه‌ای
# PEH = 0.15×EM + 0.35×R + 0.20×F + 0.15×G + 0.10×E + 0.05×W
# ─────────────────────────────────────────────────────────────────
def compute_peh(em_input=None, result=None, state=None):
    """
    محاسبهٔ امتیاز اولویت اجرایی خانوار (PEH) از ۰ تا ۱۰۰.
    خروجی: (peh_score, breakdown_dict)
    """
    state = state or {}

    # EM: شدت اولیه محرومیت (۱۵٪) — از EM-MPI
    em_score = 30
    if em_input:
        level = em_input.get("level", "")
        level_score = {"شدید": 95, "متوسط": 65, "خفیف": 35}.get(level, 30)
        redflags_count = len(em_input.get("redflags", []))
        em_score = min(level_score + redflags_count * 2, 100)

    # R: خطر و فوریت فعال (۳۵٪) — از urgent + layer3
    r_score = 0
    if result:
        urgent_count = len(result.get("urgent", []))
        r_score = min(urgent_count * 30, 90)
        if result.get("layer3_required"):
            r_score = max(r_score, 75)

    # F: احتمال تشدید بحران (۲۰٪) — از تعارض‌ها و نقص‌ها و ریسک‌نامه
    f_score = 20
    if result:
        conflicts = len(result.get("conflicts", []))
        gaps = len(result.get("gaps", []))
        f_score = min(conflicts * 25 + gaps * 8 + 20, 100)
        if result.get("layer3_required"):
            f_score = max(f_score, 60)

    # G: شدت گلوگاه‌های اصلی (۱۵٪) — از bottlenecks
    g_score = 10
    if result and result.get("bottlenecks"):
        p_order = {"P0": 100, "P1": 75, "P2": 50, "P3": 25, "P4": 10}
        scores = [p_order.get(b.get("p"), 10) for b in result["bottlenecks"]]
        g_score = min(sum(scores) / 3, 100) if scores else 10

    # E: اثربخشی و فوریت فرصت مداخله (۱۰٪) — مقدار پیش‌فرض متوسط
    e_score = 50

    # W: انتظار و عدم دریافت خدمت (۵٪)
    w_score = 30
    if em_input and em_input.get("services_received"):
        w_score = 20  # قبلاً خدمت دریافت کرده

    peh = (0.15 * em_score) + (0.35 * r_score) + (0.20 * f_score) + (0.15 * g_score) + (0.10 * e_score) + (0.05 * w_score)
    return round(peh), {
        "em": round(em_score), "r": round(r_score), "f": round(f_score),
        "g": round(g_score), "e": round(e_score), "w": round(w_score),
        "formula": "PEH = 0.15×EM + 0.35×R + 0.20×F + 0.15×G + 0.10×E + 0.05×W",
        "weights": {"EM": 15, "R": 35, "F": 20, "G": 15, "E": 10, "W": 5},
        "components": {
            "EM": "شدت اولیه محرومیت و اولویت EM-MPI",
            "R": "خطر و فوریت فعال",
            "F": "احتمال تشدید یا بازگشت بحران",
            "G": "شدت گلوگاه‌های اصلی",
            "E": "اثربخشی و فوریت فرصت مداخله",
            "W": "انتظار و عدم دریافت خدمت مشابه",
        }
    }


# ─────────────────────────────────────────────────────────────────
# امتیاز PIM (بند ۲ـ۱۰) — برای هر اقدام
# PIM = 0.30×U + 0.25×G + 0.15×D + 0.15×I + 0.10×A + 0.05×C
# ─────────────────────────────────────────────────────────────────
def compute_pim(axis_code, answer, result=None):
    """محاسبهٔ PIM برای یک محور/اقدام از ۰ تا ۱۰۰."""
    severity = (answer or {}).get("severity", "none")

    # U: فوریت و ریسک (۳۰٪)
    u_score = {"high": 95, "medium": 70, "low": 40, "none": 10}.get(severity, 10)

    # G: نقش گلوگاهی (۲۵٪)
    is_bottleneck = False
    if result and result.get("bottlenecks"):
        is_bottleneck = any(b.get("code") == axis_code for b in result["bottlenecks"])
    g_score = 90 if is_bottleneck else 45

    # D: وابستگی و پیش‌نیازی بودن (۱۵٪) — محورهای پایه در بُعد ۱
    prerequisites_axes = {"CDI-1-01", "CDI-1-03", "CDI-1-05", "CDI-4-06", "CDI-5-08"}
    d_score = 80 if axis_code in prerequisites_axes else 45

    # I: اثربخشی مورد انتظار (۱۵٪)
    # محورهای حساس معمولاً اثربخشی بالاتری در تصمیم دارند
    i_score = 70 if axis_code in SENSITIVE else 55

    # A: آمادگی و ترجیح خانوار (۱۰٪)
    a_score = 50

    # C: ظرفیت، هزینه، عدم تکرار (۵٪)
    c_score = 55

    pim = (0.30 * u_score) + (0.25 * g_score) + (0.15 * d_score) + (0.15 * i_score) + (0.10 * a_score) + (0.05 * c_score)
    return round(pim), {
        "u": round(u_score), "g": round(g_score), "d": round(d_score),
        "i": round(i_score), "a": round(a_score), "c": round(c_score),
        "is_bottleneck": is_bottleneck,
        "formula": "PIM = 0.30×U + 0.25×G + 0.15×D + 0.15×I + 0.10×A + 0.05×C",
        "weights": {"U": 30, "G": 25, "D": 15, "I": 15, "A": 10, "C": 5},
        "components": {
            "U": "فوریت و ریسک تأخیر",
            "G": "نقش گلوگاهی",
            "D": "وابستگی و پیش‌نیازی بودن",
            "I": "اثربخشی مورد انتظار",
            "A": "آمادگی و ترجیح خانوار",
            "C": "ظرفیت، هزینه، عدم تکرار",
        }
    }


def pim_to_rank(pim_score):
    """تبدیل امتیاز PIM به رتبهٔ اقدام A تا E (بند ۲ـ۱۰)."""
    if pim_score >= 80:
        return "A"
    elif pim_score >= 65:
        return "B"
    elif pim_score >= 50:
        return "C"
    elif pim_score >= 35:
        return "D"
    else:
        return "E"


# توضیحات رتبه‌های A-E
ACTION_RANKS = {
    "A": {"title": "اقدام فوری و غیرقابل تأخیر", "deadline": "همان روز تا ۷ روز",
          "stage": "باید بی‌درنگ اجرا شود", "color": "red"},
    "B": {"title": "اقدام مقدم تثبیتی", "deadline": "حداکثر ۳۰ روز",
          "stage": "مقدم بر توانمندسازی", "color": "amber"},
    "C": {"title": "اقدام هم‌زمان یا نزدیک‌مدت", "deadline": "۳۰ تا ۶۰ روز",
          "stage": "هم‌زمان یا پس از اقدام مقدم", "color": "blue"},
    "D": {"title": "اقدام توانمندساز مؤخر", "deadline": "یک تا سه ماه",
          "stage": "مرحله توانمندسازی", "color": "green"},
    "E": {"title": "اقدام مشروط، پیشگیرانه یا مؤخر", "deadline": "پس از تحقق شرط",
          "stage": "مشروط، جایگزین یا مؤخر", "color": "purple"},
}


# ─────────────────────────────────────────────────────────────────
# امتیاز PES (بند ۲ـ۱۵) — برای صف خدمت
# PES = 0.45×PEH + 0.35×PIM + 0.10×T + 0.10×K
# ─────────────────────────────────────────────────────────────────
def compute_pes(peh_score, pim_score, time_sensitivity=50, suitability=50):
    """
    محاسبهٔ امتیاز تخصیص خدمت یا منبع (PES) از ۰ تا ۱۰۰.
    T: حساسیت زمانی (مهلت تخلیه، درمان، ثبت‌نام، ...)
    K: تناسب و قابلیت اجرا (نبود خدمت مشابه، احراز پیش‌نیاز، ظرفیت)
    """
    pes = (0.45 * peh_score) + (0.35 * pim_score) + (0.10 * time_sensitivity) + (0.10 * suitability)
    return round(pes), {
        "peh": round(peh_score), "pim": round(pim_score),
        "t": round(time_sensitivity), "k": round(suitability),
        "formula": "PES = 0.45×PEH + 0.35×PIM + 0.10×T + 0.10×K",
        "weights": {"PEH": 45, "PIM": 35, "T": 10, "K": 10},
        "components": {
            "PEH": "اولویت اجرایی خانوار",
            "PIM": "اولویت همان مداخله",
            "T": "حساسیت زمانی",
            "K": "تناسب و قابلیت اجرا",
        }
    }


# ─────────────────────────────────────────────────────────────────
# سبد مداخله (بند ۲ـ۸)
# ─────────────────────────────────────────────────────────────────
def build_intervention_basket(result, em_input=None):
    """
    ساخت سبد مدخله خانوار: زنجیره‌ای از اقدامات با رتبه A-E،
    مسئول، پیش‌نیاز، مهلت، شاخص پیگیری، وضعیت، و رابطه با سایر اقدامات.
    """
    basket = []
    if not result:
        return basket

    items_by_rank = {"A": [], "B": [], "C": [], "D": [], "E": []}

    for i in result["rows"]:
        if not i.get("p"):
            continue
        code = i["code"]
        answer = {"severity": i.get("severity"), "note": i.get("note", "")}
        pim, pim_breakdown = compute_pim(code, answer, result)
        rank = pim_to_rank(pim)

        # تشخیص رابطهٔ اقدام (موقت — با قواعد ساده)
        relation = "concurrent"
        if code in SENSITIVE:
            relation = "prereq"  # محورهای حساس معمولاً پیش‌نیاز دارند
        if code in ("CDI-3-06", "CDI-3-09"):
            relation = "conditional"  # مسائل اقتصادی مشروط
        if rank == "E":
            relation = "conditional"

        # خانوادهٔ صف خدمت
        queue = AXIS_TO_QUEUE.get(code, "Q5")
        queue_info = next((q for q in SERVICE_QUEUE_FAMILIES if q["code"] == queue), None)

        # مسئول اجرا
        if rank == "A" and i.get("p") in ("P0", "P1"):
            owner = "مددکار خانواده"
        elif code in EMPLOY_DOMAIN:
            owner = "کارشناس اشتغال"
        elif code in ROSE_DOMAIN:
            owner = "کلینیک رز"
        elif code in SENSITIVE:
            owner = "کلینیک مددکاری"
        else:
            owner = "همیار مددکار"

        item = {
            "code": code,
            "title": i["title"],
            "dim": i["dim"],
            "severity": i.get("severity"),
            "severity_label": i.get("severity_label"),
            "p": i["p"],
            "rank": rank,
            "rank_info": ACTION_RANKS[rank],
            "pim": pim,
            "pim_breakdown": pim_breakdown,
            "owner": owner,
            "owner_role": "worker" if "مددکار" in owner else ("employ" if "اشتغال" in owner else ("rose" if "رز" in owner else ("swclinic" if "مددکاری" in owner else "assistant"))),
            "deadline": ACTION_RANKS[rank]["deadline"],
            "relation": relation,
            "queue": queue,
            "queue_name": queue_info["name"] if queue_info else "—",
            "queue_color": queue_info["color"] if queue_info else "P4",
            "intervention": i.get("intervention", ""),
            "prerequisite": "احراز مهارت و بازار" if rank == "E" else "—",
            "followup": i.get("intervention", "").split("پیگیری:")[-1].strip() if "پیگیری:" in i.get("intervention", "") else "ثبت شاخص پیگیری",
            "status": "pending",  # pending | in_progress | completed | deferred | rejected | review
        }
        items_by_rank[rank].append(item)
        basket.append(item)

    # مرتب‌سازی بر اساس رتبه (A → E)
    rank_order = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    basket_sorted = sorted(basket, key=lambda x: rank_order[x["rank"]])

    return {
        "actions": basket_sorted,
        "by_rank": items_by_rank,
        "counts": {r: len(items_by_rank[r]) for r in "ABCDE"},
        "total": len(basket_sorted),
    }


# ─────────────────────────────────────────────────────────────────
# محاسبهٔ کامل وضعیت خانوار
# ─────────────────────────────────────────────────────────────────
def compute_household(state):
    """
    محاسبه کامل وضعیت خانوار شامل:
    - اولویت عملیاتی بین‌خانوارها (P0–P4) با دلیل
    - توالی درون‌خانوار (گام‌های ۱ تا ۶)
    - امتیاز PEH (بند ۲ـ۵)
    - سبد مداخله با رتبه A-E و PIM (بند ۲ـ۸، ۲ـ۱۰)
    - سطح اطمینان داده و نقص‌ها
    - قاعده ورود به لایه ۳
    """
    active = state.get("active_axes") or activate_axes(
        state.get("redflags"), state.get("em_dims"),
        state.get("extra_axes"), state.get("manual_axes"))
    answers = state.get("answers", {})

    items, urgent, sequence_map = [], [], {i: [] for i, _ in SEQUENCE_STEPS}
    for code in active:
        a = AXES_BY_CODE[code]
        ans = answers.get(code, {})
        sev = ans.get("severity")
        if sev == "none" or sev is None:
            if sev is None:
                items.append({"code": code, "title": a["title"], "dim": a["dim"],
                              "severity": None, "p": None, "gap": True})
            continue
        p = a["p_map"][sev]
        seq = a["seq"]
        reason = f"{a['title']}: {SEVERITY_LABELS[sev]} → {p} (طبق نقشه اولویت سند)"
        item = {"code": code, "title": a["title"], "dim": a["dim"], "severity": sev,
                "severity_label": SEVERITY_LABELS[sev], "p": p,
                "response": PRIORITY_CLASSES[p]["response"], "reason": reason,
                "sources": a["sources"], "intervention": a["intervention"],
                "referral": a["referral"], "approver": a["approver"],
                "sensitive": code in SENSITIVE,
                "conflict": bool(ans.get("conflict")), "note": ans.get("note", "")}
        items.append(item)
        sequence_map[seq].append({"code": code, "title": a["title"], "p": p, "severity": sev})
        if p in ("P0", "P1"):
            urgent.append(item)

    # اولویت عملیاتی خانوار = شدیدترین طبقه فعال
    ps = [i["p"] for i in items if i.get("p")]
    op_priority = min(ps, key=lambda x: P_ORDER[x]) if ps else "P4"
    drivers = [i["code"] for i in items if i.get("p") == op_priority]

    # وضعیت مداخله = زودترین گام توالی دارای مسئله جدی
    serious = [s for s, arr in sequence_map.items()
               if any(x["severity"] in ("high", "medium") for x in arr)]
    stage = STAGES[min(serious)] if serious else STAGES[6]

    # گلوگاه‌ها: حداکثر سه مورد (شدیدترین، مقدم‌ترین گام)
    bottlenecks = sorted([i for i in items if i.get("p")],
                         key=lambda i: (P_ORDER[i["p"]], next(g for g, _ in SEQUENCE_STEPS
                                                              if i["code"] in [x["code"] for x in sequence_map[g]])))[:3]

    # سطح اطمینان داده
    gaps = [i["code"] for i in items if i.get("gap")]
    conflicts = [c for c, v in answers.items() if v.get("conflict")]
    if conflicts or len(gaps) > len(active) * 0.4:
        confidence, conf_note = "پایین", "تعارض داده یا نقص گسترده؛ نیازمند تکمیل پیش از تصمیم پراثر"
    elif gaps:
        confidence, conf_note = "متوسط", f"{len(gaps)} محور فعال بدون پاسخ است"
    else:
        confidence, conf_note = "بالا", "همه محورهای فعال پاسخ دریافت کرده‌اند"

    entered3, l3_reasons = layer3_gate({**state, "active_axes": active, "answers": answers})

    # توالی درون‌خانوار مرتب‌شده
    sequence = [{"step": g, "title": t, "rows": sequence_map[g]}
                for g, t in SEQUENCE_STEPS if sequence_map[g]]

    # ── امتیاز PEH (افزودهٔ بند ۲ـ۵) ──
    em_input = state.get("em_input") or {}
    interim_result = {
        "urgent": urgent, "bottlenecks": bottlenecks,
        "conflicts": conflicts, "gaps": gaps, "layer3_required": entered3,
    }
    peh, peh_breakdown = compute_peh(em_input=em_input, result=interim_result, state=state)

    # رتبهٔ کلی (نمونهٔ اولیه — بدون مقیاس ۱۰۰۰ خانوار، فقط بر اساس PEH و P)
    # در استقرار واقعی، رتبه از ۱ تا N (تعداد کل خانوارها) محاسبه می‌شود
    rank_hint = max(1, round(1000 - peh * 10))  # تقریبی

    # ── سبد مدخله (افزودهٔ بند ۲ـ۸) ──
    basket = build_intervention_basket({
        "rows": items,
        "bottlenecks": bottlenecks,
    })

    return {
        "active_axes": active,
        "rows": items,
        "operational_priority": op_priority,
        "priority_class": PRIORITY_CLASSES[op_priority],
        "drivers": drivers,
        "urgent": urgent,
        "stage": stage,
        "sequence": sequence,
        "bottlenecks": bottlenecks,
        "confidence": confidence,
        "confidence_note": conf_note,
        "gaps": gaps,
        "conflicts": conflicts,
        "layer3_required": entered3,
        "layer3_reasons": l3_reasons,
        "monitoring": MONITORING[op_priority],
        # ── افزوده‌های هماهنگ با سند ──
        "peh": peh,
        "peh_breakdown": peh_breakdown,
        "rank_hint": rank_hint,
        "basket": basket,
        "is_recommendation": True,  # بند ۹ـ۲: خروجی سامانه پیشنهاد است
    }


def system_suggestions(result):
    """پیشنهادهای سامانه/هوش مصنوعی با ذکر دلیل، سطح اطمینان و امکان اصلاح انسانی (بند ۹)."""
    sugg = []
    for i in result["rows"]:
        if not i.get("p"):
            continue
        s = {"axis": i["code"], "title": i["title"], "p": i["p"],
             "suggestion": i["intervention"], "reason": i["reason"],
             "referral_hint": i["referral"], "confidence": result["confidence"],
             "overridable": True}
        if i.get("conflict"):
            s["warning"] = "تعارض داده — پیش از اقدام نیازمند تأیید مددکار خانواده"
        if i["sensitive"]:
            s["warning"] = "محور حساس — ثبت حداقلی، ارزیابی و تصمیم با حلقه مجاز"
        sugg.append(s)
    if result["layer3_required"]:
        sugg.append({"type": "gate", "suggestion": "ورود به لایه ۳ (CDI عمیق و تخصصی) پیشنهاد می‌شود",
                     "reason": "؛ ".join(result["layer3_reasons"]), "overridable": True})
    if result["gaps"]:
        sugg.append({"type": "gap", "suggestion": "تکمیل محورهای بدون پاسخ توسط همیار مددکار",
                     "reason": "تشخیص نقص داده توسط سامانه (بند ۹ـ۱)", "axes": result["gaps"],
                     "overridable": True})
    if result["conflicts"]:
        sugg.append({"type": "conflict", "suggestion": "رفع تعارض داده‌های کلیدی",
                     "reason": "بند ۹ـ۱: تشخیص قدمت/تعارض داده", "axes": result["conflicts"],
                     "overridable": True})
    return sugg


def build_profile(household, em_input, result, preferences=None, capacities=None, causes=None):
    """پروفایل توانمندسازی خانوار — اجزای الزامی ۱۶گانه (بند ۸ـ۲)."""
    return {
        "parts_index": PROFILE_PARTS,
        "red_lines": AI_RED_LINES,
        "data": {
            "1_identity": household,
            "2_emmpi_card": em_input,
            "3_urgent": [{"axis": i["code"], "title": i["title"], "p": i["p"],
                          "action": i["intervention"], "owner": i["approver"],
                          "deadline": i["response"]} for i in result["urgent"]],
            "4_active_issues": [{"axis": i["code"], "title": i["title"], "dim": i["dim"],
                                 "severity": i.get("severity_label"), "p": i.get("p")}
                                for i in result["rows"] if i.get("p")],
            "5_root_causes": causes or [],
            "6_capacities": capacities or [],
            "7_preferences": preferences or {},
            "8_bottlenecks": [{"axis": b["code"], "title": b["title"], "p": b["p"]}
                              for b in result["bottlenecks"]],
            "9_intervention_stage": result["stage"],
            "10_operational_priority": {"class": result["operational_priority"],
                                        "definition": result["priority_class"]["definition"],
                                        "response": result["priority_class"]["response"],
                                        "ring": result["priority_class"]["ring"],
                                        "drivers": result["drivers"],
                                        "peh": result.get("peh", 0),
                                        "rank_hint": result.get("rank_hint", 0),
                                        "note": "پیشنهاد سامانه؛ تأیید نهایی با مددکار خانواده"},
            "11_intra_household_sequence": result["sequence"],
            "11_intervention_basket": result.get("basket", {"actions": [], "counts": {}}),
            "12_pathway": result["stage"],
            "13_services": em_input.get("services_received", []),
            "14_risk_register": {"red_flags": em_input.get("redflag_labels", []),
                                 "shock_axes": ["CDI-1-07", "CDI-4-08"],
                                 "layer3_reasons": result["layer3_reasons"]},
            "15_monitoring_plan": {"frequency": result["monitoring"],
                                   "criteria": [i["intervention"].split("؛ پیگیری:")[-1].strip()
                                                for i in result["rows"] if i.get("p")][:8]},
            "16_data_confidence": {"level": result["confidence"], "note": result["confidence_note"],
                                   "gaps": result["gaps"], "conflicts": result["conflicts"]},
        },
    }
