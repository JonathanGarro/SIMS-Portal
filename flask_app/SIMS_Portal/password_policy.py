"""
Password length policy (16+ characters, per an IT/compliance request).

Passwords are stored as bcrypt hashes, so existing members' password lengths are
unknown. Each account carries a `password_compliant` flag instead: it starts False
for accounts created before the policy, and is set True when the member registers,
resets or changes their password, or logs in with one that is already long enough.

Until then, every page request from a logged-in, non-compliant member is redirected
to the change-password page. This runs on every request (not just at login) so it
also catches members who stay signed in through a "remember me" cookie.

While PASSWORD_UPGRADE_DEADLINE is set and hasn't passed, the page offers a
"Remind me later" button that skips the redirect for the rest of the browser session.
"""
from datetime import date
from urllib.parse import urlsplit

from flask import current_app, redirect, request, session, url_for
from flask_login import current_user

MIN_PASSWORD_LENGTH = 16
# bcrypt only uses the first 72 bytes of a password; 64 characters stays under that
# for anything but heavy use of multi-byte characters.
MAX_PASSWORD_LENGTH = 64

SKIP_SESSION_KEY = 'password_upgrade_skipped'

# endpoints a non-compliant member can still reach
EXEMPT_ENDPOINTS = {
	'static',
	'health_check',
	'users.change_password',
	'users.skip_password_upgrade',
	'users.logout',
}


def meets_policy(password):
	return MIN_PASSWORD_LENGTH <= len(password or '') <= MAX_PASSWORD_LENGTH


def upgrade_deadline():
	"""The configured last day to skip, or None if unset or malformed."""
	value = current_app.config.get('PASSWORD_UPGRADE_DEADLINE')
	if not value:
		return None
	try:
		return date.fromisoformat(str(value))
	except ValueError:
		current_app.logger.warning('Ignoring malformed PASSWORD_UPGRADE_DEADLINE %r', value)
		return None


def can_skip_upgrade():
	deadline = upgrade_deadline()
	return deadline is not None and date.today() <= deadline


def safe_next_url(target):
	"""Return `target` only if it's a path on this site, so ?next= can't redirect off-site."""
	if not target:
		return None
	parts = urlsplit(target)
	if parts.scheme or parts.netloc or not target.startswith('/') or target.startswith('//') or '\\' in target:
		return None
	return target


def init_password_policy(app):
	@app.before_request
	def require_compliant_password():
		if not current_user.is_authenticated or current_user.password_compliant:
			return None
		if request.endpoint is None or request.endpoint in EXEMPT_ENDPOINTS:
			return None
		if session.get(SKIP_SESSION_KEY) and can_skip_upgrade():
			return None
		next_url = request.full_path if request.method == 'GET' else None
		if next_url and next_url.endswith('?'):
			next_url = next_url[:-1]
		return redirect(url_for('users.change_password', next=next_url))
