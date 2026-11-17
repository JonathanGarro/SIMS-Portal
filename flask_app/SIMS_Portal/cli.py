"""Custom `flask` CLI commands, e.g. `flask --app run.py reconcile-production-schema`."""
import click
from sqlalchemy import inspect, text

# The production database never ran the 2025 checklist migrations: it was still at
# this revision from October 2023 when the migration history was replaced by a
# baseline (#175). The baseline (c02b8677c08a) is the schema those migrations would
# have produced, so production has to be brought to that shape before Alembic can
# take over again.
LEGACY_PRODUCTION_REVISION = '1f05ced78d0d'
BASELINE_REVISION = 'c02b8677c08a'

CHECKLIST_TABLES = ('checklist', 'sub_task', 'assignment_checklist', 'assignment_sub_task')
ACRONYM_TEXT_COLUMNS = ('def_eng', 'expl_eng', 'def_esp', 'expl_esp', 'def_fra', 'expl_fra')


def init_cli(app):
	@app.cli.command('reconcile-production-schema')
	@click.option('--dry-run', is_flag=True, help='Show what would change without changing anything.')
	def reconcile_production_schema(dry_run):
		"""
		One-off: bring a database still at the legacy production revision (1f05ced78d0d)
		to the baseline schema (c02b8677c08a), then stamp it there. Afterwards run
		`flask db upgrade` as usual. Everything happens in one transaction; it refuses to
		run against a database at any other revision.
		"""
		from SIMS_Portal import db
		from SIMS_Portal import models

		with db.engine.connect() as conn:
			current = conn.execute(text('SELECT version_num FROM alembic_version')).scalar()
		if current != LEGACY_PRODUCTION_REVISION:
			raise click.ClickException(
				f'Database is at revision {current!r}, not {LEGACY_PRODUCTION_REVISION!r}; '
				'nothing to reconcile (use `flask db upgrade`).')

		inspector = inspect(db.engine)
		existing_tables = set(inspector.get_table_names())
		missing_tables = [t for t in CHECKLIST_TABLES if t not in existing_tables]
		acronym_columns = {c['name']: c for c in inspector.get_columns('acronym')}
		varchar_columns = [c for c in ACRONYM_TEXT_COLUMNS if str(acronym_columns[c]['type']).upper().startswith('VARCHAR')]
		added_by_nullable = acronym_columns['added_by']['nullable']

		plan = [f'create table {t}' for t in missing_tables]
		plan += [f'acronym.{c}: VARCHAR -> TEXT' for c in varchar_columns]
		if added_by_nullable:
			plan.append('acronym.added_by: set NOT NULL')
		plan.append(f'stamp revision {LEGACY_PRODUCTION_REVISION} -> {BASELINE_REVISION}')
		for step in plan:
			click.echo(f'  - {step}')
		if dry_run:
			click.echo('Dry run: nothing changed.')
			return

		with db.engine.begin() as conn:
			if added_by_nullable:
				nulls = conn.execute(text('SELECT count(*) FROM acronym WHERE added_by IS NULL')).scalar()
				if nulls:
					raise click.ClickException(f'{nulls} acronyms have no added_by; fix them before reconciling.')
			# create the checklist tables from the models, in dependency order
			tables = [models.db.metadata.tables[t] for t in CHECKLIST_TABLES if t in missing_tables]
			models.db.metadata.create_all(conn, tables=tables, checkfirst=True)
			for column in varchar_columns:
				conn.execute(text(f'ALTER TABLE acronym ALTER COLUMN {column} TYPE TEXT'))
			if added_by_nullable:
				conn.execute(text('ALTER TABLE acronym ALTER COLUMN added_by SET NOT NULL'))
			conn.execute(text('UPDATE alembic_version SET version_num = :rev'), {'rev': BASELINE_REVISION})
		click.echo(f'Reconciled and stamped at {BASELINE_REVISION}. Next: `flask db upgrade`.')
