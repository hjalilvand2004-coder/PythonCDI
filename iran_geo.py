# -*- coding: utf-8 -*-
"""
داده‌های جغرافیایی ایران — ۳۱ استان + شهرها + مختصات lat/lng
"""

# ۳۱ استان با شهرهای مهم و مختصات واقعی (lat, lng)
PROVINCES = {
    "tehran": {"name": "تهران", "lat": 35.6892, "lng": 51.3890,
               "cities": ["تهران", "اسلام‌شهر", "شهریار", "ورامین", "پاکدشت", "رباط‌کریم", "پردیس", "شهرقدس", "ملارد", "قرچک"]},
    "alborz": {"name": "البرز", "lat": 35.8369, "lng": 50.9476,
               "cities": ["کرج", "نظرآباد", "اشتهرد", "هشتگرد", "فردیس", "محمدشهر", "ماهدشت", "طالقان"]},
    "isfahan": {"name": "اصفهان", "lat": 32.6539, "lng": 51.6660,
                "cities": ["اصفهان", "کاشان", "نجف‌آباد", "خمینی‌شهر", "شاهین‌شهر", "فولادشهر", "زرین‌شهر", "تیران", "گلپایگان", "نطنز"]},
    "fars": {"name": "فارس", "lat": 29.5918, "lng": 52.5837,
             "cities": ["شیراز", "مرودشت", "کازرون", "جهرم", "فسا", "داراب", "لار", "خرم‌بید", "ممسنی", "استهبان"]},
    "khuzestan": {"name": "خوزستان", "lat": 31.4804, "lng": 49.5000,
                  "cities": ["اهواز", "آبادان", "خرمشهر", "دزفول", "ماهشهر", "بهبهان", "اندیمشک", "شوشتر", "رامهرمز", "سوسنگرد"]},
    "east_azarbaijan": {"name": "آذربایجان شرقی", "lat": 38.0800, "lng": 46.2900,
                        "cities": ["تبریز", "مراغه", "اهر", "مرند", "بناب", "سراب", "جلفا", "خسروشهر", "بستان‌آباد", "ورزقان"]},
    "west_azarbaijan": {"name": "آذربایجان غربی", "lat": 37.5527, "lng": 45.0000,
                        "cities": ["ارومیه", "خوی", "میاندوآب", "مهاباد", "بوکان", "سلماس", "نقده", "اشنویه", "ماکو", "شاهین‌دژ"]},
    "gilan": {"name": "گیلان", "lat": 37.2800, "lng": 49.5900,
              "cities": ["رشت", "بندر انزلی", "لاهیجان", "آستارا", "صومعه‌سرا", "تالش", "لنگرود", "رودبار", "سیاهکل", "ماسوله"]},
    "mazandaran": {"name": "مازندران", "lat": 36.5000, "lng": 52.5000,
                   "cities": ["ساری", "بابل", "آمل", "قائم‌شهر", "نوشهر", "تنکابن", "سوادکوه", "بهشهر", "فریدون‌کنار", "جویبار"]},
    "golestan": {"name": "گلستان", "lat": 37.5000, "lng": 54.5000,
                 "cities": ["گرگان", "گنبد کاووس", "آق‌قلا", "بندر ترکمن", "علی‌آباد کتول", "کلاله", "مینودشت", "آزادشهر", "رامیان", "مراوه‌تپه"]},
    "khorasan_razavi": {"name": "خراسان رضوی", "lat": 36.3100, "lng": 59.5500,
                        "cities": ["مشهد", "نیشابور", "تربت حیدریه", "سبزوار", "قوچان", "کاشمر", "تربت جام", "فریمان", "شاندیز", "طرقبه"]},
    "khorasan_south": {"name": "خراسان جنوبی", "lat": 32.8700, "lng": 59.7500,
                       "cities": ["بیرجند", "قاین", "فردوس", "نهبندان", "سرایان", "طبس", "خوسف", "زیرکوه", "بشرویه", "سرمش"]},
    "khorasan_north": {"name": "خراسان شمالی", "lat": 37.4700, "lng": 57.1000,
                       "cities": ["بجنورد", "اسفراین", "شیروان", "آشخانه", "جاجرم", "گرمه", "راز و جرگلان", "کوکند", "لطف‌آباد", "تایباد"]},
    "kermanshah": {"name": "کرمانشاه", "lat": 34.3100, "lng": 47.0700,
                    "cities": ["کرمانشاه", "اسلام‌آباد", "هرسین", "صحنه", "کنگاور", "سنقر", "قصر شیرین", "گیلانغرب", "صاحب", "روانسر"]},
    "kurdistan": {"name": "کردستان", "lat": 35.5000, "lng": 47.0000,
                  "cities": ["سنندج", "سقز", "بانه", "مریوان", "قروه", "بیجار", "دیواندره", "کامیاران", "دهگلان", "شاهو"]},
    "hamedan": {"name": "همدان", "lat": 34.8000, "lng": 48.5100,
                "cities": ["همدان", "ملایر", "نهاوند", "تویسرکان", "اسدآباد", "بهار", "کبودرآهنگ", "رزن", "لالجین", "فامنین"]},
    "kerman": {"name": "کرمان", "lat": 30.2830, "lng": 57.0790,
               "cities": ["کرمان", "سیرجان", "رفسنجان", "جیرفت", "بم", "زرند", "بافت", "کهنوج", "شهر بابک", "عنبرآباد"]},
    "yazd": {"name": "یزد", "lat": 31.8970, "lng": 54.3530,
             "cities": ["یزد", "اردکان", "میبد", "بفق", "تفت", "ابرکوه", "مهریز", "اشکذر", "هرات", "خاتم"]},
    "sistan_baluchestan": {"name": "سیستان و بلوچستان", "lat": 27.2000, "lng": 60.7000,
                           "cities": ["زاهدان", "زابل", "چابهار", "ایرانشهر", "خاش", "سراوان", "نیکشهر", "کنارک", "زهد", "میرجاوه"]},
    "lorestan": {"name": "لرستان", "lat": 33.5000, "lng": 48.3500,
                 "cities": ["خرم‌آباد", "بروجرد", "دورود", "الیگودرز", "کوهدشت", "ازنا", "الشتر", "نورآباد", "چگنی", "دلفان"]},
    "ilam": {"name": "ایلام", "lat": 33.6400, "lng": 46.4000,
             "cities": ["ایلام", "دهلران", "آبدانان", "مهران", "ایوان", "ملکشاهی", "چرداول", "بدره", "هلیلان", "ارکواز"]},
    "chaharmahal_bakhtiari": {"name": "چهارمحال و بختیاری", "lat": 32.3200, "lng": 50.8500,
                               "cities": ["شهرکرد", "بروجن", "فارسان", "لردگان", "کوهرنگ", "اردل", "بن", "جونقان", "سامان", "فرادن"]},
    "kohgiluyeh_boyerahmad": {"name": "کهگیلویه و بویراحمد", "lat": 30.8500, "lng": 51.6000,
                              "cities": ["یاسوج", "گچساران", "دهدشت", "سی‌سخت", "چرام", "لنده", "باشت", "بهمئی", "دیشمک", "مادرسید"]},
    "bushehr": {"name": "بوشهر", "lat": 28.9700, "lng": 50.8300,
                "cities": ["بوشهر", "برازجان", "گناوه", "خارک", "دیلم", "تنگستان", "جم", "عسلویه", "کنگان", "ریز"]},
    "hormozgan": {"name": "هرمزگان", "lat": 27.1900, "lng": 56.2700,
                  "cities": ["بندرعباس", "میناب", "قشم", "بندر خمیر", "رودان", "بندر لنگه", "بستک", "جاسک", "بندر جاسک", "حاجی‌آباد"]},
    "markazi": {"name": "مرکزی", "lat": 34.0900, "lng": 49.7000,
                "cities": ["اراک", "ساوه", "خمین", "محلات", "دلیجان", "تفرش", "آشتیان", "شازند", "خنداب", "فرمهین"]},
    "qazvin": {"name": "قزوین", "lat": 36.2700, "lng": 50.0000,
               "cities": ["قزوین", "تاکستان", "آبیک", "بوئین‌زهرا", "الوند", "محمودآباد", "البرز", "رازجرد", "کوهین", "ضیاءآباد"]},
    "qom": {"name": "قم", "lat": 34.6400, "lng": 50.8700,
            "cities": ["قم", "قنوات", "کهک", "جعفریه", "سلفچگان", "کوه دشت", "قهرورد", "نوفل لوشاتو", "کهیر", "قمتش"]},
    "semnan": {"name": "سمنان", "lat": 35.5700, "lng": 53.3900,
               "cities": ["سمنان", "شاهرود", "دامغان", "گرمسار", "مهدی‌شهر", "ایوانکی", "سرخه", "میامی", "کلاته", "بسطام"]},
    "zanjan": {"name": "زنجان", "lat": 36.6700, "lng": 48.5000,
               "cities": ["زنجان", "ابهر", "خرم‌دره", "قیدار", "ماه‌نشان", "طارم", "سهرورد", "آب‌بر", "جلین", "حلب"]},
    "ardabil": {"name": "اردبیل", "lat": 38.2400, "lng": 48.2900,
                "cities": ["اردبیل", "پارس‌آباد", "مشکین‌شهر", "خلخال", "گرمی", "نمین", "سرعین", "بیله‌سوار", "کوثر", "اصلاندوز"]},
}


