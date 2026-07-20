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

URL_LEVELS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=1437425318&single=true&output=csv"
URL_PLAYERS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=93759483&single=true&output=csv"

COUNTRY_MAP = {"united-states": "us", "russia": "ru", "spain": "es", "canada": "ca", "portugal": "pt", "france": "fr", "united-kingdom": "gb", "japan": "jp", "south-korea": "kr", "australia": "au", "finland": "fi", "kazakhstan": "kz", "new-zealand": "nz", "brazil": "br", "germany": "de", "hungary": "hu", "romania": "ro", "poland": "pl", "netherlands": "nl", "vietnam": "vn", "austria": "at", "belarus": "by", "sweden": "se", "norway": "no", "denmark": "dk", "italy": "it", "ukraine": "ua", "turkey": "tr", "china": "cn", "switzerland": "ch", "belgium": "be"}

def get_thumbnail(video_link):
    if not video_link: return 'images/default.jpg'
    try:
        if 'watch?v=' in video_link: video_id = video_link.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in video_link: video_id = video_link.split('youtu.be/')[1].split('?')[0]
        else: return 'images/default.jpg'
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    except: return 'images/default.jpg'

def get_country_code(name):
    return COUNTRY_MAP.get(str(name).lower().replace(" ", "-"), "world")

def fetch_csv_data(url):
    try:
        # Добавлен параметр &t=... для обхода кэширования таблиц Google
        safe_url = url + f"&t={int(time.time())}"
        r = requests.get(safe_url, timeout=20)
        return list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'))))
    except Exception as e: 
        print(f"Ошибка загрузки CSV: {e}")
        return []

def fetch_player_data(p_id, nickname, custom_data):
    # Увеличен слип, чтобы сервер не выдал блокировку 429 Too Many Requests
    time.sleep(0.3) 
    csv_country = custom_data.get('country', 'world')
    player_info = {'player_id': p_id, 'nickname': nickname, 'country': csv_country, 'is_banned': 'false', 'points': '0', 'photo': custom_data.get('photo', f'images/profiles/Bez{p_id}.png'), 'social_yt': '', 'social_tiwtch': '', 'info': '-', 'global_rank': custom_data.get('global_rank', '999')}
    player_info.update(custom_data)
    player_records = []
    
    try:
        resp = requests.get(f"{API_USER_GET}{p_id}", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get('data') or {}
            if data.get('points'): player_info['points'] = str(int(float(data.get('points', 0))))
            if data.get('placement'): player_info['global_rank'] = str(data.get('placement'))
            
            if (not csv_country or csv_country == 'world') and data.get('country'):
                api_code = get_country_code(data.get('country'))
                if api_code != "world": player_info['country'] = api_code
                
            levels_data = data.get('levels') or {}
            for cat in ['hardest', 'main', 'extended', 'verified']:
                cat_data = levels_data.get(cat, [])
                if isinstance(cat_data, dict): cat_data = [cat_data]
                for lvl in cat_data:
                    if isinstance(lvl, dict) and lvl.get('id'):
                        player_records.append({'player_id': p_id, 'level_id': str(lvl['id']), 'progress': 100, 'video_url': lvl.get('video_url', '')})
        else:
            print(f"ВНИМАНИЕ! API отказало в доступе для {nickname} (Код: {resp.status_code}). Возможно сработал Rate Limit.")
    except Exception as e: 
        print(f"Ошибка при запросе данных игрока {nickname}: {e}")
        
    return player_info, player_records

def main():
    print("--- ЗАПУСК ПОЛНОЙ СИНХРОНИЗАЦИИ ---")
    
    # 1. Загрузка уровней из CSV
    hcr_levels = fetch_csv_data(URL_LEVELS_CSV)
    all_levels_dict = {str(lvl.get('level_id', '')): lvl for lvl in hcr_levels if lvl.get('level_id')}
    
    all_records = []
    seen_records = set()
    if os.path.exists('Records.csv'):
        with open('Records.csv', 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                if row.get('player_id'):
                    all_records.append(row)
                    seen_records.add((str(row['player_id']), str(row['level_id'])))

    # 2. Сбор игроков
    unique_player_map = {}
    custom_player_data = {}
    for p in fetch_csv_data(URL_PLAYERS_CSV):
        pid = str(p.get('player_id', ''))
        if pid: unique_player_map[pid] = p.get('nickname', 'Unknown'); custom_player_data[pid] = p

    offset = 0
    while True:
        try:
            resp = requests.get(f"{BASE_API_LEADERBOARD}?limit=50&offset={offset}", headers=HEADERS).json()
            users = resp.get('data', {}).get('users', [])
            if not users: break
            for u in users: unique_player_map[str(u['id'])] = u['username']
            offset += 50
            if offset >= 500: break
        except Exception as e:
            print(f"Ошибка получения глобального лидерборда (offset {offset}): {e}")
            break

    # 3. Уровни из API (с ГЛОБАЛЬНЫМ ОБНОВЛЕНИЕМ существующих)
    try:
        api_levels = requests.get(API_LEVEL_LIST, headers=HEADERS).json()['data']['levels']
        for lvl in api_levels:
            l_id = str(lvl['id'])
            v_url = lvl.get('verification_url', '')
            
            # Если уровня нет - добавляем
            if l_id not in all_levels_dict:
                all_levels_dict[l_id] = {
                    'level_id': l_id, 'name': lvl['name'], 'publisher_id': '', 
                    'builder': lvl.get('holder', 'Unknown'), 
                    'verifier_id': str(lvl['verifier']['user_id']) if lvl.get('verifier') else '', 
                    'video_url': v_url, 
                    'thumbnail': get_thumbnail(v_url),
                    'info': 'уровень из global demonlist', 'points': lvl.get('points', 0)
                }
            # Если уровень ЕСТЬ - обновляем ему очки и превью (если их не было)
            else:
                all_levels_dict[l_id]['points'] = lvl.get('points', all_levels_dict[l_id].get('points', 0))
                if not all_levels_dict[l_id].get('thumbnail') or all_levels_dict[l_id].get('thumbnail') == 'images/default.jpg':
                    all_levels_dict[l_id]['thumbnail'] = get_thumbnail(v_url)
                    
            if lvl.get('verifier'): 
                uid = str(lvl['verifier']['user_id'])
                if uid not in unique_player_map: unique_player_map[uid] = lvl['verifier']['username']
    except Exception as e: 
        print(f"Ошибка загрузки списка уровней с сервера: {e}")

    # 4. Парсинг игроков (Количество потоков уменьшено до 3, чтобы не получить бан по IP)
    final_players = []
    print(f"Начинается парсинг {len(unique_player_map)} игроков. Это может занять некоторое время...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid], custom_player_data.get(pid, {})): pid for pid in unique_player_map}
        for f in concurrent.futures.as_completed(futures):
            p, r = f.result()
            final_players.append(p)
            for rec in r:
                if (str(rec['player_id']), str(rec['level_id'])) not in seen_records:
                    all_records.append(rec)
                    seen_records.add((str(rec['player_id']), str(rec['level_id'])))

    # 5. Сохранение
    final_players.sort(key=lambda x: int(x['global_rank']) if x['global_rank'].isdigit() else 999)
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info', 'global_rank'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(final_players)
        
    with open('Levels.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['level_id', 'name', 'publisher_id', 'builder', 'verifier_id', 'video_url', 'thumbnail', 'info', 'points'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_levels_dict.values())
        
    with open('Records.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'level_id', 'progress', 'video_url'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_records)
        
    print("--- УСПЕШНО ЗАВЕРШЕНО ---")

if __name__ == "__main__":
    main()
