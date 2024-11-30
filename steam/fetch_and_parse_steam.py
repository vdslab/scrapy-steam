import requests
from janome.tokenizer import Tokenizer
import re
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import time
import os
from tqdm import tqdm

POSITIVE_WORDS = [
    "素晴らしい", "最高", "良い", "綺麗", "美しい", "楽しい", "面白い", "満足", "優れている",
    "快適", "魅力的", "感動", "新鮮", "素敵", "便利", "爽快", "明るい", "滑らか", "高品質",
    "壮大", "優雅", "洗練", "斬新", "魅力", "リッチ", "多彩", "没入感", "快適",
    "バランスが取れている", "スムーズなプレイ", "エキサイティング", "革新的",
    "爽快感", "挑戦的", "リプレイ価値", "ダイナミック", "インタラクティブ"
]

NEGATIVE_WORDS = [
    "悪い", "低い", "ひどい", "遅い", "不満", "つまらない", "問題", "苦情", "改善",
    "不足", "不便", "不快", "退屈", "古い", "低品質", "不正確", "バグ",
    "曖昧", "不明瞭", "煩わしい", "混乱", "制限", "不安定", "ダサい", "地味", "単調",
    "劣悪", "不完全", "不適切", "不十分", "途切れる", "詰まる", "欠陥", "バランスが悪い",
    "グリッチ", "ラグ", "クランク", "バランスが崩れている", "ロード時間が長い", "ゲームバランスが悪い",
    "クランチタイム", "パッチが不完全"
]

DIFFICULTY_POSITIVE_WORDS = [
    "難しい", "難易度高い", "複雑", "困難", "手ごわい", "チャレンジング", "難関", "厄介"
]

DIFFICULTY_NEGATIVE_WORDS = [
    "簡単", "容易", "簡便", "易しい", "シンプル", "楽々", "単純", "わかりやすい"
]

STORY_EXPRESSIONS = [
    "ストーリー", "物語", "シナリオ", "話", "ナラティブ", "展開",
    "プロット", "ストーリー性", "ストーリー展開",
    "物語の深さ", "キャラクター開発", "ストーリーテリング",
    "ナラティブデザイン", "プロットの展開", "感情移入",
    "共感", "ドラマチック", "感動的"
]

ASPECT_EXPRESSIONS = {
    "グラフィック": [
        "グラフィック", "描写", "グラフィカル", "ビジュアル", "視覚効果",
        "アートスタイル", "レンダリング", "テクスチャ", "ライティング"
    ],
    "音楽": [
        "音楽", "サウンド", "サウンドトラック", "効果音", "音響",
        "オーディオ", "バックグラウンドミュージック"
    ],
    "難易度": [
        "難易度", "難しい", "手ごわい", "挑戦的", "厳しい",
        "難関", "難解", "複雑", "困難", "チャレンジング",
        "簡単", "容易", "シンプル", "楽々", "単純",
        "わかりやすい", "バランス", "調整", "バランスが取れている"
    ],
    "ストーリー性": [
        "ストーリー", "物語", "シナリオ", "話", "ナラティブ", "展開",
        "プロット", "ストーリー性", "ストーリー展開",
        "物語の深さ", "キャラクター開発", "ストーリーテリング",
        "ナラティブデザイン", "プロットの展開", "感情移入",
        "共感", "ドラマチック", "感動的"
    ]
}

tokenizer = Tokenizer()

# ストップワードリストの読み込み
def load_stopwords(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            stopwords = set(json.load(f))
        return stopwords
    except Exception as e:
        print(f"ストップワードの読み込みに失敗しました: {e}")
        return set()

STOPWORDS_PATH = 'stopwords.json'
STOPWORDS = load_stopwords(STOPWORDS_PATH)

def fetch_reviews(appid, retries=3, delay=2):
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=japanese&num_per_page=100&purchase_type=all"
    for attempt in range(retries):
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"HTTPステータスコード {response.status_code}")
            data = response.json()
            raw_reviews = data.get("reviews", [])
            reviews = []
            playtimes = []
            for review in raw_reviews:
                review_text = review.get("review", "")
                playtime = review.get("author", {}).get("playtime_forever", 0)  # 分単位
                reviews.append(review_text)
                playtimes.append(playtime)
            return reviews, playtimes
        except Exception as e:
            print(f"appid {appid} のレビュー取得に失敗しました (試行 {attempt + 1}/{retries}): {e}")
            time.sleep(delay)
    print(f"appid {appid} のレビュー取得に全て失敗しました。スキップします。")
    return [], []

