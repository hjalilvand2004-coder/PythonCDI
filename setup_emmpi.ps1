# ============================================================
# CDI + EM-MPI Setup Script — نصب خودکار فایل‌های جدید
# اجرا در PowerShell: .\setup_emmpi.ps1
# ============================================================

$projectPath = "J:\samplaeProjectPython\PythonCDI"

# بررسی مسیر پروژه
if (-not (Test-Path "$projectPath\main.py")) {
    Write-Host "خطا: پروژه در مسیر زیر یافت نشد: $projectPath" -ForegroundColor Red
    Write-Host "لطفاً مسیر projectPath را در ابتدای اسکریپت اصلاح کنید." -ForegroundColor Yellow
    return
}

Write-Host "✓ پروژه یافت شد: $projectPath" -ForegroundColor Green

# --- بکاپ‌گیری ---
$backupPath = "$projectPath\backup_emmpi_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
if (Test-Path "$projectPath\main.py") { Copy-Item "$projectPath\main.py" $backupPath }
if (Test-Path "$projectPath\cdi_engine.py") { Copy-Item "$projectPath\cdi_engine.py" $backupPath }
if (Test-Path "$projectPath\templates") { Copy-Item "$projectPath\templates\*.html" $backupPath -ErrorAction SilentlyContinue }
Write-Host "✓ بکاپ ایجاد شد: $backupPath" -ForegroundColor Green

# --- ۱. ایجاد فایل emmpi_engine.py ---
Write-Host "`n=== ایجاد emmpi_engine.py ===" -ForegroundColor Cyan
$emmpiContent = @'
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

# این فایل را از مسیر دانلود کپی کنید
# مسیر: /home/z/my-project/download/emmpi_engine.py
'@

# این فقط یک placeholder است — فایل واقعی را از مسیر دانلود کپی کنید
Write-Host "  ⚠ فایل emmpi_engine.py را از مسیر دانلود کپی کنید:" -ForegroundColor Yellow
Write-Host "    /home/z/my-project/download/emmpi_engine.py" -ForegroundColor Gray
Write-Host "    → $projectPath\emmpi_engine.py" -ForegroundColor Gray

# --- ۲. کپی فایل‌های Python ---
Write-Host "`n=== فایل‌های Python ===" -ForegroundColor Cyan
Write-Host "  فایل‌های زیر را از مسیر دانلود کپی کنید:" -ForegroundColor White
Write-Host "    /home/z/my-project/download/main.py         → $projectPath\main.py" -ForegroundColor Gray
Write-Host "    /home/z/my-project/download/cdi_engine.py   → $projectPath\cdi_engine.py" -ForegroundColor Gray
Write-Host "    /home/z/my-project/download/emmpi_engine.py → $projectPath\emmpi_engine.py" -ForegroundColor Gray

# --- ۳. کپی فایل‌های HTML ---
Write-Host "`n=== فایل‌های HTML (در پوشهٔ templates) ===" -ForegroundColor Cyan
Write-Host "  فایل‌های زیر را از مسیر دانلود کپی کنید:" -ForegroundColor White
Write-Host "    /home/z/my-project/download/cdi-templates/emmpi_form.html    → $projectPath\templates\emmpi_form.html" -ForegroundColor Gray
Write-Host "    /home/z/my-project/download/cdi-templates/emmpi_result.html  → $projectPath\templates\emmpi_result.html" -ForegroundColor Gray
Write-Host "    /home/z/my-project/download/cdi-templates/base.html          → $projectPath\templates\base.html" -ForegroundColor Gray
Write-Host "    /home/z/my-project/download/cdi-templates/household_view.html → $projectPath\templates\household_view.html" -ForegroundColor Gray
Write-Host "    /home/z/my-project/download/cdi-templates/dashboard.html       → $projectPath\templates\dashboard.html" -ForegroundColor Gray

# --- ۴. اعمال اصلاحات items → actions (اگر قبلاً انجام نشده) ---
Write-Host "`n=== اعمال اصلاحات items → actions ===" -ForegroundColor Cyan

function Replace-InFile {
    param([string]$file, [string]$find, [string]$replace)
    if (Test-Path $file) {
        $c = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
        if ($c.Contains($find)) {
            $c = $c.Replace($find, $replace)
            [System.IO.File]::WriteAllText($file, $c, [System.Text.UTF8Encoding]::new($false))
            Write-Host "  ✓ اصلاح شد: $(Split-Path $file -Leaf)" -ForegroundColor Green
        }
    }
}

# فقط اگر فایل‌ها هنوز اصلاح نشده‌اند
Replace-InFile "$projectPath\cdi_engine.py" '"items": basket_sorted,' '"actions": basket_sorted,'
Replace-InFile "$projectPath\cdi_engine.py" 'result.get("basket", {"items": [], "counts": {}})' 'result.get("basket", {"actions": [], "counts": {}})'
Replace-InFile "$projectPath\main.py" '"info": q, "items": []' '"info": q, "actions": []'
Replace-InFile "$projectPath\main.py" 'res["basket"]["items"]' 'res["basket"]["actions"]'
Replace-InFile "$projectPath\main.py" 'queue_map[item["queue"]]["items"]' 'queue_map[item["queue"]]["actions"]'
Replace-InFile "$projectPath\templates\household_view.html" 'res.basket.items' 'res.basket.actions'
Replace-InFile "$projectPath\templates\profile.html" 'res.basket.items' 'res.basket.actions'
Replace-InFile "$projectPath\templates\intervention_basket.html" 'res.basket.items' 'res.basket.actions'
Replace-InFile "$projectPath\templates\service_queues.html" 'q.items' 'q.actions'

# --- ۵. بررسی نهایی ---
Write-Host "`n=== بررسی نهایی ===" -ForegroundColor Cyan
$allGood = $true

# بررسی وجود فایل‌های جدید
$requiredFiles = @(
    "$projectPath\emmpi_engine.py",
    "$projectPath\templates\emmpi_form.html",
    "$projectPath\templates\emmpi_result.html"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $(Split-Path $file -Leaf) موجود است" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $(Split-Path $file -Leaf) یافت نشد!" -ForegroundColor Red
        $allGood = $false
    }
}

# بررسی عدم وجود basket.items
$templateFiles = Get-ChildItem "$projectPath\templates\*.html" -ErrorAction SilentlyContinue
foreach ($tf in $templateFiles) {
    $content = [System.IO.File]::ReadAllText($tf.FullName, [System.Text.Encoding]::UTF8)
    if ($content.Contains('basket.items') -or $content.Contains('q.items')) {
        Write-Host "  ✗ $($tf.Name): هنوز 'basket.items' یا 'q.items' دارد" -ForegroundColor Red
        $allGood = $false
    }
}

if ($allGood) {
    Write-Host "`n  ✓ همه چیز آماده است!" -ForegroundColor Green
}

# --- راهنمای نهایی ---
Write-Host "`n=== گام‌های بعدی ===" -ForegroundColor Cyan
Write-Host "۱. برنامه را اجرا کنید:" -ForegroundColor White
Write-Host "   cd $projectPath" -ForegroundColor Gray
Write-Host "   .venv\Scripts\python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "۲. در مرورگر: http://127.0.0.1:5000" -ForegroundColor White
Write-Host ""
Write-Host "۳. جریان کار:" -ForegroundColor White
Write-Host "   ثبت درخواست → EM-MPI (غربالگری) → CDI (ارزیابی جامع)" -ForegroundColor Gray
Write-Host ""
Write-Host "نسخهٔ بکاپ در: $backupPath" -ForegroundColor Gray
