import requests
import json
import os
import sys
import time
from tqdm import tqdm

from getAccessToken import get_access_token

from dotenv import load_dotenv

# load_dotenv

CLIENT_ID = os.getenv('CLIENT_ID')

def transform_data_to_dict(data):
    transformed_dict = {}
    for item in data:
        name = item.get('name')
        appid = item.get('appid')
        if name and appid:
            transformed_dict[name] = appid
    return transformed_dict

def fetch_twitch_top_games(token, first=100):
    base_url = 'https://api.twitch.tv/helix/games/top'
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
    }
    params = {
        'first': first
    }
    top_games = []
    cursor = None

    while True:
        if cursor:
            params['after'] = cursor
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Twitch APIのリクエストに失敗しました。ステータスコード: {response.status_code}")
            break
        data = response.json()
        games = data.get('data', [])
        top_games.extend(games)
        cursor = data.get('pagination', {}).get('cursor', None)
        if not cursor:
            break
        time.sleep(1)
    return top_games

def fetch_steam_app_list():
    url = 'https://api.steampowered.com/ISteamApps/GetAppList/v2/'
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Steam APIのリクエストに失敗しました。ステータスコード: {response.status_code}")
        return {}
    data = response.json()
    apps = data.get('applist', {}).get('apps', [])
    steam_games_dict = transform_data_to_dict(apps)
    return steam_games_dict

def fetch_total_views(twitch_id, token):
    url = 'https://api.twitch.tv/helix/videos'
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
    }
    params = {
        'sort': 'views',
        'game_id': twitch_id,
        'period': 'day',
        'first': 100
    }
    total_views = 0
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Twitch ビデオAPIのリクエストに失敗しました。ステータスコード: {response.status_code}")
        return total_views
    data = response.json()
    videos = data.get('data', [])
    for video in videos:
        total_views += video.get('view_count', 0)
    return total_views

def fetch_activity_data(steam_id):
    url = f"https://steam-active-scrape.netlify.app/.netlify/functions/activity?gameId={steam_id}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"SteamアクティビティAPIのリクエストに失敗しました。ステータスコード: {response.status_code}")
            return {'active_user': 0, 'active_chat_user': 0}
        data = response.json()
        user_count = data.get('userCount', 0)
        chat_count = data.get('chatCount', 0)
        return {'active_user': user_count, 'active_chat_user': chat_count}
    except Exception as e:
        print(f"SteamアクティビティAPIの取得中にエラーが発生しました。Steam ID: {steam_id}, エラー: {e}")
        return {'active_user': 0, 'active_chat_user': 0}

def main():
    token = get_access_token()
    if not token:
        print("アクセストークンの取得に失敗しました。")
        sys.exit(1)
    
    # Twitchのトップゲームを取得
    print("Twitch APIからトップゲームを取得中...")
    top_games = fetch_twitch_top_games(token)
    print(f"取得したトップゲームの数: {len(top_games)}")
    
    # Steamのゲームリストを取得
    print("Steam APIからゲームリストを取得中...")
    steam_games_dict = fetch_steam_app_list()
    print(f"Steamで認識されているゲームの数: {len(steam_games_dict)}")
    
    # 一致するゲームを特定
    matched_games = []
    for game in top_games:
        game_title = game.get('name')
        twitch_id = game.get('id')
        if not game_title or not twitch_id:
            continue
        if game_title == 'Just Chatting':
            continue
        steam_id = steam_games_dict.get(game_title)
        if steam_id:
            matched_games.append({
                'twitch_id': twitch_id,
                'steam_id': steam_id,
                'game_title': game_title
            })
    
    print(f"マッチしたゲームの数: {len(matched_games)}")
    
    # 視聴回数とアクティビティデータを取得
    all_data = {}
    print("各ゲームの視聴回数とアクティビティデータを取得中...")

    matched_games = matched_games[0:15]
    
    for game in tqdm(matched_games, desc="Fetching data"):
        twitch_id = game['twitch_id']
        steam_id = game['steam_id']
        game_title = game['game_title']
        
        # Twitchの総視聴回数を取得
        total_views = fetch_total_views(twitch_id, token)
        
        # Steamアクティビティデータを取得
        activity_data = fetch_activity_data(steam_id)
        
        # データを統合
        all_data[steam_id] = {
            'twitch_id': twitch_id,
            'steam_id': steam_id,
            'game_title': game_title,
            'total_views': total_views,
            'active_user': activity_data['active_user'],
            'active_chat_user': activity_data['active_chat_user']
        }
        
        time.sleep(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'top_games_data.json')
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        print(f"結果を '{output_file}' に保存しました。")
    except Exception as e:
        print(f"JSONファイルへの保存に失敗しました: {e}")

if __name__ == "__main__":
    main()