def tokenize_japanese(text):
    tokens = []
    for token in tokenizer.tokenize(text):
        pos = token.part_of_speech.split(',')[0]
        # 名詞、形容詞、動詞のみを対象
        if pos in ['名詞', '形容詞', '動詞']:
            word = token.base_form
            # 数値のみの単語を除外
            if re.match(r'^\d+$', word):
                continue
            # 記号や特殊文字のみの単語を除外
            if re.match(r'^[^\w\s]+$', word):
                continue
            # ストップワードを除外
            if word in STOPWORDS:
                continue
            tokens.append(word)
    return tokens

def split_sentences(text):
    # 日本語の文の区切り文字を正規表現で分割
    sentences = re.split(r'[。！？]', text)
    # 空の文を除外
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    return sentences

def extract_evaluations(reviews, aspects, window_size=5):
    # 初期化
    aspect_scores = {aspect: {'ポジティブ': 0, 'ネガティブ': 0} for aspect in aspects}
    aspect_scores["難易度"] = {'難しい': 0, '簡単': 0}  # 難易度専用

    # Word weightの初期化
    word_weights = {aspect: {} for aspect in aspects}
    word_weights["難易度"] = {}  # 難易度専用

    for review in reviews:
        sentences = split_sentences(review)
        for sentence in sentences:
            for aspect, expressions in aspects.items():
                if aspect == "難易度":
                    # 「難易度」が含まれる文、または「難しい」「簡単」などが含まれる文
                    if any(expr in sentence for expr in expressions):
                        tokens = tokenize_japanese(sentence)
                        # 難易度に関連する単語をカウント
                        for word in tokens:
                            if word in DIFFICULTY_POSITIVE_WORDS:
                                aspect_scores[aspect]['難しい'] += 1
                                word_weights[aspect][word] = word_weights[aspect].get(word, 0) + 1
                            elif word in DIFFICULTY_NEGATIVE_WORDS:
                                aspect_scores[aspect]['簡単'] += 1
                                word_weights[aspect][word] = word_weights[aspect].get(word, 0) + 1
                elif aspect == "ストーリー性":
                    # ストーリー性に関連する表現が含まれる文
                    if any(expr in sentence for expr in expressions):
                        tokens = tokenize_japanese(sentence)
                        # ストーリー性に関連する単語をカウント
                        for word in tokens:
                            # ストーリー性の評価は感情辞書を使用
                            if word in POSITIVE_WORDS:
                                aspect_scores[aspect]['ポジティブ'] += 1
                                word_weights[aspect][word] = word_weights[aspect].get(word, 0) + 1
                            elif word in NEGATIVE_WORDS:
                                aspect_scores[aspect]['ネガティブ'] += 1
                                word_weights[aspect][word] = word_weights[aspect].get(word, 0) + 1
                else:
                    # その他のアスペクト（グラフィック、音楽）について
                    if any(expr in sentence for expr in expressions):
                        tokens = tokenize_japanese(sentence)
                        # アスペクトに関連する単語を検出
                        if any(expr in tokens for expr in expressions):
                            for word in tokens:
                                if word in POSITIVE_WORDS:
                                    aspect_scores[aspect]['ポジティブ'] += 1
                                    word_weights[aspect][word] = word_weights[aspect].get(word, 0) + 1
                                elif word in NEGATIVE_WORDS:
                                    aspect_scores[aspect]['ネガティブ'] += 1
                                    word_weights[aspect][word] = word_weights[aspect].get(word, 0) + 1
    return aspect_scores, word_weights

