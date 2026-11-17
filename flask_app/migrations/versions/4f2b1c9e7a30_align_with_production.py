"""Align with production: log.message TEXT, log.log_type + its trigger, reporting views, region.name NOT NULL

Revision ID: 4f2b1c9e7a30
Revises: c02b8677c08a
Create Date: 2026-11-17

Production's schema had drifted from the models (#175 follow-up). This brings fresh
databases to production's shape for the parts production got right, and is safe to
run on production after `flask reconcile-production-schema` (every step is
idempotent: it checks before altering, and uses CREATE OR REPLACE / IF NOT EXISTS).

- log.message: TEXT (production's type; the model said String(500) but production
  has longer messages). Only altered when it isn't already text, because the
  reporting views below depend on the column and Postgres refuses to alter it then.
- log.log_type + the before_insert_update_log_type trigger that fills it from the
  message's leading [TAG], exactly as in production
- the latest_logins / no_logins_180_days / no_logins_194_days reporting views, as
  defined in production
- region.name NOT NULL (as in production; no rows are null)
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '4f2b1c9e7a30'
down_revision = 'c02b8677c08a'
branch_labels = None
depends_on = None

UPDATE_LOG_TYPE_FUNCTION = """
CREATE OR REPLACE FUNCTION public.update_log_type() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.log_type = CASE
                  WHEN POSITION('[' IN NEW.message) > 0 AND POSITION(']' IN NEW.message) > POSITION('[' IN NEW.message)
                  THEN SUBSTRING(NEW.message FROM POSITION('[' IN NEW.message) + 1 FOR POSITION(']' IN NEW.message) - POSITION('[' IN NEW.message) - 1)
                  ELSE NULL 
               END;
  RETURN NEW;
END;
$$;
"""

LOG_TYPE_TRIGGER = """
CREATE TRIGGER before_insert_update_log_type BEFORE INSERT ON public.log FOR EACH ROW EXECUTE FUNCTION public.update_log_type();
"""

VIEWS = {
	'latest_logins': """
CREATE OR REPLACE VIEW public.latest_logins AS
 WITH latestlogins AS (
         SELECT l."timestamp",
            concat(u.firstname, ' ', u.lastname) AS member,
            l.message,
            u.slack_id,
            row_number() OVER (PARTITION BY u.id ORDER BY l."timestamp" DESC) AS rn
           FROM (public.log l
             JOIN public."user" u ON ((u.id = l.user_id)))
          WHERE (l.message ~~ '%logged in%'::text)
        )
 SELECT latestlogins."timestamp",
    latestlogins.member,
    latestlogins.message,
    latestlogins.slack_id
   FROM latestlogins
  WHERE (latestlogins.rn = 1)
  ORDER BY latestlogins."timestamp" DESC;
""",
	'no_logins_180_days': """
CREATE OR REPLACE VIEW public.no_logins_180_days AS
 WITH subquery AS (
         SELECT log_1.user_id,
            max(log_1."timestamp") AS max_timestamp
           FROM public.log log_1
          WHERE (log_1.message ~~ '%logged in%'::text)
          GROUP BY log_1.user_id
        )
 SELECT log.user_id,
    log."timestamp",
    log.message,
    "user".firstname,
    "user".lastname,
    "user".slack_id
   FROM ((public.log log
     JOIN public."user" "user" ON (("user".id = log.user_id)))
     JOIN subquery ON (((log.user_id = subquery.user_id) AND (log."timestamp" = subquery.max_timestamp))))
  WHERE ((log."timestamp" < (CURRENT_TIMESTAMP - '180 days'::interval)) AND (("user".status)::text = 'Active'::text));
""",
	'no_logins_194_days': """
CREATE OR REPLACE VIEW public.no_logins_194_days AS
 WITH subquery AS (
         SELECT log_1.user_id,
            max(log_1."timestamp") AS max_timestamp
           FROM public.log log_1
          WHERE (log_1.message ~~ '%logged in%'::text)
          GROUP BY log_1.user_id
        )
 SELECT log.user_id,
    log."timestamp",
    log.message,
    "user".firstname,
    "user".lastname,
    "user".slack_id
   FROM ((public.log log
     JOIN public."user" "user" ON (("user".id = log.user_id)))
     JOIN subquery ON (((log.user_id = subquery.user_id) AND (log."timestamp" = subquery.max_timestamp))))
  WHERE ((log."timestamp" < (CURRENT_TIMESTAMP - '194 days'::interval)) AND (("user".status)::text = 'Active'::text));
""",
}


def upgrade():
	op.execute("""
DO $$
BEGIN
	IF (SELECT data_type FROM information_schema.columns
	    WHERE table_schema = 'public' AND table_name = 'log' AND column_name = 'message') <> 'text' THEN
		ALTER TABLE public.log ALTER COLUMN message TYPE TEXT;
	END IF;
END $$;
""")
	op.execute('ALTER TABLE public.log ADD COLUMN IF NOT EXISTS log_type VARCHAR(50)')
	op.execute(UPDATE_LOG_TYPE_FUNCTION)
	op.execute('DROP TRIGGER IF EXISTS before_insert_update_log_type ON public.log')
	op.execute(LOG_TYPE_TRIGGER)
	for definition in VIEWS.values():
		op.execute(definition)
	op.execute('ALTER TABLE public.region ALTER COLUMN name SET NOT NULL')


def downgrade():
	op.execute('ALTER TABLE public.region ALTER COLUMN name DROP NOT NULL')
	for name in VIEWS:
		op.execute(f'DROP VIEW IF EXISTS public.{name}')
	op.execute('DROP TRIGGER IF EXISTS before_insert_update_log_type ON public.log')
	op.execute('DROP FUNCTION IF EXISTS public.update_log_type()')
	op.execute('ALTER TABLE public.log DROP COLUMN IF EXISTS log_type')
	op.execute('ALTER TABLE public.log ALTER COLUMN message TYPE VARCHAR(500)')