def get_province_choices():
    """برگرداندن گزینه‌های dropdown استان."""
    return [(key, info["name"]) for key, info in PROVINCES.items()]


# ═══════════════════════════════════════════════════════════
# نگاشت کد پستی → استان (بر اساس رقم اول کد پستی ۱۰ رقمی ایران)
# ═══════════════════════════════════════════════════════════
# کد پستی ایران ۱۰ رقمی است. رقم اول نشان‌دهنده منطقه/استان است.
# این نگاشت تقریبی است و برای پیش‌تکمیل فرم استفاده می‌شود.
POSTAL_PREFIX_TO_PROVINCE = {
    "1": ("tehran", "تهران"),
    "0": ("alborz", "البرز"),
    "3": ("isfahan", "اصفهان"),
    "4": ("fars", "فارس"),
    "5": ("khorasan_razavi", "خراسان رضوی"),
    "6": ("khuzestan", "خوزستان"),
    "7": ("east_azarbaijan", "آذربایجان شرقی"),
    "8": ("gilan", "گیلان"),
    "9": ("kerman", "کرمان"),
    "2": ("qom", "قم"),
}

# نگاشت دقیق‌تر بر اساس ۲ رقم اول (در صورت موجود بودن)
POSTAL_2DIGIT_TO_PROVINCE = {
    "11": ("tehran", "تهران"),
    "13": ("tehran", "تهران"),
    "14": ("tehran", "تهران"),
    "15": ("tehran", "تهران"),
    "16": ("tehran", "تهران"),
    "17": ("tehran", "تهران"),
    "18": ("tehran", "تهران"),
    "19": ("tehran", "تهران"),
    "31": ("isfahan", "اصفهان"),
    "33": ("chaharmahal", "چهارمحال و بختیاری"),
    "38": ("isfahan", "اصفهان"),
    "41": ("fars", "فارس"),
    "43": ("kohgiluyeh", "کهگیلویه و بویراحمد"),
    "51": ("khorasan_razavi", "خراسان رضوی"),
    "56": ("khorasan_south", "خراسان جنوبی"),
    "57": ("khorasan_north", "خراسان شمالی"),
    "61": ("khuzestan", "خوزستان"),
    "63": ("bushehr", "بوشهر"),
    "67": ("hormozgan", "هرمزگان"),
    "71": ("east_azarbaijan", "آذربایجان شرقی"),
    "73": ("west_azarbaijan", "آذربایجان غربی"),
    "75": ("kurdistan", "کردستان"),
    "77": ("zanjan", "زنجان"),
    "81": ("mazandaran", "مازندران"),
    "83": ("golestan", "گلستان"),
    "85": ("gilan", "گیلان"),
    "91": ("kerman", "کرمان"),
    "93": ("sistan", "سیستان و بلوچستان"),
    "95": ("yazd", "یزد"),
    "97": ("hormozgan", "هرمزگان"),
    "01": ("alborz", "البرز"),
    "02": ("qazvin", "قزوین"),
    "21": ("qom", "قم"),
    "22": ("qom", "قم"),
    "34": ("arak", "مرکزی"),
    "39": ("arak", "مرکزی"),
    "44": ("ilam", "ایلام"),
    "45": ("lorestan", "لرستان"),
    "46": ("chaharmahal", "چهارمحال و بختیاری"),
    "49": ("hamedan", "همدان"),
    "58": ("semnan", "سمنان"),
    "64": ("chaharmahal", "چهارمحال و بختیاری"),
    "66": ("bushehr", "بوشهر"),
    "68": ("kohgiluyeh", "کهگیلویه و بویراحمد"),
    "69": ("hormozgan", "هرمزگان"),
    "76": ("kermanshah", "کرمانشاه"),
    "78": ("hamedan", "همدان"),
    "84": ("golestan", "گلستان"),
    "86": ("ardabil", "اردبیل"),
    "88": ("mazandaran", "مازندران"),
    "96": ("yazd", "یزد"),
    "99": ("kerman", "کرمان"),
}

