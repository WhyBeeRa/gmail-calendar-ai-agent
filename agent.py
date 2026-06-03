import os
import json
import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load env variables from .env file
load_dotenv()

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key and api_key != "your_gemini_api_key_here":
    client = genai.Client(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY not found or is placeholder in environment variables. Please check your .env file.")

def analyze_email(email_content, current_time_iso=None):
    """Uses Gemini to determine if an email is a meeting request, extract details, and format them."""
    if not current_time_iso:
        current_time_iso = datetime.datetime.now().isoformat()
        
    prompt = f"""
Analyze the following email content. Determine if it is a request/invitation to schedule a meeting or event.
Reference Current Time (for resolving relative terms like 'tomorrow', 'next Monday', etc.): {current_time_iso}

Return your answer strictly as a valid JSON object. Do not wrap the JSON in markdown code blocks. The JSON must have the following keys:
1. "is_meeting_request": (boolean) True if this email is clearly requesting or inviting to a meeting, session, call, or event. False otherwise.
2. "is_missing_info": (boolean) True if some critical scheduling info (like date or time) is missing or ambiguous.
3. "missing_info_reason": (string) Explanation of what is missing if is_missing_info is True (e.g. "Missing start time").
4. "subject": (string) A suggested subject/title for the calendar event (e.g., "Intro Call with Yuval").
5. "start_iso": (string or null) The proposed start time in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SS').
6. "end_iso": (string or null) The proposed end time in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SS'). If duration is not specified, assume 1 hour.
7. "description": (string) A brief description or notes for the meeting.
8. "attendees": (list of strings) List of attendee email addresses if found in the text.

Email Subject: {email_content.get('subject', '')}
Email From: {email_content.get('sender', '')}
Email Content:
{email_content.get('body', '')}
"""
    try:
        if not client:
            raise ValueError("Gemini Client is not initialized. Please set GEMINI_API_KEY in .env.")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Error parsing email with Gemini: {e}")
        # Return fallback non-meeting response
        return {
            "is_meeting_request": False,
            "is_missing_info": False,
            "missing_info_reason": "",
            "subject": "",
            "start_iso": None,
            "end_iso": None,
            "description": "",
            "attendees": []
        }
