# CDI امداد — React Native Mobile App

## ساخت APK

### پیش‌نیازها
- Node.js 18+
- JDK 17
- Android SDK (API 35+)

### مراحل
```bash
# 1. نصب وابستگی‌ها
npm install

# 2. Prebuild native code
npx expo prebuild --platform android

# 3. Build APK
cd android
./gradlew assembleDebug

# 4. APK در:
# android/app/build/outputs/apk/debug/app-debug.apk
```

### تنظیم آدرس سرور
در فایل `src/api.js`:
```javascript
const SERVER = 'http://188.212.96.235:8085';
```

### صفحات
- LoginScreen — ورود با انتخاب نقش
- HomeScreen — داشبورد با آمار
- PoolScreen — استخر درخواست‌ها (اسنپ‌مانند)
- CaseDetailScreen — جزئیات پرونده
- WalletScreen — کیف پول همیار
- SatisfactionScreen — رضایت‌سنجی (ستاره‌دار)
