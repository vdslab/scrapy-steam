import requests
import os
from dotenv import load_dotenv
import psycopg2
import datetime

def insert_token_to_db(new_token):
    
    connect = psycopg2.connect(
        host      = os.getenv('PGHOST'),
        user      = os.getenv('PGUSER'),
        password  = os.getenv('PGPASSWORD'),
        dbname    = os.getenv('PGDATABASE'),
        port      = os.getenv('PGPORT')
    )
    cur = connect.cursor()

    cur.execute(
        """INSERT INTO access_token (token, get_date) VALUES (%s, %s)""",
        (new_token, datetime.datetime.now())
    )

    connect.commit()
    cur.close()
    connect.close()


def getTwitchAccessToken():
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
        return parsed['access_token']
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    load_dotenv()

    new_token = getTwitchAccessToken()

    insert_token_to_db(new_token)