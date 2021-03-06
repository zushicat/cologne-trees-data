'''
The whole process takes a while (especially the processes under 4. and 6.), 0:52:18.818303 to be precise. 
Temporary results of each step are stored in /tmp and can be deleted after finishing the whole process chain.
You might want to take a longer coffee break when processing all at once or apply the script step by step.
'''

from datetime import datetime
import json
import os
from typing import Any, Dict, List

from _geo import create_suburb_polygons, find_neighbouring_suburbs
from _process_dataset_2017 import process_dataset_2017
from _process_dataset_2020 import process_dataset_2020
from _merge_datasets import merge_datasets
from _tree_neighbours import cleanup_close_pairs, process_tree_neighbours
from _predict_genus_age import predict_genus_age
from _osm_type import get_suburb_data, get_tree_location_types
from _export import create_reduced_data, save_compressed_data


def _save_tmp_data(file_name: str, data_to_save: List[Any]) -> None:
    with open(f"../data/tmp/{file_name}", "w") as f:
        for line in data_to_save:
            f.write(f"{json.dumps(line, ensure_ascii=False)}\n")


def _load_tmp_data() -> Dict[str, List[Dict[str, Any]]]:
    datasets: Dict[str, List[Dict[str, Any]]] = {"2017": [], "2020": []}
    for file_name in ["data_2017.jsonln", "data_2020.jsonln"]:
        with open(f"../data/tmp/{file_name}") as f:
            file_data = f.read().split("\n")
        if file_name.find("2017") != -1:
            datasets["2017"] = file_data
        else:
            datasets["2020"] = file_data
    
    return datasets


def _load_list_tmp_data(file_name: str) -> List[Dict[str, Any]]:
    with open(f"../data/tmp/{file_name}") as f: 
        incoming = f.read().split("\n")
    out: List[Dict[str, Any]] = []
    for line in incoming:
        try:
            out.append(json.loads(line))
        except:
            pass
    return out


start_time = datetime.now()  # set timer
print(f"Start: {start_time}")

# *******
# 1 - compute some geo data (both calls only take milliseconds)
# *******
create_suburb_polygons()
find_neighbouring_suburbs()  # needed for more efficient tree neighbour processing; keep uncommented until 4. is done

print(f"1. done: {datetime.now()-start_time}")

# *******
# 2 - create base datasets from original "Baumkataster" csv data
# *******
_save_tmp_data("data_2017.jsonln", process_dataset_2017())
_save_tmp_data("data_2020.jsonln", process_dataset_2020())

print(f"2. done: {datetime.now()-start_time}")

# *******
# 3 - merge datasets 2017 / 2020
# *******
datasets = _load_tmp_data()
_save_tmp_data("data_merged.jsonln", merge_datasets(datasets))

merged_data = _load_list_tmp_data("data_merged.jsonln")

print(f"3. done: {datetime.now()-start_time}")

# *******
# 4 - process neighbour trees in radius, then clean up pairs of close trees (< 2m)
# *******
close_pairs, all_pairs = process_tree_neighbours(merged_data)  # takes approx. 20 minutes
_save_tmp_data("neighbours_close_pairs.jsonln", close_pairs)
_save_tmp_data("neighbours_all_pairs.jsonln", all_pairs)

close_pair_list = _load_list_tmp_data("neighbours_close_pairs.jsonln")  # takes approx. 10-20 secs.
merged_data = cleanup_close_pairs(merged_data, close_pair_list)
_save_tmp_data("data_merged_cleanup.jsonln", merged_data)

print(f"4. done: {datetime.now()-start_time}")

# *******
# 5 - predict genus and/or age resp. age_group by clusters of neighbouring trees
# *******
merged_data = _load_list_tmp_data("data_merged_cleanup.jsonln")
neighbours_pairs = _load_list_tmp_data("neighbours_all_pairs.jsonln")

merged_data_with_predictions = predict_genus_age(merged_data, neighbours_pairs)
_save_tmp_data("data_merged_with_predictions.jsonln", merged_data_with_predictions)

print(f"5. done: {datetime.now()-start_time}")

# *******
# 6 - get location types
# *******
get_suburb_data()
merged_data_with_predictions = _load_list_tmp_data("data_merged_with_predictions.jsonln")

merged_data_with_predictions = get_tree_location_types(merged_data_with_predictions)
_save_tmp_data("data_merged_with_predictions.jsonln", merged_data_with_predictions)

# *******
# 7 - write compressed exports to /data/exports
# *******
save_compressed_data("trees_cologne.jsonln", "../data/tmp/data_merged_with_predictions.jsonln")

merged_data_with_predictions = _load_list_tmp_data("data_merged_with_predictions.jsonln")
reduced_tree_data = create_reduced_data(merged_data_with_predictions)
_save_tmp_data("data_merged_with_predictions_reduced.jsonln", reduced_tree_data)
save_compressed_data("trees_cologne_reduced.jsonln", "../data/tmp/data_merged_with_predictions_reduced.jsonln")

# Finished
print(f"All done. {datetime.now()-start_time}")