# -*- coding: utf-8 -*-
"""
موتور محاسبهٔ EM-MPI (Emdad Multidimensional Poverty Index)
سند مرجع: Emdad_sanadHemayt0004 — مدل بومی غربالگری و سطح‌بندی اولیه فقر چندبعدی

خلاصه:
- ۵ بُعد، ۳۵ شاخص، سقف امتیاز ۱۰۰۰
- هر شاخص در سه وضعیت: فاقد محرومیت (۰)، متوسط (۰٫۵)، شدید (۱)
- امتیاز شاخص = وزن × ضریب شدت
- ۹ پرچم قرمز مستقل از امتیاز
- ۸ مسیر ارجاع (پایش، بررسی تکمیلی، ارجاع عادی/اولویت‌دار/سریع به CDI، فوری، پیشگیرانه، راستی‌آزمایی)
- خط قرمز: هوش مصنوعی تصمیم‌یار است، نه تصمیم‌گیرنده
"""

# ═══════════════════════════════════════════════════════════
# ۵ بُعد EM-MPI (سقف امتیاز)
# ═══════════════════════════════════════════════════════════
DIMENSIONS = {
    "A": {"name": "سلامت و امنیت زیستی", "max": 250, "icon": "M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"},
    "B": {"name": "آموزش و رشد انسانی", "max": 200, "icon": "M22 10v6M2 10l10-5 10 5-10 5z M6 12v5c3 3 9 3 12 0v-5"},
    "C": {"name": "استاندارد زندگی و مسکن", "max": 300, "icon": "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10"},
    "D": {"name": "معیشت، اشتغال و درآمد", "max": 150, "icon": "M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"},
    "E": {"name": "آسیب‌پذیری و دسترسی به حمایت‌ها", "max": 100, "icon": "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"},
}

