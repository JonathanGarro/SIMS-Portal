from flask import current_app
from sqlalchemy import select

from SIMS_Portal import db
from SIMS_Portal.models import Badge, User, user_badge


def award_badge(user_id, badge_id, assigner, justification):
	"""
	Give a member a badge and DM them about it. Returns False (and changes nothing)
	if they already have it. Called directly from the POST handlers that validate the
	assignment form; this used to happen in GET routes the forms redirected to, which
	took the assigner from the URL and could be re-run by refreshing.
	"""
	already_has = db.session.execute(
		select(user_badge.c.user_id).where(user_badge.c.user_id == user_id, user_badge.c.badge_id == badge_id)
	).first()
	if already_has:
		return False

	db.session.execute(user_badge.insert().values(
		user_id=user_id, badge_id=badge_id, assigner_id=assigner.id, assigner_justify=justification
	))
	db.session.commit()

	try:
		from SIMS_Portal.users.utils import send_slack_dm
		receiver = db.session.get(User, user_id)
		badge = db.session.get(Badge, badge_id)
		message = 'Hi {}, you have been assigned a new badge on the SIMS Portal! {} has given you the {} badge with the following message: {}'.format(
			receiver.firstname, assigner.fullname, badge.name, justification)
		if receiver.slack_id:
			send_slack_dm(message, receiver.slack_id)
	except Exception as e:
		current_app.logger.error(f'Badge {badge_id} assigned to user {user_id}, but the Slack DM failed: {e}')
	current_app.logger.info(f'Badge {badge_id} assigned to user {user_id} by user {assigner.id}')
	return True
