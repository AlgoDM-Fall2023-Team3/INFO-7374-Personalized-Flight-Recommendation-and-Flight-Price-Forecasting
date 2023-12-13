import requests
from datetime import date, timedelta
import pandas as pd
import json 

# Set your Oxylabs API credentials
username = "user"
password = "password"

# API endpoint
url = "https://realtime.oxylabs.io/v1/queries"
flight_data = []

# List of cities for the origin and destination


cities = [
    "New York, New York, United States", "Los Angeles, California, United States",
    "Chicago, Illinois, United States", "Houston, Texas, United States",
    "Phoenix, Arizona, United States", "Philadelphia, Pennsylvania, United States",
    "San Antonio, Texas, United States", "San Diego, California, United States",
    "Dallas, Texas, United States", "San Jose, California, United States",
    "Austin, Texas, United States", "Jacksonville, Florida, United States",
    "San Francisco, California, United States", "Columbus, Ohio, United States",
    "Indianapolis, Indiana, United States", "Fort Worth, Texas, United States",
    "Charlotte, North Carolina, United States", "Seattle, Washington, United States",
    "Denver, Colorado, United States", "Washington, D.C., United States"
]

# Set the date window from December to January
start_date = date(2024, 2, 1)
end_date = date(2024, 3, 31)

# Prepare the headers
headers = {
    "Content-Type": "application/json"
}

# Prepare the authentication
auth = (username, password)

# Output JSON file
count = 0
output_file = "flight_results_future.json"

# Initialize the JSON file with an empty dictionary
with open(output_file, "w") as json_file:
    json.dump({}, json_file)

for origin_city in cities:
    for destination_city in cities:
        if origin_city != destination_city:
            for single_date in pd.date_range(start_date, end_date):
                # Adjust the query parameters based on the current origin, destination, and date
                query_params = {
                    "source": "google_search",
                    "query": f"{origin_city} to {destination_city} flights on {single_date.strftime('%Y-%m-%d')}",
                    "geo_location": origin_city,
                    "parse": True
                }

                # Make the API request
                response = requests.post(url, json=query_params, headers=headers, auth=auth)

                # Check if the request was successful (HTTP status code 200)
                if response.status_code == 200:
                    # Assuming the response contains a list of flights, adjust the key accordingly
                    flights_data = response.json()
                    flight_data.append(flights_data)
                    count += 1
                    print("Sucessfully retrieved data record No - ",count)
                    with open(output_file, "w") as json_file:
                        json.dump(flight_data, json_file)
                else:
                    print(f"Error: {response.status_code} - {response.text}")