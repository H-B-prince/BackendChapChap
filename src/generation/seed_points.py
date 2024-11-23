import json
import geopandas as gpd
from shapely.geometry import Point
import numpy as np


def load_polygon(geojson_path):
    gdf = gpd.read_file(geojson_path)
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    return gdf


def generate_uniform_points(gdf, num_points, distance_m=67.5):
    gdf_proj = gdf.to_crs(epsg=32633)
    polygon = gdf_proj.union_all()
    minx, miny, maxx, maxy = polygon.bounds
    x_coords = np.arange(minx, maxx, distance_m)
    y_coords = np.arange(miny, maxy, distance_m)
    points = []
    for x in x_coords:
        for y in y_coords:
            point = Point(x, y)
            if polygon.contains(point):
                points.append(point)
                if len(points) >= num_points:
                    break
        if len(points) >= num_points:
            break
    if len(points) < num_points:
        raise ValueError(f"Не удалось сгенерировать требуемое количество точек. Сгенерировано: {len(points)}")
    gdf_points = gpd.GeoDataFrame(geometry=points, crs=gdf_proj.crs)
    gdf_points = gdf_points.to_crs(epsg=4326)
    return gdf_points['geometry']


def save_points_to_file(gdf_points, file_path='points.json'):
    points = [{'node_id': idx + 1, 'latitude': point.y, 'longitude': point.x} for idx, point in enumerate(gdf_points)]

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(points, f, ensure_ascii=False, indent=4)
    print(f"Точки успешно сохранены в файл: {file_path}")


def main():
    geojson_path = '..//..//map.geojson'
    num_points = 265
    distance_m = 135
    print("Загрузка полигона...")
    gdf = load_polygon(geojson_path)
    print("Генерация точек...")
    try:
        gdf_points = generate_uniform_points(gdf, num_points, distance_m)
        print(f"Сгенерировано {len(gdf_points)} точек.")
        print("Сохранение точек в файл...")
        save_points_to_file(gdf_points)
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
