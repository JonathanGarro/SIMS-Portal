"""
README

- You may need to install the 'requests' module. If you get an error mentioning it, open your terminal, and run `pip install requests`
- The SIMS portal manipulates that data in a way that would not be useful to most end users, so I have omitted the full function to then send that data to our database. If you would like to save this data to a file, you can use the `with open()` feature at the bottom, which will create a CSV file on your computer in the same place that you've saved this script.
- The while loop is doing plain text-string searches. The ones you see in this version are the Molnix codes used by the GO database as of 2022-01-19 (creation date of this script). Those codes may change in the future, so reach out to the Surge database team if you have problems. IM alerts typically only include words like "Officer", "Analyst", "Coordinator", or "Manager", so that's why you see those strings in the second for loop. You can tweak that to suit your own needs by adding to or removing from that list.

Feel free to reach out to Jonathan Garro (jonathan.garro@redcross.org) with any questions about how to use or modify this code.
"""
					
import requests
import math
import csv
api_call = 'https://goadmin.ifrc.org/api/v2/surge_alert/'
r = requests.get(api_call).json()

current_page = 1
page_count = int(math.ceil(r['count'] / 50))
print(f"THE PAGE COUNT TOTAL IS: {page_count}")

output = []

while current_page <= page_count:
	for x in r['results']:
		temp_dict = {}
		if x['molnix_tags']:
			for y in x['molnix_tags']:
				if ("Manager" in y['description']) or ("Officer" in y['description']) or ("Analyst" in y['description']) or ("Coordinator" in y['description']):
					temp_dict['role_profile'] = y['description']
					temp_dict['alert_date'] = x['opens']
					temp_dict['alert_id'] = x['id']
					temp_dict['alert_status'] = x['molnix_status']
					if x['event']:
						temp_dict['event_name'] = x['event']['name']
						temp_dict['event_go_id'] = x['event']['id']
						temp_dict['event_date'] = x['event']['disaster_start_date']
					if x['country']:
						temp_dict['location'] = x['country']['name']
					output.append(temp_dict)
	if r['next']:
		next_page = requests.get(r['next']).json()
		r = next_page
		current_page += 1
	else:
		break

keys = output[0].keys()
a_file = open("output.csv", "w")
dict_writer = csv.DictWriter(a_file, keys)
dict_writer.writeheader()
dict_writer.writerows(output)
a_file.close()