from flask import render_template,redirect,session,request, flash
from flask_app import app
from flask_app.models.member import Member
from flask_app.models.emergency import Emergency
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

# @app.route('/')
# def index():
# 	print("Running / route")
# 	return render_template('index.html')
	