# ═══════════════════════════════════════════════════════════
# ۳۵ شاخص EM-MPI
# هر شاخص: weight (وزن)، dim (بُعد)، title، definition، red_flags (لیست کدهای پرچم)
# ═══════════════════════════════════════════════════════════
INDICATORS = {
    # ─── بُعد A: سلامت و امنیت زیستی (سقف ۲۵۰) ───
    "A1": {"dim": "A", "weight": 35, "title": "بیماری مزمن یا جدی مؤثر بر عملکرد و معیشت",
           "definition": "وجود عضو دارای بیماری مزمن، خاص یا صعب‌العلاج که موجب کاهش توان فعالیت روزمره، کار، تحصیل یا افزایش مستمر هزینه خانوار شده باشد.",
           "red_flags": ["R2"]},
    "A2": {"dim": "A", "weight": 35, "title": "ناتوانی یا معلولیت مؤثر و نیاز به توان‌بخشی",
           "definition": "وجود محدودیت عملکردی پایدار در حرکت، مراقبت شخصی، ارتباط، یادگیری یا اشتغال که نیازمند کمک، وسیله کمکی، مراقبت یا توان‌بخشی باشد.",
           "red_flags": ["R6"]},
    "A3": {"dim": "A", "weight": 50, "title": "نیاز درمانی یا توان‌بخشی ضروری تأمین‌نشده",
           "definition": "نیاز به درمان، دارو، جراحی، بستری، آزمایش، توان‌بخشی یا تجهیزات پزشکی که تأیید شده اما به علت هزینه، دسترسی یا تأخیر، انجام نشده یا ناقص مانده است.",
           "red_flags": ["R2"]},
    "A4": {"dim": "A", "weight": 35, "title": "فشار مالی درمان بر خانوار",
           "definition": "نسبت هزینه درمان، دارو، مراقبت و رفت‌وآمد درمانی به درآمد قابل‌دسترس خانوار در سه ماه اخیر؛ یا شواهد بدهی، فروش دارایی یا حذف نیازهای اساسی به علت درمان.",
           "red_flags": []},
    "A5": {"dim": "A", "weight": 20, "title": "پوشش مؤثر بیمه و دسترسی عملی به خدمات درمانی",
           "definition": "برخورداری واقعی اعضای نیازمند از بیمه پایه یا پوشش قابل استفاده؛ با لحاظ اعتبار بیمه، فرانشیز، فاصله، نوبت‌دهی و امکان بهره‌برداری واقعی.",
           "red_flags": []},
    "A6": {"dim": "A", "weight": 45, "title": "ناامنی غذایی خانوار",
           "definition": "سنجش وضعیت ۳۰ روز گذشته: نگرانی از تمام‌شدن غذا، کاهش کیفیت یا تنوع، حذف وعده، کاهش مقدار غذا، گرسنگی یا ناتوانی در تأمین غذای کافی.",
           "red_flags": ["R3"]},
    "A7": {"dim": "A", "weight": 30, "title": "اختلال سلامت روان یا اعتیاد مختل‌کننده عملکرد",
           "definition": "وجود اختلال روانی تأییدشده، علائم شدید پایدار یا مصرف مواد که عملکرد خانوار در امنیت، مراقبت، اشتغال، تحصیل یا روابط خانوادگی را مختل کرده است.",
           "red_flags": ["R5"]},

    # ─── بُعد B: آموزش و رشد انسانی (سقف ۲۰۰) ───
    "B1": {"dim": "B", "weight": 50, "title": "بازماندگی یا ترک تحصیل کودک و نوجوان",
           "definition": "وجود کودک یا نوجوان در سن آموزش اجباری که ثبت‌نام نشده، ترک تحصیل کرده یا به‌طور پایدار از آموزش رسمی خارج است.",
           "red_flags": ["R4"]},
    "B2": {"dim": "B", "weight": 25, "title": "خطر جدی ترک تحصیل",
           "definition": "غیبت غیرموجه مکرر، افت تحصیلی شدید، ناتوانی مالی برای هزینه ضروری، کار کودک، مراقبت اجباری از اعضای خانواده یا مشکلات خانوادگی مؤثر بر استمرار تحصیل.",
           "red_flags": ["R4"]},
    "B3": {"dim": "B", "weight": 20, "title": "محرومیت از سواد کارکردی در بزرگسال مسئول",
           "definition": "ناتوانی فرد مسئول امور خانوار در خواندن، نوشتن یا انجام امور پایه مانند تکمیل فرم، پیگیری خدمات، خواندن پیامک یا دستورالعمل درمانی.",
           "red_flags": []},
    "B4": {"dim": "B", "weight": 20, "title": "دسترسی عملی به آموزش مناسب",
           "definition": "امکان واقعی ثبت‌نام، حضور مستمر و دسترسی به مدرسه یا برنامه آموزشی مناسب با لحاظ فاصله، حمل‌ونقل، هزینه، معلولیت، مدارک هویتی و ظرفیت آموزشی.",
           "red_flags": []},
    "B5": {"dim": "B", "weight": 15, "title": "دسترسی به ابزار ضروری آموزش دیجیتال",
           "definition": "برخورداری از حداقل ابزار و اتصال لازم برای تکلیف، ارتباط با مدرسه یا آموزش دیجیتال، مشروط به اینکه برنامه آموزشی واقعاً به آن نیاز داشته باشد.",
           "red_flags": []},
    "B6": {"dim": "B", "weight": 30, "title": "نیاز آموزشی ویژه بدون خدمت متناسب",
           "definition": "وجود کودک یا نوجوان دارای معلولیت، اختلال یادگیری، نیاز ارتباطی، بیماری یا وضعیت خاص که به حمایت آموزشی نیاز دارد ولی خدمت مناسب دریافت نمی‌کند.",
           "red_flags": ["R4"]},
    "B7": {"dim": "B", "weight": 40, "title": "فقدان مسیر مهارت‌آموزی یا آمادگی اشتغال",
           "definition": "وجود نوجوان بزرگ‌تر، جوان یا بزرگسال آماده اشتغال که فاقد مهارت قابل عرضه، گواهی مهارتی، ابزار اولیه یا دسترسی به دوره مناسب است.",
           "red_flags": []},

    # ─── بُعد C: استاندارد زندگی و مسکن (سقف ۳۰۰) ───
    "C1": {"dim": "C", "weight": 60, "title": "بی‌خانمانی، سکونت اضطراری یا خطر فوری تخلیه",
           "definition": "بی‌سرپناهی، سکونت در خودرو یا فضای عمومی، سکونت اضطراری ناایمن، یا وجود اخطار معتبر تخلیه و خطر قریب‌الوقوع از دست دادن محل سکونت.",
           "red_flags": ["R1", "R9"]},
    "C2": {"dim": "C", "weight": 45, "title": "ایمنی سازه و کفایت فیزیکی مسکن",
           "definition": "وجود خطرهایی مانند فرسودگی شدید، سقف یا دیوار ناایمن، رطوبت گسترده، خطر برق‌گرفتگی، فقدان حفاظت در برابر سرما یا گرما، یا فضای غیرقابل سکونت.",
           "red_flags": []},
    "C3": {"dim": "C", "weight": 35, "title": "امنیت تصرف و پایداری سکونت",
           "definition": "بررسی ثبات حق سکونت، شامل اجاره بدون قرارداد، سکونت وابسته به بستگان، سکونت رایگان ناپایدار، دعوای مالکیت یا ناتوانی در تمدید قرارداد.",
           "red_flags": ["R1", "R8"]},
    "C4": {"dim": "C", "weight": 25, "title": "تراکم شدید سکونت",
           "definition": "نسبت تعداد اعضای خانوار به اتاق‌های قابل سکونت، با لحاظ سن، جنسیت، معلولیت و امکان خواب مناسب.",
           "red_flags": []},
    "C5": {"dim": "C", "weight": 30, "title": "دسترسی پایدار به آب، برق، گاز یا سوخت ایمن",
           "definition": "وجود و تداوم دسترسی به آب سالم، برق و سامانه گرمایش یا پخت‌وپز ایمن؛ قطع ناشی از بدهی یا نبود زیرساخت نیز بررسی می‌شود.",
           "red_flags": ["R7"]},
    "C6": {"dim": "C", "weight": 20, "title": "سرویس بهداشتی، حمام و بهداشت محیط",
           "definition": "دسترسی خانوار به سرویس بهداشتی قابل استفاده، حمام، دفع مناسب فاضلاب و محیط عاری از آلودگی یا خطر بهداشتی جدی.",
           "red_flags": []},
    "C7": {"dim": "C", "weight": 25, "title": "فقدان وسایل ضروری زندگی",
           "definition": "فقدان وسایل ضروری متناسب با شرایط خانوار مانند محل خواب ایمن، وسیله پخت‌وپز، یخچال یا امکان نگهداری ایمن غذا، گرمایش یا سرمایش ضروری.",
           "red_flags": []},
    "C8": {"dim": "C", "weight": 35, "title": "فشار هزینه مسکن",
           "definition": "نسبت هزینه ماهانه مسکن شامل اجاره، اقساط ضروری، شارژ و قبوض اصلی به درآمد قابل‌دسترس خانوار، پس از کسر هزینه ضروری درمان.",
           "red_flags": ["R1", "R9"]},
    "C9": {"dim": "C", "weight": 25, "title": "دسترسی فیزیکی به خدمات پایه ضروری",
           "definition": "امکان واقعی دسترسی خانوار به درمان، مدرسه، حمل‌ونقل، فروشگاه مواد غذایی یا خدمت حمایتی؛ محل سکونت به‌تنهایی معیار محرومیت نیست.",
           "red_flags": []},

    # ─── بُعد D: معیشت، اشتغال و درآمد (سقف ۱۵۰) ───
    "D1": {"dim": "D", "weight": 30, "title": "فقدان اشتغال یا درآمد فعال در فرد اصلی تأمین‌کننده",
           "definition": "فرد اصلی تأمین‌کننده درآمد خانوار، با وجود توان و آمادگی کار، فاقد شغل، درآمد فعال یا مسیر مؤثر کاریابی است.",
           "red_flags": []},
    "D2": {"dim": "D", "weight": 15, "title": "بیکاری یا بلااستفاده‌ماندن ظرفیت کار در اعضای توانمند",
           "definition": "تعداد اعضای بزرگسال توانمند و آماده کار که بیکارند یا به دلیل نبود فرصت، مهارت یا مانع دسترسی، خارج از بازار کار مانده‌اند.",
           "red_flags": []},
    "D3": {"dim": "D", "weight": 25, "title": "ناپایداری اشتغال یا درآمد",
           "definition": "وابستگی خانوار به کار روزمزدی، فصلی، غیررسمی، پروژه‌ای یا درآمدی که در شش ماه گذشته نوسان شدید داشته و برنامه‌ریزی برای نیازهای پایه را مختل کرده است.",
           "red_flags": ["R9"]},
    "D4": {"dim": "D", "weight": 45, "title": "ناکافی‌بودن درآمد قابل‌دسترس برای نیازهای اساسی",
           "definition": "محاسبه درآمد قابل‌دسترس پس از کسر هزینه‌های اجتناب‌ناپذیر مسکن، درمان، بدهی ضروری و نگهداری افراد وابسته؛ سپس مقایسه با خط نیاز پایه منطقه‌ای.",
           "red_flags": []},
    "D5": {"dim": "D", "weight": 20, "title": "بدهی بحرانی یا شوک اقتصادی مؤثر بر معیشت",
           "definition": "وجود بدهی معوق، هزینه ناگهانی سنگین، از دست‌دادن درآمد، خسارت حادثه یا تعهد مالی ضروری که تأمین نیازهای پایه خانوار را مختل کرده است.",
           "red_flags": ["R9"]},
    "D6": {"dim": "D", "weight": 15, "title": "فقدان مهارت، ابزار یا سرمایه حداقلی برای ورود به کار",
           "definition": "فرد آماده کار با مانع مشخصی مانند فقدان مهارت قابل عرضه، ابزار کار، گواهی لازم، هزینه رفت‌وآمد اولیه یا سرمایه بسیار محدود مواجه است.",
           "red_flags": []},

    # ─── بُعد E: آسیب‌پذیری و دسترسی به حمایت‌ها (سقف ۱۰۰) ───
    "E1": {"dim": "E", "weight": 20, "title": "فقدان ظرفیت مؤثر تأمین معاش در خانوار",
           "definition": "خانوار فاقد فرد دارای توان، امکان یا درآمد مؤثر برای تأمین معاش است؛ مانند سالمندی همراه با ناتوانی، ازکارافتادگی، بیماری جدی، زندانی‌بودن سرپرست.",
           "red_flags": ["R6"]},
    "E2": {"dim": "E", "weight": 20, "title": "بار مراقبتی سنگین و فاقد پشتیبانی",
           "definition": "وجود کودک خردسال، سالمند، بیمار یا فرد دارای معلولیت نیازمند مراقبت مستمر که زمان و امکان اشتغال، تحصیل یا پیگیری خدمات اعضای خانوار را محدود می‌کند.",
           "red_flags": ["R6"]},
    "E3": {"dim": "E", "weight": 15, "title": "فقدان شبکه حمایت خانوادگی، اجتماعی یا محلی",
           "definition": "نبود فرد، گروه یا نهاد قابل اتکا برای کمک اضطراری، مراقبت موقت، پیگیری درمان، حمایت روانی یا اتصال خانوار به خدمات.",
           "red_flags": ["R5", "R6"]},
    "E4": {"dim": "E", "weight": 15, "title": "مانع حقوقی، هویتی یا اداری مؤثر بر دسترسی",
           "definition": "فقدان یا مشکل اسناد هویتی، وضعیت حقوقی، اختلافات مؤثر، نبود دسترسی به حساب یا مدارک، یا موانع اداری که دریافت خدمات را مسدود کرده است.",
           "red_flags": ["R8"]},
    "E5": {"dim": "E", "weight": 15, "title": "عدم دسترسی مؤثر به حمایت‌ها و خدمات واجد شرایط",
           "definition": "خانوار با وجود نیاز روشن یا واجد شرایط‌بودن، به علت ناآگاهی، هزینه، فاصله، ناتوانی در پیگیری، نبود ظرفیت یا انقطاع ارتباط، از خدمات ضروری محروم مانده است.",
           "red_flags": []},
    "E6": {"dim": "E", "weight": 15, "title": "ریسک بالای تشدید محرومیت در آینده",
           "definition": "وجود دست‌کم دو عامل پیش‌نگر، مانند درآمد بسیار ناپایدار، بدهی رو به افزایش، بیماری پرهزینه، پایان قریب‌الوقوع قرارداد مسکن، نبود حمایت، احتمال بیکاری.",
           "red_flags": ["R9"]},
}

