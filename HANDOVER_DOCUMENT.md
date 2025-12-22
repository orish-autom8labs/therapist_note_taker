# מסמך חפיפה - Note Taker Project
## Handover Document for New Agent

---

## 1. תיאור הפרויקט ומטרותיו

### 1.1 מטרת הפרויקט
**Note Taker** הוא אפליקציית תמלול בזמן אמת עבור פסיכולוגים. האפליקציה מספקת:
- תמלול בזמן אמת בעברית (ללא הקלטת אודיו)
- זיהוי דוברים (Speaker 1, Speaker 2)
- שמירה אוטומטית ל-Google Drive
- אבטחה מקסימלית - אפס אחסון בשרתים שלנו

### 1.2 ארכיטקטורה
- **Backend**: FastAPI (Python) - שרת על פורט 3001
- **Frontend**: React - לקוח על פורט 3000
- **Transcription Provider**: Soniox API (כרגע לא עובד - ראה סעיף 4)
- **Storage**: Google Drive API
- **Authentication**: Google OAuth 2.0

### 1.3 תכונות עובדות ✅
- ✅ **שמירה ל-Google Drive** - עובדת במלואה
- ✅ **כפתור "View in Drive"** - עובד ומעביר ל-Drive
- ✅ **OAuth Authentication** - עובד
- ✅ **Session Management** - עובד
- ✅ **Email Notifications** - עובד
- ✅ **Error Recovery** - עובד (localStorage + Drive temp files)

### 1.4 תכונות לא עובדות ❌
- ❌ **תמלול בזמן אמת** - לא עובד (ראה סעיף 4)

---

## 2. מסמכי תכנון - נתיבים מלאים

### 2.1 מסמכי תכנון עיקריים

#### Product Requirements Document (PRD)
**נתיב**: `/Users/orish/code/note_taker/COMPREHENSIVE_PLAN.md`
- חלק 2: Product Requirements Document
- מטרות המוצר, דרישות פונקציונליות, דרישות לא-פונקציונליות

#### UX Design
**נתיב**: `/Users/orish/code/note_taker/UX_DESIGN.md`
- עיצוב מסכים, זרימת משתמש, מפרטי UI/UX

#### Testing Plan
**נתיב**: `/Users/orish/code/note_taker/IMMEDIATE_FIXES_AND_TESTING.md`
- תוכנית בדיקות, Browser Automation Testing Framework
- **נתיב נוסף**: `/Users/orish/code/note_taker/tests/` - תיקיית הבדיקות

#### Technical Analysis
**נתיב**: `/Users/orish/code/note_taker/TECHNICAL_ANALYSIS.md`
- ניתוח טכני מפורט

### 2.2 מסמכי מיגרציה ו-Architecture

#### Comparison with Official Example
**נתיב**: `/Users/orish/code/note_taker/COMPARISON_OFFICIAL_VS_OUR_CODE.md`
- השוואה מפורטת בין הקוד שלנו לדוגמה הרשמית של Soniox
- **קריטי להבנת הבעיה**

#### Migration Plan
**נתיב**: `/Users/orish/code/note_taker/MIGRATION_TO_SONIOX_SDK_PLAN.md`
- תוכנית מיגרציה מלאה ל-SDK של Soniox

#### Migration Implications
**נתיב**: `/Users/orish/code/note_taker/MIGRATION_IMPLICATIONS_SUMMARY.md`
- השלכות המיגרציה, שינויים נדרשים

### 2.3 מסמכי הסבר על Soniox

#### How to Run Official Example
**נתיב**: `/Users/orish/code/note_taker/HOW_TO_RUN_SONIOX_EXAMPLE.md`
- הוראות מפורטות להרצת הדוגמה הרשמית של Soniox
- **זה עובד מושלם!**

#### Soniox Example Review
**נתיב**: `/Users/orish/code/note_taker/SONIOX_EXAMPLE_REVIEW.md`
- סקירה של הדוגמה הרשמית

#### Temporary API Keys Explained
**נתיב**: `/Users/orish/code/note_taker/TEMPORARY_API_KEYS_EXPLAINED.md`
- הסבר על מפתחות API זמניים (ביטחון)

---

## 3. דרישות סביבה והרצה

### 3.1 דרישות מערכת

#### Backend (Python)
- Python 3.10+
- Virtual environment (`venv`)
- Dependencies: `server/requirements.txt`

#### Frontend (React)
- Node.js 18+ (מומלץ 20+)
- npm או yarn

