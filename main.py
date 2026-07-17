import requests
import csv
import concurrent.futures
import time
import os
import io

# --- НАСТРОЙКИ ---
API_LEVEL_LIST = "https://api.demonlist.org/level/classic/list"
API_USER_GET = "https://api.demonlist.org/user/get?id="
BASE_API_LEADERBOARD = "https://api.demonlist.org/leaderboard/user/list"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
URL_PLAYERS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=93759483&single=true&output=csv"

COUNTRY_MAP = {"united-states": "us", "russia": "ru", "spain": "es", "canada": "ca", "portugal": "pt", "france": "fr", "united-kingdom": "gb", "japan": "jp", "south-korea": "kr", "australia": "au", "finland": "fi", "kazakhstan": "kz", "new-zealand": "nz", "brazil": "br", "germany": "de", "hungary": "hu", "romania": "ro", "poland": "pl", "netherlands": "nl", "vietnam": "vn", "austria": "at", "belarus": "by", "sweden": "se", "norway": "no", "denmark": "dk", "italy": "it", "ukraine": "ua", "turkey": "tr", "china": "cn", "switzerland": "ch", "belgium": "be"}

def get_country_code(name):
    return COUNTRY_MAP.get(str(name).lower().replace(" ", "-"), "world")

def fetch_player_data(p_id, nickname, custom_data):
    # Данные по умолчанию из CSV
    player_info = {
        'player_id': p_id, 'nickname': nickname, 'country': 'world', 'is_banned': 'false', 
        'points': '0', 'photo': custom_data.get('photo', f'images/profiles/Bez{p_id}.png'), 
        'social_yt': '', 'social_tiwtch': '', 'info': '-', 'global_rank': '999'
    }
    player_info.update(custom_data)
    
    # ПРИОРИТЕТ API: перезаписываем данные, если они пришли из API
    try:
        resp = requests.get(f"{API_USER_GET}{p_id}", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            player_info['points'] = str(int(float(data.get('points', 0))))
            player_info['global_rank'] = str(data.get('placement', '999'))
            if data.get('country'): player_info['country'] = get_country_code(data.get('country'))
    except: pass
    return player_info

def main():
    print("--- ЗАПУСК С ПРИОРИТЕТОМ API ---")
    
    # 1. Загружаем CSV
    unique_player_map = {}
    custom_player_data = {}
    try:
        r = requests.get(URL_PLAYERS_CSV, headers=HEADERS, timeout=20)
        for p in csv.DictReader(io.StringIO(r.text)):
            pid = str(p.get('player_id', ''))
            if pid: unique_player_map[pid] = p.get('nickname', 'Unknown'); custom_player_data[pid] = p
    except: pass

    # 2. API Leaderboard (Пагинация) - ДОБАВЛЯЕМ ВСЕХ
    offset = 0
    while True:
        resp = requests.get(f"{BASE_API_LEADERBOARD}?limit=50&offset={offset}", headers=HEADERS).json()
        users = resp.get('data', {}).get('users', [])
        if not users: break
        for u in users:
            pid = str(u['id'])
            unique_player_map[pid] = u['username'] # Принудительно добавляем всех из API
        offset += 50
        if offset >= 500: break

    # 3. Парсинг
    final_players = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid], custom_player_data.get(pid, {})): pid for pid in unique_player_map}
        for f in concurrent.futures.as_completed(futures): final_players.append(f.result())
    
    # 4. Сортировка по Рангу (API Ранг > Ранг из CSV)
    final_players.sort(key=lambda x: int(x['global_rank']) if x['global_rank'].isdigit() else 999)

    # 5. Сохранение
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info', 'global_rank'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(final_players)
    
    print("--- УСПЕШНО ---")

if __name__ == "__main__":
    main()
