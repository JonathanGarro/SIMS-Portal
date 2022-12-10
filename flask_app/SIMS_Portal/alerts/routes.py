from flask import request, render_template, url_for, flash, redirect, jsonify, Blueprint, current_app
from SIMS_Portal.models import Assignment, User, Emergency, Portfolio
from SIMS_Portal.users.utils import send_slack_dm
from SIMS_Portal import db, login_manager
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, current_user, logout_user, login_required
from SIMS_Portal.assignments.forms import NewAssignmentForm, UpdateAssignmentForm
from datetime import datetime
from datetime import date, timedelta
import pandas as pd

alerts = Blueprint('alerts', __name__)