#### External Services
- Soniox API Key
- Google Cloud Project עם:
  - OAuth 2.0 credentials
  - Google Drive API enabled

### 3.2 הוראות התקנה והרצה

#### התקנה
```bash
# התקנת dependencies
cd /Users/orish/code/note_taker
npm install
cd server && pip install -r requirements.txt
cd ../client && npm install
```

#### הגדרת Environment Variables
צור קובץ `server/.env`:
```bash
SONIOX_API_KEY=your_soniox_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
TRANSCRIPTION_PROVIDER=soniox
```

#### הרצה
```bash
# Terminal 1: Backend
cd /Users/orish/code/note_taker/server
source venv/bin/activate
python run.py
# שרת רץ על http://localhost:3001

# Terminal 2: Frontend
cd /Users/orish/code/note_taker/client
npm start
# לקוח רץ על http://localhost:3000
```

### 3.3 הרצת הדוגמה הרשמית של Soniox

**נתיב לדוגמה**: `/Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/`

**סקריפט להרצה**:
```bash
cd /Users/orish/code/note_taker
./run_soniox_example.sh
```

או עקוב אחר ההוראות ב:
**נתיב**: `/Users/orish/code/note_taker/HOW_TO_RUN_SONIOX_EXAMPLE.md`

**הדוגמה הרשמית עובדת מושלם!** זה צריך להיות הבסיס למיגרציה.

---

## 4. סקירת בעיות תמלול - מה ניסינו ומה נכשל

### 4.1 בעיות עיקריות

#### בעיה #1: WebSocket 404
**תיאור**: חיבור WebSocket החזיר 404
**פתרון שניסינו**: תיקון נתיבים, בדיקת Uvicorn configuration
**תוצאה**: ✅ נפתר
**מסמך**: `/Users/orish/code/note_taker/WEBSOCKET_404_FIX.md`

#### בעיה #2: Soniox Timeout (408)
**תיאור**: Soniox החזיר timeout אחרי 20 שניות
**סיבה**: אי-התאמה בפורמט אודיו - שלחנו WebM/Opus, Soniox ציפה ל-PCM
**פתרונות שניסינו**:
- ✅ הוספת `enable_endpoint_detection`
- ✅ פיצול chunks ל-3840 bytes
- ✅ הוספת delay של 120ms בין chunks
- ❌ **לא פתרנו את בעיית פורמט האודיו הבסיסית**
**תוצאה**: ❌ עדיין לא עובד
**מסמכים**:
- `/Users/orish/code/note_taker/SONIOX_TIMEOUT_RECOVERY.md`
- `/Users/orish/code/note_taker/WHY_SONIOX_TIMED_OUT.md`
- `/Users/orish/code/note_taker/AUDIO_FORMAT_FIX_OPTIONS.md`

#### בעיה #3: תצוגת תמלול - אותיות נפרדות
**תיאור**: תמלול הופיע אות-אות במקום משפטים
**פתרון שניסינו**: שינוי לוגיקת שליחת tokens, fallback mechanism
**תוצאה**: ✅ נפתר חלקית, אבל יצר בעיות חדשות

#### בעיה #4: משפטים כפולים
**תיאור**: כל משפט הופיע פעמיים
**פתרון שניסינו**: ניסיון למנוע duplicates, ניקוי non-final tokens
**תוצאה**: ❌ לא נפתר לחלוטין

#### בעיה #5: תמלול מתדרדר עם הזמן
**תיאור**: התמלול התחיל טוב ואז התדרדר לטקסט לא קריא
**סיבה**: הצטברות של non-final tokens
**פתרון שניסינו**: מעבר לדפוס של הדוגמה הרשמית (החלפת non-final tokens)
**תוצאה**: ❌ עדיין לא עובד - תמלול לא מופיע בכלל

#### בעיה #6: תמלול לא מופיע
**תיאור**: אחרי השינויים האחרונים, תמלול לא מופיע כלל
**סיבה**: כנראה בעיה ב-rendering או ב-state management
**תוצאה**: ❌ לא נפתר

### 4.2 מה למדנו

1. **הדוגמה הרשמית של Soniox עובדת מושלם** - צריך להשתמש בה כבסיס
2. **SDK של Soniox מטפל בפורמט אודיו** - אנחנו לא צריכים לעשות זאת ידנית
3. **הארכיטקטורה הנוכחית שגויה** - צריך client-to-Soniox ישיר, לא דרך server
4. **הדוגמה הרשמית משתמשת ב-temporary API keys** - יותר בטוח

