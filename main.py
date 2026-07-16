import requests
import csv
import concurrent.futures
import time
import io
import os

# --- НАСТРОЙКИ ---
API_LEVEL_LIST = "https://api.demonlist.org/level/classic/list"
API_USER_GET = "https://api.demonlist.org/user/get?id="

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
    # Попробуем загрузить файл 3 раза, если первый не удался
    for attempt in range(3):
        try:
            print(f"Попытка загрузки данных ({attempt + 1}/3)...")
            response = requests.get(url, timeout=30) # Увеличили таймаут до 30 секунд
            response.encoding = 'utf-8'
            reader = csv.DictReader(io.StringIO(response.text))
            
            if reader.fieldnames:
                reader.fieldnames = [str(name).strip().lower() for name in reader.fieldnames]
            
            return list(reader)
            
        except Exception as e:
            print(f"Ошибка при попытке {attempt + 1}: {e}")
            time.sleep(5) # Пауза 5 секунд перед повторной попыткой
            
    print("КРИТИЧЕСКАЯ ОШИБКА: Не удалось загрузить CSV после 3 попыток.")
    return []

def fetch_player_data(p_id, fallback_name):
    time.sleep(0.5)
    player_info = {
        'player_id': p_id, 'nickname': fallback_name, 'country': 'world',
        'is_banned': 'false', 'points': '0.0', 'photo': f'images/profiles/Bez{p_id}.png',
        'social_yt': '', 'social_tiwtch': '', 'info': '- информация ещё не была добавлена -'
    }
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
    print("--- ЗАПУСК ОБНОВЛЕНИЯ ДАННЫХ ---")
    
    # 1. ЗАГРУЖАЕМ СТАРЫЕ РЕКОРДЫ (чтобы не потерять их при обновлении)
    all_records = []
    seen_records = set()
    if os.path.exists('Records.csv'):
        try:
            with open('Records.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('player_id') and row.get('level_id'):
                        all_records.append(row)
                        seen_records.add((str(row['player_id']), str(row['level_id'])))
            print(f"Успешно загружено {len(all_records)} старых записей из Records.csv.")
        except Exception as e:
            print(f"ВНИМАНИЕ: Ошибка чтения старых рекордов: {e}")
    else:
        print("Файл Records.csv не найден, начинаем сбор рекордов с чистого листа.")

    print("Загрузка списка уровней из API...")
    try:
        resp = requests.get(API_LEVEL_LIST, timeout=10)
        api_levels = resp.json()['data']['levels']
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось загрузить уровни API: {e}")
        return

    print("Загрузка дополнительных данных из Google Таблиц...")
    hcr_players = fetch_csv_data(URL_PLAYERS_CSV)
    hcr_levels = fetch_csv_data(URL_LEVELS_CSV)
    hcr_rankings = fetch_csv_data(URL_RANKINGS_CSV)
    
    all_players = hcr_players
    seen_player_ids = {str(p.get('player_id', '')) for p in hcr_players}
    
    all_levels = hcr_levels
    rankings_data = hcr_rankings

    unique_player_map = {}
    for i, lvl in enumerate(api_levels):
        l_id = str(lvl['id'])
        req = str(lvl.get('list_percent', 100)).replace('%', '') 
        
        all_levels.append({
            'level_id': l_id, 'name': lvl['name'], 'publisher_id': '', 
            'builder': lvl.get('holder', 'Unknown'),
            'verifier_id': str(lvl['verifier']['user_id']) if lvl.get('verifier') else '',
            'video_url': lvl.get('verification_url', ''), 'thumbnail': get_thumbnail(lvl.get('verification_url')),
            'info': 'уровень из global demonlist', 'points': lvl.get('points', 0)
        })
        rankings_data.append({'ranking_id': f'PCR_{i}', 'top_name': 'PCR', 'level_id': l_id, 'position': i + 1, 'requirement': req})
        
        if lvl.get('verifier'): 
            uid = str(lvl['verifier']['user_id'])
            if uid not in seen_player_ids:
                unique_player_map[uid] = lvl['verifier']['username']

    for row in rankings_data:
        if 'requirement' in row:
            row['requirement'] = str(row['requirement']).replace('%', '')

    ids_to_process = list(unique_player_map.keys())
    total = len(ids_to_process)
    print(f"Парсинг {total} новых игроков из API (может занять время)...")
    
    processed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid]): pid for pid in ids_to_process}
        for future in concurrent.futures.as_completed(futures):
            processed_count += 1
            p_info, p_recs = future.result()
            all_players.append(p_info)
            for rec in p_recs:
                key = (str(rec['player_id']), str(rec['level_id']))
                if key not in seen_records:
                    all_records.append(rec)
                    seen_records.add(key)
            if processed_count % 10 == 0 or processed_count == total:
                print(f"[{processed_count}/{total}] Обработаны рекорды для: {p_info['nickname']}")

    print("\n--- СОХРАНЕНИЕ ФАЙЛОВ ---")
    
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_players)
        print("Players.csv сохранен.")

    with open('Levels.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['level_id', 'name', 'publisher_id', 'builder', 'verifier_id', 'video_url', 'thumbnail', 'info', 'points'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_levels)
        print("Levels.csv сохранен.")

    with open('Rankings.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['ranking_id', 'top_name', 'level_id', 'position', 'requirement'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(rankings_data)
        print("Rankings.csv сохранен.")

    print(f"ИТОГО рекордов к сохранению: {len(all_records)}")
    if len(all_records) == 0:
        print("ОШИБКА: Список рекордов пуст! Файл Records.csv создастся пустым (только заголовки).")
        
    with open('Records.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'level_id', 'progress', 'video_url'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_records)
        print("Records.csv успешно сохранен.")

    print("--- ГОТОВО! ---")

if __name__ == "__main__":
    main()
