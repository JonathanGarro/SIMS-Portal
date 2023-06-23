from SIMS_Portal import db
from datetime import datetime, timedelta

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
    today = datetime.date.today()
    next_week = today + datetime.timedelta(days=7)
    dates_next_week = []
    
    for i in range(7):
        date = next_week + datetime.timedelta(days=i)
        dates_next_week.append(date)
    
    return dates_next_week