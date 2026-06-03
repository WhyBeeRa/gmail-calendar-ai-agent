# דוח הגשה - מטלה 3: Gmail & Calendar AI Agent
**קורס:** סוכני בינה מלאכותית (LLMs)
**מגיש/ים:** [שם ותעודת זהות]

---

## 1. קישור לריפו ב-GitHub
[https://github.com/WhyBeeRa/gmail-calendar-ai-agent](https://github.com/WhyBeeRa/gmail-calendar-ai-agent)

---

## 2. ארכיטקטורת המערכת וזרימת עבודה
המערכת מבוססת על סוכן אוטונומי (AI Agent) שמבצע את הפעולות הבאות:
1. **שלב המשיכה (Gmail API):** סריקת הודעות דוא"ל שלא נקראו בתיבת הדואר הנכנס.
2. **שלב הניתוח (Gemini 2.5 Flash):** שימוש בספריית `google-genai` החדשה לניתוח טקסט חופשי של המיילים, זיהוי כוונת השולח (האם מדובר בבקשת פגישה), וחילוץ ישויות מובנות (כותרת, תאריך ושעה בפורמט ISO, משתתפים ותיאור).
3. **שלב הבדיקה (Google Calendar API):** בדיקת התנגשויות ביומן בטווח הזמנים המבוקש.
4. **שלב הפעולה:**
   - **במקרה והזמן פנוי:** קביעת אירוע חדש ביומן ושליחת אישור עם קישור ישיר לפגישה.
   - **במקרה והזמן תפוס:** שליחת מייל דחייה מנומס המבקש מועד חלופי.
   - **במקרה ופרטים קריטיים חסרים:** שליחת מייל הבהרה לשולח עם פירוט המידע החסר.
   - בכל מקרה, המייל מסומן כנקרא (`Read`) כדי למנוע עיבוד כפול.

---

## 3. לוגיקת ה-Prompt
הפרומפט מנחה את מודל השפה להחזיר אובייקט JSON מובנה ומוגדר מראש (באמצעות `response_mime_type="application/json"`). המודל מקבל כקלט גם את הזמן הנוכחי של המערכת (Reference Current Time) על מנת לפתור ביטויים יחסיים (כמו "מחר", "ביום שני הבא" וכו').

---

## 4. פלט הרצה אמיתי (Logs)
להלן לוג של הרצה מוצלחת על תיבת מייל אמיתית, המציג את שלושת תרחישי הלוגיקה המרכזיים:

### א. זיהוי פגישה עם פרטים חסרים:
```text
Processing email: Subject: 'סמינר מחלקתי' | From: "מזכירות המחלקה" <noreply@mail.biu.ac.il>
-> Identified as meeting request.
-> Missing details: Missing start time and end time. Requesting details via email.
-> Missing details reply sent and email marked as read.
```

### ב. זיהוי התנגשות ביומן (זמן תפוס):
```text
Processing email: Subject: 'פגישת סטטוס חודשית' | From: Lior Levin <liorleviner@gmail.com>
-> Identified as meeting request.
-> Proposed slot: 2026-07-06T09:00:00+03:00 to 2026-07-06T10:00:00+03:00
-> Slot is busy. Sending decline email...
-> Decline reply sent and email marked as read.
```

### ג. התעלמות ממיילים שאינם זימונים:
```text
Processing email: Subject: 'Find out why work flows faster in Slack channels' | From: Slack <no-reply@email.slackhq.com>
-> Email is not a meeting request. Marking as read.
```
