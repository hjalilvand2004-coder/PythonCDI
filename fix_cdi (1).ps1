# ============================================================
# CDI System Fix Script - رفع خطای items → actions
# اجرا در PowerShell: .\fix_cdi.ps1
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
$backupPath = "$projectPath\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
Copy-Item "$projectPath\main.py" $backupPath -ErrorAction SilentlyContinue
Copy-Item "$projectPath\cdi_engine.py" $backupPath -ErrorAction SilentlyContinue
if (Test-Path "$projectPath\templates") {
    Copy-Item "$projectPath\templates\*.html" $backupPath -ErrorAction SilentlyContinue
}
Write-Host "✓ بکاپ ایجاد شد: $backupPath" -ForegroundColor Green

# --- تابع جایگزینی متن در فایل ---
function Replace-InFile {
    param(
        [string]$filePath,
        [string]$find,
        [string]$replace
    )

    if (-not (Test-Path $filePath)) {
        Write-Host "  ⚠ یافت نشد (رد شد): $filePath" -ForegroundColor Yellow
        return $false
    }

    $content = [System.IO.File]::ReadAllText($filePath, [System.Text.Encoding]::UTF8)
    if ($content.Contains($find)) {
        $newContent = $content.Replace($find, $replace)
        [System.IO.File]::WriteAllText($filePath, $newContent, [System.Text.UTF8Encoding]::new($false))
        Write-Host "  ✓ اصلاح شد: $filePath" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  - تغییری لازم نبود: $filePath" -ForegroundColor Gray
        return $false
    }
}

# --- ۱. اصلاح cdi_engine.py ---
Write-Host "`n=== اصلاح cdi_engine.py ===" -ForegroundColor Cyan
Replace-InFile "$projectPath\cdi_engine.py" `
    '"items": basket_sorted,' `
    '"actions": basket_sorted,'

Replace-InFile "$projectPath\cdi_engine.py" `
    'result.get("basket", {"items": [], "counts": {}})' `
    'result.get("basket", {"actions": [], "counts": {}})'

# --- ۲. اصلاح main.py ---
Write-Host "`n=== اصلاح main.py ===" -ForegroundColor Cyan
Replace-InFile "$projectPath\main.py" `
    '"info": q, "items": []' `
    '"info": q, "actions": []'

Replace-InFile "$projectPath\main.py" `
    'res["basket"]["items"]' `
    'res["basket"]["actions"]'

Replace-InFile "$projectPath\main.py" `
    'queue_map[item["queue"]]["items"]' `
    'queue_map[item["queue"]]["actions"]'

# --- ۳. اصلاح templates/household_view.html ---
Write-Host "`n=== اصلاح household_view.html ===" -ForegroundColor Cyan
Replace-InFile "$projectPath\templates\household_view.html" `
    'res.basket.items' `
    'res.basket.actions'

# --- ۴. اصلاح templates/profile.html ---
Write-Host "`n=== اصلاح profile.html ===" -ForegroundColor Cyan
Replace-InFile "$projectPath\templates\profile.html" `
    'res.basket.items' `
    'res.basket.actions'

# --- ۵. اصلاح templates/intervention_basket.html ---
Write-Host "`n=== اصلاح intervention_basket.html ===" -ForegroundColor Cyan
Replace-InFile "$projectPath\templates\intervention_basket.html" `
    'res.basket.items' `
    'res.basket.actions'

# --- ۶. اصلاح templates/service_queues.html ---
Write-Host "`n=== اصلاح service_queues.html ===" -ForegroundColor Cyan
Replace-InFile "$projectPath\templates\service_queues.html" `
    'q.items' `
    'q.actions'

# --- بررسی نهایی ---
Write-Host "`n=== بررسی نهایی ===" -ForegroundColor Cyan
$allGood = $true

$checkFiles = @(
    "$projectPath\templates\household_view.html",
    "$projectPath\templates\profile.html",
    "$projectPath\templates\intervention_basket.html"
)

foreach ($file in $checkFiles) {
    if (Test-Path $file) {
        $content = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
        if ($content.Contains('basket.items')) {
            $name = Split-Path $file -Leaf
            Write-Host "  ✗ $name: هنوز 'basket.items' دارد" -ForegroundColor Red
            $allGood = $false
        }
    }
}

if (Test-Path "$projectPath\templates\service_queues.html") {
    $content = [System.IO.File]::ReadAllText("$projectPath\templates\service_queues.html", [System.Text.Encoding]::UTF8)
    if ($content.Contains('q.items')) {
        Write-Host "  ✗ service_queues.html: هنوز 'q.items' دارد" -ForegroundColor Red
        $allGood = $false
    }
}

if (Test-Path "$projectPath\cdi_engine.py") {
    $content = [System.IO.File]::ReadAllText("$projectPath\cdi_engine.py", [System.Text.Encoding]::UTF8)
    if ($content.Contains('"items": basket_sorted')) {
        Write-Host "  ✗ cdi_engine.py: هنوز کلید 'items' دارد" -ForegroundColor Red
        $allGood = $false
    }
}

if ($allGood) {
    Write-Host "  ✓ تمام اصلاحات با موفقیت اعمال شد!" -ForegroundColor Green
}

# --- راهنمای نهایی ---
Write-Host "`n=== گام‌های بعدی ===" -ForegroundColor Cyan
Write-Host "۱. برنامه را اجرا کنید:" -ForegroundColor White
Write-Host "   cd $projectPath" -ForegroundColor Gray
Write-Host "   .venv\Scripts\python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "۲. در مرورگر باز کنید: http://127.0.0.1:5000" -ForegroundColor White
Write-Host ""
Write-Host "۳. اگر خطای دیگری دریافت کردید، متن کامل خطا را بفرستید." -ForegroundColor White
Write-Host ""
Write-Host "نسخهٔ بکاپ در: $backupPath" -ForegroundColor Gray
