# -*- coding: utf-8 -*-
"""
سامانهٔ تحت وب CDI — چارچوب عملیاتی ارزیابی جامع (نمونهٔ اولیه)

نسخهٔ هماهنگ با سند Emdad_sanadHemayt0005:
- ورود بر اساس نقش (ماتریس بازیگران بند ۳)
- لایه ۱: CDI سریع (فعال‌سازی شاخه‌ای از EM-MPI)
- لایه ۲: CDI هدفمند (پرسشنامهٔ پویا فقط برای محورهای فعال)
- لایه ۳: CDI عمیق (فقط با قاعده ورود بند ۴ـ۱)
- امتیاز PEH (بند ۲ـ۵)، PIM (بند ۲ـ۱۰)، PES (بند ۲ـ۱۵)
- سبد مدخله با رتبه A-E (بند ۲ـ۸)
- صف‌های ۹گانهٔ خدمت (بند ۲ـ۱۳)
- خروجی رسمی: پروفایل توانمندسازی خانوار (بند ۸)
- خط قرمزهای هوش مصنوعی (بند ۹) در کد اعمال می‌شود

اجرا: python main.py  →  http://127.0.0.1:5000
"""
import json
import os
from datetime import datetime
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for, jsonify, send_from_directory

from cdi_catalog import (ACTORS, AI_RED_LINES, AXES, AXES_BY_CODE, DIMENSIONS,
                         LAYER3_TRIGGERS, LAYERS, PRIORITY_CLASSES, RINGS,
                         SEVERITY_LABELS, SOURCES)
from cdi_engine import (ROLES, SEVERITIES, STAGES, activate_axes, alert_only,
                        build_profile, can_assess, compute_household,
                        system_suggestions,
                        # افزوده‌های هماهنگ با سند
                        SERVICE_QUEUE_FAMILIES, ACTION_RELATIONS,
                        TIEBREAK_RULES_HOUSEHOLD, TIEBREAK_RULES_QUEUE,
                        CONTROL_RULES, ACTION_RANKS,
                        compute_peh, compute_pim, pim_to_rank, compute_pes,
                        build_intervention_basket)

# ─── موتور EM-MPI (غربالگری اولیه، قبل از CDI) ───
from emmpi_engine import (DIMENSIONS as EMMPI_DIMENSIONS, INDICATORS as EMMPI_INDICATORS,
                          RED_FLAGS as EMMPI_RED_FLAGS, DEPRIVATION_LEVELS,
                          REFERRAL_PATHS, AI_RED_LINES as EMMPI_AI_RED_LINES,
                          SEVERITY_OPTIONS, compute_emmpi, suggest_assistant,
                          get_indicator_list_by_dim,
                          # تخصیص هوشمند همیاران + آیکون‌های مولفه‌ها
                          match_assistants, SAMPLE_ASSISTANTS, ASSISTANT_ROLES,
                          MATCH_CRITERIA, COMPONENT_META, get_component_meta,
                          get_referral_paths_visual,
                          # پروندهٔ شهروندی + امتیاز صداقت
                          compute_citizen_profile, SD_TO_EMPI_FULL,
                          SD_ANSWER_LABELS, EMPI_SEVERITY_LABELS, HONESTY_LEVELS,
                          # ─── توابع جدید EM-MPI نسخه ۲ (port از reference) ───
                          is_valid_iranian_national_id as emmpi_is_valid_nid,
                          national_id_error as emmpi_nid_error,
                          is_valid_mobile as emmpi_is_valid_mobile,
                          mobile_error as emmpi_mobile_error,
                          normalize_jalali_date as emmpi_normalize_jalali,
                          birth_date_error as emmpi_birth_error,
                          password_error as emmpi_password_error,
                          hash_password as emmpi_hash_password,
                          normalize_digits as emmpi_normalize_digits,
                          simulate_service_fetch as emmpi_simulate_service,
                          LOCKED_FIELDS as EMMPI_LOCKED_FIELDS,
                          RULE_SET as EMMPI_RULE_SET,
                          INDICATOR_TITLES as EMMPI_INDICATOR_TITLES,
                          WEIGHTS as EMMPI_WEIGHTS,
                          compute_assessment as emmpi_compute_assessment,
                          suggest_flags as emmpi_suggest_flags,
                          validate_weights as emmpi_validate_weights,
                          BANK_AGREEMENT_PARAGRAPHS,
                          REGISTRATION_KINDS,
                          compute_citizenship_score)

# ─── وب‌سرویس‌های فرضی (ثبت‌احوال، بیمه، آموزش، اشتغال) ───
from web_services import (fetch_all_services, fetch_civil_registry,
                          fetch_insurance, fetch_education, fetch_employment,
                          fetch_housing, DATA_SOURCE_PRIORITIES)

# ─── داده‌های جغرافیایی ایران (۳۱ استان + شهرها + مختصات) ───
from iran_geo import (PROVINCES, get_province_choices, get_cities_for_province,
                      get_province_name, get_province_coords, get_all_province_coords,
                      detect_province_from_postal_code, calculate_poverty_line,
                      PROVINCE_COST_INDEX)

# ─── سیستم مالی (کیف پول + هزینه خدمات) ───
from finance_engine import (SERVICE_COSTS, COMPLEXITY_MULTIPLIERS, ROLE_MULTIPLIERS,
                             compute_service_cost, get_service_label,
                             get_wallet, credit_wallet, credit_wallet_pending,
                             approve_transaction, approve_all_pending,
                             get_all_wallets, get_all_pending)

# ─── مسیرهای موبایل اپ (PWA) ───
# import در انتهای فایل برای جلوگیری از circular import

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdi_data.json")

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "cdi-prototype-secret-key"  # نمونهٔ اولیه

USERS = {
    # ── نقش‌های سراسری (بدون فیلتر استان) ──
    "beneficiary": {"password": "1234", "name": "نیازمند (نمونه)", "role": "beneficiary", "province": None},
    "hqmanager": {"password": "1234", "name": "مدیر ستاد مرکزی", "role": "hqmanager", "province": None},
    "employ": {"password": "1234", "name": "کارشناس اشتغال (نمونه)", "role": "employ", "province": None},

    # ── استان تهران ──
    "tehran_ast1": {"password": "1234", "name": "مریم احمدی", "role": "assistant", "province": "tehran"},
    "tehran_ast2": {"password": "1234", "name": "علی صادقی", "role": "assistant", "province": "tehran"},
    "tehran_worker": {"password": "1234", "name": "مهدی بابایی", "role": "worker", "province": "tehran"},
    "tehran_rose": {"password": "1234", "name": "فاطمه موسوی", "role": "rose", "province": "tehran"},
    "tehran_swclinic": {"password": "1234", "name": "زهرا محمدی", "role": "swclinic", "province": "tehran"},

    # ── استان سیستان و بلوچستان ──
    "sistan_ast1": {"password": "1234", "name": "نبی‌الله ریاحی", "role": "assistant", "province": "sistan_baluchestan"},
    "sistan_ast2": {"password": "1234", "name": "خدیجه بلوچ", "role": "assistant", "province": "sistan_baluchestan"},
    "sistan_worker": {"password": "1234", "name": "عبدالله نوری", "role": "worker", "province": "sistan_baluchestan"},
    "sistan_rose": {"password": "1234", "name": "معصومه کردی", "role": "rose", "province": "sistan_baluchestan"},
    "sistan_swclinic": {"password": "1234", "name": "حمید مکرانی", "role": "swclinic", "province": "sistan_baluchestan"},

    # ── استان بوشهر ──
    "bushehr_ast1": {"password": "1234", "name": "سعید کاوری", "role": "assistant", "province": "bushehr"},
    "bushehr_ast2": {"password": "1234", "name": "عطیه دیری", "role": "assistant", "province": "bushehr"},
    "bushehr_worker": {"password": "1234", "name": "ناصر عبدی", "role": "worker", "province": "bushehr"},
    "bushehr_rose": {"password": "1234", "name": "زینب حیدری", "role": "rose", "province": "bushehr"},
    "bushehr_swclinic": {"password": "1234", "name": "محمد امینی", "role": "swclinic", "province": "bushehr"},

    # ── استان فارس ──
    "fars_ast1": {"password": "1234", "name": "حسن شیرازی", "role": "assistant", "province": "fars"},
    "fars_ast2": {"password": "1234", "name": "نگار صفایی", "role": "assistant", "province": "fars"},
    "fars_worker": {"password": "1234", "name": "رضا پرچمی", "role": "worker", "province": "fars"},
    "fars_rose": {"password": "1234", "name": "شکوفه رستمی", "role": "rose", "province": "fars"},
    "fars_swclinic": {"password": "1234", "name": "کامران عسگری", "role": "swclinic", "province": "fars"},

    # ── استان خراسان جنوبی ──
    "khs_ast1": {"password": "1234", "name": "ابراهیم بیرجندی", "role": "assistant", "province": "khorasan_south"},
    "khs_ast2": {"password": "1234", "name": "الهام قائنی", "role": "assistant", "province": "khorasan_south"},
    "khs_worker": {"password": "1234", "name": "حسین طبسی", "role": "worker", "province": "khorasan_south"},
    "khs_rose": {"password": "1234", "name": "طاهره فردوسی", "role": "rose", "province": "khorasan_south"},
    "khs_swclinic": {"password": "1234", "name": "محمود سرایان", "role": "swclinic", "province": "khorasan_south"},

    # ── استان کردستان ──
    "kurd_ast1": {"password": "1234", "name": "باهط سنندجی", "role": "assistant", "province": "kurdistan"},
    "kurd_ast2": {"password": "1234", "name": "هانیه رشید", "role": "assistant", "province": "kurdistan"},
    "kurd_worker": {"password": "1234", "name": "جمال کاویانی", "role": "worker", "province": "kurdistan"},
    "kurd_rose": {"password": "1234", "name": "سهیلا مهدوی", "role": "rose", "province": "kurdistan"},
    "kurd_swclinic": {"password": "1234", "name": "عثمان قادری", "role": "swclinic", "province": "kurdistan"},

    # ─ـ استان کرمان ──
    "kerman_ast1": {"password": "1234", "name": "یوسف کرمانی", "role": "assistant", "province": "kerman"},
    "kerman_ast2": {"password": "1234", "name": "سارا مهدوی", "role": "assistant", "province": "kerman"},
    "kerman_worker": {"password": "1234", "name": "غلام نوری", "role": "worker", "province": "kerman"},
    "kerman_rose": {"password": "1234", "name": "فریبا جیری", "role": "rose", "province": "kerman"},
    "kerman_swclinic": {"password": "1234", "name": "مصطفی رفیعی", "role": "swclinic", "province": "kerman"},
}
ALL_ROLES = list(USERS.keys())

# ─── کانال‌های دریافت درخواست ───
REQUEST_CHANNELS = [
    {"code": "website", "name": "وب‌سایت سامانه", "icon": "🌐", "color": "P2"},
    {"code": "mobile_app", "name": "اپلیکیشن موبایل", "icon": "📱", "color": "P2"},
    {"code": "phone", "name": "تماس تلفنی", "icon": "📞", "color": "P3"},
    {"code": "sms", "name": "پیامک", "icon": "💬", "color": "P3"},
    {"code": "email", "name": "ایمیل", "icon": "✉️", "color": "P3"},
    {"code": "gov_window", "name": "پنجره واحد رفاه ایرانیان", "icon": "🏛️", "color": "P1"},
    {"code": "in_person", "name": "حضوری (مراجعه به دفتر)", "icon": "🏢", "color": "P3"},
    {"code": "referral", "name": "ارجاع نهاد همکار", "icon": "🤝", "color": "P2"},
    {"code": "social_media", "name": "شبکه‌های اجتماعی", "icon": "📢", "color": "P4"},
]


# ─────────────────────────────────────────────────────────
# ذخیره‌سازی JSON
# ─────────────────────────────────────────────────────────
def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"households": {}}


def save_db(db):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────
# کمک‌تابع‌ها
# ─────────────────────────────────────────────────────────
def current_user():
    uid = session.get("uid")
    if uid in USERS:
        user_data = USERS[uid]
        role = user_data.get("role", uid)
        province = user_data.get("province")
        return {
            "id": uid,
            "role": role,
            "name": user_data["name"],
            "province": province,
            "province_name": get_province_name(province) if province else None,
            **ROLES.get(role, {})
        }
    return None


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not current_user():
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


def axis_items(dim=None, active=None):
    axes = AXES if dim is None else [a for a in AXES if a["dim"] == dim]
    out = []
    for a in axes:
        out.append({
            "code": a["code"], "dim": a["dim"], "title": a["title"],
            "questions": a["questions"], "sources": a["sources"],
            "register": a["register"], "referral": a["referral"],
            "approver": a["approver"], "priority": a["priority"],
            "intervention": a["intervention"], "sensitive": a["sensitive"],
            "severity_opts": [s for s in SEVERITIES],
        })
    if active is not None:
        out = [o for o in out if o["code"] in active]
    return out


# ─────────────────────────────────────────────────────────
# اعتبارسنجی کد ملی و شماره همراه ایران
# ─────────────────────────────────────────────────────────
def validate_iran_national_id(national_id):
    """
    اعتبارسنجی کدملی ۱۰ رقمی ایران با الگوریتم چک‌سام.

    الگوریتم:
      ۱. کدملی باید ۱۰ رقم باشد.
      ۲. ۹ رقم اول با وزن‌های ۱۰، ۹، ۸، ... ۲ ضرب می‌شوند.
      ۳. مجموع حاصل‌ضرب‌ها گرفته می‌شود.
      ۴. باقی‌ماندهٔ مجموع بر ۱۱ محاسبه می‌شود.
      ۵. اگر باقی‌مانده < ۲ باشد، رقم کنترل = باقی‌مانده.
      ۶. در غیر این صورت، رقم کنترل = ۱۱ - باقی‌مانده.
      ۷. رقم کنترل باید با رقم دهم برابر باشد.

    خروجی: (is_valid: bool, error_message: str)
    """
    if not national_id:
        return False, "کدملی الزامی است."

    # نرمال‌سازی: حذف فاصله و تبدیل ارقام فارسی به لاتین
    fa_to_en = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    national_id = national_id.translate(fa_to_en).strip()

    # بررسی طول
    if len(national_id) != 10:
        return False, "کدملی باید ۱۰ رقم باشد."

    # بررسی عددی بودن
    if not national_id.isdigit():
        return False, "کدملی فقط باید شامل رقم باشد."

    # جلوگیری از کدهای تکراری (مثل ۱۱۱۱۱۱۱۱۱۱)
    if len(set(national_id)) == 1:
        return False, "کدملی نامعتبر است (عدد تکراری)."

    # الگوریتم چک‌سام
    try:
        weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
        total = sum(int(national_id[i]) * weights[i] for i in range(9))
        remainder = total % 11
        check_digit = remainder if remainder < 2 else 11 - remainder
        if check_digit != int(national_id[9]):
            return False, "کدملی نامعتبر است (رقم کنترل اشتباه)."
        return True, ""
    except (ValueError, IndexError):
        return False, "کدملی نامعتبر است."


def validate_iran_mobile(mobile):
    """
    اعتبارسنجی شماره تلفن همراه ایران.

    الگوریتم:
      ۱. شماره باید ۱۱ رقم باشد.
      ۲. با 09 شروع شود.
      ۳. رقم سوم باید یکی از 0, 1, 2, 3, 9 باشد (پیش‌شماره‌های معتبر).

    خروجی: (is_valid: bool, error_message: str)
    """
    if not mobile:
        return False, "شماره همراه الزامی است."

    # نرمال‌سازی: حذف فاصله، خط تیره و پرانتز
    fa_to_en = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    mobile = mobile.translate(fa_to_en).strip()
    mobile = mobile.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # بررسی طول
    if len(mobile) != 11:
        return False, "شماره همراه باید ۱۱ رقم باشد."

    # بررسی عددی بودن
    if not mobile.isdigit():
        return False, "شماره همراه فقط باید شامل رقم باشد."

    # باید با 09 شروع شود
    if not mobile.startswith("09"):
        return False, "شماره همراه باید با ۰۹ شروع شود."

    # رقم سوم: پیش‌شماره‌های معتبر اپراتورها
    valid_third_digits = {"0", "1", "2", "3", "9"}  # 090, 091, 092, 093, 099
    if mobile[2] not in valid_third_digits:
        return False, "پیش‌شمارهٔ نامعتبر است (باید ۰۹۰، ۰۹۱، ۰۹۲، ۰۹۳ یا ۰۹۹ باشد)."

    return True, ""


def normalize_national_id(national_id):
    """نرمال‌سازی کدملی: تبدیل ارقام فارسی به لاتین."""
    if not national_id:
        return ""
    fa_to_en = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    return national_id.translate(fa_to_en).strip()


def normalize_mobile(mobile):
    """نرمال‌سازی شماره همراه: حذف فاصله/خط تیره/پرانتز و تبدیل ارقام فارسی."""
    if not mobile:
        return ""
    fa_to_en = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    mobile = mobile.translate(fa_to_en).strip()
    return mobile.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")


# ─────────────────────────────────────────────────────────
# احراز هویت
# ─────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        uid = request.form.get("uid", "")
        pw = request.form.get("password", "")
        if uid in USERS and USERS[uid]["password"] == pw:
            session["uid"] = uid
            return redirect(url_for("index"))
        error = "نام کاربری یا گذرواژه نادرست است."
    return render_template("login.html", error=error, users=USERS, roles=ROLES,
                           province_names={k: v["name"] for k, v in PROVINCES.items()})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─────────────────────────────────────────────────────────
