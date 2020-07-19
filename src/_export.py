import json
import tarfile
from typing import Any, Dict, List, Optional
import os


DATA_PATH = "../data/exports"


def _get_reduced_tree_data(tree_data: Dict[str, Any]) -> Dict[str, Any]: # <-- check typing for .geojson datapoint return value
    new_tree_data: Dict[str, Optional[str, int, float]] = {
        "tree_id": tree_data["tree_id"],
        "district_number": tree_data["base_info"]["district_number"],
        "lat": tree_data["geo_info"]["lat"],
        "lng": tree_data["geo_info"]["lng"],
        "genus": None,
        "in_dataset_2020": tree_data["found_in_dataset"]["2020"],
        "age_group": tree_data["tree_age"]["age_group_2020"]  # check if none -> from prediction
    }

    if new_tree_data["age_group"] is None:
        if tree_data["predictions"] is not None:
            if tree_data["predictions"].get("age_prediction") is not None:
                if tree_data["predictions"]["age_prediction"]["probabiliy"] >= 0.5:
                    new_tree_data["age_group"] = tree_data["predictions"]["age_prediction"]["age_group_2020"]
            else:
                if tree_data["predictions"].get("by_radius_prediction") is not None:
                    if tree_data["predictions"]["by_radius_prediction"]["probabiliy"] >= 0.5:
                        new_tree_data["age_group"] = tree_data["predictions"]["by_radius_prediction"]["age_group_2020"]

    
    if tree_data["tree_taxonomy"]["genus"] is not None:
        new_tree_data["genus"] = tree_data["tree_taxonomy"]["genus"]
    else:
        try: 
            new_tree_data["genus"] = tree_data["predictions"]["by_radius_prediction"]["genus"]
        except:
            pass


    return new_tree_data

def create_reduced_data(tree_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    new_tree_data_list: List[Dict[str, Any]] = []
    for tree_data in tree_data_list:
        new_tree_data: Dict[str, Optional[str, int, float]] = {
            "tree_id": tree_data["tree_id"],
            "district_number": tree_data["geo_info"]["district_id"],
            "lat": tree_data["geo_info"]["lat"],
            "lng": tree_data["geo_info"]["lng"],
            "in_dataset_2020": tree_data["found_in_dataset"]["2020"],
            "genus": None,
            "age_group": None
        }

        if tree_data["tree_age"]["age_group_2020"] is not None:
            new_tree_data["age_group"] = tree_data["tree_taxonomy"]["genus"]
        else:
            try: 
                if tree_data["predictions"]["by_radius_prediction"]["age_group"]["probability"] >= 0.5:
                    new_tree_data["age_group"] = tree_data["predictions"]["by_radius_prediction"]["age_group"]["prediction"]
            except:
                pass
        
        if tree_data["tree_taxonomy"]["genus"] is not None:
            new_tree_data["genus"] = tree_data["tree_taxonomy"]["genus"]
        else:
            try: 
                if tree_data["predictions"]["by_radius_prediction"]["genus"]["probability"] >= 0.5:
                    new_tree_data["genus"] = tree_data["predictions"]["by_radius_prediction"]["genus"]["prediction"]
            except:
                pass
        
        new_tree_data_list.append(new_tree_data)
    
    return new_tree_data_list



def save_compressed_data(out_file_name: str, in_file_path: str) -> None:
    with tarfile.open(f"{DATA_PATH}/{out_file_name}.tar.gz", "w:gz") as tar:
        tar.add(in_file_path, arcname=os.path.basename(in_file_path))
