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

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            # Delete existing records from steam_data and steam_data_genres
            cur.execute("DELETE FROM steam_data_genres WHERE steam_game_id = '%s'", (item['steam_id'],))
            cur.execute("DELETE FROM steam_data WHERE steam_game_id = '%s'", (item['steam_id'],))

            # Insert data into steam_data table
            cur.execute("""
                INSERT INTO steam_data (
                    steam_game_id, twitch_game_id, game_title, webpage_url, img_url, price,
                    is_single_player, is_multi_player, is_device_windows, is_device_mac
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                item['steam_id'], item['twitch_id'], item['game_title'], item['webpage_url'],
                item['img_url'], item['price'], item['is_single_player'], item['is_multi_player'],
                item['is_device_windows'], item['is_device_mac']
            ))

            # Insert data into steam_data_genres table
            for genre in item['genres']:
                cur.execute("""
                    INSERT INTO steam_data_genres (steam_game_id, genre_id)
                    SELECT %s, genre_id FROM genres WHERE genre_id = %s
                """, (item['steam_id'], genre['id']))

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
