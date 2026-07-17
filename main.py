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

def fetch_csv_data(url):
    for _ in range(3):
        try:
            response = requests.get(url, timeout=20)
            response.encoding = 'utf-8'
            reader = csv.DictReader(io.StringIO(response.text))
            if reader.fieldnames:
                reader.fieldnames = [str(name).strip().lower() for name in reader.fieldnames]
            return list(reader)
        except: time.sleep(3)
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
    print("--- ЗАПУСК ПОЛНОГО ОБНОВЛЕНИЯ ---")
    all_records = []
    seen_records = set() # <--- ИНИЦИАЛИЗАЦИЯ

    if os.path.exists('Records.csv'):
        with open('Records.csv', 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                if row.get('player_id'):
                    all_records.append(row)
                    seen_records.add((str(row['player_id']), str(row['level_id'])))

    hcr_players = fetch_csv_data(URL_PLAYERS_CSV)
    
    unique_player_map = {}
    player_custom_data = {}

    # 1. Топ-200 из API
    try:
        data = requests.get(API_LEADERBOARD, timeout=15).json().get('data', [])
        for p in data:
            pid = str(p.get('id', p.get('user_id', '')))
            unique_player_map[pid] = p.get('name', 'Unknown')
    except: pass

    # 2. Табличные данные
    for p in hcr_players:
        pid = str(p.get('player_id', ''))
        if pid:
            unique_player_map[pid] = p.get('nickname', 'Unknown')
            player_custom_data[pid] = p 
    
    print(f"Всего игроков для сбора: {len(unique_player_map)}")

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
    
    # 3. Сохранение
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info', 'global_rank'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(final_players)
        
    with open('Records.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'level_id', 'progress', 'video_url'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_records)
    print("--- УСПЕШНО ---")

if __name__ == "__main__":
    main()
