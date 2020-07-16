# from collections import Counter, defaultdict
import json
from typing import Any, Dict, List, Optional,Tuple

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn import metrics
from sklearn.cluster import DBSCAN


MIN_SAMPLES = 5


def _split_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df["has_all"] = False
    df["missing_all"] = False
    df["missing_age_only"] = False

    df["has_all"] = pd.notna(df[["age_group_2020", "genus"]]).all(axis=1)
    df["missing_all"] = pd.isna(df[["age_group_2020", "genus"]]).all(axis=1)
    df["missing_age_only"] = df.apply(lambda x: True if (pd.notna(x.genus) and pd.isnull(x.age_group_2020)) else False, axis=1)

    drop_cols = ["has_all", "missing_all", "missing_age_only"]

    df_has_all = df[df["has_all"] == True].drop(drop_cols, axis=1)
    df_has_no_age = df[(df["missing_all"]==False) & (df["missing_age_only"]==True)].drop(drop_cols, axis=1)
    df_has_none = df[df["missing_all"] == True].drop(drop_cols, axis=1)

    df_has_all = df_has_all.dropna()

    df_has_all.reset_index(drop=True, inplace=True)
    df_has_no_age.reset_index(drop=True, inplace=True)
    df_has_none.reset_index(drop=True, inplace=True)

    return df_has_all, df_has_no_age, df_has_none


def _get_tree_features_by_id(df: pd.DataFrame) -> Dict[str, Any]:
    tree_features_by_id: Dict[str, Any] = {}
    for index, row in df.iterrows():
        tree_features_by_id[row["id"]] = {
            "age_group_2020": row["age_group_2020"],
            "year_sprout": row["year_sprout"],
            "encoded_genus": row["encoded_genus"]
        }
    
    return tree_features_by_id


def _get_cluster(current_tree_pairs: Dict[str, Any], tree_features_by_id: Dict[str, Any]) -> Tuple[np.array, np.array, np.array]:
    cluster_data_genus = np.empty((0, 1))
    cluster_data_year_sprout = np.empty((0, 1))
    cluster_data_age_group = np.empty((0, 1))
    
    for idx, distance in current_tree_pairs.items():
        if tree_features_by_id.get(idx) is None:  # trees without features are not in dict
            continue
        
        genus = tree_features_by_id[idx]["encoded_genus"]
        age_group = tree_features_by_id[idx]["age_group_2020"]
        year_sprout = tree_features_by_id[idx]["year_sprout"]

        cluster_data_genus = np.append(cluster_data_genus, np.array([[genus]]), axis=0)
        cluster_data_age_group = np.append(cluster_data_age_group, np.array([[age_group]]), axis=0)
        cluster_data_year_sprout = np.append(cluster_data_year_sprout, np.array([[year_sprout]]), axis=0)

    return cluster_data_genus, cluster_data_age_group, cluster_data_year_sprout
        

def _count_collect_cluster_labels(clusters_labels: DBSCAN, cluster_data: np.array, cluster_data_key: str, label_encoder: LabelEncoder) -> Dict[str, Any]:
    cluster_labels: Dict[str, Any] = {}
    for index, label in enumerate(clusters_labels):
        label = int(label)
        if cluster_labels.get(label) is None:
            result = int(cluster_data[index, 0])
            if cluster_data_key == "genus":
                result = label_encoder.inverse_transform([result])[0]
            
            cluster_labels[label] = {
                "count": 0, 
                cluster_data_key: result
            }
        cluster_labels[label]["count"] += 1
    
    return cluster_labels


def _get_max_cluster_label(cluster_labels: Dict[str, Any]) -> Tuple[Any, int]:
    max_key = None
    max_count = 0
    for cluster_label, cluster_vals in cluster_labels.items():
        if cluster_vals["count"] >= max_count:
            max_count = cluster_vals["count"]
            max_key = cluster_label
    
    return max_key, max_count


def _make_tree_predictions(df: pd.DataFrame, tree_features_by_id: Dict[str, Any], tree_pairs_by_id: Dict[str, Any], predictions: Dict[str, Optional[Any]], label_encoder: LabelEncoder) -> Dict[str, Optional[Any]]:
    for row_index, row in df.iterrows():
        # if row_index == 2:
        #     break

        current_tree_id = row["id"]

        # ***
        # no neighbours: nothing to cluster
        if tree_pairs_by_id.get(current_tree_id) is None:
            continue

        cluster_data_genus, cluster_data_age_group, cluster_data_year_sprout = _get_cluster(tree_pairs_by_id[current_tree_id], tree_features_by_id)

        cluster_data_collection = {
            "genus": cluster_data_genus,
            "age_group": cluster_data_age_group,
            "year_sprout": cluster_data_year_sprout
        }

        predictions[current_tree_id]: Optional[Dict[str, Any]] = None

        for cluster_data_key, cluster_data in cluster_data_collection.items():
            if len(cluster_data) < MIN_SAMPLES:
                continue
            
            X = StandardScaler().fit_transform(cluster_data)
            clusters = DBSCAN(eps=0.3, min_samples=MIN_SAMPLES).fit(X)

            core_samples_mask = np.zeros_like(clusters.labels_, dtype=bool)
            core_samples_mask[clusters.core_sample_indices_] = True

            clusters_labels = clusters.labels_

            # ***
            # collect and count each cluster label
            cluster_labels = _count_collect_cluster_labels(clusters_labels, cluster_data, cluster_data_key, label_encoder)
            
            # ***
            # get max label from counted cluster labels
            max_key, max_count = _get_max_cluster_label(cluster_labels)

            if predictions[current_tree_id] is None:
                predictions[current_tree_id] = {}
            
            predictions[current_tree_id][cluster_data_key] = {
                "prediction": cluster_labels[max_key][cluster_data_key],
                "probability": round(max_count/len(tree_pairs_by_id[current_tree_id].keys()), 2)
            }

        # except:
        #     continue
    return predictions


def train_neighbouring_tree_cluster(df: pd.DataFrame, tree_pairs_by_id: Dict[str, Any]) -> None:
    label_encoder = LabelEncoder()
    df["encoded_genus"] = label_encoder.fit_transform(df["genus"].astype(str))
    
    df_has_all, df_has_no_age, df_has_none = _split_dataframe(df)
    
    tree_features_by_id = _get_tree_features_by_id(df_has_all)
    
    predictions: Dict[str, Optional[Any]] = {}

    predictions = _make_tree_predictions(df_has_none, tree_features_by_id, tree_pairs_by_id, predictions, label_encoder)
    predictions = _make_tree_predictions(df_has_no_age, tree_features_by_id, tree_pairs_by_id, predictions, label_encoder)
    
    return predictions 