def calculate_sentiment_scores(aspect_scores):
    sentiment_scores = {}
    for aspect, sentiments in aspect_scores.items():
        if aspect != "難易度":
            positive = sentiments['ポジティブ']
            negative = sentiments['ネガティブ']
            total = positive + negative
            if total == 0:
                # 評価がない場合は中立としてスコア3を割り当て
                sentiment_scores[aspect] = 3.0
                continue
            # 感情比率を計算
            sentiment_ratio = (positive - negative) / total  # -1から1の範囲
            # -1〜1を1〜5にマッピング
            sentiment_score = 3 + sentiment_ratio * 2
            # 小数点第2位までに丸める
            sentiment_score = round(sentiment_score, 2)
            # スコアの範囲を1〜5に制限
            sentiment_score = max(1.0, min(5.0, sentiment_score))
            sentiment_scores[aspect] = sentiment_score
        else:
            # 難易度スコアの計算
            difficult = sentiments['難しい']
            easy = sentiments['簡単']
            total = difficult + easy
            if total == 0:
                # 評価がない場合は中立としてスコア3を割り当て
                sentiment_scores[aspect] = 3.0
                continue
            # 難易度比率を計算
            difficulty_ratio = (difficult - easy) / total  # -1から1の範囲
            # -1〜1を1〜5にマッピング（-1: 簡単=1, 0: 中立=3, 1: 難しい=5）
            difficulty_score = 3 + difficulty_ratio * 2
            # 小数点第2位までに丸める
            difficulty_score = round(difficulty_score, 2)
            # スコアの範囲を1〜5に制限
            difficulty_score = max(1.0, min(5.0, difficulty_score))
            sentiment_scores[aspect] = difficulty_score
    return sentiment_scores

def generate_word_weights(reviews, top_percent=25, decimal_places=2):
    # トークン化したレビュー文をスペースで結合（TF-IDF Vectorizerの入力形式に合わせる）
    tokenized_reviews = [" ".join(tokenize_japanese(review)) for review in reviews]
    
    # トークン化後のデータが空でないか確認
    if not any(tokenized_reviews):
        print("トークン化後のレビューが全て空です。TF-IDF計算をスキップします。")
        return {}
    
    try:
        # TF-IDFベクトル化
        vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(), token_pattern=None)
        tfidf_matrix = vectorizer.fit_transform(tokenized_reviews)
        
        # ボキャブラリーの取得
        feature_names = vectorizer.get_feature_names_out()
        
        # 各単語とその重みの合計を計算
        word_weights = np.sum(tfidf_matrix.toarray(), axis=0)

        # 単語とその重みの辞書を作成（1文字以下の単語を除外）
        word_weight_dict = {k: v for k, v in zip(feature_names, word_weights) if len(k) > 1}
        
        if not word_weight_dict:
            print("有効な単語が存在しません。TF-IDF計算をスキップします。")
            return {}
        
        # 単語の重みを降順にソート
        sorted_words = sorted(word_weight_dict.items(), key=lambda item: item[1], reverse=True)
        
        # 上位25%の単語数を計算
        top_n = max(int(len(sorted_words) * (top_percent / 100)), 1)  # 少なくとも1単語を保持
        top_words = sorted_words[:top_n]
        
        # 上位25%の単語のみを保持
        top_word_weight_dict = dict(top_words)

        # 小数点以下を指定桁数に丸める
        top_word_weight_dict = {k: round(v, decimal_places) for k, v in top_word_weight_dict.items()}
        
        return top_word_weight_dict
    
    except ValueError as ve:
        print(f"TF-IDF計算中にエラーが発生しました: {ve}")
        return {}
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return {}

