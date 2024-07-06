import os
import psycopg2
from dotenv import load_dotenv
import datetime

# load_dotenv()

def get_access_token():
    cur = None
    connect = None
    try:
        connect = psycopg2.connect(
            host=os.getenv('PGHOST'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            dbname=os.getenv('PGDATABASE'),
            port=os.getenv('PGPORT')
        )
        cur = connect.cursor()

        cur.execute("""
            SELECT token, expires_time
            FROM access_token
            WHERE client_id = %s
            ORDER BY get_date DESC
            LIMIT 1
        """, (os.getenv('CLIENT_ID'),))

        token_record = cur.fetchone()
        
        if token_record:
            token = token_record[0]
            expires_time = token_record[1]
            current_time = datetime.datetime.now()

            # トークンの有効期限を確認し、まだ有効な場合はそれを返す
            if expires_time > current_time:
                return token
            else:
                print("トークンの有効期限が切れています。")
                return None
        else:
            print("データベースにトークンが見つかりませんでした。")
            return None

    except Exception as e:
        print(f"データベースからトークンを取得できませんでした: {e}")
        return None

    finally:
        if cur:
            cur.close()
        if connect:
            connect.close()