### 4.3 מסמכי דיבוג נוספים

- `/Users/orish/code/note_taker/DEBUG_STEPS.md`
- `/Users/orish/code/note_taker/DEBUG_TRANSCRIPTION.md`
- `/Users/orish/code/note_taker/TRANSCRIPTION_DEBUG_ANALYSIS.md`
- `/Users/orish/code/note_taker/TROUBLESHOOTING.md`

---

## 5. הדוגמה הרשמית של Soniox - בסיס למיגרציה

### 5.1 למה הדוגמה הרשמית חשובה

**הדוגמה הרשמית עובדת מושלם!** זה צריך להיות הבסיס למיגרציה.

**נתיב לדוגמה**: `/Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/`

### 5.2 הבדלים עיקריים

#### הארכיטקטורה של הדוגמה הרשמית:
```
Browser (React)
  ↓ Uses @soniox/speech-to-text-web SDK
  ↓ Direct WebSocket to Soniox
Soniox API

Server (FastAPI)
  ↓ Only generates temporary API keys
  ↓ Does NOT handle WebSocket
  ↓ Does NOT handle audio
```

#### הארכיטקטורה הנוכחית שלנו (לא עובדת):
```
Browser (React)
  ↓ Manual WebSocket to our server
  ↓ Sends WebM/Opus audio
Our Server (FastAPI)
  ↓ Handles WebSocket connection
  ↓ Forwards audio to Soniox
  ↓ Processes tokens
Soniox API
```

### 5.3 מה צריך לעשות

**לשכתב את הקוד להשתמש בדוגמה הרשמית כבסיס:**

1. **Client Side**:
   - התקן `@soniox/speech-to-text-web` SDK
   - השתמש ב-`SonioxClient` כמו בדוגמה
   - חיבור ישיר ל-Soniox (לא דרך server)

2. **Server Side**:
   - רק endpoint ל-temporary API keys
   - REST API endpoints לשמירה ל-Drive
   - הסר את כל לוגיקת ה-WebSocket וה-audio handling

3. **State Management**:
   - השתמש ב-`finalTokens` ו-`nonFinalTokens` arrays כמו בדוגמה
   - `setNonFinalTokens(newNonFinalTokens)` - החלף, לא הוסף

### 5.4 מסמכי מיגרציה

- `/Users/orish/code/note_taker/MIGRATION_TO_SONIOX_SDK_PLAN.md` - תוכנית מפורטת
- `/Users/orish/code/note_taker/COMPARISON_OFFICIAL_VS_OUR_CODE.md` - השוואה מפורטת
- `/Users/orish/code/note_taker/MIGRATION_IMPLICATIONS_SUMMARY.md` - השלכות

---

## 6. תכונות עובדות - שמירה ל-Google Drive

### 6.1 מה עובד ✅

#### שמירה ל-Google Drive
- ✅ Auto-save כל דקה
- ✅ שמירה סופית בסוף session
- ✅ יצירת קבצים ב-Drive
- ✅ עדכון קבצים קיימים
- ✅ שמירת קבצים זמניים

**קוד רלוונטי**:
- `server/src/services/drive_service.py` - שירות Drive
- `server/main.py` - endpoints לשמירה
- `client/src/services/transcriptSyncService.js` - סינכרון מהלקוח

#### כפתור "View in Drive"
- ✅ עובד ומעביר ל-Drive
- ✅ מופעל רק כשיש קישור
- ✅ עיצוב נכון

**קוד רלוונטי**:
- `client/src/components/SuccessScreen.js`

#### OAuth Authentication
- ✅ Google OAuth 2.0
- ✅ קבלת permissions ל-Drive
- ✅ Token management

**קוד רלוונטי**:
- `client/src/services/authService.js`
- `server/main.py` - OAuth endpoints

#### Email Notifications
- ✅ שליחת email בסוף session
- ✅ קישור לקובץ ב-Drive

**קוד רלוונטי**:
- `server/src/services/email_service.py`

### 6.2 מה לא צריך לשנות

**אל תשנה את:**
- Drive service (`server/src/services/drive_service.py`)
- OAuth flow
- Email service
- Session management
- Error recovery (localStorage + Drive)

**רק צריך:**
- לשכתב את חלק התמלול להשתמש ב-SDK
- להוסיף REST endpoints לסינכרון תמלול מהלקוח

---

