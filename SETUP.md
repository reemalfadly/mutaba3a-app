# متابعة (Mutaba3a) - دليل الإعداد البسيط

مرحباً! هذا الملف يشرح لك خطوة بخطوة كيف تكمّل إعداد تطبيقك، بدون أي
تعقيد تقني. اقرأ كل قسم بالترتيب.

---

## 0. خطوة مهمة جداً ولازمة أولاً: إضافة "خط بناء التطبيق" (Workflow)

كل الكود انرفع للمستودع بنجاح، **ما عدا ملف واحد** بسبب صلاحيات الرمز
(Token) المستخدم -- ملف `.github/workflows/build.yml` وهو المسؤول عن
تشغيل عملية بناء ملف APK تلقائياً. لازم تضيفه مرة وحدة يدوياً من متصفح
الإنترنت (خطوة بسيطة، تاخذ دقيقتين):

1. افتح: https://github.com/reemalfadly/mutaba3a-app
2. اضغط زر **Add file > Create new file** (أعلى يمين قائمة الملفات).
3. في خانة اسم الملف اكتب بالضبط: `.github/workflows/build.yml`
   (اكتب الجزء اللي فيه `/` وراح ينشئ المجلدات تلقائياً).
4. الصق هذا المحتوى بالضبط داخل صندوق تحرير الملف:

```yaml
name: Build Android APK

on:
  push:
    branches: [ main ]
  workflow_dispatch: {}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cache buildozer global directory
        uses: actions/cache@v4
        with:
          path: ~/.buildozer
          key: buildozer-global-${{ hashFiles('buildozer.spec') }}

      - name: Cache buildozer local (.buildozer) directory
        uses: actions/cache@v4
        with:
          path: .buildozer
          key: buildozer-local-${{ runner.os }}-${{ hashFiles('buildozer.spec') }}
          restore-keys: |
            buildozer-local-${{ runner.os }}-

      - name: Build debug APK with buildozer
        uses: ArtemSBulgakov/buildozer-action@v1
        id: buildozer
        with:
          command: buildozer android debug
          buildozer_version: stable

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: mutaba3a-debug-apk
          path: ${{ steps.buildozer.outputs.filename }}
          if-no-files-found: error
```

