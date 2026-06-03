import sys
import datetime
from google_services import (
    list_unread_emails,
    get_email_details,
    mark_email_as_read,
    send_reply,
    check_calendar_availability,
    create_calendar_event
)
from agent import analyze_email

def main():
    # Reconfigure stdout/stderr to UTF-8 to handle Unicode characters (emojis, etc.) on Windows
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    print("Starting Auto Meeting Scheduler Agent...")
    
    # 1. Fetch unread emails
    unread_messages = list_unread_emails()
    print(f"Found {len(unread_messages)} unread messages.")
    
    for msg in unread_messages:
        msg_id = msg['id']
        email_data = get_email_details(msg_id)
        if not email_data:
            continue
            
        print(f"\nProcessing email: Subject: '{email_data['subject']}' | From: {email_data['sender']}")
        
        # 2. Analyze using Gemini
        current_time_iso = datetime.datetime.now().isoformat()
        analysis = analyze_email(email_data, current_time_iso)
        
        if not analysis.get('is_meeting_request'):
            print("-> Email is not a meeting request. Marking as read.")
            mark_email_as_read(msg_id)
            continue
            
        print("-> Identified as meeting request.")
        
        # Extract sender's email address
        sender = email_data['sender']
        sender_email = sender
        if '<' in sender and '>' in sender:
            sender_email = sender.split('<')[1].split('>')[0]
            
        # 3. Handle missing info
        if analysis.get('is_missing_info'):
            reason = analysis.get('missing_info_reason', 'Missing event details')
            print(f"-> Missing details: {reason}. Requesting details via email.")
            reply_subject = f"Re: {email_data['subject']}"
            reply_body = (
                f"Hello,\n\n"
                f"Thank you for reaching out to schedule a meeting.\n"
                f"We received your request, but some details were missing or ambiguous:\n"
                f"- {reason}\n\n"
                f"Please reply with the missing details so we can schedule the meeting.\n\n"
                f"Best regards,\n"
                f"Autonomous Meeting Scheduler Agent"
            )
            if send_reply(sender_email, reply_subject, reply_body, thread_id=msg_id):
                mark_email_as_read(msg_id)
                print("-> Missing details reply sent and email marked as read.")
            continue
            
        start_iso = analysis.get('start_iso')
        end_iso = analysis.get('end_iso')
        subject = analysis.get('subject', 'Meeting')
        description = analysis.get('description', '')
        
        print(f"-> Proposed slot: {start_iso} to {end_iso}")
        
        # 4. Check availability
        is_available = check_calendar_availability(start_iso, end_iso)
        reply_subject = f"Re: {email_data['subject']}"
        
        if is_available:
            print("-> Slot is available. Creating event...")
            # Include sender and other extracted attendees
            attendees = [sender_email]
            if analysis.get('attendees'):
                attendees.extend(analysis.get('attendees'))
            # Filter duplicates and invalid emails
            attendees = list(set([a for a in attendees if '@' in a]))
            
            event = create_calendar_event(subject, start_iso, end_iso, description, attendees)
            if event:
                print(f"-> Event created successfully: {event.get('htmlLink')}")
                reply_body = (
                    f"Hello,\n\n"
                    f"The proposed time slot ({start_iso} to {end_iso}) is available!\n"
                    f"I have successfully scheduled the meeting: '{subject}'.\n\n"
                    f"Calendar Event Link: {event.get('htmlLink')}\n\n"
                    f"Best regards,\n"
                    f"Autonomous Meeting Scheduler Agent"
                )
                if send_reply(sender_email, reply_subject, reply_body, thread_id=msg_id):
                    mark_email_as_read(msg_id)
                    print("-> Confirmation reply sent and email marked as read.")
        else:
            print("-> Slot is busy. Sending decline email...")
            reply_body = (
                f"Hello,\n\n"
                f"Thank you for the invitation: '{subject}'.\n"
                f"Unfortunately, the proposed time slot ({start_iso} to {end_iso}) is already booked.\n"
                f"Please suggest an alternative time slot.\n\n"
                f"Best regards,\n"
                f"Autonomous Meeting Scheduler Agent"
            )
            if send_reply(sender_email, reply_subject, reply_body, thread_id=msg_id):
                mark_email_as_read(msg_id)
                print("-> Decline reply sent and email marked as read.")

if __name__ == "__main__":
    main()
