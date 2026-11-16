"""Baseline: the full schema as of revision c02b8677c08a

Revision ID: c02b8677c08a
Revises:
Create Date: 2026-11-16

The original history (now in migrations/archive/, kept for reference only)
could not build a database from scratch (#175). This migration replaces it: it
creates the schema exactly as it stood at c02b8677c08a, the last revision of
the old history, and deliberately reuses that revision ID, so databases already
at c02b8677c08a (production, existing dumps) continue upgrading normally without
re-stamping. Fresh databases start here.

Generated with `flask db migrate` against an empty database, plus the user.twitter
column that still existed at this point (it's dropped by 979dd9e82cb0).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c02b8677c08a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('alert',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('molnix_id', sa.Integer(), nullable=True),
    sa.Column('alert_record_created_at', sa.DateTime(), nullable=True),
    sa.Column('event', sa.String(), nullable=True),
    sa.Column('role_profile', sa.String(), nullable=True),
    sa.Column('rotation', sa.String(), nullable=True),
    sa.Column('modality', sa.String(), nullable=True),
    sa.Column('language_required', sa.String(), nullable=True),
    sa.Column('molnix_status', sa.String(), nullable=True),
    sa.Column('alert_status', sa.String(), nullable=True),
    sa.Column('opens', sa.DateTime(), nullable=True),
    sa.Column('start', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('sectors', sa.String(), nullable=True),
    sa.Column('role_tags', sa.String(), nullable=True),
    sa.Column('scope', sa.String(), nullable=True),
    sa.Column('im_filter', sa.Boolean(), nullable=True),
    sa.Column('iso3', sa.String(), nullable=True),
    sa.Column('country_name', sa.String(), nullable=True),
    sa.Column('disaster_type_id', sa.Integer(), nullable=True),
    sa.Column('disaster_type_name', sa.String(), nullable=True),
    sa.Column('disaster_go_id', sa.Integer(), nullable=True),
    sa.Column('ifrc_severity_level_display', sa.String(), nullable=True),
    sa.Column('alert_id', sa.Integer(), nullable=True),
    sa.Column('region_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('badge',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('badge_url', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('limited_edition', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('checklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_name', sa.String(), nullable=True),
    sa.Column('task_description', sa.String(), nullable=True),
    sa.Column('task_url', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('emergencytype',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('emergency_type_go_id', sa.Integer(), nullable=True),
    sa.Column('emergency_type_name', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('language',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message', sa.String(length=500), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('nationalsociety',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ns_name', sa.String(length=120), nullable=False),
    sa.Column('country_name', sa.String(length=120), nullable=False),
    sa.Column('ns_go_id', sa.Integer(), nullable=True),
    sa.Column('iso2', sa.String(length=2), nullable=True),
    sa.Column('iso3', sa.String(length=3), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ns_go_id')
    )
    op.create_table('profile',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('image', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('region',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('skill',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('category', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=True),
    sa.Column('repo', sa.String(length=100), nullable=True),
    sa.Column('name', sa.String(length=500), nullable=True),
    sa.Column('state', sa.String(length=10), nullable=True),
    sa.Column('created_by_gh', sa.String(length=100), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.Column('assignees_gh', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('date_added', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('date_modified', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('workinggroup',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wg_name', sa.String(), nullable=False),
    sa.Column('wg_description', sa.Text(), nullable=True),
    sa.Column('wg_url', sa.String(), nullable=True),
    sa.Column('wg_external', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('emergency',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('emergency_name', sa.String(length=100), nullable=False),
    sa.Column('emergency_status', sa.String(length=100), nullable=False),
    sa.Column('emergency_glide', sa.String(length=20), nullable=True),
    sa.Column('emergency_go_id', sa.Integer(), nullable=True),
    sa.Column('emergency_location_id', sa.Integer(), nullable=True),
    sa.Column('emergency_review_id', sa.Integer(), nullable=True),
    sa.Column('activation_details', sa.String(length=1000), nullable=True),
    sa.Column('slack_channel', sa.String(), nullable=True),
    sa.Column('dropbox_url', sa.String(), nullable=True),
    sa.Column('trello_url', sa.String(), nullable=True),
    sa.Column('github_repo', sa.String(), nullable=True),
    sa.Column('emergency_type_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['emergency_type_id'], ['emergencytype.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sub_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('checklist_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('task_url', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['checklist_id'], ['checklist.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('firstname', sa.String(length=40), nullable=False),
    sa.Column('lastname', sa.String(length=40), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('birthday', sa.Date(), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password', sa.String(length=60), nullable=False),
    sa.Column('molnix_id', sa.Integer(), nullable=True),
    sa.Column('job_title', sa.String(length=120), nullable=True),
    sa.Column('unit', sa.String(length=120), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('twitter', sa.String(length=120), nullable=True),  # dropped by 979dd9e82cb0
    sa.Column('roles', sa.String(length=1000), nullable=True),
    sa.Column('image_file', sa.String(length=200), nullable=False),
    sa.Column('slack_id', sa.String(length=120), nullable=True),
    sa.Column('github', sa.String(length=120), nullable=True),
    sa.Column('linked_in', sa.String(length=120), nullable=True),
    sa.Column('messaging_number_country_code', sa.Integer(), nullable=True),
    sa.Column('messaging_number', sa.BigInteger(), nullable=True),
    sa.Column('coordinates', sa.String(length=120), nullable=True),
    sa.Column('time_zone', sa.String(length=120), nullable=True),
    sa.Column('place_label', sa.String(length=120), nullable=True),
    sa.Column('private_profile', sa.Boolean(), nullable=True),
    sa.Column('ns_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['ns_id'], ['nationalsociety.ns_go_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('acronym',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('acronym_eng', sa.String(length=255), nullable=True),
    sa.Column('def_eng', sa.Text(), nullable=True),
    sa.Column('expl_eng', sa.Text(), nullable=True),
    sa.Column('acronym_esp', sa.String(length=255), nullable=True),
    sa.Column('def_esp', sa.Text(), nullable=True),
    sa.Column('expl_esp', sa.Text(), nullable=True),
    sa.Column('acronym_fra', sa.String(length=255), nullable=True),
    sa.Column('def_fra', sa.Text(), nullable=True),
    sa.Column('expl_fra', sa.Text(), nullable=True),
    sa.Column('relevant_link', sa.String(), nullable=True),
    sa.Column('anonymous_submitter_name', sa.String(), nullable=True),
    sa.Column('anonymous_submitter_email', sa.String(), nullable=True),
    sa.Column('scope', sa.Text(), nullable=True),
    sa.Column('field', sa.Text(), nullable=True),
    sa.Column('associated_ns', sa.Integer(), nullable=True),
    sa.Column('added_by', sa.Integer(), nullable=False),
    sa.Column('approved_by', sa.Integer(), nullable=True),
    sa.Column('date_added', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('date_modified', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['added_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['approved_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['associated_ns'], ['nationalsociety.ns_go_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('assignment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=100), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('remote', sa.Boolean(), nullable=True),
    sa.Column('assignment_details', sa.String(length=1000), nullable=True),
    sa.Column('assignment_status', sa.String(length=100), nullable=True),
    sa.Column('availability', sa.String(), nullable=True),
    sa.Column('hours', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('emergency_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['emergency_id'], ['emergency.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('assignment_checklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('emergency_id', sa.Integer(), nullable=True),
    sa.Column('checklist_id', sa.Integer(), nullable=True),
    sa.Column('task_completed', sa.Boolean(), nullable=True),
    sa.Column('task_completed_date', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['checklist_id'], ['checklist.id'], ),
    sa.ForeignKeyConstraint(['emergency_id'], ['emergency.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('availability',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timeframe', sa.String(), nullable=True),
    sa.Column('dates', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('emergency_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['emergency_id'], ['emergency.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('regional_focal_point',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('regional_id', sa.Integer(), nullable=False),
    sa.Column('focal_point_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['focal_point_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['regional_id'], ['region.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('review',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('recommended_action', sa.Text(), nullable=True),
    sa.Column('follow_up', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('emergency_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['emergency_id'], ['emergency.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('story',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('header_image', sa.String(), nullable=False),
    sa.Column('header_caption', sa.String(), nullable=False),
    sa.Column('entry', sa.Text(), nullable=True),
    sa.Column('emergency_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['emergency_id'], ['emergency.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_badge',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('badge_id', sa.Integer(), nullable=True),
    sa.Column('assigner_id', sa.Integer(), nullable=True),
    sa.Column('assigner_justify', sa.Text(), nullable=True),
    sa.Column('created_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['badge_id'], ['badge.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('user_language',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('language_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['language_id'], ['language.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('user_profile',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('profile_id', sa.Integer(), nullable=True),
    sa.Column('tier', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('user_skill',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('skill_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['skill_id'], ['skill.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('user_workinggroup',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('workinggroup_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['workinggroup_id'], ['workinggroup.id'], )
    )
    op.create_table('assignment_sub_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('assignment_checklist_id', sa.Integer(), nullable=False),
    sa.Column('sub_task_id', sa.Integer(), nullable=False),
    sa.Column('task_completed', sa.Boolean(), nullable=True),
    sa.Column('task_completed_date', sa.DateTime(), nullable=True),
    sa.Column('task_completed_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['assignment_checklist_id'], ['assignment_checklist.id'], ),
    sa.ForeignKeyConstraint(['sub_task_id'], ['sub_task.id'], ),
    sa.ForeignKeyConstraint(['task_completed_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('learning',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('overall_score', sa.Integer(), nullable=False),
    sa.Column('overall_exp', sa.String(), nullable=False),
    sa.Column('got_support', sa.Integer(), nullable=True),
    sa.Column('internal_resource', sa.Integer(), nullable=True),
    sa.Column('external_resource', sa.Integer(), nullable=True),
    sa.Column('field_communication', sa.Integer(), nullable=True),
    sa.Column('clear_tasks', sa.Integer(), nullable=True),
    sa.Column('clear_deadlines', sa.Integer(), nullable=True),
    sa.Column('coordination_tools', sa.Integer(), nullable=True),
    sa.Column('assignment_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assignment_id')
    )
    op.create_table('portfolio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('type', sa.String(length=100), nullable=False),
    sa.Column('format', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('product_status', sa.String(length=100), nullable=True),
    sa.Column('local_file', sa.String(length=100), nullable=False),
    sa.Column('image_file', sa.String(length=200), nullable=True),
    sa.Column('dropbox_file', sa.String(length=300), nullable=True),
    sa.Column('external', sa.Boolean(), nullable=True),
    sa.Column('collaborator_ids', sa.String(length=200), nullable=True),
    sa.Column('approver_id', sa.Integer(), nullable=True),
    sa.Column('approver_message', sa.Text(), nullable=True),
    sa.Column('km_article_id', sa.Integer(), nullable=True),
    sa.Column('learning_site_url', sa.String(length=1000), nullable=True),
    sa.Column('assignment_id', sa.Integer(), nullable=True),
    sa.Column('creator_id', sa.Integer(), nullable=False),
    sa.Column('emergency_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ),
    sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['emergency_id'], ['emergency.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('documentation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('article_name', sa.String(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('category', sa.String(), nullable=True),
    sa.Column('summary', sa.String(), nullable=True),
    sa.Column('featured', sa.Boolean(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('portfolio_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['portfolio_id'], ['portfolio.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('documentation')
    op.drop_table('portfolio')
    op.drop_table('learning')
    op.drop_table('assignment_sub_task')
    op.drop_table('user_workinggroup')
    op.drop_table('user_skill')
    op.drop_table('user_profile')
    op.drop_table('user_language')
    op.drop_table('user_badge')
    op.drop_table('story')
    op.drop_table('review')
    op.drop_table('regional_focal_point')
    op.drop_table('availability')
    op.drop_table('assignment_checklist')
    op.drop_table('assignment')
    op.drop_table('acronym')
    op.drop_table('user')
    op.drop_table('sub_task')
    op.drop_table('emergency')
    op.drop_table('workinggroup')
    op.drop_table('task')
    op.drop_table('skill')
    op.drop_table('region')
    op.drop_table('profile')
    op.drop_table('nationalsociety')
    op.drop_table('log')
    op.drop_table('language')
    op.drop_table('emergencytype')
    op.drop_table('checklist')
    op.drop_table('badge')
    op.drop_table('alert')
