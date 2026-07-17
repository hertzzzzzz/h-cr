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
        except Exception: time.sleep(3)
    return []

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
        response = requests.get(f"{API_USER_GET}{p_id}", timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', {})
            if isinstance(data, dict):
                player_info['nickname'] = data.get('name') or player_info['nickname']
                player_info['points'] = f"{float(data.get('points', 0)):.2f}"
                player_info['global_rank'] = str(data.get('placement', '0'))
                
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
    print("--- ЗАПУСК УСИЛЕННОГО СБОРА ИГРОКОВ ---")
    
    unique_player_map = {} # Здесь будут ТОЛЬКО ID и имена
    player_custom_data = {} # Здесь данные из твоей Google Таблицы

    # 1. ШАГ ПЕРВЫЙ: Берем всех из Leaderboard (ЭТО НАШ ФУНДАМЕНТ)
    try:
        print("Загрузка Leaderboard...")
        lb_response = requests.get(API_LEADERBOARD, timeout=20)
        if lb_response.status_code == 200:
            lb_data = lb_response.json().get('data', [])
            for p in lb_data:
                pid = str(p.get('id', p.get('user_id', '')))
                if pid:
                    unique_player_map[pid] = p.get('name', 'Unknown')
        print(f"Из Leaderboard API получено {len(unique_player_map)} игроков.")
    except Exception as e:
        print(f"Ошибка загрузки Leaderboard: {e}")

    # 2. ШАГ ВТОРОЙ: Дополняем из Google Таблицы (на случай, если кого-то нет в топе, но мы хотим его видеть)
    hcr_players = fetch_csv_data(URL_PLAYERS_CSV)
    for p in hcr_players:
        pid = str(p.get('player_id', ''))
        if pid:
            unique_player_map[pid] = p.get('nickname', 'Unknown')
            player_custom_data[pid] = p 
    print(f"После добавления из Google Таблиц всего уникальных ID: {len(unique_player_map)}")

    # 3. ШАГ ТРЕТИЙ: Парсинг (забираем полные данные каждого найденного ID)
    final_players = []
    # ... (дальше идет запуск ThreadPoolExecutor и сохранение, как было)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid], player_custom_data.get(pid, {})): pid for pid in unique_player_map}
        for future in concurrent.futures.as_completed(futures):
            p, r = future.result()
            final_players.append(p)
            for rec in r:
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