# ثبت‌نام نیازمند جدید — بدون نیاز به لاگین قبلی
# ─────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    """ثبت‌نام نیازمند جدید — از صفحه لاگین قابل دسترسی است.
    کد ملی، موبایل، تاریخ تولد، کد پستی، رمز عبور را می‌گیرد،
    سرویس‌ها را واکشی می‌کند و سپس به پرسشنامه هدایت می‌شود."""
    error = ""
    if request.method == "POST":
        national_id = emmpi_normalize_digits(request.form.get("national_id", "").strip())
        date_of_birth_raw = request.form.get("date_of_birth", "").strip()
        contact = emmpi_normalize_digits(request.form.get("contact", "").strip())
        postal_code = emmpi_normalize_digits(request.form.get("postal_code", "").strip())
        password = request.form.get("password", "").strip()
        consent_bank = request.form.get("consent_bank") == "on"

        date_of_birth = emmpi_normalize_jalali(date_of_birth_raw) or date_of_birth_raw

        # اعتبارسنجی
        nid_err = emmpi_nid_error(national_id)
        if nid_err:
            error = nid_err
        else:
            mob_err = emmpi_mobile_error(contact)
            if mob_err:
                error = mob_err
            else:
                birth_err = emmpi_birth_error(date_of_birth_raw)
                if birth_err:
                    error = birth_err
                elif len(emmpi_normalize_digits(postal_code)) != 10:
                    error = "کد پستی باید دقیقاً ۱۰ رقم باشد."
                else:
                    pw_err = emmpi_password_error(password)
                    if pw_err:
                        error = pw_err
                    else:
                        # بررسی تکراری نبودن کد ملی
                        db = load_db()
                        hid = f"H-{national_id[-6:]}"
                        if hid in db["households"]:
                            error = "این کد ملی قبلاً ثبت شده است. لطفاً وارد شوید."
                        else:
                            # ساخت کاربر جدید در USERS (سراسری)
                            new_uid = f"ben_{national_id[-6:]}"
                            if new_uid not in USERS:
                                USERS[new_uid] = {
                                    "password": password,
                                    "name": f"نیازمند ({national_id[-6:]})",
                                    "role": "beneficiary",
                                    "province": None,
                                }

                            # ساخت Assessment با ۸ سرویس قطعی
                            assessment = {
                                "id": hid,
                                "createdAt": datetime.now().isoformat(timespec="seconds"),
                                "updatedAt": datetime.now().isoformat(timespec="seconds"),
                                "ruleSetVersion": EMMPI_RULE_SET["fullId"],
                                "status": "draft",
                                "demo": EMMPI_RULE_SET["demo"],
                                "registrationKind": "need_service",
                                "requestTypes": ["درخواست تشکیل/به‌روزرسانی پرونده حمایت"],
                                "household": {
                                    "headNationalId": national_id,
                                    "headNationalIdStatus": "has",
                                    "headBirthDate": date_of_birth,
                                    "headMobile": contact,
                                    "postalCode": postal_code,
                                    "headPasswordHash": emmpi_hash_password(password),
                                    "consents": {"bankAccess": consent_bank,
                                                 "agreedAt": datetime.now().isoformat(timespec="seconds")},
                                    "registeredAt": datetime.now().isoformat(timespec="seconds"),
                                },
                                "members": [],
                                "answers": {},
                                "incomeSources": [],
                                "flags": [],
                                "qualityIssues": [],
                                "referrals": [],
                                "reviews": [],
                                "corrections": [],
                                "audit": [{
                                    "at": datetime.now().isoformat(timespec="seconds"),
                                    "actor": new_uid,
                                    "role": "household",
                                    "action": "ثبت‌نام و واکشی خودکار وب‌سرویس‌ها",
                                    "detail": f"کد ملی: {national_id}",
                                }],
                                "webServices": {},
                            }

                            # واکشی ۷ سرویس
                            service_order = ["civil_registry", "post", "shaparak_bank",
                                             "insurance", "property", "higher_edu", "education_school"]
                            for svc_id in service_order:
                                result = emmpi_simulate_service(svc_id, assessment)
                                assessment["webServices"][svc_id] = result
                                if result.get("prefills"):
                                    pf = result["prefills"]
                                    if pf.get("householdPatch"):
                                        assessment["household"].update(pf["householdPatch"])
                                    if pf.get("memberCreates"):
                                        for mc in pf["memberCreates"]:
                                            mid = f"m{len(assessment['members']) + 1}"
                                            assessment["members"].append({
                                                "id": mid,
                                                "firstName": mc["firstName"],
                                                "relation": mc["relation"],
                                                "age": mc.get("age"),
                                                "gender": mc.get("gender", "male"),
                                                "memberType": "registry",
                                                "fromRegistry": True,
                                                "nationalIdStatus": "has",
                                                "schoolAge": isinstance(mc.get("age"), (int, float)) and 6 <= mc["age"] <= 18,
                                                "educationStatus": "na",
                                                "employmentStatus": "na",
                                                "isHead": mc["relation"] == "سرپرست",
                                            })
                                    if pf.get("answerPrefills"):
                                        for ap in pf["answerPrefills"]:
                                            assessment["answers"][ap["key"]] = ap["value"]
                                    if pf.get("memberPrefills"):
                                        for mp in pf["memberPrefills"]:
                                            for m in assessment["members"]:
                                                if m["id"] == mp["memberId"]:
                                                    m.update(mp["patch"])
                                                    break

                            # استخراج نام و نشانی
                            civil = assessment["webServices"].get("civil_registry", {})
                            head_name = (civil.get("data") or {}).get("نام و نام خانوادگی سرپرست", "")
                            post = assessment["webServices"].get("post", {})
                            post_data = post.get("data") or {}
                            province = post_data.get("استان", "")
                            city = post_data.get("شهرستان / منطقه", "")
                            location = f"{province}، {city}" if province and city else ""

                            # ساخت پرونده خانوار
                            h = {
                                "identity": {
                                    "hid": hid,
                                    "national_id": national_id,
                                    "name": head_name,
                                    "province": province,
                                    "province_name": province,
                                    "city": city,
                                    "location": location,
                                    "members": str(len(assessment["members"])),
                                    "contact": contact,
                                    "at_risk": "", "at_risk_list": [],
                                },
                                "em_input": {"level": "", "redflags": [], "em_dims": [],
                                             "redflag_labels": [], "services_received": [],
                                             "em_date": "", "note": ""},
                                "state": {"redflags": [], "em_dims": [], "active_axes": [],
                                          "answers": {},
                                          "created_at": datetime.now().isoformat(timespec="seconds"),
                                          "created_by": "beneficiary"},
                                "layer2_done": False, "layer3_done": False,
                                "decisions": [], "referrals": [], "history": [],
                                "preferences": {}, "capacities": [], "causes": [],
                                "national_id": national_id,
                                "request_channel": "website",
                                "status": "pending",
                                "claimed_by": None,
                                "self_declaration": {
                                    "submitted_at": datetime.now().isoformat(timespec="seconds"),
                                    "registration_kind": "need_service",
                                    "postal_code": postal_code,
                                    "date_of_birth": date_of_birth,
                                    "consent_bank": consent_bank,
                                },
                                "web_service_data": {},
                                "assessment": assessment,
                            }
                            h["history"].append({
                                "at": datetime.now().isoformat(timespec="seconds"),
                                "by": "beneficiary",
                                "action": f"ثبت‌نام با کد ملی {national_id} + واکشی {len(service_order)} سرویس — {len(assessment['members'])} عضو از ثبت احوال"
                            })
                            db["households"][hid] = h
                            save_db(db)

                            # لاگین خودکار کاربر جدید
                            session["uid"] = new_uid
                            session["role"] = "beneficiary"
                            session["beneficiary_hid"] = hid
                            return redirect(url_for("questionnaire_app", hid=hid))

    return render_template("register.html", error=error)


# ─────────────────────────────────────────────────────────
# داشبورد
# ─────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    u = current_user()
    db = load_db()
    hhs = []
    for hid, h in db["households"].items():
        # فیلتر استانی (مدیر ستاد همه را می‌بیند)
        if u.get("province"):
            hh_prov = h.get("identity", {}).get("province", "")
            if hh_prov != u["province"]:
                continue
        # نیازمند فقط پروندهٔ خودش
        if u["role"] == "beneficiary":
            beneficiary_hid = session.get("beneficiary_hid")
            if hid != beneficiary_hid and h.get("identity", {}).get("national_id") != session.get("uid"):
                continue

        st = h.get("state", {})
        if st.get("active_axes") or st.get("redflags"):
            st_with_em = {**st, "em_input": h.get("em_input", {})}
            res = compute_household(st_with_em)
        else:
            res = None
        hhs.append({"hid": hid, "h": h, "res": res})

    return render_template("dashboard.html", u=u, households=hhs)


# ═══════════════════════════════════════════════════════════
# فاز نیازمند — ثبت درخواست و خوداظهاری
# ═══════════════════════════════════════════════════════════
@app.route("/beneficiary/new-request", methods=["GET", "POST"])
@login_required
def beneficiary_new_request():
    """ثبت درخواست توسط نیازمند — خوداظهاری + واکشی وب‌سرویس."""
    u = current_user()
    if u["role"] != "beneficiary":
        return "این بخش فقط برای نیازمندان قابل دسترسی است.", 403

    if request.method == "POST":
        national_id = emmpi_normalize_digits(request.form.get("national_id", "").strip())
        date_of_birth_raw = request.form.get("date_of_birth", "").strip()
        contact = emmpi_normalize_digits(request.form.get("contact", "").strip())
        postal_code = emmpi_normalize_digits(request.form.get("postal_code", "").strip())
        password = request.form.get("password", "").strip()
        consent_bank = request.form.get("consent_bank") == "on"
        registration_kind = request.form.get("registrationKind", "need_service")

        # نرمال‌سازی تاریخ تولد شمسی
        date_of_birth = emmpi_normalize_jalali(date_of_birth_raw) or date_of_birth_raw

        # آماده‌سازی context برای ارسال مجدد در صورت خطا
        ctx = {
            "u": u,
            "national_id": national_id,
            "date_of_birth": date_of_birth,
            "contact": contact,
        }

        # ─── اعتبارسنجی با توابع جدید EM-MPI ───
        nid_err = emmpi_nid_error(national_id)
        if nid_err:
            ctx["error"] = nid_err
            return render_template("beneficiary_new_request.html", **ctx)

        mob_err = emmpi_mobile_error(contact)
        if mob_err:
            ctx["error"] = mob_err
            return render_template("beneficiary_new_request.html", **ctx)

        birth_err = emmpi_birth_error(date_of_birth_raw)
        if birth_err:
            ctx["error"] = birth_err
            return render_template("beneficiary_new_request.html", **ctx)

        if not emmpi_normalize_digits(postal_code) or len(emmpi_normalize_digits(postal_code)) != 10:
            ctx["error"] = "کد پستی باید دقیقاً ۱۰ رقم باشد."
            return render_template("beneficiary_new_request.html", **ctx)

        pw_err = emmpi_password_error(password)
        if pw_err:
            ctx["error"] = pw_err
            return render_template("beneficiary_new_request.html", **ctx)

        db = load_db()
        hid = f"H-{national_id[-6:]}"
        if hid in db["households"]:
            ctx["error"] = "شما قبلاً درخواست ثبت کرده‌اید."
            return render_template("beneficiary_new_request.html", **ctx)

        # ─── ساخت Assessment با ۸ سرویس قطعی از کد ملی ───
        assessment = {
            "id": hid,
            "createdAt": datetime.now().isoformat(timespec="seconds"),
            "updatedAt": datetime.now().isoformat(timespec="seconds"),
            "ruleSetVersion": EMMPI_RULE_SET["fullId"],
            "status": "draft",
            "demo": EMMPI_RULE_SET["demo"],
            "registrationKind": registration_kind,
            "requestTypes": ["درخواست تشکیل/به‌روزرسانی پرونده حمایت"],
            "household": {
                "headNationalId": national_id,
                "headNationalIdStatus": "has",
                "headBirthDate": date_of_birth,
                "headMobile": contact,
                "postalCode": postal_code,
                "headPasswordHash": emmpi_hash_password(password),
                "consents": {"bankAccess": consent_bank, "agreedAt": datetime.now().isoformat(timespec="seconds")},
                "registeredAt": datetime.now().isoformat(timespec="seconds"),
            },
            "members": [],
            "answers": {},
            "incomeSources": [],
            "flags": [],
            "qualityIssues": [],
            "referrals": [],
            "reviews": [],
            "corrections": [],
            "audit": [{
                "at": datetime.now().isoformat(timespec="seconds"),
                "actor": u.get("name", "beneficiary"),
                "role": "household",
                "action": "ثبت‌نام و واکشی خودکار وب‌سرویس‌ها",
                "detail": f"کد ملی: {national_id}, نوع: {registration_kind}",
            }],
            "webServices": {},
        }

        # ─── واکشی خودکار ۷ سرویس به‌صورت قطعی از کد ملی ───
        service_order = ["civil_registry", "post", "shaparak_bank", "insurance",
                         "property", "higher_edu", "education_school"]
        for svc_id in service_order:
            result = emmpi_simulate_service(svc_id, assessment)
            assessment["webServices"][svc_id] = result
            # اعمال prefills
            if result.get("prefills"):
                pf = result["prefills"]
                if pf.get("householdPatch"):
                    assessment["household"].update(pf["householdPatch"])
                if pf.get("memberCreates"):
                    for mc in pf["memberCreates"]:
                        mid = f"m{len(assessment['members']) + 1}"
                        assessment["members"].append({
                            "id": mid,
                            "firstName": mc["firstName"],
                            "relation": mc["relation"],
                            "age": mc.get("age"),
                            "gender": mc.get("gender", "male"),
                            "memberType": "registry",
                            "fromRegistry": True,
                            "nationalIdStatus": "has",
                            "schoolAge": isinstance(mc.get("age"), (int, float)) and 6 <= mc["age"] <= 18,
                            "educationStatus": "na",
                            "employmentStatus": "na",
                            "isHead": mc["relation"] == "سرپرست",
                        })
                if pf.get("answerPrefills"):
                    for ap in pf["answerPrefills"]:
                        assessment["answers"][ap["key"]] = ap["value"]
                if pf.get("memberPrefills"):
                    for mp in pf["memberPrefills"]:
                        for m in assessment["members"]:
                            if m["id"] == mp["memberId"]:
                                m.update(mp["patch"])
                                break

        # اگر provide_service، به داشبورد حرفه‌ای هدایت
        if registration_kind == "provide_service":
            session["uid"] = u.get("id", "beneficiary")
            session["role"] = u.get("role", "beneficiary")
            session["provide_service_registered"] = True
            return redirect(url_for("index"))

        # استخراج نام سرپرست از ثبت احوال
        civil = assessment["webServices"].get("civil_registry", {})
        head_name = (civil.get("data") or {}).get("نام و نام خانوادگی سرپرست", "")

        # استخراج نشانی از پست
        post = assessment["webServices"].get("post", {})
        post_data = post.get("data") or {}
        province = post_data.get("استان", "")
        city = post_data.get("شهرستان / منطقه", "")
        address = post_data.get("نشانی استاندارد (از کد پستی)", "")
        location = f"{province}، {city}" if province and city else ""

        # ساخت پرونده خانوار (backward compat با ساختار قدیمی)
        h = {
            "identity": {
                "hid": hid,
                "national_id": national_id,
                "name": head_name,
                "province": province,
                "province_name": province,
                "city": city,
                "location": location,
                "members": str(len(assessment["members"])),
                "contact": contact,
                "at_risk": "", "at_risk_list": [],
            },
            "em_input": {"level": "", "redflags": [], "em_dims": [], "redflag_labels": [],
                         "services_received": [], "em_date": "", "note": ""},
            "state": {"redflags": [], "em_dims": [], "active_axes": [], "answers": {},
                      "created_at": datetime.now().isoformat(timespec="seconds"),
                      "created_by": u["role"]},
            "layer2_done": False, "layer3_done": False,
            "decisions": [], "referrals": [], "history": [],
            "preferences": {}, "capacities": [], "causes": [],
            "national_id": national_id,
            "request_channel": "website",
            "status": "pending",
            "claimed_by": None,
            "self_declaration": {
                "submitted_at": datetime.now().isoformat(timespec="seconds"),
                "submitted_by": u["role"],
                "registration_kind": registration_kind,
                "postal_code": postal_code,
                "date_of_birth": date_of_birth,
                "consent_bank": consent_bank,
            },
            "web_service_data": {},
            # ─── Assessment جدید (مطابق reference) ───
            "assessment": assessment,
        }
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": f"ثبت‌نام با کد ملی {national_id} + واکشی {len(service_order)} سرویس — {len(assessment['members'])} عضو از ثبت احوال"
        })
        db["households"][hid] = h
        save_db(db)

        session["beneficiary_hid"] = hid
        return redirect(url_for("questionnaire_app", hid=hid))

    # GET: نمایش فرم
    return render_template("beneficiary_new_request.html", u=u)


@app.route("/beneficiary/status/<hid>")
@login_required
def beneficiary_status(hid):
    """نمایش وضعیت درخواست به نیازمند."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    return render_template("beneficiary_status.html", h=h, hid=hid, u=u)


# ─────────────────────────────────────────────────────────
# خوداظهاری نیازمند — تکمیل پرسشنامه EM-MPI توسط خود نیازمند
# ─────────────────────────────────────────────────────────
@app.route("/self-declaration/<hid>", methods=["GET", "POST"])
@login_required
def self_declaration(hid):
    """پرسشنامه خوداظهاری EM-MPI — نیازمند پس از ثبت‌نام اینجا هدایت می‌شود.
    GET: نمایش ویزارد با داده پیش‌تکمیل‌شده از سرویس‌ها
    POST: ذخیره پاسخ‌ها، محاسبه EM-MPI، انتقال به استخر درخواست‌ها"""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    assessment = h.get("assessment", {})

    if request.method == "POST":
        # جمع‌آوری پاسخ‌های فرم
        answers = {}
        simple_fields = [
            "A4_burden", "A6_now", "A7_disrupt",
            "B3_lit", "B4_barriers", "B4_detail", "B5_digital", "B7_path", "B7_skills",
            "C1_place", "C1_eviction", "C2_constr",
            "C3_right", "C3_lease_end", "C4_rooms", "C4_area", "C4_safesleep",
            "C5_water", "C5_elec", "C5_cook", "C5_effect", "C6_san",
            "C7_impact", "C8_arrears_severity", "C8_installments",
            "C9_access", "D1_no_provider",
            "E1_outlook", "E1_evidence", "E2_support", "E2_hours",
            "E3_support", "E3_who", "E4_barrier", "E4_service",
        ]
        for f in simple_fields:
            v = request.form.get(f)
            if v is not None and v != "":
                answers[f] = v
        # فیلدهای چندانتخابی
        multi_fields = ["A4_effects", "A6_exp", "A7_danger", "C2_issues",
                        "C7_missing", "E4_types"]
        for f in multi_fields:
            vals = request.form.getlist(f)
            if vals:
                answers[f] = vals
        # فیلدهای عضومحور با پسوند #memberId
        member_q_prefixes = [
            "A1_disease", "A1_impact", "A2_limit", "A2_aid",
            "A3_treatment", "A3_urgent", "A3_cause", "A5_cover", "A5_barrier",
            "A_malnut", "A_pregnant",
            "B1_status", "B1_months", "B1_reason", "B2_risks",
            "B6_need",
            "D1_ability", "D1_continuity", "D1_seasonal",
        ]
        for key in request.form.keys():
            for prefix in member_q_prefixes:
                if key.startswith(prefix + "#"):
                    answers[key] = request.form.get(key)
                    break

        # اعضا
        members = []
        member_ids_raw = request.form.get("member_ids", "")
        if member_ids_raw:
            for mid in member_ids_raw.split(","):
                if not mid.strip():
                    continue
                mid = mid.strip()
                age_str = request.form.get(f"member_{mid}_age", "0")
                try:
                    age = int(age_str)
                except (ValueError, TypeError):
                    age = 0
                members.append({
                    "id": mid,
                    "firstName": request.form.get(f"member_{mid}_firstName", ""),
                    "lastName": request.form.get(f"member_{mid}_lastName", ""),
                    "age": age,
                    "gender": request.form.get(f"member_{mid}_gender", "male"),
                    "relation": request.form.get(f"member_{mid}_relation", "سایر"),
                    "memberType": request.form.get(f"member_{mid}_memberType", "companion"),
                    "nationalId": request.form.get(f"member_{mid}_nationalId", ""),
                    "isHead": request.form.get(f"member_{mid}_isHead") == "true",
                    "isResponder": request.form.get(f"member_{mid}_isResponder") == "true",
                    "isMainProvider": request.form.get(f"member_{mid}_isMainProvider") == "true",
                    "isMainCaregiver": request.form.get(f"member_{mid}_isMainCaregiver") == "true",
                    "needsCare": request.form.get(f"member_{mid}_needsCare") == "true",
                    "schoolAge": 6 <= age <= 18,
                    "educationStatus": request.form.get(f"member_{mid}_educationStatus", "na"),
                    "employmentStatus": request.form.get(f"member_{mid}_employmentStatus", "na"),
                })
        if not members:
            members = assessment.get("members", [])

        # خانوار
        household = assessment.get("household", {})
        household["tenureType"] = request.form.get("tenureType", household.get("tenureType", "tenant"))
        household["monthlyRent"] = _safe_float(request.form.get("monthlyRent"))
        household["monthlyCharge"] = _safe_float(request.form.get("monthlyCharge"))
        household["monthlyBills"] = _safe_float(request.form.get("monthlyBills"))
        household["deposit"] = _safe_float(request.form.get("deposit"))
        household["arrears"] = _safe_float(request.form.get("arrears"))
        household["memberCount"] = len(members)

        # منابع درآمد
        income_sources = []
        income_count = int(request.form.get("income_count", 0) or 0)
        for i in range(income_count):
            income_sources.append({
                "kind": request.form.get(f"income_{i}_kind", ""),
                "monthlyAmount": _safe_float(request.form.get(f"income_{i}_amount")),
                "continuity": request.form.get(f"income_{i}_continuity", "regular"),
                "reliability": request.form.get(f"income_{i}_reliability", "reliable"),
                "receiverMemberId": request.form.get(f"income_{i}_receiver", ""),
            })

        # خط فقر
        poverty_line = {
            "monthlyPerCapita": _safe_float(request.form.get("pl_monthlyPerCapita")),
            "region": request.form.get("pl_region", ""),
            "source": request.form.get("pl_source", ""),
            "validAsOf": request.form.get("pl_validAsOf", ""),
            "status": request.form.get("pl_status", "unverified"),
        }
        household["povertyLine"] = poverty_line

        # به‌روزرسانی assessment
        assessment["answers"] = answers
        assessment["members"] = members
        assessment["household"] = household
        assessment["incomeSources"] = income_sources
        assessment["updatedAt"] = datetime.now().isoformat(timespec="seconds")
        assessment["status"] = "submitted"

        # محاسبه EM-MPI
        result = compute_emmpi(answers, members, household, income_sources, poverty_line)
        assessment["mpiResult"] = result

        # به‌روزرسانی پرونده خانوار
        h["assessment"] = assessment
        h["status"] = "pending"  # آماده تخصیص همیار
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u.get("role", "beneficiary"),
            "action": f"تکمیل خوداظهاری EM-MPI — امتیاز: {result.get('total', 'ناتمام')} — تکمیل: {result.get('completeness', 0)}%"
        })

        # ذخیره EM-MPI در ساختار قدیمی برای سازگاری با CDI
        if result.get("total") is not None:
            h["emmpi"] = {
                "indicators": answers,
                "result": {
                    "score": result["total"],
                    "level": result.get("level", {}),
                    "red_flags": result.get("flags", []),
                    "referral_path": result.get("referrals", [{}])[0] if result.get("referrals") else {},
                    "dominant_dims": result.get("dimensions", []),
                    "needs_cdi": result["total"] >= 300 or any(f["code"] in ("R1","R2","R5") for f in result.get("flags", [])),
                },
                "computed_at": datetime.now().isoformat(timespec="seconds"),
                "computed_by": u.get("role", "beneficiary"),
            }
            h["em_input"]["emmpi_score"] = result["total"]
            h["em_input"]["emmpi_level"] = result.get("level", {}).get("label", "")
            h["em_input"]["em_date"] = datetime.now().strftime("%Y-%m-%d")
            # پرچم‌ها
            rf_map = {"R1": "housing", "R2": "health", "R3": "food", "R4": "education",
                      "R5": "safety", "R6": "caregiving", "R7": "utilities", "R8": "legal", "R9": "shock"}
            redflags = []
            for f in result.get("flags", []):
                cdi_flag = rf_map.get(f["code"])
                if cdi_flag and cdi_flag not in redflags:
                    redflags.append(cdi_flag)
            h["em_input"]["redflags"] = redflags
            h["state"]["redflags"] = redflags

        save_db(db)

        # انتقال به صفحه وضعیت (نمایش نتیجه و انتظار برای تخصیص همیار)
        return redirect(url_for("beneficiary_status", hid=hid))

    # GET: نمایش فرم با داده پیش‌تکمیل
    return render_template("emmpi_form.html", u=u, h=h, hid=hid,
                           assessment=assessment,
                           DIMENSIONS=EMMPI_DIMENSIONS,
                           INDICATOR_TITLES=EMMPI_INDICATOR_TITLES,
                           WEIGHTS=EMMPI_WEIGHTS)


# ═══════════════════════════════════════════════════════════
# پرسشنامه استاتیک (port از porseshnameh-static-v0.9.6)
# ═══════════════════════════════════════════════════════════
@app.route("/questionnaire/")
@app.route("/questionnaire")
def questionnaire_new():
    """صفحه پرسشنامه برای ثبت‌نام جدید (بدون hid) — نیازمند جدید.
    نیاز به لاگین ندارد — برنامه استاتیک مودال ثبت‌نام خودش را نشان می‌دهد."""
    u = current_user() or {"role": "beneficiary"}
    role = u.get("role", "beneficiary")
    idx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "porsesh", "index.html")
    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception:
        return "فایل پرسشنامه یافت نشد", 500
    base_tag = '<base href="/static/porsesh/">'
    html = html.replace('<head>', '<head>' + base_tag, 1)
    # بدون hid → حالت ثبت‌نام جدید
    bridge = f'<script src="/static/bridge.js"></script><script>window.BRIDGE_HID="";window.BRIDGE_ROLE="{role}";</script>'
    html = html.replace('</body>', bridge + '</body>')
    return html


@app.route("/registration-success/<hid>")
def registration_success(hid):
    """صفحه موفقیت پس از تکمیل پرسشنامه — بدون نیاز به لاگین."""
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("login"))
    return render_template("registration_success.html", h=h, hid=hid)