# ═══════════════════════════════════════════════════════════
# ۹ پرچم قرمز
# ═══════════════════════════════════════════════════════════
RED_FLAGS = {
    "R1": {"title": "خطر فوری بی‌خانمانی یا تخلیه", "sources": ["C1", "C3", "C8"],
           "action": "ارجاع فوری — مستقل از امتیاز EM-MPI"},
    "R2": {"title": "بیماری حیاتی یا نیاز درمانی فوری", "sources": ["A1", "A3"],
           "action": "ارجاع فوری — مستقل از امتیاز EM-MPI"},
    "R3": {"title": "فقدان غذا یا سوءتغذیه شدید", "sources": ["A6"],
           "action": "رسیدگی فوری و ارجاع"},
    "R4": {"title": "کودک در معرض آسیب یا ترک تحصیل بحرانی", "sources": ["B1", "B2", "B6"],
           "action": "بررسی تخصصی و فوری"},
    "R5": {"title": "خشونت خانوادگی یا تهدید امنیتی", "sources": ["A7", "E3"],
           "action": "محدودسازی دسترسی و ارجاع تخصصی فوری"},
    "R6": {"title": "سالمند، بیمار یا فرد دارای معلولیت بدون مراقب", "sources": ["A2", "E2", "E3"],
           "action": "بازدید و رسیدگی فوری"},
    "R7": {"title": "قطع خدمات حیاتی در شرایط بحرانی", "sources": ["C5"],
           "action": "رسیدگی سریع"},
    "R8": {"title": "بحران حقوقی مؤثر بر امنیت یا سکونت خانوار", "sources": ["E4", "C3"],
           "action": "ارجاع حقوقی یا مددکاری فوری"},
    "R9": {"title": "احتمال قریب‌الوقوع از دست‌دادن درآمد اصلی یا مسکن", "sources": ["D3", "D5", "C1", "C8", "E6"],
           "action": "ارجاع پیشگیرانه یا فوری، حسب شدت"},
}

# ═══════════════════════════════════════════════════════════
# ۵ سطح محرومیت
# ═══════════════════════════════════════════════════════════
DEPRIVATION_LEVELS = [
    {"code": "L0", "min": 0, "max": 149, "name": "محرومیت محدود",
     "approach": "پایش یا رسیدگی متناسب", "color": "P4"},
    {"code": "L1", "min": 150, "max": 299, "name": "محرومیت خفیف",
     "approach": "بررسی تکمیلی و حمایت متناسب", "color": "P3"},
    {"code": "L2", "min": 300, "max": 449, "name": "محرومیت متوسط",
     "approach": "ارجاع عادی به CDI و طراحی حمایت هدفمند", "color": "P2"},
    {"code": "L3", "min": 450, "max": 599, "name": "محرومیت زیاد",
     "approach": "ارجاع اولویت‌دار به CDI، بررسی میدانی و برنامه مداخله چندبخشی", "color": "P1"},
    {"code": "L4", "min": 600, "max": 1000, "name": "محرومیت بسیار زیاد",
     "approach": "ارجاع سریع به CDI و بررسی مداخله چندبخشی", "color": "P0"},
]

