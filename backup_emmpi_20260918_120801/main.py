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

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdi_data.json")

app = Flask(__name__)
app.secret_key = "cdi-prototype-secret-key"  # نمونهٔ اولیه

USERS = {
    "assistant": {"password": "1234", "name": "همیار مددکار (نمونه)"},
    "rose": {"password": "1234", "name": "کلینیک مشاوره رز (نمونه)"},
    "swclinic": {"password": "1234", "name": "کلینیک مددکاری (نمونه)"},
    "worker": {"password": "1234", "name": "مددکار خانواده (نمونه)"},
    "employ": {"password": "1234", "name": "کارشناس اشتغال (نمونه)"},
    "manager": {"password": "1234", "name": "مدیر خدمت (نمونه)"},
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
            # افزودن em_input برای محاسبهٔ PEH
            st_with_em = {**st, "em_input": h.get("em_input", {})}
            res = compute_household(st_with_em)
        else:
            res = None
        hhs.append({"hid": hid, "h": h, "res": res})
    return render_template("dashboard.html", u=u, households=hhs)


# ─────────────────────────────────────────────────────────
# ایجاد پرونده + لایه ۱
# ─────────────────────────────────────────────────────────
@app.route("/household/new", methods=["GET", "POST"])
@login_required
def household_new():
    if request.method == "POST":
        hid = request.form.get("hid", "").strip()
        if not hid:
            return render_template("household_new.html", error="شناسهٔ خانوار الزامی است.")
        db = load_db()
        if hid in db["households"]:
            return render_template("household_new.html", error="این شناسه از قبل موجود است.")
        redflags = request.form.getlist("redflags")
        em_dims = request.form.getlist("em_dims")
        extra = request.form.getlist("extra_axes")
        manual = request.form.getlist("manual_axes")
        active = activate_axes(redflags, em_dims, extra, manual)
        h = {
            "identity": {
                "hid": hid, "name": request.form.get("name", ""),
                "location": request.form.get("location", ""),
                "members": request.form.get("members", ""),
                "contact": request.form.get("contact", ""),
                "at_risk": request.form.get("at_risk", ""),
            },
            "em_input": {
                "level": request.form.get("em_level", ""),
                "redflags": redflags,
                "em_dims": em_dims,
                "redflag_labels": [REDLABELS.get(r, r) for r in redflags],
                "services_received": [s.strip() for s in request.form.get("services", "").split("،") if s.strip()],
                "em_date": request.form.get("em_date", ""),
                "note": request.form.get("em_note", ""),
            },
            "state": {
                "redflags": redflags, "em_dims": em_dims,
                "active_axes": active, "answers": {},
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "created_by": session["uid"],
            },
            "layer2_done": False, "layer3_done": False,
            "decisions": [], "referrals": [], "history": [],
            "preferences": {}, "capacities": [], "causes": [],
        }
        db["households"][hid] = h
        save_db(db)
        return redirect(url_for("household_view", hid=hid))
    return render_template("household_new.html")


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
    return render_template("profile.html", h=h, hid=hid, res=res, prof=prof,
                           action_ranks=ACTION_RANKS,
                           service_queues=SERVICE_QUEUE_FAMILIES,
                           action_relations=ACTION_RELATIONS,
                           tiebreak_household=TIEBREAK_RULES_HOUSEHOLD,
                           tiebreak_queue=TIEBREAK_RULES_QUEUE,
                           control_rules=CONTROL_RULES)


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
                           roles=ROLES)


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
        q["items"].sort(key=lambda x: (p_order.get(x["p"], 9), rank_order.get(x["rank"], 9), -x["pim"]))
    return render_template("service_queues.html", u=u, queues=queue_map.values(),
                           action_ranks=ACTION_RANKS,
                           tiebreak_rules=TIEBREAK_RULES_QUEUE)


# ─────────────────────────────────────────────────────────
# کاتالوگ (مرجع کامل)
# ─────────────────────────────────────────────────────────
@app.route("/catalog")
@login_required
def catalog():
    return render_template("catalog.html", dims=DIMENSIONS, axes=AXES,
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
                           control_rules=CONTROL_RULES)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=5000)
