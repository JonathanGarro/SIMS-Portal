# Archived migrations

These are the original Alembic revisions, kept for reference only. Alembic loads
revisions from `migrations/versions/` and ignores this folder.

They could not build a database from scratch (#175):
`4c3c0ed64178_add_documentation.py` drops `workinggroup.focal_point_name`, a column
no earlier revision creates. They were replaced by
`versions/c02b8677c08a_baseline.py`, which creates the schema as it stood at
`c02b8677c08a` (the last revision here) and reuses that revision ID, so databases
already at `c02b8677c08a` keep upgrading normally.
