import requests
import csv
import concurrent.futures
import time
import os
import io

# --- НАСТРОЙКИ ---
API_LEVEL_LIST = "https://api.demonlist.org/level/classic/list"
API_USER_GET = "https://api.demonlist.org/user/get?id="
# Используем новый API для получения списка
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

def fetch_player_data(p_id, fallback_name, custom_data):
    # Данные из таблицы + дефолтные
    player_info = {
        'player_id': p_id, 'nickname': custom_data.get('nickname') or fallback_name, 
        'country': custom_data.get('country') or 'world', 'is_banned': custom_data.get('is_banned') or 'false', 
        'points': '0', 'photo': custom_data.get('photo') or f'images/profiles/Bez{p_id}.png',
        'social_yt': custom_data.get('social_yt') or '', 'social_tiwtch': custom_data.get('social_tiwtch') or '', 
        'info': custom_data.get('info') or '-', 'global_rank': '999'
    }
    player_info.update(custom_data)
    
    try:
        resp = requests.get(f"{API_USER_GET}{p_id}", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            # Обновляем актуальные данные из API (точки и ранк)
            player_info['points'] = str(int(float(data.get('points', 0))))
            player_info['global_rank'] = str(data.get('placement', '999'))
            if data.get('country'): player_info['country'] = get_country_code(data.get('country'))
    except: pass
    return player_info

def main():
    print("--- ЗАПУСК УМНОГО ОБНОВЛЕНИЯ ТОПА ---")
    
    unique_player_map = {}
    custom_player_data = {}

    # 1. Загружаем ТОП-200 из API (приоритет №1)
    try:
        print("Загрузка Leaderboard API...")
        resp = requests.get(API_LEADERBOARD, headers=HEADERS, timeout=15)
        users = resp.json().get('data', {}).get('users', [])
        for u in users:
            pid = str(u['id'])
            unique_player_map[pid] = u['username']
    except Exception as e: print(f"Ошибка API: {e}")

    # 2. Добавляем верификаторов (чтобы не потерять)
    try:
        api_levels = requests.get(API_LEVEL_LIST, headers=HEADERS, timeout=15).json()['data']['levels']
        for lvl in api_levels:
            if lvl.get('verifier'): 
                uid = str(lvl['verifier']['user_id'])
                if uid not in unique_player_map: unique_player_map[uid] = lvl['verifier']['username']
    except: pass

    # 3. Добавляем игроков из CSV (чтобы не потерять кастомные данные)
    try:
        csv_players = []
        resp = requests.get(URL_PLAYERS_CSV, headers=HEADERS, timeout=20)
        csv_players = list(csv.DictReader(io.StringIO(resp.text)))
        for p in csv_players:
            pid = str(p.get('player_id', ''))
            if pid:
                unique_player_map[pid] = p.get('nickname', 'Unknown')
                custom_player_data[pid] = p 
    except: pass

    # 4. Парсинг (собираем данные)
    print(f"Всего к обработке: {len(unique_player_map)} игроков.")
    final_players = []
    
    # Чтобы сохранить порядок, используем map (он сохраняет последовательность)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Создаем список аргументов
        args = [(pid, unique_player_map[pid], custom_player_data.get(pid, {})) for pid in unique_player_map]
        results = list(executor.map(lambda p: fetch_player_data(*p), args))
        final_players = results

    # 5. СОРТИРОВКА (ТОП-РАНК)
    # Сортируем так: сначала по ранку (число), если ранк 999 — то по очкам
    final_players.sort(key=lambda x: (int(x['global_rank']), -float(x['points'])))

    # 6. Сохранение
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info', 'global_rank'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(final_players)
    
    print("--- УСПЕШНО: Топ отсортирован и сохранен ---")

if __name__ == "__main__":
    main()
