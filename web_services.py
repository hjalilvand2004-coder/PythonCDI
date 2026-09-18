# -*- coding: utf-8 -*-
"""
وب‌سرویس‌های فرضی برای واکشی داده‌های تکمیلی خانوار
سند مرجع: بند ۲ـ۲ EMMPI — قاعدهٔ اعتبارسنجی و تقدم منابع داده

این ماژول جایگاه واقعی وب‌سرویس‌ها را شبیه‌سازی می‌کند.
در استقرار واقعی، هر تابع به یک وب‌سرویس سازمانی متصل خواهد شد.
"""
import hashlib
from datetime import datetime


def _hash_id(national_id):
    """هش شناسهٔ ملی برای تولید دادهٔ قطعی و قابل تکرار."""
    return int(hashlib.md5(str(national_id).encode("utf-8")).hexdigest(), 16)


# ─────────────────────────────────────────────────────────
# داده‌های هویتی تستی (برای آزمایش سیستم)
# اگر کدملی یکی از این موارد باشد، داده‌های مشخص برمی‌گردد
# ─────────────────────────────────────────────────────────
TEST_IDENTITIES = {
    "1234567890": {
        "name": "علی محمدی", "dob": "1360/03/15",
        "spouse": "فاطمه محمدی", "children": 2,
        "location_default": "تهران، منطقهٔ ۸",
    },
    "9876543210": {
        "name": "حسن رضایی", "dob": "1355/11/20",
        "spouse": "زهرا رضایی", "children": 3,
        "location_default": "کرج، عظیمیه",
    },
    "1111111111": {
        "name": "محمد کریمی", "dob": "1368/05/10",
        "spouse": None, "children": 1,
        "location_default": "اصفهان، خیابان آماد",
    },
    "2222222222": {
        "name": "سحر احمدی", "dob": "1370/02/18",
        "spouse": None, "children": 0,
        "location_default": "تهران، شهرری",
    },
}


def _extract_last_name(name):
    """استخراج نام خانوادگی از نام کامل."""
    if not name:
        return "محمدی"
    parts = name.strip().split()
    return parts[-1] if len(parts) > 1 else name.strip()


def _generate_first_name(h, idx, is_male):
    """تولید نام کوچک قطعی بر اساس هش."""
    first_names_m = ["علی", "حسن", "حسین", "محمد", "رضا", "مهدی", "امیر", "سعید", "کیان", "آرش",
                     "یوسف", "ابراهیم", "موسی", "عمر", "زکریا"]
    first_names_f = ["فاطمه", "زهرا", "مریم", "نسیم", "سحر", "نگار", "هانیه", "الناز", "مهسا", "پریسا",
                     "خدیجه", "عائشه", "سمیه", "رقیه", "طاهره"]
    pool = first_names_m if is_male else first_names_f
    return pool[(h >> (idx * 3)) % len(pool)]


