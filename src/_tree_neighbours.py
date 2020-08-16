import json
from math import radians, cos, sin, asin, sqrt
from typing import Any, Dict, List, Optional, Tuple

from _geo import get_bounding_box_around_lat_lng_center, get_neighbouring_suburbs, get_earth_radius



RADIUS = 50  # circle radius / bounding box half size in meter
MIN_TREE_DISTANCE = 3  # in meter
EARTH_RADIUS, EARTH_PRADIUS = get_earth_radius(50.935173)  # latitude Cologne, Germany


# ********************
# clean up pairs of close tree
# ********************
def _check_duplicate_tree(tree_1: Dict[str, Any], tree_2: Dict[str, Any]) -> str:
    tmp_is_duplicate: bool = False
    skipped_tree_id: Optional[str] = None

    # ***
    # use genus (value or None) to detemine if duplicate
    tmp_genus: List[str] = []
    for tree in [tree_1, tree_2]:
        if tree["tree_taxonomy"]["genus"] is not None:  # assumption: None means old incomplete data
            tmp_genus.append(tree["tree_taxonomy"]["genus"])
    if len(list(set(tmp_genus))) <= 1:  # both same value (len: 1) OR 1 or both None (== len: 0)
        tmp_is_duplicate = True
    
    # ***
    # take highest completeness
    if tmp_is_duplicate is True:
        tree_data_list = [tree_1, tree_2]
        tmp_completeness: List[float] = []
        
        for tree in tree_data_list:
            tmp_completeness.append(tree["dataset_completeness"])
        
        tmp_max_completeness_index = tmp_completeness.index(max(tmp_completeness))
        
        for i in range(len(tmp_completeness)):  # by definition only 2
            if i == tmp_max_completeness_index:
                continue
            skipped_tree_id = tree_data_list[i]["tree_id"]

    return skipped_tree_id


def cleanup_close_pairs(merged_data: List[Dict[str, Any]], close_pair_list: List[Any]) -> List[Dict[str, Any]]:
    def _arrange_tree_list_to_dict(merged_data: List[Any]) -> Dict[str, Any]:
        tree_dict: Dict[str, Any] = {}
        for tree in merged_data:
            tree_dict[tree["tree_id"]] = tree
        return tree_dict

    tree_dict = _arrange_tree_list_to_dict(merged_data)

    new_merged_data: List[Dict[str, Any]] = []
    skipped_tree_ids: List[str] = []
    
    for tree_pair in close_pair_list:
        tree_1_id: str = tree_pair[0]
        tree_2_id: str = tree_pair[1]
        distance: float = tree_pair[2]

        tree_1 = tree_dict[tree_1_id]
        tree_2 = tree_dict[tree_2_id]

        # **********
        # check if min. 1 id is already skipped -> no need to check further
        # **********
        pair_tree_already_in_list: bool = False
        for tree_id in [tree_1_id, tree_2_id]:
            if tree_id in skipped_tree_ids:
                pair_tree_already_in_list = True
                break

        if pair_tree_already_in_list is True:
            continue

        # **********
        # both are in same timeline: use better entry OR use newer entry
        # **********
        if tree_1["found_in_dataset"]["2020"] == tree_2["found_in_dataset"]["2020"]:  # both True or False: same timeline
            skipped_tree_id = _check_duplicate_tree(tree_1, tree_2)  # use the "better" tree
            if skipped_tree_id not in skipped_tree_ids:  # add to skip list
                skipped_tree_ids.append(skipped_tree_id)
        else:
            if tree_1["found_in_dataset"]["2020"] == False:  # OR use the "newer" tree
                skipped_tree_ids.append(tree_1_id)
            else:
                skipped_tree_ids.append(tree_2_id)

    # **********
    # use trees NOT in skip list
    # **********
    for tree_id in tree_dict.keys():
        if tree_id in skipped_tree_ids:
            continue
        new_merged_data.append(tree_dict[tree_id])

    return new_merged_data
        

