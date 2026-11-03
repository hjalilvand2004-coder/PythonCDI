# -*- coding: utf-8 -*-
"""
مسیرهای موبایل اپلیکیشن — نسخه PWA
"""
from flask import render_template, request, session, redirect, url_for, jsonify
from main import app, login_required, current_user, load_db, EMMPI_DIMENSIONS, EMMPI_INDICATOR_TITLES


# ═══════════════════════════════════════════════════════════
# موبایل اپ — داشبورد اصلی
# ═══════════════════════════════════════════════════════════
@app.route("/m")
@app.route("/mobile")
@login_required
def mobile_home():
    """صفحه اصلی موبایل اپ — داشبورد بر اساس نقش."""
    u = current_user()
    db = load_db()

    # آمار بر اساس نقش
    stats = {"pending": 0, "claimed": 0, "done": 0, "urgent": 0}
    my_cases = []

    for hid, h in db["households"].items():
        status = h.get("status", "pending")
        if status in stats:
            stats[status] += 1
        # پرچم‌های فوری
        if h.get("emmpi", {}).get("result", {}).get("red_flags"):
            stats["urgent"] += 1
        # پرونده‌های من
        claimed = h.get("claimed_by") or {}
        if claimed.get("id") == u.get("id", u.get("role")):
            my_cases.append({"hid": hid, "h": h})

    return render_template("mobile/home.html", u=u, stats=stats, my_cases=my_cases[:5])


@app.route("/m/pool")
@login_required
def mobile_pool():
    """استخر درخواست‌ها — نسخه موبایل."""
    u = current_user()
    db = load_db()
    cases = []
    for hid, h in db["households"].items():
        if h.get("status") == "pending":
            cases.append({"hid": hid, "h": h})
    return render_template("mobile/pool.html", u=u, cases=cases)


@app.route("/m/case/<hid>")
@login_required
def mobile_case_detail(hid):
    """جزئیات پرونده — نسخه موبایل."""
    u = current_user()
    db = load_db()
    h = db["households"].get(hid)
    if not h:
        return redirect(url_for("mobile_home"))
    return render_template("mobile/case_detail.html", u=u, h=h, hid=hid)
