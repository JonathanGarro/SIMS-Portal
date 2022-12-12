from SIMS_Portal import create_app

app = create_app()

# turn off user_reloader to prevent duplicate cron jobs
if __name__ == '__main__':
	app.run(debug=True, use_reloader=False)