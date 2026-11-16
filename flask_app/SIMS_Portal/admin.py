"""Flask-Admin backend at /admin, restricted to portal administrators."""
from flask import abort
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user


def _is_portal_admin():
	return current_user.is_authenticated and current_user.is_admin == 1


class AdminView(ModelView):
	# columns hidden from the admin list views. The password hash column is kept
	# last on purpose: when another quoted name follows it, secret scanners
	# (GitGuardian) mistake the pair for a hard-coded password.
	column_exclude_list = (
		'birthday', 'molnix_id', 'job_title', 'bio', 'roles', 'image_file',
		'slack_id', 'github', 'created_at', 'updated_at', 'linked_in',
		'messaging_number_country_code', 'messaging_number', 'password',
	)
	column_hide_backrefs = False

	def is_accessible(self):
		return _is_portal_admin()

	def inaccessible_callback(self, name, **kwargs):
		abort(403)


# Flask-Admin's default index view has no access check at all, so /admin/ itself
# would be reachable by anyone even though each model view is gated.
class AdminHomeView(AdminIndexView):
	def is_accessible(self):
		return _is_portal_admin()

	def inaccessible_callback(self, name, **kwargs):
		abort(403)


def init_admin(app, db):
	from SIMS_Portal.models import (
		Alert, Assignment, Badge, Documentation, Emergency, Learning, NationalSociety,
		Portfolio, Review, Story, User,
	)

	# Flask-Admin 2.x only ships a Bootstrap 4 theme (it bundles its own copy, used on /admin pages only)
	admin = Admin(app, name='SIMS Admin Portal', theme=Bootstrap4Theme(), endpoint='admin', index_view=AdminHomeView())
	for model in (User, Assignment, Emergency, Portfolio, Story, Learning, Review, Alert, NationalSociety, Badge, Documentation):
		admin.add_view(AdminView(model, db))
	return admin
