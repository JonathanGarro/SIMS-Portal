from flask import (
	request, render_template, url_for, flash, redirect,
	jsonify, Blueprint, current_app
)
from flask_login import (
	login_user, logout_user, current_user, login_required
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

from SIMS_Portal import db
from SIMS_Portal.config import Config
from SIMS_Portal.models import Learning, User, Emergency, Assignment
from SIMS_Portal.learnings.forms import NewAssignmentLearningForm
from SIMS_Portal.users.utils import send_slack_dm


learnings = Blueprint('learnings', __name__)

@learnings.route('/learning/assignment/new/<int:user_id>/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def create_new_assignment_learning(user_id, assignment_id):
	form = NewAssignmentLearningForm()
	check_for_record = db.session.query(Learning).filter(Learning.assignment_id==assignment_id).first()
	if check_for_record:
		flash('This assignment already has a learning record associated.', 'warning')
		redirect_url = '/assignment/{}'.format(assignment_id)
		return redirect(redirect_url)
	if current_user.id == user_id or current_user.is_admin == 1:
		user_info = db.session.query(User).filter(User.id==user_id).first()
		emergency_info = db.session.query(Emergency, Assignment).join(Assignment, Assignment.emergency_id==Emergency.id).filter(Assignment.id==assignment_id).first()
		if form.validate_on_submit():
			learning = Learning(
				assignment_id=assignment_id,
				overall_score=form.overall_score.data,
				overall_exp=form.overall_exp.data,
				got_support=form.got_support.data,
				internal_resource=form.internal_resource.data,
				external_resource=form.external_resource.data,
				clear_tasks=form.clear_tasks.data,
				field_communication=form.field_communication.data,
				clear_deadlines=form.clear_deadlines.data,
				coordination_tools=form.coordination_tools.data
			)
			db.session.add(learning)
			db.session.commit()
			user_info = db.session.query(User).filter(User.id == current_user.id).first()
			try:
				message = 'Hi {}, you have successfully shared your assignment review! The information you shared is not attributable to you, and only the SIMS Learning Focal Point has direct access to the data. Your responses will be aggregated once enough people have also contributed their own reviews, and will help the network learn and improve from our work.'.format(user_info.firstname)
				send_slack_dm(message, user_info.slack_id)
			# skip slack message if slack is down or user doesn't have slack ID filled in
			except:
				pass
			flash('New learning record successfully created. Thanks for your contribution!', 'success')
			redirect_url = '/assignment/{}'.format(assignment_id)
			return redirect(redirect_url)
		return render_template('learning_assignment.html', form=form, user_info=user_info, emergency_info=emergency_info)
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403