## 7. מבנה הפרויקט

### 7.1 קבצים עיקריים

#### Backend
```
server/
├── main.py                    # FastAPI app, endpoints
├── run.py                     # Entry point
├── requirements.txt           # Python dependencies
└── src/
    ├── config.py              # Configuration
    ├── providers/
    │   └── soniox_provider.py # Soniox provider (לא עובד)
    └── services/
        ├── drive_service.py   # ✅ עובד
        └── email_service.py  # ✅ עובד
```

#### Frontend
```
client/
├── src/
│   ├── App.js                 # Main app
│   ├── components/
│   │   ├── ActiveSession.js   # Session component (צריך שינוי)
│   │   ├── SuccessScreen.js   # ✅ עובד
│   │   └── LoginScreen.js    # ✅ עובד
│   ├── hooks/
│   │   └── useSonioxClient.js # Hook לתמלול (צריך שינוי)
│   └── services/
│       ├── transcriptSyncService.js # ✅ עובד
│       └── authService.js    # ✅ עובד
```

### 7.2 קבצים חשובים למיגרציה

- `client/src/hooks/useSonioxClient.js` - צריך לשכתב לפי הדוגמה
- `client/src/components/ActiveSession.js` - צריך לשכתב להשתמש ב-SDK
- `server/main.py` - צריך להוסיף REST endpoints, להסיר WebSocket

---

## 8. המלצות למיגרציה

### 8.1 שלבים מומלצים

1. **שלב 1: הבנת הדוגמה הרשמית**
   - הרץ את הדוגמה הרשמית
   - הבן את הארכיטקטורה
   - בדוק איך SDK מטפל באודיו

2. **שלב 2: מיגרציה הדרגתית**
   - התקן SDK ב-client
   - שכתב `useSonioxClient.js` לפי הדוגמה
   - שכתב `ActiveSession.js` להשתמש ב-SDK
   - הוסף REST endpoints ב-server

3. **שלב 3: שמירת תכונות עובדות**
   - שמור את Drive integration
   - שמור את OAuth
   - שמור את Email notifications

4. **שלב 4: בדיקות**
   - בדוק תמלול בזמן אמת
   - בדוק שמירה ל-Drive
   - בדוק speaker diarization

### 8.2 נקודות חשובות

- **אל תנסה לתקן את הקוד הקיים** - הוא מבוסס על ארכיטקטורה שגויה
- **השתמש בדוגמה הרשמית כבסיס** - היא עובדת מושלם
- **שמור את כל התכונות העובדות** - Drive, OAuth, Email
- **עבוד הדרגתי** - שלב אחר שלב

---

## 9. קישורים מהירים

### 9.1 מסמכים קריטיים
- **השוואה עם דוגמה רשמית**: `/Users/orish/code/note_taker/COMPARISON_OFFICIAL_VS_OUR_CODE.md`
- **תוכנית מיגרציה**: `/Users/orish/code/note_taker/MIGRATION_TO_SONIOX_SDK_PLAN.md`
- **איך להריץ דוגמה**: `/Users/orish/code/note_taker/HOW_TO_RUN_SONIOX_EXAMPLE.md`

### 9.2 קוד לדוגמה
- **דוגמה רשמית**: `/Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/`
- **סקריפט הרצה**: `/Users/orish/code/note_taker/run_soniox_example.sh`

### 9.3 תיקיות חשובות
- **Backend**: `/Users/orish/code/note_taker/server/`
- **Frontend**: `/Users/orish/code/note_taker/client/`
- **Tests**: `/Users/orish/code/note_taker/tests/`

---

## 10. סיכום

### מה עובד ✅
- שמירה ל-Google Drive
- OAuth Authentication
- Email Notifications
- Session Management
- Error Recovery

### מה לא עובד ❌
- תמלול בזמן אמת (הבעיה העיקרית)

### מה צריך לעשות
1. **לשכתב את חלק התמלול** להשתמש ב-SDK של Soniox
2. **להשתמש בדוגמה הרשמית כבסיס** - היא עובדת מושלם
3. **לשמור את כל התכונות העובדות** - Drive, OAuth, Email

### נקודת התחלה מומלצת
**התחל עם הדוגמה הרשמית:**
```bash
cd /Users/orish/code/note_taker
./run_soniox_example.sh
```

**ואז שכתב את הקוד שלנו להשתמש באותה ארכיטקטורה.**

---

**תאריך עדכון**: 2024
**גרסה**: 1.0

