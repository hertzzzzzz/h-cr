import requests
import csv

# 1. Запрашиваем общий список уровней (предполагается, что response уже получен)
url_list = "https://api.demonlist.org/level/classic/list"
response = requests.get(url_list)

if response.status_code == 200:
    levels_data = response.json()['data']['levels']

    # ==========================================
    # 3. ГЕНЕРАЦИЯ ТАБЛИЦЫ PLAYERS (Игроки)
    # ==========================================
    players_filename = 'Players.csv'
    players_headers = ['player_id', 'nickname', 'country', 'is_banned', 'points', 'photo', 'social_yt', 'social_tiwtch', 'info']
    
    # Используем словарь для фильтрации дубликатов (один ID = один профиль)
    unique_players = {}
    
    for level in levels_data:
        verifier = level.get('verifier')
        if verifier:
            p_id = verifier.get('user_id')
            # Если такого игрока еще нет в словаре, добавляем его
            if p_id not in unique_players:
                unique_players[p_id] = {
                    'player_id': p_id,
                    'nickname': verifier.get('username', ''),
                    'country': 'Unknown', # Сюда можно будет дописывать данные из второго API
                    'is_banned': 'FALSE',
                    'points': '0.0', 
                    # Берем твою дефолтную ссылку на фото из таблицы
                    'photo': 'https://i.postimg.cc/wB24cRD6/Bez-nazvania170-20260713223113.png', 
                    'social_yt': '',
                    'social_tiwtch': '',
                    'info': '- пока тут нет никакой информации, известно только то, что мальчик топ 1 гей -'
                }
                
    with open(players_filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=players_headers)
        writer.writeheader()
        # Записываем всех собранных уникальных игроков
        for player_data in unique_players.values():
            writer.writerow(player_data)


    # ==========================================
    # 4. ГЕНЕРАЦИЯ ТАБЛИЦЫ RECORDS (Рекорды)
    # ==========================================
    records_filename = 'Records.csv'
    records_headers = ['player_id', 'level_id', 'progress', 'video_url']
    
    with open(records_filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=records_headers)
        writer.writeheader()
        
        # Проходимся по уровням и записываем верификации как 100% рекорды
        for level in levels_data:
            verifier = level.get('verifier')
            if verifier:
                writer.writerow({
                    'player_id': verifier.get('user_id', ''),
                    'level_id': level.get('id', ''),
                    'progress': 100,
                    'video_url': level.get('video', '')
                })


    # ==========================================
    # 5. ГЕНЕРАЦИЯ ТАБЛИЦЫ STREAMS (Стримы)
    # ==========================================
    streams_filename = 'Streams.csv'
    streams_headers = ['stream_id', 'is_live', 'player_id', 'level_id', 'progress', 'link']
    
    with open(streams_filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=streams_headers)
        writer.writeheader()
        
        # Так как стримы — это данные в реальном времени, запишем одну строчку для примера, 
        # чтобы структура файла не была пустой и сайт смог её прочитать.
        writer.writerow({
            'stream_id': 1,
            'is_live': 'LIVE',
            'player_id': 10034,
            'level_id': 127323087,
            'progress': 62,
            'link': 'https://www.youtube.com/watch?v=r2dosVRzLSM'
        })

    print("Все таблицы (Players, Records, Streams) успешно сгенерированы!")
else:
    print(f"Ошибка API: {response.status_code}")