# ═══════════════════════════════════════════════════════════
# ۸ مسیر ارجاع
# ═══════════════════════════════════════════════════════════
REFERRAL_PATHS = {
    "P1": {"name": "پایش و خدمت عمومی", "condition": "امتیاز ۰-۱۴۹، بدون پرچم قرمز",
           "action": "ثبت اطلاعات، اطلاع‌رسانی، اتصال به خدمات عمومی و پایش دوره‌ای", "to_cdi": False, "color": "P4"},
    "P2": {"name": "بررسی تکمیلی محدود", "condition": "امتیاز ۱۵۰-۲۹۹ و بدون فوریت",
           "action": "تکمیل مدارک، تماس یا بررسی محدود و معرفی به خدمت متناسب", "to_cdi": False, "color": "P3"},
    "P3": {"name": "ارجاع عادی به CDI", "condition": "امتیاز ۳۰۰-۴۴۹",
           "action": "ارجاع عادی به CDI و طراحی حمایت هدفمند", "to_cdi": True, "color": "P2"},
    "P4": {"name": "ارجاع اولویت‌دار به CDI", "condition": "امتیاز ۴۵۰-۵۹۹",
           "action": "ارجاع اولویت‌دار، بررسی میدانی و برنامه مداخله چندبخشی", "to_cdi": True, "color": "P1"},
    "P5": {"name": "ارجاع سریع و چندبخشی", "condition": "امتیاز ۶۰۰-۱۰۰۰",
           "action": "ارزیابی سریع CDI، تعیین مددکار و مداخله چندبخشی", "to_cdi": True, "color": "P0"},
    "P6": {"name": "ارجاع فوری مستقل از امتیاز", "condition": "وجود پرچم قرمز معتبر",
           "action": "رسیدگی اضطراری، ارجاع فوری به مددکار و CDI؛ بدون انتظار برای تکمیل امتیاز", "to_cdi": True, "color": "P0"},
    "P7": {"name": "ارجاع پیشگیرانه", "condition": "E6 در سطح شدید یا تشخیص حرفه‌ای مددکار",
           "action": "بررسی تکمیلی یا ارجاع پیشگیرانه به CDI پیش از وقوع بحران", "to_cdi": True, "color": "P1"},
    "P8": {"name": "راستی‌آزمایی داده", "condition": "تناقض خوداظهاری، مدارک، داده ثبتی یا گزارش میدانی",
           "action": "توقف تصمیم خودکار، درخواست مدرک یا بازدید محدود؛ تأیید یا اصلاح توسط مددکار", "to_cdi": False, "color": "P2"},
}

# ═══════════════════════════════════════════════════════════
# منابع اطلاعات (اولویت)
# ═══════════════════════════════════════════════════════════
DATA_SOURCES = {
    1: {"code": "S", "name": "داده‌های ثبتی و استعلام‌های مجاز", "role": "تأیید اطلاعات پایه"},
    2: {"code": "D", "name": "مدارک معتبر خانوار", "role": "گواهی، قرارداد، قبض، اخطار"},
    3: {"code": "H", "name": "خوداظهاری ساختاریافته خانوار", "role": "دریافت اطلاعات اولیه"},
    4: {"code": "B", "name": "تماس، بازدید میدانی یا گزارش همیار", "role": "مشاهده و راستی‌آزمایی"},
    5: {"code": "M", "name": "تأیید، اصلاح یا رد مددکار", "role": "اعمال قضاوت حرفه‌ای"},
}

# ═══════════════════════════════════════════════════════════
# خط قرمزهای هوش مصنوعی (بند ۱۴)
# ═══════════════════════════════════════════════════════════
AI_RED_LINES = [
    "هیچ‌یک از امتیازها، شاخص‌ها، هشدارها یا پیشنهادها به‌تنهایی مبنای پذیرش، رد، حذف یا تعیین قطعی حمایت خانوار نیست.",
    "تصمیم نهایی باید انسانی، مستند، قابل توضیح، قابل اعتراض و قابل بازنگری باشد.",
    "هوش مصنوعی در EM-MPI تصمیم‌گیرنده نهایی نیست؛ بلکه تصمیم‌یار، تحلیل‌گر، هشداردهنده و تسهیل‌کننده است.",
    "پرچم قرمز با امتیاز پایین EM-MPI خنثی نمی‌شود؛ مسیر ارجاع فوری مستقل دارد.",
    "ویژگی‌هایی مانند قومیت، مذهب، زبان، محل سکونت به‌تنهایی، تعداد فرزندان به‌تنهایی یا جنسیت به‌عنوان معیار مستقل محرومیت نیستند.",
    "فقط داده‌های ضروری برای غربالگری، ارجاع، مداخله و پایش باید جمع‌آوری و پردازش شوند (حداقل‌گرایی داده).",
    "دسترسی همیاران مددکار باید محدود به پرونده‌های تخصیص‌یافته و فقط اطلاعات لازم برای مأموریت نمایش داده شود.",
]


# ═══════════════════════════════════════════════════════════
# موتور محاسبه
# ═══════════════════════════════════════════════════════════
SEVERITY_OPTIONS = [
    {"value": 0, "label": "فاقد محرومیت", "desc": "بیماری/مسئله‌ای مؤثر وجود ندارد یا کنترل‌شده است", "color": "P3"},
    {"value": 0.5, "label": "محرومیت متوسط", "desc": "مشکل وجود دارد ولی قابل مدیریت است", "color": "P1"},
    {"value": 1, "label": "محرومیت شدید", "desc": "اختلال جدی در معیشت و زندگی روزمره", "color": "P0"},
]


