from flask_app.controllers import emergencies, members, national_societies, assignments
from flask_app import app

if __name__=="__main__":
	app.run(debug=True)