import json
import psycopg2
import sys
import os
import datetime

from dotenv import load_dotenv
# load_dotenv()

def insert_views_to_db(json_file, db_host, db_port, db_name, db_user, db_password):
    try:
        connect = psycopg2.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            dbname=db_name,
            port=db_port
        )
        cur = connect.cursor()

        with open(json_file, 'r') as f:
            data = json.load(f)

        for item in data:
            cur.execute("""
                INSERT INTO game_views (get_date, game_title, twitch_id, steam_id, total_views) VALUES (%s, %s, %s, %s, %s)
            """, (datetime.datetime.now(), item['game_title'], item['twitch_id'], item['steam_id'], item['total_views']))

        connect.commit()
        cur.close()
        connect.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    json_file = 'twitch_top_games.json'
    PGHOST = os.getenv('PGHOST')
    PGPORT = os.getenv('PGPORT')
    PGDATABASE = os.getenv('PGDATABASE')
    PGUSER = os.getenv('PGUSER')
    PGPASSWORD = os.getenv('PGPASSWORD')

    if not all([PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD]):
        print("Database connection information is missing.")
        sys.exit(1)

    insert_views_to_db(json_file, PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
