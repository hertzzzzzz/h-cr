import requests
import csv
import concurrent.futures
import time
import io
import os
import sys

# --- НАСТРОЙКИ ---
API_LEVEL_LIST = "https://api.demonlist.org/level/classic/list"
API_USER_GET = "https://api.demonlist.org/user/get?id="
API_LEADERBOARD = "https://api.demonlist.org/leaderboard/user/list"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

URL_PLAYERS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=93759483&single=true&output=csv"

COUNTRY_MAP = {
    "united-states": "us", "russia": "ru", "spain": "es", "canada": "ca",
    "portugal": "pt", "france": "fr", "united-kingdom": "gb", "japan": "jp",
    "south-korea": "kr", "australia": "au", "finland": "fi", "kazakhstan": "kz",
    "new-zealand": "nz", "brazil": "br", "germany": "de", "hungary": "hu",
    "romania": "ro", "poland": "pl", "netherlands": "nl", "vietnam": "vn", "austria": "at",
    "belarus": "by"
}

def get_country_code(country_name):
    if not country_name: return "world"
    name = str(country_name).lower().replace(" ", "-")
    return COUNTRY_MAP.get(name, "world")

def get_thumbnail(video_link):
    if not video_link: return 'images/default.jpg'
    try:
        if 'watch?v=' in video_link: video_id = video_link.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in video_link: video_id = video_link.split('youtu.be/')[1].split('?')[0]
        else: return 'images/default.jpg'
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    except: return 'images/default.jpg'

def fetch_csv_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        return list(csv.DictReader(io.StringIO(response.text)))
    except: return []

def fetch_player_data(p_id, fallback_name, custom_data):
    time.sleep(0.3)
    player_info = {
        'player_id': p_id, 'nickname': custom_data.get('nickname') or fallback_name, 
        'country': custom_data.get('country') or 'world', 'is_banned': custom_data.get('is_banned') or 'false', 
        'points': '0.0', 'photo': custom_data.get('photo') or f'images/profiles/Bez{p_id}.png',
        'social_yt': custom_data.get('social_yt') or '', 'social_tiwtch': custom_data.get('social_tiwtch') or '', 
        'info': custom_data.get('info') or '- информация ещё не была добавлена -', 'global_rank': custom_data.get('global_rank') or '0'
    }
    player_records = []
    try:
        response = requests.get(f"{API_USER_GET}{p_id}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', {})
            if isinstance(data, dict):
                player_info['nickname'] = data.get('name') or player_info['nickname']
                player_info['points'] = f"{float(data.get('points', 0)):.2f}"
                player_info['global_rank'] = str(data.get('placement', '0'))
                api_country = data.get('country')
                if api_country: player_info['country'] = get_country_code(api_country)
                
                levels_data = data.get('levels', {})
                if isinstance(levels_data, dict):
                    for cat in ['hardest', 'main', 'extended', 'verified']:
                        cat_data = levels_data.get(cat)
                        if isinstance(cat_data, dict): cat_data = [cat_data]
                        if isinstance(cat_data, list):
                            for lvl in cat_data:
                                if isinstance(lvl, dict) and lvl.get('id'):
                                    player_records.append({'player_id': p_id, 'level_id': str(lvl.get('id')), 'progress': 100, 'video_url': lvl.get('video_url', '')})
    except: pass
    return player_info, player_records

def main():
    print("--- ЗАПУСК ПОЛНОГО ОБНОВЛЕНИЯ ---")
    all_records = []
    seen_records = set()

    # Загрузка старых рекордов
    if os.path.exists('Records.csv'):
        with open('Records.csv', 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                if row.get('player_id'):
                    all_records.append(row)
                    seen_records.add((str(row['player_id']), str(row['level_id'])))

    unique_player_map = {}
    player_custom_data = {}

    # 1. API Leaderboard
    try:
        resp = requests.get(API_LEADERBOARD, headers=HEADERS, timeout=15)
        users = resp.json().get('data', {}).get('users', [])
        for u in users:
            pid = str(u.get('id'))
            unique_player_map[pid] = u.get('username')
    except Exception as e: print(f"Ошибка API: {e}")

    # 2. Уровни
    all_levels = []
    try:
        levels_api = requests.get(API_LEVEL_LIST, headers=HEADERS).json()['data']['levels']
        for lvl in levels_api:
            all_levels.append({
                'level_id': str(lvl['id']), 'name': lvl['name'], 'publisher_id': '', 
                'builder': lvl.get('holder', 'Unknown'), 'verifier_id': str(lvl['verifier']['user_id']) if lvl.get('verifier') else '',
                'video_url': lvl.get('verification_url', ''), 'thumbnail': get_thumbnail(lvl.get('verification_url')),
                'info': 'уровень из global demonlist', 'points': lvl.get('points', 0)
            })
    except: pass

    # 3. Google Таблицы
    hcr_players = fetch_csv_data(URL_PLAYERS_CSV)
    for p in hcr_players:
        pid = str(p.get('player_id', ''))
        if pid:
            unique_player_map[pid] = p.get('nickname', 'Unknown')
            player_custom_data[pid] = p

    # 4. Парсинг
    final_players = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid], player_custom_data.get(pid, {})): pid for pid in unique_player_map}
        for future in concurrent.futures.as_completed(futures):
            p, r = future.result()
            final_players.append(p)
            for rec in r:
                if (str(rec['player_id']), str(rec['level_id'])) not in seen_records:
                    all_records.append(rec)
                    seen_records.add((str(rec['player_id']), str(rec['level_id'])))
    
    # 5. Сохранение
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info', 'global_rank'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(final_players)
    with open('Levels.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['level_id', 'name', 'publisher_id', 'builder', 'verifier_id', 'video_url', 'thumbnail', 'info', 'points'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_levels)
    with open('Records.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'level_id', 'progress', 'video_url'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_records)
    print("--- УСПЕШНО ---")

if __name__ == "__main__":
    main()
