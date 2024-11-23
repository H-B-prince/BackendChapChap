import json
import pandas as pd
import numpy as np
import datetime
import random

# Определение сезонов и соответствующих температурных диапазонов
SEASONS = {
    'winter': {'start': (12, 1), 'end': (2, 28), 'temp_range': (-10, 5)},  # Температура в градусах Цельсия
    'spring': {'start': (3, 1), 'end': (5, 31), 'temp_range': (5, 20)},
    'summer': {'start': (6, 1), 'end': (8, 31), 'temp_range': (15, 35)},
    'autumn': {'start': (9, 1), 'end': (11, 30), 'temp_range': (5, 20)}
}

# Параметры температур при пожаре
FIRE_TEMP_MIN = 300  # Минимальная температура пожара в °C
FIRE_TEMP_MAX = 1000  # Максимальная температура пожара в °C


def get_season(month, day):
    for season, data in SEASONS.items():
        start_month, start_day = data['start']
        end_month, end_day = data['end']
        # Используем произвольный год для сравнения
        start = datetime.date(2000, start_month, start_day)
        end = datetime.date(2000, end_month, end_day)
        current = datetime.date(2000, month, day)
        if start <= current <= end:
            return season
    return 'winter'  # По умолчанию зима


def generate_base_temperature(season):
    return np.random.uniform(SEASONS[season]['temp_range'][0],
                             SEASONS[season]['temp_range'][1])


def generate_data_for_node(season, fire=False, fire_intensity=0):
    base_temp = generate_base_temperature(season)
    base_humidity = np.random.uniform(40, 80)  # Влажность в %
    base_oxygen = np.random.uniform(19.0, 21.0)  # Кислород в %
    base_CO2 = np.random.uniform(300, 400)  # CO2 в ppm

    # Если пожар, изменяем показатели
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


def read_nodes():
    with open('..//points.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

        return data


def generate_dataset(start_date="2024-01-01 00:00:00", end_date="2024-01-01 06:00:00", fire_details=None):
    nodes = read_nodes()

    nodes_df = pd.DataFrame(nodes)
    # Конвертируем сроки
    start_datetime = pd.to_datetime(start_date)
    print("Начало:", start_datetime)

    end_datetime = pd.to_datetime(end_date)
    print("Конец:", end_datetime)

    timestamps = pd.date_range(start=start_datetime, end=end_datetime, freq="s")

    # Подготовка хранения результатов
    data = {
        "timestamp": [],
        "node_id": [],
        "latitude": [],
        "longitude": [],
        "temperature": [],
        "humidity": [],
        "oxygen": [],
        "CO2": [],
        "fire": [],
    }

    # Настройки пожара
    fire_start = pd.to_datetime(fire_details["start_time"])  # Временное начало пожара
    fire_duration = fire_details["duration"] * 60  # Длительность пожара (в секундах)
    fire_start_node = fire_details["start_node"]  # Узел начала пожара

    fire_active_nodes = set([fire_start_node])  # Узлы, где происходит пожар
    time_elapsed = 0  # Прошедшее время с начала пожара

    # Запуск симуляции
    for ts in timestamps:
        print(ts)
        season = get_season(ts.month, ts.day)

        for _, node in nodes_df.iterrows():
            fire = False
            fire_intensity = 0

            # Определяем, есть ли пожар в этом узле
            if ts >= fire_start and node["node_id"] in fire_active_nodes:
                fire = True
                fire_intensity = 1 - (time_elapsed / fire_duration)
                fire_intensity = max(fire_intensity, 0)  # Интенсивность пожара не может быть < 0

            # Генерация данных для каждого узла
            sensor_data = generate_data_for_node(season, fire, fire_intensity)
            data["timestamp"].append(ts)
            data["node_id"].append(node["node_id"])
            data["latitude"].append(node["latitude"])
            data["longitude"].append(node["longitude"])
            data["temperature"].append(sensor_data["temperature"])
            data["humidity"].append(sensor_data["humidity"])
            data["oxygen"].append(sensor_data["oxygen"])
            data["CO2"].append(sensor_data["CO2"])
            data["fire"].append(1 if fire else 0)

            # Увеличиваем набор охваченных пожаром узлов каждые 30 секунд
            if fire and time_elapsed % 30 == 0:
                for _, neighbor in nodes_df.iterrows():
                    if (
                            abs(neighbor["latitude"] - node["latitude"]) <= 0.001
                            and abs(neighbor["longitude"] - node["longitude"]) <= 0.001
                    ):
                        fire_active_nodes.add(neighbor["node_id"])

        # Увеличиваем время пожара
        if ts >= fire_start:
            time_elapsed += 1
            # Завершаем пожар, если время вышло
            if time_elapsed > fire_duration:
                fire_active_nodes.clear()

    # Возвращаем результирующий DataFrame
    return pd.DataFrame(data)

# Пример вызова
fire_details = {
    "start_time": "2024-11-23 10:01:00",  # Начало пожара
    "duration": 5,  # Длительность в минутах
    "start_node": 125,  # Узел, с которого начнется пожар
}


def main():
    output_file = 'fire_dataset.csv'

    result = generate_dataset(start_date="2024-11-23 10:00:00", end_date="2024-11-23 10:07:00", fire_details=fire_details)

    # Сохранение данных в CSV
    result.to_csv(output_file, index=False, encoding="utf-8")

if __name__ == "__main__":
    main()
