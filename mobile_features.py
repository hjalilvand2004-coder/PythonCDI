# -*- coding: utf-8 -*-
"""
مسیرهای موبایل — قابلیت‌های کامل اپلیکیشن
شامل: رضایت‌سنجی، کیف پول همیار، خدمات ارائه‌شده
"""
from main import (app, login_required, current_user, load_db, save_db,
                  get_wallet, credit_wallet, get_all_wallets,
                  compute_service_cost, get_service_label,
                  EMMPI_DIMENSIONS)
from flask import render_template, request, redirect, url_for, session, jsonify
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# رضایت‌سنجی نیازمند از عملکرد همیار (مثل اسنپ)
# ═══════════════════════════════════════════════════════════
SATISFACTION_DIMENSIONS = [
    {"id": "behavior", "label": "نحوه برخورد همیار", "icon": "😊"},
    {"id": "expertise", "label": "تخصص و دانش همیار", "icon": "🎓"},
    {"id": "punctuality", "label": "وقت‌شناسی و پاسخگویی", "icon": "⏰"},
    {"id": "followup", "label": "پیگیری و رسیدگی", "icon": "📋"},
    {"id": "respect", "label": "احترام به حریم خصوصی", "icon": "🔒"},
]

@app.route("/m/satisfaction/<hid>", methods=["GET", "POST"])
@login_required
def mobile_satisfaction(hid):
    """فرم رضایت‌سنجی نیازمند از عملکرد همیار."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("mobile_home"))

    if request.method == "POST":
        # جمع‌آوری امتیازها
        scores = {}
        total = 0
        count = 0
        for dim in SATISFACTION_DIMENSIONS:
            val = request.form.get(f"score_{dim['id']}")
            if val:
                scores[dim["id"]] = int(val)
                total += int(val)
                count += 1

        comment = request.form.get("comment", "").strip()
        avg_score = round(total / count, 1) if count > 0 else 0

        satisfaction = {
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u.get("id", u.get("role")),
            "by_name": u.get("name", ""),
            "scores": scores,
            "average": avg_score,
            "comment": comment,
            "assistant_id": h.get("claimed_by", {}).get("id", ""),
            "assistant_name": h.get("claimed_by", {}).get("name", ""),
        }

        if "satisfaction" not in h:
            h["satisfaction"] = []
        h["satisfaction"].append(satisfaction)
        h["status"] = "closed"
        h["history"].append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "by": u.get("role"),
            "action": f"ثبت رضایت‌سنجی — میانگین: {avg_score} از ۵"
        })
        save_db(db)
        return render_template("mobile/satisfaction_done.html", u=u, h=h, score=avg_score)

    # GET
    assistant = h.get("claimed_by", {})
    return render_template("mobile/satisfaction.html", u=u, h=h, hid=hid,
                           assistant=assistant, dimensions=SATISFACTION_DIMENSIONS)


# ═══════════════════════════════════════════════════════════
# کیف پول همیار + خدمات ارائه‌شده
# ═══════════════════════════════════════════════════════════
@app.route("/m/wallet")
@login_required
def mobile_wallet():
    """کیف پول همیار — نمایش خدمات ارائه‌شده و درآمد."""
    u = current_user()
    if u["role"] not in ("assistant", "worker", "rose", "swclinic", "employ"):
        return redirect(url_for("mobile_home"))

    db = load_db()
    wallet = get_wallet(u.get("id", u["role"]))

    # خدمات ارائه‌شده توسط این همیار
    my_services = []
    total_earned = 0
    total_pending = 0

    for hid, h in db["households"].items():
        claimed = h.get("claimed_by") or {}
        if claimed.get("id") == u.get("id", u["role"]) or claimed.get("role") == u["role"]:
            # محاسبه هزینه خدمت
            emmpi_score = h.get("emmpi", {}).get("result", {}).get("score", 0)
            rf = h.get("emmpi", {}).get("result", {}).get("red_flags", [])
            if emmpi_score >= 600 or rf:
                priority = "P0"
            elif emmpi_score >= 450:
                priority = "P1"
            elif emmpi_score >= 300:
                priority = "P2"
            elif emmpi_score >= 150:
                priority = "P3"
            else:
                priority = "P4"

            svc_type = "emmpi_redflag" if rf else "emmpi_assessment"
            cost = compute_service_cost(svc_type, role=u["role"], priority=priority)

            satisfaction = h.get("satisfaction", [{}])[-1] if h.get("satisfaction") else {}

            my_services.append({
                "hid": hid,
                "name": h.get("identity", {}).get("name", hid),
                "status": h.get("status", ""),
                "emmpi_score": emmpi_score,
                "cost": cost,
                "priority": priority,
                "satisfaction": satisfaction.get("average", None),
                "date": claimed.get("claimed_at", ""),
            })
            total_earned += cost

    # تراکنش‌های کیف پول
    transactions = wallet.get("transactions", [])

    return render_template("mobile/wallet.html", u=u, wallet=wallet,
                           my_services=my_services,
                           total_earned=total_earned,
                           total_pending=wallet.get("pending_balance", 0),
                           transactions=transactions[-10:])


# ═══════════════════════════════════════════════════════════
# داشبورد همیار — آمار عملکرد
# ═══════════════════════════════════════════════════════════
@app.route("/m/dashboard")
@login_required
def mobile_dashboard():
    """داشبورد عملکرد همیار."""
    u = current_user()
    db = load_db()

    stats = {
        "total_cases": 0,
        "completed": 0,
        "in_progress": 0,
        "avg_satisfaction": 0,
        "total_earned": 0,
        "urgent_cases": 0,
    }

    satisfaction_scores = []
    my_cases = []

    for hid, h in db["households"].items():
        claimed = h.get("claimed_by") or {}
        if claimed.get("id") == u.get("id", u["role"]) or claimed.get("role") == u["role"]:
            stats["total_cases"] += 1
            status = h.get("status", "")
            if status == "closed":
                stats["completed"] += 1
            elif status in ("claimed", "emmpi_done"):
                stats["in_progress"] += 1

            # رضایت‌سنجی
            if h.get("satisfaction"):
                avg = h["satisfaction"][-1].get("average", 0)
                satisfaction_scores.append(avg)

            # پرچم فوری
            if h.get("emmpi", {}).get("result", {}).get("red_flags"):
                stats["urgent_cases"] += 1

            my_cases.append({"hid": hid, "h": h})

    if satisfaction_scores:
        stats["avg_satisfaction"] = round(sum(satisfaction_scores) / len(satisfaction_scores), 1)

    # محاسبه درآمد کل
    wallet = get_wallet(u.get("id", u["role"]))
    stats["total_earned"] = wallet.get("balance", 0) + wallet.get("pending_balance", 0)

    return render_template("mobile/dashboard.html", u=u, stats=stats, my_cases=my_cases[:5])
