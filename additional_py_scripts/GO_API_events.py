# import requests package
import requests

# get data as object and assign to r
r = requests.get('https://goadmin.ifrc.org/api/v2/event/')

# create empty list
disaster_list = []

# create for loop to run through the results dictionary which is nested inside the response
for each in r.json()["results"]:
	disaster_list.append((each["name"]))

# show final output to confirm
print(disaster_list)