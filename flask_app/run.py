from SIMS_Portal import create_app
import os

app = create_app()

# set use_reloader to false when debugging to avoid duplicate cron job runs
if __name__ == '__main__':
	app.run(debug = False, use_reloader = False)
	
# port = int(os.environ.get("PORT", 5000))
# app.run(host='0.0.0.0', port=port)