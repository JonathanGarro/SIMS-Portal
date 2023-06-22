from flask import request, render_template, url_for, flash, redirect, jsonify, Blueprint, current_app
from flask_login import login_required, current_user
from SIMS_Portal.availability.utils import get_dates_current_and_next_week, get_dates_current_week
from SIMS_Portal import db
from SIMS_Portal.models import Availability, Emergency, User
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text, insert
from datetime import datetime

availability = Blueprint('availability', __name__)

@availability.route('/availability/report/<int:disaster_id>', methods=['GET', 'POST'])
@login_required
def report_availability(disaster_id):
    disaster_info = db.session.query(Emergency).filter(Emergency.id == disaster_id).first()
    
    # get current weekday number
    day_number = datetime.now().isoweekday()
    # if later than Thursday, ask for availability for remainder of week plus next
    if day_number > 4:
        date_list = get_dates_current_and_next_week()
        datetimes, readable_dates = zip(*date_list)

        return render_template('/assignment_availability.html', datetimes=datetimes, readable_dates=readable_dates, disaster_info=disaster_info, day_number=day_number)
    
    # otherwise, only show the days of the current week
    else:
        readable_dates = get_dates_current_week()
        
        return render_template('/assignment_availability.html', readable_dates=readable_dates, disaster_info=disaster_info, day_number=day_number)
    
    
@availability.route('/availability/result/<int:disaster_id>', methods=['GET', 'POST'])
@login_required
def availability_result(disaster_id):
    response = request.form.getlist('available')
    response_formatted = "{}".format(response)
    availability_id = request.form.get('availability_id')
    user_info = db.session.query(User).filter(User.id == current_user.id).first()
    
    # add year-week_number stamp to help establish timeframe
    week_number = datetime.today().isocalendar()[1]
    year = datetime.today().year
    timeframe = f"{year}-{week_number}"
    
    availability = Availability(dates=response_formatted, user_id=current_user.id, emergency_id=disaster_id, timeframe=timeframe)
    db.session.add(availability)
    db.session.commit()
    
    flash('Thank you for updating your availability for this emergency!', 'success')
    
    # try sending message if user has slack ID filled in
    try:
        message = 'Hi {}, you have successfully updated your availability!'.format(user_info.firstname)
        send_slack_dm(message, user_info.slack_id)
    except:
        pass
    
    return redirect(url_for('emergencies.view_emergency', id=disaster_id))