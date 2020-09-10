import json
import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from shapely.geometry import LineString, Point, Polygon
from slugify import slugify


OSM_DATA_DIR = "../data/geo_data/osm"
SUBURBS_GEOJSON: Dict[str, Any] = {}


def get_suburb_data() -> None:
    global SUBURBS_GEOJSON

    for dir_name in ["green_spaces_leisure", "green_spaces_agriculture", "highway"]:
        file_names = os.listdir(f"{OSM_DATA_DIR}/{dir_name}")
        for file_name in file_names:
            district_suburb_name = file_name.split(".")[0]
            
            try:
                with open(f"{OSM_DATA_DIR}/{dir_name}/{file_name}") as f:
                    suburb_data = json.load(f)
            except:
               continue

            if SUBURBS_GEOJSON.get(district_suburb_name) is None:
                SUBURBS_GEOJSON[district_suburb_name]: Dict[str, Any] = {}

            if SUBURBS_GEOJSON[district_suburb_name].get(dir_name) is None:
                SUBURBS_GEOJSON[district_suburb_name][dir_name]: Dict[str, Any] = {}
            SUBURBS_GEOJSON[district_suburb_name][dir_name] = suburb_data


def get_tree_location_types(tree_data_list: List[Dict[str, Any]]) ->  List[Dict[str, Any]]:
    new_tree_data_list: List[Dict[str, Any]] = []
    
    for tree_data in tree_data_list:
        tree_district_slug = slugify(tree_data["geo_info"]["district"], replace_latin=True)
        tree_suburb_slug = slugify(tree_data["geo_info"]["suburb"], replace_latin=True)
        tree_district_suburb = f"{tree_district_slug}_{tree_suburb_slug}"

        tree_lat = tree_data["geo_info"]["lat"]
        tree_lng = tree_data["geo_info"]["lng"]

        # define new attribute
        tree_data["tree_location_type"]: Optional[Dict[str, Any]] = None

        if SUBURBS_GEOJSON.get(tree_district_suburb) is None:
            continue

        tree_point = Point(tree_lng, tree_lat)
        
        for location_category in SUBURBS_GEOJSON[tree_district_suburb]:
            area_intersection = _check_suburb_polygons(SUBURBS_GEOJSON[tree_district_suburb][location_category], tree_point, location_category)
            
            if area_intersection is not None:
                if tree_data["tree_location_type"] is None:
                    tree_data["tree_location_type"] = {}
                if tree_data["tree_location_type"].get(location_category) is None:
                    tree_data["tree_location_type"][location_category] = {}
                tree_data["tree_location_type"][location_category] = area_intersection
            
        new_tree_data_list.append(tree_data)

    return new_tree_data_list


# **************************
#
# **************************
def _get_area_bounding_box(area_bbox_points: List[float]) -> Polygon:
    area_bbox_polygon = [
        [area_bbox_points[1], area_bbox_points[0]],
        [area_bbox_points[1], area_bbox_points[2]],
        [area_bbox_points[3], area_bbox_points[2]],
        [area_bbox_points[3], area_bbox_points[0]],
        [area_bbox_points[1], area_bbox_points[0]]
    ]

    return Polygon(area_bbox_polygon)


def _get_polygon_from_line(area_geometry: List[List[float]]) -> List[List[float]]:
    line_string_area = LineString(area_geometry)
    polygon_area = Polygon(line_string_area.buffer(0.0001, cap_style=2, join_style=2))  # 0.00005

    return polygon_area


def _check_suburb_polygons(suburb_data: Dict[str, Any], tree_point: Point, location_category: str) -> Optional[Dict[str, Any]]:
    for osm_element in suburb_data["features"]:
        area_bbox_polygon = _get_area_bounding_box(osm_element["properties"]["bounding_box"])
        area_geometry_type = osm_element["geometry"]["type"]
        area_geometry = osm_element["geometry"]["coordinates"]
        area_properties = osm_element["properties"]

        # skip if not in broad bounding box of feature
        if tree_point.within(area_bbox_polygon) is False:
            continue

        if area_geometry_type == "LineString":
            area_geometry = _get_polygon_from_line(area_geometry)  # create with buffer: 5 meter
        else:
            area_geometry = Polygon(area_geometry[0]).buffer(0.00005)

        if tree_point.within(area_geometry) is True:  # stop at first fiunding
            return {
                "category": location_category,
                "type": area_properties["type"],
                "name": area_properties["name"],
                "osm_id": area_properties["osm_id"],
                "wikidata_id": area_properties["wikidata_id"],
            }

    return None
        



