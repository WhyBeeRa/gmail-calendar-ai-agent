import os
import glob
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'
]

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Look for any client_secret JSON file in the directory
            client_secret_files = glob.glob('client_secret_*.json')
            if not client_secret_files:
                # Check for standard credentials.json as fallback
                if os.path.exists('credentials.json'):
                    client_secret_file = 'credentials.json'
                else:
                    raise FileNotFoundError("Could not find any client_secret_*.json or credentials.json file. Please place it in the directory.")
            else:
                client_secret_file = client_secret_files[0]
            
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=8080)
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

def get_gmail_service():
    creds = get_credentials()
    return build('gmail', 'v1', credentials=creds)

def get_calendar_service():
    creds = get_credentials()
    return build('calendar', 'v3', credentials=creds)

# --- Gmail Helpers ---

def list_unread_emails(query="is:unread"):
    """Lists unread emails matching the query."""
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        return messages
    except Exception as e:
        print(f"Error listing emails: {e}")
        return []

def get_email_details(message_id):
    """Retrieves subject, sender, body, and message ID of a specific email."""
    try:
        service = get_gmail_service()
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        
        headers = message.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        
        body = ""
        payload = message.get('payload', {})
        
        def parse_parts(parts):
            nonlocal body
            for part in parts:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif 'parts' in part:
                    parse_parts(part['parts'])

        if 'parts' in payload:
            parse_parts(payload['parts'])
        else:
            data = payload.get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                
        return {
            'id': message_id,
            'subject': subject,
            'sender': sender,
            'body': body
        }
    except Exception as e:
        print(f"Error getting email {message_id}: {e}")
        return None

def mark_email_as_read(message_id):
    """Removes the UNREAD label from an email."""
    try:
        service = get_gmail_service()
        service.users().messages().batchModify(
            userId='me',
            body={'ids': [message_id], 'removeLabelIds': ['UNREAD']}
        ).execute()
        return True
    except Exception as e:
        print(f"Error marking email {message_id} as read: {e}")
        return False

def send_reply(to_email, subject, body_text, thread_id=None):
    """Sends an email response."""
    try:
        service = get_gmail_service()
        message = MIMEText(body_text)
        message['to'] = to_email
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        body = {'raw': raw_message}
        if thread_id:
            body['threadId'] = thread_id
            
        service.users().messages().send(userId='me', body=body).execute()
        return True
    except Exception as e:
        print(f"Error sending reply to {to_email}: {e}")
        return False

# --- Calendar Helpers ---

def check_calendar_availability(start_iso, end_iso):
    """Checks if the user has any events between start_iso and end_iso."""
    try:
        service = get_calendar_service()
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_iso,
            timeMax=end_iso,
            singleEvents=True
        ).execute()
        events = events_result.get('items', [])
        return len(events) == 0
    except Exception as e:
        print(f"Error checking calendar: {e}")
        return False

def create_calendar_event(summary, start_iso, end_iso, description="", attendees=None):
    """Creates an event in the user's primary calendar."""
    try:
        service = get_calendar_service()
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_iso,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_iso,
                'timeZone': 'UTC',
            }
        }
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
            
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return created_event
    except Exception as e:
        print(f"Error creating calendar event: {e}")
        return None