# ─────────────────────────────────────────────────────────
# وب‌سرویس ثبت‌احوال — اطلاعات هویتی و اعضای خانوار
# ─────────────────────────────────────────────────────────
def fetch_civil_registry(national_id, name=None, date_of_birth=None):
    """
    واکشی اطلاعات هویتی و ترکیب خانوار از ثبت‌احوال.
    اگر name ارائه شود، از آن به‌عنوان نام سرپرست استفاده می‌کند.
    اگر کدملی در TEST_IDENTITIES باشد، داده‌های مشخص برمی‌گردد.
    """
    h = _hash_id(national_id)

    # بررسی داده‌های تستی
    test = TEST_IDENTITIES.get(str(national_id))
    if test:
        head_name = test["name"]
        last_name = _extract_last_name(head_name)
        family_size = 1 + (1 if test["spouse"] else 0) + test["children"]
    else:
        # استفاده از نام واردشده در فرم
        if name and name.strip():
            head_name = name.strip()
            last_name = _extract_last_name(head_name)
        else:
            # تولید نام قطعی بر اساس هش
            last_names = ["محمدی", "حسینی", "رضایی", "کریمی", "احمدی", "موسوی", "صادقی"]
            first_names_m = ["علی", "حسن", "حسین", "محمد", "رضا", "مهدی", "امیر"]
            last_name = last_names[h % len(last_names)]
            head_name = f"{first_names_m[h % len(first_names_m)]} {last_name}"
        family_size = 3 + (h % 5)  # ۳ تا ۷ عضو

    members = [{
        "name": head_name,
        "national_id": str(national_id),
        "relationship": "سرپرست",
        "age": 30 + (h % 25),
        "gender": "مرد",
        "date_of_birth": date_of_birth or "—",
    }]

    # اضافه‌کردن همسر
    if test and test["spouse"]:
        members.append({
            "name": test["spouse"],
            "national_id": f"{national_id}-spouse",
            "relationship": "همسر",
            "age": 28 + (h % 20),
            "gender": "زن",
            "date_of_birth": "—",
        })
    elif family_size > 1:
        is_male_spouse = False
        first = _generate_first_name(h, 0, is_male_spouse)
        members.append({
            "name": f"{first} {last_name}",
            "national_id": f"{national_id}-spouse",
            "relationship": "همسر",
            "age": 28 + (h % 20),
            "gender": "زن",
            "date_of_birth": "—",
        })

    # اضافه‌کردن فرزندان
    num_children = test["children"] if test else max(0, family_size - 2)
    relationships = ["فرزند", "فرزند", "فرزند", "پدر", "مادر"]
    for i in range(num_children):
        is_male = ((h >> (i * 3 + 1)) % 2 == 0)
        first = _generate_first_name(h, i + 2, is_male)
        age = 3 + ((h >> (i * 4)) % 18)
        rel = "فرزند"
        members.append({
            "name": f"{first} {last_name}",
            "national_id": f"{national_id}-{i+2}",
            "relationship": rel,
            "age": age,
            "gender": "مرد" if is_male else "زن",
            "date_of_birth": "—",
        })

    return {
        "status": "success",
        "source": "ثبت‌احوال",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "verified": True,
        "data": {
            "head_name": head_name,
            "last_name": last_name,
            "family_size": len(members),
            "members": members,
            "marriage_status": "متأهل" if len(members) > 1 and any(m["relationship"] == "همسر" for m in members) else "مطلقه/فاقد همسر",
            "date_of_birth": date_of_birth or "—",
        }
    }


# ─────────────────────────────────────────────────────────
# وب‌سرویس بیمه — وضعیت بیمهٔ اعضای خانوار
# ─────────────────────────────────────────────────────────
def fetch_insurance(national_id, family_size=None):
    """واکشی وضعیت بیمهٔ درمان و تأمین‌اجتماعی."""
    h = _hash_id(national_id)
    if family_size is None:
        family_size = 3 + (h % 5)
    insurance_types = ["بیمه سلامت", "بیمه-basic", "بیمه تأمین‌اجتماعی", "بدون بیمه"]
    members_insurance = []
    for i in range(family_size):
        ins_type = insurance_types[(h >> (i * 2)) % 4]
        members_insurance.append({
            "member_idx": i,
            "insurance_type": ins_type,
            "is_covered": ins_type != "بدون بیمه",
            "expiry_date": f"140{(h % 3) + 3}/0{(h % 9) + 1}/15",
        })
    return {
        "status": "success",
        "source": "سامانه بیمه",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "data": {
            "total_covered": sum(1 for m in members_insurance if m["is_covered"]),
            "total_uncovered": sum(1 for m in members_insurance if not m["is_covered"]),
            "members": members_insurance,
        }
    }