@app.route("/questionnaire/<hid>")
@login_required
def questionnaire_app(hid):
    """سرو کردن برنامه استاتیک پرسشنامه با bridge script — حالت بازبینی همیار."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("questionnaire_new"))
    role = request.args.get("role", u.get("role", "beneficiary"))
    idx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "porsesh", "index.html")
    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception:
        return "فایل پرسشنامه یافت نشد", 500
    base_tag = '<base href="/static/porsesh/">'
    html = html.replace('<head>', '<head>' + base_tag, 1)
    bridge = f'<script src="/static/bridge.js"></script><script>window.BRIDGE_HID="{hid}";window.BRIDGE_ROLE="{role}";</script>'
    html = html.replace('</body>', bridge + '</body>')
    return html


@app.route("/api/assessment/create", methods=["POST"])
def api_create_assessment():
    """ایجاد household جدید از داده پرسشنامه — حالت ثبت‌نام نیازمند.
    نیاز به لاگین ندارد — نیازمند از طریق پرسشنامه ثبت‌نام می‌کند."""
    u = current_user() or {"role": "beneficiary", "name": "نیازمند"}
    data = request.get_json()
    if not data or "assessments" not in data:
        return jsonify({"error": "invalid data"}), 400
    assessments = data["assessments"]
    active_id = data.get("activeId") or next(iter(assessments), "")
    assessment = assessments.get(active_id, {})
    if not assessment:
        return jsonify({"error": "no assessment"}), 400

    # استخراج کد ملی از assessment
    household_data = assessment.get("household", {})
    national_id = household_data.get("headNationalId", "")
    if not national_id:
        # اگر کد ملی در household نیست، از answers بگرد
        national_id = assessment.get("answers", {}).get("headNationalId", "")

    # ساخت hid
    if national_id and len(national_id) >= 6:
        hid = f"H-{national_id[-6:]}"
    else:
        import uuid
        hid = f"H-{uuid.uuid4().hex[:6].upper()}"

    db = load_db()
    # اگر hid قبلاً وجود دارد، به‌روزرسانی
    if hid in db["households"]:
        h = db["households"][hid]
    else:
        h = {
            "identity": {"hid": hid, "national_id": national_id},
            "em_input": {"level": "", "redflags": [], "em_dims": [], "redflag_labels": [],
                         "services_received": [], "em_date": "", "note": ""},
            "state": {"redflags": [], "em_dims": [], "active_axes": [], "answers": {},
                      "created_at": datetime.now().isoformat(timespec="seconds"),
                      "created_by": u.get("role", "beneficiary")},
            "layer2_done": False, "layer3_done": False,
            "decisions": [], "referrals": [], "history": [],
            "preferences": {}, "capacities": [], "causes": [],
            "status": "pending", "claimed_by": None,
            "national_id": national_id,
        }

    # ذخیره assessment
    assessment["status"] = "submitted"
    assessment["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    # ذخیره snapshot پاسخ‌های نیازمند (خوداظهاری) برای مقایسه بعدی با همیار
    assessment["beneficiary_answers"] = dict(assessment.get("answers", {}))
    assessment["beneficiary_submitted_at"] = datetime.now().isoformat(timespec="seconds")
    h["assessment"] = assessment

    # استخراج نام و استان
    civil_data = (assessment.get("webServices", {}).get("civil_registry", {}).get("data", {}))
    head_name = civil_data.get("نام و نام خانوادگی سرپرست", "")
    post_data = assessment.get("webServices", {}).get("post", {}).get("data", {})
    province = post_data.get("استان", "")
    city = post_data.get("شهرستان / منطقه", "")

    h["identity"].update({
        "name": head_name, "province": province, "province_name": province,
        "city": city, "location": f"{province}، {city}" if province else "",
        "members": str(len(assessment.get("members", []))),
        "contact": household_data.get("headMobile", ""),
    })

    # محاسبه EM-MPI
    answers = assessment.get("answers", {})
    members = assessment.get("members", [])
    hh = assessment.get("household", {})
    income_sources = assessment.get("incomeSources", [])
    poverty_line = hh.get("povertyLine", {})
    try:
        result = compute_emmpi(answers, members, hh, income_sources, poverty_line)
        assessment["mpiResult"] = result
        if result.get("total") is not None:
            h["emmpi"] = {
                "indicators": answers, "result": {
                    "score": result["total"], "level": result.get("level", {}),
                    "red_flags": result.get("flags", []),
                    "needs_cdi": result["total"] >= 300 or any(f["code"] in ("R1","R2","R5") for f in result.get("flags", [])),
                },
                "computed_at": datetime.now().isoformat(timespec="seconds"),
                "computed_by": u.get("role", "beneficiary"),
            }
            h["em_input"]["emmpi_score"] = result["total"]
            h["em_input"]["emmpi_level"] = result.get("level", {}).get("label", "")
            h["em_input"]["em_date"] = datetime.now().strftime("%Y-%m-%d")
            rf_map = {"R1":"housing","R2":"health","R3":"food","R4":"education",
                      "R5":"safety","R6":"caregiving","R7":"utilities","R8":"legal","R9":"shock"}
            rfs = []
            for f in result.get("flags", []):
                cf = rf_map.get(f["code"])
                if cf and cf not in rfs: rfs.append(cf)
            h["em_input"]["redflags"] = rfs
            h["state"]["redflags"] = rfs
    except Exception as e:
        print(f"[api_create] EM-MPI error: {e}")

    role = data.get("role", "beneficiary")
    if role == "assistant":
        h["status"] = "emmpi_done" if h.get("emmpi") else "claimed"
    else:
        h["status"] = "pending"

    h["history"].append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "by": u.get("role", role),
        "action": f"تکمیل پرسشنامه استاتیک — امتیاز: {result.get('total', 'ناتمام') if 'result' in dir() else 'نامشخص'}"
    })
    db["households"][hid] = h
    save_db(db)
    return jsonify({"ok": True, "hid": hid})


# ═══════════════════════════════════════════════════════════
# سرویس خط فقر منطقه‌ای — مرکز رصد فقر
# ═══════════════════════════════════════════════════════════
@app.route("/api/poverty-line", methods=["GET", "POST"])
def api_poverty_line():
    """واکشی خط فقر منطقه‌ای از مرکز رصد فقر.
    محاسبه بر اساس: استان، تعداد اعضا، ترکیب سنی، شهری/روستایی.

    GET: /api/poverty-line?province=tehran&members=4&ages=42,38,14,8&urban=1
    POST: {"province": "tehran", "members": [{"age": 42}, ...], "urban": true}
    """
    if request.method == "POST":
        data = request.get_json() or {}
        province_key = data.get("province", "")
        members = data.get("members", [])
        urban = data.get("urban", True)
        postal_code = data.get("postal_code", "")
    else:
        province_key = request.args.get("province", "")
        members_raw = request.args.get("members", "1")
        ages_raw = request.args.get("ages", "")
        urban = request.args.get("urban", "1") in ("1", "true", "True")
        postal_code = request.args.get("postal_code", "")

    # اگر استان مشخص نشده، از کد پستی تشخیص بده
    if not province_key and postal_code:
        detected = detect_province_from_postal_code(postal_code)
        if detected:
            province_key = detected[0]

    # اگر اعضا به‌صورت ages آمده، تبدیل کن
    if isinstance(members_raw, str) and ages_raw:
        ages = [int(a) for a in ages_raw.split(",") if a.strip().isdigit()]
        members = [{"age": a} for a in ages]
    elif isinstance(members_raw, str):
        n = int(members_raw) if members_raw.isdigit() else 1
        members = [{"age": 35} for _ in range(n)]  # سن پیش‌فرض

    if not province_key:
        province_key = "tehran"  # پیش‌فرض

    result = calculate_poverty_line(province_key, members, urban)
    return jsonify(result)


@app.route("/api/assessment/<hid>")
@login_required
def api_get_assessment(hid):
    """بازگرداندن داده assessment برای bridge script."""
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return jsonify({"error": "not found"}), 404
    assessment = h.get("assessment", {})
    # ساخت ساختار منطبق با Zustand store
    assessments = {hid: assessment} if assessment else {}
    return jsonify({"assessments": assessments, "hid": hid})


@app.route("/api/assessment/<hid>", methods=["POST"])
@login_required
def api_save_assessment(hid):
    """ذخیره داده assessment از bridge script."""
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return jsonify({"error": "not found"}), 404
    data = request.get_json()
    if not data or "assessments" not in data:
        return jsonify({"error": "invalid data"}), 400
    assessments = data["assessments"]
    assessment = assessments.get(hid, {})
    if assessment:
        h["assessment"] = assessment
        h["assessment"]["updatedAt"] = datetime.now().isoformat(timespec="seconds")
        save_db(db)
    return jsonify({"ok": True})


@app.route("/api/assessment/<hid>/complete", methods=["POST"])
@login_required
def api_complete_assessment(hid):
    """تکمیل نهایی assessment — ذخیره و انتقال به استخر."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return jsonify({"error": "not found"}), 404
    data = request.get_json()
    if not data or "assessments" not in data:
        return jsonify({"error": "invalid data"}), 400
    assessments = data["assessments"]
    assessment = assessments.get(hid, {})
    if assessment:
        assessment["status"] = "submitted"
        assessment["updatedAt"] = datetime.now().isoformat(timespec="seconds")
        h["assessment"] = assessment

        # ─── محاسبه امتیاز شهروندی (فقط در حالت همیار) ───
        role = data.get("role", "beneficiary")
        if role == "assistant":
            beneficiary_answers = assessment.get("beneficiary_answers", {})
            assistant_answers = assessment.get("answers", {})
            if beneficiary_answers:
                citizenship = compute_citizenship_score(beneficiary_answers, assistant_answers)
                assessment["citizenship_score"] = citizenship
                assessment["assistant_answers"] = dict(assistant_answers)
                assessment["assistant_submitted_at"] = datetime.now().isoformat(timespec="seconds")
                print(f"[api_complete] Citizenship score: {citizenship['score']} ({citizenship['level']}) — {citizenship['changed']} corrections")
            else:
                # اگر snapshot نیازمند موجود نیست (مثلاً نیازمند از سیستم قدیمی آمده)
                assessment["citizenship_score"] = {
                    "score": 100, "level": "H1", "level_label": "بدون مقایسه",
                    "total_keys": 0, "matched": 0, "changed": 0, "corrections": [],
                }

        # محاسبه EM-MPI اگر answers موجود است
        answers = assessment.get("answers", {})
        members = assessment.get("members", [])
        household = assessment.get("household", {})
        income_sources = assessment.get("incomeSources", [])
        poverty_line = household.get("povertyLine", {})
        try:
            result = compute_emmpi(answers, members, household, income_sources, poverty_line)
            assessment["mpiResult"] = result
            # ذخیره در ساختار قدیمی برای CDI
            if result.get("total") is not None:
                h["emmpi"] = {
                    "indicators": answers,
                    "result": {
                        "score": result["total"],
                        "level": result.get("level", {}),
                        "red_flags": result.get("flags", []),
                        "referral_path": result.get("referrals", [{}])[0] if result.get("referrals") else {},
                        "needs_cdi": result["total"] >= 300 or any(f["code"] in ("R1","R2","R5") for f in result.get("flags", [])),
                    },
                    "computed_at": datetime.now().isoformat(timespec="seconds"),
                    "computed_by": u.get("role", "beneficiary"),
                }
                h["em_input"]["emmpi_score"] = result["total"]
                h["em_input"]["emmpi_level"] = result.get("level", {}).get("label", "")
                h["em_input"]["em_date"] = datetime.now().strftime("%Y-%m-%d")
                rf_map = {"R1": "housing", "R2": "health", "R3": "food", "R4": "education",
                          "R5": "safety", "R6": "caregiving", "R7": "utilities", "R8": "legal", "R9": "shock"}
                redflags = []
                for f in result.get("flags", []):
                    cdi_flag = rf_map.get(f["code"])
                    if cdi_flag and cdi_flag not in redflags:
                        redflags.append(cdi_flag)
                h["em_input"]["redflags"] = redflags
                h["state"]["redflags"] = redflags
        except Exception as e:
            print(f"[api_complete] EM-MPI computation error: {e}")
        # وضعیت پرونده
        role = data.get("role", "beneficiary")
        if role == "assistant":
            # همیار در حال بازبینی است
            h["status"] = "emmpi_done" if h.get("emmpi") else "claimed"
        else:
            # نیازمند تکمیل کرده → آماده تخصیص همیار
            h["status"] = "pending"
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u.get("role", role),
            "action": f"تکمیل پرسشنامه استاتیک — امتیاز: {result.get('total', 'ناتمام') if 'result' in dir() else 'نامشخص'}"
        })
        save_db(db)
    return jsonify({"ok": True})