5. انزل لأسفل الصفحة واضغط الزر الأخضر **Commit changes...** ثم
   **Commit changes** مرة ثانية في النافذة اللي تفتح (اختر "Commit
   directly to the main branch").
6. بمجرد ما تحفظ، بيبدأ بناء APK تلقائياً -- روح لتبويب **Actions**
   بالمستودع لمتابعته (اشرح بالتفصيل في القسم 4 تحت).

بعد هذي الخطوة مرة وحدة، أي تعديل مستقبلي (مثل إضافة مفاتيح API) بيشغّل
بناء جديد تلقائياً بدون ما تكرر هذي الخطوة.

---

## 1. التطبيق يشتغل من الآن بدون أي إعداد إضافي

التطبيق فيه ميزات تشتغل *فوراً* بدون أي مفتاح (API key):
- قائمة المهام (إضافة، تعليم كمنجز، ترحيل، حذف)
- المواعيد (التقويم)
- مواقيت الصلاة (تحتاج فقط تفعيل خدمة الموقع GPS في جوالك)

فيه ميزتين تحتاجان إعداد بسيط منك (اختياري، تقدر تسويه لاحقاً):
- **البحث عن الأماكن** (يحتاج مفتاح خرائط جوجل)
- **المزامنة السحابية** (نسخ بياناتك على الإنترنت، تحتاج حساب Firebase مجاني)

لين ما تسوي هذي الخطوات، التطبيق بيعرض لك رسالة "غير مفعّل" بدل ما يتوقف
عن العمل (كراش). ما فيه أي خطر.

---

## 2. كيف تحصل على مفتاح خرائط جوجل (Google Maps API Key)

هذا المفتاح يخلّي التطبيق يبحث عن اسم مكان (مثل "مسجد النور") ويحوله
لموقع دقيق على الخريطة.

1. افتح هذا الرابط: https://console.cloud.google.com/
2. سجّل دخول بحساب جوجل (Gmail) العادي.
3. اضغط على "Create Project" (إنشاء مشروع) وسمّه مثلاً "Mutaba3a".
4. من القائمة الجانبية اذهب إلى: **APIs & Services > Library**.
5. ابحث عن **Geocoding API** واضغط **Enable** (تفعيل).
6. ابحث أيضاً عن **Places API** واضغط **Enable**.
7. اذهب إلى **APIs & Services > Credentials**.
8. اضغط **Create Credentials > API key**. راح يظهر لك مفتاح طويل من
   حروف وأرقام (مثل: `AIzaSyD...`). انسخه.
9. (يُفضّل) اضغط على المفتاح واختر "Restrict Key" وحدد فقط
   Geocoding API و Places API لحماية إضافية.

**وين تحط المفتاح؟**
افتح ملف `app/config.py` داخل مجلد المشروع، ولاقي هذا السطر:
```python
GOOGLE_MAPS_API_KEY = _env_or("", "MUTABA3A_GOOGLE_MAPS_API_KEY", "GOOGLE_MAPS_API_KEY")
```
غيّر `""` (الفراغ) إلى المفتاح بتاعك بين علامتي تنصيص، مثل:
```python
GOOGLE_MAPS_API_KEY = _env_or("AIzaSyD_ضع_مفتاحك_هنا", "MUTABA3A_GOOGLE_MAPS_API_KEY", "GOOGLE_MAPS_API_KEY")
```
احفظ الملف، وارفعه (push) إلى GitHub (اطلب من أي شخص تقني يساعدك بأمر
`git push`، أو استخدم واجهة GitHub نفسها لتعديل الملف مباشرة في المتصفح
عبر زر "Edit" على الملف في صفحة المستودع).

> ملاحظة: Google يعطيك رصيد مجاني شهري يكفي للاستخدام الشخصي العادي.

---

## 3. كيف تنشئ مشروع Firebase مجاني للمزامنة السحابية

هذا يخلّي بياناتك (مهامك ومواعيدك) محفوظة على الإنترنت، حتى لو غيّرت
جوالك أو حذفت التطبيق وثبّته من جديد.

1. افتح: https://console.firebase.google.com/
2. سجّل دخول بحساب Gmail.
3. اضغط **Add project** (إضافة مشروع) وسمّه "mutaba3a".
4. تقدر توقف "Google Analytics" (مو ضروري)، ثم اضغط **Create project**.
5. من القائمة الجانبية اذهب لـ **Build > Firestore Database**.
6. اضغط **Create database**، اختر **Start in production mode**، واختر
   أقرب موقع خادم لك، ثم **Enable**.
7. اذهب لـ **Build > Authentication** ثم **Get started**.
8. من تبويب **Sign-in method**، فعّل **Anonymous** (تسجيل دخول مجهول -
   أبسط خيار، ما يحتاج بريد إلكتروني من المستخدم).
9. ارجع للصفحة الرئيسية للمشروع (أيقونة الترس ⚙️ > **Project settings**).
10. تحت تبويب **General**، انزل لقسم "Your apps"، اضغط أيقونة **</>**
    (Web app)، سمّها "mutaba3a-web"، واضغط **Register app**.
11. راح يظهر لك كود فيه شيء اسمه `apiKey: "AIza..."` -- هذا هو
    **Web API Key**. انسخه.
12. معرّف المشروع (**Project ID**) تلقاه في نفس صفحة Project settings،
    تحت "Project ID" (كلمة إنجليزية بسيطة بدون مسافات).

**وين تحط المعلومات؟**
افتح `app/config.py` وعدّل هذي الأسطر بنفس طريقة القسم السابق:
```python
FIREBASE_WEB_API_KEY = _env_or("ضع_مفتاح_الويب_هنا", ...)
FIREBASE_PROJECT_ID = _env_or("ضع_معرف_المشروع_هنا", ...)
```
اترك `FIREBASE_AUTH_MODE` كما هي (`"anonymous"`) -- أبسط طريقة وما
تحتاج أي تسجيل دخول من المستخدم.

---

## 4. كيف تلاقي ملف APK بعد رفع الكود (push) إلى GitHub

1. افتح رابط المستودع: https://github.com/reemalfadly/mutaba3a-app
2. اضغط على تبويب **Actions** في الأعلى.
3. بتلاقي قائمة بعمليات البناء (workflow runs). اضغط على آخر عملية
   (الأحدث، فوق القائمة).
4. انتظر لين تصير علامة ✅ خضراء بجانب اسم العملية (البناء يأخذ عادة
   10-25 دقيقة، خصوصاً أول مرة).
5. انزل لأسفل الصفحة إلى قسم **Artifacts**.
6. اضغط على **mutaba3a-debug-apk** لتنزيله -- بيجيك ملف مضغوط (.zip).
7. فك ضغط الملف (Extract / استخراج)، بتلاقي بداخله ملف بامتداد `.apk`.
8. انقل ملف الـ APK لجوالك (عن طريق واتساب لنفسك، أو تلغرام، أو كيبل
   USB، أو Google Drive -- أي طريقة تناسبك).

**تثبيت APK على جوال سامسونج:**
1. اضغط على ملف الـ APK لفتحه.
2. إذا ظهرت رسالة "لا يمكن تثبيت تطبيقات من مصادر غير معروفة"، اضغط
   **الإعدادات (Settings)** في نفس الرسالة.
3. فعّل خيار **السماح من هذا المصدر** (Allow from this source) -- مثلاً
   لمتصفحك أو تطبيق الملفات اللي فتحت منه الملف.
4. ارجع واضغط تثبيت (Install).
5. افتح التطبيق، وراح يطلب منك صلاحية الموقع (GPS) -- وافق عليها عشان
   تشتغل مواقيت الصلاة تلقائياً.

---

## 5. كيف تعيد تشغيل عملية البناء بعد تعديل الإعدادات

خيار 1 (تلقائي): أي تعديل ترفعه (push) لملف داخل المشروع على فرع
`main` يشغّل بناء جديد تلقائياً.

خيار 2 (يدوي بدون تعديل شي): اذهب لتبويب **Actions**، اختر
**Build Android APK** من القائمة اليسرى، ثم اضغط زر **Run workflow**
(أعلى يمين القائمة) واختر الفرع `main` ثم **Run workflow**.

---

## 6. ملاحظات وقرارات هندسية (للمهتمين)

- استخدمنا **Kivy العادي** بدلاً من KivyMD لتقليل احتمال فشل بناء
  التطبيق على أندرويد (KivyMD تضيف تعقيد إضافي في التبعيات). صممنا
  الألوان والشكل يدوياً في `app/theme.py` بألوان مرحة (وردي، بنفسجي،
  فيروزي، أصفر دافئ).
- كل البيانات تُحفظ محلياً أولاً في SQLite (`app/db.py`)، والمزامنة مع
  Firebase (`app/sync_firebase.py`) طبقة إضافية فوقها -- التطبيق ما
  ينكسر أبداً بدون إنترنت أو بدون إعداد Firebase.
- مواقيت الصلاة تُحسب عبر خدمة Aladhan المجانية
  (https://aladhan.com/prayer-times-api) بدون أي مفتاح API، بالاعتماد
  على GPS الجوال. طريقة الحساب الافتراضية هي "أم القرى" (مناسبة لمعظم
  دول الخليج) ويمكن تغييرها من `app/config.py` (`PRAYER_CALCULATION_METHOD`).
- إذا تحب تجرب التطبيق على كمبيوتر (بدون جوال) قبل ما يوصلك الـ APK:
  ثبّت Python، ثم شغّل:
  ```
  pip install -r requirements.txt
  python main.py
  ```
  بما إن الكمبيوتر ما فيه GPS، روح لشاشة "الإعدادات" وأدخل موقع يدوي
  (خط طول/عرض) عشان تجرب مواقيت الصلاة.

---

## 7. مخاطر محتملة في أول بناء (Build) على GitHub Actions

بناء تطبيقات Kivy/Python لأندرويد لأول مرة أحياناً يحتاج محاولة أو
محاولتين بسبب تفاصيل تقنية في أدوات Android (SDK/NDK) أو نسخ المكتبات.
إذا فشل أول بناء، أعد المحاولة عبر "Run workflow" -- غالباً المحاولة
الثانية تنجح لأن بعض الملفات تكون محفوظة (cached) من قبل.