def compute_emmpi(indicators_data):
    """
    محاسبهٔ کامل EM-MPI.

    ورودی: indicators_data = {"A1": 0.5, "A2": 1, ...}
    خروجی: dict با score, dimension_scores, level, red_flags, referral_path, ...
    """
    # محاسبهٔ امتیاز هر شاخص
    indicator_scores = {}
    for code, severity in indicators_data.items():
        if code not in INDICATORS:
            continue
        weight = INDICATORS[code]["weight"]
        score = weight * severity
        indicator_scores[code] = {
            "weight": weight,
            "severity": severity,
            "score": score,
            "dim": INDICATORS[code]["dim"],
            "title": INDICATORS[code]["title"],
        }

    # محاسبهٔ امتیاز هر بُعد
    dimension_scores = {}
    for dim_key, dim_info in DIMENSIONS.items():
        dim_score = sum(
            isc["score"] for code, isc in indicator_scores.items()
            if isc["dim"] == dim_key
        )
        dimension_scores[dim_key] = {
            "name": dim_info["name"],
            "score": dim_score,
            "max": dim_info["max"],
            "pct": round(dim_score / dim_info["max"] * 100, 1) if dim_info["max"] else 0,
        }

    # امتیاز کل
    total_score = sum(d["score"] for d in dimension_scores.values())

    # تعیین سطح محرومیت
    level = None
    for lvl in DEPRIVATION_LEVELS:
        if lvl["min"] <= total_score <= lvl["max"]:
            level = lvl
            break

    # تشخیص پرچم‌های قرمز
    active_red_flags = []
    for rf_code, rf_info in RED_FLAGS.items():
        # اگر هر شاخص منبع پرچم در سطح شدید (۱) باشد، پرچم فعال می‌شود
        triggered = any(
            indicators_data.get(src) == 1
            for src in rf_info["sources"]
            if src in indicators_data
        )
        if triggered:
            active_red_flags.append({
                "code": rf_code,
                "title": rf_info["title"],
                "sources": rf_info["sources"],
                "action": rf_info["action"],
                "triggered_by": [s for s in rf_info["sources"] if indicators_data.get(s) == 1],
            })

    # تعیین مسیر ارجاع
    referral_path = None
    if active_red_flags:
        referral_path = REFERRAL_PATHS["P6"]  # ارجاع فوری
        referral_path_code = "P6"
    elif total_score >= 600:
        referral_path = REFERRAL_PATHS["P5"]
        referral_path_code = "P5"
    elif total_score >= 450:
        referral_path = REFERRAL_PATHS["P4"]
        referral_path_code = "P4"
    elif total_score >= 300:
        referral_path = REFERRAL_PATHS["P3"]
        referral_path_code = "P3"
    elif total_score >= 150:
        referral_path = REFERRAL_PATHS["P2"]
        referral_path_code = "P2"
    else:
        referral_path = REFERRAL_PATHS["P1"]
        referral_path_code = "P1"

    # بررسی مسیر پیشگیرانه (E6 شدید)
    if indicators_data.get("E6") == 1 and referral_path_code not in ("P5", "P6"):
        referral_path = REFERRAL_PATHS["P7"]
        referral_path_code = "P7"

    # ابعاد غالب (۳ بُعد با بالاترین درصد)
    dims_by_pct = sorted(
        [(k, v) for k, v in dimension_scores.items()],
        key=lambda x: x[1]["pct"], reverse=True
    )
    dominant_dims = [{"code": k, **v} for k, v in dims_by_pct[:3]]

    # شاخص‌های مؤثر (با امتیاز > 0)
    effective_indicators = sorted(
        [{"code": code, **isc} for code, isc in indicator_scores.items() if isc["score"] > 0],
        key=lambda x: x["score"], reverse=True
    )

    return {
        "score": total_score,
        "max_score": 1000,
        "score_pct": round(total_score / 10, 1),
        "dimension_scores": dimension_scores,
        "indicator_scores": indicator_scores,
        "effective_indicators": effective_indicators,
        "level": level,
        "red_flags": active_red_flags,
        "referral_path": referral_path,
        "referral_path_code": referral_path_code,
        "dominant_dims": dominant_dims,
        "needs_cdi": referral_path["to_cdi"] if referral_path else False,
        "is_recommendation": True,  # خط قرمز: پیشنهاد سامانه است
    }


def suggest_assistant(emmpi_result, household_location=None):
    """
    پیشنهاد هوشمند مددکار یا همیار متناسب با پرونده.
    (نسخهٔ اولیه — مبتنی بر قواعد ساده)
    """
    if not emmpi_result or not emmpi_result.get("red_flags"):
        return None

    suggestions = []
    for rf in emmpi_result["red_flags"]:
        if rf["code"] in ("R5",):  # خشونت
            suggestions.append({
                "role": "worker",
                "label": "مددکار خانواده + متخصص حفاظت",
                "reason": f"پرچم {rf['code']} — فقط مددکار رسمی مجاز است",
                "priority": "فوری",
            })
        elif rf["code"] in ("R2",):  # بیماری حیاتی
            suggestions.append({
                "role": "worker",
                "label": "مددکار خانواده + متخصص درمان",
                "reason": f"پرچم {rf['code']} — نیاز به ارزیابی درمانی فوری",
                "priority": "فوری",
            })
        elif rf["code"] in ("R4",):  # کودک
            suggestions.append({
                "role": "rose",
                "label": "کلینیک رز + مددکار کودک",
                "reason": f"پرچم {rf['code']} — نیاز به مشاوره کودک",
                "priority": "اولویت‌دار",
            })
        elif rf["code"] in ("R6",):  # سالمند/معلول بدون مراقب
            suggestions.append({
                "role": "assistant",
                "label": "همیار مددکار آموزش‌دیده",
                "reason": f"پرچم {rf['code']} — نیاز به بازدید میدانی",
                "priority": "اولویت‌دار",
            })

    return suggestions if suggestions else None


def get_indicator_list_by_dim():
    """گروه‌بندی شاخص‌ها بر اساس بُعد — برای فرم ورودی."""
    by_dim = {}
    for code, info in INDICATORS.items():
        dim = info["dim"]
        if dim not in by_dim:
            by_dim[dim] = []
        by_dim[dim].append({"code": code, **info})
    return by_dim


# ═══════════════════════════════════════════════════════════
# سیستم تخصیص هوشمند همیاران مددکار (مانند اسنپ)
# بند ۹ — انتخاب هوشمند مددکار یا همیار مددکار
# ═══════════════════════════════════════════════════════════

# ۷ نوع نقش قابل واگذاری به همیار (بند ۸ـ۳)
ASSISTANT_ROLES = [
    {"code": "info", "name": "تکمیل اطلاعات اولیه", "icon": "📝",
     "desc": "تماس، دریافت مدارک، تکمیل پرسش‌نامه"},
    {"code": "field", "name": "راستی‌آزمایی میدانی", "icon": "🔍",
     "desc": "بازدید محدود و ثبت وضعیت واقعی خانوار"},
    {"code": "support", "name": "پیگیری حمایتی", "icon": "🤝",
     "desc": "ارتباط با منابع محلی و خدمات موجود"},
    {"code": "specialist", "name": "بررسی تخصصی", "icon": "⚕️",
     "desc": "ارجاع به سلامت، اشتغال، آموزش، مسکن یا توان‌بخشی"},
    {"code": "social", "name": "همراهی اجتماعی", "icon": "💙",
     "desc": "راهنمایی، پیگیری خدمات و کاهش انقطاع ارتباط"},
    {"code": "monitor", "name": "پایش پس از مداخله", "icon": "📊",
     "desc": "بررسی تغییر وضعیت و ثبت گزارش دوره‌ای"},
    {"code": "facilitator", "name": "تسهیلگری محلی", "icon": "🏘️",
     "desc": "شناسایی موانع دسترسی و ظرفیت‌های محلی"},
]