def detect_province_from_postal_code(postal_code):
    """تشخیص استان از کد پستی ۱۰ رقمی.
    خروجی: (province_key, province_name) یا None"""
    import re
    # نرمال‌سازی ارقام فارسی/عربی
    fa_to_en = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    pc = str(postal_code or "").strip().translate(fa_to_en)
    pc = re.sub(r"[^\d]", "", pc)
    if len(pc) < 1:
        return None
    # ابتدا با ۲ رقم دقیق
    if len(pc) >= 2:
        two = pc[:2]
        if two in POSTAL_2DIGIT_TO_PROVINCE:
            return POSTAL_2DIGIT_TO_PROVINCE[two]
    # سپس با ۱ رقم
    one = pc[0]
    if one in POSTAL_PREFIX_TO_PROVINCE:
        return POSTAL_PREFIX_TO_PROVINCE[one]
    return None


# ═══════════════════════════════════════════════════════════
# سرویس خط فقر منطقه‌ای — مرکز رصد فقر
# ═══════════════════════════════════════════════════════════
# خط فقر بر اساس:
# ۱) استان (هزینه زندگی متفاوت)
# ۲) تعداد اعضای خانوار (اقتصاد مقیاس — sqrt)
# ۳) ترکیب سنی (کودکان هزینه کمتری دارند)
# ۴) شهری/روستایی (هزینه مسکن متفاوت)
#
# مبانی محاسبه:
# - خط فقر مطلق سرانه ماهانه (تهران شهری): ~۳٬۵۰۰٬۰۰۰ تومان (مرجع: مرکز آمار ۱۴۰۴)
# - ضریب استان: نسبت هزینه زندگی استان به تهران
# - ضریب اقتصاد مقیاس: ۱ / sqrt(n) برای خانوارهای بزرگ‌تر
# - ضریب سن: کودکان (۰-۱۸) ۰٫۷، بزرگسالان (۱۸+) ۱٫۰
# - ضریب شهری/روستایی: شهری ۱٫۰، روستایی ۰٫۸
# ═══════════════════════════════════════════════════════════