# ─────────────────────────────────────────────────────────
# وب‌سرویس آموزش — وضعیت تحصیلی اعضای خانوار
# ─────────────────────────────────────────────────────────
def fetch_education(national_id, family_size=None, members=None):
    """واکشی وضعیت تحصیلی و ثبت‌نام در سیستم آموزش."""
    h = _hash_id(national_id)
    if family_size is None:
        family_size = 3 + (h % 5)
    members_edu = []
    edu_levels = ["ابتدایی", "متوسطه اول", "متوسطه دوم", "دیپلم", "کارشناسی", "بدون تحصیل", "حوزوی"]
    for i in range(family_size):
        # اگر سن عضو موجود است از آن استفاده کن
        age = 30 + (h % 25) if i == 0 else (3 + ((h >> (i * 4)) % 50))
        if members and i < len(members):
            age = members[i].get("age", age)
        if age < 7:
            status, level = "قبل از سن مدرسه", "—"
        elif age < 18:
            status = "در حال تحصیل" if (h >> i) % 3 != 0 else "ترک تحصیل"
            level = edu_levels[(age - 7) // 3] if age - 7 < len(edu_levels) * 3 else "متوسطه دوم"
        else:
            status = "فارغ‌التحصیل" if (h >> i) % 2 == 0 else "بدون تحصیل عالی"
            level = edu_levels[(h >> (i * 2)) % len(edu_levels)]
        members_edu.append({
            "member_idx": i,
            "age": age,
            "status": status,
            "level": level,
        })
    return {
        "status": "success",
        "source": "آموزش‌وپرورش",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "data": {"members": members_edu}
    }


# ─────────────────────────────────────────────────────────
# وب‌سرویس اشتغال — سوابق بیمه و اشتغال
# ─────────────────────────────────────────────────────────
def fetch_employment(national_id, family_size=None, members=None):
    """واکشی سوابق اشتغال و بیمهٔ تأمین‌اجتماعی."""
    h = _hash_id(national_id)
    work_statuses = ["شاغل", "بیکار", "گشت‌کار", "خویش‌فرما", "بازنشسته", "دانش‌آموخته"]
    if family_size is None:
        family_size = 3 + (h % 5)
    members_emp = []
    for i in range(family_size):
        age = 30 + (h % 25) if i == 0 else (3 + ((h >> (i * 4)) % 50))
        if members and i < len(members):
            age = members[i].get("age", age)
        if age < 15:
            status, sector, income = "زیر سن کار", "—", 0
        else:
            status = work_statuses[(h >> (i * 2)) % len(work_statuses)]
            sector = ["ساخت‌وساز", "خدمات", "کشاورزی", "صنعت", "بازرگانی", "—"][(h >> i) % 6]
            income = (h >> (i * 5)) % 30 * 1000000
        members_emp.append({
            "member_idx": i,
            "age": age,
            "status": status,
            "sector": sector,
            "monthly_income": income,
        })
    total_income = sum(m["monthly_income"] for m in members_emp)
    return {
        "status": "success",
        "source": "تأمین‌اجتماعی",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "data": {
            "members": members_emp,
            "total_monthly_income": total_income,
            "income_per_capita": total_income // max(family_size, 1),
        }
    }


# ─────────────────────────────────────────────────────────
# وب‌سرویس مسکن — وضعیت ملکی/اجاره‌ای
# ─────────────────────────────────────────────────────────
def fetch_housing(national_id):
    """واکشی وضعیت مسکن (ملکی/اجاره‌ای/فاقد)."""
    h = _hash_id(national_id)
    tenure_types = ["ملکی", "اجاره‌ای", "در منزل والدین", "رایگان", "اسکان غیررسمی"]
    tenure = tenure_types[h % len(tenure_types)]
    return {
        "status": "success",
        "source": "سامانه مسکن",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "data": {
            "tenure": tenure,
            "area_m2": 40 + (h % 80),
            "rooms": 1 + (h % 4),
            "monthly_rent_or_mortgage": (h % 15) * 1000000 if tenure == "اجاره‌ای" else 0,
            "has_utilities": (h % 7) != 0,
        }
    }


# ─────────────────────────────────────────────────────────
# تابع یکپارچه — واکشی همهٔ وب‌سرویس‌ها
# ─────────────────────────────────────────────────────────
def fetch_all_services(national_id, name=None, date_of_birth=None):
    """واکشی همهٔ داده‌های تکمیلی از تمام وب‌سرویس‌ها."""
    # ابتدا ثبت‌احوال برای دریافت اعضای خانوار
    civil = fetch_civil_registry(national_id, name=name, date_of_birth=date_of_birth)
    family_size = civil["data"]["family_size"]
    members = civil["data"]["members"]

    return {
        "civil_registry": civil,
        "insurance": fetch_insurance(national_id, family_size=family_size),
        "education": fetch_education(national_id, family_size=family_size, members=members),
        "employment": fetch_employment(national_id, family_size=family_size, members=members),
        "housing": fetch_housing(national_id),
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }


# ─────────────────────────────────────────────────────────
# منابع داده (بند ۲ـ۲ EM-MPI — قاعدهٔ تقدم منابع)
# ─────────────────────────────────────────────────────────
DATA_SOURCE_PRIORITIES = [
    {"priority": 1, "code": "S", "name": "داده‌های ثبتی و استعلام‌های مجاز",
     "services": ["ثبت‌احوال", "بیمه", "آموزش‌وپرورش", "تأمین‌اجتماعی", "مسکن"],
     "role": "تأیید اطلاعات پایه"},
    {"priority": 2, "code": "D", "name": "مدارک معتبر خانوار",
     "role": "گواهی پزشک، قرارداد اجاره، قبض"},
    {"priority": 3, "code": "H", "name": "خوداظهاری ساختاریافته",
     "role": "دریافت اطلاعات اولیه و شرایط جاری"},
    {"priority": 4, "code": "B", "name": "تماس، بازدید میدانی یا گزارش همیار",
     "role": "مشاهده و راستی‌آزمایی"},
    {"priority": 5, "code": "M", "name": "تأیید، اصلاح یا رد مددکار",
     "role": "اعمال قضاوت حرفه‌ای"},
]