@app.route("/assistant/review/<hid>")
@login_required
def assistant_review(hid):
    """همیار پرسشنامه را با داده پیش‌تکمیل‌شده می‌بیند و می‌تواند اصلاح کند."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    if u["role"] not in ("assistant", "worker", "rose", "swclinic", "caseworker", "manager"):
        return "این بخش فقط برای همیاران قابل دسترسی است.", 403
    # تخصیص به همیار
    if not h.get("claimed_by"):
        h["claimed_by"] = {"id": u.get("id", u.get("role")), "name": u.get("name", ""), "at": datetime.now().isoformat(timespec="seconds")}
        h["status"] = "claimed"
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u.get("role"),
            "action": f"تخصیص پرونده به همیار: {u.get('name', '')}"
        })
        save_db(db)
    # هدایت به برنامه استاتیک با role=assistant
    return redirect(f"/questionnaire/{hid}?role=assistant")


# ═══════════════════════════════════════════════════════════
# استخر درخواست‌ها برای همیاران (مانند اسنپ — بند ۹)
# ═══════════════════════════════════════════════════════════
@app.route("/assistant/pool")
@login_required
def assistant_pool():
    """استخر درخواست‌ها — سه دسته: غربالگری، CDI لایه ۲، CDI لایه ۳."""
    u = current_user()
    db = load_db()

    # فیلتر کانال از query string
    filter_channel = request.args.get("channel", "")

    # ─── سه استخر دسته‌بندی‌شده ───
    pool_screening = []    # استخر ۱: غربالگری (EM-MPI + CDI سریع)
    pool_layer2 = []       # استخر ۲: CDI هدفمند (لایه ۲)
    pool_layer3 = []       # استخر ۳: CDI عمیق (لایه ۳)

    # درخواست‌های تخصیص‌یافته به کاربر فعلی
    my_claims = []

    for hid, h in db["households"].items():
        # فیلتر استانی (مدیر ستاد همه را می‌بیند)
        if u.get("province"):
            hh_prov = h.get("identity", {}).get("province", "")
            user_prov_name = get_province_name(u["province"])
            if hh_prov != u["province"] and hh_prov != user_prov_name:
                continue
        # فیلتر کانال
        hh_channel = h.get("request_channel", "unknown")
        if filter_channel and hh_channel != filter_channel:
            continue

        # درخواست‌های تخصیص‌یافته
        if h.get("claimed_by") and h["claimed_by"].get("id") == u["role"]:
            my_claims.append({"hid": hid, "h": h})

        # محاسبه‌ی match score
        match_score = 0
        match_reasons = []
        if u["role"] in ("assistant", "worker", "rose", "swclinic", "employ"):
            ast = next((a for a in SAMPLE_ASSISTANTS if a["role"] == u["role"]), None)
            if not ast:
                ast = SAMPLE_ASSISTANTS[0] if SAMPLE_ASSISTANTS else {"id": "default", "name": "همیار", "areas": [], "specialties": []}
            loc = (h.get("identity", {}).get("location", "") or "").lower()
            ast_areas = [a.lower() for a in ast.get("areas", [])]
            loc_match = any(a in loc or loc in a for a in ast_areas) if loc else False
            match_score = 50 + (20 if loc_match else 0)
            match_reasons = ["موقعیت منطبق" if loc_match else "سایر مناطق"]

        req_data = {
            "hid": hid, "h": h, "match_score": match_score,
            "match_reasons": match_reasons,
            "channel": hh_channel,
        }

        status = h.get("status", "pending")

        # ─── استخر ۱: غربالگری (status = pending) ───
        # دسترسی: assistant, worker
        if status == "pending":
            if u["role"] in ("assistant", "worker"):
                pool_screening.append(req_data)

        # ─── استخر ۲: CDI هدفمند (status = emmpi_done, layer2 not done) ───
        # دسترسی: assistant, rose, swclinic, employ, worker (review)
        elif status == "emmpi_done" and not h.get("layer2_done"):
            # فقط اگر محورهای فعال وجود داشته باشند
            active_axes = h.get("state", {}).get("active_axes", [])
            if active_axes:
                if u["role"] in ("assistant", "rose", "swclinic", "employ", "worker"):
                    pool_layer2.append(req_data)

        # ─── استخر ۳: CDI عمیق (layer3_required, not done) ───
        # دسترسی: rose, swclinic, worker
        elif status in ("emmpi_done", "cdi_in_progress") and h.get("layer2_done") and not h.get("layer3_done"):
            # بررسی شرایط ورود به لایه ۳
            st = h.get("state", {})
            if st.get("active_axes") or st.get("redflags"):
                st_with_em = {**st, "em_input": h.get("em_input", {})}
                try:
                    res = compute_household(st_with_em)
                    if res and res.get("layer3_required"):
                        if u["role"] in ("rose", "swclinic", "worker"):
                            pool_layer3.append(req_data)
                except Exception:
                    pass

        # پرونده‌های در حال انجام (claimed but not done)
        elif status == "claimed" and h.get("claimed_by", {}).get("id") == u["role"]:
            # این در my_claims اضافه شده
            pass

    # مرتب‌سازی هر استخر بر اساس match score
    pool_screening.sort(key=lambda x: x["match_score"], reverse=True)
    pool_layer2.sort(key=lambda x: x["match_score"], reverse=True)
    pool_layer3.sort(key=lambda x: x["match_score"], reverse=True)

    return render_template("assistant_pool.html", u=u,
                           pool_screening=pool_screening,
                           pool_layer2=pool_layer2,
                           pool_layer3=pool_layer3,
                           my_claims=my_claims,
                           assistant_roles=ASSISTANT_ROLES,
                           match_criteria=MATCH_CRITERIA,
                           REQUEST_CHANNELS=REQUEST_CHANNELS,
                           filter_channel=filter_channel)


# ═══════════════════════════════════════════════════════════
# شبیه‌ساز درخواست‌های تستی (از کانال‌های غیر وب‌سایت)
# ═══════════════════════════════════════════════════════════
import random as _random

FAKE_NAMES = [
    ("علی محمدی", "tehran", "تهران"), ("فاطمه حسینی", "tehran", "تهران"),
    ("حسن رضایی", "isfahan", "اصفهان"), ("زهرا کریمی", "fars", "شیراز"),
    ("مهدی احمدی", "khuzestan", "اهواز"), ("سحر موسوی", "tehran", "تهران"),
    ("رضا صادقی", "kerman", "کرمان"), ("نگار بابایی", "fars", "شیراز"),
    ("امیر کاویانی", "kurdistan", "سنندج"), ("پریسا جعفری", "khorasan_razavi", "مشهد"),
    ("سعید نوری", "bushehr", "بوشهر"), ("الهام رستمی", "sistan_baluchestan", "زاهدان"),
    ("کیان مرادی", "khorasan_south", "بیرجند"), ("مهسا شریفی", "kerman", "کرمان"),
    ("یوسف رحیمی", "sistan_baluchestan", "زاهدان"), ("سمیرا قاسمی", "isfahan", "اصفهان"),
]

FAKE_NEEDS = [
    "کمک هزینه معیشت و غذا", "مشکل مسکن و اجاره معوقه",
    "نیاز به درمان و بیمه", "بیکاری سرپرست خانوار",
    "مشکل تحصیل کودکان", "بدهی بحرانی",
    "نیاز به ابزار کار و اشتغال", "مشکل قطع آب و برق",
]

def _generate_fake_request(channel="phone"):
    """تولید یک درخواست تستی با داده‌های تصادفی."""
    name, prov_key, city_name = _random.choice(FAKE_NAMES)
    nat_id = str(_random.randint(1000000000, 9999999999))
    need = _random.choice(FAKE_NEEDS)
    at_risk = _random.choice(["", "کودکان زیر ۵ سال", "سالمند", "بیمار مزمن", "زن باردار"])
    contact = f"09{_random.randint(100000000, 999999999)}"

    ch_info = next((c for c in REQUEST_CHANNELS if c["code"] == channel), REQUEST_CHANNELS[0])
    prov_info = PROVINCES.get(prov_key, {"name": city_name})
    cities = prov_info.get("cities", [city_name])
    city = _random.choice(cities) if cities else city_name

    # واکشی وب‌سرویس فرضی
    ws_data = fetch_all_services(nat_id, name=name)
    civil = ws_data["civil_registry"]["data"]
    head_name = civil.get("head_name", name)

    hid = f"H-{nat_id[-6:]}"

    return {
        "identity": {
            "hid": hid, "national_id": nat_id, "name": head_name,
            "province": prov_key, "province_name": prov_info.get("name", ""),
            "city": city, "location": f"{prov_info.get('name', '')}، {city}",
            "geo_lat": "", "geo_lng": "",
            "members": str(civil.get("family_size", "")),
            "contact": contact, "at_risk": at_risk,
        },
        "em_input": {"level": "", "redflags": [], "em_dims": [], "redflag_labels": [],
                     "services_received": [], "em_date": "", "note": ""},
        "state": {"redflags": [], "em_dims": [], "active_axes": [], "answers": {},
                  "created_at": datetime.now().isoformat(timespec="seconds"),
                  "created_by": "system"},
        "layer2_done": False, "layer3_done": False,
        "decisions": [], "referrals": [], "history": [],
        "preferences": {}, "capacities": [], "causes": [],
        "national_id": nat_id,
        "request_channel": channel,
        "status": "pending",
        "claimed_by": None,
        "self_declaration": {
            "submitted_at": datetime.now().isoformat(timespec="seconds"),
            "submitted_by": "system",
            "need_description": need,
            "at_risk": at_risk,
        },
        "web_service_data": ws_data,
    }


@app.route("/assistant/simulate", methods=["GET", "POST"])
@login_required
def simulate_requests():
    """شبیه‌ساز درخواست‌های تستی از کانال‌های مختلف."""
    u = current_user()
    if u["role"] not in ("assistant", "worker", "rose", "swclinic", "employ", "hqmanager"):
        return "دسترسی محدود.", 403

    if request.method == "POST":
        channel = request.form.get("channel", "phone")
        count = int(request.form.get("count", 1))
        count = min(count, 10)  # حداکثر ۱۰

        db = load_db()
        created = []
        for _ in range(count):
            req = _generate_fake_request(channel=channel)
            hid = req["identity"]["hid"]
            if hid in db["households"]:
                # رندوم‌سازی مجدد شناسه
                req["identity"]["hid"] = f"H-{_random.randint(100000, 999999)}"
                hid = req["identity"]["hid"]
            req["history"].append({
                "at": datetime.now().isoformat(timespec="seconds"),
                "by": "system",
                "action": f"درخواست تستی از کانال: {channel}"
            })
            db["households"][hid] = req
            created.append({"hid": hid, "name": req["identity"]["name"],
                             "channel": channel, "province": req["identity"]["province_name"]})
        save_db(db)

        return render_template("simulate_requests.html", u=u,
                               created=created, channel=channel,
                               REQUEST_CHANNELS=REQUEST_CHANNELS)

    return render_template("simulate_requests.html", u=u,
                           REQUEST_CHANNELS=REQUEST_CHANNELS)


@app.route("/assistant/claim/<hid>", methods=["POST"])
@login_required
def assistant_claim(hid):
    """همیار یک درخواست را به خود تخصیص می‌دهد (claim)."""
    u = current_user()
    if u["role"] not in ("assistant", "worker", "rose", "swclinic", "employ"):
        return "فقط همیاران مجاز به تخصیص هستند.", 403

    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("assistant_pool"))

    if h.get("status") != "pending":
        return "این درخواست قبلاً تخصیص یافته است.", 400

    # یافتن همیار متناظر
    ast = next((a for a in SAMPLE_ASSISTANTS if a["role"] == u["role"]), None)
    if not ast:
        ast = {
            "id": f"USR-{u['role']}", "name": u["name"],
            "role": u["role"], "role_label": ROLES.get(u["role"], {}).get("label", u["role"]),
        }

    # ثبت تخصیص
    h["status"] = "claimed"
    h["claimed_by"] = {
        "id": ast["id"], "name": ast["name"], "role": ast["role"],
        "role_label": ast.get("role_label", u["role"]),
        "claimed_at": datetime.now().isoformat(timespec="seconds"),
    }
    h["assigned_assistant"] = h["claimed_by"]

    h["history"].append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "by": u["role"],
        "action": f"تخصیص درخواست به همیار: {ast['name']} ({ast.get('role_label', u['role'])})"
    })
    save_db(db)

    # هدایت به بازبینی پرسشنامه (برنامه استاتیک با داده پیش‌تکمل‌شده)
    return redirect(url_for("assistant_review", hid=hid))


# ─────────────────────────────────────────────────────────
# فاز EM-MPI (غربالگری اولیه — قبل از CDI)
# ─────────────────────────────────────────────────────────
@app.route("/emmpi/<hid>", methods=["GET", "POST"])
@login_required
def emmpi_form(hid):
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    if request.method == "POST":
        # جمع‌آوری دادهٔ ۳۵ شاخص
        indicators_data = {}
        for code in EMMPI_INDICATORS:
            val = request.form.get(f"ind_{code}")
            if val is not None and val != "":
                try:
                    indicators_data[code] = float(val)
                except (ValueError, TypeError):
                    pass

        # ─── محاسبهٔ EM-MPI ───
        result = compute_emmpi(indicators_data)

        # ─── محاسبهٔ پروندهٔ شهروندی + امتیاز صداقت ───
        # مقایسهٔ خوداظهاری نیازمند با ارزیابی همیار (تغییرات ثبت‌شده توسط همیار)
        sd_data = h.get("self_declaration", {}) or {}
        # اگر خوداظهاری سؤال‌ها ندارد (درخواست تستی)، یک ساختار خالی می‌دهیم
        if "questions" not in sd_data:
            sd_data["questions"] = {}

        # مقادیر پیش‌فرض خوداظهاری (برای آگاهی همیار از تغییرات)
        prefill_data_for_save = {}
        for sd_key, mapping in SD_TO_EMPI_FULL.items():
            sd_answer = sd_data.get("questions", {}).get(sd_key, "no")
            sd_value = mapping["value_map"].get(sd_answer, 0.0)
            for empi_code in mapping["indicators"]:
                prefill_data_for_save[empi_code] = sd_value

        # محاسبهٔ پروندهٔ شهروندی
        citizen_profile = compute_citizen_profile(sd_data, indicators_data, emmpi_result=result)

        # تشخیص مغایرت‌ها برای نمایش در گزارش
        discrepancies = [item for item in citizen_profile["items"] if item["match_status"] == "mismatched"]
        partial_mismatches = [item for item in citizen_profile["items"] if item["match_status"] == "partial"]
        all_changes = discrepancies + partial_mismatches

        # ذخیره در پروندهٔ خانوار
        h["emmpi"] = {
            "indicators": indicators_data,
            "result": result,
            "computed_at": datetime.now().isoformat(timespec="seconds"),
            "computed_by": u["role"],
            "discrepancies": discrepancies,  # نگه‌داشتن فیلد قدیمی برای backward compat
            "all_changes": all_changes,
            "prefill_from_sd": prefill_data_for_save,
        }
        h["citizen_profile"] = citizen_profile

        # ─── هماهنگ‌سازی با CDI ───
        # ۱. تعیین سطح EM-MPI برای فیلد level قدیمی
        level_map = {
            "L0": "خفیف", "L1": "خفیف", "L2": "متوسط", "L3": "شدید", "L4": "شدید"
        }
        if "em_input" not in h:
            h["em_input"] = {}
        h["em_input"]["level"] = level_map.get(result["level"]["code"], "متوسط")
        h["em_input"]["emmpi_score"] = result["score"]
        h["em_input"]["emmpi_level"] = result["level"]["name"]
        h["em_input"]["emmpi_referral"] = result["referral_path"]["name"]
        h["em_input"]["em_date"] = datetime.now().strftime("%Y-%m-%d")

        # ۲. تبدیل پرچم‌های قرمز EM-MPI به پرچم‌های CDI (redflags)
        # نگاشت R1-R9 → پرچم‌های قرمز CDI
        RF_TO_CDIFLAG = {
            "R1": "housing",      # خطر بی‌خانمانی/تخلیه
            "R2": "health",       # بیماری حیاتی
            "R3": "food",         # فقدان غذا
            "R4": "education",    # کودک در معرض آسیب
            "R5": "safety",       # خشونت خانوادگی
            "R6": "caregiving",   # سالمند/معلول بدون مراقب
            "R7": "utilities",    # قطع خدمات حیاتی
            "R8": "legal",       # بحران حقوقی
            "R9": "shock",        # ریسک از دست‌دادن درآمد/مسکن
        }
        redflags_for_cdi = []
        for rf in result.get("red_flags", []):
            cdi_flag = RF_TO_CDIFLAG.get(rf["code"])
            if cdi_flag and cdi_flag not in redflags_for_cdi:
                redflags_for_cdi.append(cdi_flag)

        # ۳. تعیین ابعاد غالب EM-MPI برای em_dims
        em_dims_map = {"A": "health", "B": "education", "C": "living", "D": "work", "E": "health"}
        em_dims_for_cdi = []
        for d in result.get("dominant_dims", [])[:2]:  # ۲ بُعد غالب
            mapped = em_dims_map.get(d["code"])
            if mapped and mapped not in em_dims_for_cdi:
                em_dims_for_cdi.append(mapped)

        # ۴. ذخیره در em_input و state
        h["em_input"]["redflags"] = redflags_for_cdi
        h["em_input"]["em_dims"] = em_dims_for_cdi
        h["em_input"]["redflag_labels"] = [REDLABELS.get(r, r) for r in redflags_for_cdi]

        h["state"]["redflags"] = redflags_for_cdi
        h["state"]["em_dims"] = em_dims_for_cdi

        # ۵. فعال‌سازی محورهای CDI بر اساس پرچم‌های قرمز (L1: CDI سریع)
        # این کار را فقط در صورتی انجام می‌دهیم که EM-MPI نیاز به CDI داشته باشد
        if result["needs_cdi"] and not h["state"].get("active_axes"):
            h["state"]["active_axes"] = activate_axes(redflags_for_cdi, em_dims_for_cdi, [], [])

        # ۶. ذخیره خدمات قبلی از خوداظهاری (در صورت وجود)
        # این فیلد در فرم قدیمی بود؛ فعلاً خالی می‌ماند

        # ۷. به‌روزرسانی تاریخچه
        flags_str = f" — {len(result['red_flags'])} پرچم قرمز" if result["red_flags"] else " — بدون پرچم قرمز"
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": f"غربالگری EM-MPI: امتیاز {result['score']} — سطح {result['level']['name']}{flags_str}"
        })
        # پروندهٔ شهروندی
        cp = citizen_profile
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": (f"پروندهٔ شهروندی تهیه شد — امتیاز صداقت: {cp['honesty_score']} از ۱۰۰ "
                       f"({cp['honesty_level']['name'] if cp['honesty_level'] else 'نامشخص'}) — "
                       f"{cp['summary']['matched']} انطباق، {cp['summary']['mismatched']} مغایرت")
        })
        if discrepancies:
            h["history"].append({
                "at": datetime.now().isoformat(timespec="seconds"),
                "by": u["role"],
                "action": f"⚠ {len(discrepancies)} مغایرت کامل با خوداظهاری نیازمند شناسایی شد"
            })
        if redflags_for_cdi:
            h["history"].append({
                "at": datetime.now().isoformat(timespec="seconds"),
                "by": u["role"],
                "action": f"فعال‌سازی {len(h['state']['active_axes'])} محور CDI بر اساس پرچم‌های قرمز EM-MPI"
            })

        # ۸. شارژ کیف پول همیار (در انتظار تأیید مددکار)
        # تعیین اولویت برای ضریب هزینه
        score = result.get("score", 0)
        rf = result.get("red_flags", [])
        if score >= 600 or rf:
            emmpi_priority = "P0"
        elif score >= 450:
            emmpi_priority = "P1"
        elif score >= 300:
            emmpi_priority = "P2"
        elif score >= 150:
            emmpi_priority = "P3"
        else:
            emmpi_priority = "P4"

        # نوع خدمت: EM-MPI عادی یا با پرچم قرمز
        svc_type = "emmpi_redflag" if rf else "emmpi_assessment"
        svc_cost = compute_service_cost(svc_type, role=u["role"], priority=emmpi_priority)
        # یافتن شناسهٔ کاربر (id از session)
        user_id = u.get("id", session.get("uid", ""))
        credit_wallet_pending(user_id, svc_cost, svc_type, hid=hid,
                              note=f"EM-MPI برای {h.get('identity', {}).get('name', hid)} — امتیاز {score}")
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": f"شارژ کیف پول: {svc_cost} تومان (در انتظار تأیید) — {get_service_label(svc_type)}"
        })

        # به‌روزرسانی وضعیت پرونده
        # ─── اگر امتیاز زیر ۱۵۰ و بدون پرچم قرمز → غیرنیازمند ───
        if result["score"] < 150 and not result.get("red_flags"):
            h["status"] = "not_eligible"
            h["emmpi"]["not_eligible"] = True
            h["emmpi"]["not_eligible_reason"] = "امتیاز زیر ۱۵۰ و بدون پرچم قرمز"
            h["emmpi"]["not_eligible_at"] = datetime.now().isoformat(timespec="seconds")
            h["history"].append({
                "at": datetime.now().isoformat(timespec="seconds"),
                "by": u["role"],
                "action": f"خروج از چرخه فرایند: امتیاز {result['score']} زیر ۱۵۰ — غیرنیازمند ثبت شد (امکان اعتراض وجود دارد)"
            })
        else:
            h["status"] = "emmpi_done"

        save_db(db)
        return redirect(url_for("emmpi_result", hid=hid))

    # GET: نمایش فرم
    existing_data = None
    if h.get("emmpi") and h["emmpi"].get("indicators"):
        existing_data = h["emmpi"]["indicators"]

    # ─── پیش‌پر کردن از خوداظهاری نیازمند ───
    # با استفاده از نگاشت جامع SD_TO_EMPI_FULL
    prefill_data = {}  # {indicator_code: severity_value}
    prefill_sd_source = {}  # {indicator_code: {sd_key, sd_answer, sd_label}} برای نمایش علت
    sd_questions = h.get("self_declaration", {}).get("questions", {})
    if sd_questions and not existing_data:
        for sd_key, mapping in SD_TO_EMPI_FULL.items():
            if sd_key not in sd_questions:
                continue
            sd_answer = sd_questions[sd_key]
            sd_value = mapping["value_map"].get(sd_answer, 0.0)
            for empi_code in mapping["indicators"]:
                if sd_value > 0:
                    prefill_data[empi_code] = sd_value
                prefill_sd_source[empi_code] = {
                    "sd_key": sd_key,
                    "sd_answer": sd_answer,
                    "sd_label": mapping["label"],
                    "sd_value": sd_value,
                }

    indicators_by_dim = get_indicator_list_by_dim()
    # افزودن dim_label به هر شاخص
    for dim_key, inds in indicators_by_dim.items():
        for ind in inds:
            ind["dim_label"] = EMMPI_DIMENSIONS[dim_key]["name"]

    return render_template("emmpi_form.html", h=h, hid=hid, u=u,
                           DIMENSIONS=EMMPI_DIMENSIONS,
                           indicators_by_dim=indicators_by_dim,
                           severity_options=SEVERITY_OPTIONS,
                           existing_data=existing_data,
                           prefill_data=prefill_data,
                           prefill_sd_source=prefill_sd_source,
                           sd_questions=sd_questions)


@app.route("/emmpi/<hid>/result")
@login_required
def emmpi_result(hid):
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    if not h.get("emmpi"):
        return redirect(url_for("emmpi_form", hid=hid))

    result = h["emmpi"]["result"]
    assistant_suggestions = suggest_assistant(result, h.get("identity", {}).get("location"))

    # فهرست اندپوینت‌ها برای قالب
    endpoints = []
    try:
        endpoints = [rule.endpoint for rule in app.url_map.iter_rules()]
    except Exception:
        pass

    return render_template("emmpi_result.html", h=h, hid=hid, u=u, result=result,
                           DIMENSIONS=EMMPI_DIMENSIONS,
                           ai_red_lines=EMMPI_AI_RED_LINES,
                           assistant_suggestions=assistant_suggestions,
                           endpoints=endpoints)


# ─────────────────────────────────────────────────────────
# پرسشنامه EM-MPI نسخه ۲ — مستقل، مطابق PN-QP-1405-01
# ─────────────────────────────────────────────────────────
@app.route("/emmpi-v2")
@login_required
def emmpi_v2_form():
    """ویزارد ۱۰ گامی پرسشنامه غربالگری خانوار مبتنی بر EM-MPI نسخه ۲."""
    u = current_user()
    return render_template("emmpi_form.html", u=u, hid=None, h=None, assessment={})


@app.route("/emmpi-v2/submit", methods=["POST"], endpoint="emmpi_submit")
@login_required
def emmpi_v2_submit():
    """پردازش فرم EM-MPI نسخه ۲ و محاسبه نتیجه قطعی."""
    u = current_user()
    form = request.form

    # ۱) جمع‌آوری answers از فرم
    answers = {}
    # فیلدهای ساده (تک‌گزینشی، متنی، عددی)
    simple_fields = [
        "A4_burden", "A6_now", "A7_disrupt",
        "B3_lit", "B4_barriers", "B4_detail", "B5_digital", "B7_path", "B7_skills",
        "C1_place", "C1_eviction", "C2_constr",
        "C3_right", "C3_lease_end", "C4_rooms", "C4_area", "C4_safesleep",
        "C5_water", "C5_elec", "C5_cook", "C5_effect", "C6_san",
        "C7_impact", "C8_arrears_severity", "C8_installments",
        "C9_access", "D1_no_provider",
        "E1_outlook", "E1_evidence", "E2_support", "E2_hours",
        "E3_support", "E3_who", "E4_barrier", "E4_service",
    ]
    for f in simple_fields:
        v = form.get(f)
        if v is not None and v != "":
            answers[f] = v

    # فیلدهای چندانتخابی (لیست)
    multi_fields = ["A4_effects", "A6_exp", "A7_danger", "C2_issues",
                    "C7_missing", "E4_types"]
    for f in multi_fields:
        vals = form.getlist(f)
        if vals:
            answers[f] = vals

    # فیلدهای عضومحور با پسوند #memberId
    member_question_prefixes = [
        "A1_disease", "A1_impact", "A2_limit", "A2_aid",
        "A3_treatment", "A3_urgent", "A3_cause", "A5_cover", "A5_barrier",
        "A_malnut", "A_pregnant",
        "B1_status", "B1_months", "B1_reason", "B2_risks",
        "B6_need",
        "D1_ability", "D1_continuity", "D1_seasonal",
    ]
    for key in form.keys():
        for prefix in member_question_prefixes:
            if key.startswith(prefix + "#"):
                answers[key] = form.get(key)
                break

    # ۲) جمع‌آوری اعضا
    members = []
    member_first_names = form.getlist("member_firstName") if "member_firstName" in form else []
    # اگر از جدول داینامیک است، داده‌ها با data-field هستند
    # در فرم فعلی، اعضا در جدول با input[name] داینامیک هستند
    # برای سادگی، اعضا را از فیلدهای مخفی جمع‌آوری می‌کنیم
    # در عمل، JavaScript باید داده اعضا را در فیلدهای نام‌گذاری‌شده قرار دهد
    # اینجا یک رویکرد ساده: جمع‌آوری از فیلدهای با prefix "member_"
    member_ids_raw = form.get("member_ids", "")
    if member_ids_raw:
        for mid in member_ids_raw.split(","):
            if not mid.strip():
                continue
            mid = mid.strip()
            age_str = form.get(f"member_{mid}_age", "0")
            try:
                age = int(age_str)
            except (ValueError, TypeError):
                age = 0
            members.append({
                "id": mid,
                "firstName": form.get(f"member_{mid}_firstName", ""),
                "lastName": form.get(f"member_{mid}_lastName", ""),
                "age": age,
                "gender": form.get(f"member_{mid}_gender", "male"),
                "relation": form.get(f"member_{mid}_relation", "سایر"),
                "memberType": form.get(f"member_{mid}_memberType", "companion"),
                "nationalId": form.get(f"member_{mid}_nationalId", ""),
                "isHead": form.get(f"member_{mid}_isHead") == "true",
                "isResponder": form.get(f"member_{mid}_isResponder") == "true",
                "isMainProvider": form.get(f"member_{mid}_isMainProvider") == "true",
                "isMainCaregiver": form.get(f"member_{mid}_isMainCaregiver") == "true",
                "needsCare": form.get(f"member_{mid}_needsCare") == "true",
                "schoolAge": 6 <= age <= 18,
                "educationStatus": form.get(f"member_{mid}_educationStatus", "na"),
                "employmentStatus": form.get(f"member_{mid}_employmentStatus", "na"),
            })

    # اگر اعضایی در فرم نبودند، یک سرپرست پیش‌فرض
    if not members:
        members = [{
            "id": "m1", "firstName": "سرپرست", "lastName": "", "age": 30,
            "gender": "male", "relation": "سرپرست", "memberType": "registry",
            "isHead": True, "isResponder": True, "isMainProvider": True,
            "schoolAge": False, "educationStatus": "na", "employmentStatus": "employed",
        }]

    # ۳) اطلاعات خانوار
    household = {
        "tenureType": form.get("tenureType", "tenant"),
        "monthlyRent": _safe_float(form.get("monthlyRent")),
        "monthlyCharge": _safe_float(form.get("monthlyCharge")),
        "monthlyBills": _safe_float(form.get("monthlyBills")),
        "deposit": _safe_float(form.get("deposit")),
        "arrears": _safe_float(form.get("arrears")),
        "memberCount": len(members),
    }

    # ۴) منابع درآمد
    income_sources = []
    income_count = int(form.get("income_count", 0) or 0)
    for i in range(income_count):
        amt = _safe_float(form.get(f"income_{i}_amount"))
        income_sources.append({
            "kind": form.get(f"income_{i}_kind", ""),
            "monthlyAmount": amt,
            "continuity": form.get(f"income_{i}_continuity", "regular"),
            "reliability": form.get(f"income_{i}_reliability", "reliable"),
            "receiverMemberId": form.get(f"income_{i}_receiver", ""),
        })

    # ۵) خط فقر
    pl_per_capita = _safe_float(form.get("pl_monthlyPerCapita"))
    poverty_line = {
        "monthlyPerCapita": pl_per_capita,
        "region": form.get("pl_region", ""),
        "source": form.get("pl_source", ""),
        "validAsOf": form.get("pl_validAsOf", ""),
        "status": form.get("pl_status", "unverified"),
    }

    # ۶) محاسبه EM-MPI
    result = compute_emmpi(answers, members, household, income_sources, poverty_line)

    # ۷) ذخیره در session برای نمایش نتیجه
    session["emmpi_v2_result"] = result
    session["emmpi_v2_meta"] = {
        "household_head": form.get("headNationalId", ""),
        "computed_by": u.get("role", "system"),
        "registration_kind": form.get("registrationKind", "need_service"),
        "members_count": len(members),
    }

    return redirect(url_for("emmpi_v2_result"))


@app.route("/emmpi-v2/result")
@login_required
def emmpi_v2_result():
    """نمایش نتیجه پرسشنامه EM-MPI نسخه ۲."""
    u = current_user()
    result = session.get("emmpi_v2_result")
    meta = session.get("emmpi_v2_meta", {})
    if not result:
        return redirect(url_for("emmpi_v2_form"))
    return render_template("emmpi_result_v2.html", u=u, result=result, meta=meta,
                           DIMENSIONS=EMMPI_DIMENSIONS, ai_red_lines=EMMPI_AI_RED_LINES)


def _safe_float(v, default=0.0):
    """تبدیل ایمن به float"""
    if v is None or v == "":
        return default
    try:
        return float(str(v).replace(",", "").replace("،", ""))
    except (ValueError, TypeError):
        return default


# ─────────────────────────────────────────────────────────
# اعتراض به نتیجه EM-MPI (برای پرونده‌های غیرنیازمند)
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/appeal", methods=["POST"])
@login_required
def emmpi_appeal(hid):
    """ثبت اعتراض به نتیجه EM-MPI — برای پرونده‌های غیرنیازمند (زیر ۱۵۰)."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    appeal_reason = request.form.get("appeal_reason", "").strip()
    if not appeal_reason:
        return "دلیل اعتراض الزامی است.", 400

    # ثبت اعتراض
    if "appeals" not in h:
        h["appeals"] = []

    appeal = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "by": u["role"],
        "by_name": u.get("name", u["role"]),
        "reason": appeal_reason,
        "status": "pending",  # pending | approved | rejected
        "emmpi_score": h.get("emmpi", {}).get("result", {}).get("score", 0),
    }
    h["appeals"].append(appeal)

    # بازگرداندن به چرخه فرایند (در انتظار بررسی)
    h["status"] = "appeal_pending"

    h["history"].append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "by": u["role"],
        "action": f"اعتراض ثبت شد: {appeal_reason[:100]}"
    })

    save_db(db)
    return redirect(url_for("emmpi_result", hid=hid))


@app.route("/household/<hid>/appeal/<int:idx>/resolve", methods=["POST"])
@login_required
def resolve_appeal(hid, idx):
    """بررسی اعتراض توسط مددکار/مدیر."""
    u = current_user()
    if u["role"] not in ("worker", "hqmanager"):
        return "فقط مددکار یا مدیر ستاد مجاز به بررسی اعتراض هستند.", 403

    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    if "appeals" not in h or idx >= len(h["appeals"]):
        return redirect(url_for("household_view", hid=hid))

    decision = request.form.get("decision", "")
    note = request.form.get("note", "")

    if decision == "approve":
        # تأیید اعتراض → بازگرداندن به چرخه
        h["appeals"][idx]["status"] = "approved"
        h["appeals"][idx]["resolved_by"] = u["role"]
        h["appeals"][idx]["resolved_at"] = datetime.now().isoformat(timespec="seconds")
        h["appeals"][idx]["resolve_note"] = note
        h["status"] = "emmpi_done"
        h["emmpi"]["not_eligible"] = False
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": f"اعتراض تأیید شد — پرونده به چرخه فرایند بازگردانده شد"
        })
    elif decision == "reject":
        h["appeals"][idx]["status"] = "rejected"
        h["appeals"][idx]["resolved_by"] = u["role"]
        h["appeals"][idx]["resolved_at"] = datetime.now().isoformat(timespec="seconds")
        h["appeals"][idx]["resolve_note"] = note
        h["status"] = "not_eligible"
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": f"اعتراض رد شد — پرونده غیرنیازمند باقی ماند"
        })

    save_db(db)
    return redirect(url_for("household_view", hid=hid))


