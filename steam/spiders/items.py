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
    allowed_domains = ['api.twitch.tv']
    base_url = 'https://api.twitch.tv/helix/games/top'
    token = get_access_token()
    print(token)
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }

    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'twitch_top_games.json'
    }

    def start_requests(self):
        url = self.base_url + '?first=100'
        # url = self.base_url + '?first=5'
        yield scrapy.Request(url, headers=self.headers, callback=self.parse_games)

    def parse_games(self, response):
        top_games = json.loads(response.body)
        for game in top_games['data']:
            game_title = game['name']
            game_id = game['id']

            yield scrapy.Request(
                f'https://api.twitch.tv/helix/videos?sort=views&game_id={game_id}&first=50',
                headers=self.headers,
                callback=self.parse_videos,
                meta={'game_title': game_title, 'game_id': game_id, 'total_views': 0}
            )

    def parse_videos(self, response):
        game_title = response.meta['game_title']
        game_id = response.meta['game_id']
        total_views = response.meta['total_views']

        videos = json.loads(response.body)

        for video in videos['data']:
            total_views += video['view_count']

        if 'pagination' in videos and 'cursor' in videos['pagination']:
            next_page = f'https://api.twitch.tv/helix/videos?sort=views&game_id={game_id}&first=50&after={videos["pagination"]["cursor"]}'
            yield scrapy.Request(
                next_page,
                headers=self.headers,
                callback=self.parse_videos,
                meta={'game_title': game_title, 'game_id': game_id, 'total_views': total_views}
            )
        else:
            yield {
                'game_title': game_title,
                'game_id': game_id,
                'total_views': total_views
            }
