import requests
import csv
import concurrent.futures
import time
import os
import io
import sys

# --- НАСТРОЙКИ ---
API_LEVEL_LIST = "https://api.demonlist.org/level/classic/list"
API_USER_GET = "https://api.demonlist.org/user/get?id="
BASE_API_LEADERBOARD = "https://api.demonlist.org/leaderboard/user/list"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

URL_LEVELS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=1437425318&single=true&output=csv"
URL_PLAYERS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=93759483&single=true&output=csv"

# [Функции fetch_csv_data, get_country_code, fetch_player_data оставляем как раньше]
def fetch_csv_data(url):
    try:
        r = requests.get(url, timeout=20)
        # Принудительно используем utf-8
        content = r.content.decode('utf-8-sig')
        reader = list(csv.DictReader(io.StringIO(content)))
        print(f"DEBUG: Загружено {len(reader)} строк из {url.split('gid=')[-1][:10]}...")
        if reader: print(f"DEBUG: Пример первой строки: {reader[0]}")
        return reader
    except Exception as e:
        print(f"DEBUG: ОШИБКА загрузки CSV: {e}")
        return []

def get_country_code(name):
    return {"united-states": "us", "russia": "ru", "spain": "es", "canada": "ca", "portugal": "pt", "france": "fr", "united-kingdom": "gb", "japan": "jp", "south-korea": "kr", "australia": "au", "finland": "fi", "kazakhstan": "kz", "new-zealand": "nz", "brazil": "br", "germany": "de", "hungary": "hu", "romania": "ro", "poland": "pl", "netherlands": "nl", "vietnam": "vn", "austria": "at", "belarus": "by", "sweden": "se", "norway": "no", "denmark": "dk", "italy": "it", "ukraine": "ua", "turkey": "tr", "china": "cn", "switzerland": "ch", "belgium": "be"}.get(str(name).lower().replace(" ", "-"), "world")

def fetch_player_data(p_id, nickname, custom_data):
    csv_country = custom_data.get('country', 'world')
    player_info = {'player_id': p_id, 'nickname': nickname, 'country': csv_country, 'is_banned': 'false', 'points': '0', 'photo': custom_data.get('photo', f'images/profiles/Bez{p_id}.png'), 'social_yt': '', 'social_tiwtch': '', 'info': '-', 'global_rank': custom_data.get('global_rank', '999')}
    player_info.update(custom_data)
    try:
        resp = requests.get(f"{API_USER_GET}{p_id}", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            if data.get('points'): player_info['points'] = str(int(float(data.get('points', 0))))
            if data.get('placement'): player_info['global_rank'] = str(data.get('placement'))
            if (not csv_country or csv_country == 'world') and data.get('country'):
                api_code = get_country_code(data.get('country'))
                if api_code != "world": player_info['country'] = api_code
    except: pass
    return player_info

def main():
    print("--- ЗАПУСК С ОТЛАДКОЙ УРОВНЕЙ ---")
    
    # 1. Загрузка ТВОИХ уровней
    hcr_levels = fetch_csv_data(URL_LEVELS_CSV)
    # Используем словарь для объединения
    all_levels_dict = {str(lvl.get('level_id', '')): lvl for lvl in hcr_levels if lvl.get('level_id')}
    print(f"DEBUG: Всего уровней в словаре после загрузки CSV: {len(all_levels_dict)}")

    # 2. API уровни (ДОПОЛНЯЕМ, а не перезаписываем)
    try:
        api_levels = requests.get(API_LEVEL_LIST, headers=HEADERS).json()['data']['levels']
        for lvl in api_levels:
            l_id = str(lvl['id'])
            if l_id not in all_levels_dict:
                all_levels_dict[l_id] = {'level_id': l_id, 'name': lvl['name'], 'publisher_id': '', 'builder': lvl.get('holder', 'Unknown'), 'verifier_id': str(lvl['verifier']['user_id']) if lvl.get('verifier') else '', 'video_url': lvl.get('verification_url', ''), 'thumbnail': '', 'info': 'уровень из global demonlist', 'points': lvl.get('points', 0)}
    except Exception as e: print(f"DEBUG: Ошибка API уровней: {e}")

    # 3. Сохранение
    print(f"DEBUG: Сохраняем {len(all_levels_dict)} уровней в файл.")
    with open('Levels.csv', 'w', newline='', encoding='utf-8-sig') as f:
        # Принудительно задаем поля, чтобы точно попали в файл
        writer = csv.DictWriter(f, fieldnames=['level_id', 'name', 'publisher_id', 'builder', 'verifier_id', 'video_url', 'thumbnail', 'info', 'points'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_levels_dict.values())
        
    print("--- УСПЕШНО ---")

if __name__ == "__main__":
    main()
