from flask import url_for, current_app, flash, redirect
from SIMS_Portal import db
from SIMS_Portal.models import User, Assignment, Emergency, NationalSociety
from SIMS_Portal.users.utils import send_slack_dm
import logging

def request_learnings(dis_id):
    """
    Request learning feedback from remote IM support assignments for a given disaster.
    
    Queries the database for remote IM support assignments related to a specific disaster ID.
    It sends a Slack direct message to each user associated with these assignments, requesting them to provide
    learning feedback via a provided link.
    
    Parameters:
    dis_id (int): The ID of the disaster for which to request learning feedback.
    
    Returns:
    None
    
    Side Effects:
    - Sends Slack direct messages to users requesting feedback.
    - Logs errors to the current application's logger if any occur during message sending.
    
    Raises:
    None
    """
    
    emergency_remote_assignments = db.session.query(Assignment, Emergency, User).join(Emergency, Emergency.id == Assignment.emergency_id).join(User, User.id == Assignment.user_id).filter(Emergency.id == dis_id, Assignment.role == 'Remote IM Support').with_entities(Assignment.id, User.id, User.slack_id, User.firstname, Emergency.id, Emergency.emergency_name).all()
    
    # reference the tuples returned by sql, reference first result, then relevant keys
    emergency_name = emergency_remote_assignments[0][5]
    emergency_id = emergency_remote_assignments[0][4]
    
    for row in emergency_remote_assignments:
        try:
            assignment_id = row[0]
            user_id = row[1]
            user_slack = row[2]
            user_firstname = row[3]
            feedback_link = f"https://rcrcsims.org/learning/assignment/new/{user_id}/{assignment_id}"
            message = f"Hi {user_firstname}! As a remote supporter for {emergency_name}, you've been asked to provide a learning review of your experience. This is an opportunity to provide feedback about what worked and what could be improved, which helps the SIMS network learn and evolve. To submit your feedback, <{feedback_link}|please use this link>. Note that your written response is confidential and the results of quantitative questions will only be aggregated once a minimum number of submissions have been received. *Only one learning record can be submitted per assignment*, so if you have already filled this form out for this emergency, you're all set!"
            send_slack_dm(message, user_slack)
        except Exception as e:
            current_app.logger.error("request_learnings function failed: {}".format(e))