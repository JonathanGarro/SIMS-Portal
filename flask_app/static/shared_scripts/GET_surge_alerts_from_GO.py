"""
README

- You may need to install the 'requests' module. If you get an error mentioning it, open your terminal, and run `pip install requests`
- This script will save the alerts to a list called "alert_messages". The portal manipulates that data in a way that would not be useful to most end users, so I have omitted the full function to then send that data to our database. If you would like to save this data to a file, you can use the `with open()` feature. A Google search will return several quick guides on how to manipulate the data you get back from the server. 
- The while loop is doing plain text-string searches. The ones you see in this version are the Molnix codes used by the GO database as of 2022-01-19 (creation date of this script). Those codes may change in the future, so reach out to the Surge database team if you have problems. 

Feel free to reach out to Jonathan Garro (jonathan.garro@redcross.org) with any questions about how to use or modify this code.
"""

import requests
import math

api_call = 'https://goadmin.ifrc.org/api/v2/surge_alert/'
headers = {'Authorization': 'Token "FLASK_APP_API_KEY"'}
r = requests.get(api_call, headers).json()

current_page = 1
page_count = int(math.ceil(r['count'] / 50))

alert_messages = []

while current_page <= page_count:
	for x in r["results"]:
		# if x['molnix_status'] == 'active':
		for y in x['molnix_tags']:
			if "IM-CO" in y['name']:
				alert_messages.append(x['message'])
			elif "IM-PDC" in y['name']:
				alert_messages.append(x['message'])
			elif "IM-VIZ" in y['name']:
				alert_messages.append(x['message'])
			elif "IMANALYST" in y['name']:
				alert_messages.append(x['message'])
	if r['next']:
		next_page = requests.get(r['next'], headers).json()
		r = next_page
	current_page += 1

	
	