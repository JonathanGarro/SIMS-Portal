from flask import current_app
from SIMS_Portal import db
from datetime import datetime, timedelta
from slack_sdk import WebClient

def send_slack_availability_request(disaster_id, slack_channel):
    client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
    link = current_app.config['ROOT_URL'] + '/availability/report/' + str(disaster_id)
    try:
        result = client.chat_postMessage(
            channel = slack_channel,
            text = 'Hello, <!channel>! In order to help the SIMS Remote Coordinator ensure sufficient coverage for this operation, it is requested that you submit your availability for support. The reporting process involves simply checking off the days when you are volunteering to be ready to work on tasks that match your skill set. <{}|Click this link to report.>'.format(link)
        )
    except Exception as e:
        current_app.logger.error('send_slack_availability_request failed: {}'.format(e))

def get_dates_current_and_next_week():
    today = datetime.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    next_week_start = current_week_start + timedelta(days=7)
    
    dates = []
    for i in range(14):
        current_date = current_week_start + timedelta(days=i)
        if current_date >= today:
            dates.append(current_date)
    
    readable_dates = []
    for date in dates:
        readable_dates.append(f"{date.strftime('%A')}, {date.strftime('%B')} {date.day}")
        
    zip_dates = zip(dates,readable_dates)
    
    return zip_dates
    
def get_dates_current_week():
    today = datetime.today()
    current_weekday = today.weekday()
    days_in_week = 7
    
    remaining_days = days_in_week - current_weekday
    remaining_dates = []
    
    for i in range(remaining_days):
        date = today + timedelta(days=i)
        remaining_dates.append(date)
        
    readable_dates = []
    for date in remaining_dates:
        readable_dates.append(f"{date.strftime('%A')}, {date.strftime('%B')} {date.day}")
        
    return readable_dates

def get_dates_next_week():
    # Get today's date
    today = datetime.today()
    
    # Find the next Monday
    current_day = today.weekday()
    days_ahead = 0 if current_day == 6 else (7 - current_day)
    next_monday = today + timedelta(days=days_ahead)
    
    # Generate the list of next week's days starting from Monday
    next_week = [next_monday + timedelta(days=i) for i in range(7)]
    
    readable_dates = []
    for date in next_week:
        readable_dates.append(f"{date.strftime('%A')}, {date.strftime('%B')} {date.day}")
    
    return readable_dates