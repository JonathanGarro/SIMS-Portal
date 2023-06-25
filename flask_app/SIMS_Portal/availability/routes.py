from flask import request, render_template, url_for, flash, redirect, jsonify, Blueprint, current_app
from flask_login import login_required, current_user
from SIMS_Portal.availability.utils import get_dates_current_and_next_week, get_dates_current_week, get_dates_next_week
from SIMS_Portal import db
from SIMS_Portal.models import Availability, Emergency, User
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text, insert
from datetime import datetime

availability = Blueprint('availability', __name__)

@availability.route('/availability/view/<int:user_id>/<int:emergency_id>')
@login_required
def view_availability(user_id, emergency_id):
    user_info = db.session.query(User).filter(User.id == user_id).first()
    emergency_info = db.session.query(Emergency).filter(Emergency.id == emergency_id).first()
    available_dates = db.session.query(Availability).filter(Availability.user_id == user_id, Availability.emergency_id == emergency_id).all()
    
    today = datetime.today().year
    week_number = datetime.today().isocalendar()[1]
    this_week = f"{today}-{week_number}"
    next_week = f"{today}-{week_number + 1}"
    
    this_week_dates = db.session.query(Availability.dates).filter(Availability.user_id == user_info.id, Availability.emergency_id == emergency_id, Availability.timeframe == this_week).all()

    next_week_dates = db.session.query(Availability.dates).filter(Availability.user_id == user_info.id, Availability.emergency_id == emergency_id, Availability.timeframe == next_week).all()
    
    merged_dates = []
    
    for item in this_week_dates:
        inner_list = eval(item[0])
        merged_dates.extend(inner_list)
        
    for item in next_week_dates:
        inner_list = eval(item[0])
        merged_dates.extend(inner_list)
    
    available_dates = []
    
    # convert date strings to proper format for calendar visualization
    for date in merged_dates:
        datetime_obj = datetime.strptime(date, '%A, %B %d')
        formatted_date = datetime_obj.strftime('{}-%m-%d').format(today)
        available_dates.append(formatted_date)
        
    return render_template('availability_view.html', user_info=user_info, emergency_info=emergency_info, available_dates=available_dates)


@availability.route('/availability/report/<int:disaster_id>', methods=['GET', 'POST'])
@login_required
def report_availability(disaster_id):
    disaster_info = db.session.query(Emergency).filter(Emergency.id == disaster_id).first()
    readable_dates = get_dates_current_week()
    report_type = 'current_week'
    return render_template('/assignment_availability.html', readable_dates=readable_dates, disaster_info=disaster_info, report_type=report_type)

@availability.route('/availability/report/next_week/<int:disaster_id>', methods=['GET', 'POST'])
@login_required
def report_availability_next_week(disaster_id):
    disaster_info = db.session.query(Emergency).filter(Emergency.id == disaster_id).first()
    readable_dates = get_dates_next_week()
    report_type = 'next_week'
    return render_template('/assignment_availability.html', readable_dates=readable_dates, disaster_info=disaster_info, report_type=report_type)
    
@availability.route('/availability/result/<int:disaster_id>', methods=['GET', 'POST'])
@login_required
def availability_result(disaster_id):
    user_info = db.session.query(User).filter(User.id == current_user.id).first()
    response = request.form.getlist('available')
    response_formatted = "{}".format(response)
    
    # create year-week_number stamp to establish timeframe
    week_number = datetime.today().isocalendar()[1]
    year = datetime.today().year
    timeframe = f"{year}-{week_number}"
    
    existing_user_availability_this_week = db.session.query(Availability).filter(Availability.user_id == current_user.id, Availability.emergency_id == disaster_id, Availability.timeframe == timeframe).first()
    
    # delete existing record for this timeframe if exists
    if existing_user_availability_this_week:
        db.session.delete(existing_user_availability_this_week)
        db.session.commit()
        
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
    
    return redirect(url_for('availability.view_availability', user_id=user_info.id, emergency_id=disaster_id))
    
@availability.route('/availability/result/next_week/<int:disaster_id>', methods=['GET', 'POST'])
@login_required
def availability_result_next_week(disaster_id):
    user_info = db.session.query(User).filter(User.id == current_user.id).first()
    response = request.form.getlist('available')
    response_formatted = "{}".format(response)
    
    # create year-week_number stamp to establish timeframe
    week_number = datetime.today().isocalendar()[1]
    year = datetime.today().year
    week_number += 1
    timeframe = f"{year}-{week_number}"
    
    existing_user_availability_next_week = db.session.query(Availability).filter(Availability.user_id == current_user.id, Availability.emergency_id == disaster_id, Availability.timeframe == timeframe).first()
    
    # delete existing record for next timeframe if exists
    if existing_user_availability_next_week:
        db.session.delete(existing_user_availability_next_week)
        db.session.commit()
    
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
    
    return redirect(url_for('availability.view_availability', user_id=user_info.id, emergency_id=disaster_id))