from langchain_community.agent_toolkits import GoogleCalendarToolkit
from langchain_community.tools.google_calendar.utils import (
    build_resource_service,
    get_calendar_credentials,
)
from datetime import datetime, timedelta

def get_gcal_toolkit():
    # This requires credentials to be set up.
    # The user will need to follow instructions to set up Google Cloud credentials
    # and authorize the application.
    # For now, we'll just return the toolkit.
    return GoogleCalendarToolkit()

def create_event(user_id, title, description, start_time, end_time=None):
    credentials = get_calendar_credentials()
    service = build_resource_service(credentials)

    if start_time == "now":
        start = datetime.utcnow()
    else:
        start = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")

    if end_time:
        end = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
    else:
        end = start + timedelta(hours=1)

    event = {
        'summary': title,
        'description': description,
        'start': {
            'dateTime': start.isoformat() + 'Z',
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end.isoformat() + 'Z',
            'timeZone': 'UTC',
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    return event


def get_events(user_id, time_min=None, time_max=None):
    credentials = get_calendar_credentials()
    service = build_resource_service(credentials)

    if not time_min:
        time_min = datetime.utcnow().isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', [])