# ********************
# find trees in radius of each tree and pairs of close trees
# ********************
def _haversine(lon1, lat1, lon2, lat2):
    """
    https://stackoverflow.com/a/4913653
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    distance_in_km = c * r
    distance_in_m = round(((c * r)*1000), 2)
    return distance_in_m


def _check_in_bounding_box(min_lat: float, max_lat: float, min_lng: float, max_lng: float, tree: Dict[str, Any]) -> bool:
    if tree["lat"] < min_lat or tree["lat"] > max_lat:
        return False
    if tree["lng"] < min_lng or tree["lng"] > max_lng:
        return False
    return True
    

def _calculate_distance(suburb_trees: Dict[str, Any], current_suburb: str):
    close_pairs = []
    all_pairs = []  # without neighbours which are TOO close
    
    for i in range(len(suburb_trees)):
        tree_1 = suburb_trees[i]

        # if i % 1000 == 0:
        #     print(f"-- {i} {current_suburb} --")

        if tree_1["suburb_id"] != current_suburb:
            continue
        
        try:
            min_lat, max_lat, min_lng, max_lng = get_bounding_box_around_lat_lng_center(tree_1["lat"], tree_1["lng"], RADIUS, EARTH_RADIUS, EARTH_PRADIUS)
        except:
           continue

        # print(tree_1["lat"], "--", min_lat, max_lat, min_lng, max_lng)

        for j in range(i, len(suburb_trees)):
            if j <= i:
                continue

            try:
                tree_2 = suburb_trees[j]
                is_in_bounding_box = _check_in_bounding_box(min_lat, max_lat, min_lng, max_lng, tree_2)
                
                # print(is_in_bounding_box, tree_2["lat"], tree_2["lng"])
                if is_in_bounding_box is False:
                    continue
            except:
                continue

            # print(f"   {j} {is_in_bounding_box}")

            try:
                distance = _haversine(tree_1["lng"], tree_1["lat"], tree_2["lng"], tree_2["lat"])

                if distance >= MIN_TREE_DISTANCE and distance <= RADIUS:
                    all_pairs.append([tree_1["id"], tree_2["id"], distance])
                
                if distance < MIN_TREE_DISTANCE:
                    print(f'   {current_suburb} - {i} {j} - {distance}')
                    close_pairs.append([tree_1["id"], tree_2["id"], distance])
            except:
                continue
    
    return close_pairs, all_pairs


def process_tree_neighbours(merged_data: List[Any]) -> None:
    neighbouring_suburbs = get_neighbouring_suburbs()
    
    trees_by_suburb: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    trees_neighbours: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for tree_data in merged_data:
        current_suburb = tree_data["geo_info"]["suburb_id"]
        if trees_by_suburb.get(current_suburb) is None:
            trees_by_suburb[current_suburb]: List[str, Any] = []
        trees_by_suburb[current_suburb].append({
            "id": tree_data["tree_id"],
            "lat": tree_data["geo_info"]["lat"],
            "lng": tree_data["geo_info"]["lng"],
            "suburb_id": tree_data["geo_info"]["suburb_id"]
        })


    close_pairs = []
    all_pairs = []  # without neighbours which are TOO close

    compared_suburbs: Dict[str, List[str]] = {}
    
    for current_suburb in trees_by_suburb.keys():
        if current_suburb is None:
            continue

        if compared_suburbs.get(current_suburb) is None:
            compared_suburbs[current_suburb] = []

        trees_to_compare: List[Dict[str, Any]] = trees_by_suburb[current_suburb]
        
        for neighbouring_suburb in neighbouring_suburbs[current_suburb]:
            if neighbouring_suburb in compared_suburbs[current_suburb]:
                continue

            if compared_suburbs.get(neighbouring_suburb) is not None:
                if current_suburb in compared_suburbs[neighbouring_suburb]:
                    continue

            # ***
            # add to compare list
            trees_to_compare += trees_by_suburb[neighbouring_suburb]

            # ***
            #
            compared_suburbs[current_suburb].append(neighbouring_suburb)

            if compared_suburbs.get(neighbouring_suburb) is None:
                compared_suburbs[neighbouring_suburb] = []
            
            if current_suburb in compared_suburbs[neighbouring_suburb]:
                continue

            compared_suburbs[neighbouring_suburb].append(current_suburb)
 
        # ***
        # do compare
        print(f"----- {current_suburb} {len(trees_to_compare)} -----")
        close_pairs_in_suburb, all_pairs_in_suburb = _calculate_distance(trees_to_compare, current_suburb)
        close_pairs += close_pairs_in_suburb
        all_pairs += all_pairs_in_suburb
        print(f"  {len(all_pairs_in_suburb)}, {len(close_pairs_in_suburb)}")
        print()
        
    return close_pairs, all_pairs
    