# ─────────────────────────────────────────────────────────
# صفحهٔ بررسی اعتراض با امکان اصلاح EM-MPI + لاگ تغییرات
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/appeal-review", methods=["GET", "POST"])
@login_required
def appeal_review(hid):
    """بررسی اعتراض با امکان مشاهده و اصلاح نتیجه EM-MPI — با لاگ کامل تغییرات."""
    u = current_user()
    if u["role"] not in ("worker", "rose", "swclinic", "hqmanager"):
        return "بررسی اعتراض فقط برای مددکار، کلینیک‌ها یا مدیر ستاد مجاز است.", 403
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    if request.method == "POST":
        action_type = request.form.get("action_type", "")

        if action_type == "modify_emmpi":
            # ─── اصلاح شاخص‌های EM-MPI ───
            old_indicators = dict(h.get("emmpi", {}).get("indicators", {}))
            new_indicators = {}
            for code in EMMPI_INDICATORS:
                val = request.form.get(f"ind_{code}")
                if val is not None and val != "":
                    try:
                        new_indicators[code] = float(val)
                    except (ValueError, TypeError):
                        pass

            # محاسبهٔ جدید
            new_result = compute_emmpi(new_indicators)

            # تشخیص تغییرات
            changes = []
            for code in EMMPI_INDICATORS:
                old_val = old_indicators.get(code)
                new_val = new_indicators.get(code)
                if old_val != new_val:
                    changes.append({
                        "code": code,
                        "title": EMMPI_INDICATORS[code].get("title", code),
                        "old_value": old_val,
                        "new_value": new_val,
                        "dim": EMMPI_INDICATORS[code].get("dim", ""),
                    })

            # ذخیرهٔ لاگ تغییرات
            if "emmpi_audit_log" not in h:
                h["emmpi_audit_log"] = []
            audit_entry = {
                "at": datetime.now().isoformat(timespec="seconds"),
                "by": u["role"],
                "by_name": u.get("name", u["role"]),
                "action": "اصلاح شاخص‌های EM-MPI",
                "old_score": h.get("emmpi", {}).get("result", {}).get("score", 0),
                "new_score": new_result["score"],
                "old_level": h.get("emmpi", {}).get("result", {}).get("level", {}).get("name", "—"),
                "new_level": new_result["level"]["name"],
                "changes_count": len(changes),
                "changes": changes,
                "reason": request.form.get("modify_reason", ""),
            }
            h["emmpi_audit_log"].append(audit_entry)

            # به‌روزرسانی EM-MPI
            h["emmpi"]["indicators"] = new_indicators
            h["emmpi"]["result"] = new_result
            h["emmpi"]["modified_at"] = datetime.now().isoformat(timespec="seconds")
            h["emmpi"]["modified_by"] = u["role"]
            h["emmpi"]["modified_by_name"] = u.get("name", u["role"])

            # به‌روزرسانی not_eligible
            if new_result["score"] >= 150 or new_result.get("red_flags"):
                h["emmpi"]["not_eligible"] = False
                h["emmpi"]["not_eligible_reason"] = ""
                h["status"] = "emmpi_done"
            else:
                h["emmpi"]["not_eligible"] = True

            h["history"].append({
                "at": datetime.now().isoformat(timespec="seconds"),
                "by": u["role"],
                "action": (f"اصلاح EM-MPI توسط {u.get('name', u['role'])} — "
                           f"امتیاز {audit_entry['old_score']} → {new_result['score']} "
                           f"({len(changes)} شاخص تغییر کرد)")
            })
            save_db(db)
            return redirect(url_for("appeal_review", hid=hid))

        elif action_type == "approve_appeal":
            # تأیید اعتراض
            appeal_idx = int(request.form.get("appeal_idx", 0))
            if "appeals" in h and appeal_idx < len(h["appeals"]):
                h["appeals"][appeal_idx]["status"] = "approved"
                h["appeals"][appeal_idx]["resolved_by"] = u["role"]
                h["appeals"][appeal_idx]["resolved_by_name"] = u.get("name", u["role"])
                h["appeals"][appeal_idx]["resolved_at"] = datetime.now().isoformat(timespec="seconds")
                h["appeals"][appeal_idx]["resolve_note"] = request.form.get("note", "")
                h["status"] = "emmpi_done"
                h["emmpi"]["not_eligible"] = False
                h["history"].append({
                    "at": datetime.now().isoformat(timespec="seconds"),
                    "by": u["role"],
                    "action": f"اعتراض تأیید شد توسط {u.get('name', u['role'])} — پرونده به چرخه بازگشت"
                })
            save_db(db)
            return redirect(url_for("household_view", hid=hid))

        elif action_type == "reject_appeal":
            appeal_idx = int(request.form.get("appeal_idx", 0))
            if "appeals" in h and appeal_idx < len(h["appeals"]):
                h["appeals"][appeal_idx]["status"] = "rejected"
                h["appeals"][appeal_idx]["resolved_by"] = u["role"]
                h["appeals"][appeal_idx]["resolved_by_name"] = u.get("name", u["role"])
                h["appeals"][appeal_idx]["resolved_at"] = datetime.now().isoformat(timespec="seconds")
                h["appeals"][appeal_idx]["resolve_note"] = request.form.get("note", "")
                h["status"] = "not_eligible"
                h["history"].append({
                    "at": datetime.now().isoformat(timespec="seconds"),
                    "by": u["role"],
                    "action": f"اعتراض رد شد توسط {u.get('name', u['role'])} — پرونده غیرنیازمند باقی ماند"
                })
            save_db(db)
            return redirect(url_for("household_view", hid=hid))

    # GET — نمایش صفحهٔ بررسی
    result = h.get("emmpi", {}).get("result", {})
    indicators = h.get("emmpi", {}).get("indicators", {})
    appeals = h.get("appeals", [])
    audit_log = h.get("emmpi_audit_log", [])

    # فهرست شاخص‌ها به تفکیک بُعد
    indicators_by_dim = get_indicator_list_by_dim()
    for dim_key, inds in indicators_by_dim.items():
        for ind in inds:
            ind["dim_label"] = EMMPI_DIMENSIONS[dim_key]["name"]
            ind["current_value"] = indicators.get(ind["code"])

    return render_template("appeal_review.html", h=h, hid=hid, u=u,
                           result=result,
                           indicators=indicators,
                           indicators_by_dim=indicators_by_dim,
                           DIMENSIONS=EMMPI_DIMENSIONS,
                           SEVERITY_OPTIONS=SEVERITY_OPTIONS,
                           appeals=appeals,
                           audit_log=audit_log)
# ═══════════════════════════════════════════════════════════
@app.route("/emmpi/<hid>/match")
@login_required
def assistant_match(hid):
    """نمایش صفحهٔ تخصیص هوشمند همیار — پیشنهاد سامانه + تأیید/انتخاب."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    if not h.get("emmpi"):
        return redirect(url_for("emmpi_form", hid=hid))

    emmpi_result = h["emmpi"]["result"]
    matches = match_assistants(emmpi_result, h)

    # بررسی اینکه آیا قبلاً همیار تخصیص یافته
    assigned = h.get("assigned_assistant")

    return render_template("assistant_match.html", h=h, hid=hid, u=u,
                           matches=matches, assigned=assigned,
                           assistant_roles=ASSISTANT_ROLES,
                           match_criteria=MATCH_CRITERIA,
                           emmpi_result=emmpi_result)


@app.route("/emmpi/<hid>/assign/<ast_id>", methods=["POST"])
@login_required
def assign_assistant(hid, ast_id):
    """تخصیص همیار به پروندهٔ خانوار."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    if not h.get("emmpi"):
        return redirect(url_for("emmpi_form", hid=hid))

    # یافتن همیار از فهرست نمونه
    ast = next((a for a in SAMPLE_ASSISTANTS if a["id"] == ast_id), None)
    if not ast:
        return "همیار یافت نشد.", 404

    # ثبت تخصیص
    h["assigned_assistant"] = {
        "id": ast["id"], "name": ast["name"], "role": ast["role"],
        "role_label": ast["role_label"], "assigned_at": datetime.now().isoformat(timespec="seconds"),
        "assigned_by": u["role"],
    }

    # افزایش بار کاری همیار (در نمونهٔ اولیه — در سیستم واقعی دیتابیس جداگانه)
    ast["current_load"] = min(ast["current_load"] + 1, ast["capacity_max"])

    # تاریخچه
    h["history"].append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "by": u["role"],
        "action": f"تخصیص همیار: {ast['name']} ({ast['role_label']})"
    })

    save_db(db)
    return redirect(url_for("assistant_match", hid=hid))


@app.route("/emmpi/<hid>/unassign", methods=["POST"])
@login_required
def unassign_assistant(hid):
    """لغو تخصیص همیار."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    if h.get("assigned_assistant"):
        old = h["assigned_assistant"]
        # کاهش بار کاری
        ast = next((a for a in SAMPLE_ASSISTANTS if a["id"] == old["id"]), None)
        if ast:
            ast["current_load"] = max(0, ast["current_load"] - 1)
        h["assigned_assistant"] = None
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": f"لغو تخصیص همیار: {old['name']}"
        })
        save_db(db)

    return redirect(url_for("assistant_match", hid=hid))


# مسیر شروع CDI پس از تأیید EM-MPI
@app.route("/household/<hid>/start-cdi")
@login_required
def household_new_cdi(hid):
    """شروع فاز CDI برای خانواری که EM-MPI را تکمیل کرده است."""
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    if not h.get("emmpi"):
        return redirect(url_for("emmpi_form", hid=hid))
    # فعال‌سازی محورهای CDI بر اساس پرچم‌های قرمز EM-MPI
    # این منطق در cdi_engine.activate_axes پیاده‌سازی شده
    return redirect(url_for("household_view", hid=hid))


# ─────────────────────────────────────────────────────────
# مرحله ۱: ثبت درخواست اولیه (پیش از EM-MPI)
# ─────────────────────────────────────────────────────────
@app.route("/household/new", methods=["GET", "POST"])
@login_required
def household_new():
    u = current_user()
    if request.method == "POST":
        hid = request.form.get("hid", "").strip()
        if not hid:
            return render_template("household_new.html", u=u, error="شناسهٔ خانوار الزامی است.")
        db = load_db()
        if hid in db["households"]:
            return render_template("household_new.html", u=u, error="این شناسه از قبل موجود است.")
        # ساخت پروندهٔ اولیه — بدون پرچم‌های قرمز
        # پرچم‌های قرمز در مرحلهٔ EM-MPI (غربالگری) شناسایی و ثبت می‌شوند
        h = {
            "identity": {
                "hid": hid, "name": request.form.get("name", ""),
                "location": request.form.get("location", ""),
                "members": request.form.get("members", ""),
                "contact": request.form.get("contact", ""),
                "at_risk": request.form.get("at_risk", ""),
            },
            "em_input": {
                # این فیلدها بعداً از نتایج EM-MPI تکمیل می‌شوند
                "level": "", "redflags": [], "em_dims": [],
                "redflag_labels": [], "services_received": [],
                "em_date": "", "note": "",
            },
            "state": {
                "redflags": [], "em_dims": [],
                "active_axes": [], "answers": {},
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "created_by": session["uid"],
            },
            "layer2_done": False, "layer3_done": False,
            "decisions": [], "referrals": [], "history": [],
            "preferences": {}, "capacities": [], "causes": [],
            "request_channel": request.form.get("request_channel", "in_person"),
        }
        # ثبت رویداد در تاریخچه
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": session["uid"],
            "action": "ثبت درخواست اولیه — مرحلهٔ ۱"
        })
        db["households"][hid] = h
        save_db(db)
        # هدایت خودکار به مرحلهٔ ۲: غربالگری EM-MPI
        return redirect(url_for("emmpi_form", hid=hid))
    return render_template("household_new.html", u=u)


REDLABELS = {
    "food": "ناامنی غذایی", "housing": "ناامنی مسکن", "health": "بحران سلامت",
    "caregiving": "بار مراقبتی", "safety": "خشونت/خطر حفاظتی", "utilities": "قطع خدمات حیاتی",
    "shock": "ریسک شوک", "education": "خطر ترک تحصیل", "identity": "فقدان مدارک",
    "transport": "مانع رفت‌وآمد", "digital": "محرومیت دیجیتال", "service_qual": "کیفیت خدمت",
    "employment": "بیکاری/اشتغال ناپایدار", "debt": "بدهی بحرانی", "insurance": "فقدان بیمه",
    "literacy": "ضعف سواد پایه", "mental": "فشار روانی شدید", "physical": "محدودیت جسمی",
    "motivation": "افت انگیزه", "network": "ضعف شبکه حمایت", "isolation": "انزوای اجتماعی",
    "discrimination": "تبعیض/طرد", "geography": "مانع جغرافیایی", "legal": "مانع حقوقی",
}
EMLABELS = {"health": "سلامت", "education": "آموزش", "living": "شرایط زندگی", "work": "اشتغال"}


# ─────────────────────────────────────────────────────────
# نمایش پرونده
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>")
@login_required
def household_view(hid):
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    st = h["state"]
    if st.get("active_axes") or st.get("redflags"):
        st_with_em = {**st, "em_input": h.get("em_input", {})}
        res = compute_household(st_with_em)
    else:
        res = None
    sugg = system_suggestions(res) if res else []
    pending = [r for r in h.get("referrals", []) if r["status"] == "pending"]
    my_referrals = [r for r in pending if r["to"] == u["role"]]
    return render_template("household_view.html", h=h, hid=hid, res=res, sugg=sugg,
                           u=u, pending=pending, my_referrals=my_referrals,
                           redlabels=REDLABELS, emlabels=EMLABELS, roles=ROLES,
                           priority_classes=PRIORITY_CLASSES, stages=STAGES,
                           actors=ACTORS, action_ranks=ACTION_RANKS)


# ─────────────────────────────────────────────────────────
# پروندهٔ شهروندی + امتیاز صداقت (مقایسهٔ خوداظهاری با ارزیابی همیار)
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/citizen-profile")
@login_required
def citizen_profile_view(hid):
    """پروندهٔ شهروندی — شامل خوداظهاری، ارزیابی همیار، امتیاز صداقت در ابعاد ۵گانه."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    # اگر هنوز EM-MPI انجام نشده، نمی‌توان پرونده تهیه کرد
    if not h.get("emmpi"):
        return render_template("citizen_profile.html", h=h, hid=hid, u=u,
                               not_ready=True,
                               SD_ANSWER_LABELS=SD_ANSWER_LABELS,
                               EMPI_SEVERITY_LABELS=EMPI_SEVERITY_LABELS,
                               HONESTY_LEVELS=HONESTY_LEVELS,
                               DIMENSIONS=EMMPI_DIMENSIONS)

    # محاسبهٔ دوبارهٔ پرونده (در صورت نیاز) یا استفاده از مقدار ذخیره‌شده
    cp = h.get("citizen_profile")
    if not cp:
        # اگر پروندهٔ شهروندی قبلاً محاسبه نشده، اکنون محاسبه کن
        sd_data = h.get("self_declaration", {}) or {}
        if "questions" not in sd_data:
            sd_data["questions"] = {}
        indicators_data = h.get("emmpi", {}).get("indicators", {}) or {}
        emmpi_result = h.get("emmpi", {}).get("result")
        cp = compute_citizen_profile(sd_data, indicators_data, emmpi_result=emmpi_result)
        h["citizen_profile"] = cp
        save_db(db)

    emmpi_info = h.get("emmpi", {})
    emmpi_result = emmpi_info.get("result", {})
    sd_data = h.get("self_declaration", {}) or {}

    return render_template("citizen_profile.html", h=h, hid=hid, u=u,
                           cp=cp,
                           emmpi_result=emmpi_result,
                           sd_data=sd_data,
                           emmpi_indicators=emmpi_info.get("indicators", {}),
                           SD_ANSWER_LABELS=SD_ANSWER_LABELS,
                           EMPI_SEVERITY_LABELS=EMPI_SEVERITY_LABELS,
                           HONESTY_LEVELS=HONESTY_LEVELS,
                           DIMENSIONS=EMMPI_DIMENSIONS,
                           not_ready=False)


# ─────────────────────────────────────────────────────────
# گزارش پرونده‌های شهروندی برای مدیران و کلینیک‌ها
# ─────────────────────────────────────────────────────────
@app.route("/hq/citizen-profiles")
@login_required
def citizen_profiles_report():
    """گزارش پرونده‌های شهروندی همهٔ خانوارها — برای مددکار، کلینیک، مدیر."""
    u = current_user()
    db = load_db()
    hhs = list(db["households"].items())

    # فیلتر استانی (مدیر ستاد همه را می‌بیند)
    if u.get("province"):
        hhs = [(hid, h) for hid, h in hhs
               if h.get("identity", {}).get("province", "") == u["province"]]

    rows = []
    for hid, h in hhs:
        emmpi = h.get("emmpi", {})
        cp = h.get("citizen_profile")
        if not emmpi:
            continue  # هنوز ارزیابی نشده

        # اگر پروندهٔ شهروندی نبود، اکنون بساز
        if not cp:
            sd_data = h.get("self_declaration", {}) or {}
            if "questions" not in sd_data:
                sd_data["questions"] = {}
            indicators_data = emmpi.get("indicators", {}) or {}
            emmpi_result = emmpi.get("result")
            cp = compute_citizen_profile(sd_data, indicators_data, emmpi_result=emmpi_result)
            h["citizen_profile"] = cp
        rows.append({
            "hid": hid,
            "name": h.get("identity", {}).get("name", hid),
            "province": h.get("identity", {}).get("province_name", "—"),
            "emmpi_score": emmpi.get("result", {}).get("score", 0),
            "emmpi_level": emmpi.get("result", {}).get("level", {}).get("name", "—"),
            "honesty_score": cp["honesty_score"],
            "honesty_level": cp["honesty_level"]["name"] if cp["honesty_level"] else "—",
            "matched": cp["summary"]["matched"],
            "partial": cp["summary"]["partial"],
            "mismatched": cp["summary"]["mismatched"],
            "total": cp["summary"]["total"],
            "match_rate": cp["summary"]["match_rate"],
            "mismatch_rate": cp["summary"]["mismatch_rate"],
            "has_red_flags": bool(emmpi.get("result", {}).get("red_flags")),
            "status": h.get("status", "—"),
            "computed_by": emmpi.get("computed_by", "—"),
            "computed_at": emmpi.get("computed_at", "—"),
            "honesty_level_code": cp["honesty_level"]["code"] if cp["honesty_level"] else "—",
            "interpretation": cp["interpretation"],
        })
    save_db(db)

    # مرتب‌سازی: ابتدا کمترین صداقت (بیشترین مغایرت)
    rows.sort(key=lambda x: x["honesty_score"])

    # آمار کلی
    total = len(rows)
    avg_honesty = round(sum(r["honesty_score"] for r in rows) / total, 1) if total else 0
    by_honesty_level = {"H4": 0, "H3": 0, "H2": 0, "H1": 0}
    by_dim_mismatch = {}  # {dim: count of mismatched items}
    total_mismatched = 0
    for r in rows:
        by_honesty_level[r["honesty_level_code"]] = by_honesty_level.get(r["honesty_level_code"], 0) + 1
        total_mismatched += r["mismatched"]

    # توزیع مغایرت‌ها در ابعاد ۵گانه
    dim_mismatch_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    for hid, h in hhs:
        cp = h.get("citizen_profile")
        if not cp:
            continue
        for dk, d in cp.get("dimension_scores", {}).items():
            dim_mismatch_dist[dk] = dim_mismatch_dist.get(dk, 0) + d.get("mismatched", 0)

    dim_names = {"A": "سلامت و امنیت زیستی", "B": "آموزش و رشد انسانی",
                 "C": "استاندارد زندگی و مسکن", "D": "معیشت و اشتغال",
                 "E": "آسیب‌پذیری و شبکه"}

    return render_template("citizen_profiles_report.html", u=u,
                           rows=rows, total=total,
                           avg_honesty=avg_honesty,
                           by_honesty_level=by_honesty_level,
                           dim_mismatch_dist=dim_mismatch_dist,
                           dim_names=dim_names,
                           total_mismatched=total_mismatched,
                           HONESTY_LEVELS=HONESTY_LEVELS)


# ─────────────────────────────────────────────────────────
# لایه ۲: ارزیابی هدفمند
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/assess", methods=["GET", "POST"])
@login_required
def assess(hid):
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    st = h["state"]

    # ─── کنترل دسترسی: لایه ۲ فقط برای assistant, rose, swclinic, employ قابل ثبت است.
    # hqmanager فقط مشاهده می‌کند. worker می‌تواند اصلاح کند. ───
    if request.method == "POST" and u["role"] not in ("assistant", "rose", "swclinic", "employ", "worker"):
        return "ثبت ارزیابی لایهٔ ۲ فقط برای همیار، کلینیک رز، کلینیک مددکاری، کارشناس اشتغال یا مددکار خانواده مجاز است (ماتریس بند ۳).", 403

    if request.method == "POST":
        answers = st.get("answers", {})
        for code in st.get("active_axes", []):
            sev = request.form.get(f"sev_{code}")
            if sev is None:
                continue
            if alert_only(u["role"], code):
                answers[code] = {"severity": "none", "note": "[هشدار همیار] " + request.form.get(f"note_{code}", ""),
                                 "conflict": False, "alert": True, "by": u["role"]}
                continue
            if not can_assess(u["role"], code):
                continue
            answers[code] = {
                "severity": sev if sev in SEVERITIES else "none",
                "note": request.form.get(f"note_{code}", ""),
                "conflict": bool(request.form.get(f"conf_{code}")),
                "by": u["role"],
            }
        st["answers"] = answers
        if u["role"] in ("assistant", "rose", "swclinic", "employ"):
            h["layer2_done"] = True
        h["history"].append({"at": datetime.now().isoformat(timespec="seconds"),
                             "by": u["role"], "action": "ارزیابی لایه ۲ ثبت شد"})
        save_db(db)
        return redirect(url_for("household_view", hid=hid))

    active = st.get("active_axes", [])
    items = axis_items(active=active)
    return render_template("assess.html", h=h, hid=hid, items=items, u=u,
                           severities=SEVERITIES, sev_labels=SEVERITY_LABELS,
                           sources=SOURCES)


