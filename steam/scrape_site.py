import sys
import os
import psycopg2
from dotenv import load_dotenv
import requests
import time

# load_dotenv()

base_url = "https://steam-active-scrape.netlify.app/.netlify/functions/usertags?gameId="

def scrape_site(db_host, db_port, db_name, db_user, db_password):
  cur = None
  connect = None
  try:
    connect = psycopg2.connect(
          host=db_host,
          user=db_user,
          password=db_password,
          dbname=db_name,
          port=db_port
    )

    cur = connect.cursor()

    cur.execute("""
      SELECT DISTINCT steam_game_id
      FROM steam_data
      WHERE NOT EXISTS (
        SELECT 1
        FROM steam_data_tags
        WHERE steam_data_tags.steam_game_id = steam_data.steam_game_id
      )
    """)

    game_ids = cur.fetchall()
    
    if game_ids:
      print(f"diff game_ids count:{len(game_ids)}")
      for game_id_tuple in game_ids:
        game_id = game_id_tuple[0]
        url = f"{base_url}{game_id}"
        response = requests.get(url)

        if response.status_code == 200:
          tags_data = response.json().get("tags", [])

          with connect.cursor() as cursor:
            for tag in tags_data:
              cursor.execute(
                "INSERT INTO steam_data_tags (steam_game_id, tag_name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (game_id, tag)
              )
            connect.commit()
        else:
          print(f"Failed to fetch tags for game_id: {game_id}, Status Code: {response.status_code}")
        time.sleep(1)

  finally:
    if cur:
      cur.close()
    if connect:
      connect.close()

if __name__ == "__main__":
  PGHOST = os.getenv('PGHOST')
  PGPORT = os.getenv('PGPORT')
  PGDATABASE = os.getenv('PGDATABASE')
  PGUSER = os.getenv('PGUSER')
  PGPASSWORD = os.getenv('PGPASSWORD')

  if not all([PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD]):
      print("Database connection information is missing.")
      sys.exit(1)

  scrape_site(PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
