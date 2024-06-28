import json
import psycopg2
import sys
import os

def insert_data_to_db(json_file, db_host, db_port, db_name, db_user, db_password):
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
            INSERT INTO twitch_videos (game_title, game_id, total_views) VALUES (%s, %s, %s)
        """, (item['game_title'], item['game_id'], item['total_views']))

    connect.commit()
    cur.close()
    connect.close()

if __name__ == "__main__":
    # json_file = sys.argv[1]
    json_file = 'twitch_top_games.json'
    PGHOST = os.getenv('PGHOST')
    PGPORT = os.getenv('PGPORT')
    PGDATABASE = os.getenv('PGDATABASE')
    PGUSER = os.getenv('PGUSER')
    PGPASSWORD = os.getenv('PGPASSWORD')

    insert_data_to_db(json_file, PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