# ─────────────────────────────────────────────────────────
# لایه ۳: CDI عمیق
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/layer3", methods=["GET", "POST"])
@login_required
def layer3(hid):
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    st = h["state"]
    if st.get("active_axes") or st.get("redflags"):
        st_with_em = {**st, "em_input": h.get("em_input", {})}
        res = compute_household(st_with_em)
    else:
        res = None
    allowed = bool(res and res["layer3_required"])
    if request.method == "POST" and u["role"] not in ("worker", "rose", "swclinic"):
        return "ثبت نتیجهٔ لایهٔ ۳ فقط توسط کلینیک رز، کلینیک مددکاری یا مددکار خانواده مجاز است (بند ۴).", 403
    error = ""
    if request.method == "POST":
        if not allowed:
            error = "شرایط ورود به لایهٔ سوم برقرار نیست (بند ۴ـ۱)."
        else:
            # ─── جمع‌آوری داده‌های فرم لایه ۳ متناسب با نقش ───
            layer3_data = {
                "submitted_at": datetime.now().isoformat(timespec="seconds"),
                "submitted_by": u["role"],
                "submitted_by_name": u.get("name", u["role"]),
                "role_label": ROLES.get(u["role"], {}).get("label", u["role"]),
                "reasons": res["layer3_reasons"] if res else [],
                # فیلدهای مشترک
                "summary": request.form.get("summary", ""),
                "priority_recommendation": request.form.get("priority_recommendation", ""),
                "estimated_duration": request.form.get("estimated_duration", ""),
                "follow_up_plan": request.form.get("follow_up_plan", ""),
                "consent_to_proceed": bool(request.form.get("consent_to_proceed")),
                "requires_external_referral": bool(request.form.get("requires_external_referral")),
                "external_referral_details": request.form.get("external_referral_details", ""),
                "notes": request.form.get("notes", ""),
            }

            # فیلدهای اختصاصی کلینیک رز (rose - مشاوره‌ای)
            if u["role"] == "rose":
                layer3_data["rose_analysis"] = {
                    "counseling_type": request.form.get("counseling_type", ""),
                    "counseling_type_other": request.form.get("counseling_type_other", ""),
                    "session_count_estimated": request.form.get("session_count_estimated", ""),
                    "approach": request.form.get("approach", ""),
                    "client_readiness": request.form.get("client_readiness", ""),
                    "risk_indicators": request.form.getlist("risk_indicators"),
                    "family_dynamics": request.form.get("family_dynamics", ""),
                    "communication_pattern": request.form.get("communication_pattern", ""),
                    "trauma_history": request.form.get("trauma_history", ""),
                    "support_network": request.form.get("support_network", ""),
                    "intervention_plan": request.form.get("intervention_plan", ""),
                    "counselor_recommendation": request.form.get("counselor_recommendation", ""),
                }

            # فیلدهای اختصاصی کلینیک مددکاری (swclinic - تخصصی)
            elif u["role"] == "swclinic":
                layer3_data["swclinic_analysis"] = {
                    "root_cause_analysis": request.form.get("root_cause_analysis", ""),
                    "multi_problem_assessment": request.form.get("multi_problem_assessment", ""),
                    "structural_barriers": request.form.getlist("structural_barriers"),
                    "hidden_factors": request.form.get("hidden_factors", ""),
                    "family_structure": request.form.get("family_structure", ""),
                    "economic_assessment": request.form.get("economic_assessment", ""),
                    "health_assessment": request.form.get("health_assessment", ""),
                    "psychosocial_diagnosis": request.form.get("psychosocial_diagnosis", ""),
                    "intervention_priority": request.form.get("intervention_priority", ""),
                    "capacity_assessment": request.form.get("capacity_assessment", ""),
                    "resilience_factors": request.form.get("resilience_factors", ""),
                    "recommended_interventions": request.form.getlist("recommended_interventions"),
                    "expected_outcomes": request.form.get("expected_outcomes", ""),
                    "monitoring_indicators": request.form.get("monitoring_indicators", ""),
                }

            # فیلدهای اختصاصی مددکار خانواده (worker - تأیید نهایی)
            elif u["role"] == "worker":
                layer3_data["worker_decision"] = {
                    "decision_type": request.form.get("decision_type", ""),
                    "final_priority": request.form.get("final_priority", ""),
                    "integrated_plan": request.form.get("integrated_plan", ""),
                    "service_package": request.form.getlist("service_package"),
                    "household_agreement": request.form.get("household_agreement", ""),
                    "implementation_timeline": request.form.get("implementation_timeline", ""),
                    "responsible_worker": request.form.get("responsible_worker", ""),
                    "budget_estimate": request.form.get("budget_estimate", ""),
                    "approved": bool(request.form.get("approved")),
                    "modifications": request.form.get("modifications", ""),
                    "final_note": request.form.get("final_note", ""),
                }

            # ذخیره در پرونده
            if "layer3_history" not in h:
                h["layer3_history"] = []
            h["layer3_history"].append(layer3_data)
            h["layer3_done"] = True
            h["layer3_done_by"] = u["role"]
            h["layer3_done_at"] = datetime.now().isoformat(timespec="seconds")

            action_text = f"تحلیل لایه ۳ توسط {u.get('name', u['role'])} ({ROLES.get(u['role'], {}).get('label', u['role'])}) ثبت شد"
            if layer3_data.get("summary"):
                action_text += f" — خلاصه: {layer3_data['summary'][:100]}"
            h["history"].append({
                "at": datetime.now().isoformat(timespec="seconds"),
                "by": u["role"],
                "action": action_text,
            })

            # به‌روزرسانی وضعیت پرونده
            h["status"] = "completed"

            save_db(db)
            return redirect(url_for("household_view", hid=hid))

    # GET — نمایش فرم
    return render_template("layer3.html", h=h, hid=hid, res=res, allowed=allowed,
                           error=error, u=u, triggers=LAYER3_TRIGGERS)


# ─────────────────────────────────────────────────────────
# تصمیم مددکار خانواده
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/decide", methods=["POST"])
@login_required
def decide(hid):
    u = current_user()
    if u["role"] != "worker":
        return "فقط مددکار خانواده مجاز به تصمیم نهایی است (ماتریس بند ۳).", 403
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    decision = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "priority": request.form.get("priority", ""),
        "confirm": bool(request.form.get("confirm")),
        "note": request.form.get("note", ""),
        "by": u["role"],
    }
    decision["g3"] = bool(request.form.get("g3"))
    h["decisions"].append(decision)
    flags = []
    if decision["confirm"]:
        flags.append("تأیید پیشنهاد سامانه")
    if decision["g3"]:
        flags.append("ورود به لایهٔ ۳")
    h["history"].append({"at": decision["at"], "by": u["role"],
                         "action": f"تصمیم مددکار: اولویت {decision['priority']} — {'؛ '.join(flags) if flags else 'اصلاح/یادداشت'}"})
    save_db(db)
    return redirect(url_for("household_view", hid=hid))


# ─────────────────────────────────────────────────────────
# ارجاع بین حلقه‌ها
# ─────────────────────────────────────────────────────────
REFERRAL_TARGETS = ["rose", "swclinic", "employ", "manager"]
REFERRAL_REASONS = {
    "rose": "موضوعات مشاوره‌ای: خانواده، کودک، فشار روانی، سوگ، تاب‌آوری، تحصیلی، شغلی",
    "swclinic": "تحلیل عمیق علل ریشه‌ای، پرونده چندمسئله‌ای، ابهام در CDI، منتورینگ",
    "employ": "مهارت، بازار، ابزار، وام، سرمایه‌گذاری یا کسب‌وکار",
    "manager": "گلوگاه ساختاری، کمبود ظرفیت یا تصمیم مالی استثنایی",
}


@app.route("/household/<hid>/refer", methods=["GET", "POST"])
@login_required
def refer(hid):
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    if request.method == "POST":
        r = {"at": datetime.now().isoformat(timespec="seconds"),
             "from": u["role"], "to": request.form.get("to", ""),
             "axis": request.form.get("axis", ""), "note": request.form.get("note", ""),
             "status": "pending", "result": ""}
        h["referrals"].append(r)
        h["history"].append({"at": r["at"], "by": u["role"],
                             "action": f"ارجاع به {ROLES.get(r['to'], {}).get('label', r['to'])} برای محور {r['axis']}"})
        save_db(db)
        return redirect(url_for("household_view", hid=hid))
    active = h["state"].get("active_axes", [])
    axes_list = [(c, AXES_BY_CODE[c]["title"]) for c in active if c in AXES_BY_CODE]
    return render_template("refer.html", h=h, hid=hid, u=u,
                           targets=REFERRAL_TARGETS, reasons=REFERRAL_REASONS,
                           roles=ROLES, axes_list=axes_list)


@app.route("/household/<hid>/referral/<int:idx>", methods=["POST"])
@login_required
def referral_result(hid, idx):
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    if idx < 0 or idx >= len(h["referrals"]):
        return redirect(url_for("household_view", hid=hid))
    r = h["referrals"][idx]
    u = current_user()
    if r["to"] != u["role"] and u["role"] != "worker":
        return "این ارجاع متعلق به حلقهٔ شما نیست.", 403
    r["result"] = request.form.get("result", "")
    r["status"] = "done"
    h["history"].append({"at": datetime.now().isoformat(timespec="seconds"),
                         "by": u["role"], "action": f"نتیجهٔ ارجاع ثبت شد: {r['result'][:80]}"})
    save_db(db)
    return redirect(url_for("household_view", hid=hid))


# ─────────────────────────────────────────────────────────
# پروفایل توانمندسازی
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/profile")
@login_required
def profile(hid):
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    st = h["state"]
    if not (st.get("active_axes") or st.get("redflags")):
        return redirect(url_for("household_view", hid=hid))
    st_with_em = {**st, "em_input": h.get("em_input", {})}
    res = compute_household(st_with_em)
    prof = build_profile(h["identity"], h["em_input"], res,
                         preferences=h.get("preferences"),
                         capacities=h.get("capacities"),
                         causes=h.get("causes"))
    return render_template("profile.html", u=u, h=h, hid=hid, res=res, prof=prof,
                           action_ranks=ACTION_RANKS,
                           service_queues=SERVICE_QUEUE_FAMILIES,
                           action_relations=ACTION_RELATIONS,
                           tiebreak_household=TIEBREAK_RULES_HOUSEHOLD,
                           tiebreak_queue=TIEBREAK_RULES_QUEUE,
                           control_rules=CONTROL_RULES,
                           peh_component_meta=COMPONENT_META,
                           referral_paths=get_referral_paths_visual())


# ─────────────────────────────────────────────────────────
# سبد مداخله (صفحهٔ جدید — بند ۲ـ۸)
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/basket")
@login_required
def intervention_basket(hid):
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    st = h["state"]
    if not (st.get("active_axes") or st.get("redflags")):
        return redirect(url_for("household_view", hid=hid))
    st_with_em = {**st, "em_input": h.get("em_input", {})}
    res = compute_household(st_with_em)
    return render_template("intervention_basket.html", h=h, hid=hid, res=res, u=u,
                           action_ranks=ACTION_RANKS,
                           service_queues=SERVICE_QUEUE_FAMILIES,
                           action_relations=ACTION_RELATIONS,
                           control_rules=CONTROL_RULES,
                           roles=ROLES,
                           component_meta=COMPONENT_META)


# ─────────────────────────────────────────────────────────
# صف‌های خدمت (صفحهٔ جدید — بند ۲ـ۱۲)
# ─────────────────────────────────────────────────────────
@app.route("/queues")
@login_required
def service_queues():
    u = current_user()
    db = load_db()
    # جمع‌آوری همهٔ اقدامات از همهٔ خانوارها
    queue_map = {q["code"]: {"info": q, "actions": []} for q in SERVICE_QUEUE_FAMILIES}
    for hid, h in db["households"].items():
        st = h.get("state", {})
        if not (st.get("active_axes") or st.get("redflags")):
            continue
        st_with_em = {**st, "em_input": h.get("em_input", {})}
        res = compute_household(st_with_em)
        if res and res.get("basket"):
            for item in res["basket"]["actions"]:
                queue_map[item["queue"]]["actions"].append({
                    "hid": hid, "name": h["identity"].get("name", hid),
                    "p": item["p"], "rank": item["rank"], "pim": item["pim"],
                    "peh": res.get("peh", 0), "title": item["title"],
                    "code": item["code"], "deadline": item["deadline"],
                    "owner": item["owner"],
                })
    # مرتب‌سازی هر صف بر اساس: ۱) طبقه P، ۲) رتبه A-E، ۳) PIM
    p_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
    rank_order = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    for q in queue_map.values():
        q["actions"].sort(key=lambda x: (p_order.get(x["p"], 9), rank_order.get(x["rank"], 9), -x["pim"]))
    return render_template("service_queues.html", u=u, queues=queue_map.values(),
                           action_ranks=ACTION_RANKS,
                           tiebreak_rules=TIEBREAK_RULES_QUEUE)


# ─────────────────────────────────────────────────────────
# داشبورد تحلیلی مددکار (گزارش‌ها، نمودارها، نظارت)
# ─────────────────────────────────────────────────────────
@app.route("/worker/dashboard")
@login_required
def worker_dashboard():
    """داشبورد تحلیلی مددکار — گزارش‌ها، نمودارها، جریان کار."""
    u = current_user()
    db = load_db()
    # فیلتر استانی (مدیر ستاد همه را می‌بیند)
    all_hhs = list(db["households"].items())
    if u.get("province"):
        hhs = [(hid, h) for hid, h in all_hhs
               if h.get("identity", {}).get("province", "") == u["province"]]
    else:
        hhs = all_hhs

    # آمار کلی
    total = len(hhs)
    by_status = {"pending": 0, "claimed": 0, "emmpi_done": 0, "cdi_in_progress": 0, "completed": 0}
    by_priority = {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "P4": 0, "none": 0}
    by_region = {}
    emmpi_scores = []
    red_flag_count = 0
    recent_activity = []
    # آمار جدید
    by_emmpi_level = {"L0": 0, "L1": 0, "L2": 0, "L3": 0, "L4": 0, "none": 0}
    by_red_flag_type = {}
    by_dim_severity = {"A": {"high": 0, "med": 0, "low": 0}, "B": {"high": 0, "med": 0, "low": 0},
                        "C": {"high": 0, "med": 0, "low": 0}, "D": {"high": 0, "med": 0, "low": 0},
                        "E": {"high": 0, "med": 0, "low": 0}}
    by_assistant = {}
    sd_yes_dist = []  # توزیع پاسخ‌های «بله» در خوداظهاری
    cases_by_date = {}

    # ─── آمار پروندهٔ شهروندی ───
    citizen_rows = []         # فهرست پرونده‌ها با امتیاز صداقت
    by_honesty_level = {"H4": 0, "H3": 0, "H2": 0, "H1": 0, "none": 0}
    honesty_scores_list = []
    cp_dim_mismatch_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    low_honesty_cases = []    # پرونده‌هایی با صداقت پایین (نیاز به راستی‌آزمایی)
    total_mismatched = 0
    total_matched = 0
    total_partial = 0

    for hid, h in hhs:
        st = h.get("status", "pending")
        by_status[st] = by_status.get(st, 0) + 1

        loc = (h.get("identity", {}).get("location", "") or "نامشخص").split("،")[0].strip()
        by_region[loc] = by_region.get(loc, 0) + 1

        # تاریخ ثبت برای نمودار زمانی
        created = h.get("state", {}).get("created_at", "")[:10] if h.get("state") else ""
        if created:
            cases_by_date[created] = cases_by_date.get(created, 0) + 1

        # توزیع پاسخ‌های «بله» در خوداظهاری
        sd = h.get("self_declaration", {})
        if sd and "yes_count" in sd:
            sd_yes_dist.append(sd["yes_count"])

        # آمار همیار
        cb = h.get("claimed_by")
        if cb:
            ast_name = cb.get("name", "نامشخص")
            by_assistant[ast_name] = by_assistant.get(ast_name, 0) + 1

        if h.get("emmpi"):
            r = h["emmpi"].get("result", {})
            emmpi_scores.append(r.get("score", 0))
            rf = r.get("red_flags", [])
            red_flag_count += len(rf)

            # سطح محرومیت
            lvl = r.get("level", {})
            lvl_code = lvl.get("code", "none") if lvl else "none"
            by_emmpi_level[lvl_code] = by_emmpi_level.get(lvl_code, 0) + 1

            # فراوانی هر نوع پرچم قرمز
            for rf_item in rf:
                rf_code = rf_item.get("code", "?")
                by_red_flag_type[rf_code] = by_red_flag_type.get(rf_code, 0) + 1

            # شدت هر بُعد
            dim_scores = r.get("dimension_scores", {})
            for dim_key in ["A", "B", "C", "D", "E"]:
                ds = dim_scores.get(dim_key, {})
                pct = ds.get("pct", 0) if ds else 0
                if pct >= 66:
                    by_dim_severity[dim_key]["high"] += 1
                elif pct >= 33:
                    by_dim_severity[dim_key]["med"] += 1
                else:
                    by_dim_severity[dim_key]["low"] += 1

            # اولویت
            score = r.get("score", 0)
            if score >= 600 or rf:
                by_priority["P0"] += 1
            elif score >= 450:
                by_priority["P1"] += 1
            elif score >= 300:
                by_priority["P2"] += 1
            elif score >= 150:
                by_priority["P3"] += 1
            else:
                by_priority["P4"] += 1

            # ─── محاسبهٔ پروندهٔ شهروندی (داینامیک اگر ذخیره نشده) ───
            cp = h.get("citizen_profile")
            if not cp:
                # محاسبهٔ روی‌هوا
                sd_data = h.get("self_declaration", {}) or {}
                if "questions" not in sd_data:
                    sd_data["questions"] = {}
                indicators_data = h.get("emmpi", {}).get("indicators", {}) or {}
                emmpi_result = h.get("emmpi", {}).get("result")
                try:
                    cp = compute_citizen_profile(sd_data, indicators_data, emmpi_result=emmpi_result)
                except Exception:
                    cp = None

            if cp:
                h_score = cp.get("honesty_score", 0)
                h_lvl = cp.get("honesty_level", {})
                h_code = h_lvl.get("code", "none") if h_lvl else "none"
                by_honesty_level[h_code] = by_honesty_level.get(h_code, 0) + 1
                honesty_scores_list.append(h_score)

                # آمار مغایرت در ابعاد ۵گانه
                for dk, d in cp.get("dimension_scores", {}).items():
                    cp_dim_mismatch_dist[dk] = cp_dim_mismatch_dist.get(dk, 0) + d.get("mismatched", 0)

                sumry = cp.get("summary", {})
                total_matched += sumry.get("matched", 0)
                total_partial += sumry.get("partial", 0)
                total_mismatched += sumry.get("mismatched", 0)

                # افزودن به فهرست
                citizen_rows.append({
                    "hid": hid,
                    "name": h.get("identity", {}).get("name", hid),
                    "province": h.get("identity", {}).get("province_name", "—"),
                    "emmpi_score": r.get("score", 0),
                    "emmpi_level": r.get("level", {}).get("name", "—") if r.get("level") else "—",
                    "honesty_score": h_score,
                    "honesty_level": h_lvl.get("name", "—") if h_lvl else "—",
                    "honesty_level_code": h_code,
                    "matched": sumry.get("matched", 0),
                    "partial": sumry.get("partial", 0),
                    "mismatched": sumry.get("mismatched", 0),
                    "total": sumry.get("total", 0),
                    "match_rate": sumry.get("match_rate", 0),
                    "mismatch_rate": sumry.get("mismatch_rate", 0),
                    "has_red_flags": bool(rf),
                    "interpretation": cp.get("interpretation", ""),
                })

                # پرونده‌های با صداقت پایین
                if h_score < 70:
                    low_honesty_cases.append({
                        "hid": hid,
                        "name": h.get("identity", {}).get("name", hid),
                        "honesty_score": h_score,
                        "honesty_level": h_lvl.get("name", "—") if h_lvl else "—",
                        "mismatched": sumry.get("mismatched", 0),
                        "emmpi_score": r.get("score", 0),
                        "interpretation": cp.get("interpretation", "")[:100],
                    })
        else:
            by_priority["none"] += 1

        # فعالیت‌های اخیر
        for e in h.get("history", [])[-3:]:
            recent_activity.append({
                "hid": hid, "name": h.get("identity", {}).get("name", hid),
                "at": e.get("at", ""), "by": e.get("by", ""),
                "action": e.get("action", ""),
            })

    # مرتب‌سازی فعالیت‌های اخیر بر اساس زمان (نزولی)
    recent_activity.sort(key=lambda x: x["at"], reverse=True)
    recent_activity = recent_activity[:15]

    avg_score = round(sum(emmpi_scores) / len(emmpi_scores)) if emmpi_scores else 0
    avg_honesty = round(sum(honesty_scores_list) / len(honesty_scores_list), 1) if honesty_scores_list else 0

    # مرتب‌سازی پرونده‌های شهروندی بر اساس کمترین صداقت (نیاز به بررسی فوری)
    citizen_rows.sort(key=lambda x: x["honesty_score"])
    low_honesty_cases.sort(key=lambda x: x["honesty_score"])

    # تبدیل به فرمت مورد نظر سایدبار (list of dicts با کلید h)
    households_for_tpl = [{"hid": hid, "h": h, "res": None} for hid, h in hhs]

    # نام‌های فارسی ابعاد
    cp_dim_names = {"A": "سلامت و امنیت زیستی", "B": "آموزش و رشد انسانی",
                    "C": "استاندارد زندگی و مسکن", "D": "معیشت و اشتغال",
                    "E": "آسیب‌پذیری و شبکه"}

    return render_template("worker_dashboard.html", u=u,
                           total=total, by_status=by_status, by_priority=by_priority,
                           by_region=by_region, avg_score=avg_score,
                           red_flag_count=red_flag_count,
                           emmpi_count=len(emmpi_scores),
                           recent_activity=recent_activity,
                           by_emmpi_level=by_emmpi_level,
                           by_red_flag_type=by_red_flag_type,
                           by_dim_severity=by_dim_severity,
                           by_assistant=by_assistant,
                           sd_yes_dist=sd_yes_dist,
                           cases_by_date=cases_by_date,
                           households=households_for_tpl,
                           # پروندهٔ شهروندی
                           citizen_rows=citizen_rows,
                           by_honesty_level=by_honesty_level,
                           avg_honesty=avg_honesty,
                           cp_dim_mismatch_dist=cp_dim_mismatch_dist,
                           cp_dim_names=cp_dim_names,
                           low_honesty_cases=low_honesty_cases,
                           total_matched=total_matched,
                           total_partial=total_partial,
                           total_mismatched=total_mismatched,
                           HONESTY_LEVELS=HONESTY_LEVELS)


