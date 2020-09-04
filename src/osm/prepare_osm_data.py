import json
import os
from typing import Any, Dict, List, Tuple

import requests
from shapely.geometry import LineString, Polygon
from slugify import slugify


OVERPASS_URL = "http://overpass-api.de/api/interpreter"
OSM_DATA_OUT_DIR = "../../data/geo_data/osm"

POLYGON_GEOJSON = "../../data/geo_data/cologne_districts_reduced_polygons.geojson"


# **************************
#
# **************************
def _load_polygon_data() -> List[Dict[str, Any]]:
    with open(POLYGON_GEOJSON) as f:
        data = json.load(f)
    return data["features"]


def _get_suburb_polygon_min_max_data(coordinates: List[List[List[float]]]) -> Tuple[float, float, float, float]:
    min_lat = None
    min_lng = None
    max_lat = None
    max_lng = None
    for lng_lat_pair in coordinates:
        current_lng = lng_lat_pair[0]
        current_lat = lng_lat_pair[1]
        
        # 1. iteration: init
        if min_lat is None and max_lat is None:
            min_lat = current_lat
            max_lat = current_lat
        if min_lng is None and max_lng is None:
            min_lng = current_lng
            max_lng = current_lng
        
        # 2. check/assign min, max
        if current_lat < min_lat:
            min_lat = current_lat
        if current_lat > max_lat:
            max_lat = current_lat
        if current_lng < min_lng:
            min_lng = current_lng
        if current_lng > max_lng:
            max_lng = current_lng
    
    return min_lng, min_lat, max_lng, max_lat


# **************************
# see also: https://wiki.openstreetmap.org/wiki/DE:Key:landuse
# **************************
def request_osm_urban_green_spaces(min_lng: float, min_lat: float, max_lng: float, max_lat: float) -> Dict[str, Any]:
    '''
    See also: https://janakiev.com/blog/openstreetmap-with-python-and-overpass-api/
    '''
    overpass_query = f"""
        [out:json];
	    (
            way["leisure"="park"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["leisure"="park"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        way["leisure"="playground"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["leisure"="playground"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
            way["landuse"="grass"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["landuse"="grass"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        way["landuse"="recreation_ground"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["landuse"="recreation_ground"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
            way["landuse"="cemetery"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["landuse"="cemetery"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
            way["landuse"="recreation_ground"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["landuse"="recreation_ground"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
        );
        out geom;"""

    response = requests.get(OVERPASS_URL, params={'data': overpass_query})
    return response.json()


def request_osm_agriculture(min_lng: float, min_lat: float, max_lng: float, max_lat: float) -> Dict[str, Any]:
    '''
    Agriculture in the broadest sense incl. landuse = forest
    See also: https://janakiev.com/blog/openstreetmap-with-python-and-overpass-api/
    '''
    overpass_query = f"""
        [out:json];
	    (
            way["landuse"="allotments"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["landuse"="allotments"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
            way["landuse"="farmland"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["landuse"="farmland"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
            way["landuse"="forest"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["landuse"="forest"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
            way["landuse"="meadow"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["landuse"="meadow"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
            way["landuse"="orchard"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
  	        relation["landuse"="orchard"]({min_lat},{ min_lng}, {max_lat}, {max_lng});
        );
        out geom;"""

    # print(overpass_query)

    response = requests.get(OVERPASS_URL, params={'data': overpass_query})
    return response.json()


def request_osm_highway(min_lng: float, min_lat: float, max_lng: float, max_lat: float) -> Dict[str, Any]:
    '''
    See also: https://janakiev.com/blog/openstreetmap-with-python-and-overpass-api/
    '''
    overpass_query = f"""
        [out:json];
	    (
            way( {min_lat},{min_lng}, {max_lat}, {max_lng})[highway];
  	    );
        out geom;"""

    response = requests.get(OVERPASS_URL, params={'data': overpass_query})
    return response.json()


