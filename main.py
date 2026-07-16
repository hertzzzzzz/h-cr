import requests
import csv
import time
import json

API_LEVEL_LIST = "https://api.demonlist.org/level/classic/list"
API_USER_GET = "https://api.demonlist.org/user/get?id="

def fetch_all_data():
    print("Запрос списка уровней...")
    try:
        resp = requests.get(API_LEVEL_LIST, timeout=15)
        levels = resp.json()['data']['levels']
    except Exception as e:
        print(f"Ошибка API уровней: {e}")
        return [], []

    all_records = []
    all_players = []
    
    # Собираем всех уникальных игроков из верификаторов
    unique_player_ids = set()
    for lvl in levels:
        if lvl.get('verifier'):
            unique_player_ids.add(str(lvl['verifier']['user_id']))

    print(f"Найдено {len(unique_player_ids)} уникальных верификаторов. Начинаю сбор рекордов...")

    for p_id in unique_player_ids:
        time.sleep(0.5) # Пауза для API
        try:
            r = requests.get(f"{API_USER_GET}{p_id}", timeout=10)
            if r.status_code == 200:
                data = r.json().get('data', {})
                name = data.get('name', 'Unknown')
                
                # Добавляем игрока
                all_players.append({
                    'player_id': p_id, 
                    'nickname': name, 
                    'country': 'world',
                    'is_banned': 'false', 
                    'points': data.get('points', 0), 
                    'photo': f'images/profiles/Bez{p_id}.png'
                })

                # Собираем все рекорды (из категорий)
                levels_data = data.get('levels', {})
                for cat in ['hardest', 'main', 'extended', 'verified']:
                    for lvl in levels_data.get(cat, []):
                        all_records.append({
                            'player_id': p_id,
                            'level_id': lvl.get('id'),
                            'progress': 100,
                            'video_url': lvl.get('video_url', '')
                        })
                print(f"Обработан игрок: {name} (всего рекордов: {len(all_records)})")
        except Exception as e:
            print(f"Ошибка с игроком {p_id}: {e}")

    return all_players, all_records

def main():
    players, records = fetch_all_data()

    if not records:
        print("!!! ВНИМАНИЕ: Список рекордов пуст! Данные не собрались.")
    else:
        print(f"Успешно собрано {len(records)} рекордов. Сохраняю...")

    # Сохранение Records.csv
    with open('Records.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'level_id', 'progress', 'video_url'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)

    # Сохранение Players.csv
    with open('Players.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(players)
    
    print("Готово!")

if __name__ == "__main__":
    main()
