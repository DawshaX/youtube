# زيادة حد النشر اليومي (اختياري — عشان ننشر أكتر من 6 فيديوهات/يوم)

**ليه؟** جوجل بتدّي كل **مشروع Google Cloud** حصة 10,000 وحدة/يوم، والرفعة على
يوتيوب بتاخد **1,600 وحدة** → يعني **6 فيديوهات يوميًا** لكل مشروع. ده حد من جوجل
مش من المصنع. الكود جاهز يشتغل بمشروعين = **12 فيديو/يوم**.

---

## الطريقة (1) مشروع تاني — يشتغل فورًا بما إن الكود جاهز

### الخطوة 1 — مشروع Google Cloud جديد
1. افتح <https://console.cloud.google.com/projectcreate>
2. اسم المشروع مثلًا: `daousha-publisher-2` → **Create**.

### الخطوة 2 — فعّل YouTube Data API v3
1. في المشروع الجديد: **APIs & Services → Library**
2. ابحث عن **YouTube Data API v3** → **Enable**.

### الخطوة 3 — شاشة الموافقة (OAuth consent screen)
1. **APIs & Services → OAuth consent screen**
2. نوع المستخدم: **External** → أنشئ التطبيق، واملأ الاسم والإيميل.
3. **Audience**: أضف إيميل حساب القناة نفسه في **Test users**
   (لو التطبيق في وضع Testing) — أو انشره (Publish) لو تحب.

### الخطوة 4 — أنشئ OAuth client
1. **APIs & Services → Credentials → Create credentials → OAuth client ID**
2. النوع: **Desktop app** (أسهل للحصول على refresh token).
3. خُد الـ **Client ID** و**Client Secret**.

### الخطوة 5 — هات Refresh Token (مرة واحدة)
استخدم **OAuth 2.0 Playground**:
1. افتح <https://developers.google.com/oauthplayground/>
2. من ⚙️ (الإعدادات) فعّل: **Use your own OAuth credentials** → حط الـ Client ID/Secret.
3. في الخطوة 1: اختار الـ scope: `https://www.googleapis.com/auth/youtube.upload`
   (واختياريًا أضف `https://www.googleapis.com/auth/youtube.readonly`).
4. **Authorize APIs** → سجّل دخول **بحساب القناة** → **Exchange authorization code for tokens**.
5. انسخ **Refresh token**.

### الخطوة 6 — ضيف الأسرار في المستودع
`https://github.com/DawshaX/youtube/settings/secrets/actions` → **New repository secret**:

| الاسم | القيمة |
|---|---|
| `YOUTUBE_CLIENT_ID_2` | Client ID من المشروع الجديد |
| `YOUTUBE_CLIENT_SECRET_2` | Client Secret |
| `YOUTUBE_REFRESH_TOKEN_2` | الـ Refresh token |

**وبس.** بعد كده: لما حصة المشروع الأول تخلص، الرفع بيكمّل بالاعتماد التاني
تلقائيًا (والسقف اليومي بقى 12)، وتقدر تشوف ده في لوج السير:
`⏭️ حصة الاعتماد الأساسي خلصت — برفع بالاعتماد الإضافي…`

---

## الطريقة (2) طلب زيادة حصة من جوجل (الرسمي — للمشاريع المُثبتة)

1. افتح النموذج: <https://support.google.com/youtube/contact/yt_api_form>
2. اختار **Quota Extension Request**.
3. اكتب بصراحة:
   > We run an original Arabic YouTube Shorts channel (دۅۄشے) and publish
   > original, self-produced short-form videos (60s, 1080×1920, licensed
   > footage, original TTS narration, no reused content). Our automation
   > uploads on a schedule and we have hit the default 10,000 units/day
   > (6 uploads). We are requesting a higher quota to publish more of our
   > original content daily.
4. الطلبات دي بتتراجع يدويًا وبتاخد أيام — والموافقة غالبًا بتوصل لـ 20–50 رفعة/يوم.

---

## ملاحظة مهمة قبل ما تزود العدد

القناة عندها **548 مشترك** ورفعنا النهاردة 6 فيديوهات في ساعتين ونص، وحصل إن
**9 فيديوهات اختفت** من القناة (رسالة يوتيوب: «removed by the uploader»).
قبل ما ترفع لـ 12–50 في يوم، الأنسب:
- نعرف **مين** بيمسح الفيديوهات (إنت/أداة تانية/وصول للحساب) — فيه بلاغ مفتوح **#25**
  ورادار بقاء كل 20 دقيقة بيسجّل وقت الاختفاء.
- نراقب أداء الفيديوهات الجديدة (مشاهدات/تفاعل) بعد 24 ساعة ونعدّل،
  لأن النشر الثقيل على قناة صغيرة ممكن يضر أكتر من يفيد.
