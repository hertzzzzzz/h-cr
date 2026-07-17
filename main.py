import requests
import csv
import concurrent.futures
import time
import os

# --- НАСТРОЙКИ ---
API_LEADERBOARD = "https://api.demonlist.org/leaderboard/user/list"
API_USER_GET = "https://api.demonlist.org/user/get?id="
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

URL_PLAYERS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=93759483&single=true&output=csv"

# Жесткий маппинг для флагов (имя из API -> имя файла)
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

def fetch_player_data(p_id, nickname, custom_data):
    time.sleep(0.3)
    # Базовые данные
    player_info = {
        'player_id': p_id, 'nickname': nickname, 'country': 'world', 'is_banned': 'false', 
        'points': '0', 'photo': f'images/profiles/Bez{p_id}.png', 'info': '-', 'global_rank': '0'
    }
    # Применяем ручные правки из таблицы
    if custom_data:
        player_info.update(custom_data)
    
    try:
        response = requests.get(f"{API_USER_GET}{p_id}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', {})
            if isinstance(data, dict):
                player_info['points'] = str(int(float(data.get('points', 0))))
                player_info['global_rank'] = str(data.get('placement', '0'))
                # Принудительно ставим код страны
                api_country = data.get('country')
                if api_country:
                    player_info['country'] = get_country_code(api_country)
    except: pass
    return player_info

def main():
    print("--- ЗАПУСК ОБНОВЛЕНИЯ (ФИНАЛ) ---")
    unique_player_map = {}
    player_custom_data = {}

    # 1. Берем топ из нового API
    try:
        resp = requests.get(API_LEADERBOARD, headers=HEADERS, timeout=15)
        users = resp.json().get('data', {}).get('users', [])
        for u in users:
            pid = str(u.get('id'))
            unique_player_map[pid] = u.get('username')
        print(f"Из Leaderboard API получено {len(unique_player_map)} игроков.")
    except Exception as e:
        print(f"Ошибка API: {e}")

    # 2. Дополняем из таблицы
    hcr_players = fetch_csv_data(URL_PLAYERS_CSV)
    for p in hcr_players:
        pid = str(p.get('player_id', ''))
        if pid:
            unique_player_map[pid] = p.get('nickname', 'Unknown')
            player_custom_data[pid] = p 

    # 3. Парсинг
    final_players = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid], player_custom_data.get(pid, {})): pid for pid in unique_player_map}
        for future in concurrent.futures.as_completed(futures):
            final_players.append(future.result())
    
    # 4. Сохранение
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info', 'global_rank'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(final_players)
    print(f"Сохранено {len(final_players)} игроков. Успех!")

if __name__ == "__main__":
    main()
