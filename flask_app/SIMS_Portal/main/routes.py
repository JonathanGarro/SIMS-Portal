import io
from datetime import datetime, timedelta

from flask import (
	abort, render_template, jsonify, Blueprint, current_app, send_file
)
from flask_login import (
	login_required
)
from sqlalchemy import func, distinct, desc, text
import boto3
import botocore

from SIMS_Portal import cache, db
from SIMS_Portal.main import map_data
from SIMS_Portal.models import (
	Assignment, User, Emergency, Alert, Portfolio,
	NationalSociety, Story,
	EmergencyType, RegionalFocalPoint, Region
)
from SIMS_Portal.main.utils import (
	fetch_slack_channels, user_info_by_ns
)


main = Blueprint('main', __name__)

@main.route('/')
def index():
	latest_stories = db.session.query(Story, Emergency).join(Emergency, Emergency.id == Story.emergency_id).order_by(Story.id.desc()).limit(3).all()
	return render_template('index.html', latest_stories=latest_stories)

@main.route('/about')
def about():
	count_activations = db.session.query(Emergency).count()
	all_activations = db.session.query(Emergency).all()
	lateset_activation = db.session.query(Emergency).order_by(Emergency.created_at.desc()).filter(Emergency.emergency_status != 'Removed').first()
	count_members = db.session.query(User).filter(User.status == 'Active').count()
	return render_template('about.html', count_activations=count_activations, latest_activation=lateset_activation, count_members=count_members, all_activations=all_activations)

@main.route('/portal_admins')
def portal_admins():
	list_admins = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.is_admin == True).all()
	return render_template('portal_admins.html', title='Portal Admins', list_admins=list_admins)

@main.route('/get_slack_id')
def get_slack_id():
	return render_template('slack-id-how-to.html')


@main.route('/privacy')
def privacy_policy():
	return render_template('privacy_policy.html')

@main.route('/resources')
def resources():
	return render_template('resources/resources.html')

@main.route('/resources/slack/channels')
@login_required
def resources_slack_channels():
	output = fetch_slack_channels()
	return render_template('resources/slack_channels.html', output=output)

@main.route('/dashboard')
@login_required
def dashboard():
	active_emergencies = db.session.query(Emergency, NationalSociety, EmergencyType).join(NationalSociety, NationalSociety.ns_go_id == Emergency.emergency_location_id).join(EmergencyType, EmergencyType.emergency_type_go_id == Emergency.emergency_type_id).filter(Emergency.emergency_status == 'Active').all()

	count_active_emergencies = db.session.query(Emergency, NationalSociety, EmergencyType).join(NationalSociety, NationalSociety.ns_go_id == Emergency.emergency_location_id).join(EmergencyType, EmergencyType.emergency_type_go_id == Emergency.emergency_type_id).filter(Emergency.emergency_status == 'Active').count()

	regional_im_leads = db.session.query(RegionalFocalPoint, Region, User).join(Region, Region.id == RegionalFocalPoint.regional_id).join(User, User.id == RegionalFocalPoint.focal_point_id).all()

	todays_date = datetime.today()

	assignments_by_emergency = db.session.query(Emergency.emergency_name, func.count()).\
	join(Assignment, Assignment.emergency_id == Emergency.id).\
	filter(Assignment.assignment_status != 'Removed').\
	group_by(Emergency.emergency_name).all()

	data_dict_assignments = [{'emergency_name': name, 'count_assignments': count} for name, count in assignments_by_emergency]
	labels_for_assignment = [row['emergency_name'] for row in data_dict_assignments]
	values_for_assignment = [row['count_assignments'] for row in data_dict_assignments]

	pending_user_check = db.session.query(User).filter(User.status == 'Pending').all()

	products_by_emergency = db.session.query(Emergency.emergency_name, func.count()).\
		join(Portfolio, Portfolio.emergency_id == Emergency.id).\
		filter(Portfolio.product_status != 'Removed').\
		group_by(Emergency.emergency_name).all()

	data_dict_products = [{'emergency_name': name, 'count_products': count} for name, count in products_by_emergency]
	labels_for_product = [row['emergency_name'] for row in data_dict_products]
	values_for_product = [row['count_products'] for row in data_dict_products]

	count_active_assignments = db.session.query(Assignment, User, Emergency).join(User, User.id==Assignment.user_id).join(Emergency, Emergency.id==Assignment.emergency_id).filter(Assignment.assignment_status=='Active', Assignment.end_date>todays_date).count()

	active_assignments = db.session.query(Assignment, User, Emergency, NationalSociety).join(User, User.id==Assignment.user_id).join(Emergency, Emergency.id==Assignment.emergency_id).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(Assignment.assignment_status=='Active', Assignment.role != 'Remote IM Support', Assignment.end_date>todays_date).order_by(Emergency.emergency_name, Assignment.end_date).all()

	count_active_remote_supporters = db.session.query(func.count()).select_from(Emergency).join(Assignment).filter(
		Emergency.emergency_status == 'Active',
		Assignment.assignment_status != 'Removed'
	).scalar()

	# every open surge alert from the last 90 days; the dashboard counts and shows
	# Information Management ones by default, with a switch to show them all
	ninety_days_ago = datetime.now() - timedelta(days=90)
	open_alerts = db.session.query(Alert).filter(
		Alert.alert_status == 'Open',
		Alert.alert_record_created_at >= ninety_days_ago,
		Alert.end_time.isnot(None)
	).order_by(Alert.start.desc()).all()
	count_open_alerts = len(open_alerts)
	count_open_IM_alerts = sum(1 for alert in open_alerts if alert.im_filter)

	return render_template('dashboard.html', title='Dashboard', active_assignments=active_assignments, count_active_assignments=count_active_assignments, labels_for_assignment=labels_for_assignment, values_for_assignment=values_for_assignment, labels_for_product=labels_for_product, values_for_product=values_for_product, pending_user_check=pending_user_check, active_emergencies=active_emergencies, count_active_emergencies=count_active_emergencies,regional_im_leads=regional_im_leads, count_active_remote_supporters=count_active_remote_supporters, open_alerts=open_alerts, count_open_alerts=count_open_alerts, count_open_IM_alerts=count_open_IM_alerts)

