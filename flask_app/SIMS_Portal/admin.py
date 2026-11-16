"""Flask-Admin backend at /admin, restricted to portal administrators."""
from flask import abort
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.validators import Unique
from flask_admin.form.validators import FieldListInputRequired
from flask_login import current_user

# Flask-Admin 1.6.1 declares these validators' field_flags as tuples, but WTForms 3
# expects a dict, so every admin form with a unique column (e.g. Create User)
# crashed. Remove this shim when Flask-Admin is upgraded to 2.x (#158).
Unique.field_flags = {'unique': True}
FieldListInputRequired.field_flags = {'required': True}


def _is_portal_admin():
	return current_user.is_authenticated and current_user.is_admin == 1


class AdminView(ModelView):
	column_exclude_list = (
		'birthday', 'password', 'molnix_id', 'job_title', 'bio', 'roles', 'image_file', 'twitter',
		'slack_id', 'github', 'created_at', 'updated_at', 'linked_in',
		'messaging_number_country_code', 'messaging_number',
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

	admin = Admin(app, name='SIMS Admin Portal', template_mode='bootstrap4', endpoint='admin', index_view=AdminHomeView())
	for model in (User, Assignment, Emergency, Portfolio, Story, Learning, Review, Alert, NationalSociety, Badge, Documentation):
		admin.add_view(AdminView(model, db.session))
	return admin
