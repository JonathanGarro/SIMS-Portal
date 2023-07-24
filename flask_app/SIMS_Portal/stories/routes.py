import markdown
from markdown.extensions import Extension

from flask import (
	request, render_template, url_for, flash, redirect,
	jsonify, Blueprint, current_app
)
from flask_login import (
	login_user, logout_user, current_user, login_required
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, text

from SIMS_Portal import db
from SIMS_Portal.config import Config
from SIMS_Portal.models import (
	Story, Emergency, User, Assignment, Portfolio
)
from SIMS_Portal.stories.forms import (
	NewStoryForm, UpdateStoryForm
)
from SIMS_Portal.stories.utils import save_header, check_sims_co

stories = Blueprint('stories', __name__)

class HeadingClassExtension(Extension):
	def extendMarkdown(self, md):
		md.treeprocessors.register(HeadingClassProcessor(md), 'heading_class', 1)

class HeadingClassProcessor(markdown.treeprocessors.Treeprocessor):
		def run(self, root):
			for elem in root.iter():
				if elem.tag.startswith('h2') and len(elem.tag) == 2:
					elem.set('class', 'story_h2')
				elif elem.tag.startswith('h3') and len(elem.tag) == 2:
					elem.set('class', 'story_h3')

@stories.route('/story/<int:emergency_id>')
def view_story(emergency_id): 
	story_for_emergency = db.session.query(Story).filter(Story.emergency_id == emergency_id).first()
	if story_for_emergency:
		story_data = story_for_emergency
		emergency_name = db.session.query(Story, Emergency).join(Emergency, Emergency.id == emergency_id).first()
		members_supporting = db.session.query(Assignment, User, Story).join(User, User.id == Assignment.user_id).join(Story, Story.emergency_id == Assignment.emergency_id).filter(Assignment.emergency_id == emergency_id, Assignment.assignment_status == 'Active').count()
		member_days = db.engine.execute(text("SELECT id, (end_date-start_date) as day_count, emergency_id FROM assignment WHERE emergency_id = :id AND assignment.assignment_status = 'Active'"), {'id': emergency_id})
		try:
			sum_days = 0
			for day in member_days:
				sum_days += day[1]
			sum_days = int(sum_days)
		except:
			sum_days = 0
		products_created = db.session.query(Portfolio, Emergency).join(Emergency, Emergency.id == Portfolio.emergency_id).filter(Emergency.id == emergency_id, Portfolio.product_status == 'Approved').count()
		
		story_data_html = markdown.markdown(story_data.entry, extensions=[HeadingClassExtension()])
		
		return render_template('story.html', story_data_html=story_data_html, story_data=story_data, emergency_name=emergency_name, members_supporting=members_supporting, sum_days=sum_days, products_created=products_created)
	else:
		return render_template('errors/404.html'), 404

@stories.route('/story/create/<int:emergency_id>', methods=["GET", "POST"])
@login_required
def create_story(emergency_id): 
	form = NewStoryForm()
	check_existing = db.session.query(Story).filter(Story.emergency_id == emergency_id).all()
	if check_existing:
		flash('A story already exists for this emergency', 'danger')
		return redirect(url_for('emergencies.view_emergency', id=emergency_id))
	if current_user.is_admin == 0:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403
	if request.method == 'POST' and current_user.is_admin == 1:
		if form.validate_on_submit():
			if form.header_image.data:
				header_file = save_header(form.header_image.data)
			else:
				header_file = 'default-banner.png'
			story = Story(header_image=header_file, header_caption=form.header_caption.data, entry=form.entry.data, emergency_id=emergency_id)
			db.session.add(story)
			db.session.commit()
			flash('New story added!', 'success')
			return redirect(url_for('stories.view_story', emergency_id = emergency_id))
	else:
		emergency_name = db.session.query().with_entities(Emergency.emergency_name).filter(Emergency.id == emergency_id).first()
		return render_template('story_create.html', form=form, emergency_name=emergency_name)

@stories.route('/story/edit/<int:emergency_id>', methods=["GET", "POST"])
@login_required
def edit_story(emergency_id): 
	# check if user has permission to edit
	user_is_sims_co = check_sims_co(emergency_id)
	form = UpdateStoryForm()
	story = db.session.query(Story).filter(Story.emergency_id == emergency_id).first()
	if user_is_sims_co == False and current_user.is_admin == 0:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403
	elif request.method == 'POST' and (user_is_sims_co == True or current_user.id == 1):
		if form.header_image.data:
			header_file = save_header(form.header_image.data)
		else:
			header_file = story.header_image
		header_caption = form.header_caption.data
		story.header_image = header_file
		story.header_caption = header_caption 
		story.entry = form.entry.data
		db.session.commit()
		flash('The story has been updated', 'success')
		return redirect(url_for('stories.view_story', emergency_id=story.emergency_id))
	else:
		emergency_name = db.session.query().with_entities(Emergency.emergency_name).filter(Emergency.id == emergency_id).first()
		form.header_caption.data = story.header_caption
		form.entry.data = story.entry
		return render_template('story_edit.html', form=form, emergency_name=emergency_name, story=story)
	
@stories.route('/story/delete/<int:emergency_id>', methods=["GET", "POST"])
@login_required
def delete_story(emergency_id):
	if current_user.is_admin == 1:
		try:
			db.session.query(Story).filter(Story.emergency_id==emergency_id).delete()
			db.session.commit()
			flash("Story deleted.", 'success')
		except:
			flash("Error deleting emergency. Check that the emergency ID exists.", 'danger')
		return redirect(url_for('emergencies.view_emergency', id = emergency_id))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403