# ۹ معیار پیشنهاد هوشمند (بند ۹ـ۲)
MATCH_CRITERIA = [
    {"code": "issue_type", "name": "نوع مسئله غالب", "weight": 25,
     "desc": "سلامت، مسکن، اشتغال، آموزش، کودک، سالمند، معلولیت یا خشونت"},
    {"code": "urgency", "name": "سطح فوریت", "weight": 20,
     "desc": "عادی، اولویت‌دار، سریع یا فوری"},
    {"code": "field_visit", "name": "نیاز به بازدید میدانی", "weight": 10,
     "desc": "ضرورت یا عدم ضرورت مشاهده محیط زندگی"},
    {"code": "expertise", "name": "تخصص و تجربه", "weight": 15,
     "desc": "سابقه رسیدگی به پرونده‌های مشابه"},
    {"code": "geo", "name": "موقعیت جغرافیایی", "weight": 10,
     "desc": "نزدیکی و امکان دسترسی"},
    {"code": "capacity", "name": "ظرفیت و بار کاری", "weight": 8,
     "desc": "تعداد پرونده‌های فعال و زمان پاسخ‌گویی"},
    {"code": "authority", "name": "سطح صلاحیت", "weight": 7,
     "desc": "نوع مأموریت قابل واگذاری"},
    {"code": "conflict", "name": "تعارض منافع", "weight": 3,
     "desc": "جلوگیری از ارجاع به فرد دارای رابطه شخصی"},
    {"code": "performance", "name": "عملکرد گذشته", "weight": 2,
     "desc": "کیفیت، به‌موقع‌بودن و کامل‌بودن گزارش‌ها"},
]

# ۹ نمونه همیار مددکار برای سیستم تخصیص
SAMPLE_ASSISTANTS = [
    {
        "id": "AST-001", "name": "خانم مریم احمدی", "role": "assistant",
        "role_label": "همیار مددکار", "avatar_color": "#0d9488",
        "specializations": ["health", "elderly", "caregiving"],
        "provinces": ["tehran", "alborz"],
        "areas": ["تهران", "کرج"], "capacity_max": 10, "current_load": 3,
        "performance": 4.7, "languages": ["فارسی"], "status": "online",
        "experience_years": 5, "missions": ["info", "field", "support", "monitor"]
    },
    {
        "id": "AST-002", "name": "آقای رضا کریمی", "role": "employ",
        "role_label": "کارشناس اشتغال", "avatar_color": "#2563eb",
        "specializations": ["employment", "skills", "business"],
        "provinces": ["tehran"],
        "areas": ["تهران"], "capacity_max": 8, "current_load": 2,
        "performance": 4.5, "languages": ["فارسی", "انگلیسی"], "status": "online",
        "experience_years": 8, "missions": ["specialist", "facilitator"]
    },
    {
        "id": "AST-003", "name": "خانم فاطمه موسوی", "role": "rose",
        "role_label": "مشاور کلینیک رز", "avatar_color": "#9333ea",
        "specializations": ["mental", "child", "family", "violence"],
        "provinces": ["tehran", "alborz"],
        "areas": ["تهران", "کرج"], "capacity_max": 6, "current_load": 4,
        "performance": 4.8, "languages": ["فارسی"], "status": "online",
        "experience_years": 10, "missions": ["specialist", "support"]
    },
    {
        "id": "AST-004", "name": "آقای حسن رضایی", "role": "assistant",
        "role_label": "همیار مددکار", "avatar_color": "#16a34a",
        "specializations": ["housing", "legal", "administrative"],
        "provinces": ["isfahan", "tehran"],
        "areas": ["اصفهان", "تهران"], "capacity_max": 12, "current_load": 5,
        "performance": 4.3, "languages": ["فارسی", "عربی"], "status": "online",
        "experience_years": 4, "missions": ["info", "field", "facilitator"]
    },
    {
        "id": "AST-005", "name": "خانم زهرا محمدی", "role": "swclinic",
        "role_label": "مددکار تخصصی", "avatar_color": "#d97706",
        "specializations": ["multi-issue", "complex", "mental"],
        "provinces": ["tehran", "alborz"],
        "areas": ["تهران", "کرج"], "capacity_max": 5, "current_load": 2,
        "performance": 4.9, "languages": ["فارسی", "ترکی"], "status": "busy",
        "experience_years": 12, "missions": ["specialist", "monitor"]
    },
    {
        "id": "AST-006", "name": "آقای علی صادقی", "role": "assistant",
        "role_label": "همیار آموزش‌دیده امور کودک", "avatar_color": "#dc2626",
        "specializations": ["child", "education", "protection"],
        "provinces": ["tehran"],
        "areas": ["تهران", "شهرری"], "capacity_max": 8, "current_load": 1,
        "performance": 4.6, "languages": ["فارسی"], "status": "online",
        "experience_years": 3, "missions": ["info", "field", "support", "social"]
    },
    {
        "id": "AST-007", "name": "خانم نسیم قاسمی", "role": "assistant",
        "role_label": "همیار سالمندان", "avatar_color": "#64748b",
        "specializations": ["elderly", "caregiving", "health"],
        "provinces": ["tehran"],
        "areas": ["تهران", "ورامین"], "capacity_max": 10, "current_load": 6,
        "performance": 4.4, "languages": ["فارسی"], "status": "online",
        "experience_years": 6, "missions": ["info", "field", "support", "monitor"]
    },
    {
        "id": "AST-008", "name": "آقای مهدی بابایی", "role": "worker",
        "role_label": "مددکار خانواده کمیتهٔ امداد", "avatar_color": "#0f766e",
        "specializations": ["all", "crisis", "protection", "complex"],
        "provinces": ["tehran"],
        "areas": ["تهران"], "capacity_max": 4, "current_load": 3,
        "performance": 5.0, "languages": ["فارسی"], "status": "online",
        "experience_years": 15, "missions": ["specialist", "info", "field", "monitor"]
    },
    {
        "id": "AST-009", "name": "خانم سحر اکبری", "role": "assistant",
        "role_label": "همیار امور توان‌بخشی", "avatar_color": "#7c3aed",
        "specializations": ["disability", "rehabilitation", "health"],
        "provinces": ["tehran", "mazandaran"],
        "areas": ["تهران", "ساری"], "capacity_max": 8, "current_load": 4,
        "performance": 4.5, "languages": ["فارسی"], "status": "online",
        "experience_years": 7, "missions": ["info", "field", "support", "monitor"]
    },
    {
        "id": "AST-010", "name": "آقای کاوه نوری", "role": "assistant",
        "role_label": "همیار مددکار", "avatar_color": "#0891b2",
        "specializations": ["health", "employment", "housing"],
        "provinces": ["isfahan", "fars"],
        "areas": ["اصفهان", "شیراز"], "capacity_max": 10, "current_load": 2,
        "performance": 4.6, "languages": ["فارسی"], "status": "online",
        "experience_years": 6, "missions": ["info", "field", "support"]
    },
    {
        "id": "AST-011", "name": "خانم پریسا جعفری", "role": "assistant",
        "role_label": "همیار مددکار", "avatar_color": "#be185d",
        "specializations": ["child", "education", "elderly"],
        "provinces": ["khorasan_razavi"],
        "areas": ["مشهد", "نیشابور"], "capacity_max": 8, "current_load": 3,
        "performance": 4.7, "languages": ["فارسی"], "status": "online",
        "experience_years": 5, "missions": ["info", "field", "support", "monitor"]
    },
    {
        "id": "AST-012", "name": "آقای فریدون شریفی", "role": "worker",
        "role_label": "مددکار خانواده کمیتهٔ امداد", "avatar_color": "#1e40af",
        "specializations": ["all", "crisis", "complex"],
        "provinces": ["isfahan"],
        "areas": ["اصفهان", "کاشان"], "capacity_max": 4, "current_load": 2,
        "performance": 4.8, "languages": ["فارسی"], "status": "online",
        "experience_years": 11, "missions": ["specialist", "info", "field", "monitor"]
    },
]


