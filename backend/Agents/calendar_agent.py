import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# ✅ Add Calendar Scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_calendar():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def book_appointment(summary, description, start_time, end_time, timezone='America/Los_Angeles'):
    service = authenticate_calendar()
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': timezone},
        'end': {'dateTime': end_time, 'timeZone': timezone},
        'reminders': {'useDefault': True},
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"✅ Appointment booked: {created_event.get('htmlLink')}")
    return created_event

# 🧪 Example usage
if __name__ == "__main__":
    now = datetime.utcnow() + timedelta(hours=1)
    start = now.isoformat() + 'Z'
    end = (now + timedelta(minutes=30)).isoformat() + 'Z'
    
    book_appointment(
        summary="Teeth Cleaning",
        description="Annual dental cleaning appointment",
        start_time=start,
        end_time=end
    )