# **************************
#
# **************************
def create_geojson_polygon(elements: Dict[str, Any], current_city_area_polygon: List[List[float]]) -> Dict[str, Any]:
    current_geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    def get_current_feature(element: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        tmp_properties = {
            "osm_id": element["id"],
            "osm_type": element["type"],
            "type": None,
            "name": element["tags"].get("name"),
            "wikidata_id": element["tags"].get("wikidata"),
            "bounding_box": [
                element["bounds"]["minlat"],
                element["bounds"]["minlon"],
                element["bounds"]["maxlat"],
                element["bounds"]["maxlon"]
            ]
        }
        
        has_valid_type = False
        for t in ["landuse", "leisure", "amenity", "highway"]:
            try:
                tmp_properties["type"] = element["tags"][t]
                has_valid_type = True
                break
            except:
                continue
        
        if has_valid_type is False:
            return None, None

        tmp_geometry = {
            "type": None,
            "coordinates": None
        }

        try:
            if element["geometry"][0] == element["geometry"][-1]:  # is a Polygon
                tmp_geometry["type"] = "Polygon"
                tmp_geometry["coordinates"] = [[]]
                
                for p in element["geometry"]:
                    tmp_geometry["coordinates"][0].append([p["lon"], p["lat"]])
            else:  # is a LineString i.e. highway
                tmp_geometry["type"] = "LineString"

                lng_lat_list = [list(pair.values()) for pair in element['geometry']]
                lat_lng_list = [[pair[1], pair[0]] for pair in lng_lat_list]
                
                tmp_geometry["coordinates"] = lat_lng_list
        except Exception as e:
            print(f"ERROR: {e}")
            print(json.dumps(element))
            return None, None

        return tmp_properties, tmp_geometry


    def get_iou(geometry_1: List[List[float]], geometry_2: List[List[float]]) -> float:
        '''
        https://stackoverflow.com/a/57247833
        Not used.
        '''
        poly_1: Polygon = Polygon(geometry_1)
        poly_2: Polygon = Polygon(geometry_2)
        iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
        
        return iou
    

    def get_precentage_poly_intersection(geometry_1: List[List[float]], geometry_2: List[List[float]]) -> float:
        poly_1: Polygon = Polygon(geometry_1)
        poly_2: Polygon = Polygon(geometry_2)

        return poly_1.intersection(poly_2).area/poly_1.area


    def get_line_poly_intersection(line_coordinates: List[List[float]], poly_coordinates: List[List[float]]) -> bool:
        '''
        https://gis.stackexchange.com/a/82719
        '''
        polygon = Polygon(poly_coordinates)
        line = LineString(line_coordinates)

        return line.intersects(polygon)


    for element in elements["elements"]:
        osm_type = element["type"]
        if osm_type == "way":
            tmp_properties, tmp_geometry = get_current_feature(element)

            intersects_area = False
            if tmp_geometry["type"] == "LineString":
                intersects_area = get_line_poly_intersection(tmp_geometry["coordinates"], current_city_area_polygon)
            else:
                perc_intersection = get_precentage_poly_intersection(tmp_geometry["coordinates"][0], current_city_area_polygon)
                if perc_intersection > 0.05:
                    intersects_area = True
                
            if intersects_area is True:
                current_geojson["features"].append({
                    "type": "Feature",
                    "properties": tmp_properties,
                    "geometry": tmp_geometry
                })
        
        # **
        # TODO How to handle?
        if osm_type == "relation":
            continue

    return current_geojson


def save_geojson(file_name: str, dir_name: str, geojson: Dict[str, Any]) -> None:
    with open(f"{OSM_DATA_OUT_DIR}/{dir_name}/{file_name}.json", "w") as f:
        f.write(json.dumps(geojson, indent=2, ensure_ascii=False))


def check_file_exists(file_name: str, dir_name: str) -> bool:
    return os.path.isfile(f"{OSM_DATA_OUT_DIR}/{dir_name}/{file_name}.json")


if __name__ == "__main__":
    polygon_geojson_data = _load_polygon_data()

    print(f"Number of suburbs: {len(polygon_geojson_data)}")

    for i, suburb_data in enumerate(polygon_geojson_data):
        file_name = f'{slugify(suburb_data["properties"]["STADTBEZIRK"], replace_latin=True)}_{slugify(suburb_data["properties"]["NAME"], replace_latin=True)}'
        print(i, file_name)

        current_city_area_polygon = suburb_data["geometry"]["coordinates"][0]
        min_lng, min_lat, max_lng, max_lat = _get_suburb_polygon_min_max_data(current_city_area_polygon)
        
        # ***
        # agricultural
        if check_file_exists(file_name, "green_spaces_agriculture") is False:
            try:
                osm_result_agriculture = request_osm_agriculture(min_lng, min_lat, max_lng, max_lat)
                geojson_agriculture = create_geojson_polygon(osm_result_agriculture, current_city_area_polygon)
                save_geojson(file_name, "green_spaces_agriculture", geojson_agriculture)
            except Exception as e:
                print(f"   ERROR green_spaces_agriculture: {e}")
        else:
            print("   skip green_spaces_agriculture")

        # ***
        # parks et.al.
        if check_file_exists(file_name, "green_spaces_leisure") is False:
            try:
                osm_result_leisure = request_osm_urban_green_spaces(min_lng, min_lat, max_lng, max_lat)
                geojson_leisure = create_geojson_polygon(osm_result_leisure, current_city_area_polygon)
                save_geojson(file_name, "green_spaces_leisure", geojson_leisure)
            except Exception as e:
                print(f"   ERROR green_spaces_leisure: {e}")
        else:
            print("   skip green_spaces_leisure")

        # ***
        # all street types
        if check_file_exists(file_name, "highway") is False:
            try:
                osm_result_highway = request_osm_highway(min_lng, min_lat, max_lng, max_lat)
                geojson_highway = create_geojson_polygon(osm_result_highway, current_city_area_polygon)
                save_geojson(file_name, "highway", geojson_highway)
            except Exception as e:
                print(f"   ERROR highway: {e}")
        else:
            print("   skip highway")

