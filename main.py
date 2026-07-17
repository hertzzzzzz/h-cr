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
API_LEADERBOARD = "https://api.demonlist.org/user/ranking?limit=200" # Увеличил лимит до 200, чтобы собрать больше топов!

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
    print(f"ВНИМАНИЕ: Ошибка загрузки CSV из Google Таблиц после 3 попыток.")
    return []

def fetch_player_data(p_id, fallback_name, custom_data):
    time.sleep(0.5)
    
    player_info = {
        'player_id': p_id, 
        'nickname': custom_data.get('nickname') or fallback_name, 
        'country': custom_data.get('country') or 'world',
        'is_banned': custom_data.get('is_banned') or 'false', 
        'points': '0.0', 
        'photo': custom_data.get('photo') or f'images/profiles/Bez{p_id}.png',
        'social_yt': custom_data.get('social_yt') or '', 
        'social_tiwtch': custom_data.get('social_tiwtch') or '', 
        'info': custom_data.get('info') or '- информация ещё не была добавлена -',
        'global_rank': custom_data.get('global_rank') or '0' # <- ДОБАВИЛИ ГЛОБАЛЬНЫЙ РАНК
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
                    
                    # Берем официальное место из API
                    player_info['global_rank'] = str(u_data.get('placement', '0'))
                    
                    api_country = get_country_code(u_data.get('country'))
                    if api_country != "world":
                        player_info['country'] = api_country

                    levels_data = u_data.get('levels', {})
                    if isinstance(levels_data, dict):
                        for cat in ['hardest', 'main', 'extended', 'verified']:
                            cat_data = levels_data.get(cat)
                            if not cat_data:
                                continue
                            if isinstance(cat_data, dict):
                                cat_data = [cat_data]
                            if isinstance(cat_data, list):
                                for lvl in cat_data:
                                    if isinstance(lvl, dict):
                                        l_id = lvl.get('id')
                                        if l_id: 
                                            player_records.append({'player_id': p_id, 'level_id': l_id, 'progress': 100, 'video_url': lvl.get('video_url', '')})
    except Exception as e:
        print(f"Ошибка парсинга игрока {p_id}: {e}")
        
    return player_info, player_records

def main():
    print("--- ЗАПУСК ОБНОВЛЕНИЯ ДАННЫХ ---")
    
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
        except Exception as e:
            pass

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
    
    all_levels = hcr_levels
    rankings_data = hcr_rankings
    
    unique_player_map = {}
    player_custom_data = {}

    for p in hcr_players:
        pid = str(p.get('player_id', ''))
        if pid:
            unique_player_map[pid] = p.get('nickname', 'Unknown')
            player_custom_data[pid] = p 

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
            unique_player_map[uid] = lvl['verifier']['username']

    try:
        lb_resp = requests.get(API_LEADERBOARD, timeout=10)
        if lb_resp.status_code == 200:
            lb_data = lb_resp.json()
            if isinstance(lb_data, dict) and 'data' in lb_data:
                for top_p in lb_data['data']:
                    pid = str(top_p.get('id', top_p.get('user_id', '')))
                    if pid:
                        unique_player_map[pid] = top_p.get('name', 'Unknown')
    except Exception as e:
        print("API Топ-100/200 недоступно.")

    # === ДИАГНОСТИКА СБОРА ===
    print("\n--- ДИАГНОСТИКА СБОРА ID ---")
    print(f"Игроков из Google Таблицы: {len(hcr_players)}")
    print(f"Всего уникальных ID для парсинга: {len(unique_player_map)}")
    print("----------------------------\n")

    for row in rankings_data:
        if 'requirement' in row:
            row['requirement'] = str(row['requirement']).replace('%', '')

    ids_to_process = list(unique_player_map.keys())
    total = len(ids_to_process)
    
    final_players = []
    processed_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_player_data, pid, unique_player_map[pid], player_custom_data.get(pid, {})): pid for pid in ids_to_process}
        
        for future in concurrent.futures.as_completed(futures):
            processed_count += 1
            p_info, p_recs = future.result()
            final_players.append(p_info)
            for rec in p_recs:
                key = (str(rec['player_id']), str(rec['level_id']))
                if key not in seen_records:
                    all_records.append(rec)
                    seen_records.add(key)
            if processed_count % 10 == 0 or processed_count == total:
                print(f"[{processed_count}/{total}] Обработаны данные для: {p_info['nickname']}")

    print(f"ИТОГО рекордов к сохранению: {len(all_records)}")
    if len(all_records) == 0:
        print("КРИТИЧЕСКАЯ ОШИБКА: Список рекордов пуст! Запись отменена.")
        sys.exit(1)

    print("\n--- СОХРАНЕНИЕ ФАЙЛОВ ---")
    
    # Добавили global_rank в сохранение CSV
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info', 'global_rank'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(final_players)
        
    with open('Levels.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['level_id', 'name', 'publisher_id', 'builder', 'verifier_id', 'video_url', 'thumbnail', 'info', 'points'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_levels)
        
    with open('Rankings.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['ranking_id', 'top_name', 'level_id', 'position', 'requirement'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(rankings_data)
        
    with open('Records.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'level_id', 'progress', 'video_url'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(all_records)

    print("--- ГОТОВО! ---")

if __name__ == "__main__":
    main()
