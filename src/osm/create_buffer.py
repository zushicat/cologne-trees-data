import json
import os
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import LineString, Point, Polygon
from slugify import slugify


OSM_DATA_DIR_IN = "../../data/geo_data/osm"
OSM_DATA_DIR_OUT = "../../data/geo_data/osm_buffer"


def _get_polygon_from_line(area_geometry: List[List[float]]) -> List[List[float]]:
    line_string_area = LineString(area_geometry)
    polygon_area = Polygon(line_string_area.buffer(0.00016, cap_style=2, join_style=2))  # big buffer: approx. 8m each side

    return polygon_area


def process_features(osm_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buffer_feature: List[Dict[str, Any]] = []
    for osm_feature in osm_features:
        osm_geometry = osm_feature["geometry"]
        
        try:
            if osm_geometry["type"] == "LineString":
                osm_geometry["type"] = "Polygon"
                polygon = _get_polygon_from_line(osm_geometry["coordinates"])
            elif osm_geometry["type"] == "Polygon":
                polygon = Polygon(osm_geometry["coordinates"][0]).buffer(0.00002)  # a litte buffer: approx. 1m each side
            else:
                continue

            # bounding box of new polygon (following former lat, lng converntion)
            bbox = list(polygon.bounds)
            osm_feature["properties"]["bounding_box"] = [
                bbox[1], bbox[0], bbox[3], bbox[2]
            ]

            osm_geometry["coordinates"] = [[list(pair) for pair in list(polygon.exterior.coords)]]

            buffer_feature.append(osm_feature)
        except Exception as e:
            print(e)  # debug
            continue  # rarely happens (i.e. 1x in neustadt sued suburb) -> ignore

    return buffer_feature


if __name__ == "__main__":
    for dir_name in ["green_spaces_agriculture", "green_spaces_leisure", "highway"]:
        # if dir_name != "highway":  # debug
        #     continue

        file_names = os.listdir(f"{OSM_DATA_DIR_IN}/{dir_name}")
        for file_name in file_names:
            # if file_name != "innenstadt_neustadtsud.json":  # debug
            #     continue

            try:
                with open(f"{OSM_DATA_DIR_IN}/{dir_name}/{file_name}") as f:
                    osm_in = json.load(f)
            except:
                continue

            osm_in["features"] = process_features(osm_in["features"])
            
            with open(f"{OSM_DATA_DIR_OUT}/{dir_name}/{file_name}", "w") as f:
                f.write(json.dumps(osm_in, ensure_ascii=False, indent=2))