# ─────────────────────────────────────────────────────────
# داشبورد ستاد مرکزی (گزارش کل کشور + نقشه ایران)
# ─────────────────────────────────────────────────────────
@app.route("/hq/dashboard")
@login_required
def hq_dashboard():
    """داشبورد ستاد مرکزی — گزارش کل کشور + نقشه + تحلیل MPI/CDI."""
    u = current_user()
    db = load_db()
    hhs = list(db["households"].items())

    total = len(hhs)
    by_province = {}
    by_priority_country = {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "P4": 0}
    emmpi_count = 0
    by_channel = {}  # توزیع کانال‌های دریافت
    red_flag_count = 0
    scores = []

    # تحلیل ابعاد MPI به تفکیک استان
    dim_names = {"A": "سلامت و امنیت زیستی", "B": "آموزش و رشد", "C": "استاندارد زندگی و مسکن",
                 "D": "معیشت و اشتغال", "E": "آسیب‌پذیری و شبکه"}
    mpi_dims_country = {"A": {"score": 0, "max": 0, "count": 0}, "B": {"score": 0, "max": 0, "count": 0},
                         "C": {"score": 0, "max": 0, "count": 0}, "D": {"score": 0, "max": 0, "count": 0},
                         "E": {"score": 0, "max": 0, "count": 0}}
    mpi_dims_by_province = {}  # {province_key: {dim: {score, max, count, pct}}}

    # تحلیل محورهای CDI
    cdi_axes_country = {}  # {axis_code: count}
    cdi_axes_by_province = {}  # {province: {axis_code: count}}

    # تحلیل پرچم‌های قرمز به تفکیک استان
    red_flags_by_province = {}

    # ─── تحلیل پروندهٔ شهروندی (صداقت) ───
    cp_country_stats = {
        "total_cp": 0,                   # تعداد پرونده‌های شهروندی تهیه‌شده
        "avg_honesty": 0,                # میانگین امتیاز صداقت کشور
        "total_matched": 0,
        "total_partial": 0,
        "total_mismatched": 0,
        "by_honesty_level": {"H4": 0, "H3": 0, "H2": 0, "H1": 0},
        "dim_mismatch_country": {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0},
    }
    cp_by_province = {}  # {prov: {count, avg_honesty, mismatched_count, by_level}}
    honesty_scores_list = []
    low_honesty_country = []  # پرونده‌های با صداقت پایین در کل کشور

    for hid, h in hhs:
        prov_key = h.get("identity", {}).get("province", "") or "unknown"
        by_province[prov_key] = by_province.get(prov_key, 0) + 1

        # کانال دریافت درخواست
        ch = h.get("request_channel", "unknown")
        by_channel[ch] = by_channel.get(ch, 0) + 1

        # مقداردهی استان در dict
        if prov_key not in mpi_dims_by_province:
            mpi_dims_by_province[prov_key] = {d: {"score": 0, "max": 0, "count": 0} for d in "ABCDE"}
        if prov_key not in cdi_axes_by_province:
            cdi_axes_by_province[prov_key] = {}
        if prov_key not in red_flags_by_province:
            red_flags_by_province[prov_key] = {}
        if prov_key not in cp_by_province:
            cp_by_province[prov_key] = {
                "count": 0, "honesty_sum": 0, "mismatched_count": 0,
                "by_level": {"H4": 0, "H3": 0, "H2": 0, "H1": 0},
                "low_honesty_count": 0,
            }

        if h.get("emmpi"):
            r = h["emmpi"].get("result", {})
            emmpi_count += 1
            scores.append(r.get("score", 0))
            rf = r.get("red_flags", [])
            red_flag_count += len(rf)

            # پرچم‌های قرمز به تفکیک استان
            for rf_item in rf:
                rf_code = rf_item.get("code", "?")
                red_flags_by_province[prov_key][rf_code] = red_flags_by_province[prov_key].get(rf_code, 0) + 1

            # ابعاد MPI
            dim_scores = r.get("dimension_scores", {})
            for dim_key in ["A", "B", "C", "D", "E"]:
                ds = dim_scores.get(dim_key, {})
                sc = ds.get("score", 0) if ds else 0
                mx = ds.get("max", 0) if ds else 0
                mpi_dims_country[dim_key]["score"] += sc
                mpi_dims_country[dim_key]["max"] += mx
                mpi_dims_country[dim_key]["count"] += 1
                mpi_dims_by_province[prov_key][dim_key]["score"] += sc
                mpi_dims_by_province[prov_key][dim_key]["max"] += mx
                mpi_dims_by_province[prov_key][dim_key]["count"] += 1

            # اولویت
            score = r.get("score", 0)
            if score >= 600 or rf:
                by_priority_country["P0"] += 1
            elif score >= 450:
                by_priority_country["P1"] += 1
            elif score >= 300:
                by_priority_country["P2"] += 1
            elif score >= 150:
                by_priority_country["P3"] += 1
            else:
                by_priority_country["P4"] += 1

            # ─── محاسبهٔ پروندهٔ شهروندی (داینامیک اگر ذخیره نشده) ───
            cp = h.get("citizen_profile")
            if not cp:
                sd_data = h.get("self_declaration", {}) or {}
                if "questions" not in sd_data:
                    sd_data["questions"] = {}
                indicators_data = h.get("emmpi", {}).get("indicators", {}) or {}
                emmpi_result = h.get("emmpi", {}).get("result")
                try:
                    cp = compute_citizen_profile(sd_data, indicators_data, emmpi_result=emmpi_result)
                except Exception:
                    cp = None

            if cp:
                cp_country_stats["total_cp"] += 1
                h_score = cp.get("honesty_score", 0)
                h_lvl = cp.get("honesty_level", {})
                h_code = h_lvl.get("code", "none") if h_lvl else "none"
                honesty_scores_list.append(h_score)

                # آمار کشور
                if h_code in cp_country_stats["by_honesty_level"]:
                    cp_country_stats["by_honesty_level"][h_code] += 1
                sumry = cp.get("summary", {})
                cp_country_stats["total_matched"] += sumry.get("matched", 0)
                cp_country_stats["total_partial"] += sumry.get("partial", 0)
                cp_country_stats["total_mismatched"] += sumry.get("mismatched", 0)

                # توزیع مغایرت در ابعاد
                for dk, d in cp.get("dimension_scores", {}).items():
                    cp_country_stats["dim_mismatch_country"][dk] = (
                        cp_country_stats["dim_mismatch_country"].get(dk, 0) + d.get("mismatched", 0)
                    )

                # آمار استانی
                cp_by_province[prov_key]["count"] += 1
                cp_by_province[prov_key]["honesty_sum"] += h_score
                cp_by_province[prov_key]["mismatched_count"] += sumry.get("mismatched", 0)
                if h_code in cp_by_province[prov_key]["by_level"]:
                    cp_by_province[prov_key]["by_level"][h_code] += 1
                if h_score < 70:
                    cp_by_province[prov_key]["low_honesty_count"] += 1

                # پرونده‌های با صداقت پایین کشور (مرتب‌سازی بعد)
                if h_score < 70:
                    low_honesty_country.append({
                        "hid": hid, "name": h.get("identity", {}).get("name", hid),
                        "province": h.get("identity", {}).get("province_name", "—"),
                        "province_key": prov_key,
                        "honesty_score": h_score,
                        "honesty_level": h_lvl.get("name", "—") if h_lvl else "—",
                        "mismatched": sumry.get("mismatched", 0),
                        "emmpi_score": score,
                    })

        # محورهای CDI فعال
        active_axes = h.get("state", {}).get("active_axes", [])
        for axis_code in active_axes:
            cdi_axes_country[axis_code] = cdi_axes_country.get(axis_code, 0) + 1
            cdi_axes_by_province[prov_key][axis_code] = cdi_axes_by_province[prov_key].get(axis_code, 0) + 1

    avg_score = round(sum(scores) / len(scores)) if scores else 0
    cp_country_stats["avg_honesty"] = round(sum(honesty_scores_list) / len(honesty_scores_list), 1) if honesty_scores_list else 0

    # محاسبه میانگین صداقت استانی
    cp_province_rows = []
    for pk, pv in cp_by_province.items():
        if pv["count"] == 0:
            continue
        avg_h = round(pv["honesty_sum"] / pv["count"], 1)
        cp_province_rows.append({
            "province_key": pk,
            "province_name": get_province_name(pk) if pk != "unknown" else "نامشخص",
            "count": pv["count"],
            "avg_honesty": avg_h,
            "mismatched_count": pv["mismatched_count"],
            "low_honesty_count": pv["low_honesty_count"],
            "by_level": pv["by_level"],
        })
    cp_province_rows.sort(key=lambda x: x["avg_honesty"])  # ابتدا کمترین صداقت

    # مرتب‌سازی پرونده‌های با صداقت پایین
    low_honesty_country.sort(key=lambda x: x["honesty_score"])

    # محاسبه میانگین درصد هر بُعد
    for dk in mpi_dims_country:
        d = mpi_dims_country[dk]
        d["pct"] = round(d["score"] / d["max"] * 100, 1) if d["max"] > 0 else 0
    for pk in mpi_dims_by_province:
        for dk in mpi_dims_by_province[pk]:
            d = mpi_dims_by_province[pk][dk]
            d["pct"] = round(d["score"] / d["max"] * 100, 1) if d["max"] > 0 else 0

    # داده‌های نقشه
    map_provinces = get_all_province_coords()
    map_with_stats = [{"key": m["key"], "name": m["name"], "lat": m["lat"], "lng": m["lng"],
                        "count": by_province.get(m["key"], 0)} for m in map_provinces]

    # مارکرها
    household_markers = []
    for hid, h in hhs:
        prov_key = h.get("identity", {}).get("province", "")
        lat, lng = get_province_coords(prov_key)
        household_markers.append({"lat": lat, "lng": lng,
                                   "name": h.get("identity", {}).get("name", hid), "hid": hid})

    # مرتب‌سازی محورهای CDI کشور بر اساس فراوانی
    cdi_axes_sorted = sorted(cdi_axes_country.items(), key=lambda x: x[1], reverse=True)

    # نگاشت کدهای CDI به عناوین فارسی
    cdi_axis_names = {code: info.get("title", code) for code, info in AXES_BY_CODE.items()}
    # نگاشت کدهای پرچم قرمز به عناوین فارسی
    rf_names = {code: info.get("title", code) for code, info in EMMPI_RED_FLAGS.items()}

    return render_template("hq_dashboard.html", u=u,
                           total=total, emmpi_count=emmpi_count,
                           red_flag_count=red_flag_count, avg_score=avg_score,
                           by_priority=by_priority_country,
                           by_province=by_province,
                           map_data=map_with_stats,
                           household_markers=household_markers,
                           PROVINCES=PROVINCES,
                           dim_names=dim_names,
                           mpi_dims_country=mpi_dims_country,
                           mpi_dims_by_province=mpi_dims_by_province,
                           cdi_axes_country=cdi_axes_sorted,
                           cdi_axis_names=cdi_axis_names,
                           cdi_axes_by_province=cdi_axes_by_province,
                           red_flags_by_province=red_flags_by_province,
                           red_flag_names=rf_names,
                           by_channel=by_channel,
                           REQUEST_CHANNELS=REQUEST_CHANNELS,
                           households=[{"hid": hid, "h": h} for hid, h in hhs],
                           # پروندهٔ شهروندی
                           cp_country_stats=cp_country_stats,
                           cp_province_rows=cp_province_rows,
                           low_honesty_country=low_honesty_country,
                           HONESTY_LEVELS=HONESTY_LEVELS)


# ─────────────────────────────────────────────────────────
# صفحه نظارت و پایش ستاد مرکزی
# ─────────────────────────────────────────────────────────
@app.route("/hq/oversight")
@login_required
def hq_oversight():
    """نظارت و پایش — وضعیت فرایند، موارد خارج از اولویت‌بندی، کمبود همیار."""
    u = current_user()
    db = load_db()
    hhs = list(db["households"].items())

    # ۱. وضعیت فرایند ثبت درخواست‌ها به تفکیک استان
    process_by_province = {}  # {prov: {total, pending, claimed, emmpi_done, cdi_in_progress, completed, no_emmpi}}
    for hid, h in hhs:
        pk = h.get("identity", {}).get("province", "") or "unknown"
        if pk not in process_by_province:
            process_by_province[pk] = {"total": 0, "pending": 0, "claimed": 0,
                                        "emmpi_done": 0, "cdi_in_progress": 0, "completed": 0, "no_emmpi": 0}
        st = h.get("status", "pending")
        p = process_by_province[pk]
        p["total"] += 1
        if st == "pending":
            p["pending"] += 1
        elif st == "claimed":
            p["claimed"] += 1
        elif st == "emmpi_done":
            p["emmpi_done"] += 1
        elif st == "cdi_in_progress":
            p["cdi_in_progress"] += 1
        elif st == "completed":
            p["completed"] += 1
        if not h.get("emmpi"):
            p["no_emmpi"] += 1

    # ۲. موارد خارج از اولویت‌بندی
    outliers = []
    for hid, h in hhs:
        issues = []
        # الف) EM-MPI انجام شده اما CDI شروع نشده (امتیاز بالا ولی بدون اقدام)
        if h.get("emmpi"):
            r = h["emmpi"].get("result", {})
            score = r.get("score", 0)
            needs_cdi = r.get("needs_cdi", False)
            has_cdi = bool(h.get("state", {}).get("active_axes"))
            if needs_cdi and not has_cdi:
                issues.append("نیاز به CDI تأیید شده اما شروع نشده")
            # ب) امتیاز بسیار پایین بدون پرچم قرمز
            if score < 150 and not r.get("red_flags"):
                issues.append("امتیاز بسیار پایین بدون پرچم قرمز — بررسی تأیید")
        # ج) تخصیص یافته ولی EM-MPI انجام نشده
        if h.get("claimed_by") and not h.get("emmpi"):
            issues.append("تخصیص یافته ولی EM-MPI انجام نشده")
        # د) مدت طولانی در انتظار
        created = h.get("state", {}).get("created_at", "")
        if created and st == "pending":
            issues.append("مدت طولانی در انتظار تخصیص")
        if issues:
            outliers.append({
                "hid": hid,
                "name": h.get("identity", {}).get("name", hid),
                "province": h.get("identity", {}).get("province_name", "نامشخص"),
                "province_key": h.get("identity", {}).get("province", ""),
                "status": h.get("status", "pending"),
                "issues": issues,
                "emmpi_score": h.get("emmpi", {}).get("result", {}).get("score", "—"),
            })

    # ۳. کمبود همیار/کاربر در استان‌ها
    # شمارش کاربران per استان
    users_by_province = {}
    for uid, udata in USERS.items():
        prov = udata.get("province")
        if prov:
            if prov not in users_by_province:
                users_by_province[prov] = {"assistants": 0, "workers": 0, "rose": 0, "swclinic": 0, "total": 0}
            role = udata.get("role", "")
            users_by_province[prov]["total"] += 1
            if role == "assistant":
                users_by_province[prov]["assistants"] += 1
            elif role == "worker":
                users_by_province[prov]["workers"] += 1
            elif role == "rose":
                users_by_province[prov]["rose"] += 1
            elif role == "swclinic":
                users_by_province[prov]["swclinic"] += 1

    # مقایسه تقاضا (پرونده‌های pending) با عرض (کاربران)
    shortage = []
    for pk, pv in PROVINCES.items():
        prov_cases = process_by_province.get(pk, {"total": 0, "pending": 0})
        prov_users = users_by_province.get(pk, {"assistants": 0, "workers": 0, "rose": 0, "swclinic": 0, "total": 0})
        pending = prov_cases.get("pending", 0)
        total_cases = prov_cases.get("total", 0)
        ast_count = prov_users["assistants"] + prov_users["workers"]
        ratio = round(pending / ast_count, 1) if ast_count > 0 else "∞"
        status_color = "red" if (ast_count == 0 and total_cases > 0) else ("amber" if (pending > ast_count * 3 and ast_count > 0) else "green")
        shortage.append({
            "province_key": pk, "province_name": pv["name"],
            "total_cases": total_cases, "pending": pending,
            "assistants": prov_users["assistants"], "workers": prov_users["workers"],
            "rose": prov_users["rose"], "swclinic": prov_users["swclinic"],
            "total_users": prov_users["total"],
            "ratio": ratio, "status_color": status_color,
        })

    # مرتب‌سازی بر اساس شدت کمبود
    shortage.sort(key=lambda x: (0 if x["status_color"] == "red" else (1 if x["status_color"] == "amber" else 2)))

    return render_template("hq_oversight.html", u=u,
                           process_by_province=process_by_province,
                           outliers=outliers,
                           shortage=shortage,
                           PROVINCES=PROVINCES,
                           total_outliers=len(outliers),
                           total_shortage=sum(1 for s in shortage if s["status_color"] in ("red", "amber")))


# ─────────────────────────────────────────────────────────
# گزارش منابع مورد نیاز برای توانمندسازی
# ─────────────────────────────────────────────────────────
@app.route("/hq/resources")
@login_required
def hq_resources():
    """گزارش منابع مورد نیاز بر اساس پروفایل توانمندسازی."""
    u = current_user()
    db = load_db()
    hhs = list(db["households"].items())

    # تحلیل منابع مورد نیاز
    resources_by_type = {}  # {service_type: count, cost_total}
    resources_by_province = {}  # {province: {service_type: count}}
    total_estimated_cost = 0

    for hid, h in hhs:
        pk = h.get("identity", {}).get("province", "") or "unknown"
        prov_name = get_province_name(pk) if pk != "unknown" else "نامشخص"
        if pk not in resources_by_province:
            resources_by_province[pk] = {}

        # تعیین اولویت برای ضریب هزینه
        priority = "P2"
        if h.get("emmpi"):
            r = h["emmpi"].get("result", {})
            score = r.get("score", 0)
            rf = r.get("red_flags", [])
            if score >= 600 or rf:
                priority = "P0"
            elif score >= 450:
                priority = "P1"
            elif score >= 300:
                priority = "P2"
            elif score >= 150:
                priority = "P3"
            else:
                priority = "P4"

        # منابع مورد نیاز بر اساس وضعیت پرونده
        needed_services = []

        # ۱. بازدید میدانی (همیشه نیاز است در شروع)
        if h.get("status") in ("pending", "claimed"):
            needed_services.append("field_visit")

        # ۲. EM-MPI
        if not h.get("emmpi"):
            if h.get("emmpi", {}).get("result", {}).get("red_flags"):
                needed_services.append("emmpi_redflag")
            else:
                needed_services.append("emmpi_assessment")

        # ۳. CDI بر اساس نیاز
        if h.get("emmpi") and h.get("emmpi", {}).get("result", {}).get("needs_cdi"):
            r = h["emmpi"]["result"]
            if r.get("layer3_required"):
                needed_services.append("cdi_layer3")
            elif h.get("state", {}).get("active_axes") and not h.get("state", {}).get("answers"):
                needed_services.append("cdi_layer2")
            elif not h.get("state", {}).get("active_axes"):
                needed_services.append("cdi_layer1")

        # ۴. مشاوره
        if h.get("emmpi"):
            r = h["emmpi"].get("result", {})
            rf_codes = [rf["code"] for rf in r.get("red_flags", [])]
            if "R5" in rf_codes or "R4" in rf_codes:
                needed_services.append("rose_counseling")
            if r.get("layer3_required"):
                needed_services.append("swclinic_analysis")

        # ۵. اشتغال
        active_axes = h.get("state", {}).get("active_axes", [])
        if any(a.startswith("CDI-3") for a in active_axes):
            needed_services.append("employ_assessment")

        # ۶. پایش
        if h.get("layer3_done") or h.get("state", {}).get("answers"):
            needed_services.append("monitoring_visit")

        # محاسبه هزینه
        for svc in needed_services:
            cost = compute_service_cost(svc, role="assistant", priority=priority)
            total_estimated_cost += cost

            if svc not in resources_by_type:
                resources_by_type[svc] = {"count": 0, "cost_total": 0, "label": get_service_label(svc)}
            resources_by_type[svc]["count"] += 1
            resources_by_type[svc]["cost_total"] += cost

            if svc not in resources_by_province[pk]:
                resources_by_province[pk][svc] = 0
            resources_by_province[pk][svc] += 1

    # مرتب‌سازی بر اساس تعداد
    resources_sorted = sorted(resources_by_type.items(), key=lambda x: x[1]["count"], reverse=True)

    return render_template("hq_resources.html", u=u,
                           resources_by_type=resources_sorted,
                           resources_by_province=resources_by_province,
                           total_estimated_cost=total_estimated_cost,
                           PROVINCES=PROVINCES,
                           SERVICE_COSTS=SERVICE_COSTS,
                           USERS=USERS,
                           total_services=sum(v["count"] for _, v in resources_sorted))


# ─────────────────────────────────────────────────────────
# داشبورد مالی (کیف پول + هزینه خدمات)
# ─────────────────────────────────────────────────────────
@app.route("/finance/dashboard")
@login_required
def finance_dashboard():
    """داشبورد مالی — کیف پول همیاران + هزینه خدمات + تأیید اعتبار."""
    u = current_user()
    db = load_db()

    # داده‌های کیف پول — شارژ اکنون در لحظهٔ انجام اقدام ثبت می‌شود
    # (در emmpi_form و assess) دیگر شارژ خودکار اینجا انجام نمی‌شود

    # داده‌های کیف پول
    wallets = get_all_wallets()

    # آمار مالی
    total_paid = sum(w["total_credit"] for w in wallets)
    total_transactions = sum(w["transaction_count"] for w in wallets)

    # هزینه بر اساس نوع خدمت
    cost_by_service = {}
    for w in wallets:
        for t in w["transactions"]:
            svc = t["service_type"]
            if svc not in cost_by_service:
                cost_by_service[svc] = {"total": 0, "count": 0, "label": t["service_label"]}
            cost_by_service[svc]["total"] += t["amount"]
            cost_by_service[svc]["count"] += 1

    cost_sorted = sorted(cost_by_service.items(), key=lambda x: x[1]["total"], reverse=True)

    # کیف پول کاربر فعلی
    my_wallet = get_wallet(u["id"]) if u.get("id") else {"balance": 0, "transactions": [], "total_credit": 0}

    # تراکنش‌های در انتظار تأیید (برای مددکار/مدیر)
    pending_txs = get_all_pending()

    return render_template("finance_dashboard.html", u=u,
                           wallets=wallets,
                           total_paid=total_paid,
                           total_transactions=total_transactions,
                           cost_by_service=cost_sorted,
                           my_wallet=my_wallet,
                           pending_txs=pending_txs,
                           SERVICE_COSTS=SERVICE_COSTS,
                           USERS=USERS)


# ─── تأیید اعتبار توسط مددکار/تیم نظارتی ───
@app.route("/finance/approve/<user_id>/<int:tx_index>", methods=["POST"])
@login_required
def finance_approve(user_id, tx_index):
    """تأیید یک تراکنش در انتظار."""
    u = current_user()
    if u["role"] not in ("worker", "hqmanager", "manager", "admin"):
        return "فقط مددکار یا مدیر مجاز به تأیید است.", 403
    approve_transaction(user_id, tx_index)
    return redirect(url_for("finance_dashboard"))


@app.route("/finance/approve-all/<user_id>", methods=["POST"])
@login_required
def finance_approve_all(user_id):
    """تأیید همهٔ تراکنش‌های در انتظار یک کاربر."""
    u = current_user()
    if u["role"] not in ("worker", "hqmanager", "manager", "admin"):
        return "فقط مددکار یا مدیر مجاز به تأیید است.", 403
    approve_all_pending(user_id)
    return redirect(url_for("finance_dashboard"))


# ─────────────────────────────────────────────────────────
# کاتالوگ (مرجع کامل)
# ─────────────────────────────────────────────────────────
@app.route("/catalog")
@login_required
def catalog():
    u = current_user()
    return render_template("catalog.html", u=u, dims=DIMENSIONS, axes=AXES,
                           sources=SOURCES, layers=LAYERS, rings=RINGS,
                           priority_classes=PRIORITY_CLASSES, stages=STAGES,
                           actors=ACTORS, red_lines=AI_RED_LINES,
                           triggers=LAYER3_TRIGGERS,
                           # افزوده‌های هماهنگ با سند
                           service_queues=SERVICE_QUEUE_FAMILIES,
                           action_relations=ACTION_RELATIONS,
                           action_ranks=ACTION_RANKS,
                           tiebreak_household=TIEBREAK_RULES_HOUSEHOLD,
                           tiebreak_queue=TIEBREAK_RULES_QUEUE,
                           control_rules=CONTROL_RULES,
                           component_meta=COMPONENT_META,
                           referral_paths=get_referral_paths_visual(),
                           assistant_roles=ASSISTANT_ROLES,
                           match_criteria=MATCH_CRITERIA)


# ─────────────────────────────────────────────────────────
# کاتالوگ خدمات شناسه‌دار (بند ۲ـ۱۴ سند)
# ─────────────────────────────────────────────────────────
@app.route("/services")
@login_required
def service_catalog():
    """نمایش کاتالوگ کامل ۲۶ خدمت شناسه‌دار با شرایط و رتبه‌ها."""
    u = current_user()
    from cdi_engine import (SERVICE_CATALOG, SERVICE_CATEGORIES,
                             SERVICE_STATUSES, ECONOMIC_INTERVENTION_PREREQUISITES,
                             SERVICE_QUEUE_FAMILIES, ACTION_RANKS, ACTION_RELATIONS)
    return render_template("service_catalog.html", u=u,
                           service_catalog=SERVICE_CATALOG,
                           service_categories=SERVICE_CATEGORIES,
                           service_statuses=SERVICE_STATUSES,
                           economic_prerequisites=ECONOMIC_INTERVENTION_PREREQUISITES,
                           service_queues=SERVICE_QUEUE_FAMILIES,
                           action_ranks=ACTION_RANKS,
                           action_relations=ACTION_RELATIONS)


