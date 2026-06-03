import os
import json
import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google_services import (
    list_unread_emails,
    get_email_details,
    mark_email_as_read,
    send_reply,
    check_calendar_availability,
    create_calendar_event
)

# Load env variables from .env file
load_dotenv()

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key and api_key != "your_gemini_api_key_here":
    client = genai.Client(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY not found or is placeholder in environment variables. Please check your .env file.")

def run_agent():
    """Runs the autonomous scheduling agent using Gemini Function Calling (Skills)."""
    if not client:
        print("Error: Gemini Client is not initialized. Please set GEMINI_API_KEY in .env.")
        return
        
    current_time_iso = datetime.datetime.now().isoformat()
    system_prompt = f"""
You are an Autonomous Meeting Scheduler Agent.
Reference Current Time (for resolving relative terms like 'tomorrow', 'next Monday', etc.): {current_time_iso}

Your goal is to process all unread emails in the user's mailbox.
Follow this workflow:
1. Retrieve the list of unread emails using list_unread_emails.
2. For each unread email:
   a. Retrieve its full details using get_email_details.
   b. Analyze if the email content is a request/invitation to schedule a meeting or event.
   c. If it is NOT a meeting request, mark it as read using mark_email_as_read and proceed to the next email.
   d. If it IS a meeting request:
      - Check if any critical scheduling information (e.g. date, start time, end time) is missing or ambiguous.
      - If details are missing, send a reply to the sender (using send_reply) explaining what is missing (e.g. "missing start time"), mark the email as read using mark_email_as_read, and proceed to the next email.
      - If details are complete, check calendar availability for the proposed start and end time (using check_calendar_availability).
      - If the slot is available, create the calendar event (using create_calendar_event), send a confirmation reply containing the event link (using send_reply), and mark the email as read (using mark_email_as_read).
      - If the slot is busy, send a polite reply declining the slot and asking for alternative times (using send_reply), and mark the email as read (using mark_email_as_read).
3. Once all unread emails have been processed, provide a summary of the actions taken.
"""

    messages = [
        types.Content(role="user", parts=[types.Part.from_text(text="Please start processing unread emails now.")])
    ]
    
    tool_map = {
        "list_unread_emails": list_unread_emails,
        "get_email_details": get_email_details,
        "mark_email_as_read": mark_email_as_read,
        "send_reply": send_reply,
        "check_calendar_availability": check_calendar_availability,
        "create_calendar_event": create_calendar_event
    }
    
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[
            list_unread_emails,
            get_email_details,
            mark_email_as_read,
            send_reply,
            check_calendar_availability,
            create_calendar_event
        ],
        temperature=0.0
    )
    
    print("Agent autonomous execution started...")
    
    while True:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=config
        )
        
        # Add assistant's response to history
        if response.candidates and response.candidates[0].content:
            messages.append(response.candidates[0].content)
        
        # Check if there are function calls requested
        function_calls = response.function_calls
        if not function_calls:
            if response.text:
                print(f"\n[Agent Final Response] {response.text}")
            break
            
        tool_responses = []
        for call in function_calls:
            name = call.name
            args = call.args
            
            # Print clean log of the tool execution
            print(f"\n[Tool Call] {name} called with arguments: {json.dumps(args)}")
            
            if name in tool_map:
                try:
                    result = tool_map[name](**args)
                    print(f"[Tool Response] {name} returned: {result}")
                    tool_responses.append(
                        types.Part.from_function_response(
                            name=name,
                            response={"result": result}
                        )
                    )
                except Exception as e:
                    print(f"[Tool Error] {name} failed: {e}")
                    tool_responses.append(
                        types.Part.from_function_response(
                            name=name,
                            response={"error": str(e)}
                        )
                    )
            else:
                print(f"[Tool Error] Unknown tool: {name}")
                tool_responses.append(
                    types.Part.from_function_response(
                        name=name,
                        response={"error": f"Unknown function: {name}"}
                    )
                )
                
        # Append the tool responses as a message from user role
        messages.append(
            types.Content(role="user", parts=tool_responses)
        )
