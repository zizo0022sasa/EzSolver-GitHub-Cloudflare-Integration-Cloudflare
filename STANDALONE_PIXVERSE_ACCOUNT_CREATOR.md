# 🎯 مواصفة المعمارية المبسطة: منشئ حسابات PixVerse المباشر المستقل (Standalone Account Creator)
> **الهدف:** إنشاء وتفعيل حسابات جديدة على PixVerse تلقائياً وبأقل تعقيد ممكن، بدون أي سيرفرات خلفية، وبدون استنساخ مستودعات GitHub خارجية، وبدون أي كود متعلق بالفيديوهات أو الشات.  
> **مبدأ التصميم:** `Zero-Server, Zero-GitHub, Pure Account Creation (YAGNI 100%)`

---

## 🧭 1. الرؤية الهندسية ونطاق العمل الصارم (Scope Boundary)

- **داخل النطاق (IN-SCOPE):**
  - إنشاء الحساب فقط (`hkga1official@rc.mailings.live`).
  - جلب التوكن الأمني داخلياً وبشكل مضمن (In-process Inline Execution) دون فتح أي بورت أو خادم HTTP محلي.
  - طلب كود التفعيل `POST /creative_platform/account/getVerificationCode`.
  - استقبال كود OTP وإتمام التسجيل `POST /creative_platform/account/register`.
  - حفظ بيانات الحساب الجديد في `accounts_pixverse.json`.

- **خارج النطاق بالكامل (OUT-OF-SCOPE / YAGNI):**
  - ❌ لا خوادم خلفية محلية (No Local HTTP Daemons / No SCM Services / No Port 8191).
  - ❌ لا استنساخ لمستودعات خارجية من GitHub (No EzSolver repo / No Theyka repo).
  - ❌ لا كود لتوليد الفيديو أو الشات أو نماذج الذكاء الاصطناعي في سكريبت التسجيل.
  - ❌ لا قواعد بيانات SQLite أو أنظمة IPC معقدة.

---

## 🏗️ 2. المعمارية المباشرة (Direct Architecture)

```
[ المستخدم يشغل السكريبت ]
           │
           ▼
[ pixverse_direct_register.py (ملف بايثون واحد مباشر) ]
           │
           ├─ 1. استخراج التوكن داخلياً (Inline Solver via CDP/Browser) بدون خادم خارجي
           ├─ 2. إرسال طلب رمز التحقق (POST /getVerificationCode)
           ├─ 3. إدخال رمز التحقق OTP
           ├─ 4. إرسال طلب إتمام التسجيل (POST /register)
           └─ 5. حفظ الحساب في accounts_pixverse.json وإنهاء العملية فوراً
```

---

## 🛠️ 3. خطة التنفيذ المباشرة (Detailed Implementation Steps)

### الخطوة 1: تجهيز دالة الاستخراج المباشرة المضمنة (Inline Solver)
- دالة بايثون مستقلة `get_turnstile_inline()` تفتح متصفح Chrome الأصلي لجهازك بوضع خفي، تنتظر استخراج قيمة `cf-turnstile-response` مباشرة في الذاكرة، ثم تقفل المتصفح فوراً دون تشغيل أي سيرفر خلفي.

### الخطوة 2: صياغة ريكويست كود التفعيل (Verification Code Request)
- استخدام مكتبة `requests` القياسية لإرسال:
  `POST https://app-api.pixverse.ai/creative_platform/account/getVerificationCode`
  بالبيانات: `{"Username": "...", "Mail": "hkga1official@rc.mailings.live", "Password": "...", "Validate": token}`.

### الخطوة 3: استقبال كود التفعيل (OTP)
- استقبال الكود من المستخدم مباشرة عبر التيرمينال.

### الخطوة 4: إتمام التسجيل وتأكيد الحساب (Register Request)
- استخراج التوكن المضمن الثاني وإرسال:
  `POST https://app-api.pixverse.ai/creative_platform/account/register`
  بالبيانات: `{"Username": "...", "Mail": "...", "Password": "...", "Code": otp, "Validate": token_2}`.

### الخطوة 5: حفظ بيانات الحساب والخروج
- حفظ `jwt_token` و `account_id` في `accounts_pixverse.json` وتأكيد الحصول على 60 نقطة مجانية فورية.

