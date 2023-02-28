from SIMS_Portal import create_app
import os

app = create_app()

# set use_reloader to false when debugging to avoid duplicate cron job runs
if __name__ == '__main__':
	app.run(debug = True, use_reloader = True)