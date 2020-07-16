from typing import Any, Dict, List, Tuple

from predictions._clustered_neighbour_trees import train_neighbouring_tree_cluster

import pandas as pd


def _load_neighbour_pairs(tree_pairs: List[Any]) -> Dict[str, Dict[str, float]]:
    tree_pairs_by_id: Dict[str, Any] = {}
    for pair in tree_pairs:
        id_1 = pair[0]
        id_2 = pair[1]
        distance = pair[2]
        
        # ***
        # bi-directionaly
        if tree_pairs_by_id.get(id_1) is None:
            tree_pairs_by_id[id_1] = {}
        tree_pairs_by_id[id_1][id_2] = distance

        if tree_pairs_by_id.get(id_2) is None:
            tree_pairs_by_id[id_2] = {}
        tree_pairs_by_id[id_2][id_1] = distance

    return tree_pairs_by_id


def _get_reduced_data(tree_data: List[Any]) -> pd.DataFrame:
    lines: List[Dict[str, Any]] = []
    for tree in tree_data:
        try:
            lines.append({
                "id": tree["tree_id"],
                "year_sprout": tree["tree_age"]["year_sprout"],
                "age_group_2020": tree["tree_age"]["age_group_2020"],
                "genus": tree["tree_taxonomy"]["genus"],
            })
        except Exception as e:
            print(e)
            pass
        
    return pd.DataFrame(lines)


def _enrich_tree_data(tree_data: List[Any], predictions: Dict[str, Any]) -> List[Any]:
    for i, tree in enumerate(tree_data):
        tree_id = tree["tree_id"]
        tree_data[i]["predictions"] = None

        if predictions.get(tree_id) is None:
            continue

        tree_data[i]["predictions"] = {
            "by_radius_prediction": predictions[tree_id]
        }
        
    return tree_data


def predict_genus_age(tree_data: List[Any], tree_pairs_list: List[Any]) -> None:
    print("process data...")
    df = _get_reduced_data(tree_data)
    tree_pairs_by_id = _load_neighbour_pairs(tree_pairs_list)

    print("start prediction script...")
    predictions = train_neighbouring_tree_cluster(df, tree_pairs_by_id)

    print("merge predictions with tree data...")
    tree_data = _enrich_tree_data(tree_data, predictions)

    return tree_data
    