if __name__ == "__main__":
    suburbs_geojson = get_suburb_data()

    tree_data_list: List[Dict[str, Any]] = [
        {"tree_id": "d4d45c79-764c-4a17-8354-108ef8e96cda", "dataset_completeness": 0.82, "base_info_completeness": 0.67, "tree_taxonomy_completeness": 0.6, "tree_measures_completeness": 1.0, "tree_age_completeness": 1.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": "U35", "year_planting": None}, "geo_info": {"utm_x": 358004, "utm_y": 5640698, "lat": 50.90045959721349, "lng": 6.98062069598047, "suburb": "Marienburg", "suburb_id": "202", "district": "Rodenkirchen", "district_id": "2"}, "tree_taxonomy": {"genus": "Acer", "genus_name_german": "Ahorne", "species": None, "type": None, "name_german": ["Ahorn"]}, "tree_measures": {"height": 9, "treetop_radius": 5, "bole_radius": 35}, "tree_age": {"year_sprout": 1979, "age_in_2020": 41, "age_group_2020": 2}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "7a0d5f91-f058-4018-8645-6e73beb8f3b7", "dataset_completeness": 0.82, "base_info_completeness": 0.67, "tree_taxonomy_completeness": 0.6, "tree_measures_completeness": 1.0, "tree_age_completeness": 1.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": "U28", "year_planting": None}, "geo_info": {"utm_x": 357993, "utm_y": 5640745, "lat": 50.90087928398475, "lng": 6.980446085435723, "suburb": "Marienburg", "suburb_id": "202", "district": "Rodenkirchen", "district_id": "2"}, "tree_taxonomy": {"genus": "Acer", "genus_name_german": "Ahorne", "species": None, "type": None, "name_german": ["Ahorn"]}, "tree_measures": {"height": 10, "treetop_radius": 6, "bole_radius": 40}, "tree_age": {"year_sprout": 1976, "age_in_2020": 44, "age_group_2020": 2}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "67cf9944-29b5-4f4f-976d-88d4f2138bfa", "dataset_completeness": 0.9, "base_info_completeness": 1.0, "tree_taxonomy_completeness": 0.6, "tree_measures_completeness": 1.0, "tree_age_completeness": 1.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": "U18", "year_planting": 1992}, "geo_info": {"utm_x": 358026, "utm_y": 5640817, "lat": 50.9015344675876, "lng": 6.980887087450673, "suburb": "Marienburg", "suburb_id": "202", "district": "Rodenkirchen", "district_id": "2"}, "tree_taxonomy": {"genus": "Pterocarya", "genus_name_german": "Flügelnüsse", "species": None, "type": None, "name_german": ["Flügelnuß"]}, "tree_measures": {"height": 9, "treetop_radius": 6, "bole_radius": 35}, "tree_age": {"year_sprout": 1982, "age_in_2020": 38, "age_group_2020": 1}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "19a896e9-22f2-4793-b821-bf3af86b552b", "dataset_completeness": 0.82, "base_info_completeness": 0.67, "tree_taxonomy_completeness": 0.6, "tree_measures_completeness": 1.0, "tree_age_completeness": 1.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": "U20", "year_planting": None}, "geo_info": {"utm_x": 358015, "utm_y": 5640802, "lat": 50.90139695679718, "lng": 6.980736585568239, "suburb": "Marienburg", "suburb_id": "202", "district": "Rodenkirchen", "district_id": "2"}, "tree_taxonomy": {"genus": "Acer", "genus_name_german": "Ahorne", "species": None, "type": None, "name_german": ["Ahorn"]}, "tree_measures": {"height": 7, "treetop_radius": 3, "bole_radius": 20}, "tree_age": {"year_sprout": 1989, "age_in_2020": 31, "age_group_2020": 1}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "65309a81-38dc-42fc-b062-e22b5f055707", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360944, "utm_y": 5647327, "lat": 50.960751517463166, "lng": 7.019875723522549, "suburb": "Buchheim", "suburb_id": "903", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "082dad73-96d0-4108-9b4e-e395c6efefbd", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360950, "utm_y": 5647329, "lat": 50.960770939842206, "lng": 7.019960343293718, "suburb": "Buchheim", "suburb_id": "903", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "47e7d8b2-b8a2-436d-b138-2559d14d65ca", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360962, "utm_y": 5647362, "lat": 50.961070412832775, "lng": 7.020118502118784, "suburb": "Buchheim", "suburb_id": "903", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "f73fdbc9-0b83-4781-9ae6-23f8b49847f5", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360951, "utm_y": 5647318, "lat": 50.96067232212215, "lng": 7.019978777364573, "suburb": "Buchheim", "suburb_id": "903", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "ac524eaf-e0bd-4a59-8f15-121979bd3bb2", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360953, "utm_y": 5647338, "lat": 50.96085254849879, "lng": 7.019999596220834, "suburb": "Buchheim", "suburb_id": "903", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "fee2b0e4-43e2-4aa0-83a1-b5883b3561f8", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 359914, "utm_y": 5646498, "lat": 50.953051701857916, "lng": 7.005537309087425, "suburb": "Buchforst", "suburb_id": "902", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "a8e36f33-f0ae-4d6c-8c83-672e4e5d36bb", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 361136, "utm_y": 5647537, "lat": 50.96268513446992, "lng": 7.02252787151031, "suburb": "Buchheim", "suburb_id": "903", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "e2b09d50-2100-4792-80b7-bb57d8b19d63", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360061, "utm_y": 5648747, "lat": 50.9732994297337, "lng": 7.006763832245437, "suburb": "Mülheim", "suburb_id": "901", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": {"by_radius_prediction": {"genus": {"prediction": "Acer", "probability": 0.62}, "age_group": {"prediction": 2, "probability": 0.38}, "year_sprout": {"prediction": 1976, "probability": 0.62}}}},
        {"tree_id": "f5b92eb3-1194-4017-a1ad-2ca3a3377129", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360034, "utm_y": 5648942, "lat": 50.975045351426516, "lng": 7.006304440166276, "suburb": "Mülheim", "suburb_id": "901", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "56b3d1e9-7ab6-48c8-98db-731d803f86ba", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360053, "utm_y": 5648926, "lat": 50.974906175445525, "lng": 7.006581062237473, "suburb": "Mülheim", "suburb_id": "901", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "86ff4c30-43c4-47ac-88f1-58b727a299df", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360048, "utm_y": 5648949, "lat": 50.97511166347409, "lng": 7.006501034640266, "suburb": "Mülheim", "suburb_id": "901", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None},
        {"tree_id": "29d271da-1ce1-47e0-929c-ab87729baf7c", "dataset_completeness": 0.08, "base_info_completeness": 0.33, "tree_taxonomy_completeness": 0.0, "tree_measures_completeness": 0.0, "tree_age_completeness": 0.0, "base_info": {"object_type": "building/school/dormitory (home) building", "tree_nr": None, "year_planting": None}, "geo_info": {"utm_x": 360039, "utm_y": 5648956, "lat": 50.97517238587142, "lng": 7.006370225506254, "suburb": "Mülheim", "suburb_id": "901", "district": "Mülheim", "district_id": "9"}, "tree_taxonomy": {"genus": None, "genus_name_german": None, "species": None, "type": None, "name_german": None}, "tree_measures": {"height": None, "treetop_radius": None, "bole_radius": None}, "tree_age": {"year_sprout": None, "age_in_2020": None, "age_group_2020": None}, "found_in_dataset": {"2017": False, "2020": True}, "predictions": None}
    ]

    new_tree_data_list = get_tree_location_types(tree_data_list)
    for t in new_tree_data_list:
        print(t["tree_location_type"])
        # if t["tree_location_type"] is None:
        #     print("   ", t["geo_info"]["lat"], t["geo_info"]["lng"])
