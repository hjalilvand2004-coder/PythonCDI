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

from flask import Flask, redirect, render_template, request, session, url_for

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
                          get_referral_paths_visual)

# ─── وب‌سرویس‌های فرضی (ثبت‌احوال، بیمه، آموزش، اشتغال) ───
from web_services import (fetch_all_services, fetch_civil_registry,
                          fetch_insurance, fetch_education, fetch_employment,
                          fetch_housing, DATA_SOURCE_PRIORITIES)

# ─── داده‌های جغرافیایی ایران (۳۱ استان + شهرها + مختصات) ───
from iran_geo import (PROVINCES, get_province_choices, get_cities_for_province,
                      get_province_name, get_province_coords, get_all_province_coords)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdi_data.json")

app = Flask(__name__)
app.secret_key = "cdi-prototype-secret-key"  # نمونهٔ اولیه

USERS = {
    "beneficiary": {"password": "1234", "name": "نیازمند (نمونه)"},
    "assistant": {"password": "1234", "name": "همیار مددکار (نمونه)"},
    "rose": {"password": "1234", "name": "کلینیک مشاوره رز (نمونه)"},
    "swclinic": {"password": "1234", "name": "کلینیک مددکاری (نمونه)"},
    "worker": {"password": "1234", "name": "مددکار خانواده (نمونه)"},
    "employ": {"password": "1234", "name": "کارشناس اشتغال (نمونه)"},
    "manager": {"password": "1234", "name": "مدیر خدمت (نمونه)"},
    "hqmanager": {"password": "1234", "name": "مدیر ستاد مرکزی (نمونه)"},
}
ALL_ROLES = list(USERS.keys())


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
        return {"id": uid, "role": uid, **ROLES.get(uid, {}),
                "name": USERS[uid]["name"]}
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
    return render_template("login.html", error=error, users=USERS, roles=ROLES)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


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
        st = h.get("state", {})
        if st.get("active_axes") or st.get("redflags"):
            st_with_em = {**st, "em_input": h.get("em_input", {})}
            res = compute_household(st_with_em)
        else:
            res = None
        hhs.append({"hid": hid, "h": h, "res": res})

    # برای نیازمندان: فقط پرونده‌های خودشان
    if u["role"] == "beneficiary":
        beneficiary_hid = session.get("beneficiary_hid")
        hhs = [hh for hh in hhs if hh["hid"] == beneficiary_hid or hh["h"].get("identity", {}).get("national_id") == session.get("uid")]

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
        national_id = request.form.get("national_id", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip()
        name = request.form.get("name", "").strip()
        province = request.form.get("province", "").strip()
        city = request.form.get("city", "").strip()
        location = f"{get_province_name(province)}، {city}" if province and city else ""

        if not national_id:
            return render_template("beneficiary_new_request.html", u=u, error="شناسهٔ ملی الزامی است.",
                                   provinces=get_province_choices(), PROVINCES=PROVINCES)
        if not date_of_birth:
            return render_template("beneficiary_new_request.html", u=u, error="تاریخ تولد الزامی است.",
                                   national_id=national_id, name=name,
                                   provinces=get_province_choices(), PROVINCES=PROVINCES)

        db = load_db()
        # ساخت شناسهٔ خانوار
        hid = f"H-{national_id[-6:]}"
        if hid in db["households"]:
            return render_template("beneficiary_new_request.html", u=u,
                                   error="شما قبلاً درخواست ثبت کرده‌اید.",
                                   national_id=national_id, name=name, date_of_birth=date_of_birth)

        # واکشی داده‌های وب‌سرویس (فرضی) — با نام و تاریخ تولد واردشده
        ws_data = fetch_all_services(national_id, name=name or None, date_of_birth=date_of_birth)

        # اطلاعات از ثبت‌احوال
        civil = ws_data["civil_registry"]["data"]
        head_name = civil.get("head_name", name or "")

        # ساخت پرونده
        geo_lat = request.form.get("geo_lat", "").strip()
        geo_lng = request.form.get("geo_lng", "").strip()
        h = {
            "identity": {
                "hid": hid,
                "national_id": national_id,
                "name": head_name,
                "province": province,
                "province_name": get_province_name(province),
                "city": city,
                "location": location,
                "geo_lat": geo_lat,
                "geo_lng": geo_lng,
                "members": str(civil.get("family_size", "")),
                "contact": request.form.get("contact", ""),
                "at_risk": request.form.get("at_risk", ""),
            },
            "em_input": {"level": "", "redflags": [], "em_dims": [], "redflag_labels": [],
                         "services_received": [], "em_date": "", "note": ""},
            "state": {"redflags": [], "em_dims": [], "active_axes": [], "answers": {},
                      "created_at": datetime.now().isoformat(timespec="seconds"),
                      "created_by": u["role"]},
            "layer2_done": False, "layer3_done": False,
            "decisions": [], "referrals": [], "history": [],
            "preferences": {}, "capacities": [], "causes": [],
            # فیلدهای جدید:
            "national_id": national_id,
            "status": "pending",  # pending | claimed | emmpi_done | cdi_in_progress | completed
            "claimed_by": None,
            "self_declaration": {
                "submitted_at": datetime.now().isoformat(timespec="seconds"),
                "submitted_by": u["role"],
                "need_description": request.form.get("need_description", ""),
                "at_risk": request.form.get("at_risk", ""),
                "preferred_contact": request.form.get("preferred_contact", ""),
                "preferred_gender": request.form.get("preferred_gender", ""),
                "preferred_language": request.form.get("preferred_language", "فارسی"),
                # پرسش‌های خوداظهاری (پیش‌ارزیابی ۱۸ سؤالی)
                "questions": {
                    "health_illness": request.form.get("sd_health_illness", "no"),
                    "disability": request.form.get("sd_disability", "no"),
                    "food": request.form.get("sd_food", "no"),
                    "mental": request.form.get("sd_mental", "no"),
                    "violence": request.form.get("sd_violence", "no"),
                    "dropout": request.form.get("sd_dropout", "no"),
                    "literacy": request.form.get("sd_literacy", "no"),
                    "skills": request.form.get("sd_skills", "no"),
                    "housing": request.form.get("sd_housing", "no"),
                    "utilities": request.form.get("sd_utilities", "no"),
                    "rent": request.form.get("sd_rent", "no"),
                    "housing_quality": request.form.get("sd_housing_quality", "no"),
                    "unemployment": request.form.get("sd_unemployment", "no"),
                    "debt": request.form.get("sd_debt", "no"),
                    "income": request.form.get("sd_income", "no"),
                    "caregiving": request.form.get("sd_caregiving", "no"),
                    "network": request.form.get("sd_network", "no"),
                    "legal": request.form.get("sd_legal", "no"),
                },
                # شمارش پاسخ‌های «بله» برای هشدار فوریت
                "yes_count": sum(1 for k in [
                    "sd_health_illness","sd_disability","sd_food","sd_mental","sd_violence",
                    "sd_dropout","sd_skills","sd_housing","sd_utilities","sd_rent",
                    "sd_housing_quality","sd_unemployment","sd_debt","sd_income",
                    "sd_caregiving","sd_legal"
                ] if request.form.get(k) == "yes"),
            },
            "web_service_data": ws_data,
        }
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u["role"],
            "action": "ثبت درخواست توسط نیازمند + واکشی وب‌سرویس"
        })
        db["households"][hid] = h
        save_db(db)

        # ذخیرهٔ hid در session
        session["beneficiary_hid"] = hid
        return redirect(url_for("beneficiary_status", hid=hid))

    # GET: نمایش فرم
    provinces = get_province_choices()
    return render_template("beneficiary_new_request.html", u=u,
                           provinces=provinces,
                           PROVINCES=PROVINCES)


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


