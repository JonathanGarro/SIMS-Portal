from flask import render_template,redirect,session,request, flash
from flask_app import app
from flask_app.models.member import Member
from flask_app.models.emergency import Emergency
from flask_app.models.national_society import National_Society

@app.route('/ns/<int:id>', methods=['GET','POST'])
def ns_profile(id):
	one_ns = National_Society.get_national_society_with_members({"id": id})

	member_data = {
		'id': session['member_id']
	}
	
	if 'member_id' not in session:
		return redirect('/logout')
		
	countries = National_Society.get_all_national_societies()
	return render_template('national_society_view.html', member = Member.get_member_by_id(member_data), ns_info = one_ns, countries = countries)