# ضریب هزینه زندگی استان نسبت به تهران
PROVINCE_COST_INDEX = {
    "tehran": 1.00, "alborz": 0.92, "isfahan": 0.85, "fars": 0.80,
    "khuzestan": 0.82, "east_azarbaijan": 0.78, "west_azarbaijan": 0.75,
    "gilan": 0.83, "mazandaran": 0.80, "golestan": 0.72,
    "khorasan_razavi": 0.78, "khorasan_south": 0.70, "khorasan_north": 0.72,
    "kerman": 0.75, "yazd": 0.80, "semnan": 0.78,
    "qom": 0.88, "qazvin": 0.80, "zangan": 0.75,
    "kurdistan": 0.70, "ilam": 0.68, "lorestan": 0.70,
    "hamedan": 0.72, "chaharmahal": 0.73, "kohgiluyeh": 0.68,
    "bushehr": 0.78, "hormozgan": 0.80, "sistan": 0.65,
    "arak": 0.75, "ardabil": 0.70, "kermanshah": 0.72,
}

# خط فقر مطلق سرانه ماهانه (تومان) — مبنای تهران شهری
BASE_POVERTY_LINE_PER_CAPITA = 3_500_000

def calculate_poverty_line(province_key, members, urban=True):
    """
    محاسبه خط فقر منطقه‌ای بر اساس ترکیب خانوار.

    ورودی:
      province_key: کلید استان (مثلاً 'tehran')
      members: لیست اعضای خانوار [{age: 42}, {age: 38}, ...]
      urban: True برای شهری، False برای روستایی

    خروجی:
      {
        monthlyPerCapita: خط فقر سرانه ماهانه (تومان),
        householdTotal: خط فقر کل خانوار (تومان),
        province: نام استان,
        source: 'مرکز رصد فقر',
        validAsOf: تاریخ اعتبار,
        status: 'verified',
        details: جزئیات محاسبه,
        factors: ضرایب استفاده‌شده,
      }
    """
    import math

    # ۱) ضریب استان
    prov_cost = PROVINCE_COST_INDEX.get(province_key, 0.75)
    prov_name = PROVINCES.get(province_key, {}).get("name", "نامشخص")

    # ۲) ضریب شهری/روستایی
    urban_factor = 1.0 if urban else 0.80

    # ۳) ضریب اقتصاد مقیاس (OECD modified scale)
    # اولین بزرگسال: 1.0، سایر بزرگسالان: 0.5، کودکان: 0.3
    equivalent_size = 0.0
    adult_count = 0
    child_count = 0
    for m in members:
        age = m.get("age", 0) if isinstance(m, dict) else 0
        if age >= 18:
            adult_count += 1
            if adult_count == 1:
                equivalent_size += 1.0  # اولین بزرگسال
            else:
                equivalent_size += 0.5  # سایر بزرگسالان
        else:
            child_count += 1
            equivalent_size += 0.3  # کودکان

    if equivalent_size < 1.0:
        equivalent_size = 1.0  # حداقل ۱

    # ۴) محاسبه خط فقر سرانه
    base_per_capita = BASE_POVERTY_LINE_PER_CAPITA
    adjusted_per_capita = base_per_capita * prov_cost * urban_factor

    # ۵) خط فقر کل خانوار = سرانه × اندازه معادل
    household_total = adjusted_per_capita * equivalent_size

    # ۶) خط فقر سرانه واقعی (برای مقایسه با درآمد سرانه)
    actual_n = len(members) if members else 1
    actual_per_capita = household_total / max(actual_n, 1)

    # جزئیات محاسبه
    details = (
        f"خط فقر مطلق سرانه (تهران): {base_per_capita:,} تومان\n"
        f"ضریب استان ({prov_name}): {prov_cost:.2f}\n"
        f"ضریب {'شهری' if urban else 'روستایی'}: {urban_factor:.2f}\n"
        f"خط فقر سرانه منطقه‌ای: {adjusted_per_capita:,.0f} تومان\n"
        f"تعداد اعضا: {actual_n} ({adult_count} بزرگسال، {child_count} کودک)\n"
        f"اندازه معادل (OECD): {equivalent_size:.2f}\n"
        f"خط فقر کل خانوار: {household_total:,.0f} تومان\n"
        f"خط فقر سرانه واقعی: {actual_per_capita:,.0f} تومان"
    )

    factors = {
        "base_per_capita": base_per_capita,
        "province_cost_index": prov_cost,
        "urban_factor": urban_factor,
        "equivalent_size": round(equivalent_size, 2),
        "adult_count": adult_count,
        "child_count": child_count,
        "adjusted_per_capita": round(adjusted_per_capita),
        "household_total": round(household_total),
        "actual_per_capita": round(actual_per_capita),
    }

    return {
        "monthlyPerCapita": round(actual_per_capita),
        "householdTotal": round(household_total),
        "adjustedPerCapita": round(adjusted_per_capita),
        "province": prov_name,
        "provinceKey": province_key,
        "urban": urban,
        "source": "مرکز رصد فقر — مدل اقتصاد مقیاس OECD",
        "validAsOf": "1404/07",
        "status": "verified",
        "details": details,
        "factors": factors,
    }


def get_cities_for_province(province_key):
    """برگرداندن شهرهای یک استان."""
    info = PROVINCES.get(province_key)
    return info["cities"] if info else []


def get_province_name(province_key):
    """برگرداندن نام فارسی استان."""
    info = PROVINCES.get(province_key)
    return info["name"] if info else "نامشخص"


def get_province_coords(province_key):
    """برگرداندن مختصات lat/lng استان."""
    info = PROVINCES.get(province_key)
    if info:
        return (info["lat"], info["lng"])
    return (32.4279, 53.6880)  # مرکز ایران


def get_all_province_coords():
    """برگرداندن مختصات همهٔ استان‌ها برای نقشه."""
    return [
        {"key": k, "name": v["name"], "lat": v["lat"], "lng": v["lng"]}
        for k, v in PROVINCES.items()
    ]
