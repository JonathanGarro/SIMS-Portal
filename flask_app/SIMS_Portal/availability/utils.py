from flask import current_app
from SIMS_Portal.models import Emergency
from SIMS_Portal import db
from datetime import datetime, timedelta
from slack_sdk import WebClient

def send_slack_availability_request(disaster_id, slack_channel):
    """
    Sends an availability request message to a specified Slack channel for a given disaster event.
    
    Parameters:
    disaster_id (int): The unique identifier for the emergency in the db.
    slack_channel (str): The ID of the Slack channel where the request should be sent.
    
    Returns:
    None
    
    Raises:
    ValueError: If the disaster_id or slack_channel is invalid or empty.
    SlackAPIError: If there is an issue sending the message to Slack.
    
    Example:
    send_slack_availability_request(79, "C073DGZUUKZ")
    """
    
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
    """
    Generates a list of dates for the current week and the next week, starting from today.
    
    The function calculates the start of the current week (Monday) and the start of the next week,
    then generates a list of dates from the current week start to the end of the next week.
    Each date is formatted in a readable string format.
    
    Returns:
    List[Tuple[datetime.date, str]]: A list of tuples where each tuple contains a date object and
                                     its corresponding readable string format.
    
    Example:
    dates = get_dates_current_and_next_week()
    for date, readable in dates:
        print(f"Date: {date}, Readable: {readable}")
    
    Output:
    Date: 2024-05-20, Readable: Monday, May 20
    Date: 2024-05-21, Readable: Tuesday, May 21
    ...
    Date: 2024-06-02, Readable: Sunday, June 2
    """
    
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
    """
    Generates a list of readable date strings for the remaining days of the current week, starting from today.
    
    The function calculates the current day of the week and determines the remaining days in the week.
    It then generates a list of date objects for these remaining days and converts them into readable string formats.
    
    Returns:
    List[str]: A list of readable date strings for the remaining days of the current week.
    
    Example:
    dates = get_dates_current_week()
    for readable_date in dates:
        print(readable_date)
    
    Output:
    Monday, May 20
    Tuesday, May 21
    ...
    Sunday, May 26
    """
    
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
    """
    Get readable dates for the next week starting from the upcoming Monday.
    
    Calculates the dates for the next week, starting from the upcoming Monday, and returns a list of
    these dates in a readable string format.
    
    Parameters:
    None
    
    Returns:
    list: A list of strings representing the dates of the next week in the format "Day, Month Day".
    
    Side Effects:
    None
    
    Raises:
    None
    """
    
    today = datetime.today()
    
    # find the next Monday
    current_day = today.weekday()
    days_ahead = 1 if current_day == 6 else (7 - current_day)
    next_monday = today + timedelta(days=days_ahead)
    
    # create list of next week's days starting from Monday
    next_week = [next_monday + timedelta(days=i) for i in range(7)]
    
    readable_dates = []
    for date in next_week:
        readable_dates.append(f"{date.strftime('%A')}, {date.strftime('%B')} {date.day}")
    
    return readable_dates
    
def request_availability_updates():
    """
    Request availability updates for active disasters.
    
    This function queries the database for active disasters and sends a Slack availability request for each disaster.
    It logs the success or failure of each request.
    
    Parameters:
    None
    
    Returns:
    list: A list of active disaster objects.
    
    Side Effects:
    - Sends Slack availability requests for each active disaster.
    - Logs success and error messages.
    
    Raises:
    None
    """
    
    active_disasters = db.session.query(Emergency).filter(Emergency.emergency_status == 'Active').all()
    
    for disaster in active_disasters:
        try:
            send_slack_availability_request(disaster.id, disaster.slack_channel)
            current_app.logger.info("request_availability_updates function ran successfully for {}".format(disaster.emergency_name))
        except Exception as e: 
            current_app.logger.error('Badge Assignment via SIMS Remote Coordinator Failed: {}'.format(e))
   
    return active_disasters
