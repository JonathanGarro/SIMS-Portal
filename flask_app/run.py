from SIMS_Portal import create_app
import os

app = create_app()
app.app_context().push()