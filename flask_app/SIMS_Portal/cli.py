"""Custom `flask` CLI commands, e.g. `flask --app run.py update-member-locations`."""
import click


def init_cli(app):
	@app.cli.command('update-member-locations')
	def update_member_locations_command():
		"""Regenerate static/data/locations.json (the member globe) from user coordinates."""
		from SIMS_Portal.users.utils import update_member_locations
		update_member_locations()
		click.echo('Member locations updated.')