def calculate_average_play_time(playtimes):
    if not playtimes:
        return 0  # データがない場合は0を返す
    average_minutes = sum(playtimes) / len(playtimes)
    average_hours = int(average_minutes // 60)  # 小数点以下を切り捨て
    return average_hours

def parse_steam_details(steam_id, twitch_id, additional_data):
    steam_headers = {
        'Accept-Language': 'ja'
    }

    steam_url = f'https://store.steampowered.com/api/appdetails?appids={steam_id}&cc=jp&l=japanese'

    try:
        response = requests.get(steam_url, headers=steam_headers)
        if response.status_code != 200:
            print(f"Steam APIのリクエストに失敗しました。ステータスコード: {response.status_code}")
            return None
        
        steam_details = response.json()
    except Exception as e:
        print(f"Steam APIのリクエスト中にエラーが発生しました。Steam ID: {steam_id}, エラー: {e}")
        return None

    game_data = steam_details.get(str(steam_id), {}).get('data', {})
    is_success = steam_details.get(str(steam_id), {}).get('success', False)

    if not is_success or not game_data:
        print(f"Steam ID {steam_id} のデータ取得に失敗しました。")
        return None

    # 必要な情報の抽出
    game_title = game_data.get('name', "")
    genres = game_data.get('genres', [])
    genres_list = [genre.get('description', '') for genre in genres]
    webpage_url = 'https://store.steampowered.com/app/' + str(steam_id)
    img_url = game_data.get('header_image', f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{steam_id}/header.jpg')

    price_overview = game_data.get('price_overview', {})
    price = price_overview.get('initial', 0) / 100  # 通常価格
    sale_price = price_overview.get('final', 0) / 100  # セール価格

    categories = game_data.get('categories', [])
    is_single_player = any(category.get('id') == 2 for category in categories)
    is_multi_player = any(category.get('id') == 1 for category in categories)

    platforms = game_data.get('platforms', {})
    is_device_windows = platforms.get('windows', False)
    is_device_mac = platforms.get('mac', False)

    publishers = game_data.get('publishers', [])
    developer_name = publishers[0] if publishers else 'Unknown'

    short_details = game_data.get('short_description', "")
    release_date = game_data.get('release_date', {}).get('date', "")

    # タグの取得（外部APIを使用）
    tag_res_url = f"https://steam-active-scrape.netlify.app/.netlify/functions/usertags?gameId={steam_id}"

    try:
        tag_res = requests.get(tag_res_url)
        if tag_res.status_code == 200:
            try:
                tags = tag_res.json().get('tags', [])
            except json.JSONDecodeError:
                print(f"タグ取得時に無効なJSONが返されました。Steam ID: {steam_id}")
                print(f"レスポンス内容: {tag_res.text}")
                tags = []
        else:
            print(f"タグ取得リクエストに失敗しました。ステータスコード: {tag_res.status_code}")
            tags = []
    except Exception as e:
        print(f"タグ取得中にエラーが発生しました: {e}")
        tags = []

    # 追加データの取得
    additional = additional_data.get(str(steam_id), {})
    play_time = additional.get('play_time', 0)

    sentiment_scores = additional.get('sentiment_scores', {})
    difficulty = sentiment_scores.get('難易度', 3.0)
    graphics = sentiment_scores.get('グラフィック', 3.0)
    story = sentiment_scores.get('ストーリー性', 3.0)
    music = sentiment_scores.get('音楽', 3.0)

    word_weights = additional.get('word_weights', {})
    review_text = word_weights if word_weights else {}

    result = {
        'game_title': game_title,
        'twitch_id': twitch_id,
        'steam_id': steam_id,
        'genres': genres_list,
        'webpage_url': webpage_url,
        'img_url': img_url,
        'price': price,
        'sale_price': sale_price,
        'is_single_player': is_single_player,
        'is_multi_player': is_multi_player,
        'is_device_windows': is_device_windows,
        'is_device_mac': is_device_mac,
        'play_time': play_time,
        'review_text': review_text,
        'difficulty': difficulty,
        'graphics': graphics,
        'story': story,
        'music': music,
        'developer_name': developer_name,
        'short_details': short_details,
        'release_date': release_date,
        'tags': tags,
        'total_views': additional.get('total_views', 0),
        'active_user': additional.get('active_user', 0),
        'active_chat_user': additional.get('active_chat_user', 0)
    }

    return result

def main():
    # top_games_data.jsonからデータを読み込む
    try:
        with open('top_games_data.json', 'r', encoding='utf-8') as f:
            top_games_data = json.load(f)
        if not isinstance(top_games_data, dict):
            print("top_games_data.jsonの形式が正しくありません。")
            return
        print(f"読み込んだゲームの数: {len(top_games_data)}")
    except Exception as e:
        print(f"top_games_data.jsonの読み込みに失敗しました: {e}")
        return

    # 出力ファイルのパスをスクリプトと同ディレクトリに設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'all_top_games_data.json')

    # 結果を格納するリスト
    all_data = []

    # 各ゲームについて処理
    for steam_id, game in tqdm(top_games_data.items(), total=len(top_games_data), desc="Processing games"):
        twitch_id = game.get('twitch_id')
        game_title = game.get('game_title')
        total_views = game.get('total_views', 0)
        active_user = game.get('active_user', 0)
        active_chat_user = game.get('active_chat_user', 0)

        # Steam IDの存在確認
        if not steam_id:
            print(f"Steam IDが存在しないゲーム: {game_title}. スキップします。")
            continue

        # レビューの取得
        reviews, playtimes = fetch_reviews(steam_id)

        if not reviews:
            print(f"appid {steam_id} のレビューが取得できませんでした。スキップします。")
            reviews = []
            playtimes = []

        # アスペクトに関連する評価の抽出とword_weightの収集
        aspect_scores, word_weights = extract_evaluations(reviews, ASPECT_EXPRESSIONS, window_size=5)

        # 感情スコアの計算
        sentiment_scores = calculate_sentiment_scores(aspect_scores)

        # Word Weightsの計算
        word_weight_dict = generate_word_weights(reviews, top_percent=25, decimal_places=2)

        # 平均プレイ時間の計算（時間単位、整数値、切り捨て）
        play_time_hours = calculate_average_play_time(playtimes)

        # Steamアクティビティデータを取得（すでにtop_games_data.jsonに含まれているが、念のため）
        activity_data = {
            'active_user': active_user,
            'active_chat_user': active_chat_user
        }

        # ゲーム詳細情報の取得と統合
        game_info = parse_steam_details(steam_id, twitch_id, {
            str(steam_id): {
                "play_time": play_time_hours,
                "sentiment_scores": sentiment_scores,
                "word_weights": word_weight_dict
            }
        })

        if game_info:
            # top_games_data.jsonのデータを保持しつつ、新しいデータを追加
            enriched_game = {
                'game_title': game_title,
                'twitch_id': twitch_id,
                'steam_id': steam_id,
                'genres': game_info.get('genres', []),
                'webpage_url': game_info.get('webpage_url', ''),
                'img_url': game_info.get('img_url', ''),
                'price': game_info.get('price', 0.0),
                'sale_price': game_info.get('sale_price', 0.0),
                'is_single_player': game_info.get('is_single_player', False),
                'is_multi_player': game_info.get('is_multi_player', False),
                'is_device_windows': game_info.get('is_device_windows', False),
                'is_device_mac': game_info.get('is_device_mac', False),
                'play_time': game_info.get('play_time', 0),
                'review_text': game_info.get('review_text', {}),
                'difficulty': game_info.get('difficulty', 3.0),
                'graphics': game_info.get('graphics', 3.0),
                'story': game_info.get('story', 3.0),
                'music': game_info.get('music', 3.0),
                'developer_name': game_info.get('developer_name', 'Unknown'),
                'short_details': game_info.get('short_details', ''),
                'release_date': game_info.get('release_date', ''),
                'tags': game_info.get('tags', []),
                'total_views': total_views,
                'active_user': activity_data['active_user'],
                'active_chat_user': activity_data['active_chat_user']
            }

            all_data.append(enriched_game)

        time.sleep(1)

    # 結果をJSONファイルに保存
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        print(f"すべての結果を '{output_file}' に保存しました。")
    except Exception as e:
        print(f"結果の保存に失敗しました: {e}")

if __name__ == '__main__':
    main()
