import requests
import csv
import concurrent.futures
import time
import os
import io

# --- НАСТРОЙКИ ---
API_LEVEL_LIST = "https://api.demonlist.org/level/classic/list"
API_USER_GET = "https://api.demonlist.org/user/get?id="
API_LEADERBOARD = "https://api.demonlist.org/leaderboard/user/list?limit=200"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

URL_PLAYERS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=93759483&single=true&output=csv"

COUNTRY_MAP = {
    "united-states": "us", "russia": "ru", "spain": "es", "canada": "ca", "portugal": "pt", 
    "france": "fr", "united-kingdom": "gb", "japan": "jp", "south-korea": "kr", "australia": "au", 
    "finland": "fi", "kazakhstan": "kz", "new-zealand": "nz", "brazil": "br", "germany": "de", 
    "hungary": "hu", "romania": "ro", "poland": "pl", "netherlands": "nl", "vietnam": "vn", 
    "austria": "at", "belarus": "by", "sweden": "se", "norway": "no", "denmark": "dk", 
    "italy": "it", "ukraine": "ua", "turkey": "tr", "china": "cn", "switzerland": "ch", "belgium": "be"
}

def get_country_code(country_name):
    return COUNTRY_MAP.get(str(country_name).lower().replace(" ", "-"), "world")

def fetch_csv_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        return list(csv.DictReader(io.StringIO(response.text)))
    except: return []

def fetch_player_data(p_id, nickname, custom_data):
    # Данные по умолчанию + данные из таблицы
    player_info = {'player_id': p_id, 'nickname': nickname, 'country': 'world', 'points': '0', 'global_rank': '0', 'info': '-'}
    player_info.update(custom_data)
    try:
        resp = requests.get(f"{API_USER_GET}{p_id}", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            player_info['points'] = str(int(float(data.get('points', 0))))
            player_info['global_rank'] = str(data.get('placement', '0'))
            if data.get('country'): player_info['country'] = get_country_code(data.get('country'))
    except: pass
    return player_info

def main():
    print("--- ЗАПУСК ПОЛНОЙ СИНХРОНИЗАЦИИ ---")
    
    # 1. Читаем старые файлы (сохраняем HCR рейтинг и остальные колонки)
    old_levels = {}
    if os.path.exists('Levels.csv'):
        with open('Levels.csv', 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f): old_levels[row['level_id']] = row

    # 2. Обновляем Уровни из API
    new_levels_data = []
    try:
        levels_api = requests.get(API_LEVEL_LIST, headers=HEADERS).json()['data']['levels']
        for lvl in levels_api:
            lid = str(lvl['id'])
            # Если уровень старый, сохраняем его колонки, обновляем только точки
            if lid in old_levels:
                row = old_levels[lid]
                row['points'] = lvl.get('points', 0)
                new_levels_data.append(row)
            else:
                new_levels_data.append({'level_id': lid, 'name': lvl['name'], 'points': lvl.get('points', 0), 'info': 'new'})
    except Exception as e: print(f"Ошибка уровней: {e}")

    # 3. Обновляем Игроков
    unique_player_map = {}
    custom_player_data = {}
    
    # API топов
    try:
        resp = requests.get(API_LEADERBOARD, headers=HEADERS)
        for u in resp.json().get('data', {}).get('users', []):
            unique_player_map[str(u['id'])] = u['username']
    except: pass
    
    # Таблица
    for p in fetch_csv_data(URL_PLAYERS_CSV):
        pid = str(p.get('player_id', ''))
        if pid:
            unique_player_map[pid] = p.get('nickname', 'Unknown')
            custom_player_data[pid] = p

    # Парсинг
    final_players = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid], custom_player_data.get(pid, {})): pid for pid in unique_player_map}
        for f in concurrent.futures.as_completed(futures): final_players.append(f.result())

    # 4. Сохранение ВСЕГО
    with open('Levels.csv', 'w', newline='', encoding='utf-8-sig') as f:
        if new_levels_data:
            writer = csv.DictWriter(f, fieldnames=new_levels_data[0].keys(), extrasaction='ignore')
            writer.writeheader(); writer.writerows(new_levels_data)
            
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'points', 'global_rank', 'info'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(final_players)
        
    print("--- ВСЕ ФАЙЛЫ ОБНОВЛЕНЫ ---")

if __name__ == "__main__":
    main()
