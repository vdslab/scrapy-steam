import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()
url = "https://id.twitch.tv/oauth2/token"

data = {
    "client_id": os.environ['CLIENT_ID'],
    "client_secret": os.environ['CLIENT_SECRET'],
    "grant_type": "client_credentials",
    "scope": "user:edit clips:edit",
}

response = requests.post(url, data=data)
if response.status_code == 200:
    parsed = response.json()
    print(json.dumps(parsed, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
