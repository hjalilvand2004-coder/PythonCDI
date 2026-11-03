# -*- coding: utf-8 -*-
"""
سیستم مالی سامانه — هزینه خدمات و کیف پول همیاران
مانند اسنپ: هر اقدام هزینه دارد و به کیف پول انجام‌دهنده شارژ می‌شود.
"""

# هزینه پایهٔ خدمات (به تومان)
SERVICE_COSTS = {
    # ثبت درخواست اولیه (بدون هزینه برای نیازمند)
    "registration": {"cost": 0, "label": "ثبت درخواست اولیه", "payer": "system"},

    # بازدید میدانی و تکمیل اطلاعات
    "field_visit": {"cost": 50000, "label": "بازدید میدانی", "payer": "system"},
    "info_completion": {"cost": 30000, "label": "تکمیل اطلاعات اولیه", "payer": "system"},

    # EM-MPI
    "emmpi_assessment": {"cost": 80000, "label": "ارزیابی EM-MPI (۳۵ شاخص)", "payer": "system"},
    "emmpi_redflag": {"cost": 120000, "label": "ارزیابی EM-MPI با پرچم قرمز", "payer": "system"},

    # CDI لایه‌ها
    "cdi_layer1": {"cost": 60000, "label": "CDI سریع (لایه ۱)", "payer": "system"},
    "cdi_layer2": {"cost": 150000, "label": "CDI هدفمند (لایه ۲)", "payer": "system"},
    "cdi_layer3": {"cost": 300000, "label": "CDI عمیق (لایه ۳)", "payer": "system"},

    # مشاوره
    "rose_counseling": {"cost": 100000, "label": "مشاوره کلینیک رز", "payer": "system"},
    "swclinic_analysis": {"cost": 250000, "label": "تحلیل کلینیک تخصصی مددکاری", "payer": "system"},

    # اشتغال
    "employ_assessment": {"cost": 120000, "label": "ارزیابی اشتغال", "payer": "system"},
    "employ_business_plan": {"cost": 200000, "label": "طراحی طرح کسب‌وکار", "payer": "system"},

    # پایش
    "monitoring_visit": {"cost": 40000, "label": "بازدید پایش دوره‌ای", "payer": "system"},
    "monitoring_report": {"cost": 25000, "label": "گزارش پایش", "payer": "system"},

    # تصمیم نهایی مددکار
    "worker_decision": {"cost": 150000, "label": "تصمیم نهایی مددکار خانواده", "payer": "system"},

    # ارجاع
    "referral": {"cost": 20000, "label": "ثبت ارجاع تخصصی", "payer": "system"},
}

# ضریب پیچیدگی بر اساس اولویت
COMPLEXITY_MULTIPLIERS = {
    "P0": 2.0,  # بحرانی — هزینه ۲ برابر
    "P1": 1.5,  # فوری — ۱.۵ برابر
    "P2": 1.0,  # عادی
    "P3": 0.8,  # توانمندسازی — کمتر
    "P4": 0.5,  # پایش — حداقل
}

# ضریب نقش (مددکار رسمی گران‌تر از همیار)
ROLE_MULTIPLIERS = {
    "worker": 1.5,
    "swclinic": 1.8,
    "rose": 1.2,
    "employ": 1.3,
    "assistant": 1.0,
}


def compute_service_cost(service_type, role="assistant", priority="P2"):
    """
    محاسبهٔ هزینهٔ نهایی خدمت.
    هزینه = پایه × ضریب نقش × ضریب پیچیدگی
    """
    base = SERVICE_COSTS.get(service_type, {"cost": 50000})["cost"]
    role_mult = ROLE_MULTIPLIERS.get(role, 1.0)
    priority_mult = COMPLEXITY_MULTIPLIERS.get(priority, 1.0)
    return round(base * role_mult * priority_mult)


def get_service_label(service_type):
    """برگرداندن برچسب فارسی خدمت."""
    return SERVICE_COSTS.get(service_type, {"label": service_type})["label"]


# کیف پول فرضی — در سیستم واقعی در دیتابیس ذخیره می‌شود
WALLETS = {}  # {user_id: {"balance": int, "transactions": [...]}}


def get_wallet(user_id):
    """برگرداندن موجودی کیف پول."""
    if user_id not in WALLETS:
        WALLETS[user_id] = {"balance": 0, "transactions": []}
    return WALLETS[user_id]


def credit_wallet(user_id, amount, service_type, hid="", note="", status="approved"):
    """شارژ کیف پول همیار پس از انجام خدمت.
    status: 'pending' (در انتظار تأیید مددکار) یا 'approved' (تأییدشده)
    """
    w = get_wallet(user_id)
    from datetime import datetime
    tx = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "type": "credit",
        "amount": amount,
        "service_type": service_type,
        "service_label": get_service_label(service_type),
        "hid": hid,
        "note": note,
        "status": status,
    }
    w["transactions"].append(tx)
    if status == "approved":
        w["balance"] += amount


def credit_wallet_pending(user_id, amount, service_type, hid="", note=""):
    """شارژ در انتظار تأیید — پس از تأیید مددکار فعال می‌شود."""
    credit_wallet(user_id, amount, service_type, hid, note, status="pending")


def approve_transaction(user_id, tx_index):
    """تأیید یک تراکنشِ در انتظار توسط مددکار/تیم نظارتی."""
    w = get_wallet(user_id)
    if 0 <= tx_index < len(w["transactions"]):
        tx = w["transactions"][tx_index]
        if tx["status"] == "pending":
            tx["status"] = "approved"
            w["balance"] += tx["amount"]
            return True
    return False


def approve_all_pending(user_id):
    """تأیید همهٔ تراکنش‌های در انتظار یک کاربر."""
    w = get_wallet(user_id)
    count = 0
    for tx in w["transactions"]:
        if tx["status"] == "pending":
            tx["status"] = "approved"
            w["balance"] += tx["amount"]
            count += 1
    return count


def get_all_wallets():
    """برگرداندن همهٔ کیف‌های پول برای گزارش مالی."""
    result = []
    for uid, w in WALLETS.items():
        total_credit = sum(t["amount"] for t in w["transactions"])
        pending_credit = sum(t["amount"] for t in w["transactions"] if t["status"] == "pending")
        approved_credit = sum(t["amount"] for t in w["transactions"] if t["status"] == "approved")
        pending_count = sum(1 for t in w["transactions"] if t["status"] == "pending")
        result.append({
            "user_id": uid,
            "balance": w["balance"],
            "total_credit": total_credit,
            "pending_credit": pending_credit,
            "approved_credit": approved_credit,
            "pending_count": pending_count,
            "transaction_count": len(w["transactions"]),
            "transactions": w["transactions"][-10:],
        })
    return result


def get_all_pending():
    """برگرداندن همهٔ تراکنش‌های در انتظار تأیید."""
    result = []
    for uid, w in WALLETS.items():
        for i, t in enumerate(w["transactions"]):
            if t["status"] == "pending":
                result.append({**t, "user_id": uid, "tx_index": i})
    return result
