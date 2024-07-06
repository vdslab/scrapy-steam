import scrapy
import json
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
token_path = os.path.join(parent_dir, 'getAccessToken.py')
sys.path.append(parent_dir)

from getAccessToken import get_access_token

from dotenv import load_dotenv
# load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')

class ItemsSpider(scrapy.Spider):
    name = 'items'
    allowed_domains = ['api.twitch.tv', 'api.steampowered.com']
    base_url = 'https://api.twitch.tv/helix/games/top'
    token = get_access_token()

    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }

    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'twitch_top_games.json'
    }

    def transform_data_to_dict(self, data):
        transformed_dict = {}
        for item in data:
            name = item.get('name')
            appid = item.get('appid')
            if name and appid:
                transformed_dict[name] = appid
        return transformed_dict

    def start_requests(self):
        url = self.base_url + '?first=100'
        yield scrapy.Request(url, headers=self.headers, callback=self.parse_twitch, meta={'top_games_index': 0, 'top_games': []})

    def parse_twitch(self, response):
        # top_games = response.meta['top_games']  # JSON形式に変換

        top_games_json = json.loads(response.body)
        cursor = top_games_json.get('pagination', {}).get('cursor', None)
        top_games = top_games_json['data']

        prev_top_games = response.meta['top_games']
        top_games = prev_top_games + top_games

        top_games_index = response.meta['top_games_index'] + 1
        
        if cursor:
            url = f'https://api.twitch.tv/helix/games/top?first=100&after={cursor}'
            yield scrapy.Request(
                url,
                headers=self.headers,
                callback=self.parse_twitch,
                meta={'top_games_index': top_games_index, 'top_games': top_games}
            )
        else:
            url = 'https://api.steampowered.com/ISteamApps/GetAppList/v2/'
            yield scrapy.Request(
                url,
                callback=self.parse_games,
                meta={'top_games': top_games}
            )


    def parse_games(self, response):
        steam_games_json = json.loads(response.body)
        steam_games_dict = self.transform_data_to_dict(steam_games_json['applist']['apps'])
        top_games = response.meta['top_games']

        for game in top_games:
            game_title = game['name']
            twitch_id = game['id']
            url = f'https://api.twitch.tv/helix/videos?sort=views&game_id={twitch_id}&period=day&first=100'

            if game_title in steam_games_dict and game_title != 'Just Chatting':
                steam_id = steam_games_dict[game_title]
                yield scrapy.Request(
                    url,
                    headers=self.headers,
                    callback=self.parse_videos,
                    meta={'game_title': game_title, 'twitch_id': twitch_id, 'steam_id': steam_id}
                )


    def parse_videos(self, response):
        game_title = response.meta['game_title']
        twitch_id = response.meta['twitch_id']
        steam_id = response.meta['steam_id']
        total_views = 0

        videos = json.loads(response.body)

        for video in videos['data']:
            total_views += video['view_count']

        yield {
            'game_title': game_title,
            'twitch_id': twitch_id,
            'steam_id': steam_id,
            'total_views': total_views
        }

