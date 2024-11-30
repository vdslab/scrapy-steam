import json
import psycopg2
from psycopg2 import extras
from tqdm import tqdm
import sys
import os
from dotenv import load_dotenv
from datetime import datetime

# 環境変数の読み込み
# load_dotenv()

from psycopg2.extras import Json

# データベース接続情報を環境変数から取得
PGHOST = os.getenv('PGHOST')
PGPORT = os.getenv('PGPORT')
PGDATABASE = os.getenv('PGDATABASE')
PGUSER = os.getenv('PGUSER')
PGPASSWORD = os.getenv('PGPASSWORD')

def main():
    # PostgreSQL に接続
    try:
        conn = psycopg2.connect(
            host=PGHOST,
            port=PGPORT,
            dbname=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD
        )
        cursor = conn.cursor()
        print("PostgreSQLに正常に接続しました。")
    except Exception as e:
        print(f"PostgreSQLへの接続に失敗しました: {e}")
        sys.exit(1)

    json_file_path = 'all_top_games_data.json'

    # JSONファイルの読み込み
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            all_top_games_data = json.load(f)
        print(f"{json_file_path} を正常に読み込みました。")
    except Exception as e:
        print(f"{json_file_path} の読み込みに失敗しました: {e}")
        cursor.close()
        conn.close()
        sys.exit(1)

    # 1. steam_game_data テーブル
    insert_steam_game_data = """
    INSERT INTO steam_game_data (
        steam_game_id,
        twitch_game_id,
        game_title,
        genres,
        webpage_url,
        img_url,
        price,
        sale_price,
        is_single_player,
        is_multi_player,
        is_device_windows,
        is_device_mac,
        play_time,
        review_text,
        difficulty,
        graphics,
        story,
        music,
        developer_name,
        short_details,
        release_date,
        tags
    ) VALUES (
        %(steam_id)s,
        %(twitch_id)s,
        %(game_title)s,
        %(genres)s,
        %(webpage_url)s,
        %(img_url)s,
        %(price)s,
        %(sale_price)s,
        %(is_single_player)s,
        %(is_multi_player)s,
        %(is_device_windows)s,
        %(is_device_mac)s,
        %(play_time)s,
        %(review_text)s,
        %(difficulty)s,
        %(graphics)s,
        %(story)s,
        %(music)s,
        %(developer_name)s,
        %(short_details)s,
        %(release_date)s,
        %(tags)s
    )
    ON CONFLICT (steam_game_id) DO UPDATE SET
        twitch_game_id = EXCLUDED.twitch_game_id,
        game_title = EXCLUDED.game_title,
        genres = EXCLUDED.genres,
        webpage_url = EXCLUDED.webpage_url,
        img_url = EXCLUDED.img_url,
        price = EXCLUDED.price,
        sale_price = EXCLUDED.sale_price,
        is_single_player = EXCLUDED.is_single_player,
        is_multi_player = EXCLUDED.is_multi_player,
        is_device_windows = EXCLUDED.is_device_windows,
        is_device_mac = EXCLUDED.is_device_mac,
        play_time = EXCLUDED.play_time,
        review_text = EXCLUDED.review_text,
        difficulty = EXCLUDED.difficulty,
        graphics = EXCLUDED.graphics,
        story = EXCLUDED.story,
        music = EXCLUDED.music,
        developer_name = EXCLUDED.developer_name,
        short_details = EXCLUDED.short_details,
        release_date = EXCLUDED.release_date,
        tags = EXCLUDED.tags;
    """

    # 2. game_views テーブル
    insert_game_views = """
    INSERT INTO game_views (
        get_date,
        game_title,
        twitch_id,
        steam_id,
        total_views
    ) VALUES (
        %(get_date)s,
        %(game_title)s,
        %(twitch_id)s,
        %(steam_id)s,
        %(total_views)s
    )
    ON CONFLICT (get_date, twitch_id, steam_id) DO UPDATE SET
        total_views = EXCLUDED.total_views;
    """

    # 3. steam_active_users テーブル
    insert_steam_active_users = """
    INSERT INTO steam_active_users (
        steam_id,
        get_date,
        active_user,
        active_chat_user
    ) VALUES (
        %(steam_id)s,
        %(get_date)s,
        %(active_user)s,
        %(active_chat_user)s
    )
    ON CONFLICT (steam_id, get_date) DO UPDATE SET
        active_user = EXCLUDED.active_user,
        active_chat_user = EXCLUDED.active_chat_user;
    """

    # 現在の日付を取得（YYYY-MM-DD形式）
    current_date = datetime.now().strftime('%Y-%m-%d')

    # データの挿入
    try:
        for game in tqdm(all_top_games_data, desc="Inserting data into PostgreSQL"):
            # データの準備
            steam_id = game.get('steam_id')
            twitch_id = game.get('twitch_id')
            game_title = game.get('game_title')
            genres = game.get('genres', [])
            webpage_url = game.get('webpage_url')
            img_url = game.get('img_url')
            price = game.get('price')
            sale_price = game.get('sale_price')
            is_single_player = game.get('is_single_player')
            is_multi_player = game.get('is_multi_player')
            is_device_windows = game.get('is_device_windows')
            is_device_mac = game.get('is_device_mac')
            play_time = game.get('play_time')
            review_text = game.get('review_text', {})
            difficulty = game.get('difficulty')
            graphics = game.get('graphics')
            story = game.get('story')
            music = game.get('music')
            developer_name = game.get('developer_name')
            short_details = game.get('short_details')
            release_date = game.get('release_date')
            tags = game.get('tags', [])
            total_views = game.get('total_views')
            active_user = game.get('active_user')
            active_chat_user = game.get('active_chat_user')

            # steam_game_data テーブルへの挿入
            steam_game_data_record = {
                'steam_id': steam_id,
                'twitch_id': twitch_id,
                'game_title': game_title,
                'genres': genres,
                'webpage_url': webpage_url,
                'img_url': img_url,
                'price': price,
                'sale_price': sale_price,
                'is_single_player': is_single_player,
                'is_multi_player': is_multi_player,
                'is_device_windows': is_device_windows,
                'is_device_mac': is_device_mac,
                'play_time': play_time,
                'review_text': Json(review_text),
                'difficulty': difficulty,
                'graphics': graphics,
                'story': story,
                'music': music,
                'developer_name': developer_name,
                'short_details': short_details,
                'release_date': release_date,
                'tags': tags
            }

            try:
                cursor.execute(insert_steam_game_data, steam_game_data_record)
            except Exception as e:
                print(f"steam_game_data テーブルへの挿入に失敗しました (Steam ID: {steam_id}): {e}")
                conn.rollback()
                continue

            # game_views テーブルへの挿入
            game_views_record = {
                'get_date': current_date,
                'game_title': game_title,
                'twitch_id': twitch_id,
                'steam_id': steam_id,
                'total_views': total_views
            }

            try:
                cursor.execute(insert_game_views, game_views_record)
            except Exception as e:
                print(f"game_views テーブルへの挿入に失敗しました (Steam ID: {steam_id}): {e}")
                conn.rollback()
                continue

            # steam_active_users テーブルへの挿入
            steam_active_users_record = {
                'steam_id': steam_id,
                'get_date': current_date,
                'active_user': active_user,
                'active_chat_user': active_chat_user
            }

            try:
                cursor.execute(insert_steam_active_users, steam_active_users_record)
            except Exception as e:
                print(f"steam_active_users テーブルへの挿入に失敗しました (Steam ID: {steam_id}): {e}")
                conn.rollback()
                continue

        # 変更をコミット
        conn.commit()
        print("全てのデータを正常に挿入/更新しました。")

    except Exception as e:
        print(f"データの挿入中にエラーが発生しました: {e}")
        conn.rollback()
    finally:
        # 接続を閉じる
        cursor.close()
        conn.close()
        print("PostgreSQLの接続を閉じました。")

if __name__ == '__main__':
    main()
