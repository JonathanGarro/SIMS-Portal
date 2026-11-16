"""Portfolio download and delete."""
from SIMS_Portal import db
from SIMS_Portal.models import Portfolio
from tests.seed import ADMIN_ID, MEMBER_ID


def _status(product_id):
	db.session.expire_all()
	return db.session.get(Portfolio, product_id).product_status


def _add_product(product_id, creator_id, local_file='file.pdf'):
	db.session.add(Portfolio(id=product_id, title='P', type='Map', local_file=local_file, creator_id=creator_id, emergency_id=1))
	db.session.commit()


def test_download_unknown_product_is_404(client):
	assert client.get('/portfolio/download/999').status_code == 404


def test_download_missing_file_is_404(member_client):
	assert member_client.get('/portfolio/download/1').status_code == 404  # seeded file isn't on disk


def test_download_cannot_escape_the_portfolio_folder(member_client):
	_add_product(50, MEMBER_ID, local_file='../../config.py')
	assert member_client.get('/portfolio/download/50').status_code == 404


def test_creator_can_delete_their_product(member_client):
	member_client.post('/portfolio/delete/1')  # product 1 is the member's
	assert _status(1) == 'Removed'


def test_member_cannot_delete_product_whose_id_matches_their_user_id(member_client):
	# used to be allowed: the check compared the user's ID with the product's ID
	_add_product(MEMBER_ID, ADMIN_ID)
	assert member_client.post(f'/portfolio/delete/{MEMBER_ID}').status_code == 403
	assert _status(MEMBER_ID) != 'Removed'


def test_admin_can_delete_any_product(admin_client):
	admin_client.post('/portfolio/delete/1')
	assert _status(1) == 'Removed'


def test_delete_unknown_product_is_404(admin_client):
	assert admin_client.post('/portfolio/delete/999').status_code == 404
