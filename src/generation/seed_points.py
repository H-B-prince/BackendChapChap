import json
import geojson
import numpy as np
from shapely.geometry import shape

# Загрузка GeoJSON данных
with open('../../map.geojson') as f:
    data = geojson.load(f)


def generate_hex_grid(polygon, spacing):
    """
    Генерация шестиугольной сетки внутри заданного полигона.

    :param polygon: `shapely.geometry.Polygon`, описывающий границы области.
    :param spacing: Расстояние между точками в градусах широты, грубо.
    :return: Список точек {"node_id", "latitude", "longitude"}.
    """
    from shapely.geometry import Point

    minx, miny, maxx, maxy = polygon.bounds
    dx = spacing * 3 / 2  # Горизонтальное смещение
    dy = spacing * np.sqrt(3)  # Вертикальное смещение
    points = []  # Список точек
    node_id = 1  # Уникальный идентификатор узла
    y = miny  # Начальная координата Y
    offset = 0  # Сдвиг для четных/нечетных строк

    while y <= maxy:
        x = minx + dx * offset  # Смещаем стартовую X-координату для строк через одну
        while x <= maxx:
            point = Point(x, y)
            if polygon.contains(point):
                points.append({
                    "node_id": node_id,
                    "latitude": point.y,
                    "longitude": point.x
                })
                node_id += 1
            x += dx  # Переход к следующей точке по горизонтали
        y += dy / 2  # Смещение на следующую строку
        offset = 1 - offset  # Чередуем сдвиг (0 -> 1 -> 0)

    return points


# Извлечение полигона из данных
polygon_data = data['features'][1]['geometry']
polygon = shape(polygon_data)

# Генерация точек с расстоянием 135 м
spacing = 135 / 111320  # Преобразование метров в градусы широты (грубо)

# Создание точек в шестиугольной сетке
points = generate_hex_grid(polygon, spacing)

# Сохранение точек в JSON файл с красивым форматированием
with open('points.json', 'w') as f:
    json.dump(points, f, indent=4)

print(f"Создано {len(points)} точек")
