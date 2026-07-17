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
API_LEADERBOARD = "https://api.demonlist.org/user/ranking?limit=200"

URL_LEVELS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=1437425318&single=true&output=csv"
URL_RANKINGS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=2093715526&single=true&output=csv"
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
    if "russia" in name: return "ru"
    if "united-states" in name: return "us"
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
    for _ in range(3):
        try:
            response = requests.get(url, timeout=20)
            response.encoding = 'utf-8'
            reader = csv.DictReader(io.StringIO(response.text))
            if reader.fieldnames:
                reader.fieldnames = [str(name).strip().lower() for name in reader.fieldnames]
            return list(reader)
        except Exception:
            time.sleep(3)
    return []

def fetch_player_data(p_id, fallback_name, custom_data):
    time.sleep(0.5)
    player_info = {
        'player_id': p_id, 'nickname': custom_data.get('nickname') or fallback_name, 
        'country': custom_data.get('country') or 'world', 'is_banned': custom_data.get('is_banned') or 'false', 
        'points': '0.0', 'photo': custom_data.get('photo') or f'images/profiles/Bez{p_id}.png',
        'social_yt': custom_data.get('social_yt') or '', 'social_tiwtch': custom_data.get('social_tiwtch') or '', 
        'info': custom_data.get('info') or '- информация ещё не была добавлена -', 'global_rank': custom_data.get('global_rank') or '0'
    }
    player_records = []
    try:
        response = requests.get(f"{API_USER_GET}{p_id}", timeout=10)
        if response.status_code == 200:
            req_json = response.json()
            if isinstance(req_json, dict):
                u_data = req_json.get('data', {})
                if isinstance(u_data, dict):
                    player_info['nickname'] = u_data.get('name') or player_info['nickname']
                    player_info['points'] = f"{float(u_data.get('points', 0)):.2f}"
                    player_info['global_rank'] = str(u_data.get('placement', '0'))
                    api_country = get_country_code(u_data.get('country'))
                    if api_country != "world": player_info['country'] = api_country

                    levels_data = u_data.get('levels', {})
                    if isinstance(levels_data, dict):
                        for cat in ['hardest', 'main', 'extended', 'verified']:
                            cat_data = levels_data.get(cat)
                            if isinstance(cat_data, dict): cat_data = [cat_data]
                            if isinstance(cat_data, list):
                                for lvl in cat_data:
                                    if isinstance(lvl, dict):
                                        l_id = lvl.get('id')
                                        if l_id: player_records.append({'player_id': p_id, 'level_id': l_id, 'progress': 100, 'video_url': lvl.get('video_url', '')})
    except: pass
    return player_info, player_records

def main():
    print("--- ЗАПУСК ОБНОВЛЕНИЯ ---")
    all_records = []
    seen_records = set()
    if os.path.exists('Records.csv'):
        with open('Records.csv', 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                if row.get('player_id'):
                    all_records.append(row)
                    seen_records.add((str(row['player_id']), str(row['level_id'])))

    hcr_players = fetch_csv_data(URL_PLAYERS_CSV)
    api_levels = requests.get(API_LEVEL_LIST).json()['data']['levels']
    
    unique_player_map = {}
    player_custom_data = {}

    # Фундамент: Топ-200 из API
    try:
        data = requests.get(API_LEADERBOARD).json().get('data', [])
        for p in data:
            pid = str(p.get('id', p.get('user_id', '')))
            unique_player_map[pid] = p.get('name', 'Unknown')
    except: pass

    # Объединение с ручными правками и верификаторами
    for p in hcr_players:
        pid = str(p.get('player_id', ''))
        if pid: unique_player_map[pid] = p.get('nickname', 'Unknown'); player_custom_data[pid] = p 
    
    for lvl in api_levels:
        if lvl.get('verifier'): 
            uid = str(lvl['verifier']['user_id'])
            if uid not in unique_player_map: unique_player_map[uid] = lvl['verifier']['username']

    # Парсинг
    final_players = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid], player_custom_data.get(pid, {})): pid for pid in unique_player_map}
        for future in concurrent.futures.as_completed(futures):
            p_info, p_recs = future.result()
            final_players.append(p_info)
            for rec in p_recs:
                if (str(rec['player_id']), str(rec['level_id'])) not in seen_records:
                    all_records.append(rec)
                    seen_records.add((str(rec['player_id']), str(rec['level_id'])))
    
    # Сохранение
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info', 'global_rank'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(final_players)
    with open('Records.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'level_id', 'progress', 'video_url'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_records)
    print("--- ГОТОВО ---")

if __name__ == "__main__":
    main()
