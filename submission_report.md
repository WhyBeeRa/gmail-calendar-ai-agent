# דוח הגשה - מטלה 3: Gmail & Calendar AI Agent
**קורס:** סוכני בינה מלאכותית (LLMs)
**מגיש/ים:** [שם ותעודת זהות]

---

## 1. קישור לריפו ב-GitHub
[https://github.com/WhyBeeRa/gmail-calendar-ai-agent](https://github.com/WhyBeeRa/gmail-calendar-ai-agent)

---

## 2. ארכיטקטורת המערכת וזרימת עבודה
המערכת מבוססת על סוכן אוטונומי אמיתי (Autonomous AI Agent) העושה שימוש ביכולות **Function Calling (Skills)** של Gemini:
1. **הזרקת כלים (Tools):** המערכת עוטפת את ה-APIs של Gmail ו-Calendar כפונקציות פייתון פשוטות וחושפת אותן ככלים ישירות למודל השפה (Gemini 2.5 Flash).
2. **קבלת החלטות אוטונומית:** המודל מקבל הגדרת משימה גלובלית ופועל בלולאה אוטונומית שבה הוא מחליט בעצמו לאיזה כלי לקרוא ובאילו ארגומנטים (למשל, קודם להריץ את `list_unread_emails`, אז עבור כל מייל לקרוא ל-`get_email_details`, ולאחר מכן להחליט על `check_calendar_availability` או `send_reply` ו-`mark_email_as_read`).
3. **ביצוע מקומי:** הקוד המקומי מריץ את הפונקציות שהמודל מבקש, מחזיר לו את התוצאות, והמודל ממשיך בצעד הבא עד להשלמת המשימה.

---

## 3. לוגיקת ה-Prompt והכלים
הפרומפט מוגדר כ-System Instruction שמכוון את התנהגות הסוכן וקובע את סדר העבודה והלוגיקה העסקית. המודל מקבל את משתני הסביבה והזמן הנוכחי של המערכת (Reference Current Time) על מנת לפתור ביטויים יחסיים (כמו "מחר", "ביום שני הבא" וכו') ומפעיל את הכלים הנדרשים לביצוע המשימה.

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
