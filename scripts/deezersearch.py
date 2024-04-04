import json

import requests
from urllib.parse import urlencode
import sys

# Define your query
query = sys.argv[1]

# Encode the query
encoded_query = urlencode({"q": query})

# Define the API endpoint
api_url = f"https://api.deezer.com/search/track?{encoded_query}&limit=10&output=json"

# Make the request
response = requests.get(api_url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Get the JSON response
    data = response.json()
    # Print the response
    # print(data)
else:
    print("Error:", response.status_code)


formatted_songs = []
for song in data["data"]:
    formatted_song = {
        "plugin": "deezerdl",
        "inputs": [song["link"],"FLAC"],
        "desc": f"{song['title']} by {song['artist']['name']}"
    }
    formatted_songs.append(formatted_song)
# print(formatted_songs[:2])
print(json.dumps(formatted_songs, indent=2))
