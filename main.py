import requests
import csv
import concurrent.futures
import time
import io
import os

# --- НАСТРОЙКИ ---
API_LEVEL_LIST = "https://api.demonlist.org/level/classic/list"
API_USER_GET = "https://api.demonlist.org/user/get?id="

# Твои ссылки
URL_LEVELS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=1437425318&single=true&output=csv"
URL_RANKINGS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=2093715526&single=true&output=csv"
URL_PLAYERS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=93759483&single=true&output=csv"

# ... (функции get_country_code и get_thumbnail остаются те же) ...

def get_country_code(country_name):
    if not country_name: return "world"
    name = str(country_name).lower().replace(" ", "-")
    if "russia" in name: return "ru"
    if "united-states" in name: return "us"
    return {"united-kingdom": "gb", "spain": "es", "canada": "ca", "portugal": "pt", "france": "fr", "japan": "jp", "south-korea": "kr", "australia": "au", "finland": "fi", "kazakhstan": "kz", "new-zealand": "nz", "brazil": "br", "germany": "de", "hungary": "hu", "romania": "ro", "poland": "pl", "netherlands": "nl", "vietnam": "vn", "austria": "at", "belarus": "by"}.get(name, "world")

def get_thumbnail(video_link):
    if not video_link: return 'images/default.jpg'
    try:
        if 'watch?v=' in video_link: video_id = video_link.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in video_link: video_id = video_link.split('youtu.be/')[1].split('?')[0]
        else: return 'images/default.jpg'
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    except: return 'images/default.jpg'

def fetch_csv_data_safe(url):
    """Быстрая загрузка без бесконечных попыток."""
    try:
        print(f"Попытка загрузки таблицы: {url[:50]}...")
        response = requests.get(url, timeout=10) # 10 секунд - не ответили, значит пропускаем
        response.encoding = 'utf-8'
        reader = csv.DictReader(io.StringIO(response.text))
        if reader.fieldnames:
            reader.fieldnames = [str(name).strip().lower() for name in reader.fieldnames]
        return list(reader)
    except Exception as e:
        print(f"!!! Таблица не ответила (пропускаем): {e}")
        return []

def fetch_player_data(p_id, fallback_name):
    time.sleep(0.5)
    player_info = {'player_id': p_id, 'nickname': fallback_name, 'country': 'world', 'is_banned': 'false', 'points': '0.0', 'photo': f'images/profiles/Bez{p_id}.png', 'social_yt': '', 'social_tiwtch': '', 'info': '- информация отсутствует -'}
    player_records = []
    try:
        response = requests.get(f"{API_USER_GET}{p_id}", timeout=10)
        if response.status_code == 200:
            u_data = response.json().get('data', {})
            player_info['nickname'] = u_data.get('name') or fallback_name
            player_info['points'] = f"{float(u_data.get('points', 0)):.2f}"
            player_info['country'] = get_country_code(u_data.get('country'))
            for cat in ['hardest', 'main', 'extended', 'verified']:
                for lvl in u_data.get('levels', {}).get(cat, []):
                    l_id = lvl.get('id')
                    if l_id: player_records.append({'player_id': p_id, 'level_id': l_id, 'progress': 100, 'video_url': lvl.get('video_url', '')})
    except: pass
    return player_info, player_records

def main():
    print("--- ЗАПУСК (ПРИОРИТЕТ API) ---")
    
    # 1. Загружаем старые рекорды (база)
    all_records = []
    seen_records = set()
    if os.path.exists('Records.csv'):
        with open('Records.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_records.append(row)
                seen_records.add((str(row.get('player_id','')), str(row.get('level_id',''))))

    # 2. API СНАЧАЛА
    print("Загрузка API Demonlist...")
    resp = requests.get(API_LEVEL_LIST, timeout=15)
    api_levels = resp.json()['data']['levels']
    
    # 3. ТАБЛИЦЫ ПОТОМ (необязательно)
    hcr_players = fetch_csv_data_safe(URL_PLAYERS_CSV)
    hcr_levels = fetch_csv_data_safe(URL_LEVELS_CSV)
    hcr_rankings = fetch_csv_data_safe(URL_RANKINGS_CSV)
    
    all_players = hcr_players
    all_levels = hcr_levels
    rankings_data = hcr_rankings
    seen_player_ids = {str(p.get('player_id', '')) for p in all_players}

    # ... (дальше логика обработки та же) ...
    unique_player_map = {}
    for i, lvl in enumerate(api_levels):
        l_id = str(lvl['id'])
        req = str(lvl.get('list_percent', 100)).replace('%', '') 
        
        all_levels.append({'level_id': l_id, 'name': lvl['name'], 'publisher_id': '', 'builder': lvl.get('holder', 'Unknown'), 'verifier_id': str(lvl['verifier']['user_id']) if lvl.get('verifier') else '', 'video_url': lvl.get('verification_url', ''), 'thumbnail': get_thumbnail(lvl.get('verification_url')), 'info': 'PCR Level', 'points': lvl.get('points', 0)})
        rankings_data.append({'ranking_id': f'PCR_{i}', 'top_name': 'PCR', 'level_id': l_id, 'position': i + 1, 'requirement': req})
        
        if lvl.get('verifier'): 
            uid = str(lvl['verifier']['user_id'])
            if uid not in seen_player_ids:
                unique_player_map[uid] = lvl['verifier']['username']

    # Парсинг игроков...
    print(f"Парсинг {len(unique_player_map)} игроков из API...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid]): pid for pid in unique_player_map.keys()}
        for future in concurrent.futures.as_completed(futures):
            p_info, p_recs = future.result()
            all_players.append(p_info)
            for rec in p_recs:
                key = (str(rec['player_id']), str(rec['level_id']))
                if key not in seen_records:
                    all_records.append(rec)
                    seen_records.add(key)

    # Сохранение (теперь без паники, даже если таблицы были пустыми)
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_players)
    with open('Records.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'level_id', 'progress', 'video_url'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_records)
    print("Готово!")

if __name__ == "__main__":
    main()