# ═══════════════════════════════════════════════════════════
# استخر درخواست‌ها برای همیاران (مانند اسنپ — بند ۹)
# ═══════════════════════════════════════════════════════════
@app.route("/assistant/pool")
@login_required
def assistant_pool():
    """استخر درخواست‌های در انتظار — همیاران می‌توانند انتخاب کنند."""
    u = current_user()
    db = load_db()

    # فهرست درخواست‌های pending
    pending_requests = []
    for hid, h in db["households"].items():
        if h.get("status") == "pending":
            # محاسبهٔ امتیاز تطبیق برای این همیار (اگر نقش همیار است)
            match_score = 0
            match_reasons = []
            if u["role"] in ("assistant", "worker", "rose", "swclinic", "employ"):
                # یافتن همیار متناظر
                ast = next((a for a in SAMPLE_ASSISTANTS if a["role"] == u["role"]), None)
                if not ast:
                    ast = SAMPLE_ASSISTANTS[0]  # پیش‌فرض
                # محاسبهٔ تطبیق ساده
                loc = (h.get("identity", {}).get("location", "") or "").lower()
                ast_areas = [a.lower() for a in ast.get("areas", [])]
                loc_match = any(a in loc or loc in a for a in ast_areas) if loc else False
                match_score = 50 + (20 if loc_match else 0)
                match_reasons = ["موقعیت منطبق" if loc_match else "سایر مناطق"]

            pending_requests.append({
                "hid": hid, "h": h, "match_score": match_score,
                "match_reasons": match_reasons,
            })

    # مرتب‌سازی بر اساس امتیاز تطبیق (نزولی)
    pending_requests.sort(key=lambda x: x["match_score"], reverse=True)

    # درخواست‌های تخصیص‌یافته به این کاربر
    my_claims = []
    for hid, h in db["households"].items():
        if h.get("claimed_by") and h["claimed_by"].get("id") == u["role"]:
            my_claims.append({"hid": hid, "h": h})

    return render_template("assistant_pool.html", u=u,
                           pending_requests=pending_requests,
                           my_claims=my_claims,
                           assistant_roles=ASSISTANT_ROLES,
                           match_criteria=MATCH_CRITERIA)


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

    # هدایت به فرم EM-MPI برای انجام غربالگری
    return redirect(url_for("emmpi_form", hid=hid))


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

        # محاسبهٔ EM-MPI
        result = compute_emmpi(indicators_data)

        # ذخیره در پروندهٔ خانوار
        h["emmpi"] = {
            "indicators": indicators_data,
            "result": result,
            "computed_at": datetime.now().isoformat(timespec="seconds"),
            "computed_by": u["role"],
        }

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
        if redflags_for_cdi:
            h["history"].append({
                "at": datetime.now().isoformat(timespec="seconds"),
                "by": u["role"],
                "action": f"فعال‌سازی {len(h['state']['active_axes'])} محور CDI بر اساس پرچم‌های قرمز EM-MPI"
            })

        save_db(db)
        return redirect(url_for("emmpi_result", hid=hid))

    # GET: نمایش فرم
    existing_data = None
    if h.get("emmpi") and h["emmpi"].get("indicators"):
        existing_data = h["emmpi"]["indicators"]

    indicators_by_dim = get_indicator_list_by_dim()
    # افزودن dim_label به هر شاخص
    for dim_key, inds in indicators_by_dim.items():
        for ind in inds:
            ind["dim_label"] = EMMPI_DIMENSIONS[dim_key]["name"]

    return render_template("emmpi_form.html", h=h, hid=hid, u=u,
                           DIMENSIONS=EMMPI_DIMENSIONS,
                           indicators_by_dim=indicators_by_dim,
                           severity_options=SEVERITY_OPTIONS,
                           existing_data=existing_data)


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


