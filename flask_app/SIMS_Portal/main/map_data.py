"""
Data for the d3 maps, computed from the database on request.

This used to be written to files under static/data/ (emergencies_viz.csv,
locations.json) by functions run on certain events. Those files lived inside the
deployed code, so every redeploy reset them to the stale copies committed to git
(#24). Serving the data from cached endpoints keeps the maps current without
regeneration and keeps the app from writing into its own code directory.

The endpoints are cached briefly. Code that changes the underlying data calls the
invalidate_* helpers; with the simple (per-process) cache that clears the worker
handling the change, and the others catch up within CACHE_SECONDS.
"""
from flask import current_app
from sqlalchemy import text

from SIMS_Portal import cache, db
from SIMS_Portal.models import User

CACHE_SECONDS = 15 * 60
RESPONSE_HISTORY_CACHE_KEY = 'map_data/response_history'
MEMBER_LOCATIONS_CACHE_KEY = 'map_data/member_locations'


def response_history():
	"""Number of SIMS emergencies per country, keyed by ISO3 (the about page map)."""
	rows = db.session.execute(text(
		'SELECT iso3, count(*) AS count FROM nationalsociety '
		'JOIN emergency ON emergency_location_id = nationalsociety.ns_go_id GROUP BY iso3'
	))
	return [{'iso3': row.iso3, 'count': row.count} for row in rows]


def member_locations():
	"""Coordinates of every member who has saved a location (the homepage globe)."""
	locations = []
	for user_id, coordinates in db.session.query(User.id, User.coordinates).filter(User.coordinates.isnot(None)):
		parts = coordinates.replace('[', '').replace(']', '').split(', ')
		try:
			latitude, longitude = float(parts[0]), float(parts[1])
		except (ValueError, IndexError):
			current_app.logger.warning(f'Skipping user {user_id} with malformed coordinates: {coordinates!r}')
			continue
		locations.append({'latitude': latitude, 'longitude': longitude})
	return locations


def invalidate_response_history():
	cache.delete(RESPONSE_HISTORY_CACHE_KEY)


def invalidate_member_locations():
	cache.delete(MEMBER_LOCATIONS_CACHE_KEY)