# role profile slugs used in URLs; each has a matching role_profile_<slug>.html
# template and a Profile row whose `image` column is the capitalized slug
ROLE_PROFILE_TYPES = ('datatrans', 'geo', 'infodes', 'mobdata', 'simsco', 'webviz')

@main.route('/role_profile/<type>')
def view_role_profile(type):
	if type not in ROLE_PROFILE_TYPES:
		abort(404)
	capitalized_type = type.capitalize()
	users_with_profile = db.session.execute(
		text('SELECT "user".id, firstname, lastname, max(tier) as tier, image_file FROM "user" JOIN user_profile ON "user".id = user_profile.user_id JOIN profile ON profile.id = user_profile.profile_id WHERE image = :image GROUP BY "user".id'),
		{'image': capitalized_type}
	)

	users_with_profile_tier_1 = []
	users_with_profile_tier_2 = []
	users_with_profile_tier_3 = []
	users_with_profile_tier_4 = []
	for user in users_with_profile:
		if user.tier == 1:
			users_with_profile_tier_1.append(user)
		elif user.tier == 2:
			users_with_profile_tier_2.append(user)
		elif user.tier == 3:
			users_with_profile_tier_3.append(user)
		elif user.tier == 4:
			users_with_profile_tier_4.append(user)

	unpacked_count = db.session.execute(
		text('SELECT count(distinct("user".id)) as count FROM "user" JOIN user_profile ON "user".id = user_profile.user_id JOIN profile ON profile.id = user_profile.profile_id WHERE image = :image'),
		{'image': capitalized_type}
	).scalar()

	return render_template('role_profile_{}.html'.format(type), users_with_profile_tier_1=users_with_profile_tier_1, users_with_profile_tier_2=users_with_profile_tier_2, users_with_profile_tier_3=users_with_profile_tier_3, users_with_profile_tier_4=users_with_profile_tier_4, unpacked_count=unpacked_count)


@main.route('/get_ns_member_location_data')
def get_ns_member_location_data():
	active_national_societies = db.session.query(
		distinct(NationalSociety.ns_name).label('ns_name'),
		NationalSociety.iso2,
		NationalSociety.iso3,
		NationalSociety.ns_go_id,
		func.count().over(partition_by=NationalSociety.ns_name).label('ns_name_count')
	) \
	.join(User, NationalSociety.ns_go_id == User.ns_id) \
	.filter(User.status == 'Active') \
	.filter(~NationalSociety.ns_name.like('%IFRC%')) \
	.order_by(desc('ns_name_count')) \
	.all()

	location_data = []
	for row in active_national_societies:
		location_data.append({
			"ns_name": row.ns_name,
			"ns_name_count": row.ns_name_count
		})

	return jsonify(location_data)

@main.route('/national_societies/<int:ns_id>')
@login_required
def view_national_society(ns_id):
	ns_info = db.session.query(NationalSociety).filter(NationalSociety.ns_go_id == ns_id).first()

	ns_members = user_info_by_ns(ns_id)

	active_ns_member_count = db.session.query(NationalSociety, User) \
	.join(User, User.ns_id == NationalSociety.ns_go_id) \
	.filter(NationalSociety.ns_go_id == ns_id) \
	.filter(User.status == 'Active') \
	.count()

	return render_template('national_society_view.html', ns_members=ns_members, ns_info=ns_info, active_ns_member_count=active_ns_member_count)

@main.route('/data/response_history.json')
@cache.cached(timeout=map_data.CACHE_SECONDS, key_prefix=map_data.RESPONSE_HISTORY_CACHE_KEY)
def response_history_data():
	return jsonify(map_data.response_history())


@main.route('/data/member_locations.json')
@cache.cached(timeout=map_data.CACHE_SECONDS, key_prefix=map_data.MEMBER_LOCATIONS_CACHE_KEY)
def member_locations_data():
	return jsonify(map_data.member_locations())


@main.route('/get_active_emergencies')
def get_active_emergencies():
	"""Feeds the dashboard map's active emergency data"""

	emergencies_data = db.session.query(Emergency, NationalSociety)\
		.join(NationalSociety, NationalSociety.ns_go_id == Emergency.emergency_location_id)\
		.filter(Emergency.emergency_status == 'Active').all()

	emergencies_list = []
	for emergency, national_society in emergencies_data:
		emergency_dict = {
			'iso3': national_society.iso3,
			'count': 1,
		}
		emergencies_list.append(emergency_dict)

	return jsonify(emergencies_list)

@main.route('/uploads/<path:name>')
def download_file(name):
    s3 = boto3.resource('s3')
    file_stream = io.BytesIO()
    s3_object = s3.Object(current_app.config['UPLOAD_BUCKET'], name)
    try:
        s3_object.download_fileobj(file_stream)
        content_type = s3_object.content_type
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        # ClientError: missing key / access denied; BotoCoreError: no credentials,
        # endpoint unreachable, etc.
        current_app.logger.error(e)
        abort(404)
    file_stream.seek(0)

    return send_file(file_stream, mimetype=content_type)


@main.route('/users/<int:user_id>')
@login_required
def get_user(user_id):
    user = db.get_or_404(User, user_id)
    return jsonify({
        'id': user.id,
        'fullname': user.fullname
    })