# ─────────────────────────────────────────────────────────
# بررسی پیش‌نیازهای مداخله اقتصادی (تبصره ۳)
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/economic-prerequisites")
@login_required
def economic_prerequisites(hid):
    """بررسی ۷ پیش‌شرط ورود به مداخله اقتصادی برای یک خانوار."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))
    from cdi_engine import (check_economic_intervention_prerequisites,
                             ECONOMIC_INTERVENTION_PREREQUISITES, SERVICE_CATALOG)
    # محاسبهٔ خودکار پیش‌شرط‌ها
    prereq_result = check_economic_intervention_prerequisites(h.get("state", {}))
    # خدمات اقتصادی (دستهٔ هـ)
    economic_services = [s for s in SERVICE_CATALOG if s.get("requires_economic_prereq")]
    return render_template("economic_prerequisites.html", u=u, h=h, hid=hid,
                           prereq_result=prereq_result,
                           prerequisites=ECONOMIC_INTERVENTION_PREREQUISITES,
                           economic_services=economic_services)


# ─────────────────────────────────────────────────────────
# به‌روزرسانی وضعیت خدمت در سبد مداخله
# ─────────────────────────────────────────────────────────
@app.route("/household/<hid>/basket/<int:item_index>/status", methods=["POST"])
@login_required
def update_basket_status(hid, item_index):
    """به‌روزرسانی وضعیت یک خدمت در سبد مدخله (بند ۲ـ۸)."""
    u = current_user()
    if u["role"] not in ("worker", "hqmanager"):
        return "فقط مددکار خانواده یا مدیر ستاد مجاز به تغییر وضعیت خدمت هستند.", 403
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    # محاسبهٔ سبد مداخله
    st = h["state"]
    if st.get("active_axes") or st.get("redflags"):
        st_with_em = {**st, "em_input": h.get("em_input", {})}
        res = compute_household(st_with_em)
    else:
        return "سبد مدخله موجود نیست.", 400

    basket = res.get("basket", {})
    actions = basket.get("actions", [])
    if item_index < 0 or item_index >= len(actions):
        return "اندیس خدمت نامعتبر است.", 400

    new_status = request.form.get("status", "")
    from cdi_engine import SERVICE_STATUSES
    valid_statuses = [s["code"] for s in SERVICE_STATUSES]
    if new_status not in valid_statuses:
        return "وضعیت نامعتبر است.", 400

    # ذخیرهٔ تغییر وضعیت در پروندهٔ خانوار
    if "basket_status_overrides" not in h:
        h["basket_status_overrides"] = {}
    action_code = actions[item_index]["code"]
    h["basket_status_overrides"][action_code] = {
        "status": new_status,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "updated_by": u["role"],
        "note": request.form.get("note", ""),
    }
    h["history"].append({
        "at": datetime.now().isoformat(timespec="seconds"),
        "by": u["role"],
        "action": f"تغییر وضعیت خدمت {action_code} به {new_status}"
    })
    save_db(db)
    return redirect(url_for("intervention_basket", hid=hid))


# ═══════════════════════════════════════════════════════════
# ۱. گزارش نظارت و پایش کامل جریان (مددکار خانواده)
# ═══════════════════════════════════════════════════════════
@app.route("/worker/oversight")
@login_required
def worker_oversight():
    """گزارش نظارت کامل جریان از ثبت درخواست تا خروج پایدار."""
    u = current_user()
    if u["role"] not in ("worker", "hqmanager"):
        return "این بخش فقط برای مددکار خانواده یا مدیر ستاد مجاز است.", 403
    db = load_db()
    # فیلتر استانی
    all_hhs = list(db["households"].items())
    if u.get("province"):
        hhs = [(hid, h) for hid, h in all_hhs
               if h.get("identity", {}).get("province", "") == u["province"]]
    else:
        hhs = all_hhs

    # ساخت پیمانه کامل برای هر خانوار
    pipeline_rows = []
    for hid, h in hhs:
        ident = h.get("identity", {})
        emmpi = h.get("emmpi", {})
        result = emmpi.get("result", {}) if emmpi else {}
        state = h.get("state", {})
        sd = h.get("self_declaration", {})
        claimed = h.get("claimed_by", {})
        assigned = h.get("assigned_assistant", {})
        layer3_hist = h.get("layer3_history", [])
        decisions = h.get("decisions", [])
        appeals = h.get("appeals", [])
        basket_overrides = h.get("basket_status_overrides", {})

        # محاسبه پیشرفت
        steps_done = 0
        if h.get("status") != "pending" or claimed:
            steps_done = 1  # ثبت
        if emmpi:
            steps_done = 2  # غربالگری
        if state.get("answers"):
            steps_done = 3  # CDI لایه ۲
        if h.get("layer2_done"):
            steps_done = 3
        if h.get("layer3_done"):
            steps_done = 4
        if decisions:
            steps_done = 5
        if h.get("status") == "completed":
            steps_done = 6

        # محاسبه مدت زمان
        created = state.get("created_at", "") if state else ""
        last_event = h.get("history", [{}])[-1].get("at", "") if h.get("history") else ""
        duration_days = "—"
        if created and last_event:
            try:
                from datetime import datetime as dt
                c = dt.fromisoformat(created)
                e = dt.fromisoformat(last_event)
                duration_days = (e - c).days
            except Exception:
                pass

        # شمارش اقدامات
        basket_count = 0
        completed_actions = 0
        if h.get("state", {}).get("active_axes") or h.get("state", {}).get("redflags"):
            st_with_em = {**h.get("state", {}), "em_input": h.get("em_input", {})}
            try:
                res = compute_household(st_with_em)
                if res and res.get("basket"):
                    basket_count = res["basket"].get("total", 0)
            except Exception:
                pass
        completed_actions = len([v for v in basket_overrides.values() if v.get("status") == "completed"])

        pipeline_rows.append({
            "hid": hid,
            "name": ident.get("name", hid),
            "province": ident.get("province_name", "—"),
            "location": ident.get("location", "—"),
            "status": h.get("status", "pending"),
            "steps_done": steps_done,
            "duration_days": duration_days,
            "emmpi_score": result.get("score", "—"),
            "emmpi_level": result.get("level", {}).get("name", "—") if result.get("level") else "—",
            "red_flags": len(result.get("red_flags", [])),
            "active_axes": len(state.get("active_axes", [])),
            "layer2_done": h.get("layer2_done", False),
            "layer3_done": h.get("layer3_done", False),
            "layer3_count": len(layer3_hist),
            "decisions_count": len(decisions),
            "basket_total": basket_count,
            "completed_actions": completed_actions,
            "appeals_count": len(appeals),
            "claimed_by": claimed.get("name", "—") if claimed else "—",
            "claimed_role": claimed.get("role_label", "—") if claimed else "—",
            "assigned": assigned.get("name", "—") if assigned else "—",
            "channel": h.get("request_channel", "—"),
            "created_at": created[:10] if created else "—",
            "history_count": len(h.get("history", [])),
            "not_eligible": emmpi.get("not_eligible", False),
            "sd_yes_count": sd.get("yes_count", 0) if sd else 0,
        })

    # مرتب‌سازی بر اساس مرحله پیشرفت (کمترین پیشرفت اول)
    pipeline_rows.sort(key=lambda x: x["steps_done"])

    # آمار خلاصه
    total = len(pipeline_rows)
    stage_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    for r in pipeline_rows:
        stage_counts[r["steps_done"]] = stage_counts.get(r["steps_done"], 0) + 1

    avg_duration = "—"
    durations = [r["duration_days"] for r in pipeline_rows if isinstance(r["duration_days"], (int, float))]
    if durations:
        avg_duration = round(sum(durations) / len(durations), 1)

    # آمار بازیگران (چه کسی چه تعداد پرونده را انجام داده)
    actor_stats = {}
    for hid, h in hhs:
        for e in h.get("history", []):
            by = e.get("by", "")
            if by and by != "system":
                if by not in actor_stats:
                    actor_stats[by] = {"actions": 0, "name": ""}
                actor_stats[by]["actions"] += 1
                # نام بازیگر
        if h.get("claimed_by"):
            cb = h["claimed_by"]
            key = cb.get("role", "")
            if key not in actor_stats:
                actor_stats[key] = {"actions": 0, "name": cb.get("name", "")}
            actor_stats[key]["name"] = cb.get("name", actor_stats[key].get("name", ""))
        if h.get("layer3_history"):
            for l3 in h["layer3_history"]:
                key = l3.get("submitted_by", "")
                if key and key not in actor_stats:
                    actor_stats[key] = {"actions": 0, "name": l3.get("submitted_by_name", "")}
                if key in actor_stats:
                    actor_stats[key]["actions"] += 1

    # تبدیل برای template
    actor_rows = []
    for role, stats in actor_stats.items():
        role_label = ROLES.get(role, {}).get("label", role)
        actor_rows.append({
            "role": role,
            "label": role_label,
            "name": stats.get("name", ""),
            "actions": stats.get("actions", 0),
        })
    actor_rows.sort(key=lambda x: x["actions"], reverse=True)

    households_for_tpl = [{"hid": hid, "h": h} for hid, h in hhs]

    return render_template("worker_oversight.html", u=u,
                           pipeline_rows=pipeline_rows,
                           total=total,
                           stage_counts=stage_counts,
                           avg_duration=avg_duration,
                           actor_rows=actor_rows,
                           households=households_for_tpl)


# ═══════════════════════════════════════════════════════════
# ۲. فرم ارزیابی اثربخشی خدمات
# ═══════════════════════════════════════════════════════════
EFFECTIVENESS_CRITERIA = [
    {"code": "EFF1", "name": "کاهش شدت محرومیت", "desc": "آیا پس از مداخله، شدت محرومیت خانوار کاهش یافته است؟", "scale": 5},
    {"code": "EFF2", "name": "رفع گلوگاه اصلی", "desc": "آیا گلوگاه اصلی خانوار برطرف شد؟", "scale": 5},
    {"code": "EFF3", "name": "پایداری نتیجه", "desc": "آیا نتیجه مداخله پایدار بوده است؟", "scale": 5},
    {"code": "EFF4", "name": "تناسب با نیاز", "desc": "آیا مداخله متناسب با نیاز واقعی خانوار بود؟", "scale": 5},
    {"code": "EFF5", "name": "عدم تکرار خدمت", "desc": "آیا خدمت تکراری نبود و منابع هدر نرفت؟", "scale": 5},
    {"code": "EFF6", "name": "مشارکت خانوار", "desc": "آیا خانوار در فرایند مشارکت فعال داشت؟", "scale": 5},
    {"code": "EFF7", "name": "زمان‌بندی مناسب", "desc": "آیا مداخله در زمان مناسب انجام شد؟", "scale": 5},
    {"code": "EFF8", "name": "نقشه راه", "desc": "آیا نقشه راه توانمندسازی به‌درستی دنبال شد؟", "scale": 5},
]


@app.route("/household/<hid>/effectiveness", methods=["GET", "POST"])
@login_required
def effectiveness_form(hid):
    """فرم ارزیابی اثربخشی خدمات و نقشه راه توانمندسازی."""
    u = current_user()
    if u["role"] not in ("worker", "rose", "swclinic", "hqmanager"):
        return "ثبت ارزیابی اثربخشی فقط برای مددکار، کلینیک‌ها یا مدیر ستاد مجاز است.", 403
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    if request.method == "POST":
        # جمع‌آوری ارزیابی
        effectiveness = {
            "submitted_at": datetime.now().isoformat(timespec="seconds"),
            "submitted_by": u["role"],
            "submitted_by_name": u.get("name", u["role"]),
            "overall_rating": int(request.form.get("overall_rating", 3)),
            "summary": request.form.get("summary", ""),
            "criteria": {},
            "completed_actions": request.form.get("completed_actions", ""),
            "roadmap_followed": request.form.get("roadmap_followed", ""),
            "roadmap_effectiveness": request.form.get("roadmap_effectiveness", ""),
            "recommendations": request.form.get("recommendations", ""),
        }
        for crit in EFFECTIVENESS_CRITERIA:
            val = request.form.get(f"crit_{crit['code']}", "3")
            effectiveness["criteria"][crit["code"]] = {
                "name": crit["name"],
                "rating": int(val),
            }

        # ذخیره
        if "effectiveness_reviews" not in h:
            h["effectiveness_reviews"] = []
        h["effectiveness_reviews"].append(effectiveness)
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": f"ارزیابی اثربخشی ثبت شد — امتیاز کلی: {effectiveness['overall_rating']}/۵"
        })
        save_db(db)
        return redirect(url_for("household_view", hid=hid))

    return render_template("effectiveness_form.html", h=h, hid=hid, u=u,
                           criteria=EFFECTIVENESS_CRITERIA)


# ═══════════════════════════════════════════════════════════
# ۳. فرم نظرسنجی رضایت نیازمند
# ═══════════════════════════════════════════════════════════
SATISFACTION_QUESTIONS = [
    {"code": "SAT1", "q": "میزان رضایت از سرعت رسیدگی به درخواست شما", "scale": 5},
    {"code": "SAT2", "q": "میزان رضایت از نحوه برخورد و احترام بازیگران", "scale": 5},
    {"code": "SAT3", "q": "میزان رضایت از کیفیت خدمت دریافتی", "scale": 5},
    {"code": "SAT4", "q": "میزان رضایت از شفافیت و اطلاع‌رسانی", "scale": 5},
    {"code": "SAT5", "q": "میزان رضایت از نتیجه نهایی و تاثیر آن بر زندگی شما", "scale": 5},
    {"code": "SAT6", "q": "میزان رضایت از همیار/مددکار اختصاصی شما", "scale": 5},
    {"code": "SAT7", "q": "آیا نیاز اصلی شما برطرف شد؟", "scale": 2},  # yes/no
    {"code": "SAT8", "q": "آیا احساس می‌کنید نقشه راه توانمندسازی مؤثر بود؟", "scale": 5},
]


@app.route("/household/<hid>/satisfaction", methods=["GET", "POST"])
@login_required
def satisfaction_form(hid):
    """فرم نظرسنجی رضایت نیازمند از عملکرد بازیگران."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("index"))

    if request.method == "POST":
        satisfaction = {
            "submitted_at": datetime.now().isoformat(timespec="seconds"),
            "overall_rating": int(request.form.get("overall_rating", 3)),
            "best_actor": request.form.get("best_actor", ""),
            "worst_actor": request.form.get("worst_actor", ""),
            "feedback_text": request.form.get("feedback_text", ""),
            "questions": {},
            "would_recommend": bool(request.form.get("would_recommend")),
        }
        for q in SATISFACTION_QUESTIONS:
            val = request.form.get(f"sat_{q['code']}", "3")
            satisfaction["questions"][q["code"]] = {
                "question": q["q"],
                "rating": int(val),
            }

        if "satisfaction_surveys" not in h:
            h["satisfaction_surveys"] = []
        h["satisfaction_surveys"].append(satisfaction)
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": f"نظرسنجی رضایت ثبت شد — امتیاز کلی: {satisfaction['overall_rating']}/۵"
        })
        save_db(db)
        return redirect(url_for("beneficiary_status", hid=hid))

    # دریافت بازیگران مرتبط با این پرونده
    actors_involved = []
    if h.get("claimed_by"):
        actors_involved.append({
            "role": h["claimed_by"].get("role", ""),
            "name": h["claimed_by"].get("name", ""),
            "label": h["claimed_by"].get("role_label", ""),
        })
    if h.get("assigned_assistant"):
        actors_involved.append({
            "role": h["assigned_assistant"].get("role", ""),
            "name": h["assigned_assistant"].get("name", ""),
            "label": h["assigned_assistant"].get("role_label", ""),
        })
    for r in h.get("referrals", []):
        if r.get("to"):
            actors_involved.append({
                "role": r["to"],
                "name": ROLES.get(r["to"], {}).get("label", r["to"]),
                "label": ROLES.get(r["to"], {}).get("label", r["to"]),
            })

    return render_template("satisfaction_form.html", h=h, hid=hid, u=u,
                           questions=SATISFACTION_QUESTIONS,
                           actors_involved=actors_involved)


# ═══════════════════════════════════════════════════════════
# ۴. گزارش ارزیابی عملکرد بازیگران (مدیر ستاد)
# ═══════════════════════════════════════════════════════════
@app.route("/hq/performance")
@login_required
def hq_performance():
    """گزارش ارزیابی و سطح‌بندی عملکرد بازیگران زیست‌بوم."""
    u = current_user()
    if u["role"] not in ("hqmanager", "manager", "admin"):
        return "این بخش فقط برای مدیر ستاد مجاز است.", 403
    db = load_db()
    hhs = list(db["households"].items())

    # جمع‌آوری داده‌های عملکرد هر بازیگر
    perf_data = {}  # {role: {name, actions, emmpi_done, cdi_done, layer3_done, effectiveness_avg, satisfaction_avg, ...}}

    for hid, h in hhs:
        # شمارش اقدامات از تاریخچه
        for e in h.get("history", []):
            by = e.get("by", "")
            if not by or by == "system":
                continue
            if by not in perf_data:
                perf_data[by] = {
                    "role": by,
                    "label": ROLES.get(by, {}).get("label", by),
                    "name": "",
                    "total_actions": 0,
                    "emmpi_count": 0,
                    "cdi_l2_count": 0,
                    "cdi_l3_count": 0,
                    "decisions_count": 0,
                    "effectiveness_scores": [],
                    "satisfaction_scores": [],
                    "households_touched": set(),
                }
            perf_data[by]["total_actions"] += 1
            perf_data[by]["households_touched"].add(hid)
            action_text = e.get("action", "")
            if "EM-MPI" in action_text or "غربالگری" in action_text:
                perf_data[by]["emmpi_count"] += 1
            if "لایه ۲" in action_text or "ارزیابی لایه" in action_text:
                perf_data[by]["cdi_l2_count"] += 1
            if "لایه ۳" in action_text or "تحلیل لایه" in action_text:
                perf_data[by]["cdi_l3_count"] += 1
            if "تصمیم" in action_text:
                perf_data[by]["decisions_count"] += 1

        # نام بازیگر از claimed_by
        if h.get("claimed_by"):
            cb = h["claimed_by"]
            role = cb.get("role", "")
            if role in perf_data:
                perf_data[role]["name"] = cb.get("name", perf_data[role]["name"])

        # ارزیابی اثربخشی
        for rev in h.get("effectiveness_reviews", []):
            by = rev.get("submitted_by", "")
            if by not in perf_data:
                perf_data[by] = {
                    "role": by, "label": ROLES.get(by, {}).get("label", by), "name": "",
                    "total_actions": 0, "emmpi_count": 0, "cdi_l2_count": 0,
                    "cdi_l3_count": 0, "decisions_count": 0,
                    "effectiveness_scores": [], "satisfaction_scores": [],
                    "households_touched": set(),
                }
            perf_data[by]["effectiveness_scores"].append(rev.get("overall_rating", 3))
            perf_data[by]["name"] = rev.get("submitted_by_name", perf_data[by]["name"])

        # نظرسنجی رضایت (امتیاز به بازیگران)
        for sat in h.get("satisfaction_surveys", []):
            for q_code, q_data in sat.get("questions", {}).items():
                if q_code == "SAT6":  # رضایت از همیار/مددکار
                    # این امتیاز به claimed_by داده می‌شود
                    if h.get("claimed_by"):
                        role = h["claimed_by"].get("role", "")
                        if role in perf_data:
                            perf_data[role]["satisfaction_scores"].append(q_data.get("rating", 3))
            overall = sat.get("overall_rating", 3)
            # overall به همه بازیگران مرتبط داده می‌شود
            if h.get("claimed_by"):
                role = h["claimed_by"].get("role", "")
                if role in perf_data:
                    perf_data[role]["satisfaction_scores"].append(overall)

    # محاسبه امتیاز نهایی و سطح‌بندی
    perf_rows = []
    for role, data in perf_data.items():
        avg_eff = round(sum(data["effectiveness_scores"]) / len(data["effectiveness_scores"]), 1) if data["effectiveness_scores"] else 0
        avg_sat = round(sum(data["satisfaction_scores"]) / len(data["satisfaction_scores"]), 1) if data["satisfaction_scores"] else 0

        # امتیاز عملکرد (۰-۱۰۰)
        # ۴۰٪ حجم کار + ۳۰٪ اثربخشی + ۲۰٪ رضایت + ۱۰٪ تنوع پرونده
        volume_score = min(data["total_actions"] * 2, 40)
        eff_score = (avg_eff / 5 * 30) if avg_eff else 0
        sat_score = (avg_sat / 5 * 20) if avg_sat else 0
        diversity_score = min(len(data["households_touched"]) * 2, 10)
        total_score = round(volume_score + eff_score + sat_score + diversity_score, 1)

        # سطح‌بندی
        if total_score >= 80:
            level = "عالی"
            level_color = "P3"
        elif total_score >= 60:
            level = "خوب"
            level_color = "P2"
        elif total_score >= 40:
            level = "متوسط"
            level_color = "P1"
        else:
            level = "نیازمند بهبود"
            level_color = "P0"

        perf_rows.append({
            "role": role,
            "label": data["label"],
            "name": data["name"],
            "total_actions": data["total_actions"],
            "emmpi_count": data["emmpi_count"],
            "cdi_l2_count": data["cdi_l2_count"],
            "cdi_l3_count": data["cdi_l3_count"],
            "decisions_count": data["decisions_count"],
            "households_touched": len(data["households_touched"]),
            "avg_effectiveness": avg_eff,
            "avg_satisfaction": avg_sat,
            "performance_score": total_score,
            "level": level,
            "level_color": level_color,
            "volume_score": round(volume_score, 1),
            "eff_score": round(eff_score, 1),
            "sat_score": round(sat_score, 1),
            "diversity_score": round(diversity_score, 1),
        })

    # مرتب‌سازی بر اساس امتیاز عملکرد
    perf_rows.sort(key=lambda x: x["performance_score"], reverse=True)

    # آمار کلی
    total_actors = len(perf_rows)
    avg_perf = round(sum(r["performance_score"] for r in perf_rows) / total_actors, 1) if total_actors else 0
    by_level = {"عالی": 0, "خوب": 0, "متوسط": 0, "نیازمند بهبود": 0}
    for r in perf_rows:
        by_level[r["level"]] = by_level.get(r["level"], 0) + 1

    return render_template("hq_performance.html", u=u,
                           perf_rows=perf_rows,
                           total_actors=total_actors,
                           avg_perf=avg_perf,
                           by_level=by_level)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=5000)
else:
    # When imported as module, ensure app is available
    pass

# ─── مسیرهای موبایل اپ (PWA) ───
import mobile_routes

# ─── قابلیت‌های موبایل: رضایت‌سنجی، کیف پول، داشبورد ───
import mobile_features
