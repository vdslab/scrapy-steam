import requests
import os
from dotenv import load_dotenv
import psycopg2
import datetime


def insert_token_to_db(new_token, expires_time):
    
    try:
        connect = psycopg2.connect(
            host      = os.getenv('PGHOST'),
            user      = os.getenv('PGUSER'),
            password  = os.getenv('PGPASSWORD'),
            dbname    = os.getenv('PGDATABASE'),
            port      = os.getenv('PGPORT')
        )
        cur = connect.cursor()

        cur.execute(
            """INSERT INTO access_token (token, get_date, expires_time, client_id) VALUES (%s, %s, %s, %s)""",
            (new_token, datetime.datetime.now(), expires_time, os.environ['CLIENT_ID'])
        )

        connect.commit()
        print("データーベースに追加しました。")
    except Exception as e:
        print(e)
        print("データーベースに追加できませんでした。")
    finally:
        if cur:
            cur.close()
        if connect:
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
        # 有効期限を計算し、timestampに変換
        expiration_time = datetime.datetime.now() + datetime.timedelta(seconds=parsed['expires_in'])
        return [parsed['access_token'], expiration_time]
    
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    load_dotenv()

    [new_token, expires_time] = getTwitchAccessToken()
    insert_token_to_db(new_token, expires_time)
