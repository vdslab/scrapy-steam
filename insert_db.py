import os
import psycopg2
import json

from dotenv import load_dotenv
load_dotenv()

PGHOST = os.getenv('PGHOST')
PGPORT = os.getenv('PGPORT')
PGDATABASE = os.getenv('PGDATABASE')
PGUSER = os.getenv('PGUSER')
PGPASSWORD = os.getenv('PGPASSWORD')

def insert_data():
    print(PGPORT)
    conn = psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
    )

    cur = conn.cursor()
        
    # 接続確認用のクエリを実行
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    print(f"Connected to database. PostgreSQL version: {db_version[0]}")
    
    # 接続を閉じる
    cur.close()
    conn.close()
    

if __name__ == '__main__':
    insert_data()
