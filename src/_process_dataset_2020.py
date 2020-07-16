import csv
import datetime
import json
from typing import Any, Dict, List
import uuid

from _geo import check_point_in_suburb_polygons
from predictions._age_regression import predict_year_sprout

import utm  

# ***
# https://github.com/Turbo87/utm
# utm usage:
# lat, lng = utm.to_latlon(359814, 5645658, 32, 'U')
# print(lat, lng)


def process_dataset_2020() -> List[Dict[str, Any]]:
    with open("../data/original_data/20200610_Baumbestand_Koeln.csv") as f:
        reader = csv.DictReader(f, delimiter=",")
        rows = list(reader)

    with open("../data/meta/object_types.json") as f:
        object_types = json.load(f)

    with open("../data/meta/genus_name_german.json") as f:
        genus_name_german = json.load(f)


    lines = []
    i = 0
    for row in rows:
        i += 1
        if i % 10000 == 0:
            print(i)
        try:
            x = int(row["x_koordina"])
            y = int(row["y_koordina"])

            # ***
            # ignore if geo data is not valid / missing
            lat, lng = (None, None)
            try:
                lat, lng = utm.to_latlon(x, y, 32, 'U')
            except Exception as e:
                # print(f"lat lng ERR ----> {e}")
                continue
            if lat is None or lng is None:
                continue

            height = None
            treetop_radius = None
            bole_radius = None
            try:
                if int(row["H_HE"]) > 0:
                    height = int(row["H_HE"])
            except:
                pass
            try:
                if int(row["KRONE"]) > 0:
                    treetop_radius = int(row["KRONE"])
            except:
                pass
            try:
                if int(row["STAMMBIS"]) > 0:
                    bole_radius = int(row["STAMMBIS"])
            except:
                pass

            object_type = None
            try:
                object_type = object_types["en"].get(row["objekttyp"])
                if object_type in ["NN", "Unbekannt", "unknown", "?"]:
                    object_type = None
            except:
                pass
            
            
            year_planting = None
            try:
                if int(row["PFLANZJAH"]) > 0:
                    year_planting = int(row["PFLANZJAH"])
            except:
                pass

            
            suburb_name = None
            suburb_id = None
            district_name = None
            district_id = None

            suburb_polygon_feature = check_point_in_suburb_polygons(lat, lng)
            if suburb_polygon_feature is not None:
                try:
                    suburb_name = suburb_polygon_feature["NAME"]
                    suburb_id = suburb_polygon_feature["NUMMER"]
                    district_name = suburb_polygon_feature["STADTBEZIRK"]
                    district_id = suburb_polygon_feature["NR_STADTBEZIRK"]
                except:
                    pass

            
            taxo_genus = row["Gattung"] if len(row["Gattung"]) > 0 and row["Gattung"] not in ["unbekannt", "?"] else None
            taxo_species = row["Art"] if len(row["Art"]) > 0 and row["Art"] not in ["unbekannt", "?"] else None
            taxo_type = row["Sorte"] if len(row["Sorte"]) > 0 and row["Sorte"] not in ["unbekannt", "?"] else None
            taxo_name_german = [x.strip() for x in row["DeutscherN"].split(",")] if len(row["DeutscherN"]) > 0 and row["DeutscherN"] not in ["unbekannt", "?"] else None


            year_sprout_from_regression = None
            if taxo_genus is not None and bole_radius is not None:
                try:
                    year_sprout_from_regression = predict_year_sprout(taxo_genus, bole_radius)
                except:
                    pass

            age_in_2020 = None
            age_group = None
            try:
                age_in_2020 = 2020 - year_sprout_from_regression
                for j, group in enumerate([(1,26), (26,41), (41,1000)]):
                    lower_boundary = group[0]
                    upper_boundary = group[1]
                    if age_in_2020 >= lower_boundary and age_in_2020 < upper_boundary:
                        age_group = j
                        break
            except:
                pass

            tree_id = str(uuid.uuid4()) 
            
            
            tmp = {
                "tree_id": tree_id,
                "dataset_completeness": 0.0,
                "base_info_completeness": 0.0,
                "tree_taxonomy_completeness": 0.0,
                "tree_measures_completeness": 0.0,
                "tree_age_completeness": 0.0,
                "base_info":
                {
                    "object_type": object_type,
                    "tree_nr": row["baumnr"] if len(row["baumnr"]) > 0 else None,
                    "year_planting": year_planting
                },
                "geo_info":
                {
                    "utm_x": x,
                    "utm_y": y,
                    "lat": lat,
                    "lng": lng,
                    "suburb": suburb_name,
                    "suburb_id": suburb_id,
                    "district": district_name,
                    "district_id": district_id,
                },
                "tree_taxonomy":
                {
                    "genus": taxo_genus,
                    "genus_name_german": genus_name_german[taxo_genus]["name_german"] if genus_name_german.get(taxo_genus) is not None else None,
                    "species": taxo_species,
                    "type": taxo_type,
                    "name_german": taxo_name_german,
                },
                "tree_measures":
                {
                    "height": height,
                    "treetop_radius": treetop_radius,
                    "bole_radius": bole_radius
                },
                "tree_age":
                {
                    "year_sprout": year_sprout_from_regression,
                    "age_in_2020": age_in_2020,
                    "age_group_2020": age_group,
                }
            }

            # ********
            # % completeness in "base_info", tree_taxonomy and "tree_info"
            # and overall completeness in "dataset_completeness"
            tmp_completeness_collected = 0.0
            tmp_completeness_attr = ["base_info", "tree_taxonomy", "tree_measures", "tree_age"]
            for k in tmp_completeness_attr:
                collected_types_perc = round(len([type(x).__name__ for x in tmp[k].values() if type(x).__name__ != "NoneType"]) / len(tmp[k].values()), 2)  # i.e. ["NoneType", "str", "int", "str"]
                tmp[f"{k}_completeness"] = collected_types_perc
                tmp_completeness_collected += collected_types_perc

            try:
                tmp_completeness_collected = round(tmp_completeness_collected / len(tmp_completeness_attr), 2)
            except:
                pass
            tmp["dataset_completeness"] = tmp_completeness_collected

            lines.append(tmp)
        except Exception as e:
            pass
    
    return lines
