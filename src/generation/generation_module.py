import pandas as pd
import numpy as np
import random
import json


# Генерация точек с расстоянием 135 м
spacing = 135 / 111320  # Преобразование метров в градусы широты (грубо)


SEASONS = {
    'winter': {'start': (12, 1), 'end': (2, 28), 'temp_range': (-10, 5)},
    'spring': {'start': (3, 1), 'end': (5, 31), 'temp_range': (5, 20)},
    'summer': {'start': (6, 1), 'end': (8, 31), 'temp_range': (15, 35)},
    'autumn': {'start': (9, 1), 'end': (11, 30), 'temp_range': (5, 20)}
}


def read_nodes():
    with open('D:/Python/ChapChap/src/generation/points.json') as f:
        return json.load(f)


def generate_base_temperature(season):
    return np.random.uniform(SEASONS[season]['temp_range'][0], SEASONS[season]['temp_range'][1])


def generate_data_for_node(season, fire=False, fire_intensity=0):
    base_temp = generate_base_temperature(season)
    base_humidity = np.random.uniform(40, 80)
    base_oxygen = np.random.uniform(19.0, 21.0)
    base_CO2 = np.random.uniform(300, 400)

    if fire:
        temp = base_temp + fire_intensity * np.random.uniform(30, 50)
        humidity = base_humidity * (1 - fire_intensity * 0.5)
        oxygen = base_oxygen - fire_intensity * 2.0
        CO2 = base_CO2 + fire_intensity * 200
    else:
        temp = base_temp + np.random.uniform(-2, 2)
        humidity = base_humidity + np.random.uniform(-5, 5)
        oxygen = base_oxygen + np.random.uniform(-0.2, 0.2)
        CO2 = base_CO2 + np.random.uniform(-20, 20)

    return {
        "temperature": round(temp, 2),
        "humidity": round(max(min(humidity, 100), 0), 2),
        "oxygen": round(max(min(oxygen, 21), 10), 2),
        "CO2": round(max(CO2, 0), 2),
    }


def get_season(month, day):
    # Определить сезон по месяцу и дню (пример)
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "fall"


def find_neighbors(points, target_node):
    neighbors = []
    target_lat = target_node['latitude']
    target_lon = target_node['longitude']

    # Предполагаемые соседние точки (смещения для шестиугольной сетки)
    dx = spacing * 3 / 2
    dy = spacing * np.sqrt(3) / 2

    potential_neighbors = [
        (target_lon + dx, target_lat),  # Правый
        (target_lon - dx, target_lat),  # Левый
        (target_lon + dx / 2, target_lat + dy),  # Верхний правый
        (target_lon - dx / 2, target_lat + dy),  # Верхний левый
        (target_lon + dx / 2, target_lat - dy),  # Нижний правый
        (target_lon - dx / 2, target_lat - dy),  # Нижний левый
    ]
    # Проходим по соседним позициям и сравниваем с точками
    for neighbor in potential_neighbors:
        for point in points:
            # Проверяем, близка ли точка по широте и долготе и не является ли она самой собой
            if np.isclose(point['longitude'], neighbor[0], atol=spacing / 2) and np.isclose(point['latitude'], neighbor[1], atol=spacing / 2) and (point['longitude'] != target_lon and point['latitude'] != target_lat):
                neighbors.append(point)
                break
    return neighbors


async def generate_realtime_data():

    fire_details = {}

    current_datetime = pd.Timestamp.now()

    nodes = read_nodes()
    nodes_df = pd.DataFrame(nodes)

    while True:
        season = get_season(current_datetime.month, current_datetime.day)

        # Если fire_details пуст, создаём новый пожар
        if not fire_details:
            random_node = random.choice(nodes_df.to_dict('records'))
            random_start_time = current_datetime + pd.Timedelta(minutes=0)
            random_duration = 60  # Длительность в секундах
            fire_details = {"start_time": random_start_time, "duration": random_duration,
                            "start_node": random_node["node_id"]}
            fire_intensity = 1
            fire_start_times = pd.to_datetime([fire_details["start_time"]])
            fire_durations = [fire_details["duration"]]
            fire_start_nodes = [int(fire_details["start_node"])]
            fire_end_times = {node: (fire_start_times[i] + pd.Timedelta(seconds=fire_durations[i])) for i, node in
                              enumerate(fire_start_nodes)}
            fire_active_nodes = set()

            # Изначально добавляем узлы, где пожар должен начаться в текущее время
            for i, start_time in enumerate(fire_start_times):
                if current_datetime >= start_time:
                    fire_active_nodes.add(fire_start_nodes[i])
                    fire_end_times[fire_start_nodes[i]] = fire_start_times[i] + pd.Timedelta(seconds=fire_durations[i])

        # Проверяем завершение пожара
        for node_id, end_time in list(fire_end_times.items()):
            current_datetime = pd.Timestamp.now()
            if current_datetime >= end_time:
                fire_active_nodes.discard(node_id)
                del fire_end_times[node_id]

        # Очищаем fire_details и fire_active_nodes, если пожар завершился
        if not fire_end_times:
            fire_details = {}
            fire_active_nodes = set()

        # Обновляем узлы с активным пожаром и добавляем их соседей
        new_active_nodes = set()
        for node_id in list(fire_active_nodes):  # Используем list(fire_active_nodes) для итерации по копии множества
            if current_datetime < fire_end_times.get(node_id, current_datetime):
                node = nodes_df[nodes_df["node_id"] == node_id].iloc[0]
                neighbors = find_neighbors(nodes_df.to_dict('records'), node)

                # Берём 75% случайных соседей
                num_neighbors_to_select = int(len(neighbors) * 0.75)  # 75% от общего количества соседей
                random_neighbors = random.sample(neighbors, num_neighbors_to_select)

                for neighbor in random_neighbors:  # Итерация только по случайным соседям
                    neighbor_id = neighbor['node_id']
                    if neighbor_id not in fire_active_nodes and neighbor_id not in new_active_nodes:
                        new_active_nodes.add(neighbor_id)
                        fire_end_times[neighbor_id] = fire_end_times[node_id] + pd.Timedelta(
                            seconds=2)  # Указываем тайминг

        fire_active_nodes.update(new_active_nodes)
        fire_active_nodes = {node for node in fire_active_nodes if
                             current_datetime < fire_end_times.get(node, current_datetime)}

        data = []

        for _, node in nodes_df.iterrows():
            node_id = int(node["node_id"])
            fire = node_id in fire_active_nodes
            sensor_data = generate_data_for_node(season, fire, fire_intensity)
            sensor_data["node_id"] = node_id
            sensor_data["timestamp"] = current_datetime
            sensor_data["node_y"] = node["latitude"]
            sensor_data["node_x"] = node["longitude"]
            sensor_data["fire"] = 1 if fire else 0

            data.append(sensor_data)

        df = pd.DataFrame(data)
        yield df
        current_datetime += pd.Timedelta(seconds=1)