def match_assistants(emmpi_result, household, assistants=None):
    """
    تخصیص هوشمند همیار بر اساس ۹ معیار سند (بند ۹ـ۲).
    شبیه اسنپ: درخواست به چند همیار نزدیک ارسال می‌شود؛
    بر اساس امتیاز تطبیق، مناسب‌ترین‌ها رتبه‌بندی می‌شوند.

    خروجی: فهرست مرتب‌شده بر اساس امتیاز تطبیق (۰ تا ۱۰۰)
    """
    if assistants is None:
        assistants = SAMPLE_ASSISTANTS

    if not emmpi_result:
        return []

    household_location = (household.get("identity", {}).get("location", "") or "").lower()
    dominant_dims = emmpi_result.get("dominant_dims", [])
    red_flags = emmpi_result.get("red_flags", [])
    has_urgency = len(red_flags) > 0
    needs_cdi = emmpi_result.get("needs_cdi", False)

    # نگاشت بُعد EM-MPI → تخصص
    DIM_TO_SPEC = {
        "A": "health", "B": "education", "C": "housing",
        "D": "employment", "E": "vulnerability",
    }
    needed_specs = []
    for d in dominant_dims[:3]:
        spec = DIM_TO_SPEC.get(d["code"])
        if spec:
            needed_specs.append(spec)

    # افزودن تخصص‌های خاص بر اساس پرچم‌های قرمز
    RF_TO_SPEC = {
        "R1": "housing", "R2": "health", "R3": "health",
        "R4": "child", "R5": "mental", "R6": "elderly",
        "R7": "housing", "R8": "legal", "R9": "employment",
    }
    for rf in red_flags:
        spec = RF_TO_SPEC.get(rf["code"])
        if spec and spec not in needed_specs:
            needed_specs.append(spec)

    # آیا نیاز به بازدید میدانی است؟
    needs_field_visit = bool(red_flags) or needs_cdi

    results = []
    for ast in assistants:
        score = 0
        reasons = []
        warnings = []

        # ۱. نوع مسئله غالب (۲۵٪)
        matched_specs = [s for s in needed_specs if s in ast["specializations"]]
        if matched_specs:
            spec_score = (len(matched_specs) / max(len(needed_specs), 1)) * 25
            score += spec_score
            reasons.append(f"✓ تخصص در: {', '.join(matched_specs)}")
        else:
            score += 2  # حداقل امتیاز
            warnings.append("تخصص مستقیم ندارد")

        # ۲. سطح فوریت (۲۰٪)
        if has_urgency:
            if ast["role"] in ("worker", "swclinic"):
                score += 20
                reasons.append("✓ مددکار رسمی برای فوریت")
            elif ast["role"] == "rose" and any(rf["code"] == "R5" for rf in red_flags):
                score += 18
                reasons.append("✓ کلینیک رز برای خشونت")
            elif ast["role"] == "rose" and any(rf["code"] == "R4" for rf in red_flags):
                score += 18
                reasons.append("✓ کلینیک رز برای کودک")
            else:
                score += 5
                warnings.append("برای فوریت، مددکار رسمی ترجیح دارد")
        else:
            score += 12  # فوریت پایین، همه مناسب

        # ۳. نیاز به بازدید میدانی (۱۰٪)
        if needs_field_visit:
            if "field" in ast.get("missions", []):
                score += 10
                reasons.append("✓ قادر به بازدید میدانی")
            else:
                score += 3
        else:
            score += 8

        # ۴. تخصص و تجربه (۱۵٪)
        exp = ast.get("experience_years", 0)
        exp_score = min(exp * 1.5, 15)
        score += exp_score
        reasons.append(f"تجربه: {exp} سال")

        # ۵. موقعیت جغرافیایی (۱۰٪)
        ast_areas = [a.lower() for a in ast.get("areas", [])]
        if household_location:
            matched_area = any(
                area in household_location or household_location in area
                for area in ast_areas
            )
            if matched_area:
                score += 10
                reasons.append("✓ نزدیک به محل سکونت")
            else:
                score += 2
                warnings.append("دور از محل سکونت")
        else:
            score += 5

        # ۶. ظرفیت و بار کاری (۸٪)
        available = ast["capacity_max"] - ast["current_load"]
        if available > 0:
            cap_score = min(available * 2, 8)
            score += cap_score
            reasons.append(f"ظرفیت آزاد: {available}")
        else:
            score -= 5
            warnings.append("ظرفیت تکمیل")

        # ۷. سطح صلاحیت (۷٪)
        if has_urgency and ast["role"] in ("worker", "swclinic"):
            score += 7
        elif ast["role"] == "rose":
            score += 5
        elif ast["role"] == "employ" and "employment" in needed_specs:
            score += 7
            reasons.append("✓ کارشناس اشتغال")
        else:
            score += 4

        # ۸. تعارض منافع (۳٪) — در نمونهٔ اولیه، فرض بر عدم تعارض
        score += 3

        # ۹. عملکرد گذشته (۲٪)
        perf = ast.get("performance", 4)
        score += (perf / 5) * 2
        reasons.append(f"عملکرد: {perf}/۵")

        # وضعیت آنلاین
        if ast.get("status") == "offline":
            score -= 10
            warnings.append("آفلاین")
        elif ast.get("status") == "busy":
            score -= 3
            warnings.append("در حال انجام مأموریت")

        # محدودسازی امتیاز
        score = max(0, min(score, 100))

        results.append({
            "assistant": ast,
            "score": round(score),
            "reasons": reasons,
            "warnings": warnings,
            "available": available > 0 and ast.get("status") != "offline",
            "matched_specs": matched_specs,
            "needed_specs": needed_specs,
        })

    # مرتب‌سازی بر اساس امتیاز
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════
# آیکون‌ها و برچسب‌های مولفه‌های PEH/PIM/PES
# ═══════════════════════════════════════════════════════════
COMPONENT_META = {
    # PEH (بند ۲ـ۵)
    "EM": {"label": "محرومیت اولیه", "full": "شدت اولیه محرومیت EM-MPI", "color": "amber",
           "icon_svg": '<path d="M12 2v20M7 7l-3 7a3 3 0 0 0 6 0L7 7zM17 7l-3 7a3 3 0 0 0 6 0l-3-7z"/>'},
    "R": {"label": "خطر و فوریت", "full": "خطر و فوریت فعال", "color": "red",
          "icon_svg": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'},
    "F": {"label": "تشدید بحران", "full": "احتمال تشدید یا بازگشت بحران", "color": "amber",
          "icon_svg": '<polyline points="3 17 9 11 13 15 21 7"/><polyline points="14 7 21 7 21 14"/>'},
    "G": {"label": "گلوگاه", "full": "شدت گلوگاه‌های اصلی", "color": "blue",
          "icon_svg": '<circle cx="12" cy="12" r="3"/><path d="M12 1v6M12 17v6M4.22 4.22l4.24 4.24M15.54 15.54l4.24 4.24M1 12h6M17 12h6M4.22 19.78l4.24-4.24M15.54 8.46l4.24-4.24"/>'},
    "E": {"label": "اثربخشی", "full": "اثربخشی و فوریت فرصت مداخله", "color": "green",
          "icon_svg": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>'},
    "W": {"label": "انتظار", "full": "انتظار و عدم دریافت خدمت", "color": "mut",
          "icon_svg": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'},

    # PIM (بند ۲ـ۱۰)
    "U": {"label": "فوریت و ریسک", "full": "فوریت و ریسک تأخیر", "color": "red",
          "icon_svg": '<path d="M1 21h22M4 21V10a8 8 0 0 1 16 0v11M12 2v2M19 9l1.5-1.5M5 9L3.5 7.5"/>'},
    "D": {"label": "وابستگی", "full": "وابستگی و پیش‌نیازی بودن", "color": "blue",
          "icon_svg": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'},
    "I": {"label": "اثربخشی", "full": "اثربخشی مورد انتظار", "color": "green",
          "icon_svg": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'},
    "A": {"label": "آمادگی", "full": "آمادگی و ترجیح خانوار", "color": "green",
          "icon_svg": '<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>'},
    "C": {"label": "ظرفیت", "full": "ظرفیت، هزینه، عدم تکرار", "color": "amber",
          "icon_svg": '<circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h1v4M16.71 13.88l.7.71-2.82 2.82"/>'},

    # PES (بند ۲ـ۱۵)
    "T": {"label": "حساسیت زمانی", "full": "حساسیت زمانی", "color": "red",
          "icon_svg": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'},
    "K": {"label": "تناسب", "full": "تناسب و قابلیت اجرا", "color": "blue",
          "icon_svg": '<path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2zM14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2z"/>'},
}


def get_component_meta(key):
    """برگرداندن متادادهٔ آیکون و برچسب برای مولفه‌های PEH/PIM/PES."""
    return COMPONENT_META.get(key, {"label": key, "full": key, "color": "mut", "icon_svg": ""})


def get_referral_paths_visual():
    """برگرداندن ۸ مسیر ارجاع برای نمایش بصری."""
    paths = [
        {"code": "P1", "name": "پایش و خدمت عمومی", "condition": "امتیاز ۰-۱۴۹ + بدون پرچم",
         "action": "ثبت، اطلاع‌رسانی، پایش دوره‌ای", "to_cdi": False, "color": "P4",
         "icon": '<polyline points="20 6 9 17 4 12"/>'},
        {"code": "P2", "name": "بررسی تکمیلی محدود", "condition": "امتیاز ۱۵۰-۲۹۹ + بدون فوریت",
         "action": "تکمیل مدارک، بررسی محدود", "to_cdi": False, "color": "P3",
         "icon": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'},
        {"code": "P3", "name": "ارجاع عادی به CDI", "condition": "امتیاز ۳۰۰-۴۴۹",
         "action": "ارجاع عادی به CDI", "to_cdi": True, "color": "P2",
         "icon": '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>'},
        {"code": "P4", "name": "ارجاع اولویت‌دار به CDI", "condition": "امتیاز ۴۵۰-۵۹۹",
         "action": "ارجاع اولویت‌دار، بررسی میدانی", "to_cdi": True, "color": "P1",
         "icon": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'},
        {"code": "P5", "name": "ارجاع سریع و چندبخشی", "condition": "امتیاز ۶۰۰-۱۰۰۰",
         "action": "ارزیابی سریع CDI، مداخلهٔ چندبخشی", "to_cdi": True, "color": "P0",
         "icon": '<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>'},
        {"code": "P6", "name": "ارجاع فوری (مستقل از امتیاز)", "condition": "وجود پرچم قرمز معتبر",
         "action": "رسیدگی اضطراری، ارجاع فوری", "to_cdi": True, "color": "P0",
         "icon": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'},
        {"code": "P7", "name": "ارجاع پیشگیرانه", "condition": "E6 در سطح شدید یا تشخیص مددکار",
         "action": "بررسی تکمیلی یا ارجاع پیشگیرانه", "to_cdi": True, "color": "P1",
         "icon": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'},
        {"code": "P8", "name": "راستی‌آزمایی داده", "condition": "تناقض خوداظهاری/مدارک/گزارش",
         "action": "توقف تصمیم، درخواست مدرک", "to_cdi": False, "color": "P2",
         "icon": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'},
    ]
    return paths
