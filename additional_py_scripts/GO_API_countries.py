import requests
import math

api_call = 'https://goadmin.ifrc.org/api/v2/country/'

get_variable = 'name'

r = requests.get(api_call).json()

country_list = []
page_count = int(math.ceil(r['count'] / 50))
current_page = 1

while current_page <= page_count:
	for each in r["results"]:
		country_list.append(each[get_variable])
	if r['next']:
		next_page = requests.get(r['next']).json()
		r = next_page
	current_page += 1

print(country_list)