# ═══════════════════════════════════════════════════════════
# سیستم تخصیص هوشمند همیاران (مانند اسنپ — بند ۹)
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
            h["layer3_done"] = True
            h["history"].append({"at": datetime.now().isoformat(timespec="seconds"),
                                 "by": u["role"], "action": "تحلیل لایه ۳ ثبت شد",
                                 "reasons": res["layer3_reasons"]})
            save_db(db)
            return redirect(url_for("household_view", hid=hid))
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
    hhs = list(db["households"].items())

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

    # تبدیل به فرمت مورد نظر سایدبار (list of dicts با کلید h)
    households_for_tpl = [{"hid": hid, "h": h, "res": None} for hid, h in hhs]

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
                           households=households_for_tpl)


# ─────────────────────────────────────────────────────────
# داشبورد ستاد مرکزی (گزارش کل کشور + نقشه ایران)
# ─────────────────────────────────────────────────────────
@app.route("/hq/dashboard")
@login_required
def hq_dashboard():
    """داشبورد ستاد مرکزی — گزارش کل کشور + نقشه."""
    u = current_user()
    db = load_db()
    hhs = list(db["households"].items())

    # آمار کلی کشور
    total = len(hhs)
    by_province = {}
    by_priority_country = {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "P4": 0}
    emmpi_count = 0
    red_flag_count = 0
    avg_score = 0
    scores = []

    for hid, h in hhs:
        # تعیین استان پرونده
        loc = (h.get("identity", {}).get("location", "") or "").lower()
        # تطبیق با استان‌ها
        prov_key = "unknown"
        for pk, pv in PROVINCES.items():
            if pv["name"] in loc or loc in pv["name"] or any(c in loc for c in pv["cities"]):
                prov_key = pk
                break
        by_province[prov_key] = by_province.get(prov_key, 0) + 1

        if h.get("emmpi"):
            r = h["emmpi"].get("result", {})
            emmpi_count += 1
            scores.append(r.get("score", 0))
            rf = r.get("red_flags", [])
            red_flag_count += len(rf)
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

    avg_score = round(sum(scores) / len(scores)) if scores else 0

    # داده‌های نقشه — مختصات واقعی استان‌ها
    map_provinces = get_all_province_coords()

    # آمار هر استان روی نقشه
    map_with_stats = []
    for m in map_provinces:
        count = by_province.get(m["key"], 0)
        map_with_stats.append({**m, "count": count})

    # مارکرهای پرونده‌ها (برای نقشه Leaflet)
    household_markers = []
    for hid, h in hhs:
        prov_key = h.get("identity", {}).get("province", "")
        lat, lng = get_province_coords(prov_key)
        household_markers.append({
            "lat": lat, "lng": lng,
            "name": h.get("identity", {}).get("name", hid),
            "hid": hid, "count": 1,
        })

    return render_template("hq_dashboard.html", u=u,
                           total=total, emmpi_count=emmpi_count,
                           red_flag_count=red_flag_count, avg_score=avg_score,
                           by_priority=by_priority_country,
                           by_province=by_province,
                           map_data=map_with_stats,
                           household_markers=household_markers,
                           PROVINCES=PROVINCES,
                           households=[{"hid": hid, "h": h} for hid, h in hhs])


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


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=